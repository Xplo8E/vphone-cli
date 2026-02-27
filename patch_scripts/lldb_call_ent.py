"""
lldb script to call VzCore::VirtualizationEntitlements::from_current_process()
and read the result from its static variable.

The function is void — it stores the bitmap in a static local:
  VzCore::VirtualizationEntitlements::from_current_process()::entitlements (.0)

Usage: lldb -p <pid> -o "command script import lldb_call_ent.py"
"""
import lldb

def print_bitmap(bitmap):
    print(f"bitmap=0x{bitmap:02x}")
    ents = [
        (0, 0x01, "com.apple.security.virtualization"),
        (1, 0x02, "com.apple.private.virtualization"),
        (2, 0x04, "com.apple.vm.networking"),
        (3, 0x08, "com.apple.private.ggdsw.GPUProcessProtectedContent"),
        (4, 0x10, "com.apple.private.virtualization.security-research"),
        (5, 0x20, "com.apple.private.virtualization.private-vsock"),
    ]
    for bit, mask, name in ents:
        flag = "YES" if (bitmap & mask) else "no"
        print(f"  bit {bit} (0x{mask:02x}) {name}: {flag}")
    pv3 = (bitmap & 0x12) != 0
    print(f"PV=3 validity: (0x{bitmap:02x} & 0x12) = 0x{bitmap & 0x12:02x} -> {'ENABLED' if pv3 else 'DISABLED'}")


def __lldb_init_module(debugger, internal_dict):
    target = debugger.GetSelectedTarget()
    process = target.GetProcess()
    thread = process.GetSelectedThread()
    frame = thread.GetSelectedFrame()

    func_addr = None
    static_addr = None
    guard_addr = None

    for m in target.module_iter():
        if m.file.basename == "Virtualization":
            for sym in m:
                name = sym.name
                if "from_current_process" not in name:
                    continue
                addr = sym.addr.GetLoadAddress(target)
                if "guard variable" in name:
                    guard_addr = addr
                    print(f"[*] guard var: 0x{addr:x}")
                elif ".0" in name or "entitlements" in name.split("::")[-1].split("(")[0]:
                    # the static variable (entitlements .0)
                    if "__DATA" in str(sym.addr.section) or "bss" in str(sym.addr.section):
                        static_addr = addr
                        print(f"[*] static var: 0x{addr:x}")
                elif "__TEXT" in str(sym.addr.section):
                    func_addr = addr
                    print(f"[*] function: 0x{addr:x}")
            break

    if not func_addr or not static_addr:
        print("[!] Could not find required symbols")
        return

    # Call from_current_process() to trigger one-time initialization.
    # It's void, but we need to trigger the static init.
    # PAC-sign the pointer for arm64e.
    print(f"[*] calling from_current_process to initialize static...")
    expr_call = (
        f"((void(*)(void))"
        f"__builtin_ptrauth_sign_unauthenticated("
        f"(void *){func_addr}, 0, 0))()"
    )
    val = frame.EvaluateExpression(expr_call)
    if not val.error.Success():
        print(f"[!] call failed: {val.error}")
        print(f"[*] trying without PAC sign...")
        expr_call2 = f"((void(*)(void))({func_addr}))()"
        val = frame.EvaluateExpression(expr_call2)
        if not val.error.Success():
            print(f"[!] call also failed: {val.error}")
            print(f"[*] trying to read static anyway (may already be initialized)...")

    # Read the static variable (uint32_t)
    print(f"[*] reading static var at 0x{static_addr:x}...")
    err = lldb.SBError()
    bitmap = process.ReadUnsignedFromMemory(static_addr, 4, err)
    if err.Fail():
        print(f"[!] read failed: {err}")
        return

    print_bitmap(bitmap)
