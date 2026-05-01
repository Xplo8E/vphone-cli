# vphone host ↔ guest operations

This document is for humans and for **AI assistants** automating or advising on vphone-cli workflows. It records conventions that are easy to get wrong if you treat “SSH to the phone” as one undifferentiated thing.

## What vphone is (one sentence)

**vphone-cli** runs a virtual iPhone on a Mac (Virtualization.framework). You interact with it in **different modes** (DFU + SSH ramdisk vs full iOS boot). **Port forwards, users, and tools differ by mode**—copy-pasting the wrong `ssh`/`scp`/`usbmux` line is a common failure.

---

## DFU + ramdisk vs normal boot — do not conflate them

| Aspect | DFU + SSH ramdisk | Normal GUI boot (`make boot`) |
|--------|-------------------|-------------------------------|
| **Purpose** | Install or modify **on-disk** system volumes before full iOS runs (`make cfw_install`, `cfw_install_dev`, `cfw_install_jb`). | Day-to-day use: apps, SSH for tweaks/debs, VNC, `vphoned` over vsock from the host app. |
| **How the VM is started** | `make boot_dfu` (keep running), then `make ramdisk_send` after `make ramdisk_build`. | `make boot` |
| **Guest SSH service** | SSH server on the **ramdisk** listening on guest **port 22**. | **dropbear** on guest **port 22222** (regular/dev), or **OpenSSH** on **22** after installing `openssh-server` from Sileo (jailbreak variant). |
| **Typical host forward** | `python3 -m pymobiledevice3 usbmux forward 2222 22` | `python3 -m pymobiledevice3 usbmux forward 2222 22222` (dropbear) **or** `… forward 2222 22` (JB + OpenSSH). |
| **Who drives file copy to system volumes** | Repo scripts: `scripts/cfw_install.sh`, `scripts/cfw_install_dev.sh`, `scripts/cfw_install_jb.sh` (they use `sshpass` + `ssh`/`scp` internally). | You (or automation) over the tunnel above. |
| **irecovery** | Used while the device presents as DFU for ramdisk restore flow — **not** a substitute for SSH. | Not the primary path for file transfer during normal use. |

**Rule:** If someone says “SSH into vphone,” ask **which boot mode** and **which forward** (`2222→22` vs `2222→22222` vs `2222→22` after OpenSSH).

Scripts wait on ramdisk SSH with `wait_for_device_ssh_ready` and default `SSH_PORT=2222`, `SSH_USER=root`, password `alpine` — see the top of each `cfw_install*.sh` file.

---

## USB multiplex forwards are not interchangeable

On the **host**, you choose **local port** (conventionally `2222`) and **guest port**:

- **`forward 2222 22`** — Use when the **guest is listening on 22** (ramdisk SSH, or JB with OpenSSH on 22).
- **`forward 2222 22222`** — Use when the **guest is dropbear on 22222** (typical regular/dev after first-boot dropbear key setup per README).

Running the **wrong** forward for the current boot yields connection refused, wrong shell, or “SSH works but it’s the wrong environment.”

**Multiple devices:** `pymobiledevice3 usbmux forward` can target a specific UDID; automation may need `--serial` (see `scripts/setup_machine.sh` for how the project resolves the vphone UDID).

---

## Users and passwords (normal boot, via tunnel to localhost)

| Variant | SSH (typical) | Password |
|---------|----------------|----------|
| Regular / Dev (dropbear) | `ssh -p 2222 root@127.0.0.1` | `alpine` |
| Jailbreak (OpenSSH from Sileo) | `ssh -p 2222 mobile@127.0.0.1` | `alpine` |

First-boot dropbear **host keys** are required or the server closes the session immediately — see README “First Boot”.

---

## Non-interactive SSH (run a remote command, no login shell)

SSH runs a **remote command** when you pass arguments after the destination. The session ends when the command exits — **no** interactive password prompt on the host if you supply the password non-interactively.

### Option A — `sshpass` (same pattern as `cfw_install*.sh`)

Regular / dev (dropbear, `usbmux forward 2222 22222`):

```bash
sshpass -p alpine ssh \
  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -o PreferredAuthentications=password -o ConnectTimeout=30 \
  -p 2222 root@127.0.0.1 -- uname -a
```

Jailbreak + OpenSSH on guest port 22 (`forward 2222 22`), user `mobile`:

```bash
VPHONE_SSH_USER=mobile sshpass -p alpine ssh \
  -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -o PreferredAuthentications=password -o ConnectTimeout=30 \
  -p 2222 mobile@127.0.0.1 -- whoami
```

Use `--` before the remote command so guest-side flags are not parsed as SSH options.

Ad-hoc `sshpass` one-liners do **not** set guest `PATH`; for anything beyond built-ins, mirror the README path or use `scripts/vphone_ssh.sh` instead.

### Option B — repo helper `scripts/vphone_ssh.sh`

Wraps the same options and defaults (`root`, `127.0.0.1`, port `2222`, password `alpine`). It runs **`/iosbinpack64/bin/bash --noprofile --norc -c 'PATH=…; exec …'`** so guest startup files cannot replace `PATH` with dropbear’s short **`/usr/bin:/bin`** (which hides `uname` and often **`sh`**). Override PATH with `VPHONE_REMOTE_PATH` or prefix JB tools with `VPHONE_REMOTE_PREPEND_PATH=/var/jb/usr/sbin:/var/jb/usr/bin`.

```bash
scripts/vphone_ssh.sh uname -a
scripts/vphone_ssh.sh ls /var/root
VPHONE_SSH_USER=mobile scripts/vphone_ssh.sh whoami
```

If a guest program **requires a TTY** (rare for one-shot commands), set `VPHONE_SSH_TTY=1`.

### Option C — SSH keys (no `sshpass`)

Install your public key on the guest (`ssh-copy-id` if available, or append to `authorized_keys`), then use **`ssh -o BatchMode=yes`** so failures are immediate and non-interactive:

```bash
ssh -o BatchMode=yes -p 2222 root@127.0.0.1 -- uname -a
```

### Sending a local script’s stdin to the guest

```bash
sshpass -p alpine ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null \
  -p 2222 root@127.0.0.1 -- bash -s < ./my_guest_script.sh
```

(or use `scripts/vphone_ssh.sh bash -s` with the same redirection.)

---

## File transfer: prefer **rsync** over **scp** (manual / AI workflows)

**Why this matters**

- **`scp`** is easy to misuse under automation (`-P` vs `-p`, recursive flags, quoting, non-atomic multi-file trees). Failures are opaque.
- **`rsync`** gives incremental sync, clearer progress, and stable semantics for directories. For “put this tree on the phone,” **default to rsync**.

**Repo scripts** (`cfw_install*.sh`) intentionally use **`scp`** with `sshpass` for small, deterministic payloads in a **ramdisk** context. That is **not** a recommendation to use `scp` for ad-hoc transfers during **normal boot**, especially large `.deb` trees or repeated syncs.

### Jailbreak variant — rsync with Procursus `rsync` on the guest

Dropbear’s non-login environment may not put `/var/jb/usr/bin` first on `PATH`. Point rsync at the **guest** binary explicitly:

```bash
rsync -avz -e 'ssh -p 2222' \
  '--rsync-path=/var/jb/usr/bin/rsync' \
  ./some.deb \
  root@127.0.0.1:/var/root/debs/
```

Adjust `./some.deb` and the remote path as needed. Ensure the **usbmux** forward matches **OpenSSH on 22** if that is what you use (`forward 2222 22`), and that `-p` matches the **local** side of the tunnel (here `2222`). The main README often shows **`mobile@`** for JB interactive SSH; **`root@`** is still common for pushing files into `/var/root/` when root login is allowed—use whichever matches your guest SSH config.

The repo helper wraps this flow with the same `VPHONE_SSH_*` environment defaults used for command execution:

```bash
scripts/vphone_ssh.sh push ./some.deb /var/root/debs/
scripts/vphone_ssh.sh pull /var/root/debs/some.deb ./downloads/
scripts/vphone_ssh.sh push --rsync-opts --progress -- ./some.deb /var/root/debs/
```

Override the guest rsync binary when needed:

```bash
VPHONE_RSYNC_PATH=/var/jb/usr/bin/rsync scripts/vphone_ssh.sh push ./some.deb /var/root/debs/
```

### Regular / Dev (dropbear on 22222)

Use:

```bash
python3 -m pymobiledevice3 usbmux forward 2222 22222
```

Then rsync over `ssh -p 2222`. The guest may **not** ship a user-visible `rsync` in the same place as Procursus; if `rsync` is missing, use a single-file workflow (`scp` or `sftp`) or install a guest `rsync` you control. **Do not assume** `/var/jb/usr/bin/rsync` exists on non-jailbreak variants.

---

## Not SSH: `vphoned` and the macOS app

- **`vphoned`** — Guest daemon on **vsock** (host app speaks JSON over vsock, port documented in repo as **1337**). This is **not** TCP SSH.
- **`make build` / `make boot`** — Host-side GUI and VM lifecycle; separate from ramdisk install terminals.

---

## Checklist for AI assistants

1. **Mode?** Ramdisk install (`boot_dfu` + `ramdisk_send`) vs `make boot`.
2. **Forward?** `2222→22` (ramdisk or OpenSSH) vs `2222→22222` (dropbear).
3. **User?** `root` vs `mobile` (JB OpenSSH).
4. **Transfers?** Prefer **rsync** for manual multi-file / iterative sync; use explicit `--rsync-path` on JB when `rsync` is not on default PATH.
5. **CFW install?** Read **`scripts/cfw_install.sh`** (and `_dev` / `_jb`) for the **authoritative** ramdisk SSH sequence — do not invent ports or skip `wait_for_device_ssh_ready` semantics.
6. **One-shot remote command?** Use **`scripts/vphone_ssh.sh`** or `sshpass … ssh … -- cmd` (see [Non-interactive SSH](#non-interactive-ssh-run-a-remote-command-no-login-shell)) — do not assume an interactive shell is required.

---

## Pointers

- End-user flow: [README.md](../README.md) (Install Custom Firmware, First Boot, Subsequent Boots).
- Automation reference: `scripts/setup_machine.sh` (iproxy/usbmux, ramdisk SSH wait), `scripts/cfw_install*.sh` (ramdisk `SSH_PORT`, `scp_to` / `ssh_cmd` helpers), `scripts/vphone_ssh.sh` (one-shot guest command over the same style of tunnel).
