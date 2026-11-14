# 02 · 游戏电脑（台式机）

**难度 ★★★ ｜ 推荐度：中 ｜ 成败几乎只取决于显卡**

台式机的优势是硬件可换：显卡不行就换显卡，网卡不行就插一张，比笔记本灵活得多。难点也在这——**一台游戏电脑最贵的部件往往正好是 macOS 最不支持的部件**。

---

## 一、先看显卡：这是唯一重要的事

### AMD 显卡（黑苹果首选）

| 系列 | 型号 | 支持情况 |
|---|---|---|
| Navi 21 | RX 6800 / 6800XT / 6900XT | ✅ 免驱，Big Sur 起，性能强 |
| Navi 22 / 23 | RX 6700 / 6750XT / 6600 / 6600XT | ✅ 免驱，Monterey 12.2 起 |
| Navi 1x | RX 5500XT / 5600XT / 5700 / 5700XT | ✅ 免驱，Catalina 起 |
| Vega | Vega 56 / 64 / Radeon VII | ✅ 免驱，Mojave 起 |
| Polaris | RX 470/480/570/580/590 | ✅ 免驱，High Sierra 起，性价比之王 |
| **Navi 24** | **RX 6400 / 6500XT** | ❌ **不支持**，别买 |
| **RDNA3** | **RX 7600 / 7800XT / 7900XTX** | ❌ **不支持** |

### NVIDIA 显卡（基本别想）

| 系列 | 支持情况 |
|---|---|
| RTX 50 / 40 / 30 / 20 系 | ❌ 完全不支持，永远不会有驱动 |
| GTX 16 系 | ❌ 不支持 |
| GTX 10 系（Pascal） | ⚠️ 只能到 **High Sierra 10.13.6**，需要 Web Driver，系统太老，不实用 |
| GTX 9 系及更早（Kepler） | ⚠️ 能到 Big Sur，同样偏老 |

**结论：如果你用的是 N 卡游戏电脑，只有两条路** —— 加一块 A 卡，或者只用核显。

### 关键陷阱：核显也可能不支持

很多游戏主机是「11 代 i5 + RTX 3060」这种组合。这时候：

- RTX 3060 → 不支持
- 11 代核显 UHD 730/750 → 也不支持

**两个都红，就是彻底装不了**，连装上去看个桌面都不行。

反过来，「10 代 i5 + RTX 3060」是有戏的：用 UHD 630 核显输出，虽然不能玩游戏，但能正常办公、看视频、跑开发环境。

> 判断方法很简单：跑一遍 `OpCore-Simplify`，看 GPU 那几行有没有**至少一个绿的、并且能接显示器**。

---

## 二、你的机器属于哪一档

| 配置 | 结论 | 建议 |
|---|---|---|
| AMD RX 580 / 6600 / 6800 + 任意 Intel CPU | ✅ 完美 | 直接装，体验接近白苹果 |
| 10 代及更早 Intel + N 卡 | ⚠️ 只能核显 | 能装，适合办公/开发，不适合游戏 |
| 11 代及更新 Intel + N 卡 | ❌ 装不了 | 加一块 RX 6600，或放弃 |
| AMD CPU（Ryzen）+ A 卡 | ⚠️ 可以，但要打 AMD 内核补丁 | 能用，部分软件（Adobe、虚拟机）兼容性差 |
| AMD CPU + N 卡 | ❌ 装不了 | — |

**AMD CPU 的额外代价**：需要 `AMD Vanilla` 内核补丁，装完能用，但：

- Adobe 全家桶部分版本崩溃
- Docker / 虚拟机（需要虚拟化的）经常不工作
- 部分游戏反作弊会拦
- 系统更新后偶尔要重新打补丁

如果你只是办公、写代码、剪视频（Final Cut），AMD CPU 可以接受；要跑 Adobe 或虚拟机，老实选 Intel。

---

## 三、安装步骤

前置：完成 [00 准备工作](00-prepare.md) 第 1–5 步。

### 1. BIOS 设置（台式机主板）

开机狂按 `Del`（华硕/微星/技嘉/华擎）或 `F2`：

| 项目 | 设为 | 说明 |
|---|---|---|
| Secure Boot | **Disabled** | 必须关 |
| CSM / Legacy Boot | **Disabled** | 纯 UEFI |
| Above 4G Decoding | **Enabled** | 必须开，否则 A 卡可能不亮 |
| Re-Size BAR Support | **Disabled** | macOS 不友好，开了容易黑屏 |
| Intel VT-d | **Disabled** | 减少干扰 |
| XMP / EXPO | 可以开 | 内存超频不影响 |
| TPM / fTPM | 可以保留 | macOS 不用它，Win11 需要 |
| Fast Boot | Disabled | |
| 核显（Integrated Graphics） | **Enabled / Auto** | 即使插了独显也建议开着，方便排错 |

**微星主板** 还有个 `MSI Fast Boot` 和 `Windows OS Configuration → WHQL`，都关掉。
**华硕主板** 的 `Advanced → System Agent → VT-d` 和 `PCH Storage Configuration` 注意一下。
**技嘉主板** 部分型号 `CSM Support` 在 `Boot` 菜单里。

### 2. 硬盘怎么安排

推荐三种方案，按推荐度排序：

**方案 A：两块 SSD（最佳）**
```
SSD 1：Windows（自带 EFI）
SSD 2：macOS（EFI 放 OpenCore）
```
物理隔离，互不影响，随便折腾。OpenCore 菜单里能直接看到 Windows 启动项。

**方案 B：一块 SSD 双分区**
用 DiskGenius 从 Windows 分区尾部压缩出 ≥ 100GB 未分配空间，安装时在磁盘工具里抹成 APFS。
风险：Windows 更新偶尔会动分区表；重装 Windows 可能覆盖引导。

**方案 C：全盘给 macOS**
不保留 Windows。适合专门做剪辑/开发的工作站。

### 3. 装系统

流程同 [01 办公笔记本第三节](01-office-laptop.md#2-装系统)，注意这几点：

- 磁盘工具里如果看不到硬盘 → 回 BIOS 确认 SATA 是 **AHCI**、没有开 **Intel VMD**
- 如果用的是 NVMe 且主板有多个 M.2 槽，**优先插 CPU 直连的那个槽**
- 装的时候把其他硬盘的数据线拔掉（防止误格式化），这是最保险的做法

### 4. 独立显卡的特别注意

**如果你是 A 卡 + Intel 核显：**

OpCore 默认可能把核显设成"无头模式"（headless，只用来做视频编码加速），显示走独显。这是对的。

但如果装上后**黑屏、只有独显在工作、进不去系统**，试试在 BIOS 里把主显示输出（Primary Display / Init Display First）改成 `PCIE` 或 `PEG`。

**如果你是 N 卡 + 核显（用核显输出）：**

必须在 BIOS 里：

- `Primary Display` 设为 **IGFX / 核显**
- 把显示器线**插在主板上的 HDMI/DP 口**，不是显卡上

然后在 EFI 里禁用独显（OpCore 会自动加，也可以在 `DeviceProperties` 里确认有 `disable-gpu`）。

> 这一步很多人搞错：显示器插在独显上，核显再强也点不亮。

---

## 四、台式机特有的坑

### 1. 声卡没声音

主板集成声卡基本是 Realtek ALC 系列（ALC892 / ALC897 / ALC1200 / ALC1220 / ALC4080）。

用 `AppleALC` + 正确的 `layout-id`。查表：<https://github.com/acidanthera/AppleALC/wiki/Supported-codecs>

- ALC1220 常用 `layout-id = 1` 或 `7`
- ALC897 常用 `layout-id = 11` 或 `69`
- ALC4080（很多 Z690/Z790 主板）较麻烦，可能只能用 USB 声卡

改 `layout-id` 在 `config.plist` 的 `DeviceProperties → Add → PciRoot(0x0)/Pci(0x1f,0x3)` 下面，或者在 OpCore 生成时选对声卡型号。

### 2. 网卡

| 网卡 | 情况 |
|---|---|
| Intel I219-V | 免驱 |
| Intel I225-V | 需要补丁，Ventura 之后基本可用 |
| Realtek RTL8125（2.5G） | 需要 `LucyRTL8125Ethernet.kext` |
| Realtek RTL8111 | 需要 `RealtekRTL8111.kext` |

### 3. 无线网卡（台式机最容易解决）

主板自带的 Intel AX200/AX201 能用但没隔空投送。**强烈建议**直接买：

- **Fenvi T919**（PCIe 转 BCM94360CD，免驱，全功能，约 200 元）
- 或 `BCM94360CD` + PCIe 转接卡

插上就能用隔空投送、接力、随航、通用控制。这是台式机最划算的升级。

> 注意：买之前确认主板有空的 PCIe x1 插槽。

### 4. 睡眠

台式机睡眠通常比笔记本好搞。如果一睡就重启：

- 关掉 BIOS 里的 `ErP` / `Wake on LAN`
- 在 EFI 里确认有 `SSDT-PLUG`（电源管理）和 USB 映射
- 网卡的"网络唤醒"在系统设置里关掉

### 5. 多显示器与高刷

A 卡多显示器基本没问题。高刷屏幕用 DP 线，HDMI 有时只能到 60Hz。

如果接了 4K 屏但只显示 1080p，检查是不是用了转接头，或者显示器 EDID 没读到。

---

## 五、推荐的三种配置

| 档位 | 配置 | 能干什么 |
|---|---|---|
| 入门（约 3000） | i5-10400 + RX 580 8G + B460 | 办公、4K 视频、轻度剪辑 |
| 主流（约 6000） | i5-12400 + RX 6600 + B660 | 日常全能，剪辑流畅，不能玩 3A（macOS 上游戏本来也少） |
| 高配（约 12000） | i7-13700K + RX 6800XT + Z790 | 4K 剪辑、3D、开发全栈 |

> 注意：**12400 的核显 UHD 730 是不被支持的**，但你有 RX 6600，所以没问题。如果哪天把 A 卡拔了，系统就进不去了。

---

## 六、装完检查清单

- [ ] 显卡硬件加速正常（关于本机里能看到正确型号）
- [ ] 声音正常，前置面板也能用
- [ ] 有线网络通
- [ ] 睡眠能睡能醒
- [ ] 双系统能在 OpenCore 菜单里互相切换
- [ ] Windows 没被搞坏（进得去、能正常用）

---

下一篇 → [07 安装后优化](07-post-install.md)。显卡相关故障 → [06 故障速查](06-troubleshooting.md)。
