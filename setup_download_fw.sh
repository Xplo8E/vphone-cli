#!/bin/bash
# setup_download_fw.sh — Download and prepare firmware for vphone600ap virtual iPhone.
#
# Downloads two firmware sources and mixes them into a single restore directory:
#   1. iPhone 16 (iPhone17,3) iOS 26.1 (23B85) IPSW — provides SystemVolume, Cryptex,
#      RestoreRamDisk, StaticTrustCache, RestoreTrustCache, OS image
#   2. PCC (Private Cloud Compute) cloudOS 26.1 (23B85) — provides vphone/vresearch
#      bootchain (iBSS, iBEC, LLB, kernelcache, TXM, DeviceTree, AGX, ANE, etc.)
#
# The mixed restore directory uses custom BuildManifest.plist and Restore.plist
# from contents/ that reference the correct components from each source.
#
# Prerequisites:
#   - curl
#   - unzip
#
# NOTE: This script downloads firmware directly from Apple's CDN.
#   No Apple binary files are stored in this repository — only URLs.
#
# Usage:
#   bash setup_download_fw.sh
#
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FW_DIR="${REPO_ROOT}/firmwares"
CONTENTS_DIR="${REPO_ROOT}/contents"

# ── URLs and identifiers ────────────────────────────────────────────────────

IPHONE_IPSW_URL="https://updates.cdn-apple.com/2025FallFCS/fullrestores/089-13864/668EFC0E-5911-454C-96C6-E1063CB80042/iPhone17,3_26.1_23B85_Restore.ipsw"
IPHONE_IPSW_NAME="iPhone17,3_26.1_23B85_Restore.ipsw"
IPHONE_RESTORE_DIR="iPhone17,3_26.1_23B85_Restore"

# PCC (cloudOS) firmware — IPSW asset from Apple's transparency log CDN.
# URL pattern: https://updates.cdn-apple.com/private-cloud-compute/<sha256>
# The hash can be found via: pccvre release dump --release <index> --detail
# Look for the ASSET_TYPE_OS entry with FILE_TYPE_IPSW in the metadata JSON.
PCC_IPSW_URL="https://updates.cdn-apple.com/private-cloud-compute/399b664dd623358c3de118ffc114e42dcd51c9309e751d43bc949b98f4e31349"
PCC_IPSW_NAME="pcc_os_23B85.ipsw"
PCC_EXTRACT_DIR="pcc_extracted"

PATCHED_DIR="${FW_DIR}/firmware_patched/${IPHONE_RESTORE_DIR}"

# ── helpers ──────────────────────────────────────────────────────────────────

log() { printf '\033[1;34m==>\033[0m %s\n' "$*"; }
ok() { printf '\033[1;32m  ✓\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m  !\033[0m %s\n' "$*"; }
err() { printf '\033[1;31m  ✗\033[0m %s\n' "$*" >&2; }
die() {
	err "$@"
	exit 1
}

# ── download iPhone IPSW ─────────────────────────────────────────────────────

download_iphone_ipsw() {
	log "downloading iPhone17,3 iOS 26.1 (23B85) IPSW..."

	if [ -f "${FW_DIR}/${IPHONE_IPSW_NAME}" ]; then
		ok "already exists: ${FW_DIR}/${IPHONE_IPSW_NAME}"
		return 0
	fi

	mkdir -p "${FW_DIR}"
	curl -L -o "${FW_DIR}/${IPHONE_IPSW_NAME}.part" "${IPHONE_IPSW_URL}"
	mv "${FW_DIR}/${IPHONE_IPSW_NAME}.part" "${FW_DIR}/${IPHONE_IPSW_NAME}"
	ok "downloaded: ${FW_DIR}/${IPHONE_IPSW_NAME}"
}

# ── download PCC firmware ─────────────────────────────────────────────────────

download_pcc_ipsw() {
	log "downloading PCC cloudOS 23B85 IPSW..."

	if [ -f "${FW_DIR}/${PCC_IPSW_NAME}" ]; then
		ok "already exists: ${FW_DIR}/${PCC_IPSW_NAME}"
		return 0
	fi

	mkdir -p "${FW_DIR}"
	curl -L -o "${FW_DIR}/${PCC_IPSW_NAME}.part" "${PCC_IPSW_URL}"
	mv "${FW_DIR}/${PCC_IPSW_NAME}.part" "${FW_DIR}/${PCC_IPSW_NAME}"
	ok "downloaded: ${FW_DIR}/${PCC_IPSW_NAME}"
}

# ── extract IPSWs ────────────────────────────────────────────────────────────

extract_iphone_ipsw() {
	log "extracting iPhone IPSW..."

	if [ -d "${PATCHED_DIR}" ]; then
		ok "restore directory already exists: ${PATCHED_DIR}"
		return 0
	fi

	mkdir -p "${PATCHED_DIR}"
	unzip -o "${FW_DIR}/${IPHONE_IPSW_NAME}" -d "${PATCHED_DIR}"
	ok "extracted to: ${PATCHED_DIR}"
}

extract_pcc_ipsw() {
	log "extracting PCC IPSW..."

	if [ -d "${FW_DIR}/${PCC_EXTRACT_DIR}" ]; then
		ok "PCC extract directory already exists: ${FW_DIR}/${PCC_EXTRACT_DIR}"
		return 0
	fi

	mkdir -p "${FW_DIR}/${PCC_EXTRACT_DIR}"
	unzip -o "${FW_DIR}/${PCC_IPSW_NAME}" -d "${FW_DIR}/${PCC_EXTRACT_DIR}"
	ok "extracted to: ${FW_DIR}/${PCC_EXTRACT_DIR}"
}

# ── mix firmware components ──────────────────────────────────────────────────
# Replace iPhone components with vphone/vresearch components from PCC firmware.
# iPhone IPSW provides: SystemVolume, Cryptex, RestoreRamDisk, TrustCaches
# PCC IPSW provides: bootchain (iBSS, iBEC, LLB), kernelcache, TXM, SPTM,
#                     DeviceTree, AGX, ANE, DFU, PMP, all_flash, etc.

mix_firmware() {
	log "mixing firmware components (PCC -> iPhone restore dir)..."

	local pcc="${FW_DIR}/${PCC_EXTRACT_DIR}"
	local dst="${PATCHED_DIR}"

	# kernelcache (vphone research variants from PCC)
	log "  copying kernelcache..."
	cp -f "${pcc}"/kernelcache.research.vphone600 "${dst}/" 2>/dev/null || true
	cp -f "${pcc}"/kernelcache.research.vresearch101 "${dst}/" 2>/dev/null || true

	# Firmware subdirectories from PCC
	for subdir in agx all_flash ane dfu pmp; do
		if [ -d "${pcc}/Firmware/${subdir}" ]; then
			log "  copying Firmware/${subdir}/..."
			mkdir -p "${dst}/Firmware/${subdir}"
			cp -f "${pcc}/Firmware/${subdir}"/* "${dst}/Firmware/${subdir}/" 2>/dev/null || true
		fi
	done

	# Top-level Firmware IM4P files from PCC (SPTM, TXM, etc.)
	log "  copying Firmware/*.im4p..."
	for f in "${pcc}"/Firmware/*.im4p; do
		[ -f "$f" ] && cp -f "$f" "${dst}/Firmware/"
	done

	# Custom BuildManifest.plist and Restore.plist
	log "  installing custom BuildManifest.plist and Restore.plist..."
	if [ -f "${CONTENTS_DIR}/BuildManifest.plist" ]; then
		cp -f "${CONTENTS_DIR}/BuildManifest.plist" "${dst}/BuildManifest.plist"
		ok "BuildManifest.plist"
	else
		warn "contents/BuildManifest.plist not found — skipping"
	fi

	if [ -f "${CONTENTS_DIR}/Restore.plist" ]; then
		cp -f "${CONTENTS_DIR}/Restore.plist" "${dst}/Restore.plist"
		ok "Restore.plist"
	else
		warn "contents/Restore.plist not found — skipping"
	fi

	ok "firmware mixed into: ${dst}"
}

# ── summary ──────────────────────────────────────────────────────────────────

summary() {
	echo ""
	log "firmware setup complete"
	echo ""
	echo "  Restore directory: ${PATCHED_DIR}"
	echo ""
	echo "  Next steps:"
	echo "    1. source setup_env.sh"
	echo "    2. cd patch_scripts && python3 patch_fw.py -d '${PATCHED_DIR}'"
	echo "    3. Run idevicerestore in DFU mode to flash the patched firmware"
	echo ""
}

# ── main ─────────────────────────────────────────────────────────────────────

main() {
	log "setup_download_fw.sh — download and prepare vphone600ap firmware"
	echo ""

	download_iphone_ipsw
	download_pcc_ipsw
	extract_iphone_ipsw
	extract_pcc_ipsw
	mix_firmware
	summary
}

main "$@"
