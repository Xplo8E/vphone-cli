# vphone Personal Research Baseline

This records the current personal vphone SSH and on-device research setup.

## SSH Wrapper

Use `scripts/vphone_ssh.sh` for normal-boot guest SSH through the active usbmux forward.

```bash
scripts/vphone_ssh.sh whoami
scripts/vphone_ssh.sh sh -c 'cd /var/root && ls -la'
scripts/vphone_ssh.sh <<'EOF'
set -e
cd /var/root
pwd
EOF
```

File transfer uses rsync because normal-boot `scp`/`sftp` are unreliable in this VM:

```bash
scripts/vphone_ssh.sh push ./file.deb /var/root/debs/
scripts/vphone_ssh.sh pull /var/root/debs/file.deb ./downloads/
scripts/vphone_ssh.sh push --rsync-opts --progress -- ./file.deb /var/root/debs/
```

Wrapper defaults:

- SSH host: `127.0.0.1`
- SSH port: `2222`
- SSH user: `root`
- SSH password: `alpine`
- Remote rsync: `/var/jb/usr/bin/rsync`
- Remote PATH prioritizes Procursus `/var/jb` paths, then iosbinpack.

## Installed Device-Side Tools

Keep device-side tooling lean. Heavy static analysis stays on macOS; the VM keeps tools useful for live state, app containers, quick binary inspection, and debug stubs.

Confirmed installed:

```text
curl, wget
tcpdump, lsof, nc, socat
sqlite3
file
python3
PlistBuddy, plistutil, plutil
jtool2
otool, nm, strings
objdump -> llvm-objdump-16
readelf -> llvm-readelf-16
radare2: r2, rabin2, rasm2, rax2
debugserver
jq, awk
zip, unzip
openssl
rsync
ldid
```

Intentionally not installed / not needed here:

```text
nmap
class-dump
cycript
```

Use macOS for heavier workflows like full disassembly, class recovery, IDA/Ghidra/Binja work, and larger recursive grep/extraction jobs. Use the VM for live app container state, network capture, process/file inspection, and launching debugserver.

## Useful Commands

App bundle inventory:

```bash
scripts/vphone_ssh.sh find /private/var/containers/Bundle/Application -maxdepth 2 -name '*.app'
```

App data inventory:

```bash
scripts/vphone_ssh.sh find /private/var/mobile/Containers/Data/Application -maxdepth 1 -mindepth 1 -type d
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

Quick binary checks:

```bash
scripts/vphone_ssh.sh file /path/to/App.app/AppBinary
scripts/vphone_ssh.sh ldid -e /path/to/App.app/AppBinary
scripts/vphone_ssh.sh jtool2 -l /path/to/App.app/AppBinary
scripts/vphone_ssh.sh otool -L /path/to/App.app/AppBinary
scripts/vphone_ssh.sh strings /path/to/App.app/AppBinary
```

Network/process state:

```bash
scripts/vphone_ssh.sh ps ax
scripts/vphone_ssh.sh lsof -i
scripts/vphone_ssh.sh netstat -an
scripts/vphone_ssh.sh tcpdump -i any -n
```

## Cleanup Policy

Do not delete stock iOS app bundles blindly. Current largest app bundles are stock Apple apps (`Bridge`, `FindMy`, `Maps`, `Music`), and removing them may break assumptions in the VM image.

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

Last cleanup result:

```text
/private/var/mobile/Library/Caches: 216552 KB -> 80 KB
logs: 11940 KB -> 5604 KB
apt archives: cleaned
```

