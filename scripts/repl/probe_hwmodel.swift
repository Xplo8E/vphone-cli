import Foundation
import Virtualization
import VirtualizationPrivate

let hostOS = ProcessInfo.processInfo.operatingSystemVersion
print("Host: \(hostOS.majorVersion).\(hostOS.minorVersion).\(hostOS.patchVersion)")

func test(_ label: String, _ configure: (_VZMacHardwareModelDescriptor) -> Void) {
    guard let desc = _VZMacHardwareModelDescriptor() else {
        print("  \(label): failed to create descriptor")
        return
    }
    configure(desc)
    let model = VZMacHardwareModel._hardwareModel(withDescriptor: desc)
    print("  \(label): isSupported=\(model.isSupported)")
}

print("\n=== platformVersion=2 (no boardID) ===")
test("pv2 isa2") { d in
    d.setPlatformVersion(2); d.setISA(2)
}
test("pv2 isa2 +osHints") { d in
    d.setPlatformVersion(2); d.setISA(2)
    d.setInitialGuestMacOSVersion(.init(majorVersion: 26, minorVersion: 1, patchVersion: 0))
    d.setMinimumSupportedHostOSVersion(hostOS)
}

print("\n=== platformVersion=3 + boardID=0x90 ===")
test("pv3 bid90 isa2") { d in
    d.setPlatformVersion(3); d.setBoardID(0x90); d.setISA(2)
}
test("pv3 bid90 isa2 +osHints") { d in
    d.setPlatformVersion(3); d.setBoardID(0x90); d.setISA(2)
    d.setInitialGuestMacOSVersion(.init(majorVersion: 26, minorVersion: 1, patchVersion: 0))
    d.setMinimumSupportedHostOSVersion(hostOS)
}
test("pv3 bid90 isa2 +osHints(26.3)") { d in
    d.setPlatformVersion(3); d.setBoardID(0x90); d.setISA(2)
    d.setInitialGuestMacOSVersion(.init(majorVersion: 26, minorVersion: 3, patchVersion: 0))
    d.setMinimumSupportedHostOSVersion(hostOS)
}

print("\n=== platformVersion=3 + variantID/variantName ===")
for (vid, vname) in [(0, "vresearch101"), (1, "vresearch101"), (2, "vresearch101"),
                      (0, "vphone600"), (1, "vphone600"), (2, "vphone600"),
                      (0, "vphone600ap"), (1, "vphone600ap")] as [(UInt32, String)] {
    test("pv3 bid90 isa2 var=\(vid):\(vname)") { d in
        d.setPlatformVersion(3); d.setBoardID(0x90); d.setISA(2)
        d.setVariantID(vid, variantName: vname)
        d.setInitialGuestMacOSVersion(.init(majorVersion: 26, minorVersion: 1, patchVersion: 0))
        d.setMinimumSupportedHostOSVersion(hostOS)
    }
}

print("\n=== platformVersion=2 + variantID/variantName ===")
for (vid, vname) in [(0, "vresearch101"), (1, "vresearch101"),
                      (0, "vphone600"), (1, "vphone600")] as [(UInt32, String)] {
    test("pv2 isa2 var=\(vid):\(vname)") { d in
        d.setPlatformVersion(2); d.setISA(2)
        d.setVariantID(vid, variantName: vname)
        d.setInitialGuestMacOSVersion(.init(majorVersion: 26, minorVersion: 1, patchVersion: 0))
        d.setMinimumSupportedHostOSVersion(hostOS)
    }
}

print("\n=== scan all platformVersions 0-5, ISA 0-3 ===")
for pv: UInt32 in 0...5 {
    for isa: Int64 in 0...3 {
        test("pv\(pv) isa\(isa) +osHints") { d in
            d.setPlatformVersion(pv); d.setISA(isa)
            d.setInitialGuestMacOSVersion(.init(majorVersion: 26, minorVersion: 1, patchVersion: 0))
            d.setMinimumSupportedHostOSVersion(hostOS)
        }
    }
}
