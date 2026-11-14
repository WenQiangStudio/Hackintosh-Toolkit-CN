# 07 · 安装后优化

系统装好、能进桌面，只是完成了 60%。这一篇把剩下的 40% 补齐 —— 声音、网络、睡眠、三码、双系统时间。

---

## 0. 第一件事：备份 EFI

在你改任何东西之前，把能正常启动的 `EFI` 文件夹整个复制一份到 U 盘和另一个位置：

```
备份/
├── EFI-可用-2024xxxx/     ← 今天能启动的版本
└── EFI-实验/              ← 之后折腾的版本
```

黑苹果的大部分事故是"改完 config 起不来了"。有这个备份，插上 U 盘引导就能恢复，五分钟的事；没有的话可能要重装。

---

## 1. 三码（iServices：iCloud / App Store / iMessage）

要正常登录苹果服务，需要四个东西配套：

| 字段 | 在哪 | 说明 |
|---|---|---|
| `SystemSerialNumber` | PlatformInfo → Generic | 序列号 |
| `MLB` | PlatformInfo → Generic | 主板序列号 |
| `SystemUUID` | PlatformInfo → Generic | 唯一标识 |
| `ROM` | PlatformInfo → Generic | 有线网卡的 MAC 地址，12 位十六进制 |

**怎么生成**：OpCore-Simplify 生成 EFI 时已经自动填了一套。如果你要自己换机型：

```bash
# 用 GenSMBIOS（OpenCore 配套工具）
python3 GenSMBIOS.command
# 选 1 → 输入机型（如 iMac19,1）→ 自动生成 SN/MLB/UUID
```

**注意事项**（很重要）：

- ⚠️ **不要用新注册的 Apple ID 直接登录**，容易被风控锁定。用你已有的、有购买记录的主账号。
- 一台机器的三码不能给两台机器用，会被判定为异常。
- `ROM` 要用**真实的网卡 MAC**（`系统信息 → 网络 → 以太网 → 硬件地址`），不是随便编的。
- 登录前确保 `en0` 是有线网卡（`系统信息 → 网络` 里看接口顺序）。

> 如果登录失败提示"无法验证"，多半是 `ROM` 或 `MLB` 不对，或者三码不是同一套。重新生成一次整套。

---

## 2. 声音

见 [06 故障速查 → 没有声音](06-troubleshooting.md#i-没有声音)。

调好之后检查：

- [ ] 内置扬声器有声音
- [ ] 插耳机能自动切换
- [ ] 麦克风能录（系统设置 → 声音 → 输入，看电平条有没有跳）
- [ ] 音量快捷键能用

麦克风不工作的话，通常是 `layout-id` 只匹配了输出没匹配输入，换一个编号试。

---

## 3. 网络

### 有线

装完应该直接能用。如果不行，确认对应 kext 已加载（见 [06](06-troubleshooting.md#j-网络不通)）。

### 无线

| 你的卡 | 做法 |
|---|---|
| Broadcom BCM94360 系列 | 免驱，什么都不用装 |
| Intel AX200/AX201/8265 | 装 `AirportItlwm.kext`（**必须和系统版本对应**） |
| Realtek / 高通 | 基本无解，换卡或用 USB 无线网卡 |

**Intel 网卡的版本对应很关键**：`AirportItlwm` 是按 macOS 大版本编译的，下错了会直接开不了机。去 [OpenIntelWireless 发布页](https://github.com/OpenIntelWireless/itlwm/releases) 下对应你系统版本的那个。

### 蓝牙

跟无线网卡绑定。Broadcom 免驱；Intel 需要 `IntelBluetoothFirmware.kext` + `BlueToolFixup.kext`。

---

## 4. USB 映射（强烈建议做）

这是黑苹果"稳定"的关键一步，能同时解决：

- 键鼠失灵
- 睡眠睡不醒
- USB 设备随机掉线
- 插 U 盘没反应

**工具**：`USBToolBox`（Windows 下运行）

1. 在 Windows 里以管理员身份运行
2. 选 `Discover Ports`
3. 拿一个 U 盘 / 鼠标，**逐个插拔每一个 USB 口**，让工具记录
4. 全部插一遍后选 `Select Ports`，把用不到的口关掉
5. 选 `Build kext`，生成 `USBPorts.kext`
6. 放进 `EFI/OC/Kexts/`，在 `config.plist` 的 `Kernel → Add` 里注册
7. **删掉**原来的 `USBInjectAll.kext`（会冲突）

> 笔记本做完这一步，触摸板、摄像头、蓝牙通常也会一起变好。

---

## 5. 电源管理

台式机 / 笔记本都应该有 `SSDT-PLUG`，让 macOS 正确管理 CPU 频率。

**检查有没有生效**：

```bash
# 终端里执行
ioreg -l | grep -i "plugin-type"
```

输出里有 `"plugin-type" = 1` 就说明生效了。

没生效的话，用 `SSDTTime` 生成一个 `SSDT-PLUG.aml`，丢进 `EFI/OC/ACPI/` 并在 config 里注册。

**笔记本额外注意**：`SMCBatteryManager.kext` 管电池，`SMCProcessor.kext` / `SMCSuperIO.kext` 管温度和风扇。

---

## 6. 亮度调节（笔记本）

如果 F11/F12 调不了亮度：

1. 确认 `SSDT-PNLF.aml` 在 ACPI 里
2. 确认 `WhateverGreen.kext` 已加载
3. 装 `BrightnessKeys.kext` 让快捷键生效

有些机器需要在 `DeviceProperties` 里改 `framebuffer` 参数才能调，比较麻烦，可以先用 `MonitorControl` 这个软件走软件调光。

---

## 7. 睡眠

睡眠是黑苹果最容易出问题的地方。按顺序排查：

### 7.1 先确认 USB 映射做了（第 4 节）

80% 的睡眠问题是 USB 引起的。

### 7.2 关掉网络唤醒

「系统设置 → 电池 / 节能」→ 关掉 **"唤醒以供 Wi-Fi 网络访问"**。

BIOS 里也关掉 `Wake on LAN` / `ErP`。

### 7.3 RTC 补丁

如果**一睡就立刻醒**，是 RTC 在捣乱：

- OpCore 会自动加 `SSDT-RTC0` 或 RTC 补丁
- 手动的话，在 config 里加 `DisableRtcChecksum = true`

### 7.4 检查什么在唤醒

```bash
# 看唤醒原因
pmset -g log | grep -i "wake"
```

如果反复出现 `DarkWake`，通常是网卡或蓝牙在唤醒，对应关掉。

### 7.5 实在修不好

用 `Amphetamine` 或系统设置里的「防止电脑自动进入睡眠」顶着，或者干脆设成从不睡眠、只关显示器（台式机完全够用）。

---

## 8. 键盘映射

macOS 的 `Command` 键位置和 Windows 的 `Ctrl` 不一样，用起来别扭。

**改法**：「系统设置 → 键盘 → 键盘快捷键 → 修饰键」，把：

- `Option` 换成 `Command`
- `Command` 换成 `Option`

（具体哪两个对调，看你习惯，一般是把 Alt 和 Win 键对调）

---

## 9. 双系统时间不同步

macOS 把硬件时钟当 **UTC**，Windows 当 **本地时间**。双系统切换后时间会差 8 小时。

**修法（在 Windows 里改注册表）**：

以管理员身份打开命令提示符：

```bat
reg add "HKEY_LOCAL_MACHINE\System\CurrentControlSet\Control\TimeZoneInformation" /v RealTimeIsUniversal /t REG_DWORD /d 1 /f
```

重启 Windows，之后两边时间就一致了。

---

## 10. 系统更新策略

### 小版本更新（如 14.4 → 14.5）

直接在「系统设置 → 软件更新」里装，一般没问题。**装之前备份 EFI。**

### 大版本更新（如 14 → 15）

风险明显高，因为：

- kext 可能不兼容新系统
- OpenCore 需要升级
- 部分硬件驱动会失效

**建议流程**：

1. 先查 kext 作者有没有发布支持新系统的版本
2. 升级 OpenCore 到最新版（用 `OCAT` 工具）
3. 备份当前 EFI
4. 再更新系统
5. 如果起不来，用备份的 EFI 引导回旧系统

### 关掉自动更新（稳定优先）

「系统设置 → 通用 → 软件更新 → 自动更新」→ 全部关掉。

服务器和生产力机器尤其要关。

---

## 11. 关于 SIP

macOS 的系统完整性保护默认开启。少数操作（改系统文件、装某些驱动）需要关掉。

**关掉**：`config.plist → NVRAM → csr-active-config` 设为 `03000000`

**开启**：设为 `00000000`

除非明确知道自己在干什么，**保持开启**。

---

## 12. 最后的检查清单

- [ ] EFI 已备份到 U 盘
- [ ] 声卡、麦克风正常
- [ ] 有线 + 无线网络正常
- [ ] 蓝牙正常（如果用得到）
- [ ] USB 映射完成
- [ ] 电源管理生效（`plugin-type = 1`）
- [ ] 亮度可调（笔记本）
- [ ] 睡眠正常，或者已接受"不睡眠"
- [ ] iCloud / App Store 能登录
- [ ] 双系统时间正常
- [ ] 自动更新已关闭
- [ ] 硬盘引导不依赖 U 盘

---

## 13. 日常维护

| 多久 | 做什么 |
|---|---|
| 每次改 EFI 前 | 备份当前能用的 EFI |
| 每月 | 检查 OpenCore 和 kext 有没有更新（用 `OCAT`） |
| 系统更新前 | 查兼容性、备份 EFI |
| 半年 | 清理一次 `EFI` 里没用到的 kext，减小体积 |

---

装完了。如果这套资料帮到你，欢迎把你的机型配置整理成 issue 分享出来。

上一篇 → [06 故障速查](06-troubleshooting.md) ｜ 回首页 → [README](../README.md)
