#include <CoreFoundation/CoreFoundation.h>
#include <dlfcn.h>
#include <mach/mach_time.h>
#include <stdint.h>
#include <stdio.h>
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

static int send_key_once(const HIDFns *fns, int delay_ms, uint32_t usagePage, uint32_t usage) {
    void *client = fns->createClient(NULL);
    if (!client) {
        puts("IOHIDEventSystemClientCreateSimpleClient returned NULL");
        return 1;
    }

    uint64_t now = mach_absolute_time();
    void *down = fns->createKeyboardEvent(NULL, now, usagePage, usage, true, 0);
    void *up = fns->createKeyboardEvent(NULL, now, usagePage, usage, false, 0);
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

int main(void) {
    const int delay_ms = 90;
    const uint32_t kUsagePageConsumer = 0x0c;
    const uint32_t kUsageHome = 0x40;   // Consumer "Menu" (Home button mapping).
    const uint32_t kUsagePageKeyboard = 0x07;
    const uint32_t kUsageEnter = 0x28;  // Keyboard Return/Enter.

    HIDFns fns = {0};
    if (resolve_hid_functions(&fns) != 0) return 1;

    if (send_key_once(&fns, delay_ms, kUsagePageConsumer, kUsageHome) != 0) return 1;
    usleep((useconds_t)delay_ms * 1000);
    if (send_key_once(&fns, delay_ms, kUsagePageKeyboard, kUsageEnter) != 0) return 1;

    puts("sent Home once, then Enter once via EventSystemClient");
    return 0;
}
