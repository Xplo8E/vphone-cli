# Launchdhook Assertion Handoff (2026-03-06)

## Scope

This note captures the current userspace-side findings for the failing `fw_patch_jb + cfw_install_jb` path.
It is intended as a handoff artifact for follow-up work on the `fix-boot` branch.

The current symptom is no longer "launchd does not start".
The updated symptom is:

- `launchd` starts
- injected `launchdhook.dylib` definitely loads
- `launchd` then hits an early internal assertion before the expected `bash` / follow-on job chain stabilizes

## Executive Summary

### Confirmed

- The original JB `LC_LOAD_DYLIB /cores/launchdhook.dylib` approach is structurally unsafe on the current `launchd` sample because there is not enough load-command slack.
- A short-path alias experiment fixed the Mach-O header-space problem:
  - `/cores/launchdhook.dylib` requires 56 bytes and overruns into `__TEXT,__text`
  - `/cores/b` still requires 40 bytes and also overruns
  - `/b` requires 32 bytes and fits exactly after removing `LC_CODE_SIGNATURE`
- Runtime test with `/b` proves the short-path alias loads successfully, but the main failure remains:
  - `launchdhook.dylib` prints its startup logs
  - `launchd` then asserts early: `launchd + 59944 ... 0xffffffffffffffff`

### Current conclusion

The short-path `/b` alias fixes the **injection-space** problem, but does **not** fix the **launchd assertion**.
So the remaining problem is now more likely in the hook logic (especially early XPC / daemon config hooks) than in the raw load-command insertion path.

## Evidence Collected

### 1. Mach-O injection space audit

Local dry-run against `vm/.cfw_temp/launchd` established the following:

- Existing load-command slack before the first section: 16 bytes
- After stripping `LC_CODE_SIGNATURE`: 32 bytes
- Required command sizes:
  - `/cores/launchdhook.dylib` -> 56 bytes
  - `/cores/b` -> 40 bytes
  - `/b` -> 32 bytes

Observed effect of the original long-path injection:

- `LC_LOAD_DYLIB /cores/launchdhook.dylib` overwrote the beginning of `__TEXT,__text`
- first instructions at the start of the text section were replaced by injected path bytes

Observed effect of the short-path injection:

- `LC_LOAD_DYLIB /b` fits exactly in the available 32 bytes after `LC_CODE_SIGNATURE` removal
- no additional overwrite into `__TEXT,__text` is needed for that path

### 2. Device-side mount and payload verification

Inside ramdisk shell, manual mount and inspection showed:

- `/dev/disk1s1` mounted at `/mnt1`
- `/dev/disk1s5` mounted at `/mnt5`
- `/mnt1/b` exists and is a Mach-O dylib
- `/mnt1/cores/launchdhook.dylib` exists and is a Mach-O dylib
- `/mnt1/cores/systemhook.dylib` and `/mnt1/cores/libellekit.dylib` are also present

Important clarification:

- `/.b` is an existing hidden root directory on this filesystem and is unrelated to the alias experiment
- the experiment path is `/b`, not `/.b`

### 3. Runtime serial log after switching to `/b`

The following lines appeared during boot:

- `set JB_ROOT_PATH = /private/preboot/<hash>/jb-vphone/procursus`
- `=========== hello from launchdhook.dylib ===========`
- `=========== bye from launchdhook.dylib ===========`
- `com.apple.xpc.launchd ... assertion failed: ... launchd + 59944 ... 0xffffffffffffffff`

Interpretation:

- `/b` injection is working
- `launchdhook.dylib` is loaded and runs its initializer path
- the failure is no longer attributable to the long path not loading or to the Mach-O injection missing outright

## Source-Backed Analysis from Dopamine BaseBin

Source tree used:

- `/Users/qaq/Documents/GitHub/Dopamine/BaseBin`

### 1. launchdhook initialization order

From `Dopamine/BaseBin/launchdhook/src/main.m`, the constructor initializes hooks in this order:

1. `initXPCHooks();`
2. `initDaemonHooks();`
3. `initSpawnHooks();`
4. `initIPCHooks();`
5. `initJetsamHook();`

This matters because the current assertion happens very early, after `launchdhook` has definitely run.
That makes the earlier hooks higher-priority suspects than spawn-time behavior.

### 2. What `initDaemonHooks()` actually does

From `Dopamine/BaseBin/launchdhook/src/daemon_hook.m`:

- hooks `xpc_dictionary_get_value`
- rewrites behavior for these keys:
  - `LaunchDaemons`
  - `Paths`
  - `com.apple.private.xpc.launchd.userspace-reboot`

Behavior summary:

- appends jailbreak daemon plist entries from:
  - `JBROOT_PATH("/basebin/LaunchDaemons")`
  - `JBROOT_PATH("/Library/LaunchDaemons")`
- appends those same directories to `Paths`
- conditionally returns `com.apple.private.iowatchdog.user-access` when `userspace-reboot` is false/missing

This hook touches exactly the kind of launchd configuration objects that are consulted during early daemon/bootstrap setup.

### 3. What `initSpawnHooks()` actually does

From `Dopamine/BaseBin/launchdhook/src/spawn_hook.c`:

- hooks `__posix_spawn`
- during early boot, it intentionally avoids broad injection until `xpcproxy` appears
- once `xpcproxy` is seen, it flips out of early-boot mode and uses `posix_spawn_hook_shared(...)`

Interpretation:

- spawn hook is real, but it is comparatively later than the daemon config hook
- given the current assertion timing, `initSpawnHooks()` is no longer the top suspect

### 4. What `initXPCHooks()` does

From `Dopamine/BaseBin/launchdhook/src/xpc_hook.c`:

- hooks `xpc_receive_mach_msg`
- participates in jbserver message handling and filtering inside launchd/XPC path

This is also an early-launchd hook and remains a second-tier suspect if daemon-hook isolation does not clear the assertion.

### 5. Runtime jetsam hook vs our static jetsam patch

From `Dopamine/BaseBin/launchdhook/src/jetsam_hook.c`:

- Dopamine also installs a runtime hook on `memorystatus_control`
- this is separate from the repo's static `scripts/patchers/cfw_patch_jetsam.py` binary patch

Therefore two different "jetsam" mechanisms now exist in the failing path:

- static launchd branch patch
- runtime `memorystatus_control` hook

This does not prove either is the current cause, but it means the term "jetsam patch" must be disambiguated in future debugging.

## Current Suspect Ranking

### Highest probability

1. **`initDaemonHooks()` / `daemon_hook.m`**
   - hooks `xpc_dictionary_get_value`
   - mutates `LaunchDaemons` and `Paths`
   - timing matches the observed early `launchd` assertion better than spawn-time logic

### Medium probability

2. **`initXPCHooks()` / `xpc_hook.c`**
   - also runs before spawn hook
   - directly changes launchd/XPC message handling

3. **static `patch-launchd-jetsam` matcher**
   - still considered risky because its matching strategy is heuristic and not CFG-constrained
   - but the `/b` experiment shows the assertion survives after fixing the obvious load-command overflow issue

### Lower probability for the current symptom timing

4. **`initSpawnHooks()` / `spawn_hook.c`**
   - still relevant for later `bash` / job launch failures
   - but no longer the best first suspect for the early `launchd + 59944` assertion

## Recommended Isolation Order for `fix-boot`

### Stage 1: no-daemon-hook control

Goal:

- keep `launchdhook.dylib` loading
- keep `/b` short-path alias experiment in place
- disable only `initDaemonHooks()`

Reason:

- this is the cleanest test of the current top suspect
- if the assertion disappears, the root issue is inside `daemon_hook.m`

### Stage 2: no-xpc-hook control

If stage 1 still asserts:

- restore daemon hook or keep it off, but disable `initXPCHooks()` next
- test whether the assertion is tied to XPC receive hook path instead

### Stage 3: no-spawn-hook control

Only after stages 1 and 2:

- disable `initSpawnHooks()`
- use this to isolate later `bash` / child-process failures if the launchd assertion is already gone or moves later

### Stage 4: revisit static launchd jetsam patch

If all runtime-hook controls still fail:

- re-audit `scripts/patchers/cfw_patch_jetsam.py`
- prefer a source-backed or CFG-backed site selection instead of the current backward-scan heuristic

## Concrete Handoff Notes for Claude

### Facts

- `/b` injection is confirmed working on-device
- `launchdhook.dylib` definitely runs
- launchd still asserts at `launchd + 59944`
- Dopamine source confirms `initDaemonHooks()` runs before `initSpawnHooks()`

### Inference

- the early assertion is more likely to be caused by `daemon_hook.m` or `xpc_hook.c` than by `spawn_hook.c`

### Best next change

Implement a **minimal no-daemon-hook build** first:

- edit `Dopamine/BaseBin/launchdhook/src/main.m`
- temporarily disable only `initDaemonHooks();`
- rebuild `launchdhook.dylib`
- keep `/b` alias loading strategy unchanged for the control run

## Related Files

- `scripts/cfw_install_jb.sh`
- `scripts/patchers/cfw_inject_dylib.py`
- `scripts/patchers/cfw_patch_jetsam.py`
- `research/boot_jb_mount_failure_investigation.md`
- `research/boot_hang_b19_mount_dounmount_strategy_compare.md`
- `Dopamine/BaseBin/launchdhook/src/main.m`
- `Dopamine/BaseBin/launchdhook/src/daemon_hook.m`
- `Dopamine/BaseBin/launchdhook/src/spawn_hook.c`
- `Dopamine/BaseBin/launchdhook/src/xpc_hook.c`
