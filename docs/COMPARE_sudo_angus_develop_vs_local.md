# sudo-angus/vphone-cli `develop` — features not in this checkout

This note compares **your current tree** to **`https://github.com/sudo-angus/vphone-cli` branch `develop`**, and lists **capabilities or workflows that exist on `develop` but are absent from your HEAD**. It does **not** catalogue everything you have locally that `develop` lacks.

## Baseline

| Side | Ref |
|------|-----|
| **Local (this repo)** | Branch `personal`, commit `9ad605e` (`added serial log handler`), remote `origin` → `https://github.com/Xplo8E/vphone-cli` |
| **Remote compared** | `sudo-angus/vphone-cli` **`develop`** at `444c234` (`Drop trailing commas in argument lists for Swift 6.0 compat`), fetched as `git fetch https://github.com/sudo-angus/vphone-cli.git develop:refs/remotes/sudo-angus/develop` |

**Method:** `git log --reverse HEAD..sudo-angus/develop` (18 commits), plus targeted `git diff` / file reads on Swift, Makefile, `scripts/`, guest `vphoned`, and research notes. Merge-only commits on `develop` that only absorb upstream are not treated as separate “features.”

### Kernel / firmware Swift parity

`git diff HEAD..sudo-angus/develop -- sources/FirmwarePatcher/Kernel` is **empty**: your `HEAD` and their `develop` match on the **Swift kernel patch pipeline** (including `KernelPatchExcGuard` / dev-only EXC_GUARD scheduling). The early commits on their branch (`1080e34`, `d7ad78b`, `a3c9af6`) are part of *their* history but do **not** represent extra kernel logic you are missing in Swift today.

What you *do* still lack vs `develop` is mainly **host networking**, **CLI/boot wiring**, **host-control guest forwarding**, **Keys menu clipboard UX**, **`setup_machine` phase split**, **Makefile `EXTRA_ARGS`**, **`boot.sh`**, **guest SOCKS5**, **vphoned install hardening**, **amfidont module launch**, **SIGPIPE** on host, **Swift 6 trailing-comma** touch-ups in a few patcher literals, and their **extra research/README prose** for the TCP workaround.

---

## 1. Boot-time CLI flags (`VPhoneBootCLI`)

On `develop`, `vphone-cli boot` accepts options your `resolveOptions()` / `VPhoneVirtualMachine.Options` path does not wire through:

| Flag | Role |
|------|------|
| `--tcp-workaround` | Opt-in host-side transparent TCP proxy for broken guest TCP under NAT when VPN / traffic agents interfere. Mutually exclusive with `--dfu` (validated in CLI). |
| `--socks5-port <0\|1…65535>` | When non-zero, after the vsock device exists the host starts a **SOCKS5-shaped** TCP listener on `127.0.0.1:<port>` that byte-pumps into the guest; SOCKS5 and DNS run **inside** iOS so the guest routing table (including VPN) applies. Disabled with `--dfu` or invalid range. |
| `--software-keyboard` | Omits the USB keyboard device so iOS uses the **software keyboard**; pairs with menu logic that disables “Type ASCII from Clipboard” when no hardware keyboard exists. |

`develop` passes `softwareKeyboard` into `VPhoneVirtualMachine.Options`; your VM always attaches `VZUSBKeyboardConfiguration()` and has no `softwareKeyboard` field on `Options`.

---

## 2. Integrated host TCP transparent proxy (`--tcp-workaround`)

**Goal:** Same behavior as manually running `scripts/vm_tproxy_start.sh`, but started from the app lifecycle so operators do not need a second terminal.

**Components (on `develop` only):**

- `sources/vphone-cli/VPhoneTransparentProxy.swift` — locates `scripts/vm_tproxy_start.sh` (or `VPHONE_TPROXY_SCRIPT`), runs the privileged helper via **`sudo`**, passes **`WATCH_PID`** so the helper tears down `pf` / relay if `vphone-cli` exits without a clean signal path.
- `scripts/vm_tproxy_start.sh` — shell wrapper: bridge discovery / retries, `REPLACE_EXISTING`, `pfctl` anchor, coordination with `vm_tproxy.py`.
- `scripts/vm_tproxy.py` — userspace TCP relay + `DIOCNATLOOK` / `pf` integration (IPv4 TCP scope).

**Lifecycle (on `develop`):** `VPhoneAppDelegate` starts the proxy **after** `vm.start(...)` returns (ordering fix vs early helper start). `applicationWillTerminate` calls `transparentProxy?.stop()` for cleanup.

**Docs:** `develop` adds long **Host Network Workaround** sections to `research/0_binary_patch_comparison.md` (idle-timeout removal, keepalive / blocking relay, bridge auto-detect, `WATCH_PID` watchdog, integrated vs manual parity).

---

## 3. Host SOCKS5 bridge + guest SOCKS5 daemon (`--socks5-port`)

**Host:** `sources/vphone-cli/VPhoneSocks5Bridge.swift` — listens on a local TCP port, accepts connections, opens a **vsock** session to a fixed guest port and bridges bytes (host does not implement SOCKS5; it is a pump).

**Guest:** `scripts/vphoned/vphoned_socks5.{h,m}` — SOCKS5 server on the guest side; `vphoned.m` imports it, calls `vp_socks5_start()` after feature modules load, and sets **`signal(SIGPIPE, SIG_IGN)`** in `main` so closed peers do not kill the daemon.

**Boot wiring:** `VPhoneAppDelegate` starts the bridge when `cli.socks5Port > 0` and a `VZVirtioSocketDevice` is available; stops it on terminate.

---

## 4. Team boot wrapper `boot.sh`

Repo-root **`boot.sh`** (zsh): documents that **`make amfidont_allow_vphone`** should run first, runs it, runs **`sudo -v`** to warm sudo for the TCP workaround, then **`exec make boot EXTRA_ARGS="..."`** with **default** `--tcp-workaround --software-keyboard` plus any extra user args. This is an operational convenience layer you do not have in-tree.

---

## 5. `Makefile`: forwarding extra boot args + split `setup_machine`

- **`make boot`**: `develop` appends **`$(EXTRA_ARGS)`** to the bundled `vphone-cli` invocation so flags like `--tcp-workaround` flow without editing the Makefile.
- **`make setup_machine_prep` / `make setup_machine_install`**: thin wrappers that call `scripts/setup_machine.sh` with **`--phase=prep`**, **`--phase=install`**, or **`--phase=all`**, documented in `help` output.
- **`make clean`**: `develop` replaces your interactive, tiered clean (`CLEAN_VM` / `CLEAN_IPSW` confirmations) with a **single non-interactive** clean that removes build artifacts while keeping IPSWs (behavior change aimed at simplicity).

---

## 6. `setup_machine.sh`: `--phase=all|prep|install`

**Prep (`--phase=prep`):** runs through project setup, firmware prep/patch, and **DFU restore**, then **stops** before ramdisk / CFW / first-boot heavy steps — intended so you can **reboot the host** to clear `mds` / `syspolicyd` / `amfid` wedges without redoing large downloads.

**Install (`--phase=install`):** **Preflight** checks `vm/` for `iPhone*_Restore/BuildManifest.plist`, signed `.build/release/vphone-cli`, then continues from ramdisk build through CFW install and first boot / analysis.

**Constraints:** `--less` is incompatible with the split phases (script / Makefile messaging); full `make setup_machine` remains one-shot `--phase=all`.

---

## 7. Host control Unix socket: guest-agent command forwarding

Your `VPhoneHostControl` documents tap/swipe/key/screenshot/`type` (clipboard). On `develop`, the same server adds **`ResponseBox`** and many **`case "..."`** handlers that **forward** to `VPhoneControl` / async guest RPCs, returning JSON (not always the screenshot+image pipeline).

**Documented command families on `develop` include (names as in code comments):**  
`app_list`, `app_launch`, `app_terminate`, `open_url`, `clipboard_set`, `clipboard_get`, `file_list`, `file_push`, `file_pull`, `file_mkdir`, `file_delete`, `ipa_install` — each wired with parameter validation and semaphore-synchronized `@MainActor` calls into the existing control client.

Your tree has the underlying `VPhoneControl` APIs for several of these (e.g. clipboard / app list) but **does not** expose them through the host control socket command surface.

---

## 8. Keys menu: host ↔ guest clipboard actions + hardware-keyboard gate

On `develop`, `VPhoneMenuKeys` adds:

- **“Send Host Clipboard to Guest”** — reads `NSPasteboard`, calls `control.clipboardSet`, user-facing success/warn alerts.
- **“Receive Guest Clipboard to Host”** — `control.clipboardGet`, writes text and/or PNG image data back to the host pasteboard, with summaries in alerts.
- **“Type ASCII from Clipboard”** remains but is **disabled** when `!keyHelper.hasHardwareKeyboard`, with a tooltip explaining **`--software-keyboard`** mode.

Supporting API: `VPhoneKeyHelper.hasHardwareKeyboard` (true when a `_VZKeyboard` / first keyboard exists).

---

## 9. Process hardening: ignore `SIGPIPE` in the host binary

`develop`’s `main.swift` installs **`signal(SIGPIPE, SIG_IGN)`** before parsing CLI, with a comment that vsock / pipe / subprocess peers can disappear and default `SIGPIPE` would exit **141**. Your `main.swift` does not set this.

---

## 10. Guest `vphoned`: IPA reinstall safety + SOCKS5 sidecar

**Terminate-before-reinstall (`develop`):** `vphoned_install.m` path gains logic (per commit message) to **terminate the running app and unregister** before reinstall. `vphoned_apps.m` factors **`vp_terminate_app`** (FBS `terminateApplication:…` when available, `SIGTERM` fallback, PID re-check) used from the apps command handler and install flow.

**SOCKS5 + handshake:** as in §3 — `vp_socks5_start()`, `SIGPIPE` ignore, **`vphoned_socks5`** module.

**Removed from guest hello on `develop`:** the **`ip`** field derived from `getifaddrs` / primary IPv4 is no longer attached to the JSON hello (and matching `guestIP` plumbing is removed from host `VPhoneControl` / window subtitle on `develop`). That is a **behavior change** on their side rather than an additive feature here; listed only because it ships in the same guest binary as SOCKS5.

---

## 11. `start_amfidont_for_vphone.sh`: resilient `amfidont` launch

`develop` probes **`python3`** candidates (`xcrun -f python3`, then `command -v python3`) for **`import amfidont`**, then runs:

`sudo "$PYTHON_BIN" -m amfidont daemon …`

instead of requiring a **`amfidont`** shim on `PATH`. This matches the common `python3 -m pip install amfidont` install layout.

---

## 12. Swift 6 compatibility sweep

Commit **`444c234`** on `develop` removes **trailing commas** in multi-line argument lists (e.g. `CryptexFilesystemPatcher`, `ManifestHashPatcher` placeholder `PatchRecord` literals) for **Swift 6** parsing. Your tree still uses the trailing-comma form in those spots.

---

## 13. README additions on `develop` (user-facing documentation only)

`develop`’s `README.md` adds narrative for:

- **Split `setup_machine`** (`make setup_machine_prep` / `make setup_machine_install`) and why (host daemon wedging, DFU boundary).
- **Optional host TCP workaround** (`make boot EXTRA_ARGS=--tcp-workaround`), privilege split, and pointer to the scripts.

(Your README still points at guest/host ops docs paths that `develop` does not carry the same way; this bullet is only “extra README material on their branch,” not a runtime feature.)

---

## 14. Default IPSW URLs in `scripts/fw_prepare.sh`

`develop` points **`DEFAULT_IPHONE_SOURCE`** / **`DEFAULT_CLOUDOS_SOURCE`** at different Apple CDN URLs (e.g. **26.1 / 23B85** style paths in the diff vs your **26.3.1 / 23D8133** defaults). That is **environment / baseline image selection**, not a new subsystem; worth knowing if you cherry-pick: you may want to keep **your** URLs.

---

## Commit chain (unique to `develop` vs your HEAD)

Oldest → newest (from `git log --reverse HEAD..sudo-angus/develop`). Items **1–3** are already reflected in your Swift tree (see “Kernel / firmware Swift parity” above); they remain listed for **provenance** when reading their branch history.

1. `1080e34` — kernel: add patch #26 — disable `thread_guard_violation` (EXC_GUARD)  
2. `d7ad78b` — review: remove SDK mentions, add patch #27 to patch comparison table  
3. `a3c9af6` — kernel: scope `thread_guard_violation` patch to **dev** variant only  
4. `74366cf` — feat: guest agent command forwarding via `VPhoneControl`  
5. `c5aac8f` — menu/keys: hardware typing → vsock clipboard push  
6. `8393e06` — menu/keys: restore “Type ASCII…” alongside clipboard push  
7. `c278ce4` — amfidont: `python3 -m` invocation  
8. `ddb5029` — vphoned/install: terminate + unregister before reinstall  
9. `d2fd7ed` / `995f41f` — merge `main` into `develop`  
10. `f6d53fc` — Harden host TCP proxy workaround for vphone  
11. `0d309d3` — Integrate host TCP proxy workaround into vphone-cli boot  
12. `cbf57f6` — Simple boot (supporting simplification in the series)  
13. `6540031` — vphone clipboard → host (clipboard pipeline work)  
14. `8f1c1be` — Start TCP workaround **after** VM boot  
15. `4f818d3` — Stabilize TCP workaround lifecycle  
16. `c3b931d` — add SOCKS5 port  
17. `444c234` — Swift 6.0 trailing-comma compat  

---

## Regenerating this comparison

```bash
cd /path/to/vphone-cli
git fetch https://github.com/sudo-angus/vphone-cli.git develop:refs/remotes/sudo-angus/develop
git log --oneline HEAD..sudo-angus/develop
git diff --stat HEAD..sudo-angus/develop
```

Update this doc if you move `HEAD` to another branch or if `sudo-angus/develop` advances.
