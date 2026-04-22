#!/bin/zsh
# Patch the installed Data-volume MobileGestalt cache so UIKit maps the VM to
# UIUserInterfaceIdiomPhone. Run while booted into the SSH ramdisk.
set -euo pipefail

VM_DIR="${VM_DIR:-vm}"
SSH_PORT="${SSH_PORT:-2222}"
SSH_USER="${SSH_USER:-root}"
SSH_HOST="${SSH_HOST:-localhost}"
SSH_PASS="${SSH_PASS:-alpine}"
SSH_CONNECT_TIMEOUT="${SSH_CONNECT_TIMEOUT:-5}"
SSH_COMMAND_TIMEOUT="${SSH_COMMAND_TIMEOUT:-20}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PYTHON3="${PYTHON3:-$REPO_DIR/.venv/bin/python3}"
OUT_DIR="${OUT_DIR:-$VM_DIR/.ios18_mobilegestalt_patch/$(date +%Y%m%d-%H%M%S)}"

command -v sshpass >/dev/null 2>&1 || {
    echo "[-] sshpass is required. Run make setup_tools if missing." >&2
    exit 1
}

[[ -x "$PYTHON3" ]] || PYTHON3="python3"
mkdir -p "$OUT_DIR"

SSH_OPTS=(
    -o StrictHostKeyChecking=no
    -o UserKnownHostsFile=/dev/null
    -o PreferredAuthentications=password
    -o ConnectTimeout=$SSH_CONNECT_TIMEOUT
    -o ServerAliveInterval=2
    -o ServerAliveCountMax=3
)

retry() {
    local label="$1"
    shift
    local attempt rc
    for attempt in 1 2 3 4 5; do
        "$@" && return 0
        rc=$?
        if [[ "$rc" != "255" && "$rc" != "124" ]]; then
            echo "  [$label] command failed with rc=$rc (not retrying)" >&2
            return "$rc"
        fi
        echo "  [$label] command failed with rc=$rc (attempt $attempt/5), retrying in 3s..." >&2
        sleep 3
    done
    return 255
}

with_timeout() {
    local seconds="$1"
    shift
    /usr/bin/perl -e '$SIG{ALRM}=sub{exit 124}; alarm shift @ARGV; exec @ARGV or exit 127' "$seconds" "$@"
}

ssh_cmd_raw() {
    with_timeout "$SSH_COMMAND_TIMEOUT" sshpass -p "$SSH_PASS" ssh "${SSH_OPTS[@]}" -p "$SSH_PORT" "$SSH_USER@$SSH_HOST" "$@"
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

echo "[*] Probing ramdisk block devices..."
ssh_cmd "(/sbin/mount || true); echo --dev--; (/bin/ls -la /dev/disk1* 2>/dev/null || true)"

if [[ "${IOS18_MOBILEGESTALT_PROBE_ONLY:-0}" == "1" ]]; then
    echo "[+] Probe-only mode complete."
    exit 0
fi

MG_REL="containers/Shared/SystemGroup/systemgroup.com.apple.mobilegestaltcache/Library/Caches/com.apple.MobileGestalt.plist"
MG_MNT="/mnt2"
MG_CACHE="$MG_MNT/$MG_REL"

if [[ -n "${IOS18_DATA_DEV:-}" ]]; then
    CANDIDATE_DEVS=("$IOS18_DATA_DEV")
else
    CANDIDATE_DEVS=(/dev/disk1s2 /dev/disk1s6 /dev/disk1s5 /dev/disk1s4 /dev/disk1s3 /dev/disk1s1)
fi

found_dev=""
for dev in "${CANDIDATE_DEVS[@]}"; do
    echo "[*] Trying Data candidate $dev at $MG_MNT..."
    if ssh_cmd "/sbin/mount | /usr/bin/grep -q ' on $MG_MNT ' || { /bin/mkdir -p $MG_MNT && /sbin/mount_apfs -o rw $dev $MG_MNT; }"; then
        if ssh_cmd "test -f '$MG_CACHE'"; then
            found_dev="$dev"
            break
        fi
        ssh_cmd "/sbin/umount $MG_MNT 2>/dev/null || true"
    fi
    echo "  [!] $dev did not expose MobileGestalt cache" >&2
done

if [[ -z "$found_dev" ]]; then
    echo "[-] Could not locate MobileGestalt cache on any disk1s* candidate." >&2
    echo "    Run with IOS18_DATA_DEV=/dev/disk1sN if the Data role is known." >&2
    exit 1
fi

echo "[*] Using Data volume $found_dev"

echo "[*] Creating one-time backup on guest if missing..."
ssh_cmd "test -f '${MG_CACHE}.bak' || /bin/cp '$MG_CACHE' '${MG_CACHE}.bak'"

echo "[*] Patching CacheExtra.DeviceClassNumber..."
scp_from "${MG_CACHE}.bak" "$OUT_DIR/com.apple.MobileGestalt.original.plist"
cp "$OUT_DIR/com.apple.MobileGestalt.original.plist" "$OUT_DIR/com.apple.MobileGestalt.patched.plist"
"$PYTHON3" "$SCRIPT_DIR/patchers/cfw.py" patch-mobilegestalt "$OUT_DIR/com.apple.MobileGestalt.patched.plist"
scp_to "$OUT_DIR/com.apple.MobileGestalt.patched.plist" "$MG_CACHE"
ssh_cmd "/usr/sbin/chown mobile:mobile '$MG_CACHE' 2>/dev/null || /usr/sbin/chown 501:501 '$MG_CACHE' 2>/dev/null || true"
ssh_cmd "/bin/chmod 0644 '$MG_CACHE'"

echo "[*] Verifying installed cache..."
scp_from "$MG_CACHE" "$OUT_DIR/com.apple.MobileGestalt.installed.plist"
python3 - "$OUT_DIR/com.apple.MobileGestalt.installed.plist" <<'PY'
import plistlib
import sys

with open(sys.argv[1], "rb") as f:
    pl = plistlib.load(f)
value = pl.get("CacheExtra", {}).get("DeviceClassNumber")
if value != 1:
    raise SystemExit(f"DeviceClassNumber override missing, got {value!r}")
print("CacheExtra.DeviceClassNumber = 1")
PY

echo "[+] MobileGestalt UIKit idiom patch complete."
echo "    Reboot normally, or kill SpringBoard if testing from a live userspace shell."
