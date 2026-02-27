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
    if let model = VZMacHardwareModel._hardwareModel(withDescriptor: desc) {
        print("  \(label): isSupported=\(model.isSupported)")
    } else {
        print("  \(label): nil")
    }
}

print("\n=== Basic combos (no OS hints) ===")
test("pv2 isa2") { d in d.setPlatformVersion(2); d.setISA(2) }
test("pv3 isa2") { d in d.setPlatformVersion(3); d.setISA(2) }
test("pv3 bid90 isa2") { d in d.setPlatformVersion(3); d.setBoardID(0x90); d.setISA(2) }

print("\n=== With variantID (no OS hints) ===")
for vname in ["vresearch101", "vphone600", "vphone600ap"] {
    for vid: UInt32 in [0, 1, 2, 3] {
        test("pv3 bid90 var=\(vid):\(vname)") { d in
            d.setPlatformVersion(3); d.setBoardID(0x90); d.setISA(2)
            d.setVariantID(vid, variantName: vname)
        }
        test("pv2 var=\(vid):\(vname)") { d in
            d.setPlatformVersion(2); d.setISA(2)
            d.setVariantID(vid, variantName: vname)
        }
    }
}

print("\n=== Scan pv 0-5, isa 0-3 ===")
for pv: UInt32 in 0...5 {
    for isa: Int64 in 0...3 {
        test("pv\(pv) isa\(isa)") { d in
            d.setPlatformVersion(pv); d.setISA(isa)
        }
    }
}
