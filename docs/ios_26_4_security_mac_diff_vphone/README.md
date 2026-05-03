# iOS 26.4 security + macOS kext diff + vphone scope

Single place for:

1. **Apple’s iOS/iPadOS 26.4 security bulletin** — [APPLE_SECURITY_IOS_26_4.md](APPLE_SECURITY_IOS_26_4.md) (from [support.apple.com/en-us/126792](https://support.apple.com/en-us/126792)).
2. **Vphone `vm/` firmware ↔ every bulletin component ↔ full UniversalMac diff corpus (`KEXTS/` + `DYLIBS/` + `MACHOS/`)** — [VPHONE_FIRMWARE_26_4_COVERAGE.md](VPHONE_FIRMWARE_26_4_COVERAGE.md) (regenerate: `scripts/generate_vphone_firmware_26_4_coverage.py`). Uses `**kernelcache.release.vphone600.macho`** plus inspectable files under `vm/` (mounted DMGs; `**Disk.img` skipped while VM may hold it open**).
3. `**ipsw diff` kext markdown** (subset copied into this repo) — UniversalMac `26.3.1 → 26.4`, filtered to vphone bundle IDs — `[KEXTS/](KEXTS/)`.
4. **Which bundles are “vphone scope”** — [VPHONE_KEXT_SCOPE.md](VPHONE_KEXT_SCOPE.md) (from `[kext_vphone600_vs_iphone17_26.3.1.md](../kext_vphone600_vs_iphone17_26.3.1.md)`).
5. **Cross-reference** — [CORRELATION.md](CORRELATION.md).
6. **Legacy / stock-iPhone inventory helper** — [FULL_COMPONENT_MAP.md](FULL_COMPONENT_MAP.md) (restore KC + external DSC; `scripts/generate_ios_security_component_map.py`).

## Files


| File                               | Role                                                                                                                             |
| ---------------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| `README.md`                        | This index                                                                                                                       |
| `APPLE_SECURITY_IOS_26_4.md`       | CVE/component impact + Apple fix blurbs                                                                                          |
| `VPHONE_FIRMWARE_26_4_COVERAGE.md` | **Canonical mapping**: bulletin ↔ `**vm/` vphone KC + inspectable firmware** ↔ `KEXTS`/`DYLIBS`/`MACHOS` diff corpus (generated) |
| `VPHONE_KEXT_SCOPE.md`             | All `com.apple.`* bundle IDs (common + only-vphone)                                                                              |
| `CORRELATION.md`                   | Bulletin ↔ bundles ↔ copied `KEXTS/*.md` links                                                                                   |
| `FULL_COMPONENT_MAP.md`            | Older experiment: stock iPhone DSC/KC + kext-only filtering (generated)                                                          |
| `KEXTS/*.md`                       | Copied from UniversalMac diff where bundle ∩ vphone scope; plus `com.apple.kernel.md`                                            |


## Related docs (same repo, `docs/`)

- [kext_vphone600_vs_iphone17_26.3.1.md](../kext_vphone600_vs_iphone17_26.3.1.md) — vphone600 vs iPhone17 kext lists and versions @ 26.3.1
- [kext_diff_26_3_to_26_3_1.md](../kext_diff_26_3_to_26_3_1.md) — embedded `ipsw diff` for **iPhone** `26.3 → 26.3.1`

## Counts

- Vphone-scope bundles: **161**
- `KEXTS/*.md` in this directory: **124**
- Upstream corpus path (local): `/Users/vinay/ipsw/mac_ipsw/ipsw-diffs/macOS_26_3_1_25D2128__vs_26_4_25E246/`