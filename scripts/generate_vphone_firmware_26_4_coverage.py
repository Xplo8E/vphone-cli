#!/usr/bin/env python3
"""
Build docs/ios_26_4_security_mac_diff_vphone/VPHONE_FIRMWARE_26_4_COVERAGE.md

Method (per user spec):
  - Apple security page components = vulns fixed in 26.4 (present on 26.3.1-era stacks).
  - Map each component to UniversalMac ipsw-diff artifacts under:
        KEXTS/, DYLIBS/, MACHOS/  (not kext-only).
  - Presence **only** on inspectable vphone firmware under repo `vm/`:
        * kernelcache.release.vphone600.macho  (CloudOS mix KC)
        * attachable .dmg under vm (e.g. App Cryptex)
        * other vm tree paths (excluding Disk.img / huge blobs)
        * Mach-O / kernelcache substring scan for dylibs not exposed as paths (see `fw_binary_needles`)

If a component has no carrier via those checks, it is listed at the end as
missing from firmware-on-disk (guest may still ship it inside sealed volumes / Disk.img).

Re-run:
  python3 scripts/generate_vphone_firmware_26_4_coverage.py \\
    --vm-root vm \\
    --diff-root /Users/vinay/ipsw/mac_ipsw/ipsw-diffs/macOS_26_3_1_25D2128__vs_26_4_25E246

  For repo-relative **Diff** links, mirror the ipsw-diff trees under
  `docs/ios_26_4_security_mac_diff_vphone/` (same layout as diff root):
    rsync -a "$DIFF_ROOT/KEXTS/" docs/ios_26_4_security_mac_diff_vphone/KEXTS/
    rsync -a "$DIFF_ROOT/DYLIBS/" docs/ios_26_4_security_mac_diff_vphone/DYLIBS/
    rsync -a "$DIFF_ROOT/MACHOS/" docs/ios_26_4_security_mac_diff_vphone/MACHOS/
"""

from __future__ import annotations

import argparse
import mmap
import os
import plistlib
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

import json

# --- bulletin rows: CVEs + how we probe vm + which diff stems to link -----------------

SPEC: list[dict[str, Any]] = [
    {
        "title": "802.1X",
        "cves": ["CVE-2026-28865"],
        "kc": ["IO80211", "80211Family", "BCMWLAN", "WLAN"],
        "fw_substr": ["eap8021x", "io80211", "wifi"],
        # vphone600 KC often omits IO80211Family from `ipsw kernel kexts`; substring in KC Mach-O still carries 802.1X stack text.
        "fw_binary_needles": ["IO80211", "EAPOL"],
        "diff_kext": ["com.apple.iokit.IO80211Family"],
        "diff_dylib": ["EAP8021X"],
        "diff_macho": [],
    },
    {
        "title": "Accounts",
        "cves": ["CVE-2026-28877"],
        "kc": [],
        "fw_substr": ["accounts.framework", "/accounts/", "accountsdaemon"],
        "diff_kext": [],
        "diff_dylib": ["Accounts", "AccountsDaemon", "AccountsUI"],
        "diff_macho": [],
    },
    {
        "title": "App Protection",
        "cves": ["CVE-2026-28895"],
        "kc": ["AppleSEP", "MobileFileIntegrity", "EffaceableStorage"],
        "fw_substr": ["appprotection", "localauthentication"],
        "diff_kext": [
            "com.apple.driver.AppleMobileFileIntegrity",
            "com.apple.driver.AppleSEPKeyStore",
            "com.apple.driver.AppleSEPManager",
        ],
        "diff_dylib": ["AppProtection", "AppProtectionDaemon", "LocalAuthentication", "LocalAuthenticationCore"],
        "diff_macho": [],
    },
    {
        "title": "Audio",
        "cves": ["CVE-2026-28879", "CVE-2026-28822"],
        "kc": ["Audio", "ARMIISAudio", "ExclavesAudio", "EmbeddedAudio", "AOPAudio"],
        "fw_substr": ["audiotoolbox", "avfaudio", "coreaudio"],
        "diff_kext": [
            "com.apple.driver.AppleEmbeddedAudioLibs",
            "com.apple.driver.ExclavesAudioKext",
            "com.apple.iokit.AppleARMIISAudio",
            "com.apple.driver.AppleAudioClockLibs",
            "com.apple.iokit.IOAudio2Family",
            "com.apple.driver.IISAudioIsolatedStreamECProxy",
        ],
        "diff_dylib": ["AudioToolbox", "AVFAudio", "CoreAudio"],
        "diff_macho": [],
    },
    {
        "title": "Baseband",
        "cves": ["CVE-2026-28874", "CVE-2026-28875"],
        "kc": ["Baseband"],
        "fw_substr": ["baseband", "brunor", "sumter", "savage", "modem"],
        "diff_kext": [],
        "diff_dylib": [],
        "diff_macho": [],
    },
    {
        "title": "Calling Framework",
        "cves": ["CVE-2026-28894"],
        "kc": [],
        "fw_substr": ["telephonyutilities", "callkit", "facetime"],
        "fw_binary_needles": ["TelephonyUtilities", "FaceTime", "CallKit"],
        "diff_kext": [],
        "diff_dylib": ["TelephonyUtilities", "FaceTime", "FaceTimeMessageStore"],
        "diff_macho": [],
    },
    {
        "title": "Clipboard",
        "cves": ["CVE-2026-28866"],
        "kc": [],
        "fw_substr": ["pasteboard", "clipboard", "uikit"],
        "fw_binary_needles": ["Pasteboard"],
        "diff_kext": [],
        "diff_dylib": ["UIKit"],
        "diff_macho": [],
    },
    {
        "title": "CoreMedia",
        "cves": ["CVE-2026-20690"],
        "kc": [],
        "fw_substr": ["coremedia"],
        "fw_binary_needles": ["CoreMedia"],
        "diff_kext": [],
        "diff_dylib": ["CoreMedia", "CoreMediaIO"],
        "diff_macho": [],
    },
    {
        "title": "CoreUtils",
        "cves": ["CVE-2026-28886"],
        "kc": [],
        # No CoreUtils* ASCII in inspectable Mach-O/kernelcache blobs under vm/ (may live only in sealed volumes / Disk.img).
        "fw_substr": ["coreutils"],
        "diff_kext": [],
        "diff_dylib": ["CoreUtils", "CoreUtilsExtras"],
        "diff_macho": [],
    },
    {
        "title": "Crash Reporter",
        "cves": ["CVE-2026-28878"],
        "kc": [],
        "fw_substr": ["crashreporter", "crashdiagnostic"],
        "fw_binary_needles": ["CrashReporter"],
        "diff_kext": [],
        "diff_dylib": ["CrashReporterSupport", "CrashReporter"],
        "diff_macho": [],
    },
    {
        "title": "curl",
        "cves": ["CVE-2025-14524"],
        "kc": [],
        "fw_substr": ["curl", "libcurl"],
        "fw_binary_needles": ["curl", "CFNetwork"],
        "diff_kext": [],
        "diff_dylib": ["libcurl.4.dylib", "CFNetwork"],
        "diff_macho": [],
    },
    {
        "title": "DeviceLink",
        "cves": ["CVE-2026-28876"],
        "kc": [],
        "fw_substr": ["mobiledevicelink", "devicelink"],
        "fw_binary_needles": ["DeviceLink"],
        "diff_kext": [],
        "diff_dylib": ["MobileDeviceLink"],
        "diff_macho": [],
    },
    {
        "title": "GeoServices",
        "cves": ["CVE-2026-28870"],
        "kc": [],
        "fw_substr": ["geoservices"],
        "fw_binary_needles": ["GeoServices"],
        "diff_kext": [],
        "diff_dylib": ["GeoServices", "GeoServicesCore"],
        "diff_macho": [],
    },
    {
        "title": "iCloud",
        "cves": ["CVE-2026-28880", "CVE-2026-28833"],
        "kc": [],
        "fw_substr": ["cloudkit", "icloud"],
        "diff_kext": [],
        "diff_dylib": ["CloudKit", "CloudKitDaemon", "CloudServices"],
        "diff_macho": [],
    },
    {
        "title": "ImageIO",
        "cves": ["CVE-2025-64505"],
        "kc": [],
        "fw_substr": ["imageio"],
        "fw_binary_needles": ["ImageIO"],
        "diff_kext": [],
        "diff_dylib": ["ImageIO"],
        "diff_macho": [],
    },
    {
        "title": "Kernel",
        "cves": ["CVE-2026-28868", "CVE-2026-28867", "CVE-2026-20698", "CVE-2026-20687"],
        "kc": ["__ALL__"],
        "fw_substr": [],
        "diff_kext": ["com.apple.kernel"],
        "diff_dylib": [],
        "diff_macho": [],
    },
    {
        "title": "libxpc",
        "cves": ["CVE-2026-28882"],
        "kc": [],
        # Dylib lives under sealed system volume — not visible as a path in vm/ walk + cryptex.
        # We detect `libxpc` text inside inspectable Mach-O / kernelcache blobs instead.
        "fw_substr": ["libxpc.dylib", "/usr/lib/system/libxpc"],
        "fw_binary_needles": ["libxpc"],
        "diff_kext": [],
        "diff_dylib": ["libxpc.dylib", "XPCSupport"],
        "diff_macho": [],
    },
    {
        "title": "Mail",
        "cves": ["CVE-2026-20692"],
        "kc": [],
        "fw_substr": ["mail.", "/mail/", "message.framework"],
        "fw_binary_needles": ["com.apple.mobilemail"],
        "diff_kext": [],
        "diff_dylib": ["Mail", "MailCore", "MailKit", "Email", "Message"],
        "diff_macho": [],
    },
    {
        "title": "Printing",
        "cves": ["CVE-2026-20688"],
        "kc": [],
        "fw_substr": ["printkit", "printing"],
        "fw_binary_needles": ["PrintKit"],
        "diff_kext": [],
        "diff_dylib": ["PrintKit", "PrintKitUI"],
        "diff_macho": [],
    },
    {
        "title": "Sandbox Profiles",
        "cves": ["CVE-2026-28863"],
        "kc": ["sandbox"],
        "fw_substr": ["sandbox", "containermanager"],
        "diff_kext": ["com.apple.security.sandbox"],
        "diff_dylib": ["libsystem_sandbox.dylib"],
        "diff_macho": [],
    },
    {
        "title": "Security",
        "cves": ["CVE-2026-28864"],
        "kc": ["AppleMobileFileIntegrity", "SEPKeyStore", "SEPManager", "corecrypto"],
        "fw_substr": ["security.framework"],
        "diff_kext": [
            "com.apple.driver.AppleMobileFileIntegrity",
            "com.apple.driver.AppleSEPKeyStore",
            "com.apple.driver.AppleSEPManager",
            "com.apple.kec.corecrypto",
            "com.apple.security.AppleImage4",
        ],
        "diff_dylib": ["Security"],
        "diff_macho": [],
    },
    {
        "title": "Siri",
        "cves": ["CVE-2026-28856"],
        "kc": [],
        "fw_substr": ["siri", "assistantservices"],
        "fw_binary_needles": ["AssistantServices", "SiriInference"],
        "diff_kext": [],
        "diff_dylib": ["SiriInference", "AssistantServices", "SiriActivation"],
        "diff_macho": [],
    },
    {
        "title": "Telephony",
        "cves": ["CVE-2026-28858"],
        "kc": ["Baseband", "Telephony"],
        "fw_substr": ["coretelephony"],
        "fw_binary_needles": ["CoreTelephony"],
        "diff_kext": [],
        "diff_dylib": ["CoreTelephony"],
        "diff_macho": [],
    },
    {
        "title": "UIFoundation",
        "cves": ["CVE-2026-28852"],
        "kc": [],
        "fw_substr": ["uifoundation"],
        "fw_binary_needles": ["UIFoundation"],
        "diff_kext": [],
        "diff_dylib": ["UIFoundation"],
        "diff_macho": [],
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
        "kc": [],
        "fw_substr": ["webkit.framework", "javascriptcore", "mobilesafari", "webkitlegacy"],
        "diff_kext": [],
        "diff_dylib": ["WebKit", "WebKitLegacy", "JavaScriptCore", "libWebKitSwift.dylib", "_WebKit_SwiftUI"],
        "diff_macho": [
            "com.apple.WebKit.WebContent",
            "com.apple.WebKit.Networking",
            "com.apple.WebKit.GPU",
        ],
    },
    {
        "title": "WebKit Sandboxing",
        "cves": ["CVE-2026-20691"],
        "kc": ["sandbox"],
        "fw_substr": ["webkit", "libxpc", "sandbox"],
        "diff_kext": ["com.apple.security.sandbox"],
        "diff_dylib": ["WebKit", "libxpc.dylib", "libsystem_sandbox.dylib"],
        "diff_macho": ["com.apple.WebKit.WebContent"],
    },
]


def run(cmd: list[str]) -> None:
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.stderr.write(p.stderr or p.stdout or "")
        raise RuntimeError(" ".join(cmd))


def attach_dmg(dmg: Path) -> Path | None:
    out = subprocess.run(
        ["hdiutil", "attach", "-nobrowse", "-readonly", "-plist", str(dmg)],
        capture_output=True,
    )
    if out.returncode != 0:
        return None
    pl = plistlib.loads(out.stdout)
    for ent in pl.get("system-entities", []):
        mp = ent.get("mount-point")
        if mp:
            return Path(mp)
    return None


def detach_all(mounts: list[Path]) -> None:
    for mp in mounts:
        subprocess.run(["hdiutil", "detach", str(mp)], capture_output=True)


def find_vphone_kc(vm_root: Path) -> Path | None:
    for name in (
        "kernelcache.release.vphone600.macho",
        "kernelcache.research.vphone600.macho",
    ):
        for p in vm_root.rglob(name):
            if p.is_file():
                return p
    return None


def load_kext_ids(kc: Path) -> list[str]:
    raw = subprocess.check_output(["ipsw", "kernel", "kexts", "-j", str(kc)], text=True)
    data = json.loads(raw)
    return [e["id"] for e in data]


def collect_fw_strings(vm_root: Path, extra_mounts: list[Path]) -> list[str]:
    """Lowercased path strings from vm (skipping huge / VM-owned files) + mounted DMGs."""
    skip_names = {
        "disk.img",
        ".ds_store",
    }
    paths: list[str] = []

    def walk(base: Path, max_files: int = 500_000) -> None:
        nonlocal paths
        count = 0
        for dirpath, dirnames, filenames in os.walk(base):
            # prune noisy / huge
            if "logs" in dirpath.split(os.sep):
                continue
            rel = Path(dirpath).relative_to(base)
            parts_lower = {p.lower() for p in rel.parts}
            if ".cfw_temp" in parts_lower:
                continue
            for fn in filenames:
                count += 1
                if count > max_files:
                    return
                low = fn.lower()
                if low in skip_names or low.endswith(".sock"):
                    continue
                fp = Path(dirpath) / fn
                try:
                    if fp.is_file() and fp.stat().st_size > 800_000_000:
                        continue
                except OSError:
                    continue
                paths.append(str(fp).lower())

    walk(vm_root)
    for mp in extra_mounts:
        walk(mp, max_files=200_000)
    return paths


def firmware_blob_candidates(vm_root: Path) -> list[Path]:
    """Mach-O / kernelcache files under vm (skip DMG, Disk.img, oversized)."""
    skip = {"disk.img"}
    out: list[Path] = []
    for p in vm_root.rglob("*"):
        if not p.is_file():
            continue
        if p.suffix.lower() == ".dmg":
            continue
        if p.name.lower() in skip:
            continue
        name = p.name.lower()
        if not (name.endswith(".macho") or "kernelcache" in name):
            continue
        try:
            sz = p.stat().st_size
        except OSError:
            continue
        if sz == 0 or sz > 130_000_000:
            continue
        out.append(p)
    return out


def blob_contains(path: Path, needle: bytes) -> bool:
    if not needle:
        return False
    try:
        with open(path, "rb") as f:
            with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
                return mm.find(needle) != -1
    except OSError:
        return False


def scan_blob_needles(vm_root: Path, needles: set[str]) -> dict[str, bool]:
    """For each needle (ASCII), True if any firmware blob under vm contains it."""
    if not needles:
        return {}
    blobs = firmware_blob_candidates(vm_root)
    nb_map = {n: n.encode("utf-8", "surrogateescape") for n in needles}
    result: dict[str, bool] = {n: False for n in needles}
    for p in blobs:
        for n, nb in nb_map.items():
            if result[n]:
                continue
            if blob_contains(p, nb):
                result[n] = True
    return result


def match_kc(ids: list[str], patterns: list[str]) -> tuple[bool, list[str]]:
    if patterns == ["__ALL__"]:
        return True, [f"({len(ids)} kext bundles + XNU in this KC)"]
    hits = []
    for kid in ids:
        kl = kid.lower()
        for pat in patterns:
            if pat.lower() in kl:
                hits.append(kid)
                break
    return bool(hits), sorted(set(hits))


def match_fw(fw_paths_lc: list[str], substrings: list[str]) -> tuple[bool, list[str]]:
    if not substrings:
        return False, []
    evidence: list[str] = []
    for line in fw_paths_lc:
        for sub in substrings:
            if sub.lower() in line:
                evidence.append(line)
                break
        if len(evidence) >= 6:
            break
    return bool(evidence), evidence[:6]


def index_diffs(diff_root: Path) -> tuple[dict[str, Path], dict[str, Path], dict[str, Path]]:
    kexts = {p.stem: p for p in (diff_root / "KEXTS").glob("*.md")}
    dylibs = {p.stem: p for p in (diff_root / "DYLIBS").glob("*.md")}
    machos = {p.stem: p for p in (diff_root / "MACHOS").glob("*.md")}
    return kexts, dylibs, machos


def resolve_links(
    diff_root: Path,
    dk: dict[str, Path],
    dd: dict[str, Path],
    dm: dict[str, Path],
    spec: dict[str, Any],
) -> list[Path]:
    """Absolute paths to diff markdown files (deduped, ordered)."""
    out: list[Path] = []
    for bid in spec.get("diff_kext", []):
        p = dk.get(bid)
        if p:
            out.append(p.resolve())
    for stem in spec.get("diff_dylib", []):
        p = dd.get(stem)
        if p:
            out.append(p.resolve())
    for stem in spec.get("diff_macho", []):
        p = dm.get(stem)
        if p:
            out.append(p.resolve())
    seen: set[Path] = set()
    uniq: list[Path] = []
    for p in out:
        if p not in seen:
            seen.add(p)
            uniq.append(p)
    return uniq


CVE_LINE_RE = re.compile(r"CVE-\d{4}-\d+")


def parse_apple_security_bulletin(md_path: Path) -> dict[str, tuple[str, str, str]]:
    """CVE-ID -> (Apple component heading, Impact text, Description/fix text)."""
    raw = md_path.read_text(encoding="utf-8")
    chunks = re.split(r"\n### ", raw)
    out: dict[str, tuple[str, str, str]] = {}
    for chunk in chunks[1:]:
        lines = chunk.splitlines()
        if not lines:
            continue
        title = lines[0].strip()
        impact = ""
        fix = ""
        for line in lines[1:]:
            if line.startswith("Impact:"):
                impact = line.split(":", 1)[1].strip()
            elif line.startswith("Description:"):
                fix = line.split(":", 1)[1].strip()
        block = "\n".join(lines)
        for m in CVE_LINE_RE.finditer(block):
            out[m.group(0)] = (title, impact, fix)
    return out


def md_cell_escape(text: str) -> str:
    """Single-line markdown table cell; avoid breaking on |."""
    return text.replace("|", "\\|").replace("\n", " ")


def format_vphone_bundle_cell(
    spec: dict[str, Any],
    present: bool,
    in_kc: bool,
    kc_ev: list[str],
    dk: dict[str, Path],
    dd: dict[str, Path],
    dm: dict[str, Path],
) -> str:
    """CORRELATION-style bundle labels: kext IDs / dylib stems present in diff corpus."""
    if not present:
        return "—"
    kext_hits = [bid for bid in spec.get("diff_kext", []) if bid in dk]
    if kext_hits:
        tail = " …" if len(kext_hits) > 5 else ""
        return "<br>".join(f"`{b}`" for b in kext_hits[:5]) + tail

    if spec.get("kc") == ["__ALL__"] and present:
        return "`com.apple.kernel`"

    clean_kc = [x for x in kc_ev if not x.strip().startswith("(")]
    if in_kc and clean_kc:
        uniq = sorted(set(clean_kc))
        tail = " …" if len(uniq) > 5 else ""
        return "<br>".join(f"`{x}`" for x in uniq[:5]) + tail

    stems: list[str] = []
    for s in spec.get("diff_dylib", []):
        if s in dd:
            stems.append(s if s.endswith(".dylib") else f"{s}.dylib")
    for s in spec.get("diff_macho", []):
        if s in dm:
            stems.append(s)
    if stems:
        tail = " …" if len(stems) > 6 else ""
        return "<br>".join(f"`{x}`" for x in stems[:6]) + tail

    if present:
        return "`(carrier in vm — no mapped diff stem)`"
    return "—"


def _diff_link_short_label(rel: Path) -> str:
    """Link text: `kernel.md`-style short name for `com.apple.*` stems; else filename."""
    stem = rel.stem
    name = rel.name
    if stem.startswith("com.apple."):
        return stem.rsplit(".", 1)[-1] + ".md"
    return name


def format_diff_correlation_links(paths: list[Path], diff_root: Path, doc_dir: Path) -> str:
    """Repo-relative `[short.md](KEXTS/…)` when mirrored under doc_dir; else `[short.md](file://…)` — same label style."""
    if not paths:
        return "—"
    root = diff_root.resolve()
    doc_dir = doc_dir.resolve()
    parts: list[str] = []
    for full in paths:
        full = full.resolve()
        try:
            rel = full.relative_to(root)
        except ValueError:
            try:
                href = full.as_uri()
            except ValueError:
                href = full.as_posix()
            parts.append(f"[{full.name}]({href})")
            continue
        label = rel.as_posix()
        short = _diff_link_short_label(rel)
        local = doc_dir / rel
        if local.is_file():
            parts.append(f"[{short}]({label})")
        else:
            try:
                href = full.as_uri()
            except ValueError:
                href = full.as_posix()
            parts.append(f"[{short}]({href})")
    return "<br>".join(parts)


def main() -> int:
    repo = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser()
    ap.add_argument("--vm-root", type=Path, default=repo / "vm")
    ap.add_argument(
        "--diff-root",
        type=Path,
        default=Path(
            os.environ.get(
                "IPSW_DIFF_MACOS_26_3_1_VS_26_4",
                "/Users/vinay/ipsw/mac_ipsw/ipsw-diffs/macOS_26_3_1_25D2128__vs_26_4_25E246",
            )
        ),
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=repo / "docs/ios_26_4_security_mac_diff_vphone/VPHONE_FIRMWARE_26_4_COVERAGE.md",
    )
    ap.add_argument(
        "--apple-security",
        type=Path,
        default=repo / "docs/ios_26_4_security_mac_diff_vphone/APPLE_SECURITY_IOS_26_4.md",
        help="Parsed for Impact + Description columns (CORRELATION-style table).",
    )
    args = ap.parse_args()

    vm = args.vm_root.resolve()
    diff_root = args.diff_root.resolve()
    doc_dir = args.out.parent.resolve()
    apple_md = args.apple_security.resolve()
    bulletin: dict[str, tuple[str, str, str]] = (
        parse_apple_security_bulletin(apple_md) if apple_md.is_file() else {}
    )

    if not vm.is_dir():
        print(f"vm root missing: {vm}", file=sys.stderr)
        return 1
    if not (diff_root / "KEXTS").is_dir():
        print(f"diff root missing KEXTS/: {diff_root}", file=sys.stderr)
        return 1

    kc_path = find_vphone_kc(vm)
    if not kc_path:
        print(f"No kernelcache.release.vphone600.macho under {vm}", file=sys.stderr)
        return 1

    mounts: list[Path] = []
    try:
        restore_dirs = list(vm.glob("iPhone*_Restore")) + list(vm.glob("**/iPhone*_Restore"))
        seen_dmg: set[Path] = set()
        for rd in restore_dirs:
            if not rd.is_dir():
                continue
            for dmg in sorted(rd.glob("*.dmg")):
                if dmg in seen_dmg:
                    continue
                seen_dmg.add(dmg)
                mp = attach_dmg(dmg)
                if mp:
                    mounts.append(mp)

        kext_ids = load_kext_ids(kc_path)
        fw_lc = collect_fw_strings(vm, mounts)
        blob_needles: set[str] = set()
        for sp in SPEC:
            blob_needles.update(sp.get("fw_binary_needles") or [])
        blob_hit_map = scan_blob_needles(vm, blob_needles)
        dk, dd, dm = index_diffs(diff_root)

        spec_rows: list[dict[str, Any]] = []
        absent: list[str] = []
        present_no_diff: list[str] = []

        for spec in SPEC:
            title = spec["title"]
            in_kc, kc_ev = match_kc(kext_ids, spec["kc"])
            in_fw_path, _fw_ev = match_fw(fw_lc, spec["fw_substr"])
            bin_needles = spec.get("fw_binary_needles") or []
            bin_hit = any(blob_hit_map.get(n, False) for n in bin_needles)
            in_fw = in_fw_path or bin_hit
            present = in_kc or in_fw
            link_paths = resolve_links(diff_root, dk, dd, dm, spec) if present else []
            bundle_cell = format_vphone_bundle_cell(spec, present, in_kc, kc_ev, dk, dd, dm)
            diff_cell = format_diff_correlation_links(link_paths, diff_root, doc_dir)
            spec_rows.append(
                {
                    "title": title,
                    "cves_list": list(spec["cves"]),
                    "bundle_cell": bundle_cell,
                    "diff_cell": diff_cell,
                    "present": present,
                    "has_diff": bool(link_paths),
                }
            )
            if not present:
                absent.append(title)
            elif present and not link_paths:
                present_no_diff.append(title)

        lines = []
        lines.append("# Vphone `vm/` firmware ↔ iOS 26.4 security components ↔ UniversalMac diff corpus")
        lines.append("")
        lines.append("Auto-generated by [`scripts/generate_vphone_firmware_26_4_coverage.py`](../../scripts/generate_vphone_firmware_26_4_coverage.py).")
        lines.append("")
        lines.append("## Method")
        lines.append("")
        lines.append("- **Security page** ([`APPLE_SECURITY_IOS_26_4.md`](APPLE_SECURITY_IOS_26_4.md)): fixes in **26.4** → treated as vuln surface on **26.3.1-era** stacks.")
        lines.append("- **Diff corpus**: UniversalMac `26.3.1 (25D2128)` vs `26.4 (25E246)` — **`KEXTS/` + `DYLIBS/` + `MACHOS/`** (not kext-only).")
        lines.append(f"- **Diff root (local)**: `{diff_root}`")
        lines.append(f"- **Vphone KC inspected**: `{kc_path}` (**CloudOS / vphone mix**, Mach-O slice).")
        lines.append(f"- **KC kext bundles counted**: **{len(kext_ids)}**.")
        lines.append(f"- **DMGs mounted from `vm/`**: {len(mounts)} volume(s) — " + ", ".join(str(m) for m in mounts) if mounts else "*none*")
        lines.append(
            "- **`vm/` path walk** misses dylibs inside sealed DMGs / `Disk.img` (e.g. `/usr/lib/system/libxpc.dylib`). "
            "For some bulletin rows we also scan **Mach-O / kernelcache blobs** under `vm/` for an ASCII substring (`fw_binary_needles` in the script)."
        )
        lines.append(
            "- **Coverage table**: same columns as [`CORRELATION.md`](CORRELATION.md). **Impact** and **Fix** are parsed from "
            "[`APPLE_SECURITY_IOS_26_4.md`](APPLE_SECURITY_IOS_26_4.md). **Diff** links are repo-relative "
            "(`[short.md](KEXTS/…)`, `[short.md](DYLIBS/…)`, `[short.md](MACHOS/…)`) when those trees are mirrored "
            "under this folder (see `DYLIBS/`, `MACHOS/` next to `KEXTS/`); otherwise they fall back to `file://` "
            "URLs against **Diff root**."
        )
        lines.append("")
        lines.append("## Coverage table")
        lines.append("")
        lines.append("| Apple component | CVE IDs | Impact (Apple) | Fix (Apple description) | Vphone bundle | Diff |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for sr in spec_rows:
            for cve in sr["cves_list"]:
                bt = bulletin.get(cve)
                impact_s = md_cell_escape(bt[1]) if bt and bt[1] else "—"
                fix_s = md_cell_escape(bt[2]) if bt and bt[2] else "—"
                lines.append(
                    f"| {sr['title']} | {cve} | {impact_s} | {fix_s} | {sr['bundle_cell']} | {sr['diff_cell']} |"
                )

        lines.append("")
        lines.append("## Components **not** found in inspectable vphone firmware")
        lines.append("")
        lines.append(
            "These had **no** KC substring hit **and** no carrier via **`vm/` paths**, "
            "**mounted DMGs**, or **Mach-O / kernelcache substring probes** (`fw_binary_needles`). "
            "They may still exist **inside sealed volumes or `Disk.img`**."
        )
        lines.append("")
        if absent:
            for t in absent:
                lines.append(f"- **{t}**")
        else:
            lines.append("- *(none)*")

        lines.append("")
        lines.append("## Present in firmware but **no** matching diff artifact")
        lines.append("")
        lines.append(
            "Carrier matched in KC or inspectable paths, but none of the configured `KEXTS`/`DYLIBS`/`MACHOS` stems exist in the corpus (tighten mapping in the script if needed)."
        )
        lines.append("")
        if present_no_diff:
            for t in present_no_diff:
                lines.append(f"- **{t}**")
        else:
            lines.append("- *(none)*")

        lines.append("")
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Wrote {args.out}")
        return 0
    finally:
        detach_all(mounts)


if __name__ == "__main__":
    raise SystemExit(main())
