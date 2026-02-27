#!/bin/bash
# vm_boot_dfu.sh — Start the vphone VM in DFU mode via vphone-cli.
#
# Usage:
#   ./vm_boot_dfu.sh [vm_name] [extra vphone-cli args...]
#
# Examples:
#   ./vm_boot_dfu.sh vphone --serial
#   ./vm_boot_dfu.sh vphone --skip-sep
#   ./vm_boot_dfu.sh vphone --sep-rom /path/to/sep.bin

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}"
TART_HOME="${TART_HOME:-${REPO_ROOT}/.tart}"
VPHONE_CLI="${VPHONE_CLI:-${REPO_ROOT}/vphone-cli/.build/release/vphone-cli}"

VM_NAME="${1:-vphone}"
if [ "$#" -gt 0 ]; then
	shift
fi

VM_DIR="${TART_HOME}/vms/${VM_NAME}"

# Paths inside the tart VM directory
ROM="${VM_DIR}/AVPBooter.vresearch1.bin"
DISK="${VM_DIR}/disk.img"
NVRAM="${VM_DIR}/nvram.bin"
SEP_STORAGE="${VM_DIR}/SEPStorage.img"
SEP_ROM="${VM_DIR}/AVPSEPBooter.vresearch1.bin"

if [ ! -x "${VPHONE_CLI}" ]; then
	echo "ERROR: vphone-cli not found at ${VPHONE_CLI}"
	echo "Run: cd vphone-cli && bash build_and_sign.sh"
	exit 1
fi

if [ ! -f "${ROM}" ]; then
	echo "ERROR: ROM not found: ${ROM}"
	echo "Create the VM directory with the required firmware files first."
	exit 1
fi

echo "=== Starting vphone DFU ==="
echo "VM dir : ${VM_DIR}"
echo "ROM    : ${ROM}"
echo "Disk   : ${DISK}"
echo "NVRAM  : ${NVRAM}"
echo "SEP    : ${SEP_STORAGE}"
echo "SEP ROM: ${SEP_ROM}"
echo ""

# Build CLI args
ARGS=(
	--rom "${ROM}"
	--disk "${DISK}"
	--nvram "${NVRAM}"
)

# Add SEP args if files exist (unless --skip-sep passed by user)
if [[ ! " $* " =~ " --skip-sep " ]]; then
	if [ -f "${SEP_STORAGE}" ]; then
		ARGS+=(--sep-storage "${SEP_STORAGE}")
	fi
	if [ -f "${SEP_ROM}" ]; then
		ARGS+=(--sep-rom "${SEP_ROM}")
	fi
fi

echo "Command: ${VPHONE_CLI} ${ARGS[*]} $*"
echo ""
exec "${VPHONE_CLI}" "${ARGS[@]}" "$@"
