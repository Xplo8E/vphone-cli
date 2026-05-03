#!/usr/bin/env python3
"""
Generate docs/ios_26_4_security_mac_diff_vphone/FULL_COMPONENT_MAP.md

Cross-checks every Apple security bulletin *component* (iOS 26.4 / HT213792)
against:
  - dyld_shared_cache from a **stock iPhone** IPSW-derived cache (ipsw dyld info -l)
  - **Stock iPhone restore kernelcache** kext IDs — `kernelcache.release.iphone17` from IPSW
    (ipsw kernel dec + ipsw kernel kexts -j). **Not** a vphone-patched / research kernelcache.
  - macOS UniversalMac ipsw-diff kext markdown intersecting vphone **bundle-ID scope** (KEXTS/*.md)

Paths default to Vinay's local extract layout; override with env or CLI flags.

  IPHONE_DSC=/path/to/dyld_shared_cache_arm64e \\
  IPHONE_KERNELCACHE=/path/to/kernelcache.release.iphone17 \\
  python3 scripts/generate_ios_security_component_map.py

(`VPHONE_DSC` / `VPHONE_KERNELCACHE` are still read as fallbacks but refer to **iPhone IPSW**
artifacts — not “vphone kernelcache” in the research/CFW sense.)
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path


# One row per bulletin *heading* (merged duplicate headings like Kernel / WebKit).
COMPONENTS: list[dict] = [
    {
        "title": "802.1X",
        "cves": ["CVE-2026-28865"],
        "dsc": ["EAP8021X", "IO80211"],
        "kc": ["IO80211", "80211"],
        "diff_extra": [],
        "notes": "WLAN/EAP stack; mostly DSC + Wi-Fi kexts.",
    },
    {
        "title": "Accounts",
        "cves": ["CVE-2026-28877"],
        "dsc": ["Accounts.framework/Accounts"],
        "kc": [],
        "diff_extra": [],
        "notes": "Userspace Accounts.framework.",
    },
    {
        "title": "App Protection",
        "cves": ["CVE-2026-28895"],
        "dsc": ["AppProtection.framework", "LocalAuthentication.framework"],
        "kc": ["AppleSEP", "MobileFileIntegrity", "EffaceableStorage"],
        "diff_extra": [
            "com.apple.driver.AppleMobileFileIntegrity",
            "com.apple.driver.AppleSEPKeyStore",
            "com.apple.driver.AppleSEPManager",
        ],
        "notes": "Stolen Device Protection / biometrics gating; DSC + SEP/MFII kexts.",
    },
    {
        "title": "Audio",
        "cves": ["CVE-2026-28879", "CVE-2026-28822"],
        "dsc": [
            "CoreAudio.framework",
            "AudioToolbox.framework",
            "AVFAudio.framework",
        ],
        "kc": ["Audio", "ARMIISAudio", "ExclavesAudio", "EmbeddedAudio"],
        "diff_extra": [
            "com.apple.driver.AppleEmbeddedAudioLibs",
            "com.apple.driver.ExclavesAudioKext",
            "com.apple.iokit.AppleARMIISAudio",
        ],
        "notes": "Two CVEs under same heading.",
    },
    {
        "title": "Baseband",
        "cves": ["CVE-2026-28874", "CVE-2026-28875"],
        "dsc": [],  # cellular firmware stack is mostly out-of-band vs generic DSC names
        "kc": ["Baseband"],
        "diff_extra": [],
        "notes": "Baseband CVEs; presence checked via Baseband* kext IDs (DSC rarely names modem blobs).",
    },
    {
        "title": "Calling Framework",
        "cves": ["CVE-2026-28894"],
        "dsc": ["TelephonyUtilities.framework"],
        "kc": ["Telephony", "FaceTime", "CallKit"],
        "diff_extra": [],
        "notes": "VoLTE/VoIP calling paths.",
    },
    {
        "title": "Clipboard",
        "cves": ["CVE-2026-28866"],
        "dsc": ["UIKit.framework/UIKit"],
        "kc": [],
        "diff_extra": [],
        "notes": "Pasteboard typically UIKit / SpringBoard services (UIKit as coarse anchor).",
    },
    {
        "title": "CoreMedia",
        "cves": ["CVE-2026-20690"],
        "dsc": ["CoreMedia.framework/CoreMedia"],
        "kc": [],
        "diff_extra": [],
        "notes": "",
    },
    {
        "title": "CoreUtils",
        "cves": ["CVE-2026-28886"],
        "dsc": ["CoreUtils.framework/CoreUtils"],
        "kc": [],
        "diff_extra": [],
        "notes": "",
    },
    {
        "title": "Crash Reporter",
        "cves": ["CVE-2026-28878"],
        "dsc": [
            "CrashReporter.framework/CrashReporter",
            "CrashReporterSupport.framework",
            "LoggingSupport.framework",
        ],
        "kc": [],
        "diff_extra": [],
        "notes": "",
    },
    {
        "title": "curl",
        "cves": ["CVE-2025-14524"],
        "dsc": ["libcurl.dylib", "curl.framework", "CFNetwork.framework"],
        "kc": [],
        "diff_extra": [],
        "notes": "Third-party curl CVE folded into Apple release.",
    },
    {
        "title": "DeviceLink",
        "cves": ["CVE-2026-28876"],
        "dsc": ["MobileDeviceLink.framework"],
        "kc": [],
        "diff_extra": [],
        "notes": "Apple lists “DeviceLink”; on-device image shows MobileDeviceLink.",
    },
    {
        "title": "GeoServices",
        "cves": ["CVE-2026-28870"],
        "dsc": ["GeoServices.framework", "GeoServicesCore.framework"],
        "kc": [],
        "diff_extra": [],
        "notes": "",
    },
    {
        "title": "iCloud",
        "cves": ["CVE-2026-28880", "CVE-2026-28833"],
        "dsc": ["CloudKit.framework", "CloudServices.framework"],
        "kc": [],
        "diff_extra": [],
        "notes": "",
    },
    {
        "title": "ImageIO",
        "cves": ["CVE-2025-64505"],
        "dsc": ["ImageIO.framework/ImageIO"],
        "kc": [],
        "diff_extra": [],
        "notes": "Upstream OSS CVE.",
    },
    {
        "title": "Kernel",
        "cves": [
            "CVE-2026-28868",
            "CVE-2026-28867",
            "CVE-2026-20698",
            "CVE-2026-20687",
        ],
        "dsc": [],
        "kc": ["__ALL__"],  # sentinel: entire KC
        "diff_extra": ["com.apple.kernel"],
        "notes": "XNU + all embedded kexts live in kernelcache (not DSC dylibs).",
    },
    {
        "title": "libxpc",
        "cves": ["CVE-2026-28882"],
        "dsc": ["/usr/lib/system/libxpc.dylib", "libxpc_datastores.dylib"],
        "kc": [],
        "diff_extra": [],
        "notes": "Userspace libxpc; no standalone kext bundle ID.",
    },
    {
        "title": "Mail",
        "cves": ["CVE-2026-20692"],
        "dsc": ["Email.framework/Email", "MailKit.framework", "Message.framework"],
        "kc": [],
        "diff_extra": [],
        "notes": "",
    },
    {
        "title": "Printing",
        "cves": ["CVE-2026-20688"],
        "dsc": ["PrintKit.framework", "PrintKitUI.framework"],
        "kc": [],
        "diff_extra": [],
        "notes": "",
    },
    {
        "title": "Sandbox Profiles",
        "cves": ["CVE-2026-28863"],
        "dsc": [],
        "kc": ["sandbox"],
        "diff_extra": ["com.apple.security.sandbox"],
        "notes": "Profile database + sandbox.kext.",
    },
    {
        "title": "Security",
        "cves": ["CVE-2026-28864"],
        "dsc": ["Security.framework/Security"],
        "kc": ["AppleMobileFileIntegrity", "SEPKeyStore", "SEPManager", "corecrypto"],
        "diff_extra": [
            "com.apple.driver.AppleMobileFileIntegrity",
            "com.apple.driver.AppleSEPKeyStore",
            "com.apple.driver.AppleSEPManager",
            "com.apple.kec.corecrypto",
            "com.apple.security.AppleImage4",
        ],
        "notes": "Keychain / permission checks span Security.framework + MFII/SEP/corecrypto kexts.",
    },
    {
        "title": "Siri",
        "cves": ["CVE-2026-28856"],
        "dsc": ["SiriInference.framework", "AssistantServices.framework"],
        "kc": [],
        "diff_extra": [],
        "notes": "",
    },
    {
        "title": "Telephony",
        "cves": ["CVE-2026-28858"],
        "dsc": ["CoreTelephony.framework/CoreTelephony"],
        "kc": ["Telephony", "Baseband"],
        "diff_extra": [],
        "notes": "Impact text mentions kernel memory; stack spans CoreTelephony + baseband kexts.",
    },
    {
        "title": "UIFoundation",
        "cves": ["CVE-2026-28852"],
        "dsc": ["UIFoundation.framework/UIFoundation"],
        "kc": [],
        "diff_extra": [],
        "notes": "",
    },
    {
        "title": "WebKit",
        "cves": [
            "CVE-2026-20665",
            "CVE-2026-20643",
            "CVE-2026-28871",
            "CVE-2026-20664",
            "CVE-2026-28857",
            "CVE-2026-28861",
            "CVE-2026-28859",
        ],
        "dsc": [
            "WebKit.framework/WebKit",
            "JavaScriptCore.framework/JavaScriptCore",
            "WebKitLegacy.framework",
        ],
        "kc": [],
        "diff_extra": [],
        "notes": "Multiple CVE blocks merged under one heading.",
    },
    {
        "title": "WebKit Sandboxing",
        "cves": ["CVE-2026-20691"],
        "dsc": ["WebKit.framework/WebKit", "/usr/lib/system/libxpc.dylib"],
        "kc": ["sandbox"],
        "diff_extra": ["com.apple.security.sandbox"],
        "notes": "Distinct from “Sandbox Profiles”; likely WebKit multi-process + sandbox/XPC.",
    },
]


def run(cmd: list[str]) -> str:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write(p.stderr or p.stdout or "")
        raise RuntimeError(f"command failed ({p.returncode}): {' '.join(cmd)}")
    return p.stdout


def decompress_kernelcache(src: Path, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    run(["ipsw", "kernel", "dec", str(src), "-o", str(out_dir)])
    # ipsw writes nested path under out_dir
    dec = list(out_dir.glob("*.decompressed"))
    if not dec:
        raise FileNotFoundError(f"no .decompressed under {out_dir}")
    return dec[0]


def load_dylib_lines(dsc: Path) -> list[str]:
    raw = run(["ipsw", "dyld", "info", "-l", str(dsc), "--no-color"])
    return raw.splitlines()


def load_kext_ids(kc_dec: Path) -> list[str]:
    raw = run(["ipsw", "kernel", "kexts", "-j", str(kc_dec)])
    data = json.loads(raw)
    return [e["id"] for e in data]


def parse_vphone_scope(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return set(re.findall(r"`(com\.apple\.[^`]+)`", text))


def diff_bundle_files(kexts_dir: Path) -> set[str]:
    return {p.stem for p in kexts_dir.glob("*.md")}


def match_lines(lines: list[str], substrings: list[str]) -> list[str]:
    hits: list[str] = []
    for ln in lines:
        for s in substrings:
            if s.lower() in ln.lower():
                hits.append(ln.strip())
                break
    return hits


def match_kexts(ids: list[str], patterns: list[str]) -> list[str]:
    if patterns == ["__ALL__"]:
        return ids
    hits: list[str] = []
    for kid in ids:
        kl = kid.lower()
        for p in patterns:
            if p.lower() in kl:
                hits.append(kid)
                break
    return sorted(set(hits))


def format_short(lines: list[str], limit: int = 4) -> str:
    if not lines:
        return "—"
    out = []
    for ln in lines[:limit]:
        # strip leading "NNN: (ver)   " style prefix if present
        m = re.search(r"/System/|/usr/", ln)
        out.append(ln[m.start() :] if m else ln)
    extra = len(lines) - limit
    tail = f" (+{extra} more)" if extra > 0 else ""
    return "<br>".join(out) + tail


def format_kext(ids: list[str], limit: int = 6) -> str:
    if not ids:
        return "—"
    if len(ids) > 100:  # Kernel/__ALL__
        return f"stock **iPhone** restore KC: **{len(ids)}** kext payloads (+ XNU)"
    head = ids[:limit]
    extra = len(ids) - limit
    tail = f"<br>(+{extra} more)" if extra > 0 else ""
    return "<br>".join(f"`{x}`" for x in head) + tail


def diff_column(
    title: str,
    kc_hits: list[str],
    diff_extra: list[str],
    scope: set[str],
    diff_files: set[str],
) -> str:
    # Kernel row matches every kext ID (__ALL__); do not expand to "every kext with a diff in scope".
    if title == "Kernel":
        bundles = set(diff_extra)
    else:
        bundles = set(diff_extra)
        for kid in kc_hits:
            if kid in scope and kid in diff_files:
                bundles.add(kid)
    if not bundles:
        return "— *(no linked UniversalMac kext diff in this corpus for vphone bundle-ID scope)*"
    links = []
    for b in sorted(bundles):
        if b not in diff_files:
            links.append(f"`{b}` *(listed but missing `KEXTS/{b}.md`)*")
        else:
            links.append(f"[`{b}`](../KEXTS/{b}.md)")
    return "<br>".join(links)


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    default_dsc = Path(
        os.environ.get("IPHONE_DSC")
        or os.environ.get("VPHONE_DSC")
        or "/Users/vinay/ipsw/mac_ipsw/ios_26_3_1_dsc_arm64e/23D8133__iPhone17,3/dyld_shared_cache_arm64e",
    )
    default_kc = Path(
        os.environ.get("IPHONE_KERNELCACHE")
        or os.environ.get("VPHONE_KERNELCACHE")
        or "/Users/vinay/ipsw/mac_ipsw/ios_26_3_1_extract/iPhone17,3_26.3.1_23D8133_Restore/kernelcache.release.iphone17",
    )

    ap = argparse.ArgumentParser()
    ap.add_argument("--dsc", type=Path, default=default_dsc)
    ap.add_argument("--kernelcache", type=Path, default=default_kc)
    ap.add_argument(
        "--out",
        type=Path,
        default=repo / "docs/ios_26_4_security_mac_diff_vphone/FULL_COMPONENT_MAP.md",
    )
    args = ap.parse_args()

    scope_path = repo / "docs/ios_26_4_security_mac_diff_vphone/VPHONE_KEXT_SCOPE.md"
    kexts_dir = repo / "docs/ios_26_4_security_mac_diff_vphone/KEXTS"

    if not args.dsc.exists():
        print(f"Missing DSC: {args.dsc}", file=sys.stderr)
        return 1
    if not args.kernelcache.exists():
        print(f"Missing kernelcache: {args.kernelcache}", file=sys.stderr)
        return 1

    scope = parse_vphone_scope(scope_path)
    diff_files = diff_bundle_files(kexts_dir)

    dy_lines = load_dylib_lines(args.dsc)

    with tempfile.TemporaryDirectory(prefix="kcdec_") as tmp:
        kc_dec = decompress_kernelcache(args.kernelcache, Path(tmp))
        kext_ids = load_kext_ids(kc_dec)

    rows = []
    for c in COMPONENTS:
        dsc_hits = match_lines(dy_lines, c["dsc"]) if c["dsc"] else []
        kc_hits = match_kexts(kext_ids, c["kc"]) if c["kc"] else []
        dc = diff_column(c["title"], kc_hits, c["diff_extra"], scope, diff_files)
        rows.append(
            (
                c["title"],
                ", ".join(c["cves"]),
                format_short(dsc_hits),
                format_kext(kc_hits),
                dc,
                c.get("notes") or "",
            )
        )

    generated = f"""# Full component map: iOS 26.4 security ↔ iPhone 26.3.1 DSC / stock KC ↔ vphone bundle scope ↔ macOS kext diff

Auto-generated by [`scripts/generate_ios_security_component_map.py`](../../scripts/generate_ios_security_component_map.py).

## Inputs (this run)

| Artifact | Path |
|----------|------|
| **dyld_shared_cache** (stock iPhone IPSW-derived) | `{args.dsc}` |
| **Stock iPhone restore kernelcache** (compressed IPSW file; **not** vphone/CFW/research KC) | `{args.kernelcache}` |
| **Kernelcache kext count** | **{len(kext_ids)}** bundle IDs from `ipsw kernel kexts -j` |
| **Vphone kext bundle-ID scope** | [`VPHONE_KEXT_SCOPE.md`](VPHONE_KEXT_SCOPE.md) (**{len(scope)}** bundles) — filters which UniversalMac diffs are linked |
| **UniversalMac ipsw diff** | [`KEXTS/`](KEXTS/) (`macOS_26_3_1_25D2128__vs_26_4_25E246`, vphone-scope-filtered) |

## How to read this

- **DSC / kernelcache here are stock iPhone 26.3.1** inventory checks (what ships in IPSW). A **vphone** build can replace `kernelcache` (and userspace); this output does **not** describe your patched vphone KC unless you pass `--kernelcache` to that binary.
- **DSC hits**: substring matches against `ipsw dyld info -l` paths — heuristic carrier binaries, not Apple’s internal radar component split.
- **Kernelcache hits**: substring matches on `com.apple.*` kext IDs from the **stock** restore kernelcache (or **all** IDs for **Kernel** bulletin rows).
- **macOS kext diff**: intersection of (a) bundles we explicitly tie to the bulletin row, (b) kext IDs matched in the **stock** KC that are also in vphone bundle-ID scope **and** have `KEXTS/*.md`, plus **`com.apple.kernel`** for Kernel rows. Userspace-only bulletin rows usually show **—** because this corpus is **kext/kernel diff markdown**, not DSC dylib diff.

Re-run after updating IPSW extracts or refreshing [`KEXTS/`](KEXTS/).

## Table

| Bulletin component | CVE IDs | Present in DSC (26.3.1 iPhone17,3) | Stock iPhone KC kext IDs | macOS 26.3.1→26.4 kext diff (vphone-scope-filtered) | Notes |
|--------------------|---------|--------------------------------------|--------------------------|-----------------------------------------------------|-------|
"""

    for t, cves, dsc_s, kc_s, diff_s, note in rows:
        note_esc = note.replace("|", "\\|")
        generated += f"| {t} | {cves} | {dsc_s} | {kc_s} | {diff_s} | {note_esc} |\n"

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(generated, encoding="utf-8")
    print(f"Wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
