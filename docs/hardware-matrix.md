# 硬件兼容速查表

一页看完"我这台能不能装、能装到哪个版本"。数据整理自 `tools/OpCore-Simplify` 的兼容性数据库与 Dortania 官方指南，以**你实际跑出来的报告为准**。

图例：✅ 支持 ｜ ⚠️ 有限支持 / 需补丁 ｜ ❌ 不支持

---

## 1. CPU

CPU 本身很少是瓶颈，**关键是它带的核显**。

| 代际 | 代表型号 | CPU | 核显 | 说明 |
|---|---|---|---|---|
| 1 代 Nehalem / Westmere | i5-750、i7-870 | ⚠️ | ⚠️ | 只能到 High Sierra |
| 2–3 代 Sandy / Ivy Bridge | i5-2500、i7-3770 | ✅ | ⚠️ | 核显到 Big Sur 左右 |
| 4–5 代 Haswell / Broadwell | i5-4590、i7-5775C | ✅ | ⚠️ | 核显到 Monterey |
| 6–7 代 Skylake / Kaby Lake | i5-6500、i7-7700K | ✅ | ✅ | 最佳性价比区间 |
| 8–9 代 Coffee Lake | i5-8500、i9-9900K | ✅ | ✅ | 最成熟 |
| 10 代 Comet / Ice Lake | i5-10400、i7-1065G7 | ✅ | ✅ | 核显支持的最后一代 |
| 11 代 Rocket / Tiger Lake | i5-11400、i7-11800H | ✅ | ❌ | **核显无驱动**，必须配 A 卡 |
| 12–14 代 Alder/Raptor Lake | i5-12400、i7-13700K | ✅ | ❌ | 同上 |
| Core Ultra（Arrow Lake 等） | Ultra 7 155H | ⚠️ | ❌ | 较新，补丁不成熟 |

### AMD CPU

| 平台 | 情况 |
|---|---|
| Ryzen 1000–5000（Zen/Zen2/Zen3） | ⚠️ 可用，需 `AMD Vanilla` 内核补丁 |
| Threadripper | ⚠️ 可用，ACPI 更复杂 |
| Ryzen 7000+（Zen4） | ⚠️ 实验性 |
| EPYC | ❌ 基本不支持 |

**AMD CPU 的代价**：Adobe 全家桶部分崩溃、Docker/虚拟化不稳定、部分反作弊游戏拦截、系统更新后可能重打补丁。

---

## 2. 显卡（最重要）

### AMD 独显

| 架构 | 型号 | 支持 | 最低系统 |
|---|---|---|---|
| Polaris | RX 460/470/480/550/560/570/580/590 | ✅ | High Sierra |
| Vega | Vega 56/64、Radeon VII | ✅ | Mojave |
| Navi 1x | RX 5500XT/5600XT/5700/5700XT | ✅ | Catalina |
| Navi 21 | RX 6800/6800XT/6900XT | ✅ | Big Sur |
| Navi 22/23 | RX 6600/6600XT/6700/6750XT | ✅ | Monterey 12.2 |
| **Navi 24** | **RX 6400 / 6500XT** | ❌ | — |
| **RDNA3** | **RX 7600 / 7800XT / 7900XTX** | ❌ | — |

### NVIDIA 独显

| 架构 | 型号 | 支持 | 最高系统 |
|---|---|---|---|
| Kepler | GTX 660/680/780 | ⚠️ | Big Sur |
| Maxwell | GTX 750/960/970/980 | ⚠️ | High Sierra |
| Pascal | GTX 1050/1060/1070/1080 | ⚠️ | High Sierra |
| **Turing 及以后** | **RTX 20/30/40/50、GTX 16 系** | ❌ | — |

> RTX 系列**永远**不会有 macOS 驱动。这不是"还没出"，是苹果和 NVIDIA 的合作早就断了。

### 核显

| 核显 | 平台 | 支持 |
|---|---|---|
| HD 3000 | Sandy Bridge | ⚠️ High Sierra 以下 |
| HD 4000 / 5000 | Ivy / Haswell | ⚠️ Monterey 左右 |
| HD 530 / 620 / 630 | Skylake–Kaby | ✅ |
| UHD 620 / 630 | Coffee / Comet Lake | ✅ |
| Iris Plus | Ice Lake（10 代） | ✅ |
| **Iris Xe / UHD 730/750** | **Tiger Lake 及以后** | ❌ |

---

## 3. 无线网卡

| 型号 | 支持 | 隔空投送 / 接力 |
|---|---|---|
| BCM94360CD / CS2 / NG | ✅ 免驱 | ✅ 全功能 |
| BCM94352 / BCM94350 | ✅ 需 kext | ✅ 大部分 |
| Intel AX200 / AX201 / AX210 | ✅ `AirportItlwm` | ❌ 部分接力 |
| Intel 8265 / 9260 / 9560 | ✅ `AirportItlwm` | ❌ |
| Intel AX211 / BE200 | ⚠️ 看版本 | ❌ |
| Atheros 系列 | ⚠️ 老系统 | ❌ |
| Realtek / 高通 | ❌ 多数无解 | ❌ |

> 想要完整苹果生态，**买 Broadcom 卡**是唯一可靠的路。

---

## 4. 有线网卡

| 型号 | 需要的 kext |
|---|---|
| Intel I219-V / LM | `IntelMausi.kext` |
| Intel I225-V | `IntelMausi.kext` + 补丁 |
| Intel I210 / I350 | ✅ 基本免驱 |
| Realtek RTL8111 / 8168 | `RealtekRTL8111.kext` |
| Realtek RTL8125（2.5G） | `LucyRTL8125Ethernet.kext` |
| Aquantia AQC107 / 113 | ✅ 需 kext，Big Sur 起 |
| 服务器万兆卡 | ⚠️ 多数不支持 |

---

## 5. 存储

| 类型 | 情况 |
|---|---|
| SATA SSD / HDD（AHCI） | ✅ 全部支持 |
| NVMe（主流主控） | ✅ 基本都行，个别需要 `NVMeFix.kext` |
| NVMe（国产杂牌主控） | ⚠️ 部分不认 |
| **Intel VMD / RST 模式** | ❌ **必须在 BIOS 关闭** |
| RAID 卡（PERC、LSI MegaRAID、Smart Array） | ❌ 无驱动 |
| 硬件 RAID 阵列 | ❌ 看不到 |
| USB 移动硬盘 | ✅ 一般可用 |

---

## 6. 声卡

| 型号 | 情况 |
|---|---|
| Realtek ALC 系列 | ✅ `AppleALC` + layout-id |
| ALC4080 / 4082（新主板） | ⚠️ 支持不完整，建议 USB 声卡 |
| USB 声卡 / 耳机 | ✅ 免驱 |
| HDMI / DP 音频 | ✅ 显卡支持就行 |
| 服务器板载音频 | ❌ 多数没有或不支持 |

---

## 7. 其他

| 硬件 | 情况 |
|---|---|
| 蓝牙 | 跟无线网卡绑定；Broadcom 免驱，Intel 需 kext |
| 摄像头（USB UVC） | ✅ 免驱 |
| 指纹识别 | ❌ 全部无解 |
| 读卡器 | ⚠️ 部分支持（Realtek 需 `RealtekCardReader`） |
| 雷电 3/4 | ⚠️ 半残，外接显示器常不认 |
| 触摸板（I2C） | ⚠️ 需 `VoodooI2C`，多数能修 |
| 键盘背光 | ❌ 多数不工作 |
| 风扇控制 | ❌ 基本不支持 |
| 传感器（温度电压） | ⚠️ 需 `SMCProcessor` / `SMCSuperIO` |

---

## 8. 一句话总结

> **显卡决定能不能装，核显代际决定能装多新，网卡决定用得爽不爽。**

按这个顺序判断，30 秒就能得出结论。

---

返回 → [README](../README.md)
