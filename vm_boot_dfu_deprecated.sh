#!/bin/bash
# vm_boot_dfu.sh — Start the vphone VM in DFU mode via vphone-cli.
#
# Usage:
#   ./vm_boot_dfu.sh [vm_name] [--rom PATH] [--disk PATH] [--nvram PATH] \
#                    [--sep-storage PATH] [--sep-rom PATH] [-- extra vphone-cli args...]
#
# Examples:
#   ./vm_boot_dfu.sh vphone --serial
#   ./vm_boot_dfu.sh vphone --sep-rom /path/to/AVPSEPBooter.vresearch1.bin
#   ./vm_boot_dfu.sh vphone --rom /path/to/AVPBooter.vresearch1.bin -- --no-graphics

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="${SCRIPT_DIR}"
TART_HOME="${TART_HOME:-${REPO_ROOT}/.tart}"
VPHONE_CLI="${VPHONE_CLI:-${REPO_ROOT}/vphone-cli/.build/release/vphone-cli}"

if [ "${1:-}" = "--help" ] || [ "${1:-}" = "-h" ]; then
	echo "usage: ./vm_boot_dfu.sh [vm_name] [--rom PATH] [--disk PATH] [--nvram PATH] \\"
	echo "                         [--sep-storage PATH] [--sep-rom PATH] [-- extra vphone-cli args]"
	echo ""
	echo "defaults (relative to TART_HOME VM dir):"
	echo "  ROM         : AVPBooter.vresearch1.bin"
	echo "  disk        : disk.img"
	echo "  nvram       : nvram.bin"
	echo "  sep-storage : SEPStorage"
	echo "  sep-rom     : AVPSEPBooter.vresearch1.bin"
	exit 0
fi

VM_NAME="vphone"
if [ "$#" -gt 0 ] && [[ "${1}" != -* ]]; then
	VM_NAME="${1}"
	shift
fi

VM_DIR="${TART_HOME}/vms/${VM_NAME}"

# Paths inside the tart VM directory
ROM="${VM_DIR}/AVPBooter.vresearch1.bin"
DISK="${VM_DIR}/disk.img"
NVRAM="${VM_DIR}/nvram.bin"
SEP_STORAGE="${VM_DIR}/SEPStorage"
SEP_ROM="${VM_DIR}/AVPSEPBooter.vresearch1.bin"

EXTRA_ARGS=()
while [ "$#" -gt 0 ]; do
	case "$1" in
		--rom)
			[ "$#" -ge 2 ] || { echo "ERROR: --rom requires a path"; exit 1; }
			ROM="$2"
			shift 2
			;;
		--disk)
			[ "$#" -ge 2 ] || { echo "ERROR: --disk requires a path"; exit 1; }
			DISK="$2"
			shift 2
			;;
		--nvram)
			[ "$#" -ge 2 ] || { echo "ERROR: --nvram requires a path"; exit 1; }
			NVRAM="$2"
			shift 2
			;;
		--sep-storage)
			[ "$#" -ge 2 ] || { echo "ERROR: --sep-storage requires a path"; exit 1; }
			SEP_STORAGE="$2"
			shift 2
			;;
		--sep-rom)
			[ "$#" -ge 2 ] || { echo "ERROR: --sep-rom requires a path"; exit 1; }
			SEP_ROM="$2"
			shift 2
			;;
		--)
			shift
			EXTRA_ARGS+=("$@")
			break
			;;
		*)
			EXTRA_ARGS+=("$1")
			shift
			;;
	esac
done

if [ ! -x "${VPHONE_CLI}" ]; then
	echo "ERROR: vphone-cli not found at ${VPHONE_CLI}"
	echo "Run: cd vphone-cli && bash build_and_sign.sh"
	exit 1
fi

if [ ! -f "${ROM}" ]; then
	echo "ERROR: ROM not found: ${ROM}"
	echo "Pass explicit path with --rom <path>."
	exit 1
fi

if [ ! -f "${DISK}" ]; then
	echo "ERROR: disk not found: ${DISK}"
	echo "Pass explicit path with --disk <path>."
	exit 1
fi

if [ ! -f "${NVRAM}" ]; then
	echo "ERROR: nvram not found: ${NVRAM}"
	echo "Pass explicit path with --nvram <path>."
	exit 1
fi

if [ ! -f "${SEP_STORAGE}" ]; then
	echo "ERROR: SEP storage not found: ${SEP_STORAGE}"
	echo "Pass explicit path with --sep-storage <path>."
	exit 1
fi

if [ ! -f "${SEP_ROM}" ]; then
	echo "ERROR: SEP ROM not found: ${SEP_ROM}"
	echo "Pass explicit path with --sep-rom <path>."
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
	--sep-storage "${SEP_STORAGE}"
	--sep-rom "${SEP_ROM}"
)

echo "Command: ${VPHONE_CLI} ${ARGS[*]} ${EXTRA_ARGS[*]}"
echo ""
exec "${VPHONE_CLI}" "${ARGS[@]}" "${EXTRA_ARGS[@]}"
