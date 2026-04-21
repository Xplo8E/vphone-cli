# Makefile targets - technical guide

Living document for the setup/boot pipeline. The point is not to copy the `Makefile` into prose. The point is to explain the state transition behind each target so iOS 18 retargeting does not turn into blind command cargo culting.

This repo is building a virtual research iPhone bundle. Most targets move the VM through one of these states:

1. Host is prepared: tools, Python venv, Swift binary, signing state.
2. VM bundle exists: disk, SEP storage, framework ROMs, `config.plist`.
3. Hybrid restore tree exists: retail iPhone OS files plus cloudOS/PCC research hardware files.
4. Firmware is patched in-place for the chosen variant.
5. DFU restore installs that tree onto the virtual disk.
6. Ramdisk boots over DFU so the installed filesystem can be modified.
7. CFW phases lay down guest-side tools, daemons, Cryptex content, and variant-specific changes.
8. Normal boot starts the GUI/control plane and persists VM identity.

If a command fails, debug the state transition. Do not just rerun random later commands. Example: `restore` cannot work until `boot_dfu` is running and `fw_prepare` produced exactly one `iPhone*_Restore` tree. `cfw_install` cannot work until `ramdisk_send` booted SSH ramdisk and usbmux forwarding exposes port 22 as the expected local port.

---

## Common variables

The Makefile is intentionally variable-driven. These are the knobs that change behavior without editing scripts:

| Variable | Used by | Meaning |
| --- | --- | --- |
| `VM_DIR` | almost everything | Active VM bundle directory. Default: `vm`. |
| `CPU` | `vm_new` | CPU count written into `config.plist`. Only applied when generating the VM manifest. |
| `MEMORY` | `vm_new` | Memory in MB written into `config.plist`. Only applied when generating the VM manifest. |
| `DISK_SIZE` | `vm_new` | Sparse `Disk.img` logical size in GB. Existing disk is not resized. |
| `BACKUPS_DIR` | `vm_backup`, `vm_restore`, `vm_switch`, `vm_list` | Backup root. Default: `vm.backups`. |
| `NAME` | backup/switch targets | Backup name. Must be a simple identifier, no slashes or leading dots. |
| `BACKUP_INCLUDE_IPSW` | `vm_backup`, `vm_switch` | Include active `*_Restore*` directories in backups when set to `1`. Default excludes them. |
| `FORCE` | `vm_restore` | Skip overwrite prompt when set to `1`. |
| `RESTORE_UDID` | `restore_get_shsh`, `restore`, ramdisk automation | Select the target USB/usbmux device by UDID. |
| `RESTORE_ECID` | `restore_get_shsh`, `restore` | Select DFU/recovery target by ECID. Accepts `0x...` or hex. |
| `IRECOVERY_ECID` | `ramdisk_send` | Select DFU/recovery endpoint for irecv ramdisk send. |
| `RAMDISK_UDID` | `ramdisk_build`, `ramdisk_send`, automation | Identity context for ramdisk stage. |
| `SSH_PORT` | `cfw_install*` | Local SSH port that forwards to guest ramdisk port 22. Default: `2222`. |
| `JB`, `DEV`, `LESS` | `setup_machine` | Full setup variant selector. Mutually exclusive. |
| `SKIP_PROJECT_SETUP` | `setup_machine` | Skip `setup_tools` + `build`. Useful when only rerunning device stages. |
| `NONE_INTERACTIVE` | `setup_machine` | Auto-continue prompts and run boot analysis without manual Enter presses. |
| `SUDO_PASSWORD` | `setup_machine` | Preload sudo credential for automated sudo operations. |
| `VARIANT` | `setup_tools` | When `VARIANT=less`, installs the extra APFS sealvolume helper needed by patchless flow. |

The Makefile also exports a project-local `PATH` first:

```make
.tools/bin:.venv/bin:.build/release:$PATH
```

That matters. Many scripts assume the repo-built `trustcache`, Python venv, and built `vphone-cli` are preferred over whatever the host already has.

---

## Pipeline story

### Host setup

`setup_tools` and `build` are not firmware steps. They prepare the host side: Homebrew tools, repo-built helper binaries, Python modules, Swift build artifacts, and code signing with private entitlements.

The main runtime binary must be signed. `swift build` by itself is not enough for normal boot because the private PV=3 Virtualization.framework path depends on entitlements and host policy. `make build` writes build info, builds release, and signs `.build/release/vphone-cli` with `sources/vphone.entitlements`.

### VM bundle creation

`vm_new` creates the empty machine bundle. It does not download firmware. It creates:

- sparse `Disk.img`
- `SEPStorage`
- `AVPBooter.vresearch1.bin`
- `AVPSEPBooter.vresearch1.bin`
- `config.plist`

The AVP ROMs come from `/System/Library/Frameworks/Virtualization.framework/.../Resources`, not from an IPSW. The `machineIdentifier` in `config.plist` starts empty; `vphone-cli` creates and saves it on first VM start. That first start also lets the code derive stable ECID/UDID prediction from the machine identifier.

### Firmware preparation

`fw_prepare` creates the hybrid restore tree under `VM_DIR`. It starts with the retail iPhone IPSW tree, overlays selected cloudOS/PCC files, preserves the original retail manifest as `iPhone-BuildManifest.plist`, then generates the hybrid `BuildManifest.plist` and `Restore.plist`.

This is the first major iOS-version retargeting boundary. For iOS 18 support, the interesting questions are not only "which IPSW URL?". The real questions are:

- Which retail identity supplies the OS/system images?
- Which cloudOS identities supply `vresearch101` and `vphone600` pieces?
- Did paths move between versions?
- Did restore manifest semantics change?
- Did trustcache/Cryptex/SSV expectations change?

### Firmware patching

`fw_patch*` mutates the prepared tree in place using the Swift `FirmwarePipeline`. All variants operate on the same tree layout, but choose different patcher factories.

Variant pairing is important:

| Variant | Patch target | Boot target | CFW target | Use case |
| --- | --- | --- | --- | --- |
| Patchless | `sudo make fw_patch_less` | `make boot_less` | no regular CFW phase in `setup_machine LESS=1` | Minimize IM4P patch surface; heavy filesystem/manifest work. |
| Regular | `make fw_patch` | `make boot` | `make cfw_install` | Default research VM path. |
| Development | `make fw_patch_dev` | `make boot` | `make cfw_install_dev` | Regular plus dev TXM behavior and dev guest overlay. |
| Jailbreak | `make fw_patch_jb` | `make boot` | `make cfw_install_jb` | Dev plus JB boot/kernel/runtime extensions. |

### Restore and ramdisk

`boot_dfu` starts the VM in DFU mode and must stay running while another terminal talks to it. `restore_get_shsh` fetches the TSS/SHSH record using the hybrid manifest. `restore` performs the erase restore through `pymobiledevice3`.

After restore, the VM disk has the firmware installed, but the guest filesystem still needs post-restore modifications for regular/dev/jb. That is why the flow boots DFU again, builds a signed SSH ramdisk, sends it over irecv, forwards SSH, and runs `cfw_install*`.

### Normal boot

`boot` launches the GUI app bundle, starts the VM from `config.plist`, opens the window, attaches serial, enables vsock, and connects to `vphoned` when the guest is ready. It is not just "start QEMU" style boot. The app configures a PV=3 Virtualization.framework machine with private APIs: touch, SEP coprocessor, synthetic battery, debug stub, PL011 serial, Virtio block/network/vsock, and the vphone hardware model.

---

## `help`

### Story

`make help` is the supported command index. It prints the workflow shape and the main options. Treat it as the quick map, not the source of truth.

### Facts

Runs only shell `echo` commands inside the Makefile. No filesystem state changes.

### Good use

Run it when target names drift. It is also useful for seeing which variant flags exist in the current branch (`JB`, `DEV`, `LESS`, etc.).

---

## `setup_machine`

### Story

This is the lazy full pipeline. It does the same work as the manual setup path, but it owns the orchestration: host setup, VM creation, firmware prep, firmware patching, DFU restore, optional ramdisk + CFW, first boot, and final boot analysis.

It is useful when you want a fresh machine from zero. It is less useful when you are debugging one broken stage, because it hides intermediate state inside automation. For iOS 18 retargeting, use manual commands when you need to inspect each boundary.

### Facts

Makefile target:

```make
SUDO_PASSWORD="$(SUDO_PASSWORD)" \
NONE_INTERACTIVE="$(NONE_INTERACTIVE)" \
zsh scripts/setup_machine.sh \
  $(if JB,--jb,) \
  $(if DEV,--dev,) \
  $(if LESS,--less,) \
  $(if SKIP_PROJECT_SETUP,--skip-project-setup,)
```

`scripts/setup_machine.sh` then does:

1. Validates platform and project setup unless `SKIP_PROJECT_SETUP=1`.
2. Runs `setup_tools` and `build`.
3. Prepends `.venv/bin` to `PATH`.
4. Runs `vm_new`.
5. Runs `fw_prepare`.
6. Runs the selected `fw_patch*` target. `LESS=1` uses sudo for `fw_patch_less`.
7. Starts `boot_dfu` in the background and logs to `.setup_machine_logs/boot_dfu.log`.
8. Loads predicted device identity and waits for DFU/recovery.
9. Runs `restore_get_shsh` and `restore` with explicit UDID/ECID.
10. Waits for post-restore reboot and stops DFU VM.
11. For non-less variants, starts DFU again, builds/sends ramdisk, starts iproxy, waits for SSH, runs selected `cfw_install*`, then stops DFU/iproxy.
12. For non-less variants, starts first normal boot and injects first-boot shell commands.
13. For JB, prints the first-boot JB finalization path.
14. Runs boot analysis, or `boot_less` for less mode.

### Variant behavior

| Selector | Firmware patch | CFW phase | Final boot |
| --- | --- | --- | --- |
| default | `fw_patch` | `cfw_install` | `boot` |
| `DEV=1` | `fw_patch_dev` | `cfw_install_dev` | `boot` |
| `JB=1` | `fw_patch_jb` | `cfw_install_jb` | `boot` plus first-boot JB LaunchDaemon |
| `LESS=1` | `fw_patch_less` via sudo | skipped | `boot_less` |

`JB`, `DEV`, and `LESS` are mutually exclusive. The Makefile checks this before calling the script, and the script checks again.

### Outputs

- `vm/` bundle and restore tree.
- `.setup_machine_logs/` runtime logs.
- SHSH blob in `vm/` named by ECID.
- `vm/Ramdisk/` for non-less variants.
- Guest filesystem modifications for regular/dev/jb.

### Gotchas

`setup_machine` starts long-running boot processes internally. If a stage fails, read the log it prints; rerunning from zero can hide the real failure.

For patchless, `setup_tools` is called with `VARIANT=less`, which downloads/signs `apfs_sealvolume` into `.tools/`. Regular setup skips that helper.

---

## `setup_tools`

### Story

This is the host tool bootstrap. It makes sure this repo has the exact helper binaries and Python environment the firmware/CFW scripts expect.

Do not confuse this with `build`. `setup_tools` prepares external tools; `build` compiles the Swift app.

### Facts

Makefile target:

```make
VARIANT=$(VARIANT) zsh scripts/setup_tools.sh
```

`scripts/setup_tools.sh` has five phases:

1. Homebrew packages: `aria2`, `gnu-tar`, `openssl@3`, `ldid-procursus`, `sshpass`.
2. Build `trustcache` from `scripts/repos/trustcache` into `.tools/bin/trustcache`.
3. Build `insert_dylib` from `scripts/repos/insert_dylib` into `.tools/bin/insert_dylib`.
4. Run `scripts/setup_venv.sh` to create `.venv` and install `requirements.txt`.
5. If `VARIANT=less`, fetch `apfs_sealvolume` from a macOS ramdisk using `ipsw`, extract it, place it at `.tools/apfs_sealvolume`, and ad-hoc sign it.

### Outputs

- `.tools/bin/trustcache`
- `.tools/bin/insert_dylib`
- `.venv/`
- `.tools/apfs_sealvolume` for patchless only

### Gotchas

`setup_tools` mutates host-local repo state but not the VM. You can rerun it safely. It will skip helpers that already exist.

`setup_venv.sh` builds a `libkeystone.dylib` inside the venv because `keystone-engine` Python bindings need a dynamic library at runtime. If capstone/keystone imports fail later, this phase is the one to inspect.

There is no explicit `setup_venv` Makefile target in the current `Makefile`; `setup_tools` calls `scripts/setup_venv.sh` directly.

---

## `build`

### Story

This builds the signed release runtime. Use this for anything that launches the VM.

The private Virtualization.framework path is entitlement-sensitive. A raw unsigned SwiftPM binary is the wrong artifact for normal boot. The Makefile writes the current git hash into `VPhoneBuildInfo.swift`, builds release, then signs with `sources/vphone.entitlements`.

### Facts

Target dependency:

```make
build: .build/release/vphone-cli
```

The release rule does:

1. Generate `sources/vphone-cli/VPhoneBuildInfo.swift`.
2. Run `swift build -c release`.
3. Run `codesign --force --sign - --entitlements sources/vphone.entitlements .build/release/vphone-cli`.

### Outputs

- `.build/release/vphone-cli`
- updated generated `sources/vphone-cli/VPhoneBuildInfo.swift`

### Gotchas

`build` does not create the `.app` wrapper. `boot` depends on `bundle`, and `bundle` depends on `build`.

---

## `patcher_build`

### Story

This builds the debug Swift binary used as the firmware patcher CLI. Firmware patching does not need the GUI app bundle; it needs the `patch-firmware` and `patch-component` subcommands.

### Facts

Target dependency:

```make
patcher_build: .build/debug/vphone-cli
```

The debug rule:

1. Generates `VPhoneBuildInfo.swift`.
2. Runs `swift build`.

No signing step is done here.

### Used by

- `fw_patch`
- `fw_patch_less`
- `fw_patch_dev`
- `fw_patch_jb`
- `ramdisk_build`

### Gotchas

The ramdisk builder calls the Swift binary for component-level patching when deriving ramdisk-specific TXM/kernel artifacts. If `.build/debug/vphone-cli` is missing, `ramdisk_build` tells you to run `make patcher_build`.

---

## `bundle`

### Story

This packages the signed runtime into a macOS app bundle. Normal GUI boot uses this bundle instead of launching the raw release binary.

### Facts

`bundle` depends on `build` and `sources/Info.plist`, then creates:

- `.build/vphone-cli.app/Contents/MacOS/vphone-cli`
- `.build/vphone-cli.app/Contents/Info.plist`
- `.build/vphone-cli.app/Contents/Resources/AppIcon.icns`
- `.build/vphone-cli.app/Contents/Resources/signcert.p12`
- `.build/vphone-cli.app/Contents/MacOS/ldid`

It signs bundled `ldid`, then signs the bundled `vphone-cli` with project entitlements.

### Used by

- `boot`
- `boot_less`
- `amfidont_allow_vphone`

### Gotchas

The bundle copies `signcert.p12` into resources because the app-side IPA installer/signing workflows need it available at runtime.

---

## `vphoned`

### Story

`vphoned` is the guest daemon. It runs inside iOS and exposes the host control plane over vsock: file browser, IPA install, keyboard/touch helpers, devmode, app listing, keychain features, etc.

This target builds and signs the daemon for iOS, then drops a signed copy into the active VM directory. Normal `boot` depends on it so the host can auto-update the guest daemon when the vsock handshake says the guest copy is stale.

### Facts

Target does:

```make
make -C scripts/vphoned GIT_HASH=$(GIT_HASH)
cp scripts/vphoned/vphoned $(VM_DIR)/.vphoned.signed
ldid -S scripts/vphoned/entitlements.plist -M -K scripts/vphoned/signcert.p12 $(VM_DIR)/.vphoned.signed
```

### Outputs

- `scripts/vphoned/vphoned`
- `$(VM_DIR)/.vphoned.signed`

### Gotchas

Requires `ldid`. If missing, the target tells you to install `ldid-procursus`.

`VPhoneControl` skips daemon binary auto-update for the `less` variant. That is intentional: patchless mode has different runtime assumptions.

---

## `clean`

### Story

This is a repo scrubber, not a normal build clean. Use carefully.

### Facts

Runs:

```make
git clean -fdx -e '*.ipsw' -e '*_Restore*'
```

That removes untracked and ignored files, while preserving IPSW zip files and restore directories matching `*_Restore*`.

### What it can remove

- `.build/`
- `.venv/`
- `.tools/`
- temporary VM side files if untracked and not excluded
- local logs
- any untracked docs/scripts you have not committed

### Gotchas

Do not run this casually in a dirty research workspace. It is destructive to untracked files by design.

---

## `vm_new`

### Story

This step mirrors `vrevm`-style VM creation. You are not downloading firmware; you are creating the on-disk shape Virtualization.framework expects next to `config.plist`.

The AVPBooter / AVPSEPBooter binaries are not from an IPSW. They come from Apple's framework on the host and target the `vresearch1` research chip. `Disk.img` is the guest block device. `SEPStorage` is fixed-size backing storage for the emulated SEP coprocessor.

`config.plist` is written with an empty `machineIdentifier`. On first VM start, `vphone-cli` creates a `VZMacMachineIdentifier`, saves it back into `config.plist`, and derives stable ECID / predicted UDID behavior from it.

### Facts

Makefile target:

```make
CPU="$(CPU)" MEMORY="$(MEMORY)" \
zsh scripts/vm_create.sh --dir $(VM_DIR) --disk-size $(DISK_SIZE)
```

Creates under `VM_DIR`:

- sparse `Disk.img` using `dd ... seek=<DISK_SIZE bytes>`
- `SEPStorage` sized to 512 KiB
- `AVPBooter.vresearch1.bin`
- `AVPSEPBooter.vresearch1.bin`
- `.gitkeep`
- `config.plist` generated by `scripts/vm_manifest.py`

The manifest includes:

- `platformType = vresearch101`
- empty `machineIdentifier`
- CPU/memory
- fixed screen config `1290x2796 @ 460 PPI`, scale `3.0`
- NAT network config
- disk/NVRAM/ROM/SEP storage paths

### Gotchas

Existing `Disk.img` is not overwritten. If you change `DISK_SIZE` and rerun `vm_new`, the old disk remains unless you delete it manually.

`nvram.bin` is not created by `vm_new`. It is created by `VZMacAuxiliaryStorage` when the VM is initialized.

---

## `vm_backup`

### Story

This snapshots the active VM bundle to a named directory. Use it before switching firmware versions or variants, especially while doing iOS 18 retargeting.

### Facts

Makefile target passes variables into `scripts/vm_backup.sh`:

```make
VM_DIR=$(VM_DIR) BACKUPS_DIR=$(BACKUPS_DIR) NAME=$(NAME) BACKUP_INCLUDE_IPSW=$(BACKUP_INCLUDE_IPSW) zsh scripts/vm_backup.sh
```

The script:

1. Requires `NAME`.
2. Rejects backup names with slashes or leading dots.
3. Validates `VM_DIR/config.plist` exists.
4. Warns if `vphone-cli` appears to be running against that VM.
5. Runs `rsync -aH --sparse --progress --delete` into `BACKUPS_DIR/NAME/`.
6. Excludes `*_Restore*/` unless `BACKUP_INCLUDE_IPSW=1`.
7. Writes `NAME` into `VM_DIR/.vm_name`.

### Outputs

- `vm.backups/<NAME>/`
- `vm/.vm_name`

### Gotchas

Default backups exclude restore trees because IPSW extracts are huge and reproducible. If you are preserving a fragile retargeting state, use `BACKUP_INCLUDE_IPSW=1`.

Do not snapshot a live VM unless you accept possible disk inconsistency.

---

## `vm_restore`

### Story

This replaces the active `VM_DIR` with a named backup. It is the inverse of `vm_backup`.

### Facts

The script:

1. Requires `NAME`.
2. Validates `BACKUPS_DIR/NAME/config.plist`.
3. Refuses to run if `vphone-cli` appears to be using `VM_DIR`.
4. Prompts before overwriting an existing VM unless `FORCE=1`.
5. `rsync`s backup contents into `VM_DIR` with `--delete`.
6. Writes `NAME` into `VM_DIR/.vm_name`.

### Gotchas

This is an overwrite operation. `FORCE=1` skips the prompt, not the destructive nature.

---

## `vm_switch`

### Story

This is backup-and-restore in one command. It saves the current active VM under its current name, then restores the requested backup.

This is the clean workflow when comparing, for example, `18.x-regular`, `18.x-dev`, and `26.x-known-good` without constantly rebuilding.

### Facts

The script:

1. Requires target `NAME`.
2. Validates the target backup.
3. Refuses to run if the VM is active.
4. Determines current VM name from `VM_DIR/.vm_name`; if absent, prompts for one.
5. Saves current VM into `BACKUPS_DIR/<current>/` with sparse rsync.
6. Excludes restore dirs unless `BACKUP_INCLUDE_IPSW=1`.
7. Restores target backup into `VM_DIR`.
8. Updates `VM_DIR/.vm_name`.

### Gotchas

If the current VM has no `.vm_name`, this target becomes interactive. Name VMs intentionally before relying on switch automation.

---

## `vm_list`

### Story

Quick backup inventory. It shows which saved VM is active.

### Facts

Pure Makefile shell loop over `BACKUPS_DIR/*/`. A directory is considered a backup if it contains `config.plist`.

For each backup it prints:

- backup name
- disk usage from `du -sh`
- `[active]` marker if the name matches `VM_DIR/.vm_name`

### Gotchas

This does not validate that the backup has a complete disk or restore tree. It only checks `config.plist`.

---

## `amfidont_allow_vphone`

### Story

This starts the `amfidont` daemon scoped to the current repo path so macOS will launch the signed private-entitlement binary. It is the repo-packaged version of the README host-policy workaround.

### Facts

Target depends on `bundle`, then runs:

```make
zsh scripts/start_amfidont_for_vphone.sh
```

The script runs:

```bash
sudo xcrun amfidont daemon --path "$PROJECT_ROOT" --spoof-apple
```

### Why it matters

PV=3 research virtualization needs private entitlements. If AMFI kills the signed binary with signal 9 / exit 137, the VM never gets to firmware. This helper targets host execution policy, not guest firmware.

`--spoof-apple` is especially relevant to patchless flows where signature expectations are tighter.

### Gotchas

Requires `amfidont` installed outside this repo. If missing, the script prints the install command.

---

## `boot_host_preflight`

### Story

This diagnoses whether the host can launch the signed PV=3 binary before you burn time debugging firmware.

It answers: is the host nested, is SIP/research guest mode configured, do the entitlements show up, does Gatekeeper/spctl allow execution, and does the signed release binary actually run `--help`?

### Facts

Target depends on `build`, then runs:

```make
zsh scripts/boot_host_preflight.sh
```

The script checks:

- `sw_vers`
- model name from `system_profiler`
- `kern.hv_vmm_present`
- `csrutil status`
- `csrutil allow-research-guests status`
- boot args from `sysctl` / `nvram`
- `spctl --status`
- entitlements on `.build/release/vphone-cli`
- policy assessment for release binary
- unsigned debug `--help` if built
- signed release `--help`
- ad-hoc signed debug control `--help` if debug binary exists

### Gotchas

The boot targets call a stricter internal form of this script through `boot_binary_check` / `boot_binary_check_less` with `--assert-bootable`. If you are on a nested Apple VM host, it fails before VM start.

---

## `boot_binary_check` / `boot_binary_check_less`

### Story

These are internal preflight gates used by boot targets. You normally do not run them directly.

### Facts

- `boot_binary_check` depends on the release binary and calls `boot_host_preflight.sh --assert-bootable`.
- `boot_binary_check_less` calls `boot_host_preflight.sh --assert-bootable --less`.
- Both then run the signed release binary with `--help` and fail early if launch is blocked.

### Gotchas

If `make boot` fails here, the guest never started. Debug host policy/signing first, not firmware.

---

## `boot`

### Story

This is normal GUI boot for regular/dev/jb variants. It launches the app bundle from inside `VM_DIR`, reads `config.plist`, starts the PV=3 VM, opens the UI, attaches the serial pipe, and connects the vsock control channel when the guest daemon is ready.

### Facts

Makefile dependencies:

```make
boot: bundle vphoned boot_binary_check
```

Command:

```make
cd $(VM_DIR) && "$(CURDIR)/$(BUNDLE_BIN)" --config ./config.plist
```

Runtime behavior from `VPhoneAppDelegate` / `VPhoneVirtualMachine`:

- load VM manifest
- create/load machine identifier
- write `udid-prediction.txt`
- create `VZMacPlatformConfiguration`
- create `VZMacAuxiliaryStorage` at `nvram.bin`
- set NVRAM boot args `serial=3 debug=0x104c04`
- configure ROM URL from manifest
- attach disk, NAT network, audio, display, keyboard, USB touch, vsock
- configure synthetic battery
- enable kernel GDB debug stub
- configure SEP coprocessor and SEP ROM
- validate and start the VM
- open the window/menu stack
- connect `VPhoneControl` to vsock port 1337
- optionally push updated `.vphoned.signed` into the guest after handshake

### Outputs/side effects

- creates or overwrites `nvram.bin`
- persists `machineIdentifier` to `config.plist` on first start
- writes `udid-prediction.txt`
- may update guest `vphoned` through vsock on non-less variants

### Gotchas

`boot` depends on `vphoned`, so it may rebuild/sign the daemon before launch.

If you patched with `fw_patch_less`, use `boot_less`. Variant mismatch is an easy way to chase fake bugs.

---

## `boot_less`

### Story

Patchless-compatible normal boot. Same VM runtime path as `boot`, but passes `--variant less` so host control logic knows the guest is in the less/patchless mode.

### Facts

Dependencies:

```make
boot_less: bundle vphoned boot_binary_check_less
```

Command:

```make
cd $(VM_DIR) && "$(CURDIR)/$(BUNDLE_BIN)" --config ./config.plist --variant less
```

### Gotchas

`VPhoneControl` does not auto-push daemon updates when `variant == .less`. That is deliberate.

---

## `boot_dfu`

### Story

This starts the VM into DFU mode and stays running so restore/ramdisk tooling can talk to the virtual device from another terminal.

This is not a firmware flashing command by itself. It is the host-side DFU endpoint provider.

### Facts

Dependencies:

```make
boot_dfu: build boot_binary_check
```

Command:

```make
cd $(VM_DIR) && "$(CURDIR)/$(BINARY)" --config ./config.plist --dfu
```

Runtime differences:

- no graphics (`NSApp` activation policy is prohibited)
- no vsock control channel setup
- no IPA install support
- `VZMacOSVirtualMachineStartOptions._setForceDFU(true)`

### Typical pairing

Terminal 1:

```bash
make boot_dfu
```

Terminal 2:

```bash
make restore_get_shsh
make restore
```

Then later, for ramdisk:

```bash
make boot_dfu
make ramdisk_build
make ramdisk_send
```

### Gotchas

Keep `boot_dfu` running. If it exits, the DFU/recovery endpoint disappears and `restore` / `ramdisk_send` will fail or hang waiting.

---

## `fw_prepare`

### Story

A retail iPhone IPSW is built for real phone hardware. The VM is not that hardware. It identifies as `vresearch101` for signing/restore while runtime wants `vphone600`-aligned pieces like device tree, SEP, and research kernel paths.

No single Apple IPSW ships "retail iPhone OS + PCC virtual research hardware" as one coherent restore product. `fw_prepare` creates that product locally.

It does two jobs:

1. Filesystem reality: clone/extract the retail iPhone restore tree and overlay selected cloudOS/PCC files into the paths the hybrid manifest will reference.
2. Plist reality: generate a coherent `BuildManifest.plist` / `Restore.plist` so restore tooling sees one erase identity instead of two incompatible products.

### Facts

Makefile target:

```make
cd $(VM_DIR) && bash "$(CURDIR)/scripts/fw_prepare.sh"
```

Important detail: the script runs from inside `VM_DIR`, so output restore directories land next to `Disk.img` and `config.plist`.

The script supports firmware lookup inputs through environment variables:

- `LIST_FIRMWARES=1`
- `IPHONE_DEVICE`
- `IPHONE_VERSION`
- `IPHONE_BUILD`
- `IPHONE_SOURCE`
- `CLOUDOS_SOURCE`

### Download/cache model

Under `ipsws/` there are two distinct things:

- `*.ipsw` zip files: downloaded or local source archives.
- extracted directories named after those IPSWs without `.ipsw`.

On rerun, populated extract directories let the script skip unzip and copy from the cached extract tree. The VM directory still gets a fresh working restore tree.

### Merge model

The mental model is layered overlay, not full replacement:

1. Start with retail iPhone restore tree.
2. Copy selected cloudOS files over root kernel and specific `Firmware/` paths.
3. Preserve existing retail `.dmg` and `Firmware/*.dmg.trustcache` when copy uses no-clobber behavior.
4. Preserve original retail manifest as `iPhone-BuildManifest.plist`.
5. Run `fw_manifest.py` to write hybrid plists.
6. Remove the temporary cloudOS clone inside `VM_DIR`.

### Outputs

- one active `iPhone*_Restore/` directory under `VM_DIR`
- `iPhone-BuildManifest.plist` inside that restore tree
- hybrid `BuildManifest.plist`
- hybrid `Restore.plist`

### Gotchas

If multiple `*Restore*` directories exist, later patch/restore stages can pick the wrong one. The prepare script removes stale restore directories for this reason.

For retargeting iOS 18, inspect both original and generated manifests. The failure mode is often not "download failed"; it is "hybrid identity points at a path/manifest member whose semantics changed".

Refs: `scripts/fw_prepare.sh`, `scripts/fw_manifest.py`, `research/firmware_manifest_and_origins.md`.

---

## `fw_patch` / `fw_patch_less` / `fw_patch_dev` / `fw_patch_jb`

### Story

After `fw_prepare`, the tree is hybrid but still mostly stock behavior. `fw_patch*` runs the Swift `FirmwarePipeline` and patches selected boot-chain components in place.

All variants use the same CLI shape:

```bash
.build/debug/vphone-cli patch-firmware --vm-directory <repo>/<VM_DIR> --variant <variant>
```

Variants differ by patcher factories, not by separate restore trees.

### Pipeline order

The Swift pipeline discovers one restore directory and processes components in this order:

1. `AVPBooter` from VM root
2. `iBSS` from restore `Firmware/dfu/`
3. `iBEC` from restore `Firmware/dfu/`
4. `LLB` from restore `Firmware/all_flash/`
5. `TXM` from restore `Firmware/`
6. `kernelcache.research.vphone600`
7. `DeviceTree.vphone600ap`
8. `Filesystem` step for less only
9. `Manifest` step for less only

The loader handles IM4P containers and writes patched payloads back into the original files.

### Variant behavior

#### `make fw_patch`

Regular/base patch set:

- `AVPBooterPatcher`
- `IBootPatcher` for iBSS
- `IBootPatcher` for iBEC
- `IBootPatcher` for LLB
- `TXMPatcher`
- `KernelPatcher`
- `DeviceTreePatcher`

#### `sudo make fw_patch_less`

Patchless/minimal IM4P path:

- leaves AVPBooter/iBSS/TXM/kernel without their normal patchers
- still patches iBEC and LLB for serial logs
- patches DeviceTree
- runs `CryptexFilesystemPatcher` against the restore filesystem
- runs `ManifestHashPatcher` against `BuildManifest.plist`

This target must run as root because the filesystem patcher attaches/mounts/modifies disk images and APFS metadata.

#### `make fw_patch_dev`

Regular plus dev TXM behavior:

- same as regular, except `TXMDevPatcher` replaces `TXMPatcher`
- dev TXM patcher adds entitlement/debugger/developer-mode style bypasses

#### `make fw_patch_jb`

Jailbreak extension stack:

- iBSS runs `IBootPatcher` then `IBootJBPatcher`
- TXM uses `TXMDevPatcher`
- kernel runs `KernelPatcher` then `KernelJBPatcher`
- AVPBooter/iBEC/LLB/DeviceTree otherwise follow regular behavior

### Outputs

Patched files are written in place into the active VM restore tree and VM root ROM file.

If called with `--records-out` manually, the CLI can emit JSON `PatchRecord`s. The Makefile targets do not currently request records output.

### Gotchas

`fw_patch_less` refuses to run unless effective UID is 0. Use `sudo make fw_patch_less`, not plain `make fw_patch_less`.

A failed patch means the semantic matcher did not find the expected site. For iOS 18 work, that is signal. Do not force bytes into old offsets; update the matcher/research note.

Refs: `sources/FirmwarePatcher/Pipeline/FirmwarePipeline.swift`, patcher files under `sources/FirmwarePatcher/`, `research/0_binary_patch_comparison.md`.

---

## `restore_get_shsh`

### Story

This asks Apple TSS for the signing response corresponding to the prepared hybrid restore identity and the VM device identity. The output is later used by the ramdisk builder to sign IMG4 artifacts with an IM4M manifest.

Run it while `boot_dfu` is alive.

### Facts

Makefile target:

```make
cd $(VM_DIR) && "$(PYTHON)" "$(PMD3_BRIDGE)" restore-get-shsh \
  --vm-dir . \
  [--udid $(RESTORE_UDID)] \
  [--ecid $(RESTORE_ECID)]
```

`pymobiledevice3_bridge.py` does:

1. Find exactly one `iPhone*_Restore` directory.
2. Create an `IPSW` object from that directory.
3. Resolve device by usbmux lockdownd if possible, or irecv by ECID for DFU/recovery.
4. Fetch TSS with `Recovery(..., behavior=Behavior.Erase).fetch_tss_record()`.
5. Write SHSH plist to `VM_DIR/<ECID>.shsh` or `VM_DIR/auto.shsh` when ECID is unknown.

### Outputs

- `<ECID>.shsh` in `VM_DIR`

### Gotchas

If only UDID is provided and the device is not available over lockdownd, the bridge requires `RESTORE_ECID` for DFU/recovery targeting.

For automation, `setup_machine` reads identity from `udid-prediction.txt` and passes both UDID and ECID explicitly.

---

## `restore`

### Story

This performs the actual erase restore of the virtual device using the hybrid restore tree. It is the stage that writes firmware/system content onto `Disk.img` through the virtual DFU/recovery path.

Run it while `boot_dfu` is alive, usually immediately after `restore_get_shsh`.

### Facts

Makefile target:

```make
cd $(VM_DIR) && "$(PYTHON)" "$(PMD3_BRIDGE)" restore-update \
  --vm-dir . \
  [--udid $(RESTORE_UDID)] \
  [--ecid $(RESTORE_ECID)]
```

`pymobiledevice3_bridge.py` does:

1. Find the restore directory.
2. Create `IPSW` from the directory.
3. Resolve target device.
4. Run `Restore(ipsw, device, behavior=Behavior.Erase, ignore_fdr=False).update()`.

### Outputs

No new repo artifact is the primary output. The important output is the VM disk state: the virtual device has been restored.

### Gotchas

`restore` assumes the prepared tree is coherent. If the manifest points at wrong paths or signing identities are inconsistent, restore is where that becomes visible.

---

## `ramdisk_build`

### Story

The restore stage gets the OS onto disk. The CFW stage needs filesystem access before normal boot. `ramdisk_build` creates a signed SSH ramdisk chain from the patched restore tree and the fetched SHSH.

This is a host-side artifact builder. It does not send anything to the device.

### Facts

Target depends on `patcher_build`, then runs:

```make
cd $(VM_DIR) && RAMDISK_UDID="$(RAMDISK_UDID)" $(PYTHON) scripts/ramdisk_build.py .
```

`scripts/ramdisk_build.py`:

1. Finds SHSH in `VM_DIR` and extracts IM4M.
2. Ensures `ramdisk_input/` exists, extracting `ramdisk_input.tar.zst` if needed.
3. Creates/cleans `Ramdisk/` output.
4. Signs iBSS from the patched restore tree.
5. Patches iBEC boot-args for ramdisk boot and signs it.
6. Signs SPTM, DeviceTree, SEP.
7. Patches/signs TXM release variant for ramdisk chain.
8. Builds `krnl.img4` from the restore kernel.
9. Optionally builds `krnl.ramdisk.img4` from a ramdisk-specific kernel source/snapshot.
10. Extracts, expands, modifies, shrinks, and signs the restore ramdisk.
11. Builds trustcache for ramdisk contents.
12. Writes final IMG4 artifacts under `Ramdisk/`.

### Outputs

`VM_DIR/Ramdisk/` containing artifacts such as:

- `iBSS.vresearch101.RELEASE.img4`
- `iBEC.vresearch101.RELEASE.img4`
- `sptm.vresearch1.release.img4`
- `txm.img4`
- `trustcache.img4`
- `ramdisk.img4`
- `DeviceTree.vphone600ap.img4`
- `sep-firmware.vresearch101.RELEASE.img4`
- `krnl.img4`
- optional `krnl.ramdisk.img4`

### Gotchas

Requires a prior SHSH blob. If you skipped `restore_get_shsh`, signing cannot complete.

Requires host tools: `gtar`, `ldid`, `trustcache`, Python deps, and the Swift debug patcher.

Some operations use sudo because DMG attach/resize/mount work needs elevated host privileges.

---

## `ramdisk_send`

### Story

This sends the signed ramdisk boot chain to the VM while it is in DFU mode. After it succeeds, the virtual device should boot into the SSH ramdisk, which exposes enough filesystem access for `cfw_install*`.

Run it while `boot_dfu` is alive.

### Facts

Makefile target:

```make
cd $(VM_DIR) && PMD3_BRIDGE=... PYTHON=... IRECOVERY_ECID=... RAMDISK_UDID=... RESTORE_UDID=... \
  zsh scripts/ramdisk_send.sh
```

`ramdisk_send.sh` normalizes `IRECOVERY_ECID`, validates `Ramdisk/`, then calls:

```bash
python pymobiledevice3_bridge.py ramdisk-send --ramdisk-dir Ramdisk [--ecid 0x...]
```

The bridge sends:

1. iBSS over DFU
2. iBEC over DFU
3. `go`, then waits for recovery reconnect
4. SPTM
5. TXM
6. trustcache
7. ramdisk
8. device tree
9. SEP
10. kernel via `bootx`

### Outputs

No local output is the main artifact. The expected state is: VM is booting into the custom SSH ramdisk.

### Gotchas

`ramdisk_send` does not create the local usbmux/SSH forwarding. Manual flow still needs something like:

```bash
python3 -m pymobiledevice3 usbmux forward 2222 22
```

`setup_machine` handles this by starting iproxy/usbmux forwarding internally and discovering the port.

---

## `cfw_install`

### Story

This installs the base custom firmware modifications from the SSH ramdisk into the restored root filesystem. It is the bridge between "restored stock-ish firmware" and "usable research VM with guest daemon/tools".

It runs over SSH to the ramdisk as `root:alpine` through local `SSH_PORT`.

### Facts

Makefile target:

```make
cd $(VM_DIR) && [SSH_PORT=...] _VPHONE_PATH="$PATH" zsh scripts/cfw_install.sh .
```

The script is designed to be idempotent: it keeps `.bak` copies and patches from original backups where possible.

Base phases:

1. Install Cryptex SystemOS + AppOS into `/mnt1/System/Cryptexes`, rename APFS update snapshot to `orig-fs`, and create dyld symlinks.
2. Patch `/usr/libexec/seputil`, sign it, and normalize gigalocker naming on disk1s3.
3. Install `AppleParavirtGPUMetalIOGPUFamily` bundle.
4. Install `iosbinpack64`.
5. Patch `/usr/libexec/launchd_cache_loader`.
6. Patch `/usr/libexec/mobileactivationd`.
7. Build/sign/install `vphoned`, install LaunchDaemons, and patch `System/Library/xpc/launchd.plist` to load them.

### Inputs

- running SSH ramdisk
- `cfw_input/` in `VM_DIR`, or `cfw_input.tar.zst` in resources/script/VM dir
- restore tree with `iPhone-BuildManifest.plist`
- `ipsw`, `aea`, `sshpass`, `ldid`
- Python venv with capstone/keystone

### Outputs

On guest filesystem:

- Cryptex content and symlinks
- patched `seputil`
- paravirt GPU driver bundle
- `iosbinpack64`
- patched `launchd_cache_loader`
- patched `mobileactivationd`
- `vphoned`
- LaunchDaemons for bash/dropbear/trollvnc/rpcserver/vphoned
- patched launchd service registry plist

On host VM dir:

- `.cfw_temp/` with cached Cryptex DMGs and temp files
- `.vphoned.signed`

### Gotchas

Manual flow needs port forwarding first. Default expectation is local `2222 -> guest 22`.

At the end, unless `CFW_SKIP_HALT=1`, the script halts the guest so you can normal boot into the modified filesystem.

---

## `cfw_install_dev`

### Story

Development CFW is base CFW plus a dev overlay. It pairs with `fw_patch_dev` because the firmware side enables TXM/dev behavior and the filesystem side provides the dev userland pieces.

### Facts

Makefile target shape is the same as `cfw_install`, but calls `scripts/cfw_install_dev.sh`.

It performs the same seven base phases as regular CFW, plus applies the dev overlay before installing `iosbinpack64`:

- finds `resources/cfw_dev/rpcserver_ios` or `scripts/cfw_dev/rpcserver_ios`
- opens `cfw_input/jb/iosbinpack64.tar`
- replaces `iosbinpack64/usr/local/bin/rpcserver_ios`
- repacks the tar

### Gotchas

Use this with `fw_patch_dev`, not with regular firmware, unless you are deliberately testing mismatch behavior.

---

## `cfw_install_jb`

### Story

Jailbreak CFW runs base CFW first, then layers JB-specific runtime changes on top: launchd hook injection, procursus bootstrap, basebin hooks, debugserver entitlements, tweak loader, and first-boot setup.

It pairs with `fw_patch_jb`.

### Facts

The script first runs:

```bash
CFW_SKIP_HALT=1 zsh scripts/cfw_install.sh <VM_DIR>
```

Then it runs JB phases:

1. Patch `/sbin/launchd`: preserve original entitlements, inject short `/b` dylib load for launch hook, patch jetsam guard, re-sign.
2. Install `iosbinpack64`.
3. Patch `debugserver` entitlements by removing seatbelt profile and adding `task_for_pid-allow`.
4. Install procursus bootstrap into the boot manifest hash directory on disk1s5.
5. Deploy BaseBin dylibs under `/cores/` and install short `/b` alias for `launchdhook.dylib`.
6. Build and install `TweakLoader.dylib` into procursus `usr/lib`.
7. Deploy `/cores/vphone_jb_setup.sh` and inject `com.vphone.jb-setup.plist` into launchd plist for first normal boot.

### Inputs

- everything required by base `cfw_install`
- `cfw_jb_input/` or `cfw_jb_input.tar.zst`
- `zstd`
- Xcode command line tools for building TweakLoader

### Outputs

On guest filesystem:

- patched `launchd`
- procursus bootstrap payload
- optional Sileo `.deb`
- `/cores` dylib hooks
- `/b` short launchd hook alias
- `TweakLoader.dylib`
- first-boot JB setup LaunchDaemon

### Gotchas

The JB finalization does not fully happen during ramdisk install. First normal boot runs `/cores/vphone_jb_setup.sh` via LaunchDaemon. Monitor:

```text
/var/log/vphone_jb_setup.log
```

---

## `fw_patch_less` + `boot_less` flow

Patchless deserves its own note because it breaks the regular mental model.

Regular/dev/jb do:

```text
fw_prepare -> fw_patch* -> restore -> ramdisk_build/send -> cfw_install* -> boot
```

Patchless does:

```text
fw_prepare -> sudo fw_patch_less -> restore -> boot_less
```

The `less` patcher performs filesystem/Cryptex/manifest surgery before restore, so `setup_machine LESS=1` skips the ramdisk + CFW phase entirely. That is why `cfw_install_target` is empty in the setup script for less mode.

If you manually run `cfw_install` after a less restore, you are no longer testing the clean patchless path.

---

## `restore` + `ramdisk` terminal choreography

Manual setup requires multiple terminals because some commands are long-running providers.

### Restore stage

Terminal 1:

```bash
make boot_dfu
```

Terminal 2:

```bash
make restore_get_shsh
make restore
```

### CFW stage

Terminal 1:

```bash
make boot_dfu
```

Terminal 2:

```bash
sudo make ramdisk_build
make ramdisk_send
```

Terminal 3:

```bash
python3 -m pymobiledevice3 usbmux forward 2222 22
```

Terminal 2:

```bash
make cfw_install
# or make cfw_install_dev
# or make cfw_install_jb
```

This choreography is not ceremony. `boot_dfu` provides the virtual DFU device, `ramdisk_send` changes it into an SSH ramdisk, and usbmux forwarding gives the host installer a TCP path into that ramdisk.

---

## Target dependency map

High-level dependencies as implemented by the Makefile:

```text
setup_machine
  -> setup_tools
  -> build
  -> vm_new
  -> fw_prepare
  -> fw_patch* / sudo fw_patch_less
  -> boot_dfu + restore_get_shsh + restore
  -> non-less: boot_dfu + ramdisk_build + ramdisk_send + cfw_install*
  -> boot / boot_less

boot
  -> bundle
    -> build
  -> vphoned
  -> boot_binary_check

boot_less
  -> bundle
  -> vphoned
  -> boot_binary_check_less

boot_dfu
  -> build
  -> boot_binary_check

fw_patch*
  -> patcher_build

ramdisk_build
  -> patcher_build

amfidont_allow_vphone
  -> bundle
```

---

## Practical iOS 18 retargeting checklist

Use this when changing firmware generation, not as a generic setup checklist.

1. Run `make setup_tools` once and confirm `.venv` imports capstone/keystone/pyimg4/pymobiledevice3.
2. Run `make build` and `make boot_host_preflight` before debugging firmware. If host signing is broken, firmware results are noise.
3. Create a fresh VM with a versioned name or backup current state first.
4. Run `make fw_prepare` with explicit `IPHONE_SOURCE` / `CLOUDOS_SOURCE` or explicit version/build variables. Do not rely on stale cached assumptions.
5. Diff `iPhone-BuildManifest.plist` vs generated `BuildManifest.plist` and confirm the hybrid identity selects expected iPhone vs cloudOS paths.
6. Run the smallest patch variant that answers your question. For matcher porting, `fw_patch` is easier to reason about than full JB.
7. If a patch matcher fails, update the semantic locator. Do not use hardcoded old offsets.
8. Keep `research/0_binary_patch_comparison.md` updated only when you actually add/change patch behavior, per repo rules.
9. Restore with explicit `RESTORE_UDID` / `RESTORE_ECID` once identity is known. Avoid auto-target ambiguity.
10. Snapshot known-good VM states with `vm_backup NAME=<version-variant>` before moving to the next variant.

---

## Quick command index

| Target | State transition | Main script/binary |
| --- | --- | --- |
| `help` | print command map | Makefile only |
| `setup_machine` | full setup orchestration | `scripts/setup_machine.sh` |
| `setup_tools` | install/build host tooling | `scripts/setup_tools.sh` |
| `build` | release Swift build + sign | `swift build -c release`, `codesign` |
| `patcher_build` | debug Swift patcher build | `swift build` |
| `bundle` | create `.app` wrapper | Makefile copy/sign steps |
| `vphoned` | build/sign guest daemon | `scripts/vphoned/Makefile`, `ldid` |
| `clean` | remove untracked/ignored repo state | `git clean -fdx` with exclusions |
| `vm_new` | create VM bundle skeleton | `scripts/vm_create.sh`, `scripts/vm_manifest.py` |
| `vm_backup` | save VM bundle | `scripts/vm_backup.sh` |
| `vm_restore` | restore VM backup | `scripts/vm_restore.sh` |
| `vm_switch` | save current + restore target | `scripts/vm_switch.sh` |
| `vm_list` | list backups | Makefile shell loop |
| `amfidont_allow_vphone` | start AMFI allow helper | `scripts/start_amfidont_for_vphone.sh` |
| `boot_host_preflight` | diagnose host launchability | `scripts/boot_host_preflight.sh` |
| `boot_binary_check` | internal normal boot gate | `boot_host_preflight.sh --assert-bootable` |
| `boot_binary_check_less` | internal less boot gate | `boot_host_preflight.sh --assert-bootable --less` |
| `boot` | normal GUI/control boot | `.build/vphone-cli.app/.../vphone-cli` |
| `boot_less` | normal patchless boot | app bundle with `--variant less` |
| `boot_dfu` | headless DFU provider | release binary with `--dfu` |
| `fw_prepare` | create hybrid restore tree | `scripts/fw_prepare.sh`, `scripts/fw_manifest.py` |
| `fw_patch` | regular firmware patches | debug `vphone-cli patch-firmware --variant regular` |
| `fw_patch_less` | patchless filesystem/manifest path | debug `vphone-cli patch-firmware --variant less` |
| `fw_patch_dev` | dev firmware patches | debug `vphone-cli patch-firmware --variant dev` |
| `fw_patch_jb` | jailbreak firmware patches | debug `vphone-cli patch-firmware --variant jb` |
| `restore_get_shsh` | fetch TSS/SHSH | `scripts/pymobiledevice3_bridge.py restore-get-shsh` |
| `restore` | erase restore VM | `scripts/pymobiledevice3_bridge.py restore-update` |
| `ramdisk_build` | build signed SSH ramdisk | `scripts/ramdisk_build.py` |
| `ramdisk_send` | send ramdisk boot chain | `scripts/ramdisk_send.sh`, bridge `ramdisk-send` |
| `cfw_install` | base guest CFW install | `scripts/cfw_install.sh` |
| `cfw_install_dev` | base CFW + dev overlay | `scripts/cfw_install_dev.sh` |
| `cfw_install_jb` | base CFW + jailbreak stack | `scripts/cfw_install_jb.sh` |
