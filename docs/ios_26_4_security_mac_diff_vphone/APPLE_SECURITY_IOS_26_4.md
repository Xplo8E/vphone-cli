# Apple security content: iOS 26.4 and iPadOS 26.4

Official page: [https://support.apple.com/en-us/126792](https://support.apple.com/en-us/126792)

The sections below reproduce Apple’s **Impact** and **Description** (fix summary) text for each CVE entry on that page.

---

## About Apple security updates

For our customers' protection, Apple doesn't disclose, discuss, or confirm security issues until an investigation has occurred and patches or releases are available. Recent releases are listed on the [Apple security releases](https://support.apple.com/en-us/100100) page.

Apple security documents reference vulnerabilities by [CVE-ID](https://www.cve.org/About/Overview) when possible.

For more information about security, see the [Apple Product Security](https://support.apple.com/en-us/102549) page.

## iOS 26.4 and iPadOS 26.4

Released March 24, 2026

### 802.1X

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: An attacker in a privileged network position may be able to intercept network traffic

Description: An authentication issue was addressed with improved state management.

CVE-2026-28865: Héloïse Gollier and Mathy Vanhoef (KU Leuven)

### Accounts

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: An app may be able to access sensitive user data

Description: An authorization issue was addressed with improved state management.

CVE-2026-28877: Rosyna Keller of Totally Not Malicious Software

### App Protection

Available for: iPhone 11 and later

Impact: An attacker with physical access to an iOS device with Stolen Device Protection enabled may be able to access biometrics-gated Protected Apps with the passcode

Description: The issue was addressed with improved checks.

CVE-2026-28895: Adrián Pérez Martínez, Uluk Abylbekov, and Zack Tickman

Entry updated April 9, 2026

### Audio

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: Processing maliciously crafted web content may lead to an unexpected process crash

Description: A use-after-free issue was addressed with improved memory management.

CVE-2026-28879: Justin Cohen of Google

### Audio

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: An attacker may be able to cause unexpected app termination

Description: A type confusion issue was addressed with improved memory handling.

CVE-2026-28822: Jex Amro

### Baseband

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: A remote attacker may cause an unexpected app termination

Description: The issue was addressed with improved checks.

CVE-2026-28874: Hazem Issa, Tuan D. Hoang, and Yongdae Kim @ SysSec, KAIST

### Baseband

Available for: iPhone 16e

Impact: A remote attacker may be able to cause a denial-of-service

Description: A buffer overflow was addressed with improved bounds checking.

CVE-2026-28875: Tuan D. Hoang and Yongdae Kim @ KAIST SysSec Lab

### Calling Framework

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: A remote attacker may be able to cause a denial-of-service

Description: A denial-of-service issue was addressed with improved input validation.

CVE-2026-28894: an anonymous researcher

### Clipboard

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: An app may be able to access sensitive user data

Description: This issue was addressed with improved validation of symlinks.

CVE-2026-28866: Cristian Dinca (icmd.tech)

### CoreMedia

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: Processing an audio stream in a maliciously crafted media file may terminate the process

Description: An out-of-bounds access issue was addressed with improved bounds checking.

CVE-2026-20690: Hossein Lotfi (@hosselot) of Trend Micro Zero Day Initiative

### CoreUtils

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: A user in a privileged network position may be able to cause a denial-of-service

Description: A null pointer dereference was addressed with improved input validation.

CVE-2026-28886: Etienne Charron (Renault) and Victoria Martini (Renault)

### Crash Reporter

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: An app may be able to enumerate a user's installed apps

Description: A privacy issue was addressed by removing sensitive data.

CVE-2026-28878: Zhongcheng Li from IES Red Team

### curl

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: An issue existed in curl which may result in unintentionally sending sensitive information via an incorrect connection

Description: This is a vulnerability in open source code and Apple Software is among the affected projects. The CVE-ID was assigned by a third party. Learn more about the issue and CVE-ID at [cve.org](https://www.cve.org/).

CVE-2025-14524

### DeviceLink

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: An app may be able to access sensitive user data

Description: A parsing issue in the handling of directory paths was addressed with improved path validation.

CVE-2026-28876: Andreas Jaegersberger & Ro Achterberg of Nosebeard Labs

### GeoServices

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: An app may be able to access sensitive user data

Description: An information leakage was addressed with additional validation.

CVE-2026-28870: XiguaSec

### iCloud

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: An app may be able to enumerate a user's installed apps

Description: A permissions issue was addressed with additional restrictions.

CVE-2026-28880: Zhongcheng Li from IES Red Team

CVE-2026-28833: Zhongcheng Li from IES Red Team

### ImageIO

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: Processing a maliciously crafted file may lead to unexpected app termination

Description: This is a vulnerability in open source code and Apple Software is among the affected projects. The CVE-ID was assigned by a third party. Learn more about the issue and CVE-ID at [cve.org](https://www.cve.org/).

CVE-2025-64505

### Kernel

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: An app may be able to disclose kernel memory

Description: A logging issue was addressed with improved data redaction.

CVE-2026-28868: 이동하 (Lee Dong Ha of BoB 0xB6)

### Kernel

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: An app may be able to leak sensitive kernel state

Description: This issue was addressed with improved authentication.

CVE-2026-28867: Jian Lee (@speedyfriend433)

### Kernel

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: An app may be able to cause unexpected system termination or corrupt kernel memory

Description: The issue was addressed with improved memory handling.

CVE-2026-20698: DARKNAVY (@DarkNavyOrg)

### Kernel

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: An app may be able to cause unexpected system termination or write kernel memory

Description: A use after free issue was addressed with improved memory management.

CVE-2026-20687: Johnny Franks (@zeroxjf)

### libxpc

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: An app may be able to enumerate a user's installed apps

Description: This issue was addressed with improved checks.

CVE-2026-28882: Ilias Morad (A2nkF) of Voynich Group, Duy Trần (@khanhduytran0), @hugeBlack

### Mail

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: "Hide IP Address" and "Block All Remote Content" may not apply to all mail content

Description: A privacy issue was addressed with improved handling of user preferences.

CVE-2026-20692: Andreas Jaegersberger & Ro Achterberg of Nosebeard Labs

### Printing

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: An app may be able to break out of its sandbox

Description: A path handling issue was addressed with improved validation.

CVE-2026-20688: wdszzml and Atuin Automated Vulnerability Discovery Engine

### Sandbox Profiles

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: An app may be able to fingerprint the user

Description: A permissions issue was addressed with additional restrictions.

CVE-2026-28863: Gongyu Ma (@Mezone0)

### Security

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: A local attacker may gain access to user's Keychain items

Description: This issue was addressed with improved permissions checking.

CVE-2026-28864: Alex Radocea

### Siri

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: An attacker with physical access to a locked device may be able to view sensitive user information

Description: The issue was addressed with improved authentication.

CVE-2026-28856: an anonymous researcher

### Telephony

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: A remote user may be able to cause unexpected system termination or corrupt kernel memory

Description: A buffer overflow was addressed with improved bounds checking.

CVE-2026-28858: Hazem Issa and Yongdae Kim @ SysSec, KAIST

### UIFoundation

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: An app may be able to cause a denial-of-service

Description: A stack overflow was addressed with improved input validation.

CVE-2026-28852: Caspian Tarafdar

### WebKit

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: Processing maliciously crafted web content may prevent Content Security Policy from being enforced

Description: This issue was addressed through improved state management.

WebKit Bugzilla: 304951

CVE-2026-20665: webb

### WebKit

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: Processing maliciously crafted web content may bypass Same Origin Policy

Description: A cross-origin issue in the Navigation API was addressed with improved input validation.

WebKit Bugzilla: 306050

CVE-2026-20643: Thomas Espach

### WebKit

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: Visiting a maliciously crafted website may lead to a cross-site scripting attack

Description: A logic issue was addressed with improved checks.

WebKit Bugzilla: 305859

CVE-2026-28871: @hamayanhamayan

### WebKit

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: Processing maliciously crafted web content may lead to an unexpected process crash

Description: The issue was addressed with improved memory handling.

WebKit Bugzilla: 306136

CVE-2026-20664: Daniel Rhea, Söhnke Benedikt Fischedick (Tripton), Emrovsky & Switch, Yevhen Pervushyn

WebKit Bugzilla: 307723

CVE-2026-28857: Narcis Oliveras Fontàs, Söhnke Benedikt Fischedick (Tripton), Daniel Rhea, Nathaniel Oh (@calysteon)

### WebKit

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: A malicious website may be able to access script message handlers intended for other origins

Description: A logic issue was addressed with improved state management.

WebKit Bugzilla: 307014

CVE-2026-28861: Hongze Wu and Shuaike Dong from Ant Group Infrastructure Security Team

### WebKit

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: A malicious website may be able to process restricted web content outside the sandbox

Description: The issue was addressed with improved memory handling.

WebKit Bugzilla: 308248

CVE-2026-28859: greenbynox, Arni Hardarson

### WebKit Sandboxing

Available for: iPhone 11 and later, iPad Pro 12.9-inch 3rd generation and later, iPad Pro 11-inch 1st generation and later, iPad Air 3rd generation and later, iPad 8th generation and later, and iPad mini 5th generation and later

Impact: A maliciously crafted webpage may be able to fingerprint the user

Description: An authorization issue was addressed with improved state management.

WebKit Bugzilla: 306827

CVE-2026-20691: Gongyu Ma (@Mezone0)

---

## Additional recognition

Apple publishes extended acknowledgments on the same page; omitted here for length—see the URL above.