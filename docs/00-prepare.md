# 00 · 准备工作（所有机型通用）

这一篇是四类机型共用的地基。第一次装请从头到尾走一遍，装第二台时可以直接跳到第 4 步。

**预计耗时**：1.5–3 小时（不含下载时间，镜像 12–15GB）

---

## 1. 准备清单

| 项目 | 要求 | 备注 |
|---|---|---|
| U 盘 | ≥ 16GB，USB 3.0 | **会被完全格式化**，别用存着资料的盘 |
| 另一台能上网的电脑 | Windows 或 macOS 都行 | 用来做 U 盘、生成 EFI |
| 装 macOS 的目标硬盘 | ≥ 64GB 空闲，推荐单独一块 SSD | 强烈建议和 Windows 物理隔离 |
| 备份 | 重要文件已复制到别处 | 这一步不能省 |
| 网线 | 强烈建议插网线 | 安装过程需要联网，无线网卡可能还没驱动 |

> 💡 **一台电脑装 macOS，最好的结构是**：一块 SSD 装 Windows，另一块 SSD 装 macOS，各带各的 EFI 分区。双系统共用一块盘也能做，但分区表和引导容易互相踩，出问题的概率明显更高。

---

## 2. 备份

分区和格式化操作几乎不可逆。请把目标硬盘上、以及**同一块硬盘其他分区上**的资料全部拷走。

如果目标硬盘就是你现在 Windows 所在的盘，那更要全盘备份 —— 因为要给它腾出未分配空间。

---

## 3. 安装 Python

两个工具都是 Python 脚本，没有 Python 就跑不起来。

**Windows**
1. 打开 <https://www.python.org/downloads/> 下载最新 3.12 或 3.13
2. 运行安装包，**务必勾选最下面的 `Add python.exe to PATH`**
3. 装完打开「命令提示符」输入验证：

```bat
python --version
```

能显示 `Python 3.12.x` 就对了。显示"不是内部或外部命令"说明没勾 PATH，重装一次。

**macOS**：系统自带 `python3`，跳过本步。

---

## 4. 放对路径（很重要）

OpCore-Simplify 和 gibMacOS 都**不能放在含中文、空格或特殊符号的路径下**，否则脚本会莫名其妙报错。

```
✅ D:\Tools\OpCore-Simplify
✅ C:\Hackintosh\tools
❌ D:\黑苹果工具包\OpCore-Simplify
❌ C:\Users\张三\桌面\新建文件夹 (2)
```

把本仓库整个文件夹放到一个纯英文短路径下，后面所有操作都在这里进行。

---

## 5. 生成 EFI（核心步骤）

### 5.1 启动工具

```bat
tools\OpCore-Simplify\OpCore-Simplify.bat
```

macOS 下用 `OpCore-Simplify.command`，Linux 下 `python3 OpCore-Simplify.py`。

### 5.2 导出硬件报告

菜单里选：

```
E. Export hardware report
```

它会调用系统接口把 CPU、主板、显卡、网卡、硬盘控制器、声卡、显示器连接方式全部抓出来，存成 `Report.json`。**这一步决定后面准不准，一定要用它，不要手填。**

> 如果软件报错说拿不到硬件信息，先关掉杀毒软件和「内核隔离/内存完整性」再试。

### 5.3 看兼容性报告

工具会自动跑检查，输出长这样：

```
CPU:  Intel Core i5-10210U ................ Supported
GPU:  Intel UHD Graphics 620 .............. Supported (macOS 10.15.4 - latest)
GPU:  NVIDIA GeForce MX250 ................ Not supported
Network: Intel Wi-Fi 6 AX201 .............. Supported (partial Continuity)
Storage: Intel VMD Controller ............. Not supported, disable in BIOS
```

**怎么读**：

| 显示 | 含义 |
|---|---|
| Supported | 能用，括号里是支持的 macOS 版本范围 |
| Not supported | 硬件本身无解，考虑禁用或更换 |
| 提到 `OCLP` | 需要 OpenCore Legacy Patcher 打补丁才能用，进阶操作 |
| 提到 `disable in BIOS` | 去 BIOS 关掉这个设备 |

**红灯不可怕，可怕的是红的是显卡**。显卡红 = 没有图形加速，装上也卡成幻灯片，直接换卡或放弃。网卡、声卡红一般都有替代方案。

完整对照看 [hardware-matrix.md](hardware-matrix.md)。

### 5.4 选 macOS 版本

工具默认会挑**你硬件能支持的最高版本**。直接用它推荐的就好。

几点建议：

- **别一味追新**。新系统对老硬件越来越不友好，Ventura / Sonoma 往往是老平台的甜点。
- **装了才发现缺驱动的老硬件**，降一个版本通常立刻好转。
- 装完想升级，可以在系统里正常升级小版本；跨大版本升级前先备份 EFI。

### 5.5 定制（可选，建议先跳过）

接下来会问你要不要改 ACPI、kext、SMBIOS。**第一次装全部保持默认**，工具帮你选的就是最稳的组合。等系统跑起来、发现具体问题，再回来改对应项。

### 5.6 生成

选 `Build OpenCore EFI`，它会自动联网下载 OpenCorePkg 和一堆 kext（需要几分钟，别断网）。

完成后在工具目录下会得到：

```
EFI/
├── BOOT/
│   └── BOOTx64.efi
└── OC/
    ├── ACPI/          补丁
    ├── Drivers/       驱动
    ├── Kexts/         内核扩展
    ├── Resources/     主题、字体
    └── config.plist   核心配置
```

**把这个 `EFI` 文件夹单独拷贝出来放好**，后面要往 U 盘和硬盘各放一次。

---

## 6. 做启动 U 盘

U 盘需要两个东西：**EFI 引导** + **macOS 恢复镜像**。

### 6.1 格式化 U 盘

Windows 下：右键 U 盘 → 格式化 → 文件系统选 **FAT32** → 分配单元 4096 → 快速格式化。

> 只有一个分区、FAT32，这是最省事的结构。

### 6.2 放入 EFI

把第 5 步的 `EFI` 文件夹整个复制到 U 盘根目录：

```
U盘:\
├── EFI\
│   ├── BOOT\
│   └── OC\
└── com.apple.recovery.boot\   ← 下一步生成
```

### 6.3 下载恢复镜像（推荐方式）

用 OpenCore 官方的 `macrecovery`，它直接产出能引导的恢复环境，**Windows 下也能用**，不需要 Mac。

1. 下载 OpenCorePkg 发布包：<https://github.com/acidanthera/OpenCorePkg/releases>（选 `OpenCore-x.x.x-RELEASE.zip`）
2. 解压后进入 `Utilities/macrecovery/`
3. 在该目录打开命令提示符，执行：

```bat
python macrecovery.py -b Mac-E43C1C25D4880AD6 -m 00000000000000000 -os latest download
```

它会下载 `BaseSystem.dmg` 和 `BaseSystem.chunklist`，放在 `com.apple.recovery.boot` 文件夹里。

4. 把整个 `com.apple.recovery.boot` 文件夹复制到 U 盘根目录。

> 📌 `-b` 后面的 board-id 决定能下到哪个版本的恢复镜像。`Mac-E43C1C25D4880AD6` 是通用性较好的一个，配 `-os latest` 会拿到最新的可用版本。如果提示找不到对应版本，去 [Dortania 的 U 盘制作页](https://dortania.github.io/OpenCore-Install-Guide/installer-guide/windows-install.html) 换一个 board-id 再试。

### 6.4 备选：完整安装器（只有 Mac 时）

如果你手边有 Mac：

1. 在 App Store 搜索并下载对应版本的 macOS（会下到「应用程序」里）
2. 准备 U 盘，终端执行：

```bash
diskutil list                      # 找到 U 盘的编号，比如 disk4
diskutil eraseDisk APFS USB /dev/disk4
sudo /Applications/Install\ macOS\ Sonoma.app/Contents/Resources/createinstallmedia --volume /Volumes/USB
```

3. 装完再把 `EFI` 文件夹复制到 U 盘的 EFI 分区（用 `diskutil mount` 挂载）

这种方式得到的是完整安装包，**不需要联网**，安装更快，但要求你有一台 Mac。

> ⚠️ 用 gibMacOS 在 Windows 上下载的 `InstallAssistant.pkg`，从 Big Sur 开始已经无法在 Windows 下直接做成可引导 U 盘了。所以 **Windows 用户请走 6.3 的 macrecovery 方案**。

---

## 7. 拔 U 盘，去改 BIOS

在重启进 U 盘之前，必须先改 BIOS 设置。不同品牌位置不一样，对照 [05 BIOS 设置](05-bios.md) 改。

改完后插上 U 盘，开机狂按启动菜单键（通常是 F12 / F11 / F8 / Esc），选 `UEFI: 你的U盘`。

---

## 8. 看到 OpenCore 菜单就成功一半了

顺利的话会看到图形化引导菜单，里面有：

- **macOS Base System**（或 `Install macOS ...`）← 选这个进安装器
- **Reset NVRAM** ← 卡住时可以用来清缓存
- **Windows**（如果你有）

选中按回车。接下来按你机型的教程走：

- [01 办公笔记本](01-office-laptop.md)
- [02 游戏电脑](02-gaming-pc.md)
- [03 全能本](03-allround-laptop.md)
- [04 服务器](04-server.md)

进系统后先做一遍 [07 安装后优化](07-post-install.md)，把声卡网卡电源收拾干净，再把 EFI 挪到硬盘上。

---

## ✅ 这一步的自检清单

- [ ] 数据已备份到别的硬盘
- [ ] `python --version` 正常
- [ ] 工具放在纯英文路径
- [ ] OpCore 的硬件报告里，**显卡是绿的**
- [ ] 拿到了 `EFI` 文件夹
- [ ] U 盘是 FAT32，根目录有 `EFI` 和 `com.apple.recovery.boot`
- [ ] BIOS 已按 [05](05-bios.md) 调整
