# 05 · BIOS 设置对照表

装 macOS 前，BIOS 里有一批开关必须调对。**顺序很重要：先改 BIOS，再插 U 盘启动**，否则装到一半各种奇怪问题。

---

## 一、通用必改项

无论什么机型，这几项都要改：

| 项目（英文名可能不同） | 设为 | 为什么 |
|---|---|---|
| **Secure Boot**（安全启动） | **Disabled** | 不关的话 OpenCore 直接被拦，U 盘根本引导不起来 |
| **Fast Boot**（快速启动） | **Disabled** | 快速启动会跳过 USB 初始化，U 盘识别不到 |
| **CSM / Legacy Boot** | **Disabled** | macOS 只支持纯 UEFI |
| **Boot Mode** | **UEFI Only** | 同上 |
| **SATA / Storage Mode** | **AHCI** | RAID / RST / VMD 模式下安装器看不到硬盘 |
| **Intel VMD Controller** | **Disabled** | 同上，11 代以后的主板常见 |
| **Above 4G Decoding** | **Enabled** | 关闭会导致部分 A 卡不亮、大显存卡异常 |
| **Re-Size BAR / Smart Access Memory** | **Disabled** | macOS 下开了容易黑屏 |
| **VT-d / IOMMU** | **Disabled** | 减少干扰；装完稳定了可以再开 |
| **Serial Port**（串口） | **Disabled** | 会占用资源，导致卡住 |
| **Intel SGX** | **Disabled** | 无用 |
| **TPM / fTPM / PTT** | 可保留 | macOS 不用它；双系统装 Win11 的话必须留着 |

> 双系统注意：**关 Secure Boot 不影响 Windows 11**（Win11 只强制要求 TPM 2.0 + UEFI），所以可以放心关。

---

## 二、各品牌怎么进 BIOS

| 品牌 | 进 BIOS | 启动菜单 |
|---|---|---|
| 联想 笔记本（IdeaPad/小新） | `F2` 或 `Fn + F2` | `F12` |
| ThinkPad | `F1` 或 `Enter` 后按 `F1` | `F12` |
| 联想 台式 | `F1` 或 `F2` | `F12` |
| 戴尔 笔记本/台式 | `F2` | `F12` |
| 戴尔 服务器 | `F2` | `F11` |
| 惠普 消费本 | `F10`（开机先连按 `Esc`） | `F9` |
| 惠普 商用本（EliteBook） | `F10` | `F9` |
| 惠普 服务器 | `F9` | `F11` |
| 华硕 主板 | `Del` 或 `F2` | `F8` |
| 华硕 笔记本 | `F2` | `Esc` |
| 微星 主板 | `Del` | `F11` |
| 技嘉 主板 | `Del` | `F12` |
| 华擎 主板 | `F2` 或 `Del` | `F11` |
| 宏碁 | `F2` | `F12` |
| 华为 / 荣耀 笔记本 | `F2` | `F12` |
| 小米 笔记本 | `F2` | `F12` |
| 超微 服务器 | `Del` | `F11` |

---

## 三、特殊机型补充

### 联想 / ThinkPad

- **IdeaPad / 小新**：BIOS 里 `Configuration → SATA Controller Mode` 改成 `AHCI`。有些机型有 `Security → Secure Boot` 需要先设密码才能改。
- **ThinkPad**：`Security → Secure Boot → Disabled`；`Startup → UEFI/Legacy Boot → UEFI Only`；`Config → Storage → AHCI`；`Security → I/O Port Access` 里的指纹可以关掉。
- 部分联想笔记本有 **"Intel Platform Trust Technology"**，保留即可。

### 戴尔

- `Secure Boot → Disabled`（在 `Boot Settings` 里）
- `SATA Operation → AHCI`
- 老的 Latitude 有 `Legacy Option ROMs`，关掉
- 戴尔笔记本的 **TPM 不要关**（关了可能触发 BitLocker 恢复）

### 惠普

- 商用本有 **HP Sure Start / Sure Run**，某些型号会阻止修改引导，需要在 BIOS 里先关闭
- `Secure Boot Configuration → Legacy Support Disable` + `Secure Boot Disable`
- 惠普消费本（星系列）BIOS 选项很少，有些项是隐藏的

### 华硕

- 主板：`Advanced → System Agent (SA) Configuration → VT-d` 关闭；`Boot → CSM → Disabled`；`Advanced → PCI Subsystem Settings → Above 4G Decoding → Enabled`
- 部分华硕主板需要**先设管理员密码**才能关闭 Secure Boot
- ROG 笔记本：`Advanced → Graphics Configuration` 里可以切混合/独显

### 微星

- 主板默认开了 `MSI Fast Boot`，关掉
- `Settings → Advanced → Integrated Graphics Configuration` 里可以强制开启核显
- 部分型号 `CSM` 在 `Settings → Advanced → Windows OS Configuration` 里

### 技嘉

- `Boot → CSM Support → Disabled`
- `Peripherals → Above 4G Decoding → Enabled`
- `Settings → IO Ports → SATA Mode → AHCI`

### 服务器（Dell R730/R740、HP DL380、超微）

见 [04 服务器](04-server.md) 第三节的表格，除了通用项还要注意：

- `Boot Mode` 必须是 **UEFI**，不是 BIOS/Legacy
- `SATA Settings` 改成 **AHCI**，不是 RAID
- `Serial Communication` 关掉
- `Memory Test` 可以关掉加快启动（装完系统后）

---

## 四、找不到选项怎么办

### 1. 先解锁高级菜单

很多消费级笔记本把关键选项藏起来了：

| 品牌 | 解锁方式 |
|---|---|
| 联想 IdeaPad | BIOS 里 `Configuration` 下按 `Fn + Tab` 或 `F1` 等组合，不同型号不同 |
| 惠普 | 用 `H2OFFT` / `UEFI Variable` 工具改隐藏项 |
| 华硕 笔记本 | `Advanced` 里按 `F7` 解锁 |
| 微星 | `Advanced` 里按 `Ctrl + Shift + Alt + F2` |

如果实在找不到，可以用 **`CFGLock` 工具**（在 OpenCore 的 `Utilities` 里）读取/修改 UEFI 变量，但**风险较高，改错会变砖**，不建议新手碰。

### 2. CFG Lock 关不掉也没关系

很多教程强调必须关 CFG Lock，其实 OpenCore 有 `AppleCpuPmCfgLock` / `AppleXcpmCfgLock` 两个 quirk 可以直接绕过。OpCore 会自动设置。

### 3. 有些选项真的没有

比如某些品牌机的 `AHCI` 模式被彻底移除（只留 RAID）。这种机器**装不了**，或者需要刷修改过的 BIOS（风险极高，不建议）。

---

## 五、改完后的验证

重启进 U 盘前，快速确认：

- [ ] 关掉 Secure Boot 后，开机没有"安全启动违规"提示
- [ ] U 盘能在启动菜单里以 `UEFI:` 开头出现（不是 `Legacy:`）
- [ ] 硬盘模式是 AHCI（进 PE 或用 DiskGenius 能正常读到盘）

如果 U 盘在启动菜单里根本看不到，多半是：

1. U 盘没做成 UEFI 可引导（检查根目录有没有 `EFI/BOOT/BOOTx64.efi`）
2. Secure Boot 没关
3. 主板只认 FAT32 的 ESP 分区

---

下一步 → 回到对应机型教程装系统：[01](01-office-laptop.md) ｜ [02](02-gaming-pc.md) ｜ [03](03-allround-laptop.md) ｜ [04](04-server.md)
