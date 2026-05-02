#!/usr/bin/env zsh
set -euo pipefail

SCRIPT_DIR="${0:a:h}"
REPO_DIR="${SCRIPT_DIR:h}"
DEFAULT_LOG="${REPO_DIR}/vm/logs/serial.log"
LOG_PATH="${VPHONE_SERIAL_LOG:-$DEFAULT_LOG}"

usage() {
  cat <<EOF
usage: scripts/vphone_serial.sh <command> [args]

commands:
  path                 Print active serial log path
  tail [args...]       Follow/read serial log with tail (default: -f)
  grep <pattern>       Search serial log with rg/grep
  events               Show high-signal serial events
  since <duration>      Show timestamped lines newer than duration (ex: 30s, 5m, 2h, 1d)
  snapshot [output]    Copy current serial log to a timestamped snapshot
  clear                Truncate the current serial log target

env:
  VPHONE_SERIAL_LOG    Override log path (default: vm/logs/serial.log)
EOF
}

require_log() {
  if [[ ! -e "$LOG_PATH" ]]; then
    echo "[-] serial log not found: $LOG_PATH" >&2
    echo "    Start the VM after rebuilding, or set VPHONE_SERIAL_LOG." >&2
    exit 1
  fi
}

cmd="${1:-tail}"
[[ $# -gt 0 ]] && shift

case "$cmd" in
  path)
    print -r -- "$LOG_PATH"
    ;;

  tail)
    require_log
    if [[ $# -eq 0 ]]; then
      exec tail -f "$LOG_PATH"
    else
      exec tail "$@" "$LOG_PATH"
    fi
    ;;

  grep)
    require_log
    if [[ $# -eq 0 ]]; then
      echo "[-] grep requires a pattern" >&2
      exit 2
    fi
    if command -v rg >/dev/null 2>&1; then
      exec rg --color=always "$@" "$LOG_PATH"
    else
      exec grep -E "$@" "$LOG_PATH"
    fi
    ;;

  events)
    require_log
    pattern='panic|kernel panic|IOUC|sandbox|IOHID|EXC_|crash|watchdog|Jetsam|assertion|fault|Reset|stackshot'
    if command -v rg >/dev/null 2>&1; then
      exec rg -i --color=always "$pattern" "$LOG_PATH"
    else
      exec grep -Ei "$pattern" "$LOG_PATH"
    fi
    ;;

  since)
    require_log
    if [[ $# -ne 1 ]]; then
      echo "[-] since requires one duration: 30s, 5m, 2h, 1d" >&2
      exit 2
    fi
    duration="$1"
    if [[ ! "$duration" =~ '^([0-9]+)([smhd])$' ]]; then
      echo "[-] invalid duration: $duration (use 30s, 5m, 2h, 1d)" >&2
      exit 2
    fi

    python3 - "$LOG_PATH" "$duration" <<'PY'
import re
import sys
from datetime import datetime, timedelta

path, duration = sys.argv[1], sys.argv[2]
match = re.fullmatch(r"(\d+)([smhd])", duration)
if not match:
    raise SystemExit("invalid duration")

value = int(match.group(1))
unit = match.group(2)
delta = {
    "s": timedelta(seconds=value),
    "m": timedelta(minutes=value),
    "h": timedelta(hours=value),
    "d": timedelta(days=value),
}[unit]
cutoff = datetime.now().astimezone() - delta

patterns = [
    re.compile(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) ([+-]\d{4})"),
    re.compile(r"(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})(?:\.\d+)?(?: ?([+-]\d{2}:?\d{2}|Z))?"),
    re.compile(r"\b([A-Z][a-z]{2})\s+(\d{1,2})\s+(\d{2}:\d{2}:\d{2})\b"),
]

def parse_line_time(line):
    m = patterns[0].search(line)
    if m:
        return datetime.strptime(f"{m.group(1)} {m.group(2)}", "%Y-%m-%d %H:%M:%S %z")

    m = patterns[1].search(line)
    if m:
        date_part, time_part, tz_part = m.groups()
        if tz_part == "Z":
            tz_part = "+0000"
        elif tz_part:
            tz_part = tz_part.replace(":", "")
        if tz_part:
            return datetime.strptime(f"{date_part} {time_part} {tz_part}", "%Y-%m-%d %H:%M:%S %z")
        return datetime.strptime(f"{date_part} {time_part}", "%Y-%m-%d %H:%M:%S").astimezone()

    m = patterns[2].search(line)
    if m:
        year = cutoff.year
        parsed = datetime.strptime(f"{year} {m.group(1)} {m.group(2)} {m.group(3)}", "%Y %b %d %H:%M:%S").astimezone()
        if parsed - cutoff > timedelta(days=180):
            parsed = parsed.replace(year=year - 1)
        return parsed

    return None

seen_timestamp = False
printing = False

with open(path, "r", errors="replace") as f:
    for line in f:
        ts = parse_line_time(line)
        if ts is not None:
            seen_timestamp = True
            printing = ts >= cutoff
        if printing:
            sys.stdout.write(line)

if not seen_timestamp:
    sys.stderr.write("[-] no parseable timestamps in serial log; use tail/grep/events instead\n")
    sys.exit(1)
PY
    ;;

  snapshot)
    require_log
    if [[ $# -gt 0 ]]; then
      out="$1"
    else
      ts="$(date +%Y%m%d-%H%M%S)"
      out="${REPO_DIR}/vm/logs/serial-snapshot-${ts}.log"
    fi
    mkdir -p "${out:h}"
    cp "$LOG_PATH" "$out"
    print -r -- "$out"
    ;;

  clear)
    require_log
    : > "$LOG_PATH"
    ;;

  -h|--help|help)
    usage
    ;;

  *)
    echo "[-] unknown command: $cmd" >&2
    usage >&2
    exit 2
    ;;
esac
