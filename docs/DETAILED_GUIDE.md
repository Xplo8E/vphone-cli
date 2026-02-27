# Detailed Guide: super-tart vphone600ap (Reconciled Workflow)

This guide is a script-accurate, end-to-end workflow built from:

- `README.md` (current repo quickstart)
- `document-snippets/*.md` (patching references)
- `original-research/super-tart-vphone/GUIDE.md` (primary source)
- Current executable scripts (`setup_*.sh`, `patch_scripts/*.py`, `patch_scripts/boot_rd.sh`, `vm_boot_dfu.sh`)

It is written for the firmware pair used across this repo:

- iPhone IPSW: `iPhone17,3_26.1_23B85_Restore.ipsw`
- PCC IPSW: `pcc_os_23B85.ipsw`

## 1. Host Prerequisites

Platform assumptions:

- Apple Silicon Mac
- macOS with SIP/AMFI disabled for private Virtualization.framework APIs

From the original research flow (Recovery Mode):

```bash
csrutil disable
nvram amfi_get_out_of_my_way=1
csrutil allow-research-guests enable
```

Install base dependencies:

```bash
brew install automake autoconf libtool pkg-config \
  libplist openssl@3 libimobiledevice-glue libimobiledevice libtatsu libzip \
  ldid sshpass gnu-tar
```

Also ensure: `git make clang swift python3 curl unzip`.

## 2. Build Toolchain and Environment

From repo root:

```bash
bash setup_bin.sh
source setup_env.sh
```

`setup_bin.sh` builds and stages to `bin/`:

- `img4`, `img4tool`, `trustcache`
- `irecovery`, `idevicerestore`
- `tart`
- `ldid`, `sshpass`, `gtar` (copied from host installs)

Build and sign `vphone-cli` (required by `vm_boot_dfu.sh`):

```bash
cd vphone-cli
bash build_and_sign.sh
cd ..
```

## 3. Download and Mix Firmware

```bash
bash setup_download_fw.sh
```

This script:

- Downloads both IPSWs from Apple CDN
- Extracts them into `firmwares/`
- Mixes PCC bootchain components into iPhone restore directory
- Installs repo `contents/BuildManifest.plist` and `contents/Restore.plist`

Resulting mixed restore directory:

`firmwares/firmware_patched/iPhone17,3_26.1_23B85_Restore`

## 4. Patch Bootchain and Kernel Components

```bash
cd patch_scripts
python3 patch_fw.py -d ../firmwares/firmware_patched/iPhone17,3_26.1_23B85_Restore
cd ..
```

Patched components:

- `iBSS` (signature bypass + APNonce-preserve patch to keep nonce stable across stage transitions)
- `iBEC`, `LLB` (signature bypass + boot args + SSV/rootfs bypass where applicable)
- `TXM` (trustcache checks bypassed)
- `kernelcache.research.vphone600` (SSV panic bypasses)
- `AVPBooter.vresearch1.bin` copied from host framework and patched to `bin/`

Useful verification modes:

```bash
python3 patch_scripts/patch_fw.py -d <restore_dir> --verify-only
python3 patch_scripts/patch_fw.py -d <restore_dir> --dry-run
```

Original-research baseline (`original-research/super-tart-vphone/CFW/patch_fw.py`) is broader than the cleaned script above:

- iBSS:
  - Signature bypass (`image4_validate_property_callback`)
  - Logging string edits (`Loaded iBSS`)
  - APNonce-preserve patch (skip `generate_nonce`)
- iBEC:
  - Signature bypass
  - Logging string edits (`Loaded iBEC`)
  - Boot-args redirection to `serial=3 -v debug=0x2014e %s`
- LLB:
  - Signature bypass
  - Logging string edits (`Loaded LLB`)
  - Boot-args redirection
  - SSV/rootfs bypasses and panic bypass
- TXM:
  - Trustcache bypass (3 core patches)
  - Additional jailbreak/developer/debug-oriented patches
- kernel:
  - 3 core SSV panic bypasses
  - Large set of additional jailbreak-oriented AMFI/sandbox/hook/syscall patches

Important difference: original `CFW/patch_fw.py` does not patch AVPBooter in that script; AVPBooter is handled separately (manual IDA patch in GUIDE, or `CFW/patch_avpbooter.py`).

## 5. Prepare VM Assets (Critical)

`vm_boot_dfu.sh` expects a prepared VM directory at:

`$TART_HOME/vms/vphone`

Required files:

- `AVPBooter.vresearch1.bin`
- `disk.img`
- `nvram.bin`
- `AVPSEPBooter.vresearch1.bin` (recommended)
- SEP storage file (optional but recommended)

You can satisfy this in two ways:

1. Use an existing working `vphone` VM (checkpoint/local setup).
2. Follow the original-research method to seed files from a `pccvre` VM and copy into tart VM storage.

Original-research tart selection and patching model:

- The runtime tart is `wh1te4ever/super-tart-vphone` (not stock tart).
- In original flow, JJTech `super-tart` is used only once to create a placeholder VM directory.
- `super-tart-vphone` is then built/signed via:

```bash
./scripts/run-signed.sh
```

Its `Sources/tart/VM.swift` hardwires vphone-specific private API behavior:

- `_setROMURL(...)` boot ROM override
- `_VZSEPCoprocessorConfiguration` + `_setCoprocessors(...)`
- `_VZMacHardwareModelDescriptor` with vphone/vresearch model values
- Production mode + fixed machine identifier/ECID path
- vphone display geometry (`1179x2556@460`)
- USB keyboard + USB touchscreen private config
- Debug stub and PL011 serial wiring
- `tart run ... --dfu` wired into VM start options (`forceDFU`)

Original-research run command for DFU:

```bash
./.build/debug/tart run vphone --dfu
```

Original-research provisioning sequence (manual, one-time):

```bash
# Create PCC research VM (Apple SecurityResearch tools)
cd /System/Library/SecurityResearch/usr/bin
./pccvre release download --release 35622
./pccvre instance create -N pcc-research -R 35622 --variant research

# Create placeholder vphone VM with super-tart (any restore IPSW is fine here)
git clone --recursive https://github.com/JJTech0130/super-tart
cd super-tart
./scripts/run-signed.sh
./.build/debug/tart create vphone --disk-size 32 --from-ipsw /path/to/UniversalMac_*.ipsw
```

Copy over PCC VM artifacts into the tart `vphone` VM directory:

```bash
cp ~/Library/Application\ Support/com.apple.security-research.vrevm/VM-Library/pcc-research.vm/config.plist .tart/vms/vphone/config.plist
cp ~/Library/Application\ Support/com.apple.security-research.vrevm/VM-Library/pcc-research.vm/Disk.img .tart/vms/vphone/disk.img
cp ~/Library/Application\ Support/com.apple.security-research.vrevm/VM-Library/pcc-research.vm/AuxiliaryStorage .tart/vms/vphone/nvram.bin
cp ~/Library/Application\ Support/com.apple.security-research.vrevm/VM-Library/pcc-research.vm/SEPStorage .tart/vms/vphone/SEPStorage
cp /System/Library/Frameworks/Virtualization.framework/Versions/A/Resources/AVPBooter.vresearch1.bin .tart/vms/vphone/AVPBooter.vresearch1.bin
cp /System/Library/Frameworks/Virtualization.framework/Versions/A/Resources/AVPSEPBooter.vresearch1.bin .tart/vms/vphone/AVPSEPBooter.vresearch1.bin
```

If you use repo helper `setup_vm.sh`, validate filenames afterward because runtime scripts expect `AVPBooter.vresearch1.bin` and may look for SEP storage under a different name.

### AVPBooter source choice (Desktop vs system)

Yes, using an already patched Desktop AVPBooter is okay if it matches the binary variant expected by your VM/runtime.

In this workspace, two AVPBooter variants exist:

- system/source-style: `233,368` bytes (`/System/.../AVPBooter.vresearch1.bin`)
- Desktop/vm-style: `251,856` bytes (`~/Desktop/AVPBooter.vresearch1.bin`)

Your Desktop file currently matches `.tart/vms/vphone/AVPBooter.vresearch1.bin` exactly (same SHA-256), so it is safe to use for that VM.

Recommended verification before using any prepatched AVPBooter:

```bash
shasum -a 256 ~/Desktop/AVPBooter.vresearch1.bin .tart/vms/vphone/AVPBooter.vresearch1.bin
```

And verify expected patched instructions for your variant:

- Desktop/vm variant (from GUIDE screenshots): `0x2C1C = NOP`, `0x2C20 = MOV X0,#0`
- System/source variant (patch script style): `0x2ADC = NOP`, `0x2AE0 = MOV X0,#0`

Do not mix offset sets across variants.

### tart-only DFU (no vphone-cli)

What we found:

1. Current repo `bin/tart` (`oems/super-tart`) requires `VPHONE_MODE=1` to enter vphone config path.
2. Current repo `bin/tart` expects ROM file `AVPBooter.vmapple2.bin` in VM dir.
3. Current repo `bin/tart` does not configure SEP coprocessor like original research tart did.
4. Original-research tart (`original-research/super-tart-vphone`) expects `AVPBooter.vresearch1.bin` and `AVPSEPBooter.vresearch1.bin`, and configures SEP coprocessor in VM config.

If you want tart-only with behavior closest to original research (recommended), build and run original-research tart:

```bash
cd original-research/super-tart-vphone

spm_root="$PWD/.swiftpm"
spm_home="$PWD/.swift-home"
mkdir -p "$spm_root/config" "$spm_root/security" "$spm_root/cache" "$spm_root/xdg-cache" "$spm_home"

SWIFTPM_CONFIG_PATH="$spm_root/config" \
SWIFTPM_SECURITY_PATH="$spm_root/security" \
SWIFTPM_CACHE_PATH="$spm_root/cache" \
XDG_CACHE_HOME="$spm_root/xdg-cache" \
HOME="$spm_home" \
swift build -c release --disable-sandbox --product tart

codesign --force --sign - --entitlements Resources/tart-prod.entitlements .build/release/tart
codesign -d --entitlements - .build/release/tart
```

Run command (force DFU, tart-only):

```bash
REPO="$(cd ../.. && pwd)"
export TART_HOME="$REPO/.tart"

ls -lh "$TART_HOME/vms/vphone"/AVPBooter.vresearch1.bin \
       "$TART_HOME/vms/vphone"/AVPSEPBooter.vresearch1.bin \
       "$TART_HOME/vms/vphone"/disk.img \
       "$TART_HOME/vms/vphone"/nvram.bin

"$REPO/bin/tart" run vphone --dfu --serial
```

If you see `Failed to open auxiliary storage` and logs mention paths under `~/.tart/vms/vphone`, use this compatibility shim first (original-research `VM.swift` hardcodes Home-based `nvram.bin` and `SEPStorage` paths):

```bash
REPO="/Users/vinay/super-tart-vphone-writeup/external/Lakr233-super-tart-vphone-writeup"
export TART_HOME="$REPO/.tart"

mkdir -p "$HOME/.tart/vms"
ln -sfn "$TART_HOME/vms/vphone" "$HOME/.tart/vms/vphone"

"$REPO/bin/tart" run vphone --dfu --serial
```

If you must use current repo `bin/tart`:

```bash
export TART_HOME="$PWD/.tart"
ln -sf AVPBooter.vresearch1.bin "$TART_HOME/vms/vphone/AVPBooter.vmapple2.bin"
VPHONE_MODE=1 "$PWD/bin/tart" run vphone --dfu --serial
```

Note: this current `bin/tart` path is DFU-capable but does not replicate original SEP-coprocessor behavior.

Quick check:

```bash
ls -lh "$TART_HOME/vms/vphone"
```

## 6. Enter DFU Mode

Start DFU VM in one terminal and keep it running:

```bash
./vm_boot_dfu.sh vphone --serial
```

Notes:

- `vm_boot_dfu.sh` uses `vphone-cli` and passes ROM/disk/nvram automatically.
- If SEP files are present and named as expected, they are passed too.
- If you need custom SEP args, pass through flags supported by `vphone-cli`.

## 7. Build Signed IMG4 + SSH Ramdisk

In another terminal:

```bash
cd patch_scripts
python3 prepare_ramdisk.py
cd ..
```

What it does:

1. Fetches SHSH (`idevicerestore -t`) from DFU device
2. Extracts IM4M ticket
3. Signs patched firmware pieces to `.img4`
4. Builds enlarged SSH ramdisk
5. Builds ramdisk trustcache
6. Outputs final images under `Ramdisk/`

Important session rule:

- `prepare_ramdisk.py` personalizes IMG4 files for the currently connected DFU session (SHSH/IM4M derived from device nonces).
- If you restart tart/VM between `prepare_ramdisk.py` and `boot_rd.sh`, previously generated `Ramdisk/*.img4` may become invalid for the new session.
- Symptom in tart serial: `Kernelcache image not valid`.
- Fix: keep the same tart DFU session alive, rerun `prepare_ramdisk.py`, then immediately rerun `boot_rd.sh`.
- Script behavior now avoids stale artifacts:
  - old `ramdisk_work/shsh/*.shsh*` are removed before ticket fetch
  - newest fetched SHSH is selected deterministically
  - kernel IMG4 is built from an `rkrn` IM4P (matching original `CFW/get_rd.py` behavior), with PAYP preservation before signing

If reusing a previously extracted IM4M:

```bash
python3 patch_scripts/prepare_ramdisk.py --skip-shsh --im4m /path/to/vphone.im4m
```

## 8. Boot SSH Ramdisk via DFU

```bash
cd patch_scripts
bash boot_rd.sh
```

This sends, in order:

`iBSS -> iBEC -> go -> sptm -> txm -> trustcache -> ramdisk -> devicetree -> sep -> kernel -> bootx`

After boot:

```bash
iproxy 2222 22 &
ssh root@127.0.0.1 -p2222
# password: alpine
```

### Known Failure: `Kernelcache image not valid`

Root cause observed during tart-only bring-up:

- `boot_rd.sh` can complete all sends but still return to Recovery if ticket/boot context is inconsistent.
- Most common causes were:
  - stale SHSH/IM4M reused from a previous run
  - kernel payload built with an incompatible IM4P type path for this flow

Current scripts now mitigate this:

- `boot_rd.sh` validates NONC against `vphone.im4m` (and re-checks after iBSS transition).
- `prepare_ramdisk.py` always fetches fresh SHSH cleanly and builds kernel through `rkrn` path.

Validated working sequence:

```bash
# Terminal 1 (keep running)
REPO="/Users/vinay/super-tart-vphone-writeup/external/Lakr233-super-tart-vphone-writeup"
"$REPO/bin/tart" run vphone --dfu --serial
```

```bash
# Terminal 2
cd "$REPO/patch_scripts"
python3 prepare_ramdisk.py
bash boot_rd.sh
iproxy 2222 22 &
ssh root@127.0.0.1 -p2222
# password: alpine
```

## 9. Rootfs Setup (Cryptex + Daemons + Patches)

Before running, provide required jailbreak payloads (at minimum):

- `jb/iosbinpack64.tar`
- optional/custom `jb/LaunchDaemons/*.plist` (script can generate defaults for bash/dropbear)

Then run:

```bash
cd patch_scripts
python3 setup_rootfs.py -d ../firmwares/firmware_patched/iPhone17,3_26.1_23B85_Restore
cd ..
```

Main actions:

- Mounts rootfs RW and renames snapshot
- Installs Cryptex SystemOS/AppOS
- Patches `seputil` and `launchd_cache_loader`
- Patches `mobileactivationd` (activation bypass used by original research flow)
- Optional `launchd` patch (disabled by default in current script; enable only when explicitly needed)
- Installs iosbinpack64
- Installs/injects launch daemons (`bash`, `dropbear`, optional `trollvnc`)
- Optional GPU bundle install via `--pcc-gpu-bundle`
- Optional Metal compiler plugin install via `--pcc-gpu-plugin`
- Halts VM at end (unless `--no-halt`)

### 9.1 Metal Support (Required for Setup UI Stability)

Validated behavior from this workspace and `README_old`:

- Without Metal bundle + compiler plugin, setup UI may stay black/respring.
- Required target path on rootfs:
  - `/System/Library/Extensions/AppleParavirtGPUMetalIOGPUFamily.bundle`
- Required additional file:
  - `libAppleParavirtCompilerPluginIOGPUFamily.dylib`

Validated source path for the bundle (host):

- `/tmp/pcc_mount/System/Library/Extensions/AppleParavirtGPUMetalIOGPUFamily.bundle`
  - obtained by mounting PCC VM disk image:
  - `~/Library/Application Support/com.apple.security-research.vrevm/VM-Library/pcc-research.vm/Disk.img`

Recommended one-time cache on host:

```bash
REPO="/Users/vinay/super-tart-vphone-writeup/external/Lakr233-super-tart-vphone-writeup"
SRC="/tmp/pcc_mount/System/Library/Extensions/AppleParavirtGPUMetalIOGPUFamily.bundle"
CACHE="$REPO/patch_scripts/metal_cache"
mkdir -p "$CACHE"
rsync -a "$SRC/" "$CACHE/AppleParavirtGPUMetalIOGPUFamily.bundle/"
tar -C "$CACHE" -cf "$CACHE/AppleParavirtGPUMetalIOGPUFamily.tar" AppleParavirtGPUMetalIOGPUFamily.bundle
```

Build compiler plugin dylib (blog-based clean-room source):

```bash
mkdir -p "$REPO/patch_scripts/metal_plugin"
curl -L https://zeroxjf.github.io/blog/assets/metal-patch/main.mm -o "$REPO/patch_scripts/metal_plugin/main.mm"
curl -L https://zeroxjf.github.io/blog/assets/metal-patch/build.sh -o "$REPO/patch_scripts/metal_plugin/build.sh"
chmod +x "$REPO/patch_scripts/metal_plugin/build.sh"
(cd "$REPO/patch_scripts/metal_plugin" && ./build.sh)
```

Apply in SSH ramdisk session (`boot_rd.sh` active, `iproxy 2222 22`):

```bash
REPO="/Users/vinay/super-tart-vphone-writeup/external/Lakr233-super-tart-vphone-writeup"
TAR="$REPO/patch_scripts/metal_cache/AppleParavirtGPUMetalIOGPUFamily.tar"
PLUGIN="$REPO/patch_scripts/metal_plugin/libAppleParavirtCompilerPluginIOGPUFamily.dylib"

ssh -p 2222 root@127.0.0.1 '/sbin/mount_apfs -o rw /dev/disk1s1 /mnt1 >/dev/null 2>&1 || true'
scp -P 2222 "$TAR" root@127.0.0.1:/mnt1/
ssh -p 2222 root@127.0.0.1 '/usr/bin/tar --preserve-permissions --no-overwrite-dir -xvf /mnt1/AppleParavirtGPUMetalIOGPUFamily.tar -C /mnt1'

# if tar extracted directly under /mnt1, move it into Extensions
ssh -p 2222 root@127.0.0.1 '/bin/mkdir -p /mnt1/System/Library/Extensions; [ -d /mnt1/AppleParavirtGPUMetalIOGPUFamily.bundle ] && /bin/mv /mnt1/AppleParavirtGPUMetalIOGPUFamily.bundle /mnt1/System/Library/Extensions/'

scp -P 2222 "$PLUGIN" root@127.0.0.1:/mnt1/System/Library/Extensions/AppleParavirtGPUMetalIOGPUFamily.bundle/
```

Finalize permissions:

```bash
ssh -p 2222 root@127.0.0.1 '
/usr/sbin/chown -R 0:0 /mnt1/System/Library/Extensions/AppleParavirtGPUMetalIOGPUFamily.bundle
/bin/chmod 0755 /mnt1/System/Library/Extensions/AppleParavirtGPUMetalIOGPUFamily.bundle
/bin/chmod 0755 /mnt1/System/Library/Extensions/AppleParavirtGPUMetalIOGPUFamily.bundle/AppleParavirtGPUMetalIOGPUFamily
/bin/chmod 0755 /mnt1/System/Library/Extensions/AppleParavirtGPUMetalIOGPUFamily.bundle/libAppleParavirtCompilerPluginIOGPUFamily.dylib
/bin/chmod 0644 /mnt1/System/Library/Extensions/AppleParavirtGPUMetalIOGPUFamily.bundle/Info.plist
/bin/chmod 0644 /mnt1/System/Library/Extensions/AppleParavirtGPUMetalIOGPUFamily.bundle/_CodeSignature/CodeResources
'
```

### 9.2 Verify Critical Boot-Fix Patches (Do Not Skip)

Use the helper script to patch/verify local copies with correct offsets:

```bash
python3 patch_scripts/fix_boot_patch_verify.py --verify --dir /tmp
```

Expected values:

- `launchd_cache_loader @ 0xB58` => `0xD503201F` (`dd` bytes: `1f2003d5`)
- `mobileactivationd @ 0x2F5F84` => `0xD2800020` (`dd` bytes: `200080d2`)
- `launchd @ 0xD73C` => `0x14000017` (`dd` bytes: `17000014`)

Note the corrected decimal offset for `mobileactivationd`:

- `0x2F5F84` = `3104644` (not `3102596`)

## 10. Boot Normally and Validate

After halt, boot the VM in normal mode using your chosen runtime path (original guide used `tart run ... --vnc-experimental`).

Expected first-boot services after rootfs setup:

- dropbear SSH
- bash daemon
- optional TrollVNC

Recommended checks:

- SSH reachable on forwarded port
- Cryptex directories populated under `/System/Cryptexes`
- Patched binaries present and executable

### 10.1 Verified Working State (2026-02-26)

This sequence was validated end-to-end in this repo workspace:

- SSH ramdisk mode:
  - `iproxy 2222 22`
  - `ssh root@127.0.0.1 -p2222` (password: `alpine`)
- Normal boot mode:
  - If using original-research dropbear plist, dropbear listens on `22222`
  - connect over USB tunnel: `iproxy 2222 22222` then `ssh root@127.0.0.1 -p2222`
  - or connect directly via VM IP: `ssh root@$(tart ip vphone) -p22222`
  - if your generated plist uses `-p 22`, forward `2222 -> 22` instead

Important: `irecovery` is not expected to work in normal boot mode. It is for DFU/Recovery stages.

### 10.2 If SSH Closes Immediately in Normal Boot

Use the original-research runtime bootstrap once in serial on normal boot:

```bash
export PATH='/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/bin/X11:/usr/games:/iosbinpack64/usr/local/sbin:/iosbinpack64/usr/local/bin:/iosbinpack64/usr/sbin:/iosbinpack64/usr/bin:/iosbinpack64/sbin:/iosbinpack64/bin'
/iosbinpack64/bin/mkdir -p /var/dropbear
/iosbinpack64/bin/cp /iosbinpack64/etc/profile /var/profile
/iosbinpack64/bin/cp /iosbinpack64/etc/motd /var/motd
```

If manual launch is needed for debugging:

```bash
/iosbinpack64/bin/killall dropbear
/iosbinpack64/usr/local/bin/dropbear --shell /iosbinpack64/bin/bash -R -E -F -p 22222 -a
```

Then connect from host:

```bash
ssh root@<guest-ip> -p22222
```

### 10.3 Setup Screen Interaction Notes

If the UI shows "Security Research Device" and interaction feels limited, use the original-research touch path:

- Start VM with:

```bash
tart run vphone --vnc --serial
```

- Verified Home gesture in this workspace:
  - right-click + scroll up => Home button action
- `CMD + H` can still be used as fallback.
- `--vnc-experimental` can display setup, but touch handling may be less reliable on some host versions.
- `--capture-system-keys` only works with the default VM UI (not `--vnc` / `--vnc-experimental`).
- optional TrollVNC from guest (`5901`) can still be used when needed.

If touch still does not behave well on your host/version combination, continue setup through serial/SSH first, then return to UI flow.

### 10.4 Common Runtime Pitfalls (Validated)

- Symptom: `ssh ... -p2222` fails with `Connection refused` in normal boot.
  - Cause: forwarding to wrong guest port or wrong device mode.
  - Fix: in ramdisk use `iproxy 2222 22`; in normal boot usually `iproxy 2222 22222` (original-research plist).
- Symptom: `scp: dest open "/mnt1/...": Failure`.
  - Cause: `/mnt1` not mounted RW.
  - Fix: in ramdisk shell run `mount_apfs -o rw /dev/disk1s1 /mnt1` and retry copy.
- Symptom: files copied to `/mnt1` but not under `/System/Library/Extensions`.
  - Cause: tar extracted bundle at `/mnt1/AppleParavirtGPUMetalIOGPUFamily.bundle`.
  - Fix: move it to `/mnt1/System/Library/Extensions/AppleParavirtGPUMetalIOGPUFamily.bundle`.
- Symptom: launchd panic with launch-constraint violation.
  - Cause: incorrect/mismatched `launchd` patch.
  - Fix: keep default script behavior (skip launchd patch) unless you have a known-good offset set.
- Symptom: commands like `awk`, `plutil`, `mount`, `touch` missing in SSHRD shell.
  - Cause: minimal ramdisk userland.
  - Fix: use built-in paths carefully and rely on host-side tooling where possible.

## 11. Optional Patch Verification in IDA

From `document-snippets` and original notes:

- Search for `0x4447` (DGST) in `image4_validate_property_callback`
- Confirm patch points force return success (`MOV X0, #0`)
- Rebase bootloader raws at `0x7006C000` (`iBSS/iBEC/LLB`) and AVPBooter at `0x100000`

## 12. Checkpoints and Resume

You can skip heavy stages by extracting checkpoint tarballs at repo root:

- `01-mixed-firmware-unpatch.tar`: skip downloads/mix
- `02-raw-binaries-extracted.tar`: skip raw IM4P extraction setup
- `03-firmware-patched.tar`: skip patching
- `04-patches-verified-ida.tar`: skip patch verification prep

## 13. Missing/Implicit Items Identified

Compared to the current quickstart, these were implicit or missing:

1. `vphone-cli` build/sign is required before `vm_boot_dfu.sh`.
2. VM asset provisioning is required (`$TART_HOME/vms/vphone` files must already exist).
3. `prepare_ramdisk.py` requires an active DFU device unless using `--skip-shsh`.
4. `setup_rootfs.py` needs `jb/iosbinpack64.tar` and host tools (`ipsw`, `aea`, `sshpass`, `ldid`).
5. The high-level order must ensure DFU is running before SHSH fetch/signing.

If you want, this guide can be turned into a strict checklist script with per-step preflight assertions.

## 14. Jailbreak Stages (Original-Research Order)

From the original flow, jailbreak is not a single step. It is:

1. DFU + ramdisk: stage Procursus payload into preboot
2. Normal boot: complete Procursus bootstrap from live system
3. DFU + ramdisk again: install basebin launch hooks

### 14.1 Stage Procursus (ramdisk mode)

Prereq: VM is in SSH ramdisk mode (`boot_rd.sh` active, `iproxy 2222 22` running).

```bash
cd patch_scripts
python3 install_jb_procursus.py
```

Equivalent source reference:

- [GUIDE.md:376](/Users/vinay/super-tart-vphone-writeup/external/Lakr233-super-tart-vphone-writeup/original-research/super-tart-vphone/GUIDE.md:376)
- [install_jb_procursus.py:36](/Users/vinay/super-tart-vphone-writeup/external/Lakr233-super-tart-vphone-writeup/original-research/super-tart-vphone/CFW/install_jb_procursus.py:36)

### 14.2 Complete Procursus (normal boot mode)

1. Halt ramdisk.
2. Boot normal VM UI (`--vnc --serial` recommended).
3. Connect over dropbear (`22222` in original plist):

```bash
iproxy 2222 22222
ssh root@127.0.0.1 -p2222
```

4. Run the preboot-link/bootstrap commands from original guide:

- [GUIDE.md:413](/Users/vinay/super-tart-vphone-writeup/external/Lakr233-super-tart-vphone-writeup/original-research/super-tart-vphone/GUIDE.md:413)

### 14.3 Install BaseBin Hooks (ramdisk mode again)

Go back to DFU + ramdisk, then:

```bash
cd patch_scripts
python3 install_jb_basebin.py
```

Equivalent source reference:

- [GUIDE.md:451](/Users/vinay/super-tart-vphone-writeup/external/Lakr233-super-tart-vphone-writeup/original-research/super-tart-vphone/GUIDE.md:451)
- [install_jb_basebin.py:28](/Users/vinay/super-tart-vphone-writeup/external/Lakr233-super-tart-vphone-writeup/original-research/super-tart-vphone/CFW/install_jb_basebin.py:28)

Notes:

- Original dropbear plist listens on `22222`:
  - [dropbear.plist:27](/Users/vinay/super-tart-vphone-writeup/external/Lakr233-super-tart-vphone-writeup/original-research/super-tart-vphone/CFW/jb/LaunchDaemons/dropbear.plist:27)
- `install_jb_basebin.py` requires `optool` + `BaseBin` sources + `libellekit.dylib` from original-research tree.

### 14.4 Panics Encountered and Resolved (Validated)

During this workspace run, these two panic classes appeared before successful normal boot:

- Panic A (code-signature load failure):
  - `initproc failed to start -- ... Library not loaded: /cores/launchdhook.dylib`
  - `code signature invalid ... '/cores/launchdhook.dylib' (errno=1)`
  - Cause: injected hook dylib not signed in a way acceptable for this chain.
  - Fix used: sign `systemhook.dylib`, `launchdhook.dylib`, and `libellekit.dylib` before uploading to `/mnt1/cores` (script now does this).

- Panic B (`launchd cannot be run directly`):
  - `initproc exited -- exit reason namespace 7 subcode 0x1 description: launchd cannot be run directly (stdout: 1)`
  - Cause: this `launchd` build hit a direct-run stdout check path after hook injection.
  - Fix used: patch `launchd` at `0x17738` from expected `0x360026A8` to `0xD503201F` (NOP).
  - Safety guard: installer validates the expected opcode first and aborts on mismatch.
  - Result: normal boot succeeded after applying this bypass.

### 14.5 `prep_bootstrap.sh` Warnings vs Failure

These messages were observed and can still end in a successful stage completion:

- `add-shell: not found`
- `update-alternatives: not found`
- `pwd_mkdb: warning, unknown root shell`
- `pw: user '' disappeared during update`

Treat the stage as successful if post-steps work and markers exist:

```bash
ls -l /var/jb/.procursus_strapped /var/jb/.installed_dopamine
```

Expected: both files present (`-rw-r--r-- root wheel 0 ...`).

### 14.6 Developer Mode Note (Observed During Sileo Bring-Up)

During this workspace run, launching Sileo produced AMFI logs like:

- `Developer mode is disabled, get-task-allow is disallowed`

Observed behavior:

- After connecting the VM/device to Xcode, the Developer Mode option became visible.

Practical guidance:

- If you see the AMFI message above while testing Sileo/tweaks, check Developer Mode state first.
- Enabling Developer Mode via the standard UI flow is the expected path before continuing UI-side jailbreak app testing.

## 15. TXM Patch Update Workflow (Re-Restore Required)

If you change TXM patch offsets in `patch_scripts/patch_fw.py` (for example jailbreak/dev-mode helper patches), you must re-restore so normal boot actually uses the new TXM.

This is the validated order and exact command set.

### 15.1 Stop Current Ramdisk Session

```bash
ssh root@127.0.0.1 -p2222 'halt'
```

### 15.2 Apply TXM Patch on Host (No DFU Needed Yet)

```bash
REPO="/Users/vinay/super-tart-vphone-writeup/external/Lakr233-super-tart-vphone-writeup"
FW="$REPO/firmwares/firmware_patched/iPhone17,3_26.1_23B85_Restore"

cd "$REPO"
python3 patch_scripts/patch_fw.py -d "$FW" -c TXM
```

Optional verification:

```bash
python3 patch_scripts/patch_fw.py -d "$FW" -c TXM --verify-only
```

### 15.3 Re-Restore Patched Firmware

Terminal A (keep running):

```bash
cd "$REPO"
./vm_boot_dfu.sh vphone
```

Terminal B:

```bash
cd "$REPO"
"$REPO/bin/idevicerestore" -e -y "$FW"
```

Note: after restore completes, VM typically panics/reboots; that is expected in this flow.

### 15.4 Boot DFU Again, Regenerate Ramdisk IMG4, Boot Ramdisk

```bash
cd "$REPO"
./vm_boot_dfu.sh vphone
python3 patch_scripts/prepare_ramdisk.py -d "$FW"
bash patch_scripts/boot_rd.sh
```

### 15.5 Re-Apply Rootfs Changes (Restore Resets Them)

```bash
cd "$REPO/patch_scripts"
python3 setup_rootfs.py -d ../firmwares/firmware_patched/iPhone17,3_26.1_23B85_Restore
```

### 15.6 Normal Boot

```bash
cd "$REPO"
"$REPO/bin/tart" run vphone --vnc --serial
```

### 15.7 Why Re-Restore Is Needed

- `prepare_ramdisk.py` + `boot_rd.sh` only boot a ramdisk session.
- TXM in normal boot comes from restored firmware state.
- Therefore TXM patch changes must be followed by re-restore, then ramdisk/rootfs steps again.

## 16. Full End-to-End Command Order (No-Miss Checklist)

This section is a single ordered runbook to reach a fully usable virtual iOS research device (boot patches, rootfs changes, Metal support, and jailbreak stages).

### 16.1 Variables (set once)

```bash
REPO="/Users/vinay/super-tart-vphone-writeup/external/Lakr233-super-tart-vphone-writeup"
FW="$REPO/firmwares/firmware_patched/iPhone17,3_26.1_23B85_Restore"
GPU_BUNDLE="$REPO/patch_scripts/metal_cache/AppleParavirtGPUMetalIOGPUFamily.bundle"
GPU_PLUGIN="$REPO/patch_scripts/metal_plugin/libAppleParavirtCompilerPluginIOGPUFamily.dylib"
```

### 16.2 Patch Firmware (host-side)

Core patch set:

```bash
cd "$REPO"
python3 patch_scripts/patch_fw.py -d "$FW"
```

TXM mode behavior in current script:

- Default = **minimal/stable** (trustcache-only TXM patches)
- Optional = **jb-extra/experimental** (adds original-research TXM dev-mode helper block)

If you changed only TXM and want to re-apply only TXM:

```bash
python3 patch_scripts/patch_fw.py -d "$FW" -c TXM
```

If you explicitly want the experimental TXM jb-extra block:

```bash
python3 patch_scripts/patch_fw.py -d "$FW" -c TXM --txm-jb-extra
```

Optional verification:

```bash
python3 patch_scripts/patch_fw.py -d "$FW" --verify-only
```

### 16.3 Restore Patched Firmware

Terminal A:

```bash
cd "$REPO"
./vm_boot_dfu.sh vphone
```

Terminal B:

```bash
cd "$REPO"
"$REPO/bin/idevicerestore" -e -y "$FW"
```

### 16.4 Build Personalized Ramdisk IMG4 and Boot Ramdisk

```bash
cd "$REPO"
./vm_boot_dfu.sh vphone
python3 patch_scripts/prepare_ramdisk.py -d "$FW"
bash patch_scripts/boot_rd.sh
```

### 16.5 Apply Rootfs Changes

Full run (Cryptex + patches + iosbinpack + daemons + Metal):

```bash
cd "$REPO/patch_scripts"
python3 setup_rootfs.py \
  -d ../firmwares/firmware_patched/iPhone17,3_26.1_23B85_Restore \
  --pcc-gpu-bundle "$GPU_BUNDLE" \
  --pcc-gpu-plugin "$GPU_PLUGIN"
```

If only Metal step is needed after an earlier full run:

```bash
python3 setup_rootfs.py \
  -d ../firmwares/firmware_patched/iPhone17,3_26.1_23B85_Restore \
  --skip-cryptex --skip-patches --skip-iosbinpack --skip-daemons \
  --pcc-gpu-bundle "$GPU_BUNDLE" \
  --pcc-gpu-plugin "$GPU_PLUGIN"
```

### 16.6 Normal Boot and Basic Access

```bash
cd "$REPO"
"$REPO/bin/tart" run vphone --vnc --serial
```

First-boot checkpoint (important):

- On the first boot after restore + rootfs setup, wait for the iPhone first-boot/setup animation flow to appear.
- Let SpringBoard settle for a few minutes before starting jailbreak stages.
- If setup UI is responsive, complete baseline setup once before moving to JB stages.

If you cannot reach this checkpoint and instead see repeated TXM code-signature spam/bootloop, go back to Section 15 and re-restore using TXM minimal mode (no `--txm-jb-extra`).

USB-tunnel SSH (normal boot with original dropbear plist):

```bash
iproxy 2222 22222
ssh root@127.0.0.1 -p2222
```

Direct over VM IP alternative:

```bash
ssh root@$(tart ip vphone) -p22222
```

### 16.7 Developer Mode / Sileo UI Note

If Sileo logs:

- `Developer mode is disabled, get-task-allow is disallowed`

Use standard Developer Mode enable flow (Settings/Xcode-assisted path) before continuing UI-side tweak testing.

### 16.8 Jailbreak Stage Order (after normal boot is stable)

Stage A (DFU + ramdisk, stage Procursus payload):

```bash
cd "$REPO"
./vm_boot_dfu.sh vphone
python3 patch_scripts/prepare_ramdisk.py -d "$FW"
bash patch_scripts/boot_rd.sh
cd "$REPO/patch_scripts"
python3 install_jb_procursus.py
ssh root@127.0.0.1 -p2222 'halt'
```

Stage B (normal boot, finalize Procursus + Sileo):

```bash
cd "$REPO"
"$REPO/bin/tart" run vphone --vnc --serial
iproxy 2222 22222
ssh root@127.0.0.1 -p2222
```

In guest shell:

```bash
HASH="$(ls /private/preboot | head -n1)"
ln -sfn "/private/preboot/$HASH/jb-vphone/procursus" /private/var/jb
mkdir -p /var/jb/var/mobile/Library/Preferences
chown -R 501:501 /var/jb/var/mobile/Library
chmod 0755 /var/jb/var/mobile/Library
chown -R 501:501 /var/jb/var/mobile/Library/Preferences
chmod 0755 /var/jb/var/mobile/Library/Preferences
/var/jb/prep_bootstrap.sh
export PATH='/sbin:/bin:/usr/sbin:/usr/bin:/var/jb/sbin:/var/jb/bin:/var/jb/usr/sbin:/var/jb/usr/bin'
export TERM='xterm-256color'
/var/jb/bin/touch /var/jb/.procursus_strapped
/var/jb/bin/chown 0:0 /var/jb/.procursus_strapped
/var/jb/usr/bin/chmod 0644 /var/jb/.procursus_strapped
/var/jb/bin/touch /var/jb/.installed_dopamine
/var/jb/bin/chown 0:0 /var/jb/.installed_dopamine
/var/jb/usr/bin/chmod 0644 /var/jb/.installed_dopamine
/var/jb/usr/bin/dpkg -i "/private/preboot/$HASH/org.coolstar.sileo_2.5.1_iphoneos-arm64.deb"
/var/jb/usr/bin/uicache -a
```

Stage C (DFU + ramdisk, install basebin hooks):

```bash
cd "$REPO"
./vm_boot_dfu.sh vphone
python3 patch_scripts/prepare_ramdisk.py -d "$FW"
bash patch_scripts/boot_rd.sh
cd "$REPO/patch_scripts"
python3 install_jb_basebin.py
```

Then normal boot again:

```bash
cd "$REPO"
"$REPO/bin/tart" run vphone --vnc --serial
```

### 16.9 Quick Validation Commands

Guest checks:

```bash
ls -l /cores/systemhook.dylib /cores/launchdhook.dylib /cores/libellekit.dylib
ls -l /var/jb/.procursus_strapped /var/jb/.installed_dopamine
```

Patch verify helper:

```bash
python3 "$REPO/patch_scripts/fix_boot_patch_verify.py" --verify --dir /tmp
```

### 16.10 Re-Run Rules

- Changed `patch_fw.py` firmware patches (TXM/kernel/bootchain): re-restore is required.
- Changed only rootfs content (`setup_rootfs.py` outputs): no re-restore needed; ramdisk + setup_rootfs rerun is enough.
- Changed only normal-boot userland state (`/var/jb`, Sileo, etc.): no re-restore needed.
