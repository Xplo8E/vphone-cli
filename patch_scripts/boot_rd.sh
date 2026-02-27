#!/bin/zsh
# boot_rd.sh - Load IMG4 firmware components into DFU VM via irecovery.
#
# Prerequisites:
#   - prepare_ramdisk.py must have been run (IMG4 files in Ramdisk/)
#   - VM must be in DFU mode (started with tart)
#   - irecovery must be available
#
# Usage:
#   ./boot_rd.sh [ramdisk_dir]
#
# The boot sequence loads components in order:
#   iBSS → iBEC → go → SPTM → TXM → trustcache → ramdisk →
#   devicetree → SEP → kernel → bootx
#
# After boot, use iproxy to connect:
#   iproxy 2222 22 &
#   ssh root@127.0.0.1 -p2222  (password: alpine)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
BIN_DIR="$REPO_ROOT/bin"

# Ramdisk directory (first arg or default)
RD_DIR="${1:-$REPO_ROOT/Ramdisk}"

# irecovery path
IRECOVERY="${IRECOVERY:-$BIN_DIR/irecovery}"
MAX_RETRIES="${MAX_RETRIES:-40}"
RETRY_SLEEP="${RETRY_SLEEP:-1}"
WAIT_TIMEOUT="${WAIT_TIMEOUT:-45}"
CMD_TIMEOUT="${CMD_TIMEOUT:-25}"
PROBE_TIMEOUT="${PROBE_TIMEOUT:-3}"
SLEEP_BIN="/bin/sleep"
PYTHON_BIN="${PYTHON_BIN:-$REPO_ROOT/.venv/bin/python3}"
PYIMG4_BIN="${PYIMG4_BIN:-$REPO_ROOT/.venv/bin/pyimg4}"
IM4M_PATH="${IM4M_PATH:-$REPO_ROOT/firmwares/firmware_patched/ramdisk_work/vphone.im4m}"

if [ ! -x "$IRECOVERY" ]; then
	echo "ERROR: irecovery not found at $IRECOVERY"
	exit 1
fi

if [ ! -x "$PYTHON_BIN" ]; then
	# Fallback to system python if local venv isn't available.
	PYTHON_BIN="$(command -v python3 || true)"
fi

if [ -z "$PYTHON_BIN" ] || [ ! -x "$PYTHON_BIN" ]; then
	echo "ERROR: python3 not found. Tried: $REPO_ROOT/.venv/bin/python3 and PATH lookup."
	echo "Set PYTHON_BIN=/path/to/python3 when running this script."
	exit 1
fi

if [ ! -d "$RD_DIR" ]; then
	echo "ERROR: Ramdisk directory not found: $RD_DIR"
	echo "Run prepare_ramdisk.py first."
	exit 1
fi

probe_device() {
	run_with_timeout "$PROBE_TIMEOUT" "$IRECOVERY" -q >/dev/null 2>&1
}

get_mode() {
	local out mode
	if out="$(run_with_timeout "$PROBE_TIMEOUT" "$IRECOVERY" -q 2>/dev/null)"; then
		mode="$(printf "%s\n" "$out" | awk -F': *' '/^MODE:/ {print $2; exit}')"
		printf "%s" "$mode"
		return 0
	fi
	return 1
}

wait_for_mode() {
	local target="$1"
	local timeout="${2:-$WAIT_TIMEOUT}"
	local elapsed=0
	local mode
	while [ "$elapsed" -lt "$timeout" ]; do
		if mode="$(get_mode)"; then
			if [ "$mode" = "$target" ]; then
				return 0
			fi
		fi
		"$SLEEP_BIN" "$RETRY_SLEEP"
		elapsed=$((elapsed + RETRY_SLEEP))
	done
	return 1
}

wait_for_device() {
	local timeout="${1:-$WAIT_TIMEOUT}"
	local elapsed=0
	while [ "$elapsed" -lt "$timeout" ]; do
		if probe_device; then
			return 0
		fi
		"$SLEEP_BIN" "$RETRY_SLEEP"
		elapsed=$((elapsed + RETRY_SLEEP))
	done
	return 1
}

wait_for_disconnect() {
	local timeout="${1:-$WAIT_TIMEOUT}"
	local elapsed=0
	while [ "$elapsed" -lt "$timeout" ]; do
		if ! probe_device; then
			return 0
		fi
		"$SLEEP_BIN" "$RETRY_SLEEP"
		elapsed=$((elapsed + RETRY_SLEEP))
	done
	return 1
}

run_with_timeout() {
	local timeout="$1"
	shift
	# Use Python timeout wrapper so command output is shown live on terminal.
	"$PYTHON_BIN" - "$timeout" "$@" <<'PY'
import subprocess
import sys

timeout = float(sys.argv[1])
cmd = sys.argv[2:]

try:
    proc = subprocess.Popen(cmd)
    rc = proc.wait(timeout=timeout)
    raise SystemExit(rc)
except subprocess.TimeoutExpired:
    try:
        proc.terminate()
        proc.wait(timeout=1)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass
    raise SystemExit(124)
PY
}

run_with_retry() {
	local label="$1"
	shift
	local attempt=1
	local rc=0
	while [ "$attempt" -le "$MAX_RETRIES" ]; do
		echo "  attempt $attempt/$MAX_RETRIES: $label"
		if run_with_timeout "$CMD_TIMEOUT" "$@"; then
			rc=0
		else
			rc=$?
		fi
		if [ "$rc" -eq 0 ]; then
			return 0
		fi
		if [ "$rc" -eq 124 ]; then
			echo "  timeout after ${CMD_TIMEOUT}s for $label"
		else
			echo "  failed rc=$rc for $label"
		fi
		echo "  retrying..."
		"$SLEEP_BIN" "$RETRY_SLEEP"
		attempt=$((attempt + 1))
	done
	echo "ERROR: failed after retries: $label"
	return 1
}

send_file() {
	local label="$1"
	local path="$2"
	echo "  waiting for USB device..."
	if ! wait_for_device "$WAIT_TIMEOUT"; then
		echo "ERROR: device not detected before sending $label"
		return 1
	fi
	run_with_retry "$label" "$IRECOVERY" -f "$path"
}

send_cmd() {
	local label="$1"
	local cmd="$2"
	echo "  waiting for USB device..."
	if ! wait_for_device "$WAIT_TIMEOUT"; then
		echo "ERROR: device not detected before command $label"
		return 1
	fi
	run_with_retry "$label" "$IRECOVERY" -c "$cmd"
}

get_live_nonce() {
	local out
	if out="$(run_with_timeout "$PROBE_TIMEOUT" "$IRECOVERY" -q 2>/dev/null)"; then
		printf "%s\n" "$out" | sed -n 's/^NONC: //p' | tr '[:upper:]' '[:lower:]'
		return 0
	fi
	return 1
}

get_im4m_nonce() {
	if [ ! -x "$PYIMG4_BIN" ] || [ ! -f "$IM4M_PATH" ]; then
		return 1
	fi
	"$PYIMG4_BIN" im4m info -i "$IM4M_PATH" 2>/dev/null \
		| sed -n 's/^[[:space:]]*ApNonce (hex): //p' \
		| tr '[:upper:]' '[:lower:]'
}

check_nonce_match() {
	local live_nonce im4m_nonce
	live_nonce="$(get_live_nonce || true)"
	im4m_nonce="$(get_im4m_nonce || true)"

	if [ -z "$live_nonce" ] || [ -z "$im4m_nonce" ]; then
		return 0
	fi

	echo "Preflight NONC check:"
	echo "  live NONC: $live_nonce"
	echo "  IM4M NONC: $im4m_nonce"

	if [ "$live_nonce" != "$im4m_nonce" ]; then
		echo "ERROR: NONC mismatch. Refusing to continue."
		echo "Fix:"
		echo "  1) keep current tart session running"
		echo "  2) rerun: python3 prepare_ramdisk.py"
		echo "  3) rerun: bash boot_rd.sh"
		return 1
	fi
	return 0
}

# Verify all required files exist
REQUIRED_FILES=(
	"iBSS.vresearch101.RELEASE.img4"
	"iBEC.vresearch101.RELEASE.img4"
	"sptm.vresearch1.release.img4"
	"txm.img4"
	"trustcache.img4"
	"ramdisk.img4"
	"DeviceTree.vphone600ap.img4"
	"sep-firmware.vresearch101.RELEASE.img4"
	"krnl.img4"
)

for f in "${REQUIRED_FILES[@]}"; do
	if [ ! -f "$RD_DIR/$f" ]; then
		echo "ERROR: Missing $RD_DIR/$f"
		exit 1
	fi
done

initial_mode="$(get_mode || true)"
if [ "$initial_mode" = "DFU" ]; then
	if ! check_nonce_match; then
		exit 1
	fi
elif [ -n "$initial_mode" ]; then
	echo "Preflight mode: $initial_mode"
	echo "  Skipping strict NONC precheck before iBSS."
	echo "  NONC will be validated after iBSS stage transition."
fi

echo "=== Loading firmware components into DFU VM ==="
echo "Ramdisk dir: $RD_DIR"
echo ""

# 1. iBSS (first-stage bootloader)
echo "[1/10] Loading iBSS..."
send_file "iBSS" "$RD_DIR/iBSS.vresearch101.RELEASE.img4"
echo "  waiting for iBSS stage transition..."
if wait_for_mode "Recovery" "$WAIT_TIMEOUT"; then
	echo "  recovery mode detected."
else
	if wait_for_disconnect "$WAIT_TIMEOUT"; then
		if ! wait_for_device "$WAIT_TIMEOUT"; then
			echo "ERROR: device did not reappear after iBSS"
			exit 1
		fi
	else
		echo "  no disconnect observed; continuing once device responds..."
		if ! wait_for_device "$WAIT_TIMEOUT"; then
			echo "ERROR: device not responding after iBSS"
			exit 1
		fi
	fi
fi

if ! check_nonce_match; then
	echo "ERROR: NONC mismatch after iBSS stage transition."
	echo "This indicates the current ticket does not match the active boot nonce."
	exit 1
fi

# 2. iBEC (second-stage bootloader)
echo "[2/10] Loading iBEC..."
send_file "iBEC" "$RD_DIR/iBEC.vresearch101.RELEASE.img4"

# 3. Execute bootloader
echo "[3/10] Executing bootloader (go)..."
send_cmd "go" "go"

echo "  waiting for post-go stage transition..."
if wait_for_mode "Recovery" "$WAIT_TIMEOUT"; then
	echo "  recovery mode detected after go."
else
	echo "  recovery mode not observed after go; proceeding when USB responds."
	if ! wait_for_device "$WAIT_TIMEOUT"; then
		echo "ERROR: device not responding after go"
		exit 1
	fi
fi

"$SLEEP_BIN" 1

# 4. SPTM (Secure Page Table Monitor)
echo "[4/10] Loading SPTM..."
send_file "SPTM" "$RD_DIR/sptm.vresearch1.release.img4"
send_cmd "firmware (SPTM)" "firmware"

# 5. TXM (Trustcache Manager)
echo "[5/10] Loading TXM..."
send_file "TXM" "$RD_DIR/txm.img4"
send_cmd "firmware (TXM)" "firmware"

# 6. Trustcache
echo "[6/10] Loading trustcache..."
send_file "trustcache" "$RD_DIR/trustcache.img4"
send_cmd "firmware (trustcache)" "firmware"

# 7. Ramdisk
echo "[7/10] Loading ramdisk..."
send_file "ramdisk" "$RD_DIR/ramdisk.img4"
send_cmd "ramdisk" "ramdisk"

# 8. Device Tree
echo "[8/10] Loading device tree..."
send_file "devicetree" "$RD_DIR/DeviceTree.vphone600ap.img4"
send_cmd "devicetree" "devicetree"

# 9. SEP firmware
echo "[9/10] Loading SEP firmware..."
send_file "SEP firmware" "$RD_DIR/sep-firmware.vresearch101.RELEASE.img4"
send_cmd "firmware (SEP)" "firmware"

# Validate nonce again right before kernel handoff.
if ! check_nonce_match; then
	echo "ERROR: NONC mismatch before kernel/bootx."
	echo "This commonly causes 'Memory image not valid' at bootx."
	exit 1
fi

# 10. Kernel (triggers boot)
echo "[10/10] Loading kernel and booting..."
send_file "kernel" "$RD_DIR/krnl.img4"
send_cmd "bootx" "bootx"

"$SLEEP_BIN" 2
if mode="$(get_mode)"; then
	echo "  post-boot USB mode: $mode"
	if [ "$mode" = "Recovery" ]; then
		echo "  WARNING: device is still in Recovery after bootx."
		echo "           If tart serial shows 'Kernelcache image not valid',"
		echo "           regenerate IMG4 in the same active DFU session:"
		echo "             1) keep tart running in DFU (do not restart it)"
		echo "             2) run prepare_ramdisk.py again"
		echo "             3) rerun boot_rd.sh"
	fi
fi

echo ""
echo "=== Boot sequence complete ==="
echo ""
echo "If you see the Creeper face in the VM window and 'iPhone Research...'"
echo "appears in System Information > USB, the ramdisk booted successfully."
echo ""
echo "To connect via SSH:"
echo "  iproxy 2222 22 &"
echo "  ssh root@127.0.0.1 -p2222"
echo "  (password: alpine)"
