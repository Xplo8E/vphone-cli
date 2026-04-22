#!/bin/zsh
# Collect offline SpringBoard/launchd state from the installed disk while the
# VM is booted into the SSH ramdisk.
set -euo pipefail

VM_DIR="${VM_DIR:-vm}"
SSH_PORT="${SSH_PORT:-2222}"
SSH_USER="${SSH_USER:-root}"
SSH_HOST="${SSH_HOST:-localhost}"
SSH_PASS="${SSH_PASS:-alpine}"
OUT_DIR="${OUT_DIR:-$VM_DIR/offline_ui_probe_$(date +%Y%m%d-%H%M%S)}"

command -v sshpass >/dev/null 2>&1 || {
    echo "[-] sshpass is required. Run make setup_tools if missing." >&2
    exit 1
}

mkdir -p "$OUT_DIR"/{raw,plist,logs}

SSH_OPTS=(
    -o StrictHostKeyChecking=no
    -o UserKnownHostsFile=/dev/null
    -o PreferredAuthentications=password
    -o ConnectTimeout=10
    -q
)

ssh_cmd() {
    sshpass -p "$SSH_PASS" ssh "${SSH_OPTS[@]}" -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" "$@"
}

scp_from() {
    local remote="$1" local_path="$2"
    sshpass -p "$SSH_PASS" scp -q "${SSH_OPTS[@]}" -P "$SSH_PORT" "$SSH_USER@$SSH_HOST:$remote" "$local_path"
}

copy_if_exists() {
    local remote="$1" name="$2"
    if ssh_cmd "test -e '$remote'"; then
        scp_from "$remote" "$OUT_DIR/raw/$name"
        if [[ "$name" == *.plist* ]]; then
            plutil -p "$OUT_DIR/raw/$name" >"$OUT_DIR/plist/$name.txt" 2>&1 || true
            plutil -convert xml1 -o "$OUT_DIR/plist/$name.xml" "$OUT_DIR/raw/$name" 2>/dev/null || true
        fi
    else
        echo "missing: $remote" >>"$OUT_DIR/logs/missing.txt"
    fi
}

echo "[*] Waiting for ramdisk SSH on ${SSH_HOST}:${SSH_PORT}..."
ssh_cmd "echo ready" >/dev/null

echo "[*] Mounting installed rootfs at /mnt1..."
ssh_cmd "/bin/mkdir -p /mnt1"
ssh_cmd "/sbin/mount | /usr/bin/grep -q ' on /mnt1 ' || /sbin/mount_apfs -o rw /dev/disk1s1 /mnt1"

echo "[*] Collecting launchd and UI plists..."
copy_if_exists "/mnt1/System/Library/xpc/launchd.plist" "launchd.plist"
copy_if_exists "/mnt1/System/Library/xpc/launchd.plist.bak" "launchd.plist.bak"
copy_if_exists "/mnt1/System/Library/LaunchDaemons/com.apple.SpringBoard.plist" "com.apple.SpringBoard.plist"
copy_if_exists "/mnt1/System/Library/LaunchDaemons/com.apple.backboardd.plist" "com.apple.backboardd.plist"
copy_if_exists "/mnt1/System/Library/LaunchDaemons/com.apple.runningboardd.plist" "com.apple.runningboardd.plist"
copy_if_exists "/mnt1/System/Library/LaunchDaemons/com.apple.mobileactivationd.plist" "com.apple.mobileactivationd.plist"
copy_if_exists "/mnt1/System/Library/LaunchDaemons/com.apple.purplebuddy.budd.plist" "com.apple.purplebuddy.budd.plist"
copy_if_exists "/mnt1/System/Library/LaunchDaemons/com.apple.MTLAssetUpgraderD.plist" "com.apple.MTLAssetUpgraderD.plist"
copy_if_exists "/mnt1/System/Library/CoreServices/SpringBoard.app/Info.plist" "SpringBoard.Info.plist"

echo "[*] Collecting filesystem facts..."
ssh_cmd "/bin/ls -la /mnt1/System/Library/LaunchDaemons | /usr/bin/grep -Ei 'spring|backboard|running|frontboard|buddy|setup|activation' || true" >"$OUT_DIR/logs/ui_launchdaemons.txt"
ssh_cmd "/bin/ls -la /mnt1/System/Library/CoreServices/SpringBoard.app || true" >"$OUT_DIR/logs/springboard_app_ls.txt"
ssh_cmd "snaputil -l /mnt1 2>/dev/null || true" >"$OUT_DIR/logs/snapshots.txt"
ssh_cmd "/usr/bin/find /mnt1/var/db -iname '*launch*' -o -iname '*disabled*' 2>/dev/null | /usr/bin/head -100 || true" >"$OUT_DIR/logs/var_db_launch_files.txt"

echo "[*] Host-side greps..."
for f in "$OUT_DIR"/raw/*; do
    [[ -f "$f" ]] || continue
    strings "$f" | grep -Ei 'SpringBoard|backboard|runningboard|frontboard|mobileactivation|buddy|setup|LimitLoad|Session|Disabled|MachServices|RunAtLoad|ProgramArguments' >"$OUT_DIR/logs/$(basename "$f").strings.ui.txt" 2>/dev/null || true
done

if [[ -f "$OUT_DIR/plist/launchd.plist.xml" && -f "$OUT_DIR/plist/launchd.plist.bak.xml" ]]; then
    diff -u "$OUT_DIR/plist/launchd.plist.bak.xml" "$OUT_DIR/plist/launchd.plist.xml" >"$OUT_DIR/logs/launchd_xml.diff" || true
fi

echo "[+] Offline UI probe complete: $OUT_DIR"
echo "    Review:"
echo "      $OUT_DIR/plist/com.apple.SpringBoard.plist.txt"
echo "      $OUT_DIR/logs/launchd.plist.strings.ui.txt"
echo "      $OUT_DIR/logs/launchd_xml.diff"
