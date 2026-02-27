# Session Progress: vphone Virtual iPhone Setup

**Date:** 2026-02-26
**Firmware base:** cloudOS 23B85 (PCC) + iOS 26.1 23B85 (iPhone17,3)
**Target platform:** VPHONE600AP / vresearch101ap
**Approach:** `wh1te4ever/super-tart-vphone` via `original-research/` directory

---

## Table of Contents

1. [Overview](#overview)
2. [Key Discoveries](#key-discoveries)
   - [Authoritative Reference Guide](#1-authoritative-reference-guide)
   - [pccvre VM Already Created](#2-pccvre-vm-already-created)
   - [NVRAM Overwrite Bug in vphone-cli](#3-nvram-overwrite-bug-in-vphone-cli)
   - [SEP Required for DFU USB Enumeration](#4-sep-required-for-dfu-usb-enumeration)
   - [Firmware Was Not Patched with Original patch_fw.py](#5-firmware-was-not-patched-with-original-patch_fwpy)
   - [Patches Applied by Original Research patch_fw.py](#6-patches-applied-by-original-research-patch_fwpy)
   - [AVPBooter Already Patched](#7-avpbooter-already-patched)
   - [SHSH Blob Obtained](#8-shsh-blob-obtained)
3. [Current State](#current-state)
4. [Approach Comparison: Lakr233 vs Original Research](#approach-comparison-lakr233-vs-original-research)
5. [Key Commands Reference](#key-commands-reference)
6. [Important File Locations](#important-file-locations)
7. [Next Steps](#next-steps)

---

## Overview

This session established a working DFU boot pipeline for a virtual iPhone using Apple's VPHONE600AP component from the PCC firmware. The goal is to restore a mixed iPhone + PCC firmware to the vphone VM, enabling a functional virtual iOS device.

The critical insight from this session is that the `original-research/super-tart-vphone/` directory contains `wh1te4ever`'s authoritative process, which differs in several important ways from the Lakr233 approach built into the repo's top-level scripts. The original research approach must be followed for this firmware combination.

---

## Key Discoveries

### 1. Authoritative Reference Guide

**Location:** `original-research/super-tart-vphone/GUIDE.md`

This is `wh1te4ever`'s actual step-by-step guide. It is distinct from both the Lakr233 `README.md` and the `AGENTS.md` documentation. Key differences the guide reveals:

- Uses `pccvre` (Apple's internal PCC research VM tool) to bootstrap a real `pcc-research` VM first
- Steals the initialized `AuxiliaryStorage` (nvram.bin) and `SEPStorage` from the pcc-research VM
- Uses `wh1te4ever`'s fork of super-tart directly (`.build/debug/tart run vphone --dfu`)
- Applies patches via `original-research/super-tart-vphone/CFW/patch_fw.py`, not the Lakr233 `patch_scripts/patch_fw.py`
- Uses `idevicerestore -e -y` (without `-T`) for restore, saving the SHSH as a gzip-compressed file

---

### 2. pccvre VM Already Created

The `pcc-research` VM was already created in a prior session using:

```bash
cd /System/Library/SecurityResearch/usr/bin
./pccvre release download --release 35622
./pccvre instance create -N pcc-research -R 35622 --variant research
```

**VM files at:**
```
~/Library/Application Support/com.apple.security-research.vrevm/VM-Library/pcc-research.vm/
```

| File | Size | Purpose |
|------|------|---------|
| `AuxiliaryStorage` | 33 MB | Properly initialized NVRAM for vresearch101 platform |
| `SEPStorage` | 512 KB | SEP coprocessor persistent storage |
| `Disk.img` | 64 GB | Full restored PCC rootfs |

These were copied to the vphone VM directory:
- `AuxiliaryStorage` -> `.tart/vms/vphone/nvram.bin`
- `SEPStorage` -> `.tart/vms/vphone/SEPStorage`

The `AuxiliaryStorage` file from a properly restored pcc-research VM contains platform-specific NVRAM variables (board ID, chip ID, ApNonce slot assignments) that the `VZMacAuxiliaryStorage` initializer cannot synthesize correctly for the vresearch101 platform. This is why creating the nvram.bin from scratch produces a VM that fails to enumerate the DFU USB device properly.

---

### 3. NVRAM Overwrite Bug in vphone-cli

**File:** `vphone-cli/Sources/vphone-cli/VPhoneVM.swift`

**Bug:** The original upstream `VPhoneVM.swift` called `VZMacAuxiliaryStorage(creatingStorageAt:hardwareModel:options:)` unconditionally with `.allowOverwrite` on every VM start. This destroyed the pcc-research-derived nvram.bin on each invocation.

**Fix applied this session:** Added an existence check so the existing file is used if present.

```swift
// Before (always overwrites):
platform.auxiliaryStorage = try VZMacAuxiliaryStorage(
    creatingStorageAt: options.nvramURL,
    hardwareModel: hwModel,
    options: .allowOverwrite
)

// After (preserves existing nvram.bin):
if FileManager.default.fileExists(atPath: options.nvramURL.path) {
    print("[vphone] Using existing NVRAM: \(options.nvramURL.path)")
    platform.auxiliaryStorage = VZMacAuxiliaryStorage(url: options.nvramURL)
} else {
    print("[vphone] Creating new NVRAM: \(options.nvramURL.path)")
    platform.auxiliaryStorage = try VZMacAuxiliaryStorage(
        creatingStorageAt: options.nvramURL,
        hardwareModel: hwModel,
        options: []
    )
}
```

**Rebuild required after this change:**
```bash
cd vphone-cli
bash build_and_sign.sh
```

**Important:** The VM may still corrupt nvram.bin during certain failure modes. It is safest to restore it from the pcc-research source before each DFU boot session. See the [Key Commands Reference](#key-commands-reference) section.

---

### 4. SEP Required for DFU USB Enumeration

**Finding:** The `--skip-sep` flag (which was the previous default) prevents the DFU USB device from appearing on the host.

| Mode | USB Device Visible | irecovery Output |
|------|--------------------|-----------------|
| `--skip-sep` | No | Times out / no device |
| `--sep-storage .tart/vms/vphone/SEPStorage` | Yes | CPID: 0xfe01, BDID: 0x90, MODE: DFU |

**Verified working output from `bin/irecovery -q`:**
```
CPID: 0xfe01, BDID: 0x90, MODE: DFU
PRODUCT: iPhone99,11, MODEL: vresearch101ap
```

The SEP coprocessor handles the USB DFU device enumeration in this platform configuration. Without a functional SEP, the DFU interface is not exposed to the host. The `SEPStorage` file from the pcc-research VM carries the initialized SEP state required for this.

The current `vm_boot_dfu.sh` script handles this automatically: it checks for `.tart/vms/vphone/SEPStorage` and passes `--sep-storage` if the file exists. However, note that the default SEP storage path in the script is `SEPStorage.img`, not `SEPStorage`. The explicit `--sep-storage` flag must be used when the file is named `SEPStorage`:

```bash
./vm_boot_dfu.sh vphone --sep-storage .tart/vms/vphone/SEPStorage
```

---

### 5. Firmware Was Not Patched with Original patch_fw.py

The mixed firmware directory `firmware-work/iPhone17,3_26.1_23B85_Restore_mixed/` had `.bak` files from a previous partial run, but the ApNonce patch was absent from iBSS.

**Root cause:** The Lakr233 `patch_scripts/patch_fw.py` (the repo top-level patching script) applies a different patch set than the original research `patch_fw.py`. The critical missing patch is the nonce fixation in iBSS.

**The nonce patch (`patch_fw.py` line 34):**
```python
# patch not to call generate_nonce; keep apnonce
patch(0x1b544, 0x1400000e)  # b #0x38
```

Without this patch, the ApNonce regenerates on every DFU boot cycle. A fresh nonce means previously saved SHSH blobs are invalid for restore, because the SHSH blob records the ApNonce that Apple's TSS server used when signing the personalized firmware manifest.

**Fix:** Ran `patch_fw.py` from `original-research/super-tart-vphone/CFW/`:
```bash
cd original-research/super-tart-vphone/CFW
python3 patch_fw.py
```

The `iPhone17,3_26.1_23B85_Restore` symlink in that directory points to `firmware-work/iPhone17,3_26.1_23B85_Restore_mixed/`, so the script patches the correct location.

---

### 6. Patches Applied by Original Research patch_fw.py

All patches are applied in-place to IM4P files inside `iPhone17,3_26.1_23B85_Restore/`. The script creates `.bak` files before modifying.

#### iBSS (`Firmware/dfu/iBSS.vresearch101.RELEASE.im4p`)

| Offset | Value | Purpose |
|--------|-------|---------|
| `0x9D10` | `0xD503201F` (NOP) | image4_validate_property_callback bypass (step 1) |
| `0x9D14` | `0xD2800000` (MOV X0,#0) | image4_validate_property_callback bypass (step 2, force return 0) |
| `0x1b544` | `0x1400000E` (B #0x38) | Skip `generate_nonce`, keep ApNonce fixed across reboots |

#### iBEC (`Firmware/dfu/iBEC.vresearch101.RELEASE.im4p`)

| Offset | Value | Purpose |
|--------|-------|---------|
| `0x9D10` | `0xD503201F` (NOP) | image4_validate_property_callback bypass (step 1) |
| `0x9D14` | `0xD2800000` (MOV X0,#0) | image4_validate_property_callback bypass (step 2) |
| `0x122d4` | `0xD0000082` (ADRP X2, #0x12000) | Boot-args override relocation (step 1) |
| `0x122d8` | `0x9101C042` (ADD X2, X2, #0x70) | Boot-args override relocation (step 2) |
| `0x24070` | `"serial=3 -v debug=0x2014e %s"` | Boot-args string payload |

#### LLB (`Firmware/all_flash/LLB.vresearch101.RESEARCH_RELEASE.im4p`)

| Offset | Value | Purpose |
|--------|-------|---------|
| `0xA0D8` | `0xD503201F` (NOP) | image4_validate_property_callback bypass (step 1) |
| `0xA0DC` | `0xD2800000` (MOV X0,#0) | image4_validate_property_callback bypass (step 2) |
| `0x12888` | `0xD0000082` | Boot-args override relocation (step 1) |
| `0x1288C` | `0x91264042` | Boot-args override relocation (step 2) |
| `0x24990` | `"serial=3 -v debug=0x2014e %s"` | Boot-args string payload |
| `0x2BFE8` | `0x1400000B` | SSV bypass (patch 1 of 5) |
| `0x2BCA0` | `0xD503201F` (NOP) | SSV bypass (patch 2 of 5) |
| `0x2C03C` | `0x17FFFF6A` | SSV bypass (patch 3 of 5) |
| `0x2FCEC` | `0xD503201F` (NOP) | SSV bypass (patch 4 of 5) |
| `0x2FEE8` | `0x14000009` | SSV bypass (patch 5 of 5) |
| `0x1AEE4` | `0xD503201F` (NOP) | Panic bypass |

#### TXM (`Firmware/txm.iphoneos.research.im4p`)

Extracted with `pyimg4`, patched as raw binary, repackaged with PAYP structure preserved.

Core trustcache bypass patches (enable running binaries not in trustcache):

| Offset (from base `0xFFFFFFF017004000`) | Virtual Address | Value | Purpose |
|--------|-----------------|-------|---------|
| `0x2C1F8` | `0xFFFFFFF0170301F8` | `0xD2800000` (MOV X0,#0) | Trustcache check bypass (1/3) |
| `0x2BEF4` | `0xFFFFFFF01702FEF4` | `0xD2800000` (MOV X0,#0) | Trustcache check bypass (2/3) |
| `0x2C060` | `0xFFFFFFF017030060` | `0xD2800000` (MOV X0,#0) | Trustcache check bypass (3/3) |

Additional jailbreak patches (get-task-allow, developer mode, debugger support) are also included.

#### Kernel (`kernelcache.research.vphone600`)

Extracted with `pyimg4`, patched as raw binary, repackaged with PAYP structure preserved.

Core SSV bypass patches (prevent boot panics on modified rootfs):

| Offset | Virtual Address | Value | Purpose |
|--------|-----------------|-------|---------|
| `0x2476964` | `0xFFFFFE000947A964` | `0xD503201F` (NOP) | `_apfs_vfsop_mount`: bypass "Failed to find root snapshot" panic |
| `0x23CFDE4` | `0xFFFFFE00093D3DE4` | `0xD503201F` (NOP) | `_authapfs_seal_is_broken`: bypass "root volume seal is broken" panic |
| `0xF6D960` | `0xFFFFFE0007F71960` | `0xD503201F` (NOP) | `_bsd_init`: bypass "rootvp not authenticated" panic |

Additional jailbreak patches (AMFIIsCDHashInTrustCache, launch constraints, credential hooks, syscall filter, kcall10 via SYS_kas_info, task_for_pid, VM protections) are also included.

**ARM64 patch constants used throughout:**
- NOP: `0xD503201F`
- MOV X0, #0: `0xD2800000`
- MOV W0, #0: `0x52800000`
- MOV W0, #1: `0x52800020`

---

### 7. AVPBooter Patch — FIXED

**File:** `.tart/vms/vphone/AVPBooter.vmapple2.bin`

A prior session had patched at `0x2C20` (wrong offset — that was a `RET` instruction, not `MOV X0, X20`). The correct `image4_validate_property_callback` was found via automated binary analysis and correctly patched.

#### How the function was found

The binary was analyzed programmatically:
1. Searched for ARM64 `CMP + B.NE + MOV X0,Xn + RETAB` epilogue patterns (stack-cookie check before return)
2. Filtered to candidates with 0 direct BL callers (called via function pointer = callbacks)
3. Found that `image4_validate_property_callback` at file offset `0x02308` (VA `0x102308`) is stored as a function pointer at file offset `0x2E3E8` in a callback registration table
4. Its epilogue at `0x02AD8–0x02B00` matches the guide's described pattern exactly

**Cross-confirmed via IDA** (`document-snippets/01-avpbooter-patching-gist.md`): The function contains `MOV W1, #0x44475354` (`'DGST'` tag) at file `0x02754` — this is the `"0x4447"` marker the guide/gist references. IDA output matches our binary exactly at those offsets.

#### Correct patch locations (our binary version)

```
Function: image4_validate_property_callback
  Start:    file:0x02308  VA:0x102308  (size: 0x7FC bytes)
  Stored:   file:0x2E3E8  (callback table entry)

Epilogue (stack cookie check before RETAB):
  file:0x02AD8  VA:0x102AD8  0xEB08013F  CMP X9, X8
  file:0x02ADC  VA:0x102ADC  0x540005E1  B.NE 0x102B98  -> PATCH 1: NOP (0xD503201F)
  file:0x02AE0  VA:0x102AE0  0xAA1403E0  MOV X0, X20   -> PATCH 2: MOV X0,#0 (0xD2800000)
  file:0x02AE4                           LDP ...
  ...
  file:0x02B00  VA:0x102B00  RETAB
```

Both patches have been applied to `.tart/vms/vphone/AVPBooter.vmapple2.bin`.

**Verification (run from repo root):**
```bash
python3 -c "
import struct
orig = open('/System/Library/Frameworks/Virtualization.framework/Versions/A/Resources/AVPBooter.vresearch1.bin','rb').read()
pat = open('.tart/vms/vphone/AVPBooter.vmapple2.bin','rb').read()
diffs = [(i, struct.unpack('<I',orig[i:i+4])[0], struct.unpack('<I',pat[i:i+4])[0])
         for i in range(0,len(orig)-3,4) if orig[i:i+4] != pat[i:i+4]]
for off, ov, pv in diffs:
    print(f'0x{off:05X}: 0x{ov:08X} -> 0x{pv:08X}')
"
```

**Expected output (exactly these 2 lines, nothing else):**
```
0x02ADC: 0x540005E1 -> 0xD503201F
0x02AE0: 0xAA1403E0 -> 0xD2800000
```

Meaning:
- `0x02ADC`: `B.NE 0x102B98` (stack-cookie-fail abort branch) → `NOP`
- `0x02AE0`: `MOV X0, X20` (return error code) → `MOV X0, #0` (always return success)

**Confirmed correct** — verified 2026-02-26.

---

### 8. SHSH Blob Obtained

With the nonce fixation patch in place (iBSS offset `0x1b544`), the ApNonce is now stable across DFU boot cycles.

**Fixed nonce (bytes):** `73 ca 02 5c 7f 4f 65 01 ...`

**SHSH blob saved at:**
```
original-research/super-tart-vphone/CFW/shsh/vphone.shsh
```

**ECID:** `9702785896832668844`

The SHSH blob contains Apple's TSS-signed personalization ticket for this specific ApNonce + ECID combination. It is required for restore because `idevicerestore` needs a valid personalized manifest to send to iBEC during the restore handshake.

---

## Current State

| Component | Status | Notes |
|-----------|--------|-------|
| DFU boot | Working | Requires SEP and correct nvram.bin |
| irecovery connection | Working | `CPID: 0xfe01, MODE: DFU` |
| AVPBooter patch | **FIXED** | Correct offsets 0x02ADC+0x02AE0 — see section 7 |
| iBSS/iBEC/LLB patches | Applied | Via original research `patch_fw.py` |
| TXM patches | Applied | PAYP structure preserved |
| Kernel patches | Applied | PAYP structure preserved |
| SHSH blob | Saved | `shsh/vphone.shsh`, nonce is fixed |
| Restore | **READY TO RETRY** | AVPBooter patch fixed — retry idevicerestore |

**Root cause of restore failure:** The AVPBooter patch is at the wrong offset for our binary version. The real `image4_validate_property_callback` is unpatched, so AVPBooter validates our patched iBSS, fails, and resets the USB device silently without transitioning to iBSS. The correct offset needs to be found via IDA Pro analysis of the actual binary from our macOS/VZ framework version.

---

## Approach Comparison: Lakr233 vs Original Research

Understanding which approach applies to which files is critical. These are two separate workflows present in the same repository.

| Aspect | Lakr233 (top-level) | Original Research (`original-research/`) |
|--------|--------------------|-----------------------------------------|
| VM tool | `vphone-cli` (new, Swift) | Modified `tart` binary directly |
| DFU launch | `./vm_boot_dfu.sh vphone` | `./.build/debug/tart run vphone --dfu` |
| SEP default | `--skip-sep` (wrong for DFU enumeration) | SEP enabled (required) |
| NVRAM source | Synthesized (wrong for vresearch101) | From pcc-research `AuxiliaryStorage` |
| Firmware patches | `patch_scripts/patch_fw.py` | `original-research/.../CFW/patch_fw.py` |
| TSS approach | Real TSS + `-T` ticket flag | `fake_tss_server.py` + pre-recorded response |
| SHSH format | Direct (not gzipped) | gzip-compressed (requires `gunzip`) |
| Firmware path | `firmwares/firmware_patched/` | `firmware-work/` (via symlink in CFW) |

For the current session's goal (restoring iOS 26.1 to a vphone VM), the original research workflow is the correct one. The Lakr233 top-level scripts reflect an attempt to generalize and automate the process, but they have not been fully reconciled with the pccvre-based NVRAM requirement.

---

## Key Commands Reference

### Start DFU VM (every session)

The nvram.bin must be restored from the pcc-research VM before starting, because the VM may corrupt it during failed boots or panics.

```bash
# Step 1: Restore nvram.bin from pcc-research source
cp ~/Library/Application\ Support/com.apple.security-research.vrevm/VM-Library/pcc-research.vm/AuxiliaryStorage \
    /Users/vinay/super-tart-vphone-writeup/external/Lakr233-super-tart-vphone-writeup/.tart/vms/vphone/nvram.bin

# Step 2: Start VM with SEP enabled (required for USB enumeration)
cd /Users/vinay/super-tart-vphone-writeup/external/Lakr233-super-tart-vphone-writeup
./vm_boot_dfu.sh vphone --sep-storage .tart/vms/vphone/SEPStorage
```

### Verify DFU Device

```bash
bin/irecovery -q
# Expected output:
# CPID: 0xfe01, BDID: 0x90, MODE: DFU
# PRODUCT: iPhone99,11, MODEL: vresearch101ap
```

### Save SHSH Blob (one-time, nonce is now fixed)

```bash
cd original-research/super-tart-vphone/CFW

# Save blob (idevicerestore -t only saves, does not restore)
../../../bin/idevicerestore -e -y ./iPhone17,3_26.1_23B85_Restore -t

# Rename to standard name
mv shsh/*-iPhone99,11-*.shsh shsh/vphone.shsh
```

Note: If the saved blob arrives as gzip-compressed data (as per the original guide), decompress first:
```bash
mv shsh/vphone.shsh shsh/vphone.shsh.gz
gunzip shsh/vphone.shsh.gz
```

### Restore Using Saved Ticket

```bash
cd original-research/super-tart-vphone/CFW

# Use -T to specify pre-saved SHSH ticket (avoids fresh TSS fetch with new nonce check)
../../../bin/idevicerestore -e -y -T shsh/vphone.shsh ./iPhone17,3_26.1_23B85_Restore
```

### Apply Firmware Patches

Only needed once. Script checks for `.bak` files and skips re-patching if already done.

```bash
cd original-research/super-tart-vphone/CFW
python3 patch_fw.py
```

The `iPhone17,3_26.1_23B85_Restore` entry in that directory is a symlink to the actual mixed firmware tree.

### Rebuild vphone-cli After Code Changes

```bash
cd /Users/vinay/super-tart-vphone-writeup/external/Lakr233-super-tart-vphone-writeup/vphone-cli
bash build_and_sign.sh
```

---

## Important File Locations

| File | Path | Notes |
|------|------|-------|
| vphone-cli VM config | `vphone-cli/Sources/vphone-cli/VPhoneVM.swift` | Modified this session: NVRAM existence check |
| VM NVRAM | `.tart/vms/vphone/nvram.bin` | Must be restored from pcc-research before each session |
| VM SEP storage | `.tart/vms/vphone/SEPStorage` | From pcc-research VM; required for DFU USB |
| VM ROM | `.tart/vms/vphone/AVPBooter.vmapple2.bin` | Patched: `0x2C20 = 0xD2800000` |
| Original-guide ROM (super-tart-vphone) | `.tart/vms/vphone/AVPBooter.vresearch1.bin` | Required by `original-research/super-tart-vphone` code path (`VMDirectory.romURL`) |
| Original-guide SEP ROM (super-tart-vphone) | `.tart/vms/vphone/AVPSEPBooter.vresearch1.bin` | Required by `original-research/super-tart-vphone` code path (`VMDirectory.sepromURL`) |
| NVRAM source | `~/Library/Application Support/com.apple.security-research.vrevm/VM-Library/pcc-research.vm/AuxiliaryStorage` | 33 MB, do not overwrite |
| SEP source | `~/Library/Application Support/com.apple.security-research.vrevm/VM-Library/pcc-research.vm/SEPStorage` | 512 KB |
| Firmware symlink | `original-research/super-tart-vphone/CFW/iPhone17,3_26.1_23B85_Restore` | Points to mixed+patched firmware |
| SHSH blob | `original-research/super-tart-vphone/CFW/shsh/vphone.shsh` | Saved; ECID 9702785896832668844 |
| Original patch script | `original-research/super-tart-vphone/CFW/patch_fw.py` | Authoritative for this firmware |
| Original guide | `original-research/super-tart-vphone/GUIDE.md` | wh1te4ever's step-by-step |
| Boot ramdisk script | `original-research/super-tart-vphone/CFW/boot_rd.sh` | Used after DFU VM is running |

---

## New Findings (2026-02-26)

### Confirmed Technical Findings

1. iBSS patch requirements are confirmed:
   - `0x9D10 = 0xD503201F`
   - `0x9D14 = 0xD2800000`
   - `0x1B544 = 0x1400000E` (keep nonce stable)

2. iBEC patch requirements are confirmed:
   - `0x9D10 = 0xD503201F`
   - `0x9D14 = 0xD2800000`
   - `0x122D4 = 0xD0000082`
   - `0x122D8 = 0x9101C042`
   - `0x24070 = "serial=3 -v debug=0x2014e %s\\0"`
   - `0x1B544` in iBEC should remain stock (`0x370801C8`)

3. `prepare_ramdisk.py` issues are fixed and validated:
   - SHSH parsing issue fixed by gzip magic-byte detection for `.shsh` files.
   - Step 4b stale `ramdisk1.dmg` handling added.
   - Step 4g resize permission fallback to `sudo` added.
   - End-to-end run completed successfully and produced full `Ramdisk/*.img4` set.

4. Current runtime behavior is consistent:
   - DFU starts correctly (`irecovery -q` reports `CPID: 0xfe01`, `PRODUCT: iPhone99,11`).
   - `vphone-cli` only shows startup/config logs during DFU stage.
   - This is expected; DFU handoff failures usually surface in `irecovery/idevicerestore`, not rich VM logs.

### Current Blocker

`iBSS` upload succeeds, but transition to `iBEC` fails:

- `patch_scripts/boot_rd.sh`
  - `[1/10] Loading iBSS...` success
  - `[2/10] Loading iBEC...` -> `ERROR: Unable to connect to device`
- `idevicerestore` path shows equivalent symptom:
  - `Device did not reconnect in recovery mode. Possibly invalid iBEC.`

This means we are failing at the DFU re-enumeration/handoff boundary.

### Evidence Snapshot

1. Ramdisk assets are ready in `Ramdisk/`:
   - `iBSS.vresearch101.RELEASE.img4`
   - `iBEC.vresearch101.RELEASE.img4`
   - `sptm.vresearch1.release.img4`
   - `txm.img4`
   - `trustcache.img4`
   - `ramdisk.img4`
   - `DeviceTree.vphone600ap.img4`
   - `sep-firmware.vresearch101.RELEASE.img4`
   - `krnl.img4`

2. DFU device is present before handoff:
   - vendor/product observed as Apple DFU (`0x05ac:0x1227`)
   - `irecovery -q` returns valid `iPhone99,11` DFU identity.

3. Active script caveat:
   - Current `patch_scripts/boot_rd.sh` in working tree is the simple send sequence.
   - Retry/wait helper logic is not currently present in that file state.

### Reset Procedure (for reconnect failures)

Use this whenever you see:
- `Unable to place device into recovery mode from DFU mode`
- `Unable to connect to device` after iBSS/iBEC

```bash
# stop current DFU runner
# (Ctrl+C in vm_boot_dfu.sh terminal)
pkill -f vphone-cli 2>/dev/null || true

# restart DFU VM
cd /Users/vinay/super-tart-vphone-writeup/external/Lakr233-super-tart-vphone-writeup
./vm_boot_dfu.sh vphone --sep-storage .tart/vms/vphone/SEPStorage

# verify DFU is back
bin/irecovery -q
```

### Next Attempt Order

1. Re-add and validate retry/wait logic in `patch_scripts/boot_rd.sh` against the current file state.
2. Run `boot_rd.sh` with extended timeout/retries and capture full output.
3. If still failing at iBEC handoff, continue AVPBooter offset validation in IDA for this exact binary build and re-test.
