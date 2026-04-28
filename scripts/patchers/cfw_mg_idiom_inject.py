"""
cfw_mg_idiom_inject.py — Inject DYLD_INSERT_LIBRARIES=vphone_mg_idiom.dylib
into launchd.plist job entries whose userspace reads MobileGestalt's
DeviceClassNumber and asserts on unknown idioms (iOS 18.5 on vresearch101).

Affected targets (iOS 18.5):
    - com.apple.SpringBoard
    - com.apple.AccessibilityUIServer
    - com.apple.chronod
    - com.apple.ndoagent
    - com.apple.spaceattributiond
    - com.apple.nanotimekitcompaniond
    - com.apple.backboardd
    - com.apple.datamigrator
    - com.apple.migrationpluginwrapper

Called from scripts/cfw_install_dev.sh during the launchd.plist patching phase.
"""

import plistlib
import sys


# Labels whose UIKit-dependent code paths crash on ComputeModule14,2 raw
# DeviceClassNumber and need the idiom interposer.
MG_IDIOM_INJECT_LABELS = {
    "com.apple.SpringBoard",
    "com.apple.AccessibilityUIServer",
    "com.apple.chronod",
    "com.apple.ndoagent",
    "com.apple.spaceattributiond",
    "com.apple.nanotimekitcompaniond",
    "com.apple.backboardd",
    "com.apple.datamigrator",
    "com.apple.migrationpluginwrapper",
}

DYLIB_PATH = "/usr/lib/vphone_mg_idiom.dylib"


def inject_mg_idiom(plist_path):
    """Inject DYLD_INSERT_LIBRARIES into targeted launchd job entries."""
    with open(plist_path, "rb") as f:
        root = plistlib.load(f)

    injected = 0
    for section_key, section in root.items():
        if not isinstance(section, dict):
            continue
        for job_key, job in section.items():
            if not isinstance(job, dict):
                continue
            label = job.get("Label", "")
            if label not in MG_IDIOM_INJECT_LABELS:
                continue

            env = job.get("EnvironmentVariables")
            if env is None:
                env = {}
                job["EnvironmentVariables"] = env

            existing = env.get("DYLD_INSERT_LIBRARIES", "")
            # Idempotent: skip if already injected.
            if DYLIB_PATH in existing.split(":"):
                print(f"  [=] {label}: DYLD_INSERT_LIBRARIES already set")
                continue

            env["DYLD_INSERT_LIBRARIES"] = (
                f"{existing}:{DYLIB_PATH}" if existing else DYLIB_PATH
            )
            print(f"  [+] {label}: DYLD_INSERT_LIBRARIES <- {DYLIB_PATH}")
            injected += 1

    with open(plist_path, "wb") as f:
        plistlib.dump(root, f, sort_keys=False)

    print(f"  [+] injected mg_idiom into {injected} jobs")
    return injected


def main(argv):
    if len(argv) != 2:
        print("Usage: cfw_mg_idiom_inject.py <launchd.plist>", file=sys.stderr)
        return 2
    inject_mg_idiom(argv[1])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
