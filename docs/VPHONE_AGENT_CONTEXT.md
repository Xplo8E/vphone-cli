# vphone Agent Context

Use this file as the compact context pack for agents working on vphone-cli, vphone SSH workflows, or iOS vulnerability research inside the vphone VM. It is written to prevent common hallucinations: wrong boot mode, wrong SSH port, wrong component origin, and assuming the VM is a normal physical iPhone.

## What vphone-cli Is

`vphone-cli` boots a virtual iPhone using Apple's `Virtualization.framework` PV=3/private APIs and a hybrid restore image built from:

- iPhone IPSW content
- Private Cloud Compute / cloudOS research VM content
- repo-generated patches and custom firmware installation steps

The current working VM is a jailbreak variant normal-boot VM with SSH access and Procursus/Sileo tooling. Heavy static reversing should stay on the Mac when possible; the vphone guest is best used for live app state, process/network inspection, app containers, and debug stubs.

## Source Provenance

The firmware is a hybrid. Do not describe every component as "from iPhone" or every component as "from cloudOS".

```text
vphone restore / boot image
├── iPhone IPSW: iPhone17,3
│   ├── OS image / filesystem
│   ├── SystemVolume metadata and root hash
│   ├── Static trust cache
│   └── Cryptex SystemOS/AppOS userland binaries patched during CFW install
│
├── cloudOS / PCC: vresearch101ap
│   ├── DFU/TSS identity fields
│   ├── AVPBooter / AVPSEPBooter ROM model
│   ├── iBSS
│   ├── iBEC
│   ├── LLB
│   ├── iBoot
│   ├── RestoreRamDisk
│   ├── RestoreTrustCache
│   ├── SPTM
│   └── TXM / RestoreTXM
│
├── cloudOS / PCC: vphone600ap
│   ├── DeviceTree
│   ├── RestoreDeviceTree
│   ├── SEP / RestoreSEP
│   ├── KernelCache
│   ├── RestoreKernelCache
│   └── RecoveryMode
│
└── repo-generated modifications
    ├── boot-chain patches
    ├── TXM patches
    ├── kernelcache patches
    ├── CFW binary/plist patches
    ├── vphoned guest daemon
    ├── iosbinpack/dropbear/trollvnc/rpcserver payloads
    └── jailbreak bootstrap/hooks for JB variant
```

Why this split exists:

- DFU hardware identifies as `vresearch101ap` / BDID `0x90`, so DFU/TSS/SHSH signing must use `vresearch101ap` identity fields.
- Full runtime boot uses `vphone600ap` pieces because its DeviceTree/SEP/kernel path matches the virtual iPhone runtime. Its DeviceTree sets the MKB `dt=1` behavior needed for keybag-less boot.
- The iPhone IPSW supplies the actual iOS filesystem and userland content.

## VM Directory

`vm/` is the active VM bundle unless `VM_DIR` is overridden.

```text
vm/
├── config.plist                  # VM manifest; boot reads this
├── Disk.img                      # sparse virtual disk
├── SEPStorage                    # SEP persistent storage
├── nvram.bin                     # auxiliary/NVRAM storage, generated on boot
├── AVPBooter.vresearch1.bin      # copied from host Virtualization.framework
├── AVPSEPBooter.vresearch1.bin   # copied from host Virtualization.framework
├── udid-prediction.txt           # generated from VZ machineIdentifier
├── *Restore*/                    # prepared hybrid restore tree from fw_prepare
├── Firmware/                     # extracted/merged firmware components
├── cfw_input/                    # CFW install payloads
└── cfw_jb_input/                 # JB-only payloads, when using jailbreak variant
```

Create/switch/backup:

```bash
make vm_new CPU=8 MEMORY=8192 DISK_SIZE=64
make vm_backup NAME=26.3-jb
make vm_list
make vm_switch NAME=26.3-jb
```

Always stop the VM before backup/switch/restore.

## Build and Setup Flow

Manual setup, high level:

```bash
make setup_tools
make build
make vm_new
make fw_prepare
make fw_patch_jb
make boot_dfu
make restore
make boot_dfu
make ramdisk_build
make ramdisk_send
make cfw_install_jb
make boot
```

Common variant targets:

```text
Patchless:    fw_patch_less + boot_less
Regular:      fw_patch      + cfw_install
Development:  fw_patch_dev  + cfw_install_dev
Jailbreak:    fw_patch_jb   + cfw_install_jb
```

Jailbreak finalization happens on first boot through:

```text
/cores/vphone_jb_setup.sh
/var/log/vphone_jb_setup.log
```

## Boot Modes

Do not conflate DFU/ramdisk mode with normal boot.

```text
DFU / ramdisk mode
├── make boot_dfu
├── no GUI window
├── used for restore, ramdisk_send, cfw_install*
├── guest SSH ramdisk listens on guest port 22
└── usual host forward: python3 -m pymobiledevice3 usbmux forward 2222 22

Normal boot
├── make boot
├── boots full iOS/SpringBoard
├── vphoned control channel over vsock, not TCP
├── regular/dev dropbear listens on guest port 22222
├── JB OpenSSH commonly listens on guest port 22 if installed
└── host forward depends on guest SSH service:
    ├── dropbear: python3 -m pymobiledevice3 usbmux forward 2222 22222
    └── JB OpenSSH: python3 -m pymobiledevice3 usbmux forward 2222 22
```

The current personal workflow is normal boot, JB variant, SSH over local host port `2222`.

## Host/Guest Channels

```text
host macOS
├── vphone-cli app process
│   ├── Virtualization.framework VM
│   ├── VM window/menus when GUI mode is used
│   └── vsock client to vphoned
│
├── pymobiledevice3 usbmux forward
│   └── localhost:2222 -> guest SSH port
│
└── scripts/vphone_ssh.sh
    ├── one-shot SSH commands
    ├── heredoc/multiline command mode
    └── rsync push/pull wrapper

guest iOS
├── full iOS runtime
├── jailbreak Procursus tree at /var/jb
├── iosbinpack64 at /iosbinpack64
├── vphoned daemon over vsock
├── SSH server
└── app bundle/data containers under /private/var/...
```

`vphoned` is not SSH. It is a guest daemon reached by the host app over vsock.

## SSH Wrapper

Use `scripts/vphone_ssh.sh` instead of raw SSH for automation. It sets the right PATH and quoting for normal-boot one-shot commands.

```bash
scripts/vphone_ssh.sh whoami
scripts/vphone_ssh.sh sh -c 'cd /var/root && ls -la'
scripts/vphone_ssh.sh bash -c '
set -e
cd /var/root
pwd
ls -la
'
```

Preferred multiline form:

```bash
scripts/vphone_ssh.sh <<'EOF'
set -e
cd /var/root
pwd
for f in *; do
  echo "item:$f"
done
EOF
```

Wrapper defaults:

```text
VPHONE_SSH_HOST=127.0.0.1
VPHONE_SSH_PORT=2222
VPHONE_SSH_USER=root
VPHONE_SSH_PASS=alpine
VPHONE_RSYNC_PATH=/var/jb/usr/bin/rsync
```

The wrapper remote PATH prioritizes:

```text
/var/jb/usr/local/sbin
/var/jb/usr/local/bin
/var/jb/usr/sbin
/var/jb/usr/bin
/var/jb/usr/libexec
/var/jb/sbin
/var/jb/bin
/iosbinpack64/...
```

## File Transfer

Normal-boot `scp`/`sftp` are unreliable in this setup. Use rsync through the wrapper.

```bash
scripts/vphone_ssh.sh push ./local.deb /var/root/debs/
scripts/vphone_ssh.sh pull /var/root/debs/local.deb ./downloads/
scripts/vphone_ssh.sh push --rsync-opts --progress -- ./local.deb /var/root/debs/
```

Multiple files and spaces are supported:

```bash
scripts/vphone_ssh.sh push "./one space.txt" ./two.txt /var/root/tmp/
scripts/vphone_ssh.sh pull "/var/root/tmp/one space.txt" /var/root/tmp/two.txt ./out/
```

## Installed Guest Research Tools

Verified available in the current JB guest:

```text
Package / network:
  apt, apt-get, apt-cache, dpkg, dpkg-query
  curl, wget, rsync

Process / network:
  ps, launchctl, lsof, netstat, tcpdump, nc, socat

Plist / data:
  PlistBuddy, plistutil, plutil, sqlite3, jq

Binary / RE quick checks:
  file, ldid, jtool, jtool2
  otool, nm, strings
  objdump -> llvm-objdump-16
  readelf -> llvm-readelf-16
  r2, rabin2, rasm2, rax2

Debug:
  debugserver
  lldb is installed, but prefer Mac-side LLDB for heavier sessions

Shell / utility:
  bash, sh, zsh, awk/gawk, grep, sed, find, xargs, tar, gzip, zip, unzip, openssl
```

Intentionally not needed for this VM baseline:

```text
nmap
class-dump
cycript
```

## iOS App Research Paths

Bundle containers:

```text
/private/var/containers/Bundle/Application/<UUID>/<App>.app
```

Data containers:

```text
/private/var/mobile/Containers/Data/Application/<UUID>
```

Container metadata:

```text
/private/var/mobile/Containers/Data/Application/<UUID>/.com.apple.mobile_container_manager.metadata.plist
```

Map data containers to bundle IDs:

```bash
scripts/vphone_ssh.sh <<'EOF'
find /private/var/mobile/Containers/Data/Application -maxdepth 1 -mindepth 1 -type d | while read -r d; do
  meta="$d/.com.apple.mobile_container_manager.metadata.plist"
  bid="?"
  [ -f "$meta" ] && bid="$(PlistBuddy -c 'Print :MCMMetadataIdentifier' "$meta" 2>/dev/null || true)"
  printf '%s\t%s\n' "$bid" "$d"
done
EOF
```

List app bundles:

```bash
scripts/vphone_ssh.sh find /private/var/containers/Bundle/Application -maxdepth 2 -name '*.app'
```

Inspect app metadata:

```bash
scripts/vphone_ssh.sh PlistBuddy -c Print /path/to/App.app/Info.plist
scripts/vphone_ssh.sh plutil -p /path/to/App.app/Info.plist
```

Inspect binary:

```bash
scripts/vphone_ssh.sh file /path/to/App.app/AppBinary
scripts/vphone_ssh.sh ldid -e /path/to/App.app/AppBinary
scripts/vphone_ssh.sh jtool2 -l /path/to/App.app/AppBinary
scripts/vphone_ssh.sh otool -L /path/to/App.app/AppBinary
scripts/vphone_ssh.sh nm /path/to/App.app/AppBinary
scripts/vphone_ssh.sh strings /path/to/App.app/AppBinary
scripts/vphone_ssh.sh rabin2 -I /path/to/App.app/AppBinary
```

For deep static work, pull the app to macOS and use IDA/Ghidra/Binja there:

```bash
scripts/vphone_ssh.sh pull /private/var/containers/Bundle/Application/<UUID>/<App>.app ./loot/
```

## Runtime Commands

Process list:

```bash
scripts/vphone_ssh.sh ps ax
```

Open sockets/files:

```bash
scripts/vphone_ssh.sh lsof -i
scripts/vphone_ssh.sh netstat -an
```

Packet capture:

```bash
scripts/vphone_ssh.sh tcpdump -i any -n
```

Debugserver skeleton:

```bash
scripts/vphone_ssh.sh debugserver 127.0.0.1:1234 -a <ProcessNameOrPID>
```

Then forward/connect from host as appropriate. Prefer Mac-side LLDB for UI and symbols.

## CFW/JB Installed Runtime Components

Regular CFW installs:

```text
Cryptex SystemOS + AppOS
GPU driver bundle
iosbinpack64
vphoned
LaunchDaemons for bash/dropbear/trollvnc/rpcserver_ios/vphoned
```

JB variant adds:

```text
Procursus bootstrap
Sileo / apt environment
BaseBin hooks under /cores
launchd hook dylib alias /b
TweakLoader.dylib at /var/jb/usr/lib/TweakLoader.dylib
TrollStore-related first-boot setup
```

Monitor JB finalization:

```bash
scripts/vphone_ssh.sh tail -f /var/log/vphone_jb_setup.log
```

## Cleanup Policy

Do not delete stock iOS app bundles blindly. In this VM, large app bundles are mostly Apple stock apps such as `Bridge`, `FindMy`, `Maps`, and `Music`.

Safe cleanup targets:

```bash
scripts/vphone_ssh.sh <<'EOF'
find /private/var/mobile/Library/Caches -mindepth 1 -maxdepth 1 -exec rm -rf {} + 2>/dev/null || true
find /private/var/mobile/Containers/Data/Application -path '*/Library/Caches/*' -mindepth 1 -maxdepth 6 -exec rm -rf {} + 2>/dev/null || true
find /private/var/mobile/Library/Logs -mindepth 1 -maxdepth 2 -exec rm -rf {} + 2>/dev/null || true
find /private/var/log -type f \( -name '*.log' -o -name '*.gz' -o -name '*.old' \) -delete 2>/dev/null || true
rm -rf /private/var/tmp/* /tmp/* 2>/dev/null || true
apt-get clean >/dev/null 2>&1 || true
EOF
```

## Common Agent Mistakes To Avoid

- Do not use DFU SSH assumptions for normal boot.
- Do not assume guest SSH is always port 22. Normal dropbear uses guest `22222`; JB OpenSSH commonly uses guest `22`.
- Do not use raw `scp`/`sftp` as the default transfer path. Use wrapper rsync.
- Do not claim a component is iPhone-origin when it is PCC/cloudOS-origin.
- Do not claim a component is cloudOS-origin when it is iPhone filesystem/userland.
- Do not report vulnerabilities from reasoning alone. Keep finding state as `hypothesis`, `candidate`, or `confirmed`.
- Do not delete system app bundles to save space unless specifically requested and backed up.
- Do not assume Frida state/version. This context intentionally does not rely on Frida.

