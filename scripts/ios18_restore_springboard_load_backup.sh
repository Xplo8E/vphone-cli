#!/bin/zsh
# Restore the iOS 18.5 SpringBoard/launchd plist backups created by
# ios18_patch_springboard_load.sh.
#
# Run this while booted into the SSH ramdisk. This script deliberately copies
# the original backup bytes back in place; it does not parse or rewrite the
# launchd service cache plist.
set -euo pipefail

VM_DIR="${VM_DIR:-vm}"
SSH_PORT="${SSH_PORT:-2222}"
SSH_USER="${SSH_USER:-root}"
SSH_HOST="${SSH_HOST:-localhost}"
SSH_PASS="${SSH_PASS:-alpine}"
OUT_DIR="${OUT_DIR:-$VM_DIR/.ios18_ui_patch/rollback_$(date +%Y%m%d-%H%M%S)}"

command -v sshpass >/dev/null 2>&1 || {
    echo "[-] sshpass is required. Run make setup_tools if missing." >&2
    exit 1
}

mkdir -p "$OUT_DIR"

SSH_OPTS=(
    -o StrictHostKeyChecking=no
    -o UserKnownHostsFile=/dev/null
    -o PreferredAuthentications=password
    -o ConnectTimeout=10
    -q
)

retry() {
    local label="$1"
    shift
    local attempt rc
    for attempt in 1 2 3 4 5; do
        "$@" && return 0
        rc=$?
        if [[ "$rc" != "255" ]]; then
            return "$rc"
        fi
        echo "  [$label] connection lost (attempt $attempt/5), retrying in 3s..." >&2
        sleep 3
    done
    return 255
}

ssh_cmd_raw() {
    sshpass -p "$SSH_PASS" ssh "${SSH_OPTS[@]}" -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" "$@"
}

ssh_cmd() {
    retry ssh ssh_cmd_raw "$@"
}

scp_from_raw() {
    sshpass -p "$SSH_PASS" scp -q "${SSH_OPTS[@]}" -P "$SSH_PORT" "$SSH_USER@$SSH_HOST:$1" "$2"
}

scp_from() {
    retry scp scp_from_raw "$@"
}

echo "[*] Waiting for ramdisk SSH on ${SSH_HOST}:${SSH_PORT}..."
ssh_cmd "echo ready" >/dev/null

echo "[*] Mounting installed rootfs at /mnt1..."
ssh_cmd "/bin/mkdir -p /mnt1"
ssh_cmd "/sbin/mount | /usr/bin/grep -q ' on /mnt1 ' || /sbin/mount_apfs -o rw /dev/disk1s1 /mnt1"

SPRINGBOARD_PLIST="/mnt1/System/Library/LaunchDaemons/com.apple.SpringBoard.plist"
LAUNCHD_PLIST="/mnt1/System/Library/xpc/launchd.plist"

echo "[*] Verifying one-time backups exist..."
ssh_cmd "test -f ${SPRINGBOARD_PLIST}.ios18-ui-bak"
ssh_cmd "test -f ${LAUNCHD_PLIST}.ios18-ui-bak"

echo "[*] Restoring original SpringBoard and launchd plists..."
ssh_cmd "/bin/cp ${SPRINGBOARD_PLIST}.ios18-ui-bak ${SPRINGBOARD_PLIST}"
ssh_cmd "/bin/cp ${LAUNCHD_PLIST}.ios18-ui-bak ${LAUNCHD_PLIST}"
ssh_cmd "/bin/chmod 0644 ${SPRINGBOARD_PLIST} ${LAUNCHD_PLIST}"

echo "[*] Collecting restored files for host-side verification..."
scp_from "$SPRINGBOARD_PLIST" "$OUT_DIR/com.apple.SpringBoard.restored.plist"
scp_from "$LAUNCHD_PLIST" "$OUT_DIR/launchd.restored.plist"

python3 - "$OUT_DIR/com.apple.SpringBoard.restored.plist" "$OUT_DIR/launchd.restored.plist" <<'PY'
import plistlib
import sys
from pathlib import Path

SPRINGBOARD_PATH = "/System/Library/LaunchDaemons/com.apple.SpringBoard.plist"
REQUIRED_KEYS = ("_LimitLoadFromClarityMode", "LimitLoadFromHardware")

for path_s in sys.argv[1:]:
    path = Path(path_s)
    with path.open("rb") as f:
        obj = plistlib.load(f)

    if path.name == "launchd.restored.plist":
        obj = obj.get("LaunchDaemons", {}).get(SPRINGBOARD_PATH)
        if not isinstance(obj, dict):
            raise SystemExit(f"{path}: SpringBoard entry missing")

    missing = [key for key in REQUIRED_KEYS if key not in obj]
    if missing:
        raise SystemExit(f"{path}: backup restore incomplete; missing {missing}")
    print(f"{path}: SpringBoard load gates restored")
PY

echo "[+] SpringBoard load gate rollback complete."
echo "    Reboot normally; this should return the VM to the pre-experiment progress-bar state."
