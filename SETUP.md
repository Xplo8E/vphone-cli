# vphone600ap Setup Guide

Full pre-patching setup from a bare macOS machine to a working vphone VM. Covers everything before `patch_fw.py` runs. Based on the actual steps used to build this workspace.

---

## Step 0: Host Prerequisites (One-Time — Requires Recovery Mode)

Boot into macOS Recovery Mode (hold power on Apple Silicon) and run:

```bash
csrutil disable
nvram amfi_get_out_of_my_way=1
csrutil allow-research-guests enable
```

Reboot normally after. Also required:

- **Xcode 26.2+** — needed for the Swift build of tart
- **Homebrew** — install from [brew.sh](https://brew.sh/)

Install Homebrew dependencies:

```bash
brew install automake autoconf libtool pkg-config \
             libplist openssl@3 libimobiledevice-glue \
             libimobiledevice libtatsu libzip \
             ldid sshpass gtar usbmuxd
```

---

## Step 1: Build OEM Tools

From repo root:

```bash
bash setup_bin.sh
```

Builds (in dependency order): libgeneral → img4lib → img4tool → trustcache → libirecovery → idevicerestore → super-tart. Also copies ldid, sshpass, gtar, iproxy from Homebrew into `bin/`. Creates a Python venv at `.venv/` with `pyimg4` and `capstone`.

`bin/tart` is built with the vphone patches and signed with the required entitlements (including `com.apple.private.virtualization.security-research`) automatically by `setup_bin.sh`.

Expected `bin/` contents after success:

```
bin/img4          bin/img4tool      bin/trustcache
bin/irecovery     bin/idevicerestore  bin/tart
bin/ldid          bin/sshpass       bin/gtar
bin/iproxy        bin/AVPBooter.vresearch1.bin
```

---

## Step 2: Activate Environment

Must be sourced before using any repo tools or running patch scripts:

```bash
source setup_env.sh
```

Sets `TART_HOME=.tart/`, `PATH` (adds `bin/` and `.local/bin`), `IMG4TOOL`, `IMG4`, `TRUSTCACHE`, `PYIMG4`, and activates the `.venv`.

---

## Step 3: Download and Mix Firmware

Two firmware sources are needed:

**iPhone IPSW** (~10 GB):

Download `iPhone17,3_26.1_23B85_Restore.ipsw` from [ipsw.me](https://ipsw.me) and place it in `_work/firmwares/`:

```bash
mkdir -p _work/firmwares
# download manually → _work/firmwares/iPhone17,3_26.1_23B85_Restore.ipsw
```

**PCC cloudOS IPSW** (~892 MB) — two options:

Option A — automated download via `setup_download_fw.sh` (fetches from Apple CDN):

```bash
bash setup_download_fw.sh
```

This handles download, extraction, and mixing in one shot. Skip the manual steps below if you use this.

Option B — using the system `pccvre` tool:

```bash
cd /System/Library/SecurityResearch/usr/bin
./pccvre release download --release 35622
# copy the downloaded IPSW to the repo's _work/firmwares directory:
cp /path/to/downloaded/pcc_os_23B85.ipsw /path/to/repo/_work/firmwares/pcc_os_23B85.ipsw
```

If you used Option B and already have both IPSWs in `_work/firmwares/`, run the mix:

```bash
bash setup_download_fw.sh  # safe to re-run — skips already-downloaded files
```

Result: `_work/firmwares/firmware_patched/iPhone17,3_26.1_23B85_Restore/` with mixed components from both IPSWs and the custom `BuildManifest.plist` / `Restore.plist` from `contents/`.
The patch scripts still auto-detect legacy `firmwares/...` paths for compatibility.

---

## Step 4: Create the vphone VM

The vphone VM is built on top of a `pcc-research` VM created by pccvre — this gives the correct disk image, SEP storage, and hardware config for the vphone hardware model.

### 4a. Create the PCC research VM (if not done already)

```bash
cd /System/Library/SecurityResearch/usr/bin
./pccvre instance create -N pcc-research -R 35622 --variant research
```

Wait for restore to complete. The VM will be stored at:

```
~/Library/Application Support/com.apple.security-research.vrevm/VM-Library/pcc-research.vm/
```

### 4b. Scaffold the vphone VM using bin/tart

```bash
REPO="$(pwd)"  # run from repo root
source setup_env.sh
# any macOS IPSW works as the --from-ipsw source; we overwrite everything next
tart create vphone --disk-size 40 --from-ipsw /path/to/any-macos.ipsw
```

This creates `.tart/vms/vphone/` (TART_HOME is `.tart/` when setup_env.sh is sourced).

### 4c. Replace placeholder files with PCC VM contents

```bash
PCC_VM="$HOME/Library/Application Support/com.apple.security-research.vrevm/VM-Library/pcc-research.vm"

# Remove files created by tart create (we overwrite them)
rm "$TART_HOME/vms/vphone/AVPBooter.vmapple2.bin"
rm "$TART_HOME/vms/vphone/disk.img"
rm "$TART_HOME/vms/vphone/nvram.bin"

# Copy PCC VM files
cp "$PCC_VM/config.plist" "$TART_HOME/vms/vphone/config.plist"
cp "$PCC_VM/Disk.img"     "$TART_HOME/vms/vphone/disk.img"
cp "$PCC_VM/AuxiliaryStorage" "$TART_HOME/vms/vphone/nvram.bin"
cp "$PCC_VM/SEPStorage"   "$TART_HOME/vms/vphone/SEPStorage"
```

### 4d. Copy AVPBooter from system Virtualization.framework

```bash
VZ="/System/Library/Frameworks/Virtualization.framework/Versions/A/Resources"
cp "$VZ/AVPBooter.vresearch1.bin"    "$TART_HOME/vms/vphone/AVPBooter.vresearch1.bin"
cp "$VZ/AVPSEPBooter.vresearch1.bin" "$TART_HOME/vms/vphone/AVPSEPBooter.vresearch1.bin"
```

The `AVPBooter.vresearch1.bin` copied here is the **stock (unpatched)** Apple binary. It gets patched later by `patch_fw.py -c AVPBooter`, which writes the patched version to `bin/AVPBooter.vresearch1.bin`. The patched copy is then placed back into the VM directory before restore.

---

## Step 5: Verify the VM boots in DFU mode

```bash
source setup_env.sh
tart run vphone --dfu --serial
```

Open **System Information → Hardware → USB** on the host. If a DFU device appears, the VM is working correctly.

---

## You're Ready

At this point:

- All tools are built and in `bin/` — including `bin/tart` signed with vphone entitlements
- Firmware is mixed into `_work/firmwares/firmware_patched/iPhone17,3_26.1_23B85_Restore/`
- `.tart/vms/vphone/` exists with PCC disk + SEP + AVPBooter

---

## Next: Firmware Patch + Restore

Continue with `VPHONE_RUNBOOK.md` Section 1 for the full flow. Quick start:

```bash
REPO="$(pwd)"
FW="$REPO/_work/firmwares/firmware_patched/iPhone17,3_26.1_23B85_Restore"

cd "$REPO"
source setup_env.sh

# Patch firmware (full jailbreak-oriented set)
python3 patch_scripts/patch_fw.py -d "$FW" --kernel-jb-extra --txm-jb-extra

# Terminal A — start VM in DFU
"$REPO/bin/tart" run vphone --dfu --serial

# Terminal B — restore patched firmware
"$REPO/bin/idevicerestore" -e -y "$FW"
```

After restore, follow `VPHONE_RUNBOOK.md` for the full flow — ramdisk boot, rootfs setup, SSH/VNC access, jailbreak staging, and troubleshooting.
