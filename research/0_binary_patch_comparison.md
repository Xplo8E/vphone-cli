# Patch Comparison: Regular / Development / Jailbreak

## Boot Chain Patches

### AVPBooter

| #   | Patch        | Purpose                          | Regular | Dev | JB  |
| --- | ------------ | -------------------------------- | :-----: | :-: | :-: |
| 1   | `mov x0, #0` | DGST signature validation bypass |    Y    |  Y  |  Y  |

### iBSS

| #   | Patch                               | Purpose                                                       | Regular | Dev | JB  |
| --- | ----------------------------------- | ------------------------------------------------------------- | :-----: | :-: | :-: |
| 1   | Serial labels (2x)                  | "Loaded iBSS" in serial log                                   |    Y    |  Y  |  Y  |
| 2   | `image4_validate_property_callback` | Signature bypass (`b.ne` -> NOP, `mov x0,x22` -> `mov x0,#0`) |    Y    |  Y  |  Y  |
| 3   | Skip `generate_nonce`               | Keep apnonce stable for SHSH (`tbz` -> unconditional `b`)     |    -    |  -  |  Y  |

### iBEC

| #   | Patch                               | Purpose                                    | Regular | Dev | JB  |
| --- | ----------------------------------- | ------------------------------------------ | :-----: | :-: | :-: |
| 1   | Serial labels (2x)                  | "Loaded iBEC" in serial log                |    Y    |  Y  |  Y  |
| 2   | `image4_validate_property_callback` | Signature bypass                           |    Y    |  Y  |  Y  |
| 3   | Boot-args redirect                  | ADRP+ADD -> `serial=3 -v debug=0x2014e %s` |    Y    |  Y  |  Y  |

### LLB

| #   | Patch                               | Purpose                                    | Regular | Dev | JB  |
| --- | ----------------------------------- | ------------------------------------------ | :-----: | :-: | :-: |
| 1   | Serial labels (2x)                  | "Loaded LLB" in serial log                 |    Y    |  Y  |  Y  |
| 2   | `image4_validate_property_callback` | Signature bypass                           |    Y    |  Y  |  Y  |
| 3   | Boot-args redirect                  | ADRP+ADD -> `serial=3 -v debug=0x2014e %s` |    Y    |  Y  |  Y  |
| 4   | Rootfs bypass (5 patches)           | Allow edited rootfs loading                |    Y    |  Y  |  Y  |
| 5   | Panic bypass                        | NOP `cbnz` after `mov w8,#0x328` check     |    Y    |  Y  |  Y  |
| 6   | iOS 18.5 auth-blob gate             | NOP `TBNZ W0,#31` after `system-volume-auth-blob` lookup |  18.5  | 18.5 | 18.5 |

`LLB` patch 6 is profile-scoped to `FIRMWARE_PROFILE=ios18-22F76`. It is not part of legacy/iOS 26 parity. The semantic matcher requires the adjacent `system-volume-auth-blob` / `boot-path` string pair, finds the nearby `BL <auth blob helper>; TBNZ W0,#31,<recovery bail>` pair, and NOPs only that failure branch. On `LLB.vresearch101.RELEASE` from 18.5 `22F76`, this is file offset `0x001CE8`.

### TXM

| #   | Patch                                             | Purpose                                   | Regular | Dev | JB  |
| --- | ------------------------------------------------- | ----------------------------------------- | :-----: | :-: | :-: |
| 1   | Trustcache binary-search bypass                   | `bl hash_cmp` -> `mov x0, #0`             |    Y    |  Y  |  Y  |
| 2   | Selector24 bypass: `mov w0, #0xa1`                | Return PASS (byte 1 = 0) after prologue   |    -    |  Y  |  Y  |
| 3   | Selector24 bypass: `b <epilogue>`                 | Skip validation, jump to register restore |    -    |  Y  |  Y  |
| 4   | get-task-allow (selector 41\|29)                  | `bl` -> `mov x0, #1`                      |    -    |  Y  |  Y  |
| 5   | Selector42\|29 shellcode: branch to cave          | Redirect dispatch stub to shellcode       |    -    |  Y  |  Y  |
| 6   | Selector42\|29 shellcode: NOP pad                 | UDF -> NOP in code cave                   |    -    |  Y  |  Y  |
| 7   | Selector42\|29 shellcode: `mov x0, #1`            | Set return value to true                  |    -    |  Y  |  Y  |
| 8   | Selector42\|29 shellcode: `strb w0, [x20, #0x30]` | Set manifest flag                         |    -    |  Y  |  Y  |
| 9   | Selector42\|29 shellcode: `mov x0, x20`           | Restore context pointer                   |    -    |  Y  |  Y  |
| 10  | Selector42\|29 shellcode: branch back             | Return from shellcode to stub+4           |    -    |  Y  |  Y  |
| 11  | Debugger entitlement (selector 42\|37)            | `bl` -> `mov w0, #1`                      |    -    |  Y  |  Y  |
| 12  | Developer mode bypass                             | NOP conditional guard before deny path    |    -    |  Y  |  Y  |

## Kernelcache

### Base Patches (All Variants)

| #     | Patch                      | Function                         | Purpose                                            | Regular | Dev | JB  |
| ----- | -------------------------- | -------------------------------- | -------------------------------------------------- | :-----: | :-: | :-: |
| 1     | NOP `tbnz w8,#5`           | `_apfs_vfsop_mount`              | Skip root snapshot sealed-volume check             |    Y    |  Y  |  Y  |
| 2     | NOP conditional            | `_authapfs_seal_is_broken`       | Skip root volume seal panic                        |    Y    |  Y  |  Y  |
| 3     | NOP conditional            | `_bsd_init`                      | Skip rootvp not-authenticated panic                |    Y    |  Y  |  Y  |
| 4-5   | `mov w0,#0; ret`           | `_proc_check_launch_constraints` | Bypass launch constraints                          |    Y    |  Y  |  Y  |
| 6-7   | `mov x0,#1` (2x)           | `PE_i_can_has_debugger`          | Enable kernel debugger                             |    Y    |  Y  |  Y  |
| 8     | NOP                        | `_postValidation`                | Skip AMFI post-validation                          |    Y    |  Y  |  Y  |
| 9     | `cmp w0,w0`                | `_postValidation`                | Force comparison true                              |    Y    |  Y  |  Y  |
| 10-11 | `mov w0,#1` (2x)           | `_check_dyld_policy_internal`    | Allow dyld loading                                 |    Y    |  Y  |  Y  |
| 12    | `mov w0,#0`                | `_apfs_graft`                    | Allow APFS graft                                   |    Y    |  Y  |  Y  |
| 13    | `cmp x0,x0`                | `_apfs_vfsop_mount`              | Skip mount check                                   |    Y    |  Y  |  Y  |
| 14    | `mov w0,#0`                | `_apfs_mount_upgrade_checks`     | Allow mount upgrade                                |    Y    |  Y  |  Y  |
| 15    | `mov w0,#0`                | `_handle_fsioc_graft`            | Allow fsioc graft                                  |    Y    |  Y  |  Y  |
| 16    | NOP (3x)                   | `handle_get_dev_by_role`         | Bypass APFS role-lookup deny gates for boot mounts |    Y    |  Y  |  Y  |
| 17-26 | `mov x0,#0; ret` (5 hooks) | Sandbox MACF ops table           | Stub 5 sandbox hooks                               |    Y    |  Y  |  Y  |

### JB-Only Kernel Methods (Reference List)

| #     | Group | Method                                | Function                                                                                             | Purpose                                                                                                                                                                              | JB Enabled |
| ----- | ----- | ------------------------------------- | ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :--------: |
| JB-01 | A     | `patch_amfi_cdhash_in_trustcache`     | `AMFIIsCDHashInTrustCache`                                                                           | Always return true + store hash                                                                                                                                                      |     Y      |
| JB-02 | A     | `patch_amfi_execve_kill_path`         | AMFI execve kill return site                                                                         | Convert shared kill return from deny to allow (superseded by C21; standalone only)                                                                                                   |     N      |
| JB-03 | C     | `patch_cred_label_update_execve`      | `_cred_label_update_execve`                                                                          | Reworked C21-v3: C21-v1 already boots; v3 keeps split late exits and additionally ORs success-only helper bits `0xC` after clearing `0x3F00`; still disabled pending boot validation |     N      |
| JB-04 | C     | `patch_hook_cred_label_update_execve` | sandbox `mpo_cred_label_update_execve` wrapper (`ops[18]` -> `sub_FFFFFE00093BDB64`)                 | Faithful upstream C23 trampoline: copy `VSUID`/`VSGID` owner state into pending cred, set `P_SUGID`, then branch back to wrapper                                                     |     Y      |
| JB-05 | C     | `patch_kcall10`                       | `sysent[439]` (`SYS_kas_info` replacement)                                                           | Rebuilt ABI-correct kcall cave: `target + 7 args -> uint64 x0`; re-enabled after focused dry-run validation                                                                          |     Y      |
| JB-06 | B     | `patch_post_validation_additional`    | `_postValidation` (additional)                                                                       | Disable SHA256-only hash-type reject                                                                                                                                                 |     Y      |
| JB-07 | C     | `patch_syscallmask_apply_to_proc`     | syscallmask apply wrapper (`_proc_apply_syscall_masks` path)                                         | Faithful upstream C22: mutate installed Unix/Mach/KOBJ masks to all-ones via structural cave, then continue into setter; distinct from `NULL`-mask alternative                       |     Y      |
| JB-08 | A     | `patch_task_conversion_eval_internal` | `_task_conversion_eval_internal`                                                                     | Allow task conversion                                                                                                                                                                |     Y      |
| JB-09 | A     | `patch_sandbox_hooks_extended`        | Sandbox MACF ops (extended)                                                                          | Stub remaining 30+ sandbox hooks (incl. IOKit 201..210)                                                                                                                              |     Y      |
| JB-10 | A     | `patch_iouc_failed_macf`              | IOUC MACF shared gate                                                                                | A5-v2: patch only the post-`mac_iokit_check_open` deny gate (`CBZ W0, allow` -> `B allow`) and keep the rest of the IOUserClient open path intact                                    |     Y      |
| JB-11 | B     | `patch_proc_security_policy`          | `_proc_security_policy`                                                                              | Bypass security policy                                                                                                                                                               |     Y      |
| JB-12 | B     | `patch_proc_pidinfo`                  | `_proc_pidinfo`                                                                                      | Allow pid 0 info                                                                                                                                                                     |     Y      |
| JB-13 | B     | `patch_convert_port_to_map`           | `_convert_port_to_map_with_flavor`                                                                   | Skip kernel map panic                                                                                                                                                                |     Y      |
| JB-14 | B     | `patch_bsd_init_auth`                 | `_bsd_init` rootauth-failure branch                                                                  | Ignore `FSIOC_KERNEL_ROOTAUTH` failure in `bsd_init`; same gate as base patch #3 when layered                                                                                        |     Y      |
| JB-15 | B     | `patch_dounmount`                     | `_dounmount`                                                                                         | Allow unmount via upstream coveredvp cleanup-call NOP                                                                                                                                |     Y      |
| JB-16 | B     | `patch_io_secure_bsd_root`            | `AppleARMPE::callPlatformFunction` (`"SecureRootName"` return select), called from `IOSecureBSDRoot` | Force `"SecureRootName"` policy return to success without altering callback flow; implementation retargeted 2026-03-06                                                               |     Y      |
| JB-17 | B     | `patch_load_dylinker`                 | `_load_dylinker`                                                                                     | Skip strict `LC_LOAD_DYLINKER == "/usr/lib/dyld"` gate                                                                                                                               |     Y      |
| JB-18 | B     | `patch_mac_mount`                     | `___mac_mount`                                                                                       | Upstream mount-role wrapper bypass (`tbnz` NOP + role-byte zeroing)                                                                                                                  |     Y      |
| JB-19 | B     | `patch_nvram_verify_permission`       | `_verifyPermission` (NVRAM)                                                                          | Allow NVRAM writes                                                                                                                                                                   |     Y      |
| JB-20 | B     | `patch_shared_region_map`             | `_shared_region_map_and_slide_setup`                                                                 | Force root-vs-process-root mount compare to succeed before Cryptex fallback                                                                                                          |     Y      |
| JB-21 | B     | `patch_spawn_validate_persona`        | `_spawn_validate_persona`                                                                            | Upstream dual-`cbz` persona helper bypass                                                                                                                                            |     Y      |
| JB-22 | B     | `patch_task_for_pid`                  | `_task_for_pid`                                                                                      | Allow task_for_pid via upstream early `pid == 0` gate NOP                                                                                                                            |     Y      |
| JB-23 | B     | `patch_thid_should_crash`             | `_thid_should_crash`                                                                                 | Prevent GUARD_TYPE_MACH_PORT crash                                                                                                                                                   |     Y      |
| JB-24 | B     | `patch_vm_fault_enter_prepare`        | `_vm_fault_enter_prepare`                                                                            | Force `cs_bypass` fast path in runtime fault validation                                                                                                                              |     Y      |
| JB-25 | B     | `patch_vm_map_protect`                | `_vm_map_protect`                                                                                    | Skip upstream write-downgrade gate in `vm_map_protect`                                                                                                                               |     Y      |

## CFW Installation Patches

### Binary Patches Applied Over SSH Ramdisk

| #   | Patch                     | Binary                 | Purpose                                                       | Regular | Dev | JB  |
| --- | ------------------------- | ---------------------- | ------------------------------------------------------------- | :-----: | :-: | :-: |
| 1   | `/%s.gl` -> `/AA.gl`      | `seputil`              | Gigalocker UUID fix                                           |    Y    |  Y  |  Y  |
| 2   | NOP cache validation      | `launchd_cache_loader` | Allow modified `launchd.plist`                                |    Y    |  Y  |  Y  |
| 3   | `mov x0,#1; ret`          | `mobileactivationd`    | Activation bypass                                             |    Y    |  Y  |  Y  |
| 4   | Plist injection           | `launchd.plist`        | bash/dropbear/trollvnc/vphoned daemons                        |    Y    |  Y  |  Y  |
| 5   | `b` (skip jetsam guard)   | `launchd`              | Prevent jetsam panic on boot                                  |    -    |  Y  |  Y  |
| 6   | `LC_LOAD_DYLIB` injection | `launchd`              | Load short alias `/b` (copy of `launchdhook.dylib`) at launch |    -    |  -  |  Y  |

### Installed Components

| #   | Component                  | Description                                                                                                        | Regular | Dev | JB  |
| --- | -------------------------- | ------------------------------------------------------------------------------------------------------------------ | :-----: | :-: | :-: |
| 1   | Cryptex SystemOS + AppOS   | Decrypt AEA + mount + copy to device                                                                               |    Y    |  Y  |  Y  |
| 2   | GPU driver                 | AppleParavirtGPUMetalIOGPUFamily bundle                                                                            |    Y    |  Y  |  Y  |
| 3   | `iosbinpack64`             | Jailbreak tools (base set)                                                                                         |    Y    |  Y  |  Y  |
| 4   | `iosbinpack64` dev overlay | Replace `rpcserver_ios` with dev build                                                                             |    -    |  Y  |  -  |
| 5   | `vphoned`                  | vsock HID/control daemon (built + signed)                                                                          |    Y    |  Y  |  Y  |
| 6   | LaunchDaemons              | bash/dropbear/trollvnc/rpcserver_ios/vphoned plists                                                                |    Y    |  Y  |  Y  |
| 7   | MobileGestalt cache patcher | First-boot `CacheExtra["DeviceClassNumber"] = 1` writer                                                            |    -    |  Y  |  -  |
| 8   | MobileGestalt idiom interposer | `arm64e` `/usr/lib/vphone_mg_idiom.dylib`; SpringBoard `/v` re-export shim with in-process MG rebinder; cdhashes appended to StaticTrustCache; no new SpringBoard load-command growth | - | Y | - |
| 9   | Procursus bootstrap        | Bootstrap filesystem + optional Sileo deb                                                                          |    -    |  -  |  Y  |
| 10  | BaseBin hooks              | `systemhook.dylib` / `launchdhook.dylib` / `libellekit.dylib` -> `/cores/` plus `/b` alias for `launchdhook.dylib` |    -    |  -  |  Y  |
| 11  | `TweakLoader.dylib`        | Lean user-tweak loader built from source and installed to `/var/jb/usr/lib/TweakLoader.dylib`                      |    -    |  -  |  Y  |

### CFW Installer Flow Matrix (Script-Level)

| Flow Item                                     | Regular (`cfw_install.sh`)      | Dev (`cfw_install_dev.sh`) | JB (`cfw_install_jb.sh`)                      |
| --------------------------------------------- | ------------------------------- | -------------------------- | --------------------------------------------- |
| Base CFW phases (1/7 -> 7/7)                  | Runs directly                   | Runs directly              | Runs via `CFW_SKIP_HALT=1 zsh cfw_install.sh` |
| Dev overlay (`rpcserver_ios` replacement)     | -                               | Y (`apply_dev_overlay`)    | -                                             |
| SSH readiness wait before install             | Y (`wait_for_device_ssh_ready`) | -                          | Y (inherited from base run)                   |
| launchd jetsam patch (`patch-launchd-jetsam`) | -                               | Y (base-flow injection)    | Y (JB-1)                                      |
| launchd dylib injection (`inject-dylib /b`)   | -                               | -                          | Y (JB-1)                                      |

| Procursus bootstrap deployment | - | - | Y (JB-2) |
| BaseBin hook deployment (`*.dylib` -> `/mnt1/cores`) | - | - | Y (JB-3) |
| First-boot JB finalization (`vphone_jb_setup.sh`) | - | - | Y (post-boot; now fails before done marker if TrollStore Lite install does not complete) |
| Additional input resources | `cfw_input` | `cfw_input` + `resources/cfw_dev/rpcserver_ios` | `cfw_input` + `cfw_jb_input` |
| Extra tool requirement beyond base | - | - | `zstd` |
| Halt behavior | Halts unless `CFW_SKIP_HALT=1` | Halts unless `CFW_SKIP_HALT=1` | Always halts after JB phases |

## Summary

| Component                | Regular | Dev |  JB |
| ------------------------ | ------: | --: | --: |
| AVPBooter                |       1 |   1 |   1 |
| iBSS                     |       2 |   2 |   3 |
| iBEC                     |       3 |   3 |   3 |
| LLB                      |       6 |   6 |   6 |
| TXM                      |       1 |  12 |  12 |
| Kernel (base)            |      28 |  28 |  28 |
| Kernel (JB methods)      |       - |   - |  59 |
| Boot chain total         |      41 |  52 | 112 |
| CFW binary patches       |       4 |   5 |   6 |
| CFW installed components |       6 |   8 |   9 |
| CFW total                |      10 |  13 |  15 |
| Grand total              |      51 |  65 | 127 |

## Ramdisk Variant Matrix

| Variant       | Pre-step            | `Ramdisk/txm.img4`               | `Ramdisk/krnl.ramdisk.img4`                                                      | `Ramdisk/krnl.img4`                       | Effective kernel used by `ramdisk_send.sh`          |
| ------------- | ------------------- | -------------------------------- | -------------------------------------------------------------------------------- | ----------------------------------------- | --------------------------------------------------- |
| `RAMDISK`     | `make fw_patch`     | release TXM + base TXM patch (1) | base kernel (28), legacy `*.ramdisk` preferred else derive from pristine CloudOS | restore kernel from `fw_patch` (28)       | `krnl.ramdisk.img4` preferred, fallback `krnl.img4` |
| `DEV+RAMDISK` | `make fw_patch_dev` | release TXM + base TXM patch (1) | base kernel (28), same derivation rule                                           | restore kernel from `fw_patch_dev` (28)   | `krnl.ramdisk.img4` preferred, fallback `krnl.img4` |
| `JB+RAMDISK`  | `make fw_patch_jb`  | release TXM + base TXM patch (1) | base kernel (28), same derivation rule                                           | restore kernel from `fw_patch_jb` (28+59) | `krnl.ramdisk.img4` preferred, fallback `krnl.img4` |

### iOS 18.5 `ios18-22F76` Ramdisk Kernel Exception

The legacy matrix above is still valid for the vphone600 path. The 18.5 `vresearch101` profile is intentionally different after runtime validation:

| Profile        | `Ramdisk/krnl.ramdisk.img4` behavior | Effective kernel used by `ramdisk_send.sh` | Evidence |
| -------------- | ------------------------------------- | ------------------------------------------ | -------- |
| `ios18-22F76`  | Do not generate/prefer it             | `krnl.img4` from the restore-patched kernel | Generated `krnl.ramdisk.img4` completed iBoot transfer but hung after `bootx` with no kernel serial/usbmux. `krnl.img4` booted the SSH ramdisk to `SSHRD_Script` and SSH `ready` on port 2222. |

## Cross-Version Dynamic Snapshot

| Case                | TXM_JB_PATCHES | KERNEL_JB_PATCHES |
| ------------------- | -------------: | ----------------: |
| PCC 26.1 (`23B85`)  |             14 |                59 |
| PCC 26.3 (`23D128`) |             14 |                59 |
| iOS 26.1 (`23B85`)  |             14 |                59 |
| iOS 26.3 (`23D127`) |             14 |                59 |

## Swift Migration Notes (2026-03-10)

- Swift `FirmwarePatcher` now matches the Python reference patch output across all checked components:
  - `avpbooter` 1/1
  - `ibss` 4/4
  - `ibec` 7/7
  - `llb` 13/13
  - `txm` 1/1
  - `txm_dev` 12/12
  - `kernelcache` 28/28
  - `ibss_jb` 1/1
  - `kernelcache_jb` 84/84
- JB parity fixes completed in Swift:
  - C23 `vnode_getattr` resolution now follows the Python backward BL scan and resolves `0x00CD44F8`.
  - C22 syscallmask cave encodings were corrected and centralized in `ARM64Constants.swift`.
  - Task-conversion matcher masks and kernel-text scan range were corrected, restoring the patch at `0x00B0C400`.
  - `jbDecodeBranchTarget()` now correctly decodes `cbz/cbnz`, restoring the real `_bsd_init` rootauth gate at `0x00F7798C`.
  - IOUC MACF matching now uses Python-equivalent disassembly semantics for the aggregator shape, restoring the deny-to-allow patch at `0x01260644`.
- C24 `kcall10` cave instruction bytes were re-verified against macOS `clang`/`as`; no Swift byte changes were needed.
- The Swift pipeline is now directly invokable from the product binary:
  - `vphone-cli patch-firmware --vm-directory <dir> --variant {regular|dev|jb}`
  - `vphone-cli patch-component --component {txm|kernel-base} --input <file> --output <raw>` is available for non-firmware tooling that still needs a single patched payload during ramdisk packaging
  - default loader now preserves IM4P containers via `IM4PHandler`
  - DeviceTree patching now uses the real Swift `DeviceTreePatcher` in the pipeline
  - project `make fw_patch`, `make fw_patch_dev`, and `make fw_patch_jb` targets now invoke this Swift pipeline via the unsigned debug `vphone-cli` build, while the signed release build remains reserved for VM boot/DFU paths
  - on 2026-03-11, the legacy Python firmware patcher entrypoints and patch modules were temporarily restored from pre-removal history for parity/debug work.
  - after byte-for-byte parity was revalidated against Python on `26.1` and `26.3` for `regular`, `dev`, and `jb`, those legacy firmware-patcher Python sources and transient comparison/export helpers were removed again so the repo keeps Swift as the single firmware-patching implementation.
- Swift pipeline follow-up fixes completed after CLI bring-up:
  - `findFile()` now supports glob patterns such as `AVPBooter*.bin` instead of treating them as literal paths.
  - JB variant sequencing now runs base iBSS/kernel patchers first, then the JB extension patchers.
  - Sequential pipeline application now merges each patcher's `PatchRecord` writes onto the shared output buffer while keeping later patcher searches anchored to the original payload, matching the standalone Swift/Python validation model.
  - `apply()` now reuses an already-populated `patches` array instead of re-running `findAll()`, so `patch-firmware` / `patch-component` no longer double-scan or double-print the same component diagnostics on a single invocation.
  - unaligned integer reads across the firmware patcher now go through a shared safe `Data.loadLE(...)` helper, fixing the JB IM4P crash (`Swift/UnsafeRawPointer.swift:449` misaligned raw pointer load).
  - `TXMPatcher` now preserves pristine Python parity by preferring the legacy trustcache binary-search site when present, and only falls back to the selector24 hash-flags call chain (`ldr x1, [x20,#0x38]` -> `add x2, sp, #4` -> `bl` -> `ldp x0, x1, [x20,#0x30]` -> `add x2, sp, #8` -> `bl`) when rerunning on a VM tree that already carries the dev/JB selector24 early-return patch.
  - `TXMDevPatcher` now resolves cstring references through Mach-O segment VM addresses for iOS 18.5 TXM. It supports direct `ADR` refs and ADRP+ADD refs while keeping the flat offset fallback for older payloads. This restores the 12-record dev TXM set on `cloudOS_18.5_22F76` `txm.iphoneos.research.im4p`.
  - The iOS 18.5 TXM developer-mode patch shape changed from a legacy adjacent guard NOP to `cbz w9, force_enable -> b force_enable` at file offset `0x01B9C4`; this keeps the patch semantic as "force developer mode enabled" instead of blindly NOPing the new branch.
  - `vphone-cli patch-component` now accepts `--component txm-dev` for direct dev TXM verification outside a full restore tree.
  - `DeviceTreePatcher` now selects profile-specific patch sets. The `legacy` profile still requires the old vphone600 `buttons/home-button-type` and `island-notch-location` fields; `ios18-22F76` skips those absent legacy nodes and patches only `serial-number` plus existing `product/artwork-device-subtype`.
  - `vphone-cli patch-component` now accepts `--component device-tree --firmware-profile <profile>` for direct DeviceTree verification outside a full restore tree.
  - Kernel patch `[8]` now accepts the iOS 18.5 post-validation branch shape after `TXM [Error]: CodeSignature`: `cmp w8,#1; b.eq error_path` is NOPed, while legacy `tbnz`/`tbz`/`cbz`/`cbnz` shapes remain supported by the same semantic scan.
  - Kernel patch `[16]` now prefers the branch immediately after the `com.apple.apfs.get-dev-by-role` entitlement check and recognizes the iOS 18.5 entitlement-deny line ID `0x3EC2`, while keeping legacy APFS line IDs `0x332D` and `0x333B`.
  - `IBootPatcher` now accepts a firmware profile. For `ios18-22F76` LLB only, it adds the experimental LocalPolicy boot-object bypass: `system-volume-auth-blob` lookup failure branch `TBNZ W0,#31` -> `NOP`. Direct verifier on the real 18.5 LLB emitted `0x001CE8: tbnz w0,#0x1f,0x1d90 -> nop`.
  - `vphone-cli patch-component` now accepts `--component llb --firmware-profile <profile>` for direct LLB verification outside a full restore tree.
  - `scripts/fw_prepare.sh` now deletes stale sibling `*Restore*` directories in the working VM directory before patching continues, so a fresh `make fw_prepare && make fw_patch` cannot accidentally select an older prepared firmware tree (for example `26.1`) when a newer one (for example `26.3`) was just generated.
- IM4P/output parity fixes completed after synthetic full-pipeline comparison:
  - `IM4PHandler.save()` no longer forces a generic LZFSE re-encode.
  - Swift now rebuilds IM4Ps in the same effective shape as the Python patch flow and only preserves trailing `PAYP` metadata for `TXM` (`trxm`) and `kernelcache` (`krnl`).
  - `IBootPatcher` serial labels now match Python casing exactly (`Loaded iBSS`, `Loaded iBEC`, `Loaded LLB`).
  - `DeviceTreePatcher` now serializes the full patched flat tree, matching Python `dtree.py`, instead of relying on in-place property writes alone.
- Synthetic CLI dry-run status on 2026-03-10 using IM4P-backed inputs under `ipsws/patch_refactor_input`:
  - regular: 58 patch records
  - dev: 69 patch records
  - jb: 154 patch records
- Full synthetic Python-vs-Swift pipeline comparison status on 2026-03-10 using `scripts/compare_swift_python_pipeline.py`:
  - regular: all 7 component payloads match
  - dev: all 7 component payloads match
  - jb: all 7 component payloads match
- Real prepared-firmware Python-vs-Swift pipeline comparison status on 2026-03-10 using `vm/` after `make fw_prepare`:
  - historical note: the now-removed `scripts/compare_swift_python_pipeline.py` cloned only the prepared `*Restore*` tree plus `AVPBooter*.bin`, `AVPSEPBooter*.bin`, and `config.plist`, avoiding `No space left on device` failures from copying `Disk.img` after `make vm_new`.
  - regular: all 7 component payloads match
  - dev: all 7 component payloads match
  - jb: all 7 component payloads match
- Runtime validation blocker observed on 2026-03-10:
  - `NONE_INTERACTIVE=1 SKIP_PROJECT_SETUP=1 make setup_machine JB=1` reaches the Swift patch stage and reports `[patch-firmware] applied 154 patches for jb`, then fails when the flow transitions into `make boot_dfu`.
  - `make boot_dfu` originally failed at launch-policy time with exit `137` / signal `9` because the release `vphone-cli` could not launch on this host.
  - `amfidont` was then validated on-host:
    - it can attach to `/usr/libexec/amfid`
    - the initial path allow rule failed because `AMFIPathValidator` reports URL-encoded paths (`/Volumes/My%20Shared%20Files/...`)
    - rerunning `amfidont` with the encoded project path and the release-binary CDHash allows the signed release `vphone-cli` to launch
    - this workflow is now packaged as `make amfidont_allow_vphone` / `scripts/start_amfidont_for_vphone.sh`
  - With launch policy bypassed, `make boot_dfu` advances into VM setup, emits `vm/udid-prediction.txt`, and then fails with `VZErrorDomain Code=2 "Virtualization is not available on this hardware."`
  - `VPhoneAppDelegate` startup failure handling was tightened so these fatal boot/DFU startup errors now exit non-zero; `make boot_dfu` now reports `make: *** [boot_dfu] Error 1` for the nested-virtualization failure instead of incorrectly returning success.
  - The host itself is a nested Apple VM (`Model Name: Apple Virtual Machine 1`, `kern.hv_vmm_present=1`), so the remaining blocker is lack of nested Virtualization.framework availability rather than firmware patching or AMFI bypass.
  - `boot_binary_check` now uses strict host preflight and fails earlier on this class of host with `make: *** [boot_binary_check] Error 3`, avoiding a wasted VM-start attempt once the nested-virtualization condition is already known.
  - Added `make boot_host_preflight` / `scripts/boot_host_preflight.sh` to capture this state in one command:
    - model: `Apple Virtual Machine 1`
    - `kern.hv_vmm_present`: `1`
    - SIP: disabled
    - `allow-research-guests`: disabled
    - current `kern.bootargs`: empty
    - next-boot `nvram boot-args`: `amfi_get_out_of_my_way=1 -v` (staged on 2026-03-10; requires reboot before it affects launch policy)
    - `spctl --status`: assessments enabled
    - `spctl --assess` rejects the signed release binary
    - unsigned debug `vphone-cli --help`: exit `0`
    - signed release `vphone-cli --help`: exit `137`
    - freshly signed debug control binary `--help`: exit `137`

## Automation Notes (2026-03-06)

- `scripts/setup_machine.sh` non-interactive flow fix: renamed local variable `status` to `boot_state` in first-boot log wait and boot-analysis wait helpers to avoid zsh `status` read-only special parameter collision.
- `scripts/setup_machine.sh` non-interactive first-boot wait fix: replaced `(( waited++ ))` with `(( ++waited ))` in `monitor_boot_log_until` to avoid `set -e` abort when arithmetic expression evaluates to `0`.
- `scripts/jb_patch_autotest.sh` loop fix for sweep stability under `set -e`: replaced `((idx++))` with `(( ++idx ))`.
- `scripts/jb_patch_autotest.sh` zsh compatibility fix: renamed per-case result variable `status` to `case_status` to avoid `status` read-only special parameter collision.
- `scripts/jb_patch_autotest.sh` selection logic update:
  - default run now excludes methods listed in `KernelJBPatcher._DEV_SINGLE_WORKING_METHODS` (pending-only sweep).
  - set `JB_AUTOTEST_INCLUDE_WORKING=1` to include already-working methods and run the full list.
- Sweep run record:
  - `setup_logs/jb_patch_tests_20260306_114417` (2026-03-06): aborted at `[1/20]` with `read-only variable: status` in `jb_patch_autotest.sh`.
  - `setup_logs/jb_patch_tests_20260306_115027` (2026-03-06): rerun after `status` fix, pending-only mode (`Total methods: 19`).
- Final run result from `jb_patch_tests_20260306_115027` at `2026-03-06 13:17`:
  - Finished: 19/19 (`PASS=15`, `FAIL=4`, all fails `rc=2`).
  - Failing methods at that time: `patch_bsd_init_auth`, `patch_io_secure_bsd_root`, `patch_vm_fault_enter_prepare`, `patch_cred_label_update_execve`.
  - 2026-03-06 follow-up: `patch_io_secure_bsd_root` failure is now attributed to a wrong-site patch in `AppleARMPE::callPlatformFunction` (`"SecureRoot"` gate at `0xFFFFFE000836E1F0`), not the intended `"SecureRootName"` deny-return path. The code was retargeted the same day to `0xFFFFFE000836E464` and re-enabled for the next restore/boot check.
  - 2026-03-06 follow-up: `patch_bsd_init_auth` was retargeted after confirming the old matcher was hitting unrelated code; keep disabled in default schedule until a fresh clean-baseline boot test passes.
  - Final case: `[19/19] patch_syscallmask_apply_to_proc` (`PASS`).
  - 2026-03-06 re-analysis: that historical `PASS` is now treated as a false positive for functionality, because the recorded bytes landed at `0xfffffe00093ae6e4`/`0xfffffe00093ae6e8` inside `_profile_syscallmask_destroy` underflow handling, not in `_proc_apply_syscall_masks`.
  - 2026-03-06 code update: `scripts/patchers/kernel_jb_patch_syscallmask.py` was rebuilt to target the real syscallmask apply wrapper structurally and now dry-runs on `PCC-CloudOS-26.1-23B85 kernelcache.research.vphone600` with 3 writes: `0x02395530`, `0x023955E8`, and cave `0x00AB1720`. User-side boot validation succeeded the same day.
- 2026-03-06 follow-up: `patch_kcall10` was rebuilt from the old ABI-unsafe pseudo-10-arg design into an ABI-correct `sysent[439]` cave. Focused dry-run on `PCC-CloudOS-26.1-23B85 kernelcache.research.vphone600` now emits 4 writes: cave `0x00AB1720`, `sy_call` `0x0073E180`, `sy_arg_munge32` `0x0073E188`, and metadata `0x0073E190`; the method was re-enabled in `_GROUP_C_METHODS`.
  - Observed failure symptom in current failing set: first boot panic before command injection (or boot process early exit).
- Post-run schedule change (per user request):
  - commented out failing methods from default `KernelJBPatcher._PATCH_METHODS` schedule in `scripts/patchers/kernel_jb.py`:
    - `patch_bsd_init_auth`
    - `patch_io_secure_bsd_root`
    - `patch_vm_fault_enter_prepare`
    - `patch_cred_label_update_execve`
- 2026-03-06 re-research note for `patch_cred_label_update_execve`:
  - old entry-time early-return strategy was identified as boot-unsafe because it skipped AMFI exec-time `csflags` and entitlement propagation entirely.
  - implementation was reworked to a success-tail trampoline that preserves normal AMFI processing and only clears restrictive `csflags` bits on the success path.
  - default JB schedule still keeps the method disabled until the reworked strategy is boot-validated.
- Manual DEV+single (`setup_machine` + `PATCH=<method>`) working set now includes:
  - `patch_amfi_cdhash_in_trustcache`
  - `patch_amfi_execve_kill_path`
  - `patch_task_conversion_eval_internal`
  - `patch_sandbox_hooks_extended`
  - `patch_post_validation_additional`
- 2026-03-07 host-side note:
  - reviewed private Virtualization.framework display APIs against the recorder pipeline in `sources/vphone-cli/VPhoneScreenRecorder.swift`.
  - replaced the old AppKit-first recorder path with a private-display-only implementation built around hidden `VZGraphicsDisplay._takeScreenshotWithCompletionHandler:` capture.
  - added still screenshot actions that can copy the captured image to the pasteboard or save a PNG to disk using the same private capture path.
  - `make build` is used as the sanity check path; live VM validation is still needed to confirm the exact screenshot object type returned on macOS 15.
- 2026-03-15 tooling source sync update:
  - removed ad-hoc `git clone` source fetching from `scripts/setup_tools.sh` and `scripts/setup_libimobiledevice.sh`.
  - added pinned git-submodule sources under `scripts/repos/` for: `trustcache`, `insert_dylib`, `libplist`, `libimobiledevice-glue`, `libusbmuxd`, `libtatsu`, `libimobiledevice`, `libirecovery`, `idevicerestore`.
  - setup scripts now initialize required submodules via `git submodule update --init --recursive <path>` and stage build copies under local tool build directories.

## iOS 18.5 UIKitCore Idiom Resolver Patch

SpringBoard and AccessibilityUIServer continued to crash inside `_UIDeviceNativeUserInterfaceIdiomIgnoringClassic` even after the MobileGestalt cache contained `CacheExtra["DeviceClassNumber"] = 1`. IDA/`ipsw` evidence showed the failing UIKitCore function lives at unslid `0x185599978` in the iOS 18.5 SystemOS dyld shared cache. `ipsw dyld a2o` resolves it to subcache `dyld_shared_cache_arm64e.03`, aggregate cache offset `0x5599978`, subcache-local file offset `0x1a5978`.

Patch target:

```text
/System/Library/Caches/com.apple.dyld/dyld_shared_cache_arm64e.03 + 0x1a5978
before: 7f2303d5 f44fbea9    pacibsp; stp x20, x19, [sp, #-0x20]!
after:  000080d2 c0035fd6    mov x0, #0; ret
```

This forces `_UIDeviceNativeUserInterfaceIdiomIgnoringClassic` to return `UIUserInterfaceIdiomPhone` directly and bypasses the MobileGestalt answer path entirely. The mounted SystemOS Cryptex DMG is sealed/read-only, so the patch is applied after Cryptex contents are copied onto the writable restored rootfs under `/mnt1/System/Cryptexes/OS/...`. `scripts/cfw_install_dev.sh` now applies this patch during phase `1/8`, and `scripts/ios18_patch_uikit_idiom_from_ramdisk.sh` provides a one-off ramdisk patch path for existing installs.

Implementation notes for the UIKitCore patch:

- Use subcache-local file offset `0x1a5978`, not aggregate cache offset `0x5599978`, when writing into `dyld_shared_cache_arm64e.03` directly.
- Use `xxd -r -p` to materialize bytes on the ramdisk. Shell `printf '\x..'` is not reliable there and previously produced literal ASCII bytes (`7830307830307838`) before being repaired.
- Verification command shape: `dd if=<subcache> bs=1 skip=1726840 count=8 | xxd -p` must return `000080d2c0035fd6`.

## iOS 18.5 CODESIGNING: Invalid Page SIGKILLs — port JB AMFI patches into dev

The UIKitCore byte-patch modifies a page whose CDHash is baked into the shared-cache code directory. Every process that memory-maps UIKit from `dyld_shared_cache_arm64e.03` (SpringBoard, AccessibilityUIServer, ReportCrash, chronod, ndoagent, webbookmarksd, spaceattributiond, nanotimekitcompaniond, ...) is SIGKILLed by AMFI with:

```json
"exception": {"type":"EXC_CRASH","signal":"SIGKILL - CODESIGNING"}
"termination": {"namespace":"CODESIGNING","indicator":"Invalid Page"}
```

Base + dev patches 8 and 9 (`KernelPatchPostValidation`) already cover TXM CodeSignature errors and the AMFI `postValidation` cmp-rewrite, but neither bypasses `AMFIIsCDHashInTrustCache`, which is the function that reports "this cdhash is not trusted" for our modified page. The JB variant's Group-A method `patch_amfi_cdhash_in_trustcache` rewrites exactly that function to always return 1.

Planned patch-set expansion (not yet applied):

| # | Source file (JB) | Target function | Purpose | Status |
| - | --- | --- | --- | --- |
| DEV-CS-1 | `Kernel/JBPatches/KernelJBPatchAmfiTrustcache.swift` | `AMFIIsCDHashInTrustCache` | Always return 1 + store hash | Planned for dev variant |
| DEV-CS-2 | `Kernel/JBPatches/KernelJBPatchAmfiExecve.swift` | AMFI execve kill return site | Convert deny to allow on exec-time AMFI kill | Planned for dev variant, optional belt-and-suspenders |

Wiring plan in `sources/FirmwarePatcher/Pipeline/FirmwarePipeline.swift`:

- For `.dev`, additionally run `KernelJBPatcher` but only allow the two `patchAmfi*` methods to execute.
- Alternative: factor the two method bodies into a file under `sources/FirmwarePatcher/Kernel/Patches/` and add `patchAmfiCdhashInTrustcache()` / `patchAmfiExecve()` calls from `KernelPatcher.findAll()` gated on the variant. Slightly more Swift plumbing but no per-variant construction logic.

Do not expand to the other Group B / Group C JB methods unless later evidence shows surviving SIGKILLs that those methods specifically cover. The goal is the minimum codesign-relaxation surface needed to keep vphone dev variant functional.

### 2026-04-22 Phase 1 applied: lifted `patchAmfiCdhashInTrustcache` to base kernel patcher

Implementation landed:

- Moved `patchAmfiCdhashInTrustcache` from `KernelJBPatcher` extension to an extension on `KernelPatcherBase` at `sources/FirmwarePatcher/Kernel/Patches/KernelPatchAmfiTrustcache.swift`. Body is unchanged — same semantic match (PACIBSP-bounded function, mov x19,x2 / stp xzr,xzr,[sp,...] / mov x2,sp / bl / mov x20,x0 / cbnz w0 / cbz x19) and same 4-instruction always-allow stub (mov x0,#1 / cbz x2,+8 / str x0,[x2] / ret).
- Deleted the old `sources/FirmwarePatcher/Kernel/JBPatches/KernelJBPatchAmfiTrustcache.swift` to avoid a duplicate-definition ambiguity on `KernelJBPatcher`.
- `KernelPatcher.findAll()` now calls `patchAmfiCdhashInTrustcache()` as patch `9a`, right after the existing AMFI `postValidation` rewrite (patch 9). Applied for regular + dev (both call `KernelPatcher`).
- `KernelJBPatcher.findAll()` still calls `patchAmfiCdhashInTrustcache()` — now resolved via the `KernelPatcherBase` extension, so JB variant keeps the same behaviour.
- `make build` green. No other call sites needed updating.

`patchAmfiExecveKillPath` (DEV-CS-2) was NOT ported. The comparison table shows it as JB-disabled (superseded by C21). If SIGKILLs survive the trustcache patch, port it next.

Next session: `make fw_patch_dev` + DFU restore + `cfw_install_dev` + `make boot`. If SpringBoard stops crashing, the dev-variant codesign bypass works. If not, triage the remaining SIGKILLs and decide whether to port more JB patches.

### 2026-04-22 Phase 2 applied: `make fw_patch_dev` regenerated kernelcache with CS-1

Ran `make fw_patch_dev FIRMWARE_PROFILE=ios18-22F76 VM_DIR=vm`. Summary of kernel output:

```
[CS] AMFIIsCDHashInTrustCache: always allow + store flag
  0x13F0F78: pacibsp                       → mov x0, #1
  0x13F0F7C: sub sp, sp, #0x30             → cbz x2, 0x13F0F84
  0x13F0F80: stp x20, x19, [sp, #0x10]     → str x0, [x2]
  0x13F0F84: stp x29, x30, [sp, #0x20]     → ret
  [19 kernel patches applied]
```

`AMFIIsCDHashInTrustCache` resolved to file offset `0x13F0F78` in the dev kernelcache, shape matched on first candidate, 4 instructions rewritten for the always-allow stub. Total kernel patch count went from 18 to 19.

Noted pre-existing misses (do NOT touch for this session): patches 12, 13, 14, 15 all log `[-] ... not found` on the 18.5 kernelcache. These are APFS-graft / mount validation patches that were written for older kernelcache shapes. They're unrelated to the current SIGKILL work but should be re-researched when we harden the pipeline. `[9] postValidation: cmp w0,w0` also reports `0 sites found` — its anchor string is now different on 18.5 and our new `patchAmfiCdhashInTrustcache` partly covers the same semantic ground (the postValidation CMP-rewrite was about making AMFI's `postValidation` return equal; bypassing `AMFIIsCDHashInTrustCache` short-circuits earlier).

Phase 2 output is written to `vm/iPhone17,3_18.5_22F76_Restore/kernelcache.research.vresearch101` etc. Next phase is the DFU restore cycle.

### 2026-04-22 Phase 3 fix: stale kernelcache corruption after repeated patching

The first ramdisk boot after the AMFI trustcache port made it through iBSS/iBEC and started the kernel, then panicked immediately inside `AppleMobileFileIntegrity`:

```text
panic(cpu 0 caller ...): Undefined kernel instruction: pc=0xfffffe00310f985c instr=7980 @sleh.c:1594
Kernel Extensions in backtrace:
  com.apple.driver.AppleMobileFileIntegrity(1.0.5)
  com.apple.security.sandbox(300.0)
```

Runtime mapping:

- AMFI runtime base: `0xfffffe00310eff10`
- panic PC delta from AMFI base: `0x994c`
- kernelcache load address: `0xfffffe002fd04000`
- raw kernel payload offset: `0x13f585c`

Root cause was a stale/corrupted restore kernelcache, not `irecovery`, AVPBooter, or the new trustcache stub. The restore kernel is an IM4P container, so diagnostics must extract the raw payload before checking offsets. In the bad payload:

```text
0x13f585c: 80 79 00 00 00 80 52 c0 03 5f d6 ...
```

The first word decodes to the undefined instruction `0x00007980`. Clean/current-source patching keeps the instruction aligned and valid:

```text
0x13f585c: 80 79 00 90 00 80 3c 91 fd 7b 41 a9 ...
0x13f5880: 00 00 80 52 c0 03 5f d6 ...
```

This showed an older/bad launch-constraints patch had written a `mov w0,#0; ret` style stub starting three bytes off instruction alignment near `0x13f585f`, while the current patcher correctly stubs `_proc_check_launch_constraints` at aligned offset `0x13f5880`.

Clean rebuild procedure:

1. Stop the panicked DFU VM.
2. Copy pristine CloudOS kernel/iBSS/iBEC/LLB/DeviceTree/TXM inputs from `ipsws/cloudOS_18.5_22F76/` back into `vm/iPhone17,3_18.5_22F76_Restore/`.
3. Rerun `make fw_patch_dev FIRMWARE_PROFILE=ios18-22F76 VM_DIR=vm`.
4. Extract the raw kernel payload and verify:

```text
0x13f0f78: 20 00 80 d2 42 00 00 b4 40 00 00 f9 c0 03 5f d6
0x13f585c: 80 79 00 90 00 80 3c 91 fd 7b 41 a9 f4 4f c2 a8
0x13f5880: 00 00 80 52 c0 03 5f d6 fa 67 01 a9 f8 5f 02 a9
```

After this clean rebuild, `make ramdisk_build` + `make ramdisk_send` completed, iBEC loaded normally, the kernel no longer panicked at AMFI+`0x994c`, and SSHRD booted successfully.

### 2026-04-23 Phase 4 attempt: vm_fault CS bypass not applied

Normal boot after the clean restore still reached userspace but SpringBoard did not stay alive. Serial CrashReporter evidence showed:

```text
SpringBoard throttled after OS_REASON_CODESIGNING
ReportCrash: SIGKILL - CODESIGNING
termination namespace: CODESIGNING
termination indicator: Invalid Page
```

Datamigrator stackshots are secondary: migration plugins wait on services that launchd has already throttled after codesigning exits. The primary failing invariant is still the patched dyld shared-cache page being rejected at runtime while UIKit consumers fault it in.

Implementation state:

- Moved `patchVmFaultEnterPrepare` from `sources/FirmwarePatcher/Kernel/JBPatches/KernelJBPatchVmFault.swift` to `sources/FirmwarePatcher/Kernel/Patches/KernelPatchVmFault.swift`.
- Retargeted it from `KernelJBPatcher` to `KernelJBPatcherBase`, so future symbol-capable patcher layers can reuse the existing semantic matcher without enabling the full JB patch set.
- Kept the repaired matcher semantics: resolve `_vm_fault_enter_prepare` when symbols exist, otherwise scan PACIBSP-bounded functions for the prologue flags load from `[fault_info,#0x28]`, locate the unique `tbz Wflags,#3; mov W?,#0; b ...` gate, and NOP only that gate.
- Tried a `KernelDevCSPatcher` layer after the regular kernel patcher. It was removed from `.dev` wiring because the 18.5 restore kernel has no symbols, no `vm_fault_enter_prepare` string, and the fallback PACIBSP scan still found zero matching CS-bypass gates.
- `.dev` currently remains wired to `KernelPatcher` only. `fw_patch_dev` must not depend on this incomplete vm_fault matcher.

Rationale: `patchAmfiCdhashInTrustcache` covered the trustcache query, but the observed crash reason is `CODESIGNING_EXIT_REASON_INVALID_PAGE`, which XNU reports from the VM fault code-signing violation path. Forcing the existing `cs_bypass` fast-path in `_vm_fault_enter_prepare` is the narrowest existing repo patch that matches this evidence.

Current result: `patchVmFaultEnterPrepare` is still active for the JB patcher only. The dev variant does **not** get a vm_fault patch yet.

`patchAmfiExecveKillPath` remains unported. It targets AMFI exec-time kill returns, while this boot is failing on runtime page validation. Revisit execve only if a later crash report shows taskgated invalid signature or explicit AMFI execve kill evidence.

### 2026-04-23 Phase 5 runtime state: restore/CFW evidence and TXM dirty-input panic

Commands that completed before the current failure thread:

```sh
make fw_patch_dev FIRMWARE_PROFILE=ios18-22F76 VM_DIR=vm
make ramdisk_build FIRMWARE_PROFILE=ios18-22F76 VM_DIR=vm
make ramdisk_send
make restore_get_shsh
make restore
make boot_dfu
make ramdisk_send
make cfw_install_dev
make boot
```

The full restore reached `verify-restore: 100/100`. The post-restore ramdisk and dev CFW path then got far enough to install Cryptex/SystemOS/AppOS and first-boot services. A normal boot reached userspace far enough for these processes to exist:

```text
runningboardd
rpcserver_ios
backboardd
com.apple.datamigrator
vphoned
com.apple.migrationpluginwrapper
ReportCrash
```

`SpringBoard` did not remain alive. CrashReporter and stackshot evidence after the normal boot showed the same primary failure as Phase 4:

```text
SpringBoard throttled after OS_REASON_CODESIGNING
ReportCrash throttled after OS_REASON_CODESIGNING
ReportCrash: SIGKILL - CODESIGNING
termination namespace: CODESIGNING
termination indicator: Invalid Page
```

Observed datamigrator stackshots were secondary symptoms. Migration plugins such as `com.apple.MobileSlideShow`, `com.apple.locationd.migrator`, and `com.apple.sbmigrator` reported hangs or missing pids because launchd was throttling dependent services after codesigning exits. Do not treat the datamigrator stackshot itself as the root cause unless later evidence shows migration-specific corruption.

A separate old panic found in CrashReporter is not the current blocker:

```text
panic-full-2026-04-22-173409.0002.ips
panicString: initproc failed to start -- Library not loaded: /usr/lib/libSystem.B.dylib
Reason: tried: '/usr/lib/libSystem.B.dylib' (no such file, no dyld cache)
```

That panic came from an earlier rootfs/dyld-cache boot attempt. It predates the successful userspace boot with `runningboardd`, `backboardd`, `vphoned`, and datamigrator alive.

After a later `cfw_install_dev` attempt failed at the ramdisk SSH step:

```text
Mounting device rootfs rw...
[ssh] connection lost (attempt 1/3), retrying in 3s...
[ssh] connection lost (attempt 2/3), retrying in 3s...
[ssh] connection lost (attempt 3/3), retrying in 3s...
make: *** [cfw_install_dev] Error 255
```

Host-side checks showed the command was correct, but `127.0.0.1:2222` was not listening. The failure mode is a missing/stopped `pymobiledevice3 usbmux forward 2222 22`, not an incorrect CFW target. Required flow for any repeat CFW install:

```sh
make boot_dfu
make ramdisk_send
source .venv/bin/activate
python -m pymobiledevice3 usbmux forward 2222 22
nc -vz 127.0.0.1 2222
sshpass -p alpine ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 2222 root@localhost 'uname -a'
make cfw_install_dev
```

The newest normal-boot panic is different from the userspace codesigning reports. It is a TXM panic during early root-auth/Image4 handling:

```text
TXM [Error]: Errno: selector: 45 | 78
AppleImage4: trap failed: set boot uuid
AppleImage4: failed to set boot uuid in supervisor: 78
AppleImage4: magazine[cptx]: failed to get nonce: 13
AppleImage4: magazine[c1bt]: failed to get nonce: 6
is_root_hash_authentication_required: disk1s1 Root Volume, root hash authentication is required
panic(cpu 0 caller ...): [TXM] Unhandled synchronous exception taken from GL0 at pc 0xfffffe002f38fe38, lr 0x93dd7e002f390008
Kernel Extensions in backtrace:
  com.apple.sptm(24.5)
  com.apple.txm(24.5)
```

Runtime mapping from that panic:

```text
TXM load address: 0xfffffe002f368000
panic pc:         0xfffffe002f38fe38 -> TXM offset 0x027e38
panic lr:         0xfffffe002f390008 -> TXM offset 0x028008
```

This is adjacent to the dev TXM trustcache patch site observed in patch logs:

```text
TXM trustcache patch site: 0x027e54
```

The staged restore TXM differed from the pristine CloudOS TXM:

```text
ipsws/cloudOS_18.5_22F76/Firmware/txm.iphoneos.research.im4p
  466c2d2684f148533d1342651a98198c0d289fb7e7d3dedb3c94145248433d32

vm/iPhone17,3_18.5_22F76_Restore/Firmware/txm.iphoneos.research.im4p
  02c4c7733c5962696e6911a2a87e57f3174b206032209058e45014797dec95ef
```

Inference: this panic is most likely dirty staged TXM input from repeated `fw_patch_dev` runs, not a new CFW installer issue. During the clean kernelcache rebuild we restored `kernelcache.*`, `Firmware/dfu/`, and `Firmware/all_flash/`, but did not restore `Firmware/txm*.im4p`. That left TXM vulnerable to patch-on-patched drift.

Supporting evidence from prior patch logs: selector24 TXM patch offsets drifted between runs (`0x02CCE0`, `0x02CC3C`, `0x02CB54`). Patch site drift inside the same firmware profile is not expected for a clean deterministic input and should be treated as dirty-input evidence until proven otherwise.

Required clean rebuild before the next restore:

```sh
rsync -a ipsws/cloudOS_18.5_22F76/kernelcache.* vm/iPhone17,3_18.5_22F76_Restore/
rsync -a ipsws/cloudOS_18.5_22F76/Firmware/dfu/ vm/iPhone17,3_18.5_22F76_Restore/Firmware/dfu/
rsync -a ipsws/cloudOS_18.5_22F76/Firmware/all_flash/ vm/iPhone17,3_18.5_22F76_Restore/Firmware/all_flash/
rsync -a ipsws/cloudOS_18.5_22F76/Firmware/txm*.im4p vm/iPhone17,3_18.5_22F76_Restore/Firmware/
make fw_patch_dev FIRMWARE_PROFILE=ios18-22F76 VM_DIR=vm
```

Then run a full restore, not only CFW install, because normal boot consumes the restored boot chain/TXM/kernel artifacts:

```sh
make boot_dfu
make restore_get_shsh
make restore
```

After restore:

```sh
make boot_dfu
make ramdisk_send
source .venv/bin/activate
python -m pymobiledevice3 usbmux forward 2222 22
make cfw_install_dev
make boot
```

Current blocker state:

- `confirmed`: dev normal boot previously reached userspace after full restore and CFW install.
- `confirmed`: SpringBoard/ReportCrash userspace failure reason was `SIGKILL - CODESIGNING`, `Invalid Page`.
- `confirmed`: the newest panic maps into TXM at offset `0x027e38`, adjacent to the TXM trustcache patch region.
- `candidate`: staged TXM was dirty/repatched and caused the TXM synchronous exception.
- `hypothesis`: after restoring pristine TXM inputs and doing one clean `fw_patch_dev` + full restore, the boot should return to the previous userspace codesigning state, at which point the next real patch target remains runtime invalid-page handling in the VM fault path.
