#!/bin/zsh
# Experimental iOS 18.5 UI bring-up patch.
#
# Runs while booted into the SSH ramdisk. It mounts the installed rootfs and
# removes SpringBoard load gates that can suppress the service on research /
# diagnostics-like hardware state.
#
# This experiment caused launchd to panic with "No service cache" after the
# binary launchd.plist was reserialized. Keep it opt-in so it is not rerun by
# accident.
set -euo pipefail

VM_DIR="${VM_DIR:-vm}"
SSH_PORT="${SSH_PORT:-2222}"
SSH_USER="${SSH_USER:-root}"
SSH_HOST="${SSH_HOST:-localhost}"
SSH_PASS="${SSH_PASS:-alpine}"
TEMP_DIR="${VM_DIR}/.ios18_ui_patch"

if [[ "${IOS18_ALLOW_UNSAFE_LAUNCHD_PLIST_PATCH:-0}" != "1" ]]; then
    echo "[-] Refusing to rewrite launchd.plist by default." >&2
    echo "    This experiment caused an iOS 18.5 launchd 'No service cache' panic." >&2
    echo "    To rerun intentionally: IOS18_ALLOW_UNSAFE_LAUNCHD_PLIST_PATCH=1 $0" >&2
    echo "    To recover: scripts/ios18_restore_springboard_load_backup.sh" >&2
    exit 2
fi

command -v sshpass >/dev/null 2>&1 || {
    echo "[-] sshpass is required. Run make setup_tools if missing." >&2
    exit 1
}

mkdir -p "$TEMP_DIR"

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

SPRINGBOARD_PLIST="/mnt1/System/Library/LaunchDaemons/com.apple.SpringBoard.plist"
LAUNCHD_PLIST="/mnt1/System/Library/xpc/launchd.plist"

echo "[*] Creating one-time backups on guest if missing..."
ssh_cmd "test -f ${SPRINGBOARD_PLIST}.ios18-ui-bak || /bin/cp ${SPRINGBOARD_PLIST} ${SPRINGBOARD_PLIST}.ios18-ui-bak"
ssh_cmd "test -f ${LAUNCHD_PLIST}.ios18-ui-bak || /bin/cp ${LAUNCHD_PLIST} ${LAUNCHD_PLIST}.ios18-ui-bak"

scp_from "$SPRINGBOARD_PLIST" "$TEMP_DIR/com.apple.SpringBoard.plist"
scp_from "$LAUNCHD_PLIST" "$TEMP_DIR/launchd.plist"

python3 - "$TEMP_DIR/com.apple.SpringBoard.plist" "$TEMP_DIR/launchd.plist" <<'PY'
import plistlib
import sys
from pathlib import Path

SPRINGBOARD_PATH = "/System/Library/LaunchDaemons/com.apple.SpringBoard.plist"
REMOVE_KEYS = ("_LimitLoadFromClarityMode", "LimitLoadFromHardware")

def remove_gates(d):
    removed = {}
    for key in REMOVE_KEYS:
        if key in d:
            removed[key] = d.pop(key)
    return removed

for path_s in sys.argv[1:]:
    path = Path(path_s)
    with path.open("rb") as f:
        obj = plistlib.load(f)

    if path.name == "launchd.plist":
        sb = obj.get("LaunchDaemons", {}).get(SPRINGBOARD_PATH)
        if not isinstance(sb, dict):
            raise SystemExit(f"SpringBoard entry not found in {path}")
        removed = remove_gates(sb)
    else:
        if not isinstance(obj, dict) or obj.get("Label") != "com.apple.SpringBoard":
            raise SystemExit(f"{path} is not the SpringBoard plist")
        removed = remove_gates(obj)

    if not removed:
        print(f"{path}: no gates removed")
    else:
        print(f"{path}: removed {removed}")

    with path.open("wb") as f:
        plistlib.dump(obj, f, fmt=plistlib.FMT_BINARY, sort_keys=False)
PY

echo "[*] Installing patched plists..."
scp_to "$TEMP_DIR/com.apple.SpringBoard.plist" "$SPRINGBOARD_PLIST"
scp_to "$TEMP_DIR/launchd.plist" "$LAUNCHD_PLIST"
ssh_cmd "/bin/chmod 0644 $SPRINGBOARD_PLIST $LAUNCHD_PLIST"

echo "[*] Verifying patched keys are absent..."
scp_from "$SPRINGBOARD_PLIST" "$TEMP_DIR/com.apple.SpringBoard.after.plist"
scp_from "$LAUNCHD_PLIST" "$TEMP_DIR/launchd.after.plist"
python3 - "$TEMP_DIR/com.apple.SpringBoard.after.plist" "$TEMP_DIR/launchd.after.plist" <<'PY'
import plistlib
import sys
from pathlib import Path

SPRINGBOARD_PATH = "/System/Library/LaunchDaemons/com.apple.SpringBoard.plist"
for path_s in sys.argv[1:]:
    path = Path(path_s)
    obj = plistlib.load(path.open("rb"))
    if path.name == "launchd.after.plist":
        obj = obj["LaunchDaemons"][SPRINGBOARD_PATH]
    remaining = [k for k in ("_LimitLoadFromClarityMode", "LimitLoadFromHardware") if k in obj]
    if remaining:
        raise SystemExit(f"{path}: still has {remaining}")
    print(f"{path}: SpringBoard load gates removed")
PY

echo "[+] SpringBoard load gate patch complete."
echo "    Reboot normally and check whether SpringBoard appears in ps/UI."
