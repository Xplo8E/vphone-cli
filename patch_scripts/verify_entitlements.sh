#!/bin/bash
#
# verify_entitlements.sh — Iterate over all known Virtualization-related entitlements,
# sign the dummy loader with each one, launch it, attach lldb to read the
# entitlement bitmap, and report results.
#
# Tests our 6 known bitmap entitlements + all entitlements from the XPC daemon.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SRC="$SCRIPT_DIR/verify_entitlements.c"
LLDB_SCRIPT="$SCRIPT_DIR/lldb_call_ent.py"
BIN="/tmp/verify_ent"

cleanup() { pkill -f verify_ent 2>/dev/null || true; }
trap cleanup EXIT

echo "=== Building verify_entitlements ==="
clang -O2 -o "$BIN" "$SRC" -arch arm64e -lobjc \
    -framework CoreFoundation -framework Virtualization
echo "Built: $BIN"
echo ""

# Launch process with given entitlements plist, attach lldb, return bitmap
read_bitmap() {
    local ent_plist="$1"

    pkill -f verify_ent 2>/dev/null || true
    sleep 0.3

    if [ "$ent_plist" = "NONE" ]; then
        codesign --force --sign - "$BIN" 2>/dev/null
    else
        codesign --force --sign - --entitlements "$ent_plist" "$BIN" 2>/dev/null
    fi

    "$BIN" > /dev/null 2>&1 &
    sleep 0.8

    local pid
    pid=$(pgrep -f verify_ent | head -1 || true)
    if [ -z "$pid" ]; then
        echo "CRASH"
        return
    fi

    local result
    result=$(lldb -p "$pid" --batch \
        -o "command script import $LLDB_SCRIPT" 2>&1 \
        | grep "^bitmap=" | head -1 | cut -d= -f2 || true)

    kill "$pid" 2>/dev/null || true
    wait "$pid" 2>/dev/null || true

    echo "${result:-FAILED}"
}

make_plist() {
    local plist="$1"
    shift
    {
        echo '<?xml version="1.0" encoding="UTF-8"?>'
        echo '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">'
        echo '<plist version="1.0">'
        echo '<dict>'
        for key in "$@"; do
            echo "  <key>${key}</key>"
            echo '  <true/>'
        done
        echo '</dict>'
        echo '</plist>'
    } > "$plist"
}

# ============================================================
# Test 1: Baseline
# ============================================================
echo "=== Test 1: No entitlements (baseline) ==="
BASELINE=$(read_bitmap "NONE")
echo "  bitmap = $BASELINE"
echo ""

# ============================================================
# Test 2: Known 6 bitmap entitlements (individually)
# ============================================================
KNOWN_ENTS=(
    "com.apple.security.virtualization"
    "com.apple.private.virtualization"
    "com.apple.vm.networking"
    "com.apple.private.ggdsw.GPUProcessProtectedContent"
    "com.apple.private.virtualization.security-research"
    "com.apple.private.virtualization.private-vsock"
)

echo "=== Test 2: Known 6 bitmap entitlements (individually) ==="
printf "  %-60s %s\n" "Entitlement" "Bitmap"
printf "  %-60s %s\n" "$(printf '%.0s-' {1..60})" "------"

for i in "${!KNOWN_ENTS[@]}"; do
    ent="${KNOWN_ENTS[$i]}"
    plist="/tmp/ent_known_${i}.plist"
    make_plist "$plist" "$ent"
    result=$(read_bitmap "$plist")
    printf "  %-60s %s\n" "$ent" "$result"
done

echo ""

# ============================================================
# Test 3: Cumulative (add one by one)
# ============================================================
echo "=== Test 3: Cumulative (add entitlements one by one) ==="
printf "  %-4s %-60s %s\n" "#" "Added Entitlement" "Bitmap"
printf "  %-4s %-60s %s\n" "----" "$(printf '%.0s-' {1..60})" "------"

for n in $(seq 1 ${#KNOWN_ENTS[@]}); do
    plist="/tmp/ent_cumul_${n}.plist"
    make_plist "$plist" "${KNOWN_ENTS[@]:0:$n}"
    result=$(read_bitmap "$plist")
    printf "  %-4s %-60s %s\n" "$n" "${KNOWN_ENTS[$((n-1))]}" "$result"
done

echo ""

# ============================================================
# Test 4: All entitlements from XPC daemon
# (ones not already in the 6 known set)
# ============================================================
XPC_ENTS=(
    "com.apple.ane.iokit-user-access"
    "com.apple.aned.private.adapterWeight.allow"
    "com.apple.aned.private.allow"
    "com.apple.developer.kernel.increased-memory-limit"
    "com.apple.private.AppleVirtualPlatformIdentity"
    "com.apple.private.FairPlayIOKitUserClient.Virtual.access"
    "com.apple.private.PCIPassthrough.access"
    "com.apple.private.ane.privileged-vm-client"
    "com.apple.private.apfs.no-padding"
    "com.apple.private.biometrickit.allow-match"
    "com.apple.private.fpsd.client"
    "com.apple.private.hypervisor"
    "com.apple.private.proreshw"
    "com.apple.private.security.message-filter"
    "com.apple.private.system-keychain"
    "com.apple.private.vfs.open-by-id"
    "com.apple.private.virtualization.linux-gpu-support"
    "com.apple.private.virtualization.plugin-loader"
    "com.apple.private.xpc.domain-extension"
    "com.apple.security.hardened-process"
    "com.apple.security.hypervisor"
    "com.apple.usb.hostcontrollerinterface"
)

echo "=== Test 4: XPC daemon entitlements (not in known 6) ==="
printf "  %-60s %s\n" "Entitlement" "Bitmap"
printf "  %-60s %s\n" "$(printf '%.0s-' {1..60})" "------"

for i in "${!XPC_ENTS[@]}"; do
    ent="${XPC_ENTS[$i]}"
    plist="/tmp/ent_xpc_${i}.plist"
    make_plist "$plist" "$ent"
    result=$(read_bitmap "$plist")
    printf "  %-60s %s\n" "$ent" "$result"
done

echo ""

# ============================================================
# Test 5: Strings from Virtualization.framework binary
# (entitlement-like strings found by IDA regex)
# ============================================================
EXTRA_ENTS=(
    "com.apple.private.virtualization.linux-gpu-support"
    "com.apple.private.virtualization.plugin-loader"
    "com.apple.security.hypervisor"
    "com.apple.private.hypervisor"
)

echo "=== Test 5: Additional entitlement-like strings from binary ==="
printf "  %-60s %s\n" "Entitlement" "Bitmap"
printf "  %-60s %s\n" "$(printf '%.0s-' {1..60})" "------"

for i in "${!EXTRA_ENTS[@]}"; do
    ent="${EXTRA_ENTS[$i]}"
    plist="/tmp/ent_extra_${i}.plist"
    make_plist "$plist" "$ent"
    result=$(read_bitmap "$plist")
    printf "  %-60s %s\n" "$ent" "$result"
done

echo ""

# ============================================================
# Test 6: All 6 known + all XPC daemon ents combined
# ============================================================
echo "=== Test 6: All entitlements combined ==="
ALL_ENTS=("${KNOWN_ENTS[@]}" "${XPC_ENTS[@]}")
plist="/tmp/ent_everything.plist"
make_plist "$plist" "${ALL_ENTS[@]}"
result=$(read_bitmap "$plist")
echo "  bitmap = $result"

echo ""
echo "=== Done ==="
