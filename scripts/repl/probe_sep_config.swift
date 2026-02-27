import Foundation
import Virtualization
import ObjectiveC

// Probe _VZSEPCoprocessorConfiguration validation behavior
// Test what combination of properties makes it valid

let sepClass: AnyClass = NSClassFromString("_VZSEPCoprocessorConfiguration")!
let configClass: AnyClass = NSClassFromString("VZVirtualMachineConfiguration")!

let sepromURL = URL(fileURLWithPath: "/System/Library/Frameworks/Virtualization.framework/Versions/A/Resources/AVPSEPBooter.vresearch1.bin")
let tempStorage = URL(fileURLWithPath: NSTemporaryDirectory()).appendingPathComponent("SEPStorageTest")
try? FileManager.default.createDirectory(at: tempStorage, withIntermediateDirectories: true)

print("=== Test 1: storageURL only (no romBinaryURL) ===")
do {
    let sep = (sepClass as! NSObject.Type).perform(NSSelectorFromString("alloc"))!
        .takeUnretainedValue()
        .perform(NSSelectorFromString("initWithStorageURL:"), with: tempStorage)!
        .takeUnretainedValue()

    let hasRom = sep.perform(NSSelectorFromString("romBinaryURL"))
    print("romBinaryURL: \(hasRom?.takeUnretainedValue() ?? "nil")")
    print("Created OK (no romBinaryURL)")
} catch {
    print("Failed: \(error)")
}

print("\n=== Test 2: storageURL + romBinaryURL ===")
do {
    let sep = (sepClass as! NSObject.Type).perform(NSSelectorFromString("alloc"))!
        .takeUnretainedValue()
        .perform(NSSelectorFromString("initWithStorageURL:"), with: tempStorage)!
        .takeUnretainedValue()

    sep.perform(NSSelectorFromString("setRomBinaryURL:"), with: sepromURL)
    let hasRom = sep.perform(NSSelectorFromString("romBinaryURL"))
    print("romBinaryURL: \(hasRom?.takeUnretainedValue() ?? "nil")")
    print("Created OK (with romBinaryURL)")
} catch {
    print("Failed: \(error)")
}

// Cleanup
try? FileManager.default.removeItem(at: tempStorage)
