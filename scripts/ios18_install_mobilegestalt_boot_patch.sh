#!/bin/zsh
# Install a one-shot normal-boot MobileGestalt patcher. Use this when the SSH
# ramdisk cannot mount the Data volume directly.
set -euo pipefail

VM_DIR="${VM_DIR:-vm}"
SSH_PORT="${SSH_PORT:-2222}"
SSH_USER="${SSH_USER:-root}"
SSH_HOST="${SSH_HOST:-localhost}"
SSH_PASS="${SSH_PASS:-alpine}"
SSH_CONNECT_TIMEOUT="${SSH_CONNECT_TIMEOUT:-5}"
SSH_COMMAND_TIMEOUT="${SSH_COMMAND_TIMEOUT:-30}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON3="${PYTHON3:-$REPO_DIR/.venv/bin/python3}"
MG_DIR="$SCRIPT_DIR/ios18_mgpatch"
TEMP_DIR="${TEMP_DIR:-$VM_DIR/.ios18_mgpatch_install}"

command -v sshpass >/dev/null 2>&1 || { echo "[-] sshpass is required" >&2; exit 1; }
command -v xcrun >/dev/null 2>&1 || { echo "[-] xcrun is required" >&2; exit 1; }
command -v ldid >/dev/null 2>&1 || { echo "[-] ldid is required" >&2; exit 1; }
[[ -x "$PYTHON3" ]] || PYTHON3="python3"
mkdir -p "$TEMP_DIR/LaunchDaemons"

SSH_OPTS=(
    -o StrictHostKeyChecking=no
    -o UserKnownHostsFile=/dev/null
    -o PreferredAuthentications=password
    -o ConnectTimeout=$SSH_CONNECT_TIMEOUT
    -o ServerAliveInterval=2
    -o ServerAliveCountMax=3
)

with_timeout() {
    local seconds="$1"
    shift
    /usr/bin/perl -e '$SIG{ALRM}=sub{exit 124}; alarm shift @ARGV; exec @ARGV or exit 127' "$seconds" "$@"
}

ssh_cmd() {
    with_timeout "$SSH_COMMAND_TIMEOUT" sshpass -p "$SSH_PASS" ssh "${SSH_OPTS[@]}" -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" "$@"
}

scp_to() {
    sshpass -p "$SSH_PASS" scp -q "${SSH_OPTS[@]}" -P "$SSH_PORT" "$1" "$SSH_USER@$SSH_HOST:$2"
}

scp_from() {
    sshpass -p "$SSH_PASS" scp -q "${SSH_OPTS[@]}" -P "$SSH_PORT" "$SSH_USER@$SSH_HOST:$1" "$2"
}

remote_file_exists() {
    ssh_cmd "test -f '$1'" >/dev/null 2>&1
}

echo "[*] Building vphone_mgpatch for arm64 iphoneos..."
xcrun -sdk iphoneos clang -arch arm64 -Os -fobjc-arc \
    -o "$TEMP_DIR/vphone_mgpatch" "$MG_DIR/vphone_mgpatch.m" \
    -framework Foundation
ldid -S"$SCRIPT_DIR/vphoned/entitlements.plist" -M "-K$SCRIPT_DIR/vphoned/signcert.p12" "$TEMP_DIR/vphone_mgpatch"
cp "$MG_DIR/vphone_mgpatch.plist" "$TEMP_DIR/LaunchDaemons/vphone_mgpatch.plist"

printf '[*] Waiting for ramdisk SSH on %s:%s...\n' "$SSH_HOST" "$SSH_PORT"
ssh_cmd "echo ready" >/dev/null

echo "[*] Mounting System volume rw at /mnt1..."
ssh_cmd "/sbin/mount | /usr/bin/grep -q ' on /mnt1 ' && /sbin/umount /mnt1 2>/dev/null || true"
ssh_cmd "/bin/mkdir -p /mnt1 && /sbin/mount_apfs -o rw /dev/disk1s1 /mnt1"

echo "[*] Installing boot-time MobileGestalt patcher..."
scp_to "$TEMP_DIR/vphone_mgpatch" "/mnt1/usr/bin/vphone_mgpatch"
ssh_cmd "/bin/chmod 0755 /mnt1/usr/bin/vphone_mgpatch"
scp_to "$TEMP_DIR/LaunchDaemons/vphone_mgpatch.plist" "/mnt1/System/Library/LaunchDaemons/vphone_mgpatch.plist"
ssh_cmd "/bin/chmod 0644 /mnt1/System/Library/LaunchDaemons/vphone_mgpatch.plist"

echo "[*] Injecting vphone_mgpatch into launchd cache..."
scp_from "/mnt1/System/Library/xpc/launchd.plist" "$TEMP_DIR/launchd.plist"
"$PYTHON3" "$SCRIPT_DIR/patchers/cfw.py" inject-daemons "$TEMP_DIR/launchd.plist" "$TEMP_DIR/LaunchDaemons"
scp_to "$TEMP_DIR/launchd.plist" "/mnt1/System/Library/xpc/launchd.plist"
ssh_cmd "/bin/chmod 0644 /mnt1/System/Library/xpc/launchd.plist"

if remote_file_exists "/mnt1/System/Library/xpc/launchd.plist.bak"; then
    echo "[*] Existing launchd.plist.bak kept unchanged."
fi

echo "[+] Boot-time MobileGestalt patch installed."
echo "    Boot normally, then check /private/var/root/.vphone_mobilegestalt_patched and /private/var/log/vphone_mgpatch.log."
