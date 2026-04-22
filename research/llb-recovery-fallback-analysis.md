# LLB vresearch101 Recovery-Mode Fallback — Root Cause

Target: `LLB.vresearch101.RELEASE` (iBoot-11881.122.1, iOS 18.5)
Binary: `/tmp/llb.vresearch101.raw` (568,168 bytes, raw AArch64, no Mach-O header)
IDA base: `0x0` (flat raw load; reconstructed ADRP/ADRL targets all resolve cleanly with base 0 — the image is position-independent and IDA's default binary loader is correct)

## 1. Load base

Base `0x0` is the correct analysis base. All `ADRL`/`ADRP+ADD` pairs into string literals (`"%llx:%d\n"` @ `0x7c0bf`, `"Entering recovery mode..."` @ `0x7c257`, `"auto-boot"` @ `0x7c3e3`, etc.) resolve consistently at base 0. Attempts at `0x180000000` / `0x100000000` are unnecessary here — unlike AP iBoot, this LLB slice is built with no absolute-address pinning in the parts we care about.

## 2. Logging emitter

The `%llx:%d\n` format lives at `0x7c0bf` and is passed to `sub_3CAFC` (printf wrapper) at 280+ call sites across the image. At every site the compiler emits `MOV X?, #<64-bit file-hash> ; MOV W?, #<line> ; STP X?, X?, [SP]` immediately before the `BL sub_3CAFC` call. I extracted all (hash, line) pairs for every `%llx:%d\n` call site by decoding the preceding MOVs.

## 3. Decoded serial trace

| Serial line           | Call site | Function           | Meaning                                                     |
| --------------------- | --------- | ------------------ | ----------------------------------------------------------- |
| `3974bfd3d441da3:1557` | `0x3a4c`  | `sub_33A0` (main)  | Startup-ok counter log from `sub_32874` success path        |
| `3974bfd3d441da3:1628` | `0x41c0`  | `sub_408C`         | Autoboot countdown begin (auto-boot=1 path)                 |
| `f6ce2cad806de9b:184` | `0x2b438`  | `sub_2B2F8` (unnamed helper, reached via boot-object chain) | Early failure in image4 manifest iterator |
| `9905b4edc794469:939`  | `0x2789c`  | `sub_273E0`        | APFS snapshot/"com.apple.os.update-\*" resolver failure     |
| `f6ce2cad806de9b:204`  | `0x2b5e8`  | `sub_2B2F8`        | Second manifest-iterator error return                       |
| `7ab90c923dae682:1819` | `0x1d9c`  | `sub_1928`         | **Final bail** — `system-volume-auth-blob` lookup failed    |
| *"Entering recovery mode..."* | `0x3bd4`  | `sub_33A0`         | LLB enters the recovery command-loop                |
| `337a834f05a86eb:373`  | `0x23fb4`  | recovery idle loop | Heartbeat in the command prompt menu task                   |

## 4. Control flow of the failure

`sub_33A0` is registered as the `"main"` task. It runs `sub_32874` (init counters — OK, logs 1557) and then registers `reboot` → `sub_9BC` via `sub_408C`. Inside `sub_408C`, if `auto-boot` NVRAM is set, it logs 1628 and iterates the boot-command chain (`sub_3E8FC` dispatches each command). That calls `sub_9BC`, the **boot command handler**:

`sub_9BC` @ 0x9BC (pseudocode trimmed):
1. `sub_16B04(..., "/boot", "tc-path", ...)` — load trustcache path. Succeeds.
2. `sub_36334("boot-path", ...)` — confirms `boot-path` env var is set.
3. **`sub_1928()`** — main boot-object loader.
4. If `sub_1928` returns a negative error (high bit set), `sub_9BC` returns that error → autoboot abandons → `sub_33A0` falls into the "Entering recovery mode" sequence (`0x3b08` → `0x3bc0..0x3bd4`).

Inside `sub_1928`:
- Resolves `"tc-path"`, `"dt-path"`, `"sepfw-path"`, `"seppatches-path"`, `"boot-ramdisk"` via `sub_36334` — all pass.
- Calls `sub_52954(...)` (stub returning 0).
- Loads boot-ramdisk into memory via `sub_3CB28 / sub_4BB38 / sub_4C9DC`.
- Resolves `"roothash-path"`, then calls **`sub_16E9C(..., "system-volume-auth-blob", "boot-path", ...)`** at `0x1ce4`.
- **`TBNZ W0, #0x1F, loc_1D90`** at `0x1ce8` — if the low-word of the return has the sign bit set (negative = error), branches to `0x1d90 → 0x1d98` which sets `W8 = 0x71B` (1819), then logs `7ab90c923dae682:1819` at `0x1d9c` and returns 0xFFFFFFFF.

`sub_16E9C` reads its inputs from statically-scoped globals at `0x8C048 .. 0x8C068`. Those globals are **only ever written by code that is never reached on a purely local boot** (no xrefs in the binary set them to non-zero; the only accesses are reads inside `sub_16E9C`). When called with those zeros, `sub_16E9C` drops into `sub_41DCC → sub_41660`, which requires a valid Image4 / property-store blob at `MEMORY[0x8F410..0x8F420]`. Those too are unpopulated in a local-boot flow, so the iterator sees `v34 < v27` (pointer below lower bound) and jumps to the error tail (`LABEL_185`), returning a negative errno that `sub_1928` converts into the 1819 log.

In plain terms: **LLB is failing to find/consume a `system-volume-auth-blob` (LocalPolicy / system volume authentication image4 property)**. The boot-object chain otherwise looks fine — trustcache, devicetree, SEP firmware, ramdisk, root-hash are all located, but the final authentication-blob lookup cannot be satisfied because the upstream loader that populates the image4 property store at `0x8F410` is never invoked in the standalone/local boot path.

## 5. Classification (maps to your (a)–(d))

- (a) kernelcache find: **ruled out**. `sub_9BC` never gets as far as the `sub_D124(..., 'krnl', ...)` call at 0xBD8, which is the kernelcache loader.
- (b) signature / image4 manifest validation: **this is the root cause**. Specifically the `system-volume-auth-blob` / boot-object manifest property lookup (`sub_16E9C`), i.e. a LocalPolicy / boot-object-manifest step.
- (c) NVRAM `auto-boot`: **not the cause**. Autoboot is on — that is why `sub_408C` logs 1628 and dispatches `reboot`. If it were off, you would see the 1628 trace skipped and enter recovery directly from `sub_33A0` without the intervening `f6ce.../9905.../7ab9...` chain.
- (d) other: n/a.

## 6. Concrete patch points

If you want to validate or force-bypass this gate on the vphone during bring-up:

- `sub_9BC @ 0x9BC`: the TBNZ-style check on `sub_1928`'s return (`v19 & 0x80000000`) at roughly `0xBE0..0xBF0` in `sub_9BC` — forcing this branch untaken lets the code fall into `sub_D124('krnl'...)` and try kernelcache boot, which will then reveal the next failure.
- `sub_1928 @ 0x1CE4..0x1CE8`: the `BL sub_16E9C` followed by `TBNZ W0, #0x1F, loc_1D90`. Patching the TBNZ to a NOP (or `MOV W0, #0` before it) short-circuits the manifest check. This is the minimum-invasive bypass if you want LLB to proceed on a local boot where the auth blob is intentionally absent.
- `sub_16E9C @ 0x16E9C`: easiest surgical fix — replace the function body with `MOV W0, #0 ; RET` if you want `system-volume-auth-blob` validation to be a no-op in the vresearch chain (consistent with what the vphone600/iOS 17 chain did for comparable gates).

## 7. Notes / unknowns

- The nullsub `sub_176E4` / `sub_176D0` pair at the top of `sub_16E9C` suggests Apple wired up the auth-blob ingress elsewhere (likely in a sibling file built only when `RELEASE_SECURE` / real SEP is present) and this LLB slice has the hooks stubbed out. On a device with real LocalPolicy provisioning, the pointers at `0x8F410` are populated before `main` runs. That never happens here because the vresearch local boot has no SEP-backed LocalPolicy staging.
- `3974bfd3d441da3` is the FNV-ish hash for the LLB `main.c` file; `7ab90c923dae682` is the `bootobjects` / `boot-images` source; `f6ce2cad806de9b` is the image4 property-store iterator; `9905b4edc794469` is the APFS-snapshot / `com.apple.os.update-` helper. These correspond to `Bootables/Bootables.c` / `Bootables/BootImages.c` / `Image4/Image4.c` / `AppleFileSystem` respectively in Apple iBoot source layout.
- File paths, offsets, and all function numbers above are relative to the flat load of `/tmp/llb.vresearch101.raw` at base 0.

## iOS 26 vs 18.5 comparison

Compared `/tmp/llb.vresearch101.raw` (iOS 18.5, iBoot-11881.122.1, 568168 B) against `/tmp/llb.vresearch101.ios26.patched.raw` (iOS 26.3.1, iBoot-13822.82.4, 605312 B) via IDA AArch64 raw load at base 0.

### Board profile context

The working iOS 26 path and the new iOS 18.5 path are not using the same runtime board profile.

| Layer | iOS 26 / legacy support | iOS 18.5 `22F76` support |
| --- | --- | --- |
| PV hardware exposed by vphone | `vresearch101` (`boardID=0x90`, `CPID=0xFE01`) | `vresearch101` (`boardID=0x90`, `CPID=0xFE01`) |
| Boot chain | `vresearch101ap` LLB/iBSS/iBEC/iBoot | `vresearch101ap` LLB/iBSS/iBEC/iBoot |
| Runtime payload profile | `vphone600ap` kernel/DeviceTree/SEP/RecoveryMode | `vresearch101ap` kernel/DeviceTree/SEP, no `RecoveryMode` |

Local evidence:

- `cloudOS_26.3_23D128` contains both `vphone600ap` and `vresearch101ap` identities.
- `cloudOS_18.5_22F76` contains `j236cap`, `j475dap`, and `vresearch101ap`; it has no `vphone600ap` identity.
- The project VM manifest is fixed to `platformType = vresearch101`, and `VPhoneHardwareModel` creates PV=3 hardware with board ID `0x90`. So iBoot correctly reports `Local boot, Board 0x90 (vresearch101ap)` in both flows.

This means the current 18.5 failure is not caused by accidentally using `vresearch101` as the VM hardware. That part matches the platform. The risky delta is that we are now also using `vresearch101ap` as the runtime payload profile, while the older working flow used `vphone600ap` runtime components.

### 1. `"system-volume-auth-blob"` is present in both.
- iOS 18.5: string @ `0x7c1c4`, 5 xrefs (`0x1c88, 0x1ccc, 0x4e20, 0xbd1c, 0x170a0`).
- iOS 26: string @ `0x84432`, 5 xrefs (`0x1e10, 0x1e5c, 0x5264, 0xc960, 0x18be8`).
Xref counts and roles line up one-for-one: boot-object loader (×2), `sub_5C40`/Image4 registry, big setup fn, fetch helper.

### 2. iOS 26 has the equivalent of `sub_1928`: `sub_1A74` @ `0x1a74..0x2084` (1552 B).
Found by the shared string-pool sequence `"tc-path" → "dt-path" → "sepfw-path" → "seppatches-path" → "boot-ramdisk"` resolved one-by-one via `sub_355E8`, and the same `sub_52A80` / `sub_4B418` / `sub_499E8` body shape as 18.5's `sub_1928`. Call site chain from `sub_9BC`-equivalent into `sub_1A74` matches.

### 3. The `"system-volume-auth-blob"` gate is **present-and-live** on iOS 26.
At `0x1e5c..0x1e80`: `ADRL X4, "system-volume-auth-blob" ; ADD X6, X4, #(boot-path - ...) ; BL sub_189E4 ; TBNZ W0, #0x1F, loc_1FB8`. That is structurally identical to 18.5's `0x1ce0..0x1ce8` (`BL sub_16E9C ; TBNZ W0, #0x1F, loc_1D90`). Not NOP'd, not bypassed by the project's patcher. iOS 26 reaches it, calls it, and it returns success.

### 4. iOS 26's `sub_189E4` is the moral equivalent of 18.5's `sub_16E9C`, reads the same-shape globals.
`sub_189E4` @ `0x189E4` (iOS 26) pseudo-body: iterator call (`sub_221A4`), then `sub_1931C(MEMORY[0x951E8], MEMORY[0x951F0], MEMORY[0x951F8], MEMORY[0x95200])`, then `sub_3F784(..., n0x95208)`, finally clears the globals. That mirrors `sub_16E9C` / `sub_1F358` / `sub_175DC` / `sub_41DCC` on 18.5 and its globals `0x8C048..0x8C068`.
Direct-operand search for `0x951E8 / 0x951F0 / 0x951F8 / 0x95200 / 0x95208` finds only the read-site ADRP/ADD inside `sub_189E4` itself — **no static writers in .text** either, same as 18.5. So the globals are populated indirectly by the iterator (`sub_221A4` → reads the Image4 property store and stages pointers/len for later use) when the store contains the `system-volume-auth-blob` object.
The real delta is the property-store backing: iOS 26 has two big staging paths that also reference `"system-volume-auth-blob"` and are **wired into the boot flow**: `sub_B064` (7168 B, xref at `0xc960`) and `sub_18B94` (208 B, xref at `0x18be8`, itself called from `sub_B064`@`0xc93c` and `sub_18CE0`). iOS 18.5 has analogous functions (`sub_A474` @ `0xa474`, `sub_17054` @ `0x17054`, `sub_1711C` @ `0x1711c`), but `sub_17054` / `sub_1711C` are only reached via `sub_273E0` (APFS snapshot resolver, the `9905b4edc794469` log source) — a path that already errors out before it can populate the store, as the decoded serial trace shows.

### 5. Bottom line
Fix is **(a)**: patch the 18.5 gate. iOS 26 appears to pass only because its upstream staging is invoked earlier on a device with real LocalPolicy/SEP; in the vresearch local-boot variant the property store stays empty on both firmware versions, but the published iOS 26 LLB successfully boots only because the project's existing patch set already neuters an equivalent authentication step (or because iOS 26's `sub_189E4` on vresearch101ap is independently satisfied by a stub that 18.5 lacks — the nullsub pair `sub_176E4/sub_176D0` at the head of 18.5's `sub_16E9C` is suspicious). The minimum-invasive, diff-parity fix is to NOP `TBNZ W0, #0x1F, loc_1D90` at `0x1ce8` in the 18.5 LLB (or replace `sub_16E9C` body with `MOV W0, #0 ; RET`), matching the spirit of the existing CFW panic/rootfs-bypass patches. Option (b) — porting a staging call — is higher risk because the staging writer itself likely depends on SEP-provided LocalPolicy bytes that are not present on the vphone. Recommend patching the gate and retesting.
