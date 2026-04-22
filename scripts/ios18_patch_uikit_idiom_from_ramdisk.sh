#!/bin/zsh
# Patch copied SystemOS UIKitCore's idiom resolver from the SSH ramdisk.
set -euo pipefail

VM_DIR="${VM_DIR:-vm}"
SSH_PORT="${SSH_PORT:-2222}"
SSH_USER="${SSH_USER:-root}"
SSH_HOST="${SSH_HOST:-localhost}"
SSH_PASS="${SSH_PASS:-alpine}"
SSH_CONNECT_TIMEOUT="${SSH_CONNECT_TIMEOUT:-5}"
SSH_COMMAND_TIMEOUT="${SSH_COMMAND_TIMEOUT:-30}"
TEMP_DIR="${TEMP_DIR:-$VM_DIR/.ios18_uikit_idiom_patch}"
mkdir -p "$TEMP_DIR"

command -v sshpass >/dev/null 2>&1 || { echo "[-] sshpass is required" >&2; exit 1; }

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

scp_from() {
    sshpass -p "$SSH_PASS" scp -q "${SSH_OPTS[@]}" -P "$SSH_PORT" "$SSH_USER@$SSH_HOST:$1" "$2"
}

cache="/mnt1/System/Cryptexes/OS/System/Library/Caches/com.apple.dyld/dyld_shared_cache_arm64e.03"
offset=1726840 # 0x1a5978, _UIDeviceNativeUserInterfaceIdiomIgnoringClassic
expected="7f2303d5f44fbea9"
patched="000080d2c0035fd6" # mov x0,#0; ret
literal_bad="7830307830307838" # old broken printf writer: ASCII x00x00x8

read_remote_hex() {
    ssh_cmd "/bin/dd if='$cache' bs=1 skip=$offset count=8 2>/dev/null | /usr/bin/xxd -p" | tr -d '\r\n'
}

echo "[*] Waiting for ramdisk SSH on ${SSH_HOST}:${SSH_PORT}..."
ssh_cmd "echo ready" >/dev/null

echo "[*] Mounting System volume rw at /mnt1..."
ssh_cmd "/sbin/mount | /usr/bin/grep -q ' on /mnt1 ' || { /bin/mkdir -p /mnt1 && /sbin/mount_apfs -o rw /dev/disk1s1 /mnt1; }"

echo "[*] Checking UIKitCore idiom resolver bytes..."
current="$(read_remote_hex)"
if [[ "$current" == "$patched" ]]; then
    echo "[=] Already patched: $cache+$offset"
    exit 0
fi
if [[ "$current" == "$literal_bad" ]]; then
    echo "[!] Found old broken literal printf bytes; repairing in place"
elif [[ "$current" != "$expected" ]]; then
    echo "[-] Unexpected bytes at $cache+$offset: '$current' (expected $expected)" >&2
    exit 1
fi

echo "[*] Patching _UIDeviceNativeUserInterfaceIdiomIgnoringClassic -> mov x0,#0; ret..."
ssh_cmd "/usr/bin/printf '$patched' | /usr/bin/xxd -r -p | /bin/dd of='$cache' bs=1 seek=$offset conv=notrunc 2>/dev/null"
current="$(read_remote_hex)"
[[ "$current" == "$patched" ]] || { echo "[-] verification failed: got '$current'" >&2; exit 1; }

echo "[+] UIKitCore idiom resolver patched."
