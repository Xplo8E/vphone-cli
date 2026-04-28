# Handoff: vphone-cli iOS 18.5 Boot Path

Last updated: 2026-04-27
Branch: `ios-18-support`

## Project Context

`vphone-cli` (`/Users/vinay/vphone-cli`) — porting an iOS 26-working VM boot pipeline to iOS 18.5. Target: `vresearch101ap` (PCC virtualization, `ComputeModule14,2`). Goal: reach SpringBoard / home screen on iOS 18.5 guest.

Legacy = iOS 26.x cloudOS (works end-to-end). Target = iOS 18.5 build 22F76. No iOS 17 in this project.

## Current State

VM booted normally, **userspace alive**, vphone.sock working, but **stuck at 100% boot progress with no SpringBoard**. Serial shell was lost. Host `vphone.sock` (vphoned protocol) is the remaining channel — supports `ping`, `file_get`, `file_put`, `file_list`, `devmode`, etc. (see `sources/vphone-cli/VPhoneControl.swift` and `scripts/vphoned/vphoned.m`).

## Block-by-block fixes completed (in order, all in tree)

1. **LLB recovery-mode gate** (iOS 18.5 only): patched `TBNZ W0,#0x1F` at file offset `0x001CE8` after `system-volume-auth-blob` lookup. Wired in `IBootPatcher` as profile-scoped patch. Done, working.

2. **fairplayd disabled** to break datamigrator/locationd deadlock chain. `scripts/cfw_install_dev.sh::disable_remote_fairplayd` renames `/System/Library/LaunchDaemons/com.apple.fairplayd*.plist` → `.disabled`. Working.

3. **UIKitCore byte-patch attempt (FAILED, abandoned)** — patched `_UIDeviceNativeUserInterfaceIdiomIgnoringClassic` at `dyld_shared_cache_arm64e.03 + 0x1a5978` to `mov x0,#0; ret`. Caused `SIGKILL - CODESIGNING / Invalid Page` for every UIKit consumer. Now gated behind `VPHONE_UIKIT_DSC_BYTE_PATCH=1` env (off by default). Helper `patch_remote_uikit_idiom` retained but not called.

4. **AMFI trustcache kernel patch attempt (FAILED, reverted)** — moved `patchAmfiCdhashInTrustcache` from JB to base. Did NOT stop the SIGKILLs because "Invalid Page" is emitted by VM-fault page-CS validator, not AMFI cdhash trustcache. Reverted; JB file restored.

## Path 2 In Progress: MobileGestalt Interposer Dylib

Replaces the byte-patch with a runtime DYLD_INSERT_LIBRARIES that overrides `MGCopyAnswer("DeviceClassNumber") → @1`.

**Files added:**
- `scripts/vphone_mg_idiom/vphone_mg_idiom.m` — Objective-C interposer using `__DATA,__interpose`
- `scripts/vphone_mg_idiom/Makefile` — builds arm64 iOS dylib via `xcrun --sdk iphoneos clang`, signs with **plain `ldid -S`** (NO entitlements; original `entitlements.plist` deleted because AMFI rejected dylib-with-entitlements)
- `scripts/patchers/cfw_mg_idiom_inject.py` — Python patcher that injects `DYLD_INSERT_LIBRARIES=/usr/lib/vphone_mg_idiom.dylib` into `EnvironmentVariables` for UIKit jobs: SpringBoard, AccessibilityUIServer, chronod, ndoagent, spaceattributiond, nanotimekitcompaniond, backboardd, datamigrator, migrationpluginwrapper
- `scripts/patchers/mg_idiom_trustcache.py` — appends the signed dylib cdhash to the restore StaticTrustCache and updates BuildManifest digests
- `scripts/patchers/cfw.py` — added `inject-mg-idiom` subcommand
- `scripts/cfw_install_dev.sh` — copies dylib to `/mnt1/usr/lib/vphone_mg_idiom.dylib` and calls `inject-mg-idiom` during install
- `Makefile` — added `mg_idiom` target; `cfw_install_dev` depends on it

Note on `cfw_patch_mobilegestalt.py`: also exists, was an earlier MG cache plist override approach — kept but not actively used (cache-edit approach didn't stick because UIKit reads through different paths).

## Where Path 2 is stuck right now

Last test cycle on the running VM (boot @ 21:37, crash @ 21:38):

- **Dylib on disk: clean (no entitlements).** `ldid -e /usr/lib/vphone_mg_idiom.dylib` returns empty.
- **AMFI no longer complains** in dmesg about `vphone_mg_idiom`.
- **launchd.plist correctly has `DYLD_INSERT_LIBRARIES` set** under `com.apple.SpringBoard`'s `EnvironmentVariables` block (XML form, alongside existing `CA_ASSERT_MAIN_THREAD_TRANSACTIONS`).
- **dyld DOES load the dylib** when run manually with `DYLD_INSERT_LIBRARIES=...` (UUID `920BF9C1-23C2-3E9A-B36E-8A8B73596F68` shows in load list).
- **BUT SpringBoard still crashes with the same NSAssertion** in `_UIDeviceNativeUserInterfaceIdiomIgnoringClassic`. Same SIGABRT, same stack as if interposer never loaded.

**Confirmed refinement:** trust is necessary but still not sufficient for SpringBoard on the normal-boot path. Earlier, `DYLD_INSERT_LIBRARIES` was rejected because `cfw_install_dev.sh` re-signed the temp dylib after `fw_patch_dev` had trusted the built artifact: trustcache contained `c96fc1ccd4e64126b38a8cd2daef3a3617414c58`, while `/usr/lib/vphone_mg_idiom.dylib` had `1d2cde79de73482721b7b3cebef7e0389d567248`. After commenting out the second install-time `ldid_sign`, the installed dylib now matches the trusted CDHash (`c96fc1ccd4e64126b38a8cd2daef3a3617414c58`), and live `launchd.plist` contains `DYLD_INSERT_LIBRARIES=/usr/lib/vphone_mg_idiom.dylib` for `com.apple.SpringBoard`. A fresh `SpringBoard-2026-04-27-201509.ips` still lacks `/usr/lib/vphone_mg_idiom.dylib` in `usedImages` and crashes at `_UIDeviceNativeUserInterfaceIdiomIgnoringClassic`, so dyld/launchd is still not honoring env insertion for this platform job.

**Diagnostic that was about to be run when shell was lost:**

```sh
DYLD_PRINT_LIBRARIES=1 DYLD_PRINT_RESTRICTED=1 DYLD_INSERT_LIBRARIES=/usr/lib/vphone_mg_idiom.dylib /System/Library/CoreServices/SpringBoard.app/SpringBoard --help 2>&1 | head -20
VPHONE_MG_IDIOM_DEBUG=1 DYLD_INSERT_LIBRARIES=/usr/lib/vphone_mg_idiom.dylib /iosbinpack64/bin/ls /dev/null 2>&1 | head
```

These would confirm whether dyld drops the insert (look for "restricted" / dropped env, or absence of `[vphone_mg_idiom] loaded pid=...` line from the dylib's constructor).

## Next steps for the resuming agent

Reach the VM via vphone.sock (serial gone, SSH may also be down):

The host has `vm/vphone.sock` listening (vphoned). Look at `sources/vphone-cli/VPhoneControl.swift` and `scripts/vphoned/vphoned.m` for protocol. Supported types include `ping`, `file_get`, `file_put`, `file_list`, etc. — write a small client (Python or Swift) that connects to that unix socket with length-prefixed JSON to:

1. Confirm dylib state on disk: `file_get /usr/lib/vphone_mg_idiom.dylib` checksum.
2. Check launchd.plist: `file_get /System/Library/xpc/launchd.plist` and grep for `vphone_mg_idiom`.
3. Run a shell command if vphoned exposes one.

If vphoned doesn't have an exec primitive, options:

- **(A) Add a dyld trust cache entry** for the dylib. Implemented in `scripts/patchers/mg_idiom_trustcache.py` and wired into `make fw_patch_dev`. Verified cdhash: `c96fc1ccd4e64126b38a8cd2daef3a3617414c58`. Install must copy this exact built dylib; `cfw_install_dev.sh` now must not re-sign it.

- **(B) ObjC method swizzling instead of `__DATA,__interpose`.** Add a constructor in `vphone_mg_idiom.m` that hooks `+[_UIApplicationInfoParser _computeSupportedInterfaceOrientationsWithInfo:]` and/or `+[UIDevice currentDevice]` directly, returning iPhone idiom. dyld interpose may be ignored, but ObjC swizzle from a dylib that *does* load (constructor fires) would still work — except if dyld drops the load entirely for SpringBoard, same root problem.

- **(C) SpringBoard load-path pivot.** Env-var injection is ignored, and adding a new `LC_LOAD_DYLIB` is confirmed corrupting: IDA showed `sizeofcmds=0x558` and the entrypoint at `0x100000568`, so `insert_dylib` writes the new command over code at file offset `0x568`. Strong `/v` load proved the `arm64e` dylib can load once trusted, but SpringBoard crashed with the same `0x568` SIGILL. A proposed no-growth `Foundation -> /v` replacement was rejected because `vphone_mg_idiom.dylib` is not a Foundation re-export shim; replacing a real platform dependency with it can break dyld binding.

**Current recommendation:** (A) is implemented and required. Do not add new load commands to SpringBoard, and do not replace existing framework load commands unless the replacement dylib re-exports the original install name.

## Untouched background items (not blockers)

- `vm/.cfw_temp/` keeps cached SystemOS/AppOS Cryptex DMGs (4GB, slow to regenerate). Don't delete unless needed.
- `vm/iPhone17,3_18.5_22F76_Restore/` is the patched firmware tree, current with `make fw_patch_dev` from this session.
- `nvram.bin` boot-args: VZMacAuxiliaryStorage doesn't reach iBoot; iBoot reads from a different NVRAM. `IBootPatcher.bootArgs` is the only effective channel for kernel boot-args.

## Key reference files

- `research/ios-18-preparations.md` — full session log, all decisions recorded
- `research/0_binary_patch_comparison.md` — patch matrix per variant
- `research/uikit-idiom-assertion.md` — IDA proof that `DeviceClassNumber=1` is the exact answer needed
- `research/llb-recovery-fallback-analysis.md` — LLB gate root cause

## Active session-end snapshot

- Source tree: clean, builds green, all changes intentional
- VM: stuck at 100% with userspace alive, no SpringBoard, lost serial, vphone.sock open
- Last known crash: `_UIDeviceNativeUserInterfaceIdiomIgnoringClassic` NSAssertion → `abort()` → SIGABRT, every ~1 minute, `consecutiveCrashCount` climbing
- Don't terminate the VM — diagnostic value if the resuming agent can reach it via vphone.sock

The interposer approach is sound, but the deployment vector (DYLD_INSERT_LIBRARIES env on a CS-restricted binary) may be the wrong shape for iOS 18.5. Trustcache + interposer is the proven path.
