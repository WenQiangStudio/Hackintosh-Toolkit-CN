# 黑苹果工具包 · 中文安装指南

一套自带工具、按机型分类的 Hackintosh（黑苹果）安装资料包。目标只有一个：**让你少走弯路，先判断能不能装，再决定怎么装。**

- 工具：`OpCore-Simplify`（自动生成 OpenCore EFI）+ `gibMacOS`（从苹果服务器下载镜像）
- 教程：办公笔记本 / 游戏电脑 / 全能本 / 服务器，四条独立路线
- 附带：兼容性速查表、BIOS 设置对照、故障速查、安装后驱动微调

---

## ⚠️ 开始之前，请先读这三条

1. **风险评估先于一切**。分区、格式化、改 BIOS 都可能让数据不可恢复。**请先把重要文件备份到另一块硬盘或云盘。** 推荐做法：macOS 单独装一块 SSD，和 Windows 物理隔离。
2. **许可提醒**。macOS 的最终用户许可协议（EULA）限定只能在 Apple 硬件上运行，在普通 PC 上安装属于违反协议的行为（不涉及破解正版镜像，安装包本身是苹果免费公开的）。是否进行请自行判断并承担相应责任，本仓库仅整理公开资料与开源工具。
3. **不是所有电脑都能装**。显卡、网卡、硬盘控制器这三样经常是硬门槛，详见下面的「三条红线」。

---

## 🚦 三条红线：30 秒判断能不能装

不满足就直接放弃，省下几小时：

| 红线 | 能装 | 不能装 |
|---|---|---|
| **显卡（决定成败）** | AMD RX 400/500/5000/6000 系；Intel 核显（10 代 Ice Lake 及更早） | NVIDIA RTX 20/30/40/50 系**全部无解**；AMD RX 7000 系（RDNA3）无解；Intel 11 代及更新的核显无解 |
| **硬盘控制器** | SATA / AHCI / 普通 NVMe | **Intel VMD / RST 模式**必须先关掉，否则安装器看不到硬盘 |
| **无线网卡** | Broadcom BCM94360 系列（免驱，隔空投送全功能）、Intel 网卡（能上网，但无隔空投送） | 部分 Realtek / 高通网卡无解，需换卡或买 USB 网卡 |

> 拿不准就跑一遍 `tools/OpCore-Simplify`，它会直接给你的每个硬件标绿灯/红灯。

---

## 🧭 我该看哪一篇？

| 你的电脑 | 典型例子 | 难度 | 推荐度 | 教程 |
|---|---|---|---|---|
| 办公笔记本 | ThinkPad T480/X1C、小新 Air、Latitude、EliteBook | ★★☆ | 高，最成熟 | [01 办公笔记本](docs/01-office-laptop.md) |
| 游戏电脑（台式） | i5/i7 + 独显、自己攒的机器 | ★★★ | 中，看显卡 | [02 游戏电脑](docs/02-gaming-pc.md) |
| 全能本 / 游戏本 | 拯救者、幻 16、天选、暗影精灵 | ★★★★★ | 低，多数装不了 | [03 全能本](docs/03-allround-laptop.md) |
| 服务器 | Dell R730/R740、HP DL380、超微、自建 Xeon | ★★★★ | 中，看用途 | [04 服务器](docs/04-server.md) |

**如果你的是笔记本但带独立显卡**（大多数 2020 年后的轻薄本和游戏本），请先看 [03 全能本](docs/03-allround-laptop.md) 里的「先做这个判断」，再决定要不要继续。

---

## 🗺️ 通用流程（所有机型都走这 7 步）

```
① 备份数据  →  ② 跑兼容性检查  →  ③ 装 Python + 生成 EFI  →  ④ 做启动 U 盘
                    ↓
⑦ 装完微调  ←  ⑥ 进安装器装系统  ←  ⑤ 改 BIOS 设置
```

| 步骤 | 做什么 | 看这篇 |
|---|---|---|
| ① | 备份，准备一个 16GB 以上 U 盘（会被格式化） | [00 准备工作](docs/00-prepare.md) |
| ② | 运行 OpCore-Simplify，确认红绿灯，它会推荐适合你的 macOS 版本 | [00 准备工作](docs/00-prepare.md) |
| ③ | 同上，生成 EFI 文件夹 | [00 准备工作](docs/00-prepare.md) |
| ④ | 写入 OpenCore 引导 + 下载恢复镜像 | 各机型教程 |
| ⑤ | 关安全启动、VMD、开 UEFI 等 | [05 BIOS 设置](docs/05-bios.md) |
| ⑥ | 进安装器，格式化 APFS，装系统 | 各机型教程 |
| ⑦ | 声卡、网卡、电源、睡眠修复 | [07 安装后优化](docs/07-post-install.md) |

**卡住了** → [06 故障速查](docs/06-troubleshooting.md)（按现象查，比如"卡在苹果 logo"、"禁行符号"、"只有 1024×768"）。

---

## 📦 目录结构

```
Hackintosh-Toolkit-CN/
├── README.md                  ← 你在这里
├── docs/
│   ├── 00-prepare.md          准备工作 + 生成 EFI
│   ├── 01-office-laptop.md    办公笔记本
│   ├── 02-gaming-pc.md        游戏电脑
│   ├── 03-allround-laptop.md  全能本 / 游戏本
│   ├── 04-server.md           服务器
│   ├── 05-bios.md             BIOS 设置对照表
│   ├── 06-troubleshooting.md  故障速查
│   ├── 07-post-install.md     安装后优化
│   └── hardware-matrix.md     硬件兼容速查
├── scripts/
│   └── check_env.py           环境自检（Python 版本、路径、文件完整性）
└── tools/
    ├── OpCore-Simplify/       自动生成 OpenCore EFI
    └── gibMacOS/              下载 macOS 安装镜像
```

---

## 🔧 工具说明

### OpCore-Simplify

扫描你的硬件 → 自动匹配 ACPI 补丁和 kext → 生成可直接用的 OpenCore EFI。

- Windows：双击 `tools/OpCore-Simplify/OpCore-Simplify.bat`
- 需要 Python 3.8+，安装时务必勾选 **Add Python to PATH**
- **解压路径不能有中文或空格**，例如 `D:\Tools\OpCore` ✅，`D:\黑苹果工具` ❌
- 用法：菜单里选 `E. Export hardware report` 导出硬件报告，比手动选更准

### gibMacOS

从苹果官方服务器直接下载 macOS 安装包，可离线保存。

- Windows：双击 `tools/gibMacOS/gibMacOS.bat`
- 亦需 Python
- ⚠️ 注意：Big Sur 及以后，Windows 下已经**不能**用它直接做恢复 U 盘了（苹果改了分发方式）。现在更通用的做法是用 OpenCore 官方的 `macrecovery`，见各机型教程第 4 步。

### 关于 DiskGenius

原包里给的是网盘链接。**本仓库不打包 DiskGenius**（它是闭源商业软件，不允许随包分发），请从官网下载免费版：
<https://www.diskgenius.cn/download.php>

Windows 自带的「磁盘管理」+ 一个 FAT32 格式的 U 盘，其实就够完成本教程的所有分区操作。

---

## ✅ 装完能用什么

| 功能 | 情况 |
|---|---|
| 硬件加速 / 图形性能 | 显卡免驱的话完美 |
| 声音 | 多数用 AppleALC，需要选对 layout-id |
| 有线网络 | Intel / Realtek 基本全支持 |
| 无线网络 | 换 Broadcom 卡最省心；Intel 卡能上网但无隔空投送 |
| 蓝牙 | 跟无线网卡绑定，同上 |
| 睡眠 / 唤醒 | 大部分台式机和部分笔记本可以，需要修 USB 和 RTC |
| 隔空投送 / 接力 / 随航 | **必须** Broadcom 卡 |
| 指纹识别 | 全部无解 |
| 独显切换（Optimus/MUX） | 基本无解，只能固定用一个 |

---

## 🤝 致谢与来源

本仓库是资料的整理与再组织，工具版权属于原作者，均保留了原始许可证：

- [OpCore-Simplify](https://github.com/lzhoang2801/OpCore-Simplify) — BSD 3-Clause，作者 lzhoang2601
- [gibMacOS](https://github.com/corpnewt/gibMacOS) — MIT，作者 CorpNewt
- 引导器 [OpenCorePkg](https://github.com/acidanthera/OpenCorePkg) — Acidanthera 团队
- 方法论参考 [Dortania 官方指南](https://dortania.github.io/OpenCore-Install-Guide/)

遇到问题优先查 [Dortania](https://dortania.github.io/OpenCore-Install-Guide/) 原文，它的准确度高于任何二手教程。

---

## 📄 许可

本仓库的文档整理部分使用 MIT 协议；`tools/` 下各工具沿用其原始许可证，请遵守对应条款。
