//
// verify_entitlements.c — Dummy process that loads Virtualization.framework,
// triggers entitlement evaluation, then sleeps forever for lldb attach.
//
// The entitlement bitmap is computed inside from_current_process() which is
// called when creating a VZMacHardwareModel. We trigger it via ObjC, then
// lldb reads the static variable.
//
// Usage:
//   clang -O2 -o verify_ent verify_entitlements.c -arch arm64e -lobjc \
//         -framework CoreFoundation -framework Virtualization
//   codesign -f -s - --entitlements <ent.plist> verify_ent
//   ./verify_ent &
//   lldb -p $(pgrep verify_ent) -o "command script import lldb_call_ent.py"
//
#include <stdio.h>
#include <dlfcn.h>
#include <objc/runtime.h>
#include <objc/message.h>
#include <CoreFoundation/CoreFoundation.h>

int main(void) {
    void *vz = dlopen("/System/Library/Frameworks/Virtualization.framework/Virtualization", RTLD_NOW);
    if (!vz) {
        fprintf(stderr, "dlopen failed: %s\n", dlerror());
        return 1;
    }

    // Trigger entitlement evaluation by creating a hardware model descriptor
    // and calling _hardwareModelWithDescriptor: which calls from_current_process()
    Class descCls = objc_getClass("_VZMacHardwareModelDescriptor");
    Class hwCls = objc_getClass("VZMacHardwareModel");

    if (descCls && hwCls) {
        id desc = ((id(*)(id, SEL))objc_msgSend)(
            (id)descCls, sel_registerName("alloc"));
        desc = ((id(*)(id, SEL))objc_msgSend)(
            desc, sel_registerName("init"));
        ((void(*)(id, SEL, unsigned int))objc_msgSend)(
            desc, sel_registerName("setPlatformVersion:"), 3);
        ((void(*)(id, SEL, unsigned int))objc_msgSend)(
            desc, sel_registerName("setISA:"), 2);

        id model = ((id(*)(id, SEL, id))objc_msgSend)(
            (id)hwCls, sel_registerName("_hardwareModelWithDescriptor:"), desc);

        BOOL supported = ((BOOL(*)(id, SEL))objc_msgSend)(
            model, sel_registerName("isSupported"));

        printf("isSupported(PV=3) = %s\n", supported ? "YES" : "NO");
    }

    printf("pid=%d\n", getpid());
    printf("Attach: lldb -p %d -o \"command script import lldb_call_ent.py\"\n", getpid());
    fflush(stdout);

    CFRunLoopRun();
    return 0;
}
