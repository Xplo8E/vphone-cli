#!/bin/zsh
# Rebuild the active launchd service cache after an unsafe UI experiment.
#
# This is the last CFW phase only: copy our daemon plists back to the installed
# rootfs, rebuild /System/Library/xpc/launchd.plist from launchd.plist.bak with
# the normal CFW injector, and write it back. Run from the host while the VM is
# booted into the SSH ramdisk.
set -euo pipefail

VM_DIR="${VM_DIR:-vm}"
SSH_PORT="${SSH_PORT:-2222}"
SSH_USER="${SSH_USER:-root}"
SSH_HOST="${SSH_HOST:-localhost}"
SSH_PASS="${SSH_PASS:-alpine}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON3="${PYTHON3:-$REPO_DIR/.venv/bin/python3}"
TEMP_DIR="${VM_DIR}/.ios18_ui_patch/launchd_rebuild_$(date +%Y%m%d-%H%M%S)"
INPUT_DIR="${VM_DIR}/cfw_input"
VPHONED_SRC="$SCRIPT_DIR/vphoned"

command -v sshpass >/dev/null 2>&1 || {
    echo "[-] sshpass is required. Run make setup_tools if missing." >&2
    exit 1
}

[[ -x "$PYTHON3" ]] || PYTHON3="python3"
[[ -d "$INPUT_DIR/jb/LaunchDaemons" ]] || {
    echo "[-] Missing $INPUT_DIR/jb/LaunchDaemons. Run cfw_install_dev once first." >&2
    exit 1
}
[[ -f "$VPHONED_SRC/vphoned.plist" ]] || {
    echo "[-] Missing $VPHONED_SRC/vphoned.plist" >&2
    exit 1
}

mkdir -p "$TEMP_DIR/LaunchDaemons"
cp "$INPUT_DIR/jb/LaunchDaemons"/{bash,dropbear,trollvnc,rpcserver_ios}.plist "$TEMP_DIR/LaunchDaemons/"
cp "$VPHONED_SRC/vphoned.plist" "$TEMP_DIR/LaunchDaemons/"

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

scp_to_raw() {
    sshpass -p "$SSH_PASS" scp -q "${SSH_OPTS[@]}" -P "$SSH_PORT" "$1" "$SSH_USER@$SSH_HOST:$2"
}

scp_from_raw() {
    sshpass -p "$SSH_PASS" scp -q "${SSH_OPTS[@]}" -P "$SSH_PORT" "$SSH_USER@$SSH_HOST:$1" "$2"
}

scp_to() {
    retry scp scp_to_raw "$@"
}

scp_from() {
    retry scp scp_from_raw "$@"
}

echo "[*] Waiting for ramdisk SSH on ${SSH_HOST}:${SSH_PORT}..."
ssh_cmd "echo ready" >/dev/null

echo "[*] Mounting installed rootfs at /mnt1..."
ssh_cmd "/bin/mkdir -p /mnt1"
ssh_cmd "/sbin/mount | /usr/bin/grep -q ' on /mnt1 ' || /sbin/mount_apfs -o rw /dev/disk1s1 /mnt1"

echo "[*] Installing CFW LaunchDaemon plists..."
for plist in bash.plist dropbear.plist trollvnc.plist rpcserver_ios.plist vphoned.plist; do
    scp_to "$TEMP_DIR/LaunchDaemons/$plist" "/mnt1/System/Library/LaunchDaemons/"
    ssh_cmd "/bin/chmod 0644 /mnt1/System/Library/LaunchDaemons/$plist"
done

echo "[*] Rebuilding launchd.plist from launchd.plist.bak..."
ssh_cmd "test -f /mnt1/System/Library/xpc/launchd.plist.bak"
scp_from "/mnt1/System/Library/xpc/launchd.plist.bak" "$TEMP_DIR/launchd.plist"
"$PYTHON3" "$SCRIPT_DIR/patchers/cfw.py" inject-daemons "$TEMP_DIR/launchd.plist" "$TEMP_DIR/LaunchDaemons"
scp_to "$TEMP_DIR/launchd.plist" "/mnt1/System/Library/xpc/launchd.plist"
ssh_cmd "/bin/chmod 0644 /mnt1/System/Library/xpc/launchd.plist"

echo "[*] Verifying rebuilt cache contains CFW daemons..."
scp_from "/mnt1/System/Library/xpc/launchd.plist" "$TEMP_DIR/launchd.rebuilt.plist"
python3 - "$TEMP_DIR/launchd.rebuilt.plist" <<'PY'
import plistlib
import sys

with open(sys.argv[1], "rb") as f:
    obj = plistlib.load(f)
daemons = obj.get("LaunchDaemons", {})
required = [
    "/System/Library/LaunchDaemons/bash.plist",
    "/System/Library/LaunchDaemons/dropbear.plist",
    "/System/Library/LaunchDaemons/trollvnc.plist",
    "/System/Library/LaunchDaemons/vphoned.plist",
    "/System/Library/LaunchDaemons/rpcserver_ios.plist",
]
missing = [key for key in required if key not in daemons]
if missing:
    raise SystemExit(f"rebuilt launchd cache missing {missing}")
print("rebuilt launchd cache has CFW daemons")
PY

echo "[+] CFW launchd cache repair complete."
echo "    Reboot normally. If launchd still panics, rerun full cfw_install_dev."
