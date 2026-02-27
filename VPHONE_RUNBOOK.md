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
./vm_boot_dfu.sh vphone
```

Terminal B:

```bash
cd "$REPO"
"$REPO/bin/idevicerestore" -e -y "$FW"
```

After restore, continue with ramdisk steps.

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

### 9.2 Add Third-Party Repo (Legacy `.list` style)

Example: add Xplo8E repo for `apt`:

```bash
echo "deb [trusted=yes arch=iphoneos-arm64] https://xplo8e.github.io/sileo/ ./" > /var/jb/etc/apt/sources.list.d/xplo8e.list
apt update
```

---

## 10) Procursus/Jailbreak Stages (A/B/C)

### Stage A: DFU + ramdisk + stage Procursus payload

```bash
cd "$REPO"
source setup_env.sh
./vm_boot_dfu.sh vphone
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
./vm_boot_dfu.sh vphone
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
