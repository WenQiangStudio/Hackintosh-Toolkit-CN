# 01 · 办公笔记本

**难度 ★★☆ ｜ 推荐度：高 ｜ 成功率：最高的一类**

这是黑苹果最成熟的场景。2015–2020 年的办公本（尤其是商务本）硬件构成简单、社区验证充分，绝大多数能装到很新的系统并日常使用。

> 代表机型：ThinkPad T460/T470/T480/X1 Carbon、联想小新 Air/Pro、戴尔 Latitude 5000/7000 系、惠普 EliteBook 800 系、华硕灵耀、华为 MateBook D14

---

## 一、先做 3 个判断

### 判断 1：核显是哪一代？

办公本几乎全靠核显输出，所以核显就是命门。

| 核显 | 平台 | 能装到 | 结论 |
|---|---|---|---|
| UHD 620 / 630 / Iris Plus | 8–10 代（Coffee/Comet/Ice Lake） | 最新系统 | ✅ 最理想 |
| HD 620 / 630 / 530 | 6–7 代（Skylake/Kaby Lake） | Ventura 左右 | ✅ 很好 |
| HD 4400 / 4600 / 5500 | 4–5 代（Haswell/Broadwell） | Monterey 左右 | ⚠️ 可以，但系统偏老 |
| Iris Xe（11 代及以后） | Tiger Lake 以后 | ❌ 不支持 | ❌ 放弃 |

**11 代酷睿之后的核显在 macOS 里没有驱动**，这是硬限制，没有绕过的办法。2021 年以后的轻薄本基本都属于这一类。

### 判断 2：有没有独立显卡？

轻薄本常见 MX150 / MX250 / MX350 / MX450 —— **这些全都没有驱动**。

解决办法是在 EFI 里把它禁用掉（OpCore 会自动加 `disable-gpu` 属性）。禁用后不影响使用，因为办公本的视频输出本来就主要走核显，只是续航会略差一点点。

### 判断 3：硬盘是 AHCI 还是 VMD/RST？

不少 10 代以后的笔记本出厂把硬盘设成 **Intel RST / VMD 模式**。这个模式下 macOS 安装器**看不到硬盘**，表现是「磁盘工具里一片空白」。

必须进 BIOS 把它改成 **AHCI**。

> ⚠️ 改之前要注意：如果你的 Windows 是在 RST 模式下装的，直接改成 AHCI 会导致 Windows 蓝屏（INACCESSIBLE_BOOT_DEVICE）。正确做法是先在 Windows 里用安全模式方式切一次驱动，或者干脆把 macOS 装到另一块盘上。具体方法搜「RST 转 AHCI 不重装系统」。

---

## 二、你的配置大概能到什么程度

| 你的配置 | 预期结果 |
|---|---|
| 8 代 i5 + UHD620 + Intel 网卡 | 完美，唯一遗憾是隔空投送 |
| 10 代 i5 + UHD620 + AX201 | 完美，同上 |
| 7 代 i5 + HD620 + 独显 MX150 | 良好，需禁用独显 |
| 4 代 i5 + HD4400 | 可用但系统只能到 Monterey，且需 OCLP 补丁才能上更高版本 |
| 11 代及以上 | 装不了，建议虚拟机 |

---

## 三、安装步骤

前置：先完成 [00 准备工作](00-prepare.md) 的第 1–5 步，拿到 `EFI` 文件夹。

### 1. 改 BIOS（笔记本通用）

开机按 F2 / F1（ThinkPad） / F10（惠普，先按 Esc）进设置：

| 项目 | 设为 |
|---|---|
| Secure Boot（安全启动） | **Disabled** |
| Fast Boot（快速启动） | **Disabled** |
| UEFI / Legacy | **UEFI Only** |
| CSM | **Disabled** |
| SATA / Storage 模式 | **AHCI**（不是 RST/RAID/Intel VMD） |
| Intel VMD Controller | **Disabled**（如果有这一项） |
| VT-d | **Disabled**（减少干扰，装完可再开） |
| CFG Lock | 能关就关（关不掉也没关系，OpCore 会处理） |

ThinkPad 部分机型还需要 **关掉 "Security → I/O Port Access → Fingerprint"** 之类，以及某些 X1 需要在 BIOS 里 **禁用 "Intel AMT"**。

### 2. 装系统

插 U 盘，开机启动菜单选 U 盘（ThinkPad 是 F12），进 OpenCore 菜单后选 `macOS Base System`。

进到恢复环境后：

1. 打开「磁盘工具」
2. 左上角切到「显示所有设备」
3. 选中你的目标硬盘（**别选错**），点「抹掉」：
   - 名称：`Macintosh HD`
   - 格式：**APFS**
   - 方案：**GUID 分区图**
4. 关掉磁盘工具，选「安装 macOS」
5. 按提示走，中途会重启几次，**每次都选 U 盘里的 OpenCore 菜单，再选 "macOS Installer"**（不是 Base System）

> 💡 进度条卡在最后 1/10 很久是正常的，别急着断电。

### 3. 第一次进系统

装完最后一次重启，选硬盘上的 macOS 启动。

此时你会遇到：

- 没有声音 → 正常，进系统后修（见第 4 节）
- 网卡可能没有 → 插网线，或用 USB 网卡
- 分辨率可能不对 → 重启用 `-v` 看报错，通常是显卡驱动没加载

进得去桌面，就成功了 80%。

### 4. 把 EFI 挪到硬盘

现在系统能跑了，但还依赖 U 盘引导。要做的是让硬盘自己引导：

**方法 A（Windows 下，最省事）**
1. 用 DiskGenius 或 `diskpart` 给硬盘的 EFI 分区（ESP）分配一个盘符
2. 把 U 盘里的 `EFI` 文件夹复制进去（如果已有 `Microsoft` 文件夹，**别覆盖它**）
3. 在 BIOS 启动项里把 `OpenCore` 调到第一位

**方法 B（macOS 下）**
```bash
diskutil list                  # 找到 EFI 分区，比如 disk0s1
sudo diskutil mount disk0s1
cp -R /Volumes/EFI/EFI /Volumes/磁盘的EFI分区/
```

> 注意：硬盘 ESP 分区通常只有 100–200MB。如果 OpCore 生成的 EFI 塞不下（一般不会，约 30–60MB），需要用分区工具把 ESP 扩到 300MB。

---

## 四、办公本特有的坑

### 1. 触摸板不能用

笔记本触摸板大多是 **I2C 接口**（Synaptics / ELAN / ALPS），需要 `VoodooI2C` 系列驱动。

OpCore 通常会加，但仍然需要：

- ACPI 里有正确的 `GPI0` 设备
- 少数机型需要手工加 `SSDT-GPI0` 或 `SSDT-XOSI`

**排查方法**：进系统后看「系统信息 → 硬件 → 蓝牙/USB」里能不能看到触摸板设备。看不到就是 ACPI 没配对。

如果只是打字时手掌误触，可以在「系统设置 → 触控板」里关掉「使用触控板打字」。

### 2. 电池电量显示不对 / 不显示

需要 `SMCBatteryManager.kext`（OpCore 一般会加）。有些机型还要配合 EC 补丁。

如果显示"未在充电"但实际在充，通常是 EC 数据读取问题，重做一次硬件报告重新生成 EFI 往往能解决。

### 3. 睡眠睡死 / 一睡就醒

笔记本睡眠是黑苹果的老大难。常见原因：

- USB 控制器没做映射 → 用 `USBToolBox` / `USBMap` 生成 `USBPorts.kext`
- RTC 唤醒 → OpCore 会加 `SSDT-RTC0` / RTC 补丁
- 网卡唤醒 → 在「系统设置 → 节能」里关掉"唤醒以供网络访问"

**短期方案**：把「系统设置 → 锁定屏幕 → 关闭显示器后需要密码」设短，手动合盖前先锁屏。

### 4. 无线网卡

| 你的网卡 | 情况 |
|---|---|
| Intel AX200 / AX201 / 8265 / 9260 | 能用 `AirportItlwm`，正常上网，**但隔空投送、接力、随航不可用** |
| Broadcom BCM94360 / BCM94352 | 免驱，全功能 |
| Realtek / 高通 | 多半无解，换卡或买 USB 无线网卡 |

**想完整用苹果生态**：买一张 `BCM94360NG` 或 `BCM94360CS2` 转接卡换上（ThinkPad 有白名单，注意买对应 FRU 的）。这是办公本最值得的一笔投入，几十块钱。

### 5. 雷电 3 / USB-C 扩展坞

雷电控制器部分工作，但**外接显示器、雷电硬盘盒经常不认**。USB-C 的普通 USB 功能和充电一般正常。

如果你重度依赖扩展坞，提前有心理准备。

### 6. 指纹识别

**全部无解**。没有任何驱动能让 macOS 用上笔记本的指纹模块。开机输密码吧。

### 7. 摄像头

绝大多数是 USB UVC，免驱。个别机型（如某些 ThinkPad 的 IR 摄像头）只有普通摄像头能出图，红外人脸识别不可用。

---

## 五、装完检查清单

- [ ] 能正常关机、重启、睡眠
- [ ] 声音正常（插耳机也能切）
- [ ] 亮度调节可用（F11/F12 或系统设置里能拖）
- [ ] Wi-Fi 能连（有线网更稳）
- [ ] 触摸板能点、能双指滚动
- [ ] 电池图标显示正常
- [ ] 硬盘引导不需要 U 盘
- [ ] `iCloud` 能登录（**别用新 Apple ID 直接登，容易封号，用已有的主账号**）

---

## 六、参考配置与对应版本

| 机型（示例） | CPU / 核显 | 建议版本 | 备注 |
|---|---|---|---|
| ThinkPad T480 | i5-8250U / UHD620 | Sonoma 或 Sequoia | 社区 EFI 最多，最容易 |
| ThinkPad X1 Carbon 6th | i7-8550U / UHD620 | Sonoma | 需注意 WWAN 白名单 |
| 联想小新 Air 14 2020 | i5-10210U / UHD620 | Ventura / Sonoma | 关闭 VMD |
| 戴尔 Latitude 7490 | i5-8250U / UHD620 | Sonoma | BIOS 里关 TPM |
| 惠普 EliteBook 840 G6 | i5-8365U / UHD620 | Ventura | 需关 HP Sure Start |
| 华为 MateBook D14 (2019) | i5-8265U / UHD620 | Ventura | 网卡多为 Realtek，需换 |

> 同一型号不同批次硬件可能不同（尤其是网卡和屏幕）。**永远以你自己跑出来的 OpCore 报告为准**，别照抄别人的 EFI。

---

下一篇 → [07 安装后优化](07-post-install.md) 把驱动收尾。出问题 → [06 故障速查](06-troubleshooting.md)。
