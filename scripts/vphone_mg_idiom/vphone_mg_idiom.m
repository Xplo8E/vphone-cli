// vphone_mg_idiom.m — MobileGestalt interposer for UIKit idiom resolution.
//
// Problem:
//   UIKitCore's _UIDeviceNativeUserInterfaceIdiomIgnoringClassic reads the
//   integer MobileGestalt answer "DeviceClassNumber" and NSAssertion-fires
//   when the returned value is not in its known raw device-class set
//   (valid values on iOS 18.5: 1, 2, 3, 4, 6, 7). On vresearch101 /
//   ComputeModule14,2, MobileGestalt returns a value outside that set, so
//   SpringBoard + AccessibilityUIServer (+ the many other processes that
//   transitively link UIKitCore) abort at launch.
//
// Fix:
//   Interpose MobileGestalt's answer APIs. For the exact key
//   "DeviceClassNumber" return NSNumber @1 (maps to UIUserInterfaceIdiomPhone),
//   and for the integer variants return 1. All other keys fall through to
//   the real implementation via dlsym(RTLD_NEXT).
//
// Deployment:
//   Dropped at /usr/lib/vphone_mg_idiom.dylib and injected into SpringBoard,
//   AccessibilityUIServer, and any other UIKit-consuming process via
//   EnvironmentVariables.DYLD_INSERT_LIBRARIES set on their LaunchDaemon
//   plists. Signed with ldid without entitlements and added to the restore
//   StaticTrustCache so restricted/platform processes accept the insertion.
//
// Rationale for runtime approach:
//   The previous attempt byte-patched UIKitCore inside the signed
//   dyld_shared_cache. That modifies a signed page, AMFI / the VM-fault
//   code-sign validator notice the hash mismatch, and every process that
//   memory-maps UIKit gets SIGKILLed with "CODESIGNING: Invalid Page".
//   An interposer dylib leaves the shared cache untouched.

#import <Foundation/Foundation.h>
#import <stdarg.h>
#import <fcntl.h>
#import <stdint.h>
#import <stdio.h>
#import <string.h>
#import <sys/time.h>
#import <unistd.h>

// Forward declarations of MobileGestalt's C API. Linked against
// libMobileGestalt.dylib (dyld binds these to the real symbols), but the
// __DATA,__interpose records below cause every OTHER caller of these symbols
// in the same process to go through our replacements first.
extern CFTypeRef MGCopyAnswer(CFStringRef key);
extern CFTypeRef MGCopyAnswerWithError(CFStringRef key, int32_t *err);
extern int32_t   MGGetSInt32Answer(CFStringRef key, int32_t defaultValue);

// The Mach-O interpose record format. One entry per interposed symbol.
struct vphone_interpose_entry {
    const void *replacement;
    const void *original;
};

// ---------------------------------------------------------------------------
// Target-key matching helpers.
// ---------------------------------------------------------------------------

static const int32_t kVPhoneIdiomPhoneRaw = 1; // DeviceClassNumber → iPhone

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

    int fd = open("/private/var/log/vphone_mg_idiom.log", O_WRONLY | O_CREAT | O_APPEND, 0644);
    if (fd >= 0) {
        write(fd, line, (size_t)n);
        close(fd);
    }
}

// Always writes a file log; stderr is additionally available when
// VPHONE_MG_IDIOM_DEBUG=1 is set.
static inline void vphone_log(const char *fmt, ...) {
    va_list file_ap;
    va_start(file_ap, fmt);
    vphone_file_log("vphone_mg_idiom", fmt, file_ap);
    va_end(file_ap);

    static int enabled = -1;
    if (enabled < 0) {
        const char *v = getenv("VPHONE_MG_IDIOM_DEBUG");
        enabled = (v != NULL && v[0] == '1') ? 1 : 0;
    }
    if (!enabled) return;
    va_list ap;
    va_start(ap, fmt);
    fprintf(stderr, "[vphone_mg_idiom] ");
    vfprintf(stderr, fmt, ap);
    fprintf(stderr, "\n");
    va_end(ap);
}

// ---------------------------------------------------------------------------
// Interposer stubs. Each resolves the real symbol via RTLD_NEXT on first call
// and forwards everything except our override keys.
// ---------------------------------------------------------------------------

// Inside an interpose replacement, calling the "original" symbol resolves to
// the real libMobileGestalt implementation because dyld's __interpose rewrite
// only applies to OTHER images' call sites — not to our own image's relocations.
// So `MGCopyAnswer(key)` here is literally the real function.

static CFTypeRef vphone_MGCopyAnswer(CFStringRef key) {
    if (vphone_is_device_class_number(key)) {
        vphone_log("MGCopyAnswer(\"DeviceClassNumber\") → 1");
        return (CFTypeRef)CFBridgingRetain(@(kVPhoneIdiomPhoneRaw));
    }
    return MGCopyAnswer(key);
}

static CFTypeRef vphone_MGCopyAnswerWithError(CFStringRef key, int32_t *err) {
    if (vphone_is_device_class_number(key)) {
        vphone_log("MGCopyAnswerWithError(\"DeviceClassNumber\") → 1");
        if (err != NULL) *err = 0;
        return (CFTypeRef)CFBridgingRetain(@(kVPhoneIdiomPhoneRaw));
    }
    return MGCopyAnswerWithError(key, err);
}

static int32_t vphone_MGGetSInt32Answer(CFStringRef key, int32_t defaultValue) {
    if (vphone_is_device_class_number(key)) {
        vphone_log("MGGetSInt32Answer(\"DeviceClassNumber\") → 1");
        return kVPhoneIdiomPhoneRaw;
    }
    return MGGetSInt32Answer(key, defaultValue);
}

// ---------------------------------------------------------------------------
// Mach-O __DATA,__interpose records. dyld reads this section at load time
// and rebinds every OTHER image's reference to the "original" symbol through
// the "replacement" stub, without touching the target library's code.
// ---------------------------------------------------------------------------

__attribute__((used)) static const struct vphone_interpose_entry
vphone_interposers[] __attribute__((section("__DATA,__interpose"))) = {
    { (const void *)vphone_MGCopyAnswer,          (const void *)MGCopyAnswer },
    { (const void *)vphone_MGCopyAnswerWithError, (const void *)MGCopyAnswerWithError },
    { (const void *)vphone_MGGetSInt32Answer,     (const void *)MGGetSInt32Answer },
};

// Constructor just to announce we're loaded.
__attribute__((constructor))
static void vphone_mg_idiom_init(void) {
    vphone_log("loaded");
}
