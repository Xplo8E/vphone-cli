// vphone_sb_shim.m — SpringBoard.framework re-export shim plus MG idiom fix.
//
// SpringBoard.app/SpringBoard has no spare Mach-O header room, so adding a new
// LC_LOAD_DYLIB corrupts its entry stub. This shim is loaded by replacing the
// existing SpringBoard.framework load-command path with /v. It re-exports the
// real SpringBoard framework so _SBSystemAppMain still binds, while also
// carrying the MobileGestalt interposers needed before UIKit's idiom resolver
// asserts on ComputeModule14,2.

#import <Foundation/Foundation.h>
#import <dlfcn.h>
#import <mach/mach.h>
#import <mach/vm_map.h>
#import <mach/vm_param.h>
#import <mach-o/dyld.h>
#import <mach-o/loader.h>
#import <mach-o/nlist.h>
#import <stdarg.h>
#import <fcntl.h>
#import <stdbool.h>
#import <stdint.h>
#import <stdio.h>
#import <string.h>
#import <sys/time.h>
#import <unistd.h>

extern CFTypeRef MGCopyAnswer(CFStringRef key);
extern CFTypeRef MGCopyAnswerWithError(CFStringRef key, int32_t *err);
extern int32_t MGGetSInt32Answer(CFStringRef key, int32_t defaultValue);

#define VPHONE_SEG_LINKEDIT "__LINKEDIT"
#define VPHONE_SEG_DATA "__DATA"
#define VPHONE_SEG_DATA_CONST "__DATA_CONST"

typedef struct mach_header_64 vphone_mach_header_t;
typedef struct segment_command_64 vphone_segment_command_t;
typedef struct section_64 vphone_section_t;
typedef struct nlist_64 vphone_nlist_t;

struct vphone_interpose_entry {
    const void *replacement;
    const void *original;
};

static const int32_t kVPhoneIdiomPhoneRaw = 1;

static CFTypeRef (*real_MGCopyAnswer)(CFStringRef key) = NULL;
static CFTypeRef (*real_MGCopyAnswerWithError)(CFStringRef key, int32_t *err) = NULL;
static int32_t (*real_MGGetSInt32Answer)(CFStringRef key, int32_t defaultValue) = NULL;
static const struct mach_header *vphone_self_header = NULL;

static inline BOOL vphone_is_device_class_number(CFStringRef key) {
    if (key == NULL) return NO;
    return CFStringCompare(key, CFSTR("DeviceClassNumber"), 0) == kCFCompareEqualTo;
}

static inline void vphone_process_path(char *buf, size_t len) {
    if (len == 0) return;
    buf[0] = '\0';
    uint32_t size = (uint32_t)len;
    extern int _NSGetExecutablePath(char *buf, uint32_t *bufsize);
    if (_NSGetExecutablePath(buf, &size) != 0) {
        snprintf(buf, len, "<path-too-long>");
    }
}

static inline void vphone_file_log(const char *prefix, const char *fmt, va_list ap) {
    char msg[1024];
    vsnprintf(msg, sizeof(msg), fmt, ap);

    char exe[512];
    vphone_process_path(exe, sizeof(exe));

    struct timeval tv;
    gettimeofday(&tv, NULL);

    char line[1600];
    int n = snprintf(
        line,
        sizeof(line),
        "%lld.%06d [%s] pid=%d exe=%s %s\n",
        (long long)tv.tv_sec,
        (int)tv.tv_usec,
        prefix,
        getpid(),
        exe,
        msg
    );
    if (n <= 0) return;
    if (n > (int)sizeof(line)) n = (int)sizeof(line);

    const char *paths[] = {
        "/private/var/log/vphone_sb_shim.log",
        "/private/var/mobile/Library/Logs/vphone_sb_shim.log",
        "/tmp/vphone_sb_shim.log",
    };
    for (size_t i = 0; i < sizeof(paths) / sizeof(paths[0]); i++) {
        int fd = open(paths[i], O_WRONLY | O_CREAT | O_APPEND, 0644);
        if (fd >= 0) {
            write(fd, line, (size_t)n);
            close(fd);
            return;
        }
    }
}

static inline void vphone_log(const char *fmt, ...) {
    va_list file_ap;
    va_start(file_ap, fmt);
    vphone_file_log("vphone_sb_shim", fmt, file_ap);
    va_end(file_ap);

    static int enabled = -1;
    if (enabled < 0) {
        const char *v = getenv("VPHONE_MG_IDIOM_DEBUG");
        enabled = (v != NULL && v[0] == '1') ? 1 : 0;
    }
    if (!enabled) return;
    va_list ap;
    va_start(ap, fmt);
    fprintf(stderr, "[vphone_sb_shim] ");
    vfprintf(stderr, fmt, ap);
    fprintf(stderr, "\n");
    va_end(ap);
}

static CFTypeRef vphone_MGCopyAnswer(CFStringRef key) {
    if (vphone_is_device_class_number(key)) {
        vphone_log("MGCopyAnswer(DeviceClassNumber) -> 1");
        return (CFTypeRef)CFBridgingRetain(@(kVPhoneIdiomPhoneRaw));
    }
    return real_MGCopyAnswer != NULL ? real_MGCopyAnswer(key) : MGCopyAnswer(key);
}

static CFTypeRef vphone_MGCopyAnswerWithError(CFStringRef key, int32_t *err) {
    if (vphone_is_device_class_number(key)) {
        vphone_log("MGCopyAnswerWithError(DeviceClassNumber) -> 1");
        if (err != NULL) *err = 0;
        return (CFTypeRef)CFBridgingRetain(@(kVPhoneIdiomPhoneRaw));
    }
    return real_MGCopyAnswerWithError != NULL ? real_MGCopyAnswerWithError(key, err) : MGCopyAnswerWithError(key, err);
}

static int32_t vphone_MGGetSInt32Answer(CFStringRef key, int32_t defaultValue) {
    if (vphone_is_device_class_number(key)) {
        vphone_log("MGGetSInt32Answer(DeviceClassNumber) -> 1");
        return kVPhoneIdiomPhoneRaw;
    }
    return real_MGGetSInt32Answer != NULL ? real_MGGetSInt32Answer(key, defaultValue) : MGGetSInt32Answer(key, defaultValue);
}

struct vphone_rebinding {
    const char *name;
    void *replacement;
    void **replaced;
};

static void vphone_rebind_section(
    const struct vphone_rebinding *rebindings,
    size_t rebindings_count,
    vphone_section_t *section,
    intptr_t slide,
    vphone_nlist_t *symtab,
    char *strtab,
    uint32_t *indirect_symtab,
    const char *image_name
) {
    uint32_t *indices = indirect_symtab + section->reserved1;
    void **bindings = (void **)((uintptr_t)slide + section->addr);
    size_t count = (size_t)(section->size / sizeof(void *));
    vm_address_t page_start = (vm_address_t)((uintptr_t)bindings & ~((uintptr_t)vm_page_size - 1));
    vm_address_t page_end = (vm_address_t)(((uintptr_t)bindings + (uintptr_t)section->size + (uintptr_t)vm_page_size - 1) & ~((uintptr_t)vm_page_size - 1));
    vm_size_t page_size = page_end - page_start;

    for (size_t i = 0; i < count; i++) {
        uint32_t sym_index = indices[i];
        if (sym_index == INDIRECT_SYMBOL_ABS ||
            sym_index == INDIRECT_SYMBOL_LOCAL ||
            sym_index == (INDIRECT_SYMBOL_LOCAL | INDIRECT_SYMBOL_ABS)) {
            continue;
        }

        char *symbol = strtab + symtab[sym_index].n_un.n_strx;
        if (symbol[0] != '_' || symbol[1] == '\0') continue;

        for (size_t j = 0; j < rebindings_count; j++) {
            if (strcmp(symbol + 1, rebindings[j].name) != 0) continue;

            if (rebindings[j].replaced != NULL &&
                *rebindings[j].replaced == NULL &&
                bindings[i] != rebindings[j].replacement) {
                *rebindings[j].replaced = bindings[i];
            }

            kern_return_t kr = vm_protect(mach_task_self(), page_start, page_size, false, VM_PROT_READ | VM_PROT_WRITE | VM_PROT_COPY);
            kern_return_t kr_remap = KERN_SUCCESS;
            if (kr != KERN_SUCCESS) {
                kern_return_t kr_max = vm_protect(mach_task_self(), page_start, page_size, true, VM_PROT_READ | VM_PROT_WRITE | VM_PROT_COPY);
                if (kr_max == KERN_SUCCESS) {
                    kr = vm_protect(mach_task_self(), page_start, page_size, false, VM_PROT_READ | VM_PROT_WRITE | VM_PROT_COPY);
                }
                if (kr != KERN_SUCCESS) {
                    vm_address_t remap_addr = page_start;
                    vm_prot_t cur_prot = VM_PROT_READ | VM_PROT_WRITE | VM_PROT_COPY;
                    vm_prot_t max_prot = VM_PROT_READ | VM_PROT_WRITE | VM_PROT_COPY;
                    kr_remap = vm_remap(
                        mach_task_self(),
                        &remap_addr,
                        page_size,
                        0,
                        VM_FLAGS_FIXED | VM_FLAGS_OVERWRITE,
                        mach_task_self(),
                        page_start,
                        true,
                        &cur_prot,
                        &max_prot,
                        VM_INHERIT_DEFAULT
                    );
                    if (kr_remap == KERN_SUCCESS && remap_addr == page_start) {
                        kr = vm_protect(mach_task_self(), page_start, page_size, false, VM_PROT_READ | VM_PROT_WRITE | VM_PROT_COPY);
                    }
                }
                if (kr != KERN_SUCCESS) {
                    vphone_log(
                        "failed to make %s writable in %s: kr=%d kr_max=%d kr_remap=%d bindings=%p page=%p size=0x%llx sect=%s,%s",
                        rebindings[j].name,
                        image_name != NULL ? image_name : "<unknown>",
                        kr,
                        kr_max,
                        kr_remap,
                        bindings,
                        (void *)page_start,
                        (unsigned long long)page_size,
                        section->segname,
                        section->sectname
                    );
                }
            }
            if (kr == KERN_SUCCESS) {
                bindings[i] = rebindings[j].replacement;
                vphone_log(
                    "rebound %s in %s bindings=%p page=%p size=0x%llx sect=%s,%s",
                    rebindings[j].name,
                    image_name != NULL ? image_name : "<unknown>",
                    bindings,
                    (void *)page_start,
                    (unsigned long long)page_size,
                    section->segname,
                    section->sectname
                );
            }
            break;
        }
    }
}

static void vphone_rebind_image(const struct mach_header *header, intptr_t slide) {
    if (header == NULL || header->magic != MH_MAGIC_64) return;
    if (header == vphone_self_header) return;

    Dl_info info;
    const char *image_name = "<unknown>";
    if (dladdr(header, &info) != 0 && info.dli_fname != NULL) {
        image_name = info.dli_fname;
    }

    vphone_segment_command_t *linkedit = NULL;
    struct symtab_command *symtab_cmd = NULL;
    struct dysymtab_command *dysymtab_cmd = NULL;

    uintptr_t cur = (uintptr_t)header + sizeof(vphone_mach_header_t);
    for (uint32_t i = 0; i < header->ncmds; i++) {
        struct load_command *lc = (struct load_command *)cur;
        if (lc->cmd == LC_SEGMENT_64) {
            vphone_segment_command_t *seg = (vphone_segment_command_t *)cur;
            if (strcmp(seg->segname, VPHONE_SEG_LINKEDIT) == 0) linkedit = seg;
        } else if (lc->cmd == LC_SYMTAB) {
            symtab_cmd = (struct symtab_command *)cur;
        } else if (lc->cmd == LC_DYSYMTAB) {
            dysymtab_cmd = (struct dysymtab_command *)cur;
        }
        cur += lc->cmdsize;
    }

    if (linkedit == NULL || symtab_cmd == NULL || dysymtab_cmd == NULL || dysymtab_cmd->nindirectsyms == 0) {
        return;
    }

    uintptr_t linkedit_base = (uintptr_t)slide + linkedit->vmaddr - linkedit->fileoff;
    vphone_nlist_t *symtab = (vphone_nlist_t *)(linkedit_base + symtab_cmd->symoff);
    char *strtab = (char *)(linkedit_base + symtab_cmd->stroff);
    uint32_t *indirect_symtab = (uint32_t *)(linkedit_base + dysymtab_cmd->indirectsymoff);

    struct vphone_rebinding rebindings[] = {
        { "MGCopyAnswer", (void *)vphone_MGCopyAnswer, (void **)&real_MGCopyAnswer },
        { "MGCopyAnswerWithError", (void *)vphone_MGCopyAnswerWithError, (void **)&real_MGCopyAnswerWithError },
        { "MGGetSInt32Answer", (void *)vphone_MGGetSInt32Answer, (void **)&real_MGGetSInt32Answer },
    };

    cur = (uintptr_t)header + sizeof(vphone_mach_header_t);
    for (uint32_t i = 0; i < header->ncmds; i++) {
        struct load_command *lc = (struct load_command *)cur;
        if (lc->cmd == LC_SEGMENT_64) {
            vphone_segment_command_t *seg = (vphone_segment_command_t *)cur;
            if (strcmp(seg->segname, VPHONE_SEG_DATA) == 0 ||
                strcmp(seg->segname, VPHONE_SEG_DATA_CONST) == 0) {
                vphone_section_t *section = (vphone_section_t *)(cur + sizeof(vphone_segment_command_t));
                for (uint32_t j = 0; j < seg->nsects; j++) {
                    uint32_t type = section[j].flags & SECTION_TYPE;
                    if (type == S_LAZY_SYMBOL_POINTERS || type == S_NON_LAZY_SYMBOL_POINTERS) {
                        vphone_rebind_section(
                            rebindings,
                            sizeof(rebindings) / sizeof(rebindings[0]),
                            &section[j],
                            slide,
                            symtab,
                            strtab,
                            indirect_symtab,
                            image_name
                        );
                    }
                }
            }
        }
        cur += lc->cmdsize;
    }
}

static void vphone_rebind_added_image(const struct mach_header *header, intptr_t slide) {
    vphone_rebind_image(header, slide);
}

static void vphone_install_mg_rebindings(void) {
    vphone_self_header = _dyld_get_image_header(0);
    Dl_info self_info;
    if (dladdr((const void *)vphone_install_mg_rebindings, &self_info) != 0 && self_info.dli_fbase != NULL) {
        vphone_self_header = (const struct mach_header *)self_info.dli_fbase;
    }

    real_MGCopyAnswer = MGCopyAnswer;
    real_MGCopyAnswerWithError = MGCopyAnswerWithError;
    real_MGGetSInt32Answer = MGGetSInt32Answer;

    uint32_t image_count = _dyld_image_count();
    for (uint32_t i = 0; i < image_count; i++) {
        vphone_rebind_image(_dyld_get_image_header(i), _dyld_get_image_vmaddr_slide(i));
    }
    _dyld_register_func_for_add_image(vphone_rebind_added_image);
}

__attribute__((used)) static const struct vphone_interpose_entry
vphone_interposers[] __attribute__((section("__DATA,__interpose"))) = {
    { (const void *)vphone_MGCopyAnswer, (const void *)MGCopyAnswer },
    { (const void *)vphone_MGCopyAnswerWithError, (const void *)MGCopyAnswerWithError },
    { (const void *)vphone_MGGetSInt32Answer, (const void *)MGGetSInt32Answer },
};

__attribute__((constructor))
static void vphone_sb_shim_init(void) {
    vphone_log("loaded");
    vphone_install_mg_rebindings();
}
