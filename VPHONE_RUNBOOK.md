# VPHONE Runbook (Repo-Root Friendly)

This is a practical end-to-end command guide for this repo.

It covers:
- firmware patch + restore
- ramdisk + rootfs setup
- SSH / TrollVNC fixes
- jetsam panic mitigation
- jailbreak staging (Procursus + basebin)

## 0) One-Time Setup Variables

Run from repo root.

```bash
pwd
REPO="$(pwd)"
FW="$REPO/_work/firmwares/firmware_patched/iPhone17,3_26.1_23B85_Restore"
```

Why this style:
- avoids hardcoded absolute paths
- easier to copy/paste on any machine
- matches current script defaults (`_work/...`); legacy `firmwares/...` is still auto-detected

---

## 1) Firmware Patch + Verify + Restore (Fresh Start)

### 1.1 Check patch options (recommended)

```bash
cd "$REPO"
python3 patch_scripts/patch_fw.py --help
```

Use this to confirm available flags before patching.

### 1.2 Patch firmware

```bash
cd "$REPO"
python3 patch_scripts/patch_fw.py -d "$FW" --kernel-jb-extra --txm-jb-extra
```

### 1.3 Verify patched outputs

```bash
python3 patch_scripts/patch_fw.py -d "$FW" --verify-only
```

Optional strict check:

```bash
python3 patch_scripts/patch_fw.py -d "$FW" --verify-only | tee /tmp/patch_fw_verify.log
grep -E "WARNING|FAILED|ERROR" /tmp/patch_fw_verify.log && echo "Review warnings before continuing"
```

### 1.4 Restore patched firmware

Terminal A:

```bash
cd "$REPO"
source setup_env.sh
"$REPO/bin/tart" run vphone --dfu --serial
```

Terminal B:

```bash
cd "$REPO"
"$REPO/bin/idevicerestore" -e -y "$FW"
```

After restore, panic will happen, u dont need to panic it's expected, continue with ramdisk steps. 

---

## 2) Ramdisk Boot + Rootfs Setup

### 2.1 Boot DFU + ramdisk

Terminal A:

```bash
cd "$REPO"
source setup_env.sh
"$REPO/bin/tart" run vphone --dfu --serial
```

Terminal B:

```bash
iproxy 2222 22
```

Terminal C:

```bash
cd "$REPO/patch_scripts"
python3 prepare_ramdisk.py
bash boot_rd.sh
```

Note: do not use `--skip-shsh` unless you intentionally reuse a valid matching ticket.

### 2.2 First-time rootfs setup (full)

```bash
cd "$REPO/patch_scripts"
python3 setup_rootfs.py --no-halt
```

This is the correct first pass after a fresh restore.

### 2.3 Re-run rootfs (faster, partial)

Use this only when you already did a full rootfs run and just need daemon/iosbinpack refresh:

```bash
cd "$REPO/patch_scripts"
python3 setup_rootfs.py \
  --skip-cryptex \
  --skip-patches \
  --no-halt
```

### 2.4 Optional: GPU payload setup during rootfs

```bash
cd "$REPO/patch_scripts"
python3 setup_rootfs.py \
  --pcc-gpu-bundle "$REPO/patch_scripts/metal_cache/AppleParavirtGPUMetalIOGPUFamily.bundle" \
  --pcc-gpu-plugin "$REPO/patch_scripts/metal_plugin/libAppleParavirtCompilerPluginIOGPUFamily.dylib" \
  --no-halt
```

---

## 3) Verify Daemons and launchd Injection (Before Halt)

### 3.1 Verify uploaded binaries + plists in ramdisk shell

```bash
ssh -o StrictHostKeyChecking=no -p 2222 root@127.0.0.1 \
'ls -l /mnt1/iosbinpack64/usr/local/bin/dropbear /mnt1/iosbinpack64/bin/bash /mnt1/iosbinpack64/bin/trollvncserver /mnt1/System/Library/LaunchDaemons/bash.plist /mnt1/System/Library/LaunchDaemons/dropbear.plist /mnt1/System/Library/LaunchDaemons/trollvnc.plist'
```

### 3.2 Verify launchd.plist injection from host

```bash
scp -O -P 2222 root@127.0.0.1:/mnt1/System/Library/xpc/launchd.plist /tmp/launchd.vphone.plist
/usr/bin/plutil -convert xml1 -o - /tmp/launchd.vphone.plist | grep -nE 'bash\.plist|dropbear\.plist|trollvnc\.plist'
```

---

## 4) Jetsam Panic Mitigation (Only If You Hit Panic)

Symptom:
`initproc exited ... jetsam property category (Daemon) is not initialized`

Apply launchd mitigation:

```bash
cd "$REPO/patch_scripts"
python3 setup_rootfs.py \
  --skip-cryptex \
  --skip-iosbinpack \
  --skip-daemons \
  --patch-launchd \
  --no-halt
```

Verify patch bytes:

```bash
scp -O -P 2222 root@127.0.0.1:/mnt1/sbin/launchd /tmp/launchd.patched
xxd -g 1 -l 4 -s 0xd73c /tmp/launchd.patched
# expected: 17 00 00 14
```

```bash
scp -O -P 2222 root@127.0.0.1:/mnt1/usr/libexec/launchd_cache_loader /tmp/launchd_cache_loader.patched
xxd -g 1 -l 4 -s 0xb58 /tmp/launchd_cache_loader.patched
# expected: 1f 20 03 d5
```

---

## 5) Halt Ramdisk and Boot Normal

```bash
ssh -o StrictHostKeyChecking=no -p 2222 root@127.0.0.1 '/sbin/halt'
```

Normal boot:

```bash
cd "$REPO"
"$REPO/bin/tart" run vphone --vnc --serial
```

---

## 6) Normal Boot Access (SSH + VNC)

### 6.1 SSH tunnel (dropbear port is 22222)

```bash
pkill -f 'iproxy 2222' 2>/dev/null || true
iproxy 2222 22222
```

Then:

```bash
ssh root@127.0.0.1 -p 2222
```

### 6.2 VNC tunnel

```bash
iproxy 5901 5901
```

Connect VNC client to `127.0.0.1:5901` (password: `alpine`).

---

## 7) If SSH Closes Immediately (Dropbear Host Key Fix)

If GUI/VNC works but SSH drops during handshake, initialize dropbear host key once from serial shell:

```bash
export PATH='/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/bin/X11:/usr/games:/iosbinpack64/usr/local/sbin:/iosbinpack64/usr/local/bin:/iosbinpack64/usr/sbin:/iosbinpack64/usr/bin:/iosbinpack64/sbin:/iosbinpack64/bin'
/iosbinpack64/bin/mkdir -p /var/dropbear
/iosbinpack64/bin/cp /iosbinpack64/etc/profile /var/profile
/iosbinpack64/bin/cp /iosbinpack64/etc/motd /var/motd
dropbearkey -t rsa -s 2048 -f /var/dropbear/dropbear_rsa_host_key
chmod 600 /var/dropbear/dropbear_rsa_host_key
```

Reconnect:

```bash
pkill -f 'iproxy 2222' 2>/dev/null || true
iproxy 2222 22222
ssh root@127.0.0.1 -p 2222
```

---

## 8) Persistent Shell Env for SSH Sessions

If commands like `ls` fail, fix PATH/TERM/SHELL:

```bash
export PATH='/var/jb/usr/local/sbin:/var/jb/usr/local/bin:/var/jb/usr/sbin:/var/jb/usr/bin:/var/jb/sbin:/var/jb/bin:/iosbinpack64/usr/local/sbin:/iosbinpack64/usr/local/bin:/iosbinpack64/usr/sbin:/iosbinpack64/usr/bin:/iosbinpack64/sbin:/iosbinpack64/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
export TERM='xterm-256color'
export SHELL='/iosbinpack64/bin/bash'
```

Persist in `/var/profile`:

```bash
/iosbinpack64/bin/cp /iosbinpack64/etc/profile /var/profile
/iosbinpack64/usr/bin/grep -q "var/jb/usr/bin" /var/profile || /iosbinpack64/bin/cat >> /var/profile <<'EOF2'
export PATH='/var/jb/usr/local/sbin:/var/jb/usr/local/bin:/var/jb/usr/sbin:/var/jb/usr/bin:/var/jb/sbin:/var/jb/bin:/iosbinpack64/usr/local/sbin:/iosbinpack64/usr/local/bin:/iosbinpack64/usr/sbin:/iosbinpack64/usr/bin:/iosbinpack64/sbin:/iosbinpack64/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
export TERM='xterm-256color'
export SHELL='/iosbinpack64/bin/bash'
EOF2
/iosbinpack64/bin/cp /var/profile /var/root/.profile
```

---

## 9) FAQ: `apt` Works Once, Fails After Re-login

Symptom:

- `apt --version` works after manual export.
- After reconnecting SSH, `apt: command not found`.

Cause:

- `apt` lives in `/var/jb/usr/bin`.
- SSH default PATH often only includes base + `/iosbinpack64`, not `/var/jb/usr/bin`.

Fix in current SSH session:

```bash
export PATH='/var/jb/usr/local/sbin:/var/jb/usr/local/bin:/var/jb/usr/sbin:/var/jb/usr/bin:/var/jb/sbin:/var/jb/bin:/iosbinpack64/usr/local/sbin:/iosbinpack64/usr/local/bin:/iosbinpack64/usr/sbin:/iosbinpack64/usr/bin:/iosbinpack64/sbin:/iosbinpack64/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
export TERM='xterm-256color'
export SHELL='/iosbinpack64/bin/bash'
if [ ! -x /var/jb/usr/bin/apt ]; then
  HASH="$(/iosbinpack64/bin/ls /private/preboot | /iosbinpack64/usr/bin/head -n1)"
  /iosbinpack64/bin/ln -sfn "/private/preboot/$HASH/jb-vphone/procursus" /private/var/jb
fi
/var/jb/usr/bin/apt --version
```

Persist for future SSH logins:

```bash
/iosbinpack64/bin/cp /iosbinpack64/etc/profile /var/profile 2>/dev/null || true
/iosbinpack64/usr/bin/grep -q "var/jb/usr/bin" /var/profile || /iosbinpack64/bin/cat >> /var/profile <<'EOF2'
export PATH='/var/jb/usr/local/sbin:/var/jb/usr/local/bin:/var/jb/usr/sbin:/var/jb/usr/bin:/var/jb/sbin:/var/jb/bin:/iosbinpack64/usr/local/sbin:/iosbinpack64/usr/local/bin:/iosbinpack64/usr/sbin:/iosbinpack64/usr/bin:/iosbinpack64/sbin:/iosbinpack64/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin'
export TERM='xterm-256color'
export SHELL='/iosbinpack64/bin/bash'
EOF2
/iosbinpack64/bin/cp /var/profile /var/root/.profile
```

Reliable fallback (works even if PATH is wrong):

```bash
/var/jb/usr/bin/apt update
/var/jb/usr/bin/apt install -y <package-name>
```

### 9.1 Fix Procursus `Signed-By` / `NO_PUBKEY` Warning

If `apt update` shows:

- `Missing Signed-By ...`
- `NO_PUBKEY 6430292CF9551B0E`
- duplicate target warnings for `procursus.sources` and `procursus.sources.list`

use this exact fix:

```bash
rm -f /var/jb/etc/apt/sources.list.d/procursus.sources.list
mkdir -p /var/jb/usr/share/keyrings
curl -fsSL https://apt.procurs.us/memo.gpg -o /var/jb/usr/share/keyrings/procursus.gpg
cat > /var/jb/etc/apt/sources.list.d/procursus.sources <<'EOF'
Types: deb
URIs: https://apt.procurs.us/
Suites: 1900
Components: main
Signed-By: /var/jb/usr/share/keyrings/procursus.gpg
EOF
apt update
```

Note:

- `https://apt.procurs.us/apt.key` currently returns 404; use `memo.gpg`.

### 9.2 Add Third-Party Repos (deb822 `.sources` format)

Use the modern deb822 format (same as `procursus.sources`) instead of legacy `.list` files. Run all of these at once to add the commonly needed repos:

```bash
cat > /var/jb/etc/apt/sources.list.d/appknox.sources << 'EOF'
Types: deb
URIs: https://cydia.appknox.com/
Suites: ./
Trusted: yes
EOF

cat > /var/jb/etc/apt/sources.list.d/ellekit_space.sources << 'EOF'
Types: deb
URIs: https://ellekit.space/
Suites: ./
Architectures: iphoneos-arm64
Trusted: yes
EOF

cat > /var/jb/etc/apt/sources.list.d/frida.sources << 'EOF'
Types: deb
URIs: https://build.frida.re/
Suites: ./
Architectures: iphoneos-arm64
Trusted: yes
EOF

cat > /var/jb/etc/apt/sources.list.d/havoc.sources << 'EOF'
Types: deb
URIs: https://havoc.app/
Suites: ./
Architectures: iphoneos-arm64
Trusted: yes
EOF

cat > /var/jb/etc/apt/sources.list.d/jjolano.sources << 'EOF'
Types: deb
URIs: https://ios.jjolano.me/
Suites: ./
Architectures: iphoneos-arm64
Trusted: yes
EOF

cat > /var/jb/etc/apt/sources.list.d/opa334.sources << 'EOF'
Types: deb
URIs: https://opa334.github.io/
Suites: ./
Architectures: iphoneos-arm64
Trusted: yes
EOF

cat > /var/jb/etc/apt/sources.list.d/ryley.sources << 'EOF'
Types: deb
URIs: https://ryleyangus.com/repo/
Suites: ./
Architectures: iphoneos-arm64
Trusted: yes
EOF

cat > /var/jb/etc/apt/sources.list.d/xplo8e.sources << 'EOF'
Types: deb
URIs: https://xplo8e.github.io/sileo/
Suites: ./
Architectures: iphoneos-arm64
Trusted: yes
EOF

apt update
```

If you previously added repos using the old `.list` format, remove them first:

```bash
rm -f /var/jb/etc/apt/sources.list.d/*.list
apt update
```

---

## 10) Procursus/Jailbreak Stages (A/B/C)

### Stage A: DFU + ramdisk + stage Procursus payload

```bash
cd "$REPO"
source setup_env.sh
"$REPO/bin/tart" run vphone --dfu --serial
```

```bash
# new terminal
iproxy 2222 22
```

```bash
# new terminal
cd "$REPO"
python3 patch_scripts/prepare_ramdisk.py -d "$FW" --skip-shsh
bash patch_scripts/boot_rd.sh
cd "$REPO/patch_scripts"
python3 install_jb_procursus.py
ssh -o StrictHostKeyChecking=no -p 2222 root@127.0.0.1 'halt'
```

### Stage B: normal boot + finalize Procursus + install Sileo

```bash
cd "$REPO"
"$REPO/bin/tart" run vphone --vnc --serial
```

```bash
# host terminal
pkill -f 'iproxy 2222' 2>/dev/null || true
iproxy 2222 22222
ssh -o StrictHostKeyChecking=no -p 2222 root@127.0.0.1
```

Inside guest shell:

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
apt update
apt install -y libkrw0-tfp0
apt upgrade -y || apt upgrade -y --allow-downgrades
halt
```

### Stage C: DFU + ramdisk + install basebin hooks (jetsam patch)

```bash
cd "$REPO"
source setup_env.sh
"$REPO/bin/tart" run vphone --dfu --serial
```

```bash
# new terminal
iproxy 2222 22
```

```bash
# new terminal
cd "$REPO"
python3 patch_scripts/prepare_ramdisk.py -d "$FW" --skip-shsh
bash patch_scripts/boot_rd.sh
cd "$REPO/patch_scripts"
python3 install_jb_basebin.py --jetsam-patch
```

Final normal boot + validation:

```bash
cd "$REPO"
"$REPO/bin/tart" run vphone --vnc --serial
```

```bash
pkill -f 'iproxy 2222' 2>/dev/null || true
iproxy 2222 22222
ssh -o StrictHostKeyChecking=no -p 2222 root@127.0.0.1 \
'export PATH="/iosbinpack64/usr/local/bin:/iosbinpack64/usr/bin:/iosbinpack64/bin:/usr/bin:/bin:/usr/sbin:/sbin"; /iosbinpack64/bin/ls -l /cores/systemhook.dylib /cores/launchdhook.dylib /cores/libellekit.dylib /var/jb/.procursus_strapped /var/jb/.installed_dopamine'
```


## 11) ElleKit — Fix Injection Permissions

ElleKit uses `systemhook.dylib` (loaded into launchd) to inject dylibs into processes via `posix_spawn` hooking. If the ElleKit dylibs in `/var/jb/usr/lib/ellekit/` have wrong permissions or no entitlements, the kernel sandbox blocks them from loading — and nothing gets injected into anything.

### 11.1 Symptoms

- Tweaks not loading in any process
- `idevicesyslog` shows: `kernel(Sandbox): deny(1) file-read-data .../ellekit/libinjector.dylib`
- `lsof -p $(pgrep installd) | grep ellekit` returns nothing

### 11.2 Verify ElleKit is loaded in launchd

```bash
lsof -p 1 | grep -i "systemhook\|ellekit"
```

Both `systemhook.dylib` and `libellekit.dylib` should appear. If they do, the base injection infrastructure is working.

### 11.3 Fix dylib permissions and entitlements

The ElleKit dylibs ship with `644` permissions (not executable) and no entitlements — this causes sandbox denials when they're mapped into processes.

```bash
# fix permissions
chmod 755 /var/jb/usr/lib/ellekit/libinjector.dylib
chmod 755 /var/jb/usr/lib/ellekit/pspawn.dylib
chmod 755 /var/jb/usr/lib/ellekit/MobileSafety.dylib

# create entitlements plist
cat > /tmp/ellekit-ent.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>platform-application</key>
    <true/>
    <key>com.apple.private.security.no-container</key>
    <true/>
    <key>com.apple.private.skip-library-validation</key>
    <true/>
</dict>
</plist>
EOF

# sign all three dylibs
ldid -S/tmp/ellekit-ent.plist /var/jb/usr/lib/ellekit/libinjector.dylib
ldid -S/tmp/ellekit-ent.plist /var/jb/usr/lib/ellekit/pspawn.dylib
ldid -S/tmp/ellekit-ent.plist /var/jb/usr/lib/ellekit/MobileSafety.dylib
```

Verify the entitlements applied:

```bash
ldid -e /var/jb/usr/lib/ellekit/libinjector.dylib
```

### 11.4 Create ElleKit pspawn config

ElleKit needs a config dir to know which dylibs to inject into which processes. Without it, nothing gets injected even if the infrastructure is working.

```bash
mkdir -p /var/jb/etc/ellekit
cat > /var/jb/etc/ellekit/pspawn.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>installd</key>
    <array>
        <string>/var/jb/usr/lib/TweakInject/AppSyncUnified-installd.dylib</string>
    </array>
</dict>
</plist>
EOF
```

Reboot for changes to take effect.

---

## 12) Installing Apps via TrollStore

### Why ideviceinstaller fails on iOS 26

`ideviceinstaller` routes installs through `installd` which runs as `_installd` (non-root system user). ElleKit's `systemhook.dylib` only injects into processes launched by launchd as root — it cannot cross the user boundary into `_installd`. This means AppSync Unified never loads into installd, so `MICodeSigningVerifier` runs unhooked and rejects any adhoc-signed IPA.

### Why TrollStore UI fails

TrollStoreLite runs as `mobile` (euid 501). When you tap install, it tries to `posix_spawn` `trollstorehelper` to do the actual work. This spawn fails with `error 1 (EPERM)` because a sandboxed mobile-user process cannot spawn a privileged helper on iOS 26 — even with `no-sandbox` entitlements.

### Working method — invoke trollstorehelper directly from root shell

TrollStore's install mechanism bypasses `installd` entirely — it uses `ldid` to re-sign the binary with `jb.pmap_cs_custom_trust = PMAP_CS_APP_STORE` (which tells the kernel to treat it as a trusted App Store app), then installs directly via `MCMAppContainer` private API.

First, symlink `trollstorehelper` into PATH so you can call it from anywhere:

```bash
HASH="$(ls /private/preboot/ | head -n1)"
ln -sfn /private/preboot/$HASH/jb-vphone/procursus/Applications/TrollStoreLite.app/trollstorehelper /var/jb/usr/bin/trollstorehelper
```

Then install any IPA:

```bash
trollstorehelper install "/path/to/app.ipa"
```

After install, register with SpringBoard:

```bash
uicache -a
```

To remove the symlink later:

```bash
rm /var/jb/usr/bin/trollstorehelper
```

### Finding the IPA path

IPAs downloaded via the Files app are stored in the Files app's shared container:

```
/private/var/mobile/Containers/Shared/AppGroup/<UUID>/File Provider Storage/Downloads/<app>.ipa
```

Find it on device:

```bash
find /private/var/mobile/Containers/Shared/AppGroup -name "*.ipa" 2>/dev/null
```

### Full example

```bash
trollstorehelper install '/private/var/mobile/Containers/Shared/AppGroup/A1B432C4-2BFB-42B9-B38D-B1F2BFBA601C/File Provider Storage/Downloads/geekbench-6-v6.1.0.ipa'
uicache -a
```

`trollstorehelper returning 0` = success.