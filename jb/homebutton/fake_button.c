#include <CoreFoundation/CoreFoundation.h>
#include <dlfcn.h>
#include <mach/mach_time.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

typedef void *(*IOHIDEventSystemClientCreateSimpleClientFn)(CFAllocatorRef allocator);
typedef void *(*IOHIDEventCreateKeyboardEventFn)(CFAllocatorRef allocator,
                                                  uint64_t timestamp,
                                                  uint32_t usagePage,
                                                  uint32_t usage,
                                                  Boolean down,
                                                  uint32_t options);
typedef void (*IOHIDEventSystemClientDispatchEventFn)(void *client, void *event);

typedef struct {
    IOHIDEventSystemClientCreateSimpleClientFn createClient;
    IOHIDEventCreateKeyboardEventFn createKeyboardEvent;
    IOHIDEventSystemClientDispatchEventFn dispatchEvent;
} HIDFns;

static int parse_int_arg(const char *value, int fallback) {
    if (!value || !*value) return fallback;
    char *end = NULL;
    long v = strtol(value, &end, 10);
    if (!end || *end != '\0' || v <= 0 || v > 100000) return fallback;
    return (int)v;
}

static int resolve_hid_functions(HIDFns *fns) {
    void *h = dlopen("/System/Library/Frameworks/IOKit.framework/IOKit", RTLD_NOW);
    if (!h) {
        printf("dlopen(IOKit) failed: %s\n", dlerror());
        return 1;
    }

    fns->createClient =
        (IOHIDEventSystemClientCreateSimpleClientFn)dlsym(h, "IOHIDEventSystemClientCreateSimpleClient");
    fns->createKeyboardEvent =
        (IOHIDEventCreateKeyboardEventFn)dlsym(h, "IOHIDEventCreateKeyboardEvent");
    fns->dispatchEvent =
        (IOHIDEventSystemClientDispatchEventFn)dlsym(h, "IOHIDEventSystemClientDispatchEvent");

    if (!fns->createClient || !fns->createKeyboardEvent || !fns->dispatchEvent) {
        printf("required symbols missing: create=%p keyboard=%p dispatch=%p\n",
               (void *)fns->createClient,
               (void *)fns->createKeyboardEvent,
               (void *)fns->dispatchEvent);
        dlclose(h);
        return 1;
    }

    return 0;
}

static int send_home_once(const HIDFns *fns, int delay_ms) {
    void *client = fns->createClient(NULL);
    if (!client) {
        puts("IOHIDEventSystemClientCreateSimpleClient returned NULL");
        return 1;
    }

    uint64_t now = mach_absolute_time();
    void *down = fns->createKeyboardEvent(NULL, now, 0x0c, 0x40, true, 0);
    void *up = fns->createKeyboardEvent(NULL, now, 0x0c, 0x40, false, 0);
    if (!down || !up) {
        printf("IOHIDEventCreateKeyboardEvent failed: down=%p up=%p\n", down, up);
        if (down) CFRelease(down);
        if (up) CFRelease(up);
        CFRelease(client);
        return 1;
    }

    fns->dispatchEvent(client, down);
    usleep((useconds_t)delay_ms * 1000);
    fns->dispatchEvent(client, up);

    CFRelease(down);
    CFRelease(up);
    CFRelease(client);
    return 0;
}

int main(int argc, char **argv) {
    int delay_ms = 90;
    int repeat = 1;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--delay-ms") == 0 && (i + 1) < argc) {
            delay_ms = parse_int_arg(argv[++i], delay_ms);
        } else if (strcmp(argv[i], "--repeat") == 0 && (i + 1) < argc) {
            repeat = parse_int_arg(argv[++i], repeat);
        }
    }

    HIDFns fns = {0};
    if (resolve_hid_functions(&fns) != 0) return 1;

    for (int n = 0; n < repeat; n++) {
        if (send_home_once(&fns, delay_ms) != 0) return 1;
    }

    if (repeat == 1) {
        puts("sent IOHID consumer menu down/up via EventSystemClient");
    } else {
        printf("sent IOHID consumer menu down/up x%d via EventSystemClient\n", repeat);
    }
    return 0;
}
