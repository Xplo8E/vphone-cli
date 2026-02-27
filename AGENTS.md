# Agent Instructions

## Canonical Docs
- `README.md` — script-first quickstart.
- `SETUP.md` — host + build + firmware mix + VM scaffold.
- `VPHONE_RUNBOOK.md` — operational flow (restore, ramdisk, rootfs, SSH/VNC, jailbreak stages).
- `docs/DETAILED_GUIDE.md` — deep-dive notes and references.
- `docs/cc-tut.md` — deprecated pointer to `../VPHONE_RUNBOOK.md`.

## Package Manager
- Homebrew (host deps):
```bash
brew install automake autoconf libtool pkg-config \
             libplist openssl@3 libimobiledevice-glue \
             libimobiledevice libtatsu libzip \
             ldid sshpass gtar usbmuxd
```
- Python env:
```bash
bash setup_bin.sh
# or
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
- Repo environment:
```bash
source setup_env.sh
```

## Commit Attribution
- AI commits MUST include:
```text
Co-Authored-By: Codex (GPT-5) <noreply@openai.com>
```

## Key Conventions
- Run commands from repo root unless a section says otherwise.
- Use repo-root variables; avoid hardcoded absolute paths:
```bash
REPO="$(pwd)"
FW="$REPO/firmwares/firmware_patched/iPhone17,3_26.1_23B85_Restore"
```
- Use `source setup_env.sh` before `tart`, `irecovery`, or patch scripts.
- First rootfs pass is full:
```bash
cd patch_scripts
python3 setup_rootfs.py --no-halt
```
- Re-run rootfs for daemon refresh only:
```bash
python3 setup_rootfs.py --skip-cryptex --skip-patches --no-halt
```
- Normal boot SSH uses dropbear guest port `22222` (`iproxy 2222 22222`).
- Ramdisk SSH uses guest port `22` (`iproxy 2222 22`).
- If SSH closes immediately in normal boot, initialize dropbear host key from serial shell (`/var/dropbear/dropbear_rsa_host_key`).
- Jetsam panic (`initproc exited ... jetsam property category (Daemon) is not initialized`) mitigation:
```bash
python3 patch_scripts/setup_rootfs.py --skip-cryptex --skip-iosbinpack --skip-daemons --patch-launchd --no-halt
```

## Repository Layout
- `oems/` — upstream dependency repos listed in `.gitmodules` (currently cloned locally).
- `patch_oems/` — local OEM patch sets.
- `patch_scripts/` — firmware/ramdisk/rootfs/jailbreak tooling.
- `jb/` — payloads, LaunchDaemons, jailbreak assets.
- `bin/` — built tools (generated, gitignored).
- `firmwares/` — IPSWs + mixed/working firmware trees (generated, gitignored).
- `Ramdisk/` — generated IMG4s (gitignored except placeholders).
- `shsh/` — generated tickets (gitignored except placeholders).
- `checkpoints/` — optional local tarball snapshots (gitignored except placeholders).

## Standard Flow
```bash
bash setup_bin.sh
source setup_env.sh
bash setup_download_fw.sh

cd patch_scripts
python3 patch_fw.py -d ../firmwares/firmware_patched/iPhone17,3_26.1_23B85_Restore --kernel-jb-extra --txm-jb-extra
python3 prepare_ramdisk.py

cd ..
./vm_boot_dfu.sh vphone

cd patch_scripts
bash boot_rd.sh
python3 setup_rootfs.py --no-halt
```

## Gitignored Artifacts
- Keep generated artifacts out of commits:
  - `bin/`, `.local/`, `.venv/`, `.tart/`, `.swiftpm/`, `.swift-home/`
  - `firmwares/*`, `Ramdisk/*`, `shsh/*`, `checkpoints/*`, `patch_scripts/raw/*`
  - `patch_scripts/metal_cache/`, `patch_scripts/metal_plugin/`
  - `*.ipsw`, `*.im4m`, `*.shsh`, `*.shsh.gz`, `patch_scripts/signcert.p12`, `nvram.bin`

## OEM Source Refresh
- Reclone `oems/*` from `.gitmodules` URLs:
```bash
git config -f .gitmodules --get-regexp '^submodule\..*\.path$' | while read -r key spath; do
  sname="${key#submodule.}"
  sname="${sname%.path}"
  surl="$(git config -f .gitmodules --get "submodule.${sname}.url")"
  [ -d "$spath/.git" ] && continue
  git clone --depth 1 "$surl" "$spath"
done
```

## Local Skills
- No project-local skills discovered at:
  - `.claude/skills`
  - `plugins/*/skills/*/SKILL.md`
