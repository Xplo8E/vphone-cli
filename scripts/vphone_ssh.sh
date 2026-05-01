#!/usr/bin/env bash
# vphone_ssh.sh — Run a single non-interactive command on the guest over SSH (password auth).
#
# Requires: sshpass (make setup_tools), usbmux forward already running (see README).
#
# Usage:
#   scripts/vphone_ssh.sh uname -a
#   scripts/vphone_ssh.sh ls /var/root
#   scripts/vphone_ssh.sh sh -c 'cd /var/root && ls -la'
#   scripts/vphone_ssh.sh < ./guest_script.sh
#   scripts/vphone_ssh.sh push ./file.deb /var/root/debs/
#   scripts/vphone_ssh.sh pull /var/root/test.sh ./downloads/
#   scripts/vphone_ssh.sh push --rsync-opts --progress -- ./file.deb /var/root/debs/
#
# Environment (defaults match README / cfw_install ramdisk-style tunnel on localhost):
#   VPHONE_SSH_PORT   default 2222
#   VPHONE_SSH_USER   default root  (use mobile for JB OpenSSH if needed)
#   VPHONE_SSH_HOST   default 127.0.0.1
#   VPHONE_SSH_PASS   default alpine
#   VPHONE_REMOTE_PATH  guest PATH for the command (default: README dropbear/iosbinpack layout)
#   VPHONE_REMOTE_PREPEND_PATH  optional prefix (e.g. /var/jb/usr/sbin:/var/jb/usr/bin:)
#   VPHONE_REMOTE_SHELL  default /iosbinpack64/bin/bash — must be absolute (no PATH yet).
#     Normal vphone guest has no /bin/sh; ramdisk may use e.g. VPHONE_REMOTE_SHELL=/bin/sh.
#     Bash gets --noprofile --norc so guest rc files cannot replace PATH (dropbear often sets
#     PATH=/usr/bin:/bin before your command, which hides iosbinpack tools like uname).
#   VPHONE_RSYNC_PATH  guest rsync path for push/pull (default: /var/jb/usr/bin/rsync)
#
# Optional:
#   VPHONE_SSH_TTY=1  pass -t to ssh (allocate pseudo-tty for sudo/password prompts on guest)
#   VPHONE_SSH_STDIN=1  keep stdin open for commands like `bash -s < script.sh`
set -euo pipefail

SSH_PORT="${VPHONE_SSH_PORT:-2222}"
SSH_USER="${VPHONE_SSH_USER:-root}"
SSH_HOST="${VPHONE_SSH_HOST:-127.0.0.1}"
SSH_PASS="${VPHONE_SSH_PASS:-alpine}"

# Include Procursus first for jailbreak variants; nonexistent PATH entries are harmless on regular/dev.
_DEFAULT_REMOTE_PATH='/var/jb/usr/local/sbin:/var/jb/usr/local/bin:/var/jb/usr/sbin:/var/jb/usr/bin:/var/jb/usr/libexec:/var/jb/sbin:/var/jb/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/bin/X11:/usr/games:/iosbinpack64/usr/local/sbin:/iosbinpack64/usr/local/bin:/iosbinpack64/usr/sbin:/iosbinpack64/usr/bin:/iosbinpack64/sbin:/iosbinpack64/bin'
REMOTE_PATH="${VPHONE_REMOTE_PATH:-$_DEFAULT_REMOTE_PATH}"
if [[ -n "${VPHONE_REMOTE_PREPEND_PATH:-}" ]]; then
    REMOTE_PATH="${VPHONE_REMOTE_PREPEND_PATH%:}:${REMOTE_PATH}"
fi

SSH_OPTS=(
    -o StrictHostKeyChecking=no
    -o UserKnownHostsFile=/dev/null
    -o PreferredAuthentications=password
    -o ConnectTimeout=30
    -o LogLevel=ERROR
)

script_name="$(basename "$0")"

stdin_is_tty=0
[[ -t 0 ]] && stdin_is_tty=1

usage() {
    echo "usage: ${script_name} <remote-command> [args...]  OR  ${script_name} < guest_script.sh" >&2
    echo "       ${script_name} push [--rsync-opts <options...> --] <local...> <remote-path>" >&2
    echo "       ${script_name} pull [--rsync-opts <options...> --] <remote...> <local-path>" >&2
    echo "example: ${script_name} uname -a" >&2
    echo "example: ${script_name} sh -c 'cd /var/root && ls -la'" >&2
    echo "example: ${script_name} < ./guest_script.sh" >&2
    echo "example: ${script_name} push ./file.deb /var/root/debs/" >&2
    echo "example: ${script_name} pull /var/root/test.sh ./downloads/" >&2
    echo "example: ${script_name} push --rsync-opts --progress -- ./file.deb /var/root/debs/" >&2
    echo "env: VPHONE_SSH_USER=mobile VPHONE_SSH_PASS=alpine ${script_name} whoami" >&2
}

if (($# == 0)) && ((stdin_is_tty)); then
    usage
    exit 1
fi

SSHPASS_BIN="$(command -v sshpass || true)"
[[ -x "$SSHPASS_BIN" ]] || {
    echo "[-] sshpass not found. Run: make setup_tools" >&2
    exit 1
}

quote_remote_arg() {
    printf "%q" "$1"
}

if (($# > 0)) && [[ "$1" == "push" || "$1" == "pull" ]]; then
    mode="$1"
    shift
    if (($# < 2)); then
        usage
        exit 1
    fi

    RSYNC_BIN="$(command -v rsync || true)"
    [[ -x "$RSYNC_BIN" ]] || {
        echo "[-] rsync not found. Install rsync on the host." >&2
        exit 1
    }

    passthrough_rsync_args=()
    if [[ "${1:-}" == "--rsync-opts" ]]; then
        shift
        while (($# > 0)); do
            [[ "$1" == "--" ]] && {
                shift
                break
            }
            passthrough_rsync_args+=("$1")
            shift
        done
        if (($# < 2)); then
            usage
            exit 1
        fi
    elif [[ "${1:-}" == "--" ]]; then
        shift
    fi

    RSYNC_PATH="${VPHONE_RSYNC_PATH:-/var/jb/usr/bin/rsync}"
    remote_prefix="${SSH_USER}@${SSH_HOST}:"
    rsync_ssh="ssh -p ${SSH_PORT} -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o PreferredAuthentications=password -o ConnectTimeout=30 -o LogLevel=ERROR"
    rsync_args=(-avz -e "$rsync_ssh" "--rsync-path=$RSYNC_PATH")

    if [[ "${VPHONE_RSYNC_DELETE:-}" == 1 ]]; then
        rsync_args+=(--delete)
    fi
    ((${#passthrough_rsync_args[@]})) && rsync_args+=("${passthrough_rsync_args[@]}")

    if [[ "$mode" == "push" ]]; then
        remote_path="${@: -1}"
        local_count=$(($# - 1))
        local_paths=("${@:1:$local_count}")
        exec "$SSHPASS_BIN" -p "$SSH_PASS" "$RSYNC_BIN" "${rsync_args[@]}" \
            "${local_paths[@]}" "${remote_prefix}${remote_path}"
    else
        local_path="${@: -1}"
        remote_count=$(($# - 1))
        remote_paths=("${@:1:$remote_count}")
        rsync_sources=()
        for remote_path in "${remote_paths[@]}"; do
            rsync_sources+=("${remote_prefix}${remote_path}")
        done
        exec "$SSHPASS_BIN" -p "$SSH_PASS" "$RSYNC_BIN" "${rsync_args[@]}" \
            "${rsync_sources[@]}" "$local_path"
    fi
fi

ssh_tty=()
[[ "${VPHONE_SSH_TTY:-}" == 1 ]] && ssh_tty=(-t)

ssh_stdin=()
if ((stdin_is_tty)) && [[ "${VPHONE_SSH_STDIN:-}" != 1 ]]; then
    ssh_stdin=(-n)
fi

REMOTE_SHELL="${VPHONE_REMOTE_SHELL:-/iosbinpack64/bin/bash}"

# PATH=…; … — set PATH inside the clean shell. --noprofile --norc
# stops bash from sourcing rc that overwrites PATH; dropbear/login often pre-set PATH=/usr/bin:/bin.
shell_argv=("$REMOTE_SHELL")
[[ "$(basename "$REMOTE_SHELL")" == bash ]] && shell_argv+=(--noprofile --norc)

# One remote -c string: OpenSSH sends the channel "exec" as a single line; multiple argv after
# the host were being parsed by the guest login shell, breaking $1/$@ and breaking /bin/sh.
inner="PATH=$(quote_remote_arg "$REMOTE_PATH");"
if (($# == 0)); then
    for a in "${shell_argv[@]}"; do
        inner+=" $(quote_remote_arg "$a")"
    done
    inner+=" -s"
else
    for a in "$@"; do
        inner+=" $(quote_remote_arg "$a")"
    done
fi

remote_command=""
for a in "${shell_argv[@]}"; do
    remote_command+=" $(quote_remote_arg "$a")"
done
remote_command+=" -c $(quote_remote_arg "$inner")"
remote_command="${remote_command# }"

ssh_cmd=("$SSHPASS_BIN" -p "$SSH_PASS" ssh "${SSH_OPTS[@]}")
((${#ssh_tty[@]})) && ssh_cmd+=("${ssh_tty[@]}")
((${#ssh_stdin[@]})) && ssh_cmd+=("${ssh_stdin[@]}")
ssh_cmd+=(-p "$SSH_PORT" "$SSH_USER@$SSH_HOST" "$remote_command")

exec "${ssh_cmd[@]}"
