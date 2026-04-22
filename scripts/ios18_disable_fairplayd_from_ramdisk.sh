#!/bin/zsh
# Disable fairplayd LaunchDaemons on the installed System volume from the SSH ramdisk.
#
# Why: On vresearch101ap, fairplayd.H2 crashes near-instantly on SEP
# key operations (AKS sel 35 e00002f0), launchd throttles it, and consumers
# block turnstile-waiting on `com.apple.fairplayd.versioned`. This cascades
# to locationd (CLHarvestControllerSilo) and datamigrator's
# CoreLocationMigrator plugin, which deadlocks the 100% boot-progress stage.
#
# Disabling the LaunchDaemons makes clients' port lookups fail fast instead
# of blocking. The binaries themselves stay on disk unchanged; only the
# launchd plist filenames are changed from *.plist to *.plist.disabled so
# launchd skips them at load time.
set -euo pipefail

VM_DIR="${VM_DIR:-vm}"
SSH_PORT="${SSH_PORT:-2222}"
SSH_USER="${SSH_USER:-root}"
SSH_HOST="${SSH_HOST:-localhost}"
SSH_PASS="${SSH_PASS:-alpine}"
SSH_CONNECT_TIMEOUT="${SSH_CONNECT_TIMEOUT:-5}"
SSH_COMMAND_TIMEOUT="${SSH_COMMAND_TIMEOUT:-30}"

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

daemons=(
    /mnt1/System/Library/LaunchDaemons/com.apple.fairplayd.H2.plist
    /mnt1/System/Library/LaunchDaemons/com.apple.fairplaydeviceidentityd.plist
)

# The SSH ramdisk has no /bin/test binary (test is a shell builtin only).
# We use ls/stat to check for file existence instead.
remote_file_exists() {
    ssh_cmd "ls '$1' >/dev/null 2>&1"
}

echo "[*] Waiting for ramdisk SSH on ${SSH_HOST}:${SSH_PORT}..."
ssh_cmd "echo ready" >/dev/null

echo "[*] Mounting System volume rw at /mnt1..."
ssh_cmd "/sbin/mount | /usr/bin/grep -q ' on /mnt1 ' || { mkdir -p /mnt1 && /sbin/mount_apfs -o rw /dev/disk1s1 /mnt1; }"

for plist in "${daemons[@]}"; do
    disabled="${plist}.disabled"
    bak="${plist}.vphone_bak"
    if remote_file_exists "$disabled"; then
        echo "[=] Already disabled: $plist"
        continue
    fi
    if ! remote_file_exists "$plist"; then
        echo "[!] Not present (skipping): $plist"
        continue
    fi
    # Keep a one-time pristine copy as .vphone_bak so re-runs are safe and we
    # can always revert by renaming .disabled back to .plist.
    if ! remote_file_exists "$bak"; then
        ssh_cmd "cp '$plist' '$bak'"
    fi
    ssh_cmd "mv '$plist' '$disabled'"
    echo "[+] Disabled: $plist -> $disabled"
done

echo "[+] fairplayd LaunchDaemons disabled (launchd will skip them on next boot)."
