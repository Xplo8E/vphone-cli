import Foundation
import Virtualization
import ObjectiveC

// Probe setVariantID:variantName: and its effect on hardware model support
let descClass: AnyClass = NSClassFromString("_VZMacHardwareModelDescriptor")!
let hwmClass: AnyClass = NSClassFromString("VZMacHardwareModel")!
let makeHWSel = NSSelectorFromString("_hardwareModelWithDescriptor:")

let hostOS = ProcessInfo.processInfo.operatingSystemVersion
print("Host OS: \(hostOS.majorVersion).\(hostOS.minorVersion).\(hostOS.patchVersion)")

// Helper
func testConfig(pv: Int, isa: Int, boardID: Int? = nil, variantID: Int? = nil, variantName: String? = nil, guestMajor: Int = 26, guestMinor: Int = 1) {
    let desc = (descClass as! NSObject.Type).init()
    desc.perform(NSSelectorFromString("setPlatformVersion:"), with: pv)
    desc.perform(NSSelectorFromString("setISA:"), with: isa)

    if let bid = boardID {
        desc.perform(NSSelectorFromString("setBoardID:"), with: bid)
    }

    if let vid = variantID, let vname = variantName {
        desc.perform(NSSelectorFromString("setVariantID:variantName:"), with: vid, with: vname)
    }

    let guestOS = OperatingSystemVersion(majorVersion: guestMajor, minorVersion: guestMinor, patchVersion: 0)
    desc.perform(NSSelectorFromString("setInitialGuestMacOSVersion:"), with: guestOS)
    desc.perform(NSSelectorFromString("setMinimumSupportedHostOSVersion:"), with: hostOS)

    let result = (hwmClass as AnyObject).perform(makeHWSel, with: desc)
    if let model = result?.takeUnretainedValue() as? VZMacHardwareModel {
        var label = "pv=\(pv) isa=\(isa)"
        if let bid = boardID { label += " bid=0x\(String(bid, radix: 16))" }
        if let vid = variantID, let vname = variantName { label += " var=\(vid):\(vname)" }
        label += " guest=\(guestMajor).\(guestMinor)"
        print("  \(label) → isSupported=\(model.isSupported)")
    } else {
        print("  pv=\(pv) isa=\(isa) → nil (failed to create)")
    }
}

print("\n=== Baseline: platformVersion=2 ISA=2 (current code) ===")
testConfig(pv: 2, isa: 2)
testConfig(pv: 2, isa: 2, guestMajor: 26, guestMinor: 3)

print("\n=== Old code: platformVersion=3 boardID=0x90 ISA=2 ===")
testConfig(pv: 3, isa: 2, boardID: 0x90)
testConfig(pv: 3, isa: 2, boardID: 0x90, guestMajor: 26, guestMinor: 3)

print("\n=== With variantID/variantName (new 26.3 API) ===")
// Try common variant names that might exist
for vname in ["vresearch101", "vphone600", "vphone600ap", "research", "phone"] {
    for vid in [0, 1, 2, 3] {
        testConfig(pv: 2, isa: 2, variantID: vid, variantName: vname)
    }
}

print("\n=== platformVersion=3 + variants ===")
for vname in ["vresearch101", "vphone600", "vphone600ap"] {
    for vid in [0, 1, 2, 3] {
        testConfig(pv: 3, isa: 2, boardID: 0x90, variantID: vid, variantName: vname)
    }
}

print("\n=== Scan platformVersions 0-5 with ISA=2 ===")
for pv in 0...5 {
    testConfig(pv: pv, isa: 2)
}

print("\n=== _defaultBoardIDForPlatformVersion ===")
let boardIDSel = NSSelectorFromString("_defaultBoardIDForPlatformVersion:")
for pv in 0...5 {
    if hwmClass.responds(to: boardIDSel) {
        let result = (hwmClass as AnyObject).perform(boardIDSel, with: pv as NSNumber)
        print("  pv=\(pv) → defaultBoardID=\(result?.takeUnretainedValue() ?? "nil")")
    }
}
