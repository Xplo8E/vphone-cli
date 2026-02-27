# Gaps Between DETAILED_GUIDE and Original Research

Comparison of `docs/DETAILED_GUIDE.md` (current working flow) against `original-research/super-tart-vphone/GUIDE.md` and `CFW/` scripts.

Status key: `[ ]` = not started, `[~]` = partial/investigating, `[x]` = resolved

---

## Critical Gaps

### 1. [x] ~194 Missing Kernel Jailbreak Patches (RESOLVED 2026-02-26)

Current `patch_fw.py` applies **5 kernel patches** (3 SSV bypass + 2 launch constraints).
Original `CFW/patch_fw.py` applies **~80+** covering:

- AMFI bypass (~15 patches)
- Sandbox policy bypass (~10 patches)
- Codesign bypass (~10 patches)
- task_for_pid / tfp0 access (~5 patches)
- MAC policy bypass — `mac_proc_check_*` (~8 patches)
- kcall10 syscall hook shellcode injection (4 shellcode regions at 0xAB1720, 0xAB1740, 0xAB17D8, 0xAB1890)
- ~25+ miscellaneous jb-required patches

Impact: VM boots and rootfs works, but full jailbreak (Sileo tweaks, tfp0, runtime code injection) won't function. Basebin hooks partially work via TXM trustcache bypass, but kernel enforcement (AMFI, sandbox, codesigning) remains active.

Source reference: `original-research/super-tart-vphone/CFW/patch_fw.py` — search for the large kernel patch block after the 3 SSV patches.

**Resolution:** Added `--kernel-jb-extra` flag to `patch_fw.py` with all 194 patches from original
`CFW/patch_fw.py`. Includes AMFI trustcache bypass, 4 shellcode caves (cred_label, syscallmask,
hook_cred_label, kcall10), 31 MACF hook table overrides, task/process/VM/mount bypasses, and
sysent table replacement for kcall10 syscall primitive. Verified all offsets land on expected
targets. Usage: `python3 patch_fw.py -d <fw_dir> --kernel-jb-extra`

**Reminder:** Kernel patches require re-restore to take effect (see DETAILED_GUIDE Section 15).

### 2. [x] `snaputil` Commands — NOT A GAP (RESOLVED 2026-02-26)

Original GUIDE Step 7:
```bash
/usr/sbin/mount_apfs -o rw /dev/disk1s1 /mnt1
/usr/sbin/snaputil -d /mnt1
/usr/sbin/snaputil -d /mnt1 com.apple.os.update-xxxx
```

These delete APFS snapshots so rootfs modifications persist across reboot. Current `setup_rootfs.py` mounts RW and renames the snapshot but never runs `snaputil -d`.

**Resolution:** False alarm. Original GUIDE.md (line 322) uses `snaputil -n` (rename), NOT
`snaputil -d` (delete). Current `setup_rootfs.py` `step_mount_rootfs()` already does exactly
this: lists snapshots, renames `com.apple.os.update-xxx` to `orig-fs`. Matches original flow.

### 3. [ ] Ramdisk Boot-Args `rd=md0 wdt=-1` Not Applied

Original `get_rd.py` patches iBEC with ramdisk-specific boot-args (`rd=md0 wdt=-1`) that differ from normal boot-args. Current `prepare_ramdisk.py` reuses the same iBEC patched for normal boot.

- `rd=md0` — tells kernel to use memory disk 0 as root device (ramdisk)
- `wdt=-1` — disables watchdog timer (prevents timeout panics during slow ramdisk boot)

Impact: If ramdisk boot times out or kernel can't find root device, this is likely why.

### 4. [x] Ramdisk Kernel Gets Zero Intermediate JB Patches (RESOLVED BY GAP #1)

Original `get_rd.py` applies ~21 intermediate jailbreak patches to the ramdisk kernel (subset of full jb set). Current `prepare_ramdisk.py` applies zero additional patches — uses kernel from `patch_fw.py` which only has 5 patches.

**Resolution:** Gap #1's `--kernel-jb-extra` flag patches the kernel in `firmware_patched/` with all 199
patches. Since `prepare_ramdisk.py` takes that same patched kernel, re-packs as `rkrn`, and signs it,
the ramdisk kernel now gets all 199 patches — a superset of the original's 21 intermediate patches.
No changes to `prepare_ramdisk.py` needed.

---

## Moderate Gaps

### 5. [ ] `fake_tss_server.py` Not Ported

Original has an offline TSS server at `CFW/fake_tss_server.py` — HTTP server on `127.0.0.1:1337` serving pre-captured `CFW/tss_response`. Enables `idevicerestore` without live Apple CDN access.

Impact: Every restore currently requires network access to Apple's signing servers.

To port: Copy `fake_tss_server.py` and `tss_response` to current repo. Run before `idevicerestore`:
```bash
python3 fake_tss_server.py &
idevicerestore -e -y --server http://127.0.0.1:1337 <restore_dir>
```

### 6. [x] `test_live_patch.py` Workflow Not Documented (RESOLVED 2026-02-26)

Original `CFW/test_live_patch.py` patches kernel + TXM live via SSH ramdisk:
1. Grabs `apticket.der` from preboot
2. Applies full jb patch set (~80+ kernel, full TXM)
3. Signs with the ticket
4. Uploads to preboot paths
5. Halts

This avoids the full re-restore cycle (DETAILED_GUIDE Section 15) when only changing patch offsets. Significant time-saver for iterative patch development.

**Resolution:** Created `patch_scripts/live_patch.py` — imports patch lists directly from `patch_fw.py`
(no duplication). Supports `--kernel-jb-extra`, `--txm-jb-extra`, `--kernel-only`, `--txm-only`,
`--no-halt`, `--dry-run`. Workflow:
```bash
# Terminal 1: VM in DFU + ramdisk booted
# Terminal 2: iproxy 2222 22
# Terminal 3:
cd patch_scripts
python3 live_patch.py --kernel-jb-extra --txm-jb-extra
# Device halts. Normal boot picks up patched kernel + TXM.
```

### 7. [x] `signcert.p12` Sourcing Undocumented (RESOLVED 2026-02-26 — NOT A GAP)

Multiple scripts prefer `signcert.p12` for signing:
- `install_jb_basebin.py`
- `setup_rootfs.py`

Original includes it at `CFW/signcert.p12`. Current repo doesn't distribute it.

Scripts fall back to ad-hoc signing (`ldid -S`), but `install_jb_basebin.py` comments warn ad-hoc can "trigger early init failures" for launchd hooks.

**Resolution:** Moved `signcert.p12` to `patch_scripts/signcert.p12` so scripts do not depend on
repo-root placement. Both `setup_rootfs.py` and `install_jb_basebin.py` now check
`patch_scripts/signcert.p12` first, then fall back to `REPO_ROOT/signcert.p12` and
`original-research/.../CFW/signcert.p12`. The cert is an expired Apple Developer Distribution cert
(team "jiu de", 2017-2018) —
expiration irrelevant since `ldid` uses it for code directory hashing, not Apple chain validation,
and TXM trustcache bypass skips cert verification.

Action needed: Document how to obtain or generate `signcert.p12`, or verify ad-hoc signing works for all cases in current flow.

### 8. [x] Two AVPBooter Variants — Only One Documented (RESOLVED 2026-02-26)

| Variant | Source | Size | Patch Offsets |
|---------|--------|------|---------------|
| System (vresearch1) | `/System/.../AVPBooter.vresearch1.bin` | 233,368 bytes | 0x2ADC (NOP), 0x2AE0 (MOV X0,#0) |
| Desktop/VM (IPSW) | From firmware_patched/ or Desktop | 251,856 bytes | 0x2C1C (NOP), 0x2C20 (MOV X0,#0) |

DETAILED_GUIDE covers Desktop/VM variant only. Anyone following original pccvre workflow needs system variant offsets.

Original script: `CFW/patch_avpbooter.py` — patches system variant.
Current script: `patch_fw.py` — was incorrectly using Desktop/VM offset (0x2C20) on system binary.

**Resolution:** Fixed `patch_fw.py` to use system variant offsets (0x2ADC NOP + 0x2AE0 MOV X0,#0).
Also added the NOP patch at 0x2ADC (stack-cookie abort branch bypass) which the old single-patch
version was missing. Updated EXPECTED_ORIGINALS to verify both offsets. Re-patched `bin/AVPBooter.vresearch1.bin`
with correct offsets. The old 0x2C20 patch was writing MOV X0,#0 over a RET instruction — wrong target.

### 9. [x] Logging String Patches Omitted (RESOLVED 2026-02-26)

Original patches ASCII strings in iBSS/iBEC/LLB to say `Loaded iBSS`, `Loaded iBEC`, `Loaded LLB`. These appear on serial console during boot.

Cosmetic but very useful for debugging boot failures — you can tell exactly which stage was reached.

**Resolution:** Added serial logging string patches to `patch_fw.py`:
- iBSS: 0x84349, 0x843F4 → `"Loaded iBSS"`
- iBEC: 0x84349, 0x843F4 → `"Loaded iBEC"`
- LLB:  0x86809, 0x868B4 → `"Loaded LLB"`

These are applied automatically with all other patches. Requires re-patching iBSS/iBEC/LLB.

### 10. [ ] Post-Procursus `apt` Commands Missing

Original GUIDE after Procursus bootstrap:
```bash
apt update && apt install libkrw0-tfp0 && apt upgrade -y
```

Not in DETAILED_GUIDE Section 14.2 guest shell commands. `libkrw0-tfp0` is the kernel read/write library needed by Sileo and tweaks.

### 11. [ ] Ellekit Sileo Repo Not Documented

Original GUIDE:
> Add repo in Sileo: `https://ellekit.space`
> Install ElleKit from Sileo

DETAILED_GUIDE mentions `libellekit.dylib` as a file dependency but not the package manager integration for runtime updates.

### 12. [ ] FakeDeviceInfo Tweak Not Documented

Original GUIDE appendix documents a FakeDeviceInfo tweak for spoofing device identity. Pre-built binary exists at `CFW/jb/FakeDeviceInfo`. Not mentioned in DETAILED_GUIDE.

### 13. [x] debugserver Fix Not Documented (RESOLVED 2026-02-26)

Original GUIDE appendix describes patching debugserver for remote debugging. Not covered in DETAILED_GUIDE. Relevant for anyone doing runtime debugging via lldb.

**Resolution:** Documented here for reference. Run on guest (normal boot SSH):
```bash
ldid -e /usr/libexec/debugserver > /tmp/e.xml
cd /var/jb/usr/lib/llvm-16/bin
ldid -S/tmp/e.xml -M ./debugserver
```
This re-signs the Procursus debugserver with the system debugserver's entitlements,
enabling lldb remote debugging via `debugserver *:1234 -- /path/to/binary`.

---

## Minor Gaps / Nice-to-Haves

### 14. [ ] `bspatch43` and `kerneldiff` Tools Missing

Original `CFW/tools/` includes `bspatch43` and `kerneldiff`. Used in vma2pwn workflow (referenced in `document-snippets/02-vma2pwn-prepare.md`). Not built by `setup_bin.sh`.

### 15. [x] `iosbinpack64` Source Not Documented (RESOLVED 2026-02-26)

`setup_rootfs.py` expects `jb/iosbinpack64.tar` but DETAILED_GUIDE doesn't document where to obtain it. Original bundles it in `CFW/jb/`.

**Resolution:** Copied `iosbinpack64.tar` (30 MB) from original-research to local `jb/iosbinpack64.tar`.
`setup_rootfs.py` already searches this path first.

### 16. [ ] sftp-server Entitlements in Ramdisk

Original `get_rd.py` signs sftp-server with `sftp_server_ents.plist` entitlements. Current `prepare_ramdisk.py` doesn't mention sftp-server entitlements. May affect file transfer in ramdisk if sftp is needed.

### 17. [x] MetalTest and tfp0test Binaries (RESOLVED 2026-02-26)

Original `CFW/jb/` includes `MetalTest` (GPU validation) and `tfp0test` (task-for-pid-0 test). Useful for validating that patches work. Not mentioned in DETAILED_GUIDE.

**Resolution:** Copied `MetalTest/` and `tfp0test/` to local `jb/`. `tfp0test` has a pre-built
arm64 binary. `MetalTest` requires building: `cd jb/MetalTest && bash build.sh` (needs Xcode
iPhone SDK). Both use `signcert.p12` for signing. Upload to guest and run to validate kernel
patches:
```bash
# On guest — test tfp0 (kernel r/w primitive)
scp -P 22222 jb/tfp0test/tfp0test root@<vm-ip>:/tmp/
ssh root@<vm-ip> -p 22222 '/tmp/tfp0test'

# On guest — test Metal GPU (requires Metal bundle installed)
# Build first: cd jb/MetalTest && bash build.sh
scp -P 22222 jb/MetalTest/MetalTest root@<vm-ip>:/tmp/
ssh root@<vm-ip> -p 22222 '/tmp/MetalTest'
```

### 18. [ ] TrollVNC Installation Steps

Current repo has TrollVNC submodule but DETAILED_GUIDE doesn't cover build/install steps for the VNC server binary on the guest.

### 19. [ ] Disk Space Requirements

No explicit disk space requirements documented anywhere. Estimated needs:
- IPSWs: ~11 GB
- Mixed firmware: ~10 GB
- VM disk: ~40 GB sparse
- Build artifacts: ~2 GB
- **Total: ~60-70 GB free recommended**

---

## Things DETAILED_GUIDE Does Better Than Original

For reference — these are improvements in the current flow that the original lacks:

1. **Checkpoint system** — 4 tarball snapshots for resuming from intermediate stages
2. **`--verify-only` and `--dry-run`** — Non-destructive patch validation
3. **NONC validation in `boot_rd.sh`** — Validates APNonce before/after iBSS, with retry logic
4. **Expected-opcode verification** — Checks unpatched values match before patching (won't silently corrupt)
5. **TXM re-restore workflow** — Documented procedure (Section 15)
6. **Full end-to-end checklist** — Section 16 with copy-pasteable commands
7. **Extensive troubleshooting** — Panic docs, SSH pitfalls, port confusion
8. **Hook signing before upload** — Signs systemhook/launchdhook/libellekit before SCP (fixes code signature failures original had)
9. **`launchd` direct-run stdout bypass** — New patch at 0x17738 not in original
10. **Stale artifact cleanup** — `prepare_ramdisk.py` removes old signed files before regenerating
11. **Multiple runtime paths** — Documents both original-research tart and current vphone-cli approaches
