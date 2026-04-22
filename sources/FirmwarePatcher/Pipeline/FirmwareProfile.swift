// FirmwareProfile.swift — Firmware layout profiles for restore/patch flows.

import Foundation

/// Describes board-specific firmware paths used by the patching and signing flows.
///
/// The legacy profile keeps the original hybrid layout: vresearch101 boot chain
/// with vphone600 runtime components. iOS 18.5 cloudOS no longer ships the
/// vphone600 runtime identity in the local firmware set, so the 22F76 profile
/// uses vresearch101 for both boot and runtime components.
public enum FirmwareProfile: String, CaseIterable, Sendable {
    case legacy
    case ios18_22F76 = "ios18-22F76"

    public static let defaultProfile: FirmwareProfile = .legacy

    public var bootDeviceClass: String { "vresearch101ap" }

    public var runtimeDeviceClass: String {
        switch self {
        case .legacy:
            "vphone600ap"
        case .ios18_22F76:
            "vresearch101ap"
        }
    }

    public var recoveryModeRequired: Bool {
        switch self {
        case .legacy:
            true
        case .ios18_22F76:
            false
        }
    }

    public var deviceMapBoardConfigs: [String] {
        var seen = Set<String>()
        return [runtimeDeviceClass, bootDeviceClass].filter { seen.insert($0).inserted }
    }

    public var iBSSReleasePath: String { "Firmware/dfu/iBSS.vresearch101.RELEASE.im4p" }
    public var iBECReleasePath: String { "Firmware/dfu/iBEC.vresearch101.RELEASE.im4p" }
    public var llbReleasePath: String { "Firmware/all_flash/LLB.vresearch101.RELEASE.im4p" }
    public var txmResearchPath: String { "Firmware/txm.iphoneos.research.im4p" }
    public var txmReleasePath: String { "Firmware/txm.iphoneos.release.im4p" }
    public var sptmReleasePath: String { "Firmware/sptm.vresearch1.release.im4p" }
    public var sepReleasePath: String { "Firmware/all_flash/sep-firmware.vresearch101.RELEASE.im4p" }

    public var kernelResearchPath: String {
        switch self {
        case .legacy:
            "kernelcache.research.vphone600"
        case .ios18_22F76:
            "kernelcache.research.vresearch101"
        }
    }

    public var deviceTreePath: String {
        switch self {
        case .legacy:
            "Firmware/all_flash/DeviceTree.vphone600ap.im4p"
        case .ios18_22F76:
            "Firmware/all_flash/DeviceTree.vresearch101ap.im4p"
        }
    }

    public var deviceTreeIMG4Name: String {
        switch self {
        case .legacy:
            "DeviceTree.vphone600ap.img4"
        case .ios18_22F76:
            "DeviceTree.vresearch101ap.img4"
        }
    }
}
