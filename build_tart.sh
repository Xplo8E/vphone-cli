#!/bin/bash
# build_tart.sh — Patch VM.swift and rebuild super-tart binary only.
# Faster than running setup_bin.sh when you just need to rebuild tart.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BIN_DIR="${REPO_ROOT}/bin"
OEMS_DIR="${REPO_ROOT}/oems"

log() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
ok()  { printf '\033[1;32m  ✓\033[0m %s\n' "$*"; }
err() { printf '\033[1;31m  ✗\033[0m %s\n' "$*" >&2; }
die() { err "$@"; exit 1; }

TARGET="${OEMS_DIR}/super-tart/Sources/tart/VM.swift"
[ -f "${TARGET}" ] || die "VM.swift not found at ${TARGET}"

# ── patch VM.swift ────────────────────────────────────────────────────────────

if rg -q 'import VirtualizationPrivate' "${TARGET}" && rg -q '!!!vsepstorageURL' "${TARGET}"; then
    log "detected wh1te4ever-style vphone VM.swift; skipping auto-patch step"
else
log "patching super-tart VM.swift for vphone (VPHONE_MODE)..."
TARGET="${TARGET}" python3 - <<'PY'
from pathlib import Path
import os, re, sys, textwrap

path = Path(os.environ["TARGET"])
data = path.read_text()

if "VPHONE_MODE" in data:
    print("  ✓ VM.swift already patched")
    sys.exit(0)

needle_class = "class VM: NSObject, VZVirtualMachineDelegate, ObservableObject {\n"
if needle_class not in data:
    raise SystemExit("patch failed: class VM declaration not found")

insert_helpers = needle_class + textwrap.dedent("""\
  static private func vphoneEnabled() -> Bool {
    return ProcessInfo.processInfo.environment["VPHONE_MODE"] == "1"
  }

  // vzHardwareModel derives the VZMacHardwareModel config specific to the "platform type"
  // of the VM (currently only vresearch101 supported)
  // macOS 26+: platformVersion=2 + ISA=2 + OS version hints required for isSupported=true
  static private func vzHardwareModel_VRESEARCH101() throws -> VZMacHardwareModel {
    let hw_descriptor = Dynamic._VZMacHardwareModelDescriptor()
    hw_descriptor.setPlatformVersion(2)
    hw_descriptor.setISA(2)
    // Set guest/host OS versions (required on macOS 26+)
    let guestOS = OperatingSystemVersion(majorVersion: 26, minorVersion: 1, patchVersion: 0)
    hw_descriptor.setInitialGuestMacOSVersion(guestOS)
    let hostOS = ProcessInfo.processInfo.operatingSystemVersion
    hw_descriptor.setMinimumSupportedHostOSVersion(hostOS)

    let hw_model_dyn = Dynamic.VZMacHardwareModel._hardwareModel(withDescriptor: hw_descriptor.asObject)
    guard let hw_model = hw_model_dyn.asObject as? VZMacHardwareModel else {
      fatalError("Failed to create hardware model")
    }

    guard hw_model.isSupported else {
        fatalError("VM hardware config not supported (model.isSupported = false)")
    }

    return hw_model
  }

""")
data = data.replace(needle_class, insert_helpers)

def indent_block(block, indent):
    lines = block.splitlines()
    return "\n".join((indent + line if line else line) for line in lines) + "\n"

def line_start(s, idx):
    return s.rfind("\n", 0, idx) + 1

platform_block = textwrap.dedent("""\
    let vphoneMode = Self.vphoneEnabled()

    // Platform
    if vphoneMode {
      let vmRoot = nvramURL.deletingLastPathComponent()
      let sepstorageURL = vmRoot.appendingPathComponent("SEPStorage")
      let sepConfig = Dynamic._VZSEPCoprocessorConfiguration(storageURL: sepstorageURL)
      sepConfig.debugStub = Dynamic._VZGDBDebugStubConfiguration(port: 8001)
      Dynamic(configuration)._setCoprocessors([sepConfig.asObject])

      let pconf = VZMacPlatformConfiguration()
      pconf.hardwareModel = try vzHardwareModel_VRESEARCH101()

      let serial = Dynamic._VZMacSerialNumber.initWithString("AAAAAA1337")
      let identifier = Dynamic.VZMacMachineIdentifier._machineIdentifierWithECID(0x1111111111111111, serialNumber: serial.asObject)
      pconf.machineIdentifier = identifier.asObject as! VZMacMachineIdentifier

      Dynamic(pconf)._setProductionModeEnabled(true)
      pconf.auxiliaryStorage = VZMacAuxiliaryStorage(url: nvramURL)
      configuration.platform = pconf
    } else {
      configuration.platform = try vmConfig.platform.platform(nvramURL: nvramURL, needsNestedVirtualization: nested)
    }

    // Display
    if vphoneMode {
      let graphics_config = VZMacGraphicsDeviceConfiguration()
      let displays_config = VZMacGraphicsDisplayConfiguration(
          widthInPixels: 1179,
          heightInPixels: 2556,
          pixelsPerInch: 460
      )
      graphics_config.displays.append(displays_config)
      configuration.graphicsDevices = [graphics_config]
    } else {
      configuration.graphicsDevices = [vmConfig.platform.graphicsDevice(vmConfig: vmConfig)]
    }
""")

platform_start = data.find("// Platform")
platform_end = data.find("// Audio", platform_start)
if platform_start == -1 or platform_end == -1:
    raise SystemExit("patch failed: platform/display block not found")
platform_line = line_start(data, platform_start)
platform_indent = re.match(r"[ \t]*", data[platform_line:]).group(0)
data = data[:platform_line] + indent_block(platform_block, platform_indent) + data[platform_end:]

kb_block = textwrap.dedent("""\
    // Keyboard and mouse
    if vphoneMode {
      if #available(macOS 14, *) {
        let keyboard = VZUSBKeyboardConfiguration()
        configuration.keyboards = [keyboard]
      }
      configuration.pointingDevices = vmConfig.platform.pointingDevices()

      if #available(macOS 14, *) {
        let touch = Dynamic._VZUSBTouchScreenConfiguration()
        Dynamic(configuration)._setMultiTouchDevices([touch.asObject])
      }
    } else if suspendable, let platformSuspendable = vmConfig.platform.self as? PlatformSuspendable {
      configuration.keyboards = platformSuspendable.keyboardsSuspendable()
      configuration.pointingDevices = platformSuspendable.pointingDevicesSuspendable()
    } else {
      configuration.keyboards = vmConfig.platform.keyboards()
      configuration.pointingDevices = vmConfig.platform.pointingDevices()
    }
""")

kb_start = data.find("// Keyboard and mouse")
kb_end = data.find("// Networking", kb_start)
if kb_start == -1 or kb_end == -1:
    raise SystemExit("patch failed: keyboard/mouse block not found")
kb_line = line_start(data, kb_start)
kb_indent = re.match(r"[ \t]*", data[kb_line:]).group(0)
data = data[:kb_line] + indent_block(kb_block, kb_indent) + data[kb_end:]

path.write_text(data)
print("  ✓ VM.swift patched")
PY
ok "VM.swift patched"
fi

# ── build ─────────────────────────────────────────────────────────────────────

log "building super-tart (swift build -c release)..."
spm_root="${REPO_ROOT}/.swiftpm"
spm_home="${REPO_ROOT}/.swift-home"
mkdir -p "${spm_root}/config" "${spm_root}/security" "${spm_root}/cache" "${spm_root}/xdg-cache" "${spm_home}"
mkdir -p "${REPO_ROOT}/_work/logs"
BUILD_LOG="${REPO_ROOT}/_work/logs/build_tart_$(date +%Y%m%d_%H%M%S).log"
ok "build log: ${BUILD_LOG}"

pushd "${OEMS_DIR}/super-tart" >/dev/null
if ! SWIFTPM_CONFIG_PATH="${spm_root}/config" \
    SWIFTPM_SECURITY_PATH="${spm_root}/security" \
    SWIFTPM_CACHE_PATH="${spm_root}/cache" \
    XDG_CACHE_HOME="${spm_root}/xdg-cache" \
    HOME="${spm_home}" \
    swift build -c release --disable-sandbox >"${BUILD_LOG}" 2>&1; then
    popd >/dev/null
    err "swift build failed. Last log lines:"
    tail -n 120 "${BUILD_LOG}" >&2 || true
    die "build log: ${BUILD_LOG}"
fi
popd >/dev/null
tail -n 20 "${BUILD_LOG}" || true

cp -f "${OEMS_DIR}/super-tart/.build/release/tart" "${BIN_DIR}/tart"
ok "tart -> ${BIN_DIR}/tart"

# ── sign ──────────────────────────────────────────────────────────────────────

log "signing tart with prod entitlements..."
ENTITLEMENTS="${OEMS_DIR}/super-tart/Resources/tart-prod.entitlements"
codesign --force --sign - --entitlements "${ENTITLEMENTS}" "${BIN_DIR}/tart"
ok "tart signed (com.apple.private.virtualization + com.apple.security.virtualization)"

# ── verify ────────────────────────────────────────────────────────────────────

if strings "${BIN_DIR}/tart" 2>/dev/null | grep "_setCoprocessors" >/dev/null; then
    ok "binary verified: vphone support confirmed (_setCoprocessors present)"
else
    err "warning: _setCoprocessors not found — patch may not have applied"
fi

echo ""
log "done. Run: ./vm_boot_dfu.sh vphone"
