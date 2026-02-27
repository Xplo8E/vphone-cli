#!/bin/bash
# setup_vm.sh — Bootstrap the vphone VM directory for super-tart.
#
# Creates .tart/vms/vphone/ with:
#   disk.img    — 40 GB sparse disk image
#   nvram.bin   — blank NVRAM (AuxiliaryStorage), initialized on first DFU restore
#   SEPStorage  — blank SEP coprocessor storage, initialized on first DFU restore
#   AVPBooter.vmapple2.bin — patched AVPBooter (copied from bin/)
#   config.json — minimal valid tart config (hardware model overridden by VPHONE_MODE=1)
#
# Run this AFTER patch_fw.py has produced patch_scripts/raw/AVPBooter.raw.
# Then proceed with: prepare_ramdisk.py -> vm_boot_dfu.sh -> boot_rd.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}"
TART_HOME="${TART_HOME:-${REPO_ROOT}/.tart}"
VM_NAME="${1:-vphone}"
VM_DIR="${TART_HOME}/vms/${VM_NAME}"

AVP_RAW="${REPO_ROOT}/bin/AVPBooter.vresearch1.bin"

echo "=== vphone VM bootstrap ==="
echo "VM dir  : ${VM_DIR}"
echo "TART_HOME: ${TART_HOME}"
echo ""

# Refuse to clobber an existing VM
if [ -d "${VM_DIR}" ]; then
    echo "ERROR: VM directory already exists: ${VM_DIR}"
    echo "Remove it first if you want to start fresh:"
    echo "  rm -rf '${VM_DIR}'"
    exit 1
fi

# Check AVPBooter.raw exists
if [ ! -f "${AVP_RAW}" ]; then
    echo "ERROR: Patched AVPBooter not found at: ${AVP_RAW}"
    echo "Run patch_fw.py first to produce bin/AVPBooter.vresearch1.bin"
    exit 1
fi

mkdir -p "${VM_DIR}"

# 1. Sparse 40 GB disk image
echo "[1/4] Creating 40 GB sparse disk image..."
truncate -s 40g "${VM_DIR}/disk.img"

# 2. Blank NVRAM — VZ framework will initialize it on first DFU restore
echo "[2/4] Creating blank nvram.bin..."
touch "${VM_DIR}/nvram.bin"

# 3. Blank SEPStorage — same, initialized on first boot
echo "[3/4] Creating blank SEPStorage..."
touch "${VM_DIR}/SEPStorage"

# 4. Copy patched AVPBooter as romURL
echo "[4/4] Copying patched AVPBooter -> AVPBooter.vmapple2.bin..."
cp "${AVP_RAW}" "${VM_DIR}/AVPBooter.vmapple2.bin"

# 5. Write config.json
# ecid/hardwareModel are vresearch101 values generated via _VZMacHardwareModelDescriptor
# (boardID=0x90, platformVersion=3, ISA=2). These are overridden at runtime by VPHONE_MODE=1
# so the exact values here don't matter as long as they parse — but using real ones avoids crashes.
# Memory: 6 GB (matches typical PCC vphone config). CPU: 4.
cat > "${VM_DIR}/config.json" << 'CONFIG'
{
  "arch" : "arm64",
  "cpuCount" : 4,
  "cpuCountMin" : 4,
  "debugPort" : 8000,
  "display" : {
    "height" : 2556,
    "width" : 1179
  },
  "ecid" : "YnBsaXN0MDDRAQJURUNJRBNN+hoWZxm8hQgLEAAAAAAAAAEBAAAAAAAAAAMAAAAAAAAAAAAAAAAAAAAZ",
  "hardwareModel" : "YnBsaXN0MDDVAQIDBAUGBwkKC18QD1BsYXRmb3JtVmVyc2lvbl8QEk1pbmltdW1TdXBwb3J0ZWRPU1dCb2FyZElEXxAZRGF0YVJlcHJlc2VudGF0aW9uVmVyc2lvblNJU0ESs6gbZaMICAgT//////////8Ss6hS5RABE66sFcmzqBvlCBMlOkJeYmdrdHl7AAAAAAAAAQEAAAAAAAAADAAAAAAAAAAAAAAAAAAAAIQ=",
  "macAddress" : "ee:b2:6a:1a:a9:f4",
  "memorySize" : 6442450944,
  "memorySizeMin" : 6442450944,
  "os" : "darwin",
  "version" : 1
}
CONFIG

echo ""
echo "=== VM bootstrapped successfully ==="
echo ""
echo "Contents of ${VM_DIR}:"
ls -lh "${VM_DIR}"
echo ""
echo "Next steps:"
echo "  1. source setup_env.sh"
echo "  2. cd patch_scripts && python3 prepare_ramdisk.py"
echo "  3. ./vm_boot_dfu.sh ${VM_NAME}"
echo "  4. bash boot_rd.sh"
