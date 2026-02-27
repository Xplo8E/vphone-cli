# isSupported 深度逆向分析 — Virtualization.framework (macOS 26.3)

**Date:** 2026-02-26
**Binary:** Virtualization.framework (dyld shared cache, arm64e)
**Tool:** IDA Pro + MCP

---

## 1. 问题背景

macOS 26 beta 3 中，Apple 从 Virtualization.framework 的 `default_configuration_for_platform_version()` 静态配置表中将 platformVersion=3 (vresearch101) 的 **validity byte 设为 0**，导致 `VZMacHardwareModel.isSupported` 返回 `false`。通过 ObjC runtime method swizzling 可以绕过这一检查使 `validate()` 通过，但这并不能解决根本问题——真正的拦截发生在 hypervisor daemon 的 XPC 层（SEP coprocessor 被拒绝）。

---

## 2. isSupported 调用链总览

```
VZVirtualMachineConfiguration.validateWithError:
├── 检查 com.apple.security.virtualization entitlement
├── 检查 kern.hv_support sysctl
├── VZMacPlatformConfiguration.validate
│   ├── auxiliaryStorage != nil ?
│   ├── [hardwareModel isSupported]  ← 核心检查
│   └── machineIdentifier != nil ?
├── bootLoader.validate
├── _validateAcceleratorDevicesWithError:
│   └── [_VZMacVideoToolboxDeviceConfiguration _isSupported]
├── _validateCoprocessorsWithError:
│   └── platform 必须是 VZMacPlatformConfiguration
├── ... (graphics, storage, network, etc.)
└── validate 通过 → VZVirtualMachine init → start()
                                              └── XPC → hypervisor daemon
                                                  └── SEP 被拒绝 ← 真正的拦截点
```

---

## 3. -[VZMacHardwareModel isSupported] 汇编级分析

**地址:** `0x2301f520c` (34 instructions)

```asm
; 函数入口
LDR   X8, [X0, #0x38]        ; 加载 self._defaultPlatformConfiguration 指针
CBZ   X8, return_false        ; 如果 NULL → 直接返回 false

; 关键检查: validity byte
LDRB  W8, [X8, #0x24]        ; 加载 config + 0x24 (offset 36) 的 byte
CMP   W8, #1                 ; 必须等于 1
B.NE  return_false            ; 不等于 1 → 返回 false

; OS 版本检查
LDR   Q0, [X0, #0x10]        ; 加载 minimumSupportedHostOSVersion (major + minor)
LDR   X8, [X0, #0x20]        ; 加载 patchVersion
; 调用 [NSProcessInfo.processInfo isOperatingSystemAtLeastVersion:]
; 返回该结果

return_false:
  MOV   W0, #0
  RET
```

**三阶段检查:**
1. `self+0x38` (state pointer) 不为 NULL → 由 `default_configuration_for_platform_version()` 生成
2. `state[0x24]` (validity byte) 必须等于 1 → **这就是 Apple 关闭 PV=1/3 的开关**
3. 主机 macOS 版本 >= `_minimumSupportedHostOSVersion`

> 注意: IDA 反编译器将 `state[0x24]` 误标为 `->var4`，这是错误的。实际上是 offset 36 (0x24) 的 byte，不是 offset 4 的字段。

---

## 4. default_configuration_for_platform_version() 静态配置表

**地址:** `0x2301f4d90` (static local, runtime 初始化)

这个函数维护一个 4 个条目的静态数组，每条 **40 bytes**，按 platformVersion 索引：

```c
char* default_configuration_for_platform_version(unsigned int pv) {
    static ConfigEntry configs[4];  // 一次性初始化
    char* result = &configs[pv];    // 40 * pv 偏移

    if (pv >= 4) return NULL;       // 范围检查
    if (pv == 0) return NULL;       // PV=0 不支持
    return result;
}
```

### 配置条目结构 (40 bytes)

| Offset | Size | Field | 描述 |
|--------|------|-------|------|
| +0x00 | 4 | flags | 配置标识/能力位 |
| +0x04 | 4 | boardID | 默认 board ID |
| +0x08 | 8 | majorVersion | minimumSupportedHostOSVersion.major |
| +0x10 | 8 | minorVersion | minimumSupportedHostOSVersion.minor |
| +0x18 | 8 | patchVersion | minimumSupportedHostOSVersion.patch |
| +0x20 | 4 | extra_field | 附加数据 |
| **+0x24** | **1** | **validity** | **isSupported 开关 (必须 = 1)** |
| +0x25 | 3 | padding | 对齐填充 |

### 初始化赋值 (从反编译)

```c
// Entry 0 (PV=0): 全零 → 函数返回 NULL
// Entry 1 (PV=1):
configs[1].flags_boardID = 0xF800008103LL;  // flags=0x8103, boardID=0xF8
configs[1].majorVersion  = 12;               // macOS 12.0.0
configs[1].minorVersion  = 0;
configs[1].patchVersion  = 0;
// validity byte 未设置 → 保持为 0 ← PV=1 被禁用的原因!

// Entry 2 (PV=2):
configs[2].flags_boardID = 0x200000FE00LL;  // flags=0xFE00, boardID=0x20
configs[2].majorVersion  = 12;
configs[2].minorVersion  = 0;
configs[2].patchVersion  = 0;
configs[2].extra_field   = 1;
configs[2].validity      = 1;               // ← PV=2 被启用!

// Entry 3 (PV=3):
configs[3].flags_boardID = 0x900000FE01LL;  // flags=0xFE01, boardID=0x90
configs[3].majorVersion  = 15;               // macOS 15.0.0
configs[3].minorVersion  = 0;
configs[3].patchVersion  = 0;
configs[3].extra_field   = 2;
configs[3].validity      = (entitlements & 0x12) != 0;  // ← 条件启用!
```

### 完整配置表

| PV | flags | boardID | minOS | extra | validity byte | isSupported |
|:--:|:-----:|:-------:|:-----:|:-----:|:-------------:|:-----------:|
| 0 | — | — | — | — | — | N/A (NULL) |
| 1 | 0x8103 | **0xF8** (248) | 12.0.0 | 0 | **0** | **false** (已禁用) |
| **2** | 0xFE00 | **0x20** (32) | 12.0.0 | 1 | **1** | **true** |
| 3 | 0xFE01 | **0x90** (144) | 15.0.0 | 2 | **(ent & 0x12)?** | **条件** (需要 entitlements bit 1 或 4) |
| ≥4 | — | — | — | — | — | N/A (NULL) |

---

## 5. Entitlement 位图

`VzCore::VirtualizationEntitlements::from_current_process()` (地址 `0x23034aaf0`) 从当前进程的 SecTask 中读取 entitlement，构建位图。实际的 bitmap 构建在 `entitlements_from_task<Base::Security::SecTask>()` (地址 `0x23034a454`) 中完成。

### 完整 Entitlement 映射 (已确认)

| Bit | Mask | Entitlement | String 地址 | 说明 |
|:---:|:----:|:------------|:-----------:|:-----|
| 0 | 0x01 | `com.apple.security.virtualization` | `0x2303910b1` | 公开 entitlement (App Store 可用) |
| 1 | 0x02 | `com.apple.private.virtualization` | `0x230391090` | 私有; 同时设置 bit 0，所以实际值为 0x03 |
| 2 | 0x04 | `com.apple.vm.networking` | `0x2303910d3` | VM 网络功能 |
| 3 | 0x08 | `com.apple.private.ggdsw.GPUProcessProtectedContent` | `0x2303910eb` | GPU 保护内容直通 |
| 4 | 0x10 | `com.apple.private.virtualization.security-research` | `0x23039111e` | 安全研究 VM 支持 |
| 5 | 0x20 | `com.apple.private.virtualization.private-vsock` | `0x230391151` | 私有 vsock 通信 |

### entitlements_from_task 汇编逻辑

```c
uint32_t entitlements_from_task(SecTask task) {
    uint32_t result = 0;

    // 先检查私有 entitlement (grants bits 0+1)
    if (SecTaskValueForEntitlement(task, "com.apple.private.virtualization"))
        result = 3;  // 0x03 = bit 0 + bit 1
    else if (SecTaskValueForEntitlement(task, "com.apple.security.virtualization"))
        result = 1;  // 0x01 = bit 0 only

    if (SecTaskValueForEntitlement(task, "com.apple.vm.networking"))
        result |= 0x04;  // bit 2

    if (SecTaskValueForEntitlement(task, "com.apple.private.ggdsw.GPUProcessProtectedContent"))
        result |= 0x08;  // bit 3

    if (SecTaskValueForEntitlement(task, "com.apple.private.virtualization.security-research"))
        result |= 0x10;  // bit 4

    if (SecTaskValueForEntitlement(task, "com.apple.private.virtualization.private-vsock"))
        result |= 0x20;  // bit 5

    return result;
}
```

### PV=3 的 Entitlement 条件

PV=3 的 validity 条件是 `(entitlements & 0x12) != 0`，即 `0x12 = 0x02 | 0x10` = bit 1 + bit 4:

| 满足条件的 Entitlement | Bit | 说明 |
|:----------------------:|:---:|:-----|
| `com.apple.private.virtualization` | bit 1 (0x02) | Apple 内部通用私有虚拟化 |
| `com.apple.private.virtualization.security-research` | bit 4 (0x10) | PCC 安全研究专用 |

**任一**即可使 PV=3 的 validity byte = 1。

### 当前进程的 Entitlement 状态

| 场景 | Entitlement Bitmap | PV=3 validity |
|:-----|:------------------:|:-------------:|
| super-tart (无签名, SIP off) | 0x00 | **0** (false) |
| super-tart + `com.apple.security.virtualization` | 0x01 | **0** (0x01 & 0x12 = 0) |
| Apple 签名 + `com.apple.private.virtualization` | 0x03 | **1** (0x03 & 0x12 = 0x02 ≠ 0) |
| Apple 签名 + `security-research` entitlement | 0x11 | **1** (0x11 & 0x12 = 0x10 ≠ 0) |

在 macOS 26.3 上，即使 SIP 关闭，ad-hoc 签名的进程也没有 private entitlement，所以 PV=3 对非 Apple 签名的二进制有效为 **always false**。

### 运行时验证 (Runtime Verification)

使用 `verify_entitlements.sh` 测试工具验证: 编译一个加载 Virtualization.framework 并触发 `from_current_process()` 的 dummy 进程，用不同 entitlements 签名后启动，通过 lldb attach 读取静态变量 `from_current_process()::entitlements` 的值。

> 注意: `from_current_process()` 是 void 函数，将 bitmap 存储在 C++ static local 变量中 (地址 `0x294f49a40`，`__DATA.__bss+1712`)，通过 `__cxa_guard` 实现线程安全的一次性初始化。bitmap 不在返回值寄存器中。

```
=== Test 1: No entitlements (baseline) ===
  bitmap = 0x00

=== Test 2: Each entitlement individually ===
  Entitlement                                                  Bitmap
  ------------------------------------------------------------ ------
  com.apple.security.virtualization                            0x01
  com.apple.private.virtualization                             0x03
  com.apple.vm.networking                                      0x04
  com.apple.private.ggdsw.GPUProcessProtectedContent           0x08
  com.apple.private.virtualization.security-research           0x10
  com.apple.private.virtualization.private-vsock               0x20

=== Test 3: Cumulative (add entitlements one by one) ===
  #    Added Entitlement                                            Bitmap
  ---- ------------------------------------------------------------ ------
  1    com.apple.security.virtualization                            0x01
  2    com.apple.private.virtualization                             0x03
  3    com.apple.vm.networking                                      0x07
  4    com.apple.private.ggdsw.GPUProcessProtectedContent           0x0f
  5    com.apple.private.virtualization.security-research           0x1f
  6    com.apple.private.virtualization.private-vsock               0x3f

=== Test 4: All entitlements ===
  bitmap = 0x3f (expected 0x3f)
```

**所有 6 个 bit 位与 IDA 逆向分析完全一致。** 累加测试确认 OR 行为正确，`com.apple.private.virtualization` 同时设置 bit 0+1 (`0x03`)。

### XPC Daemon 及其他 Entitlements 扫描

XPC daemon (`com.apple.Virtualization.VirtualMachine.xpc`) 本身拥有 28 个 entitlements。将所有 daemon entitlements 以及 Virtualization.framework 二进制中找到的 entitlement-like 字符串全部逐一测试:

```
=== XPC daemon entitlements (not in known 6) ===
  Entitlement                                                  Bitmap
  ------------------------------------------------------------ ------
  com.apple.ane.iokit-user-access                              0x00
  com.apple.aned.private.adapterWeight.allow                   0x00
  com.apple.aned.private.allow                                 0x00
  com.apple.developer.kernel.increased-memory-limit            0x00
  com.apple.private.AppleVirtualPlatformIdentity               0x00
  com.apple.private.FairPlayIOKitUserClient.Virtual.access     0x00
  com.apple.private.PCIPassthrough.access                      0x00
  com.apple.private.ane.privileged-vm-client                   0x00
  com.apple.private.apfs.no-padding                            0x00
  com.apple.private.biometrickit.allow-match                   0x00
  com.apple.private.fpsd.client                                0x00
  com.apple.private.hypervisor                                 0x00
  com.apple.private.proreshw                                   0x00
  com.apple.private.security.message-filter                    0x00
  com.apple.private.system-keychain                            0x00
  com.apple.private.vfs.open-by-id                             0x00
  com.apple.private.virtualization.linux-gpu-support           0x00
  com.apple.private.virtualization.plugin-loader               0x00
  com.apple.private.xpc.domain-extension                       0x00
  com.apple.security.hardened-process                          0x00
  com.apple.security.hypervisor                                0x00
  com.apple.usb.hostcontrollerinterface                        0x00

=== All entitlements combined ===
  bitmap = 0x3f
```

**确认: bitmap 只有 6 bit (0x3f)。** XPC daemon 的 22 个其他 entitlements（包括 `com.apple.private.hypervisor`、`com.apple.security.hypervisor`、`com.apple.private.virtualization.linux-gpu-support`、`com.apple.private.virtualization.plugin-loader` 等）均不影响 bitmap。即使同时赋予全部 28 个 entitlements，bitmap 仍然只到 `0x3f`。

> entitlement 检查发生在调用方进程 (caller) 的 Virtualization.framework 中，不在 XPC daemon 端。daemon 不做 entitlement bitmap 检查——SEP coprocessor 的拒绝是 daemon 端的独立验证逻辑，与 entitlement bitmap 无关。

### XPC Daemon 完整 Entitlement 列表

`com.apple.Virtualization.VirtualMachine.xpc` 的签名包含以下 entitlements:

```
adi-client = "3894944679"
com.apple.ane.iokit-user-access = true
com.apple.aned.private.adapterWeight.allow = true
com.apple.aned.private.allow = true
com.apple.developer.kernel.increased-memory-limit = true
com.apple.private.AppleVirtualPlatformIdentity = true
com.apple.private.FairPlayIOKitUserClient.Virtual.access = true
com.apple.private.PCIPassthrough.access = true
com.apple.private.ane.privileged-vm-client = true
com.apple.private.apfs.no-padding = true
com.apple.private.biometrickit.allow-match = true
com.apple.private.fpsd.client = true
com.apple.private.ggdsw.GPUProcessProtectedContent = true
com.apple.private.hypervisor = true
com.apple.private.proreshw = true
com.apple.private.security.message-filter = true
com.apple.private.system-keychain = true
com.apple.private.vfs.open-by-id = true
com.apple.private.virtualization = true
com.apple.private.virtualization.linux-gpu-support = true
com.apple.private.virtualization.plugin-loader = true
com.apple.private.xpc.domain-extension = true
com.apple.security.hardened-process = true
com.apple.security.hypervisor = true
com.apple.usb.hostcontrollerinterface = true
com.apple.vm.networking = true
keychain-access-groups = ["com.apple.Virtualization.snapshot.encryption.keychain-access-group"]
lskdd-client = "4039799425"
```

---

## 6. VZMacHardwareModel 对象布局

从 `_initWithDescriptor:` (地址 `0x2301f4bdc`) 和 accessor 方法反推：

| Offset | Size | Field | 来源 |
|--------|------|-------|------|
| +0x00 | 8 | isa (ObjC) | runtime |
| +0x08 | 8 | _isa (platform ISA) | descriptor[56] |
| +0x10 | 8 | minOSVersion.major | config[8] 或 descriptor[24] |
| +0x18 | 8 | minOSVersion.minor | config[16] 或 descriptor[32] |
| +0x20 | 8 | minOSVersion.patch | config[24] 或 descriptor[40] |
| +0x28 | 4 | _boardID | config[4] 或 descriptor[16] |
| +0x2C | 4 | _variantID | descriptor |
| +0x30 | 8 | _variantName | descriptor (NSString*) |
| +0x38 | 8 | _defaultPlatformConfiguration | `default_configuration_for_platform_version(pv)` |
| +0x40 | 4 | _platformVersion | descriptor[8] |
| +0x48 | 8 | 附加字段 (1 或 2) | 基于 ISA |

### _isa 映射表

`_platform` 方法使用 ISA 值索引查找表 (地址 `0x23037BEA8`):

| ISA 输入 | 映射值 | 用途 |
|:--------:|:------:|:----:|
| 0 | 2 | 标准 |
| 1 | 0 | 默认 (省略序列化) |
| 2 | 1 | vresearch |
| ≥3 | — | 抛出 "Invalid ISA" |

特殊值: `_isa == 0x1000 (4096)` → 返回 1, `_isa == 0x1001 (4097)` → 返回 2

---

## 7. dataRepresentation Plist 格式

`-[VZMacHardwareModel dataRepresentation]` (地址 `0x2301f4eb8`) 序列化为 bplist:

```plist
{
    DataRepresentationVersion = <uint>;  // 0, 1, 或 2
    PlatformVersion = <uint>;            // 1, 2, 3
    MinimumSupportedOS = (<int>, <int>, <int>);  // [major, minor, patch]
    ISA = <uint>;                        // 仅当 != 1 时序列化
    BoardID = <uint>;                    // 仅当与默认 config 不同时序列化
    VariantID = <uint>;                  // 仅当非零时序列化
    VariantName = <string>;              // 仅当非 nil 时序列化
}
```

`initWithDataRepresentation:` (地址 `0x2301f457c`) 反序列化时：
- 检查 DataRepresentationVersion ≤ 2
- PlatformVersion 必须 engaged
- MinimumSupportedOS 必须是长度为 3 的数组
- ISA 默认值为 1
- BoardID/VariantID/VariantName 可选

---

## 8. _defaultBoardIDForPlatformVersion: 的连带影响

地址 `0x2301f52f8`:

```c
unsigned int _defaultBoardIDForPlatformVersion(unsigned int pv) {
    char* config = default_configuration_for_platform_version(pv);
    if (config && config[36] == 1)   // 同一个 validity byte!
        return *(uint32_t*)(config + 4);  // 返回 boardID
    else
        return 0xFFFFFFFF;  // -1, 无效
}
```

对于 PV=3: validity=0 → 返回 **0xFFFFFFFF** 而非 0x90。这意味着即使 swizzle 了 `isSupported`，某些依赖 `_defaultBoardIDForPlatformVersion:` 的内部路径也会得到错误的 boardID。

---

## 9. 验证链中的所有 isSupported 检查

| 方法 | 地址 | 检查内容 | 是否受 swizzle 影响 |
|------|------|---------|:------------------:|
| `+[VZVirtualMachine isSupported]` | `0x23028e6dc` | `kern.hv_support` sysctl | 否 (class method) |
| `-[VZMacHardwareModel isSupported]` | `0x2301f520c` | validity byte + OS 版本 | **是 (被 swizzle)** |
| `+[_VZMacVideoToolboxDeviceConfiguration _isSupported]` | `0x2301ceb34` | 两个全局变量 (VT 初始化) | 否 (class method) |
| `-[VZMacOSRestoreImage isSupported]` | `0x2301c7a14` | mostFeaturefulSupportedConfiguration != nil | 间接受影响 |

### Swizzle 覆盖的调用点

| 调用者 | 地址 | 用途 |
|--------|------|------|
| `-[VZMacPlatformConfiguration validate]` | `0x2301f7f48` | 验证 hardwareModel 是否支持 |
| `-[VZMacAuxiliaryStorage initCreatingStorageAt:hardwareModel:options:error:]` | `0x2301ef428` | 创建 NVRAM 存储前检查 |
| `-[VZMacOSRestoreImage mostFeaturefulSupportedConfiguration]` | `0x2301c7b20` | 遍历 restore image 中的 config |

### Swizzle 不覆盖的检查

| 检查 | 位置 | 影响 |
|------|------|------|
| `_defaultBoardIDForPlatformVersion:` 的 validity check | `0x2301f5308` | 返回 -1 代替正确的 boardID |
| PV=3 的 config data (boardID=0x90, minOS=15.0) 虽然存在但标记无效 | config table | 某些内部路径可能使用默认值 |
| XPC daemon 的服务端验证 | `com.apple.Virtualization.VirtualMachine` | **不受 swizzle 影响** |

---

## 10. _platform 方法如何构建 VM 配置

`-[VZMacPlatformConfiguration _platform]` (地址 `0x2301f661c`, ~3584 bytes, 极大函数) 构建发送给 XPC daemon 的平台配置：

```
读取流程:
1. 打开 auxiliaryStorage 文件 → flock 锁定
2. 读取 machineIdentifier → ECID, serialNumber
3. 读取 hardwareModel._variantName
4. 检查 _isFairPlayEnabled, _hostAttributeShareOptions
5. 构建 host/guest service allow lists
6. 读取 encryption wrapping key
7. 获取 hardwareModel._isa → 查 dword_23037BEA8[] 映射
8. 获取 hardwareModel._boardID
9. 获取 hardwareModel._variantID
10. 获取 hardwareModel._platformVersion
11. 读取 machdep.cpu.brand_string → 附加 " (Virtual)"
12. 读取 RegionInfo → MGCopyAnswer
13. 构建 VzCore::VirtualMachineConfiguration::Platforms::Mac 对象
14. 通过 XPC 发送给 hypervisor daemon
```

关键: 这里直接从 hardware model 读取 boardID、ISA、platformVersion，**不再**检查 validity byte。所以 swizzle 后这些值正确传递到 daemon。

---

## 11. 真正的拦截点: Hypervisor Daemon XPC

从 super-tart 的测试结果（见 `vrevm_analysis_macos26b3.md`）：

| 配置 | isSupported | validate() | VZVirtualMachine init | start() |
|------|:-----------:|:----------:|:---------------------:|:-------:|
| PV=3 + boardID=0x90 (无 swizzle) | **false** | FAIL | — | — |
| PV=3 + boardID=0x90 + swizzle | true | PASS | PASS | 见下表 |
| PV=2 + boardID=0x90 (无 swizzle) | true | PASS | PASS | 见下表 |

| 配置 | SEP | start() 结果 |
|------|-----|:------------:|
| PV=3 + swizzle + SEP (full) | `_VZSEPCoprocessorConfiguration` + ROM + debug | **FAIL**: "coprocessor configuration is invalid" |
| PV=3 + swizzle + SEP (minimal) | `_VZSEPCoprocessorConfiguration` (仅 storage) | **FAIL**: 同上 |
| PV=2 + SEP (full) | 同上 | **FAIL**: 同上 |
| PV=3 + swizzle + **无 SEP** | 不调用 `_setCoprocessors` | **PASS** → DFU 模式 |
| PV=2 + **无 SEP** | 不调用 `_setCoprocessors` | **PASS** → DFU 模式 |

**结论:** SEP coprocessor 被 hypervisor daemon 在 `start()` XPC 调用中拒绝，这与 `isSupported` 完全无关。这是一个独立的限制。

---

## 12. Framework 层的 Coprocessor 验证

`-[VZVirtualMachineConfiguration _validateCoprocessorsWithError:]` (地址 `0x230255748`) 只做了一个简单检查:

```c
if (coprocessors.count > 0) {
    if (!(platform isKindOfClass: VZMacPlatformConfiguration))
        error("Coprocessors are only supported on Apple platforms.");
        return false;
    }
}
return true;
```

这个检查在 `validateWithError:` 中通过了。真正的 SEP 拒绝发生在 daemon 端。

`-[_VZSEPCoprocessorConfiguration _coprocessor]` (地址 `0x2301d4a7c`) 做了:
1. 打开 ROM binary URL → 如果失败报错
2. 打开 SEP storage file → 如果失败报错
3. 初始化 debug stub → 如果失败报错
4. 构建 `VzCore::VirtualMachineConfiguration::Coprocessor` 对象

这些都是文件操作，不涉及平台验证。

---

## 13. 根因分析总结

```
isSupported = false 的根因:
┌──────────────────────────────────────────────────┐
│ default_configuration_for_platform_version()     │
│ 静态表中 PV=3 的 validity byte (offset 0x24)     │
│ 在 macOS 26.3 中被设为:                          │
│   (entitlements & 0x12) != 0                     │
│ 而普通进程 entitlements = 0x01 → 0x01 & 0x12 = 0 │
│ → validity = 0 → isSupported = false             │
└──────────────────────────────────────────────────┘
                    │
                    ▼
         Swizzle 绕过了这一层
                    │
                    ▼
┌──────────────────────────────────────────────────┐
│ VM 启动后的真正问题:                              │
│                                                  │
│ 1. SEP Coprocessor 被 daemon 拒绝               │
│    "The coprocessor configuration is invalid."   │
│    → 与 isSupported 无关                         │
│    → 发生在 XPC daemon 端                        │
│    → PV=2 和 PV=3 都受影响                       │
│                                                  │
│ 2. 无 SEP 时 VM 可以进入 DFU                     │
│    → 但 firmware bootchain 需要 SEP 进行         │
│      secure boot / data protection               │
│    → kernel 最终会 panic                         │
└──────────────────────────────────────────────────┘
```

---

## 14. 可能的解决方案

### 方案 A: 降级到 macOS 26 beta 2
在 beta 2 中 PV=3 和 SEP coprocessor 都是支持的。最简单的解决方案。

### 方案 B: 逆向 XPC daemon 的 SEP 验证
`com.apple.Virtualization.VirtualMachine.xpc` 服务有自己的验证逻辑。需要:
1. 从 dyld shared cache 或 XPC bundle 中提取 daemon 二进制
2. 找到处理 `start_or_restore` XPC 消息的函数
3. 定位 coprocessor 验证检查
4. 通过 DYLD_INSERT_LIBRARIES 或二进制 patch 绕过

### 方案 C: 使用 _coprocessorStorageFileDescriptor 替代
`VZVirtualMachineConfiguration` 有一个 `_coprocessorStorageFileDescriptor` 属性，可能是绕过 `_VZSEPCoprocessorConfiguration` 的替代路径。

### 方案 D: 给 super-tart 签名 private entitlements
如果有 Apple Developer 证书:
- 添加 `com.apple.private.virtualization` → 使 PV=3 原生 supported
- 但可能仍无法解决 daemon 端的 SEP 限制

### 方案 E: 在无 SEP 的情况下修改 firmware
修改 iBSS/iBEC/LLB/kernel 的 SEP 相关检查，使 bootchain 在无 SEP 环境下也能继续。但这需要大量 firmware 逆向工作。

---

## 15. 关键地址索引

| 符号 | 地址 | 用途 |
|------|------|------|
| `-[VZMacHardwareModel isSupported]` | `0x2301f520c` | validity + OS 版本检查 |
| `default_configuration_for_platform_version` | `0x2301f4d90` | 静态配置表 |
| `-[VZMacHardwareModel _initWithDescriptor:]` | `0x2301f4bdc` | 初始化 hardware model |
| `-[VZMacHardwareModel initWithDataRepresentation:]` | `0x2301f457c` | 从 plist 反序列化 |
| `-[VZMacHardwareModel dataRepresentation]` | `0x2301f4eb8` | 序列化为 plist |
| `+[VZMacHardwareModel _defaultHardwareModel]` | `0x2301f5334` | 创建默认 hardware model (PV=1) |
| `+[VZMacHardwareModel _hardwareModelWithDescriptor:]` | `0x2301f5434` | 从 descriptor 创建 model |
| `+[VZMacHardwareModel _defaultBoardIDForPlatformVersion:]` | `0x2301f52f8` | 获取默认 boardID (也检查 validity!) |
| `-[VZMacPlatformConfiguration validate]` | `0x2301f7f10` | 平台验证 (调用 isSupported) |
| `-[VZMacPlatformConfiguration _platform]` | `0x2301f661c` | 构建 XPC 发送的平台配置 |
| `-[VZVirtualMachineConfiguration validateWithError:]` | `0x2302525ac` | 主验证入口 |
| `-[VZVirtualMachineConfiguration _validateCoprocessorsWithError:]` | `0x230255748` | Coprocessor 验证 (仅检查平台类型) |
| `VzCore::VirtualizationEntitlements::from_current_process` | `0x23034aaf0` | 读取进程 entitlements |
| `entitlements_from_task<SecTask>` | `0x23034a454` | Entitlement 位图构建 |
| `+[VZVirtualMachine isSupported]` | `0x23028e6dc` | HV 支持检查 (kern.hv_support) |
| `-[_VZSEPCoprocessorConfiguration _coprocessor]` | `0x2301d4a7c` | SEP 配置对象构建 |
| ISA 查找表 | `0x23037BEA8` | ISA → platform config 映射 ({2, 0, 1}) |
