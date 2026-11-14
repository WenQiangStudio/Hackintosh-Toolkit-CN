# 04 · 服务器

**难度 ★★★★ ｜ 推荐度：中（但先看完第一节）**

服务器装 macOS 是四类里最特殊的一类：硬件规格高、扩展性好，但**天生缺了 macOS 最需要的两样东西** —— 核显和消费级存储控制器。

> 常见机型：Dell PowerEdge R730/R740/R640、HP ProLiant DL380 G9/G10、Supermicro X10/X11 系列、自建 Xeon E5 工作站

---

## 一、先问自己一个问题

> **你是要"一台跑 macOS 的机器"，还是要"这台服务器本身跑 macOS"？**

如果是前者，**虚拟机方案几乎总是更优**，跳到第五节。原因很简单：

- 服务器有 RAID 卡 → macOS 认不到，得绕
- 服务器没有核显 → 必须插显卡
- 装完还得长期维护一个非官方支持的系统和一堆补丁
- 而虚拟机可以快照、可以远程、可以随时删掉重来，宿主系统一点不受影响

裸装唯一的意义是：**要 GPU 直通做视频渲染/CI 编译，且需要接近原生的性能**。

---

## 二、服务器和普通 PC 的 5 个致命差异

### 1. 没有核显

绝大多数 Xeon 平台没有集成显卡。**必须在 PCIe 插槽上装一块免驱的 AMD 显卡**，否则连安装界面都看不到。

- 1U 机箱基本放不下显卡，2U 起步
- 需要确认服务器有 GPU 供电（Dell R730/R740 需要 GPU 启用套件 + 额外供电线）
- 建议选**低功耗、半高**的卡：`RX 6600`、`RX 6400`（注意 6400 是 Navi 24，**不支持**，别买）、`RX 560`

> ⚠️ 别买 RX 6400/6500XT，虽然是低功耗小卡，但 macOS 没有驱动。

### 2. RAID 卡不认

服务器标配的阵列卡（Dell PERC H730/H740、HP Smart Array P440、LSI MegaRAID）在 macOS 下**没有任何驱动**，硬盘一个都看不到。

解决办法：

| 方案 | 说明 |
|---|---|
| 用主板板载 SATA 口 | 多数服务器主板上还有 1–2 个 SATA 接口，接一块 SSD 装系统 |
| 换支持 AHCI 的扩展卡 | 买一张普通 SATA 扩展卡（如 Marvell 9215 芯片的），插 PCIe |
| BOSS 卡 / M.2 直连 | 部分机型有独立 M.2 槽，走 CPU 直连 PCIe |

**不要指望把阵列卡设成 Non-RAID 就能用** —— 问题不在盘，在于 macOS 没有这个控制器本身的驱动。

### 3. 远程管理是救命稻草

iDRAC（Dell）/ iLO（HP）/ IPMI（超微）可以在**没有显卡输出**的情况下看到安装画面、传 ISO、远程操作。

**强烈建议所有操作先在远程控制台里做**：

- 装的时候不怕黑屏
- 出问题能远程重启
- 装完再插显示器切本地

但注意：iDRAC 的"虚拟光驱"挂载 U 盘镜像来引导 OpenCore 有时不工作。更稳的做法是**物理插 U 盘**，只用 iDRAC 看画面。

### 4. 双路 CPU 的 ACPI 很复杂

双路 Xeon 有 `UNC0`（非核心缓存设备）、两套 IOAPIC、NUMA 结构。macOS 会因为多出来的 CPU 节点直接崩溃。

OpCore-Simplify 有专门的处理（把第一个 CPU 条目指向活跃 CPU、禁用 UNC0），所以**务必用它生成，不要手工拼 config**。

如果生成后双路还是起不来，试试在 BIOS 里**只留一个 CPU**（拔掉第二颗）先装通，再插回去调。

### 5. 风扇噪音

服务器风扇是按数据中心环境调的，装上 macOS 后会**全速狂转**（因为 macOS 读不到 BMC 的温度数据）。

- Dell：iDRAC 里把风扇策略调成 `Custom`，手动设一个较低的百分比
- HP：iLO 里设 `Fan Control` 为手动
- 超微：IPMI 里可以调 `Fan Mode`

如果你要把服务器放在卧室或办公室，这一点必须先解决，否则待不住人。

---

## 三、哪些平台能装

| 平台 | 例子 | 支持情况 | 建议版本 |
|---|---|---|---|
| Xeon E5 v3 / v4（Haswell-EP / Broadwell-EP） | R730、DL380 G9、X99 | ✅ 成熟 | Monterey 最稳 |
| Xeon Scalable 1/2 代（Skylake-SP / Cascade Lake） | R640、R740、DL380 G10、X11 | ⚠️ 可以，需要较多 ACPI 修补 | Ventura 左右 |
| Xeon E5 v1/v2（Sandy/Ivy Bridge-EP） | R720、DL380 G8 | ⚠️ 能装但系统很老 | Big Sur 以下 |
| AMD EPYC | — | ❌ 基本不支持 | — |

> 规律：**越老的 Xeon 越好装，越新的越麻烦**。因为 macOS 对这些平台的原生支持是随时间倒退的。

---

## 四、裸装步骤（如果你确定要走这条）

### 1. 硬件准备

- [ ] 一块免驱 A 卡（RX 6600 / RX 580 / RX 560）
- [ ] 一块 SATA SSD（系统盘，接板载 SATA 或扩展卡）
- [ ] 确认 GPU 供电线
- [ ] U 盘（16GB+）

### 2. BIOS 设置

服务器 BIOS 叫法不太一样：

| 项目 | 位置（Dell 为例） | 设为 |
|---|---|---|
| Boot Mode | Boot Settings | **UEFI** |
| Secure Boot | Boot Settings → Secure Boot | **Disabled** |
| SATA / Storage | System BIOS → SATA Settings | **AHCI**（不是 RAID） |
| 板载阵列卡 | Integrated Devices | 可以保持，但别把系统盘接在上面 |
| VT-d / IOMMU | Processor Settings | Disabled（减少干扰） |
| Above 4G Decoding | PCIe Settings | **Enabled** |
| 串口 Serial Port | Serial Communication | Disabled |
| 内存测试 | Memory Settings | 可以开启，装完后关掉加快启动 |

### 3. 生成 EFI

用 OpCore-Simplify，**必须导出硬件报告**（不要手填），它才能正确识别双路和多出来的 PCI 设备。

生成后检查 `config.plist` 里：

- 有 `SSDT-UNC`（双路关 UNC0）
- 有 `SSDT-PLUG`（CPU 电源管理）
- 独显没有被误禁

### 4. 安装

用 iDRAC/iLO 远程控制台看画面，物理 U 盘引导。

流程同 [01](01-office-laptop.md)，注意：

- 磁盘工具里如果看不到盘 → 大概率系统盘接在阵列卡上了，换到板载 SATA
- 第一次进系统可能很慢（服务器内存自检 + 大量 PCI 设备）

### 5. 装完之后必须做的

- [ ] 装 `AppleIntelE1000e` 或对应网卡驱动（服务器多是 Intel 网卡）
- [ ] 装 `SMCProcessor` / `SMCSuperIO` 读温度和电压
- [ ] 调风扇策略（见上面第 5 点）
- [ ] 关闭系统自动更新（服务器上不需要新功能，稳定第一）
- [ ] 装远程管理工具（`RealVNC` / `AnyDesk` / `SSH`）

### 6. 长期运行的注意

- 服务器 7×24 运行，**好的电源和散热比性能更重要**
- 关掉 macOS 的"自动下载更新"，避免半夜自动重启
- 定期备份 EFI 分区（系统升级后 EFI 可能要重做）
- 不要用这台机器做重要数据的唯一存储

---

## 五、替代方案：虚拟机上跑 macOS（推荐）

如果你不是非要裸装，这条路成功率接近 100%，而且更适合服务器场景。

### 为什么更好

| 对比项 | 裸装 | 虚拟机 |
|---|---|---|
| 硬件兼容 | 要看显卡、阵列卡 | 虚拟硬件，全部兼容 |
| RAID 卡 | 认不到 | 宿主处理，随便用 |
| 快照回滚 | 没有 | 随时 |
| 系统升级 | 有变砖风险 | 坏了回滚 |
| 远程管理 | 要另配 | 宿主自带 |
| 图形性能 | 原生 | 无加速（或需直通） |
| iCloud/隔空 | 可用 | 需要小心配置 |

### 方案：Proxmox VE + OSX-KVM

1. 装 **Proxmox VE**（免费，基于 Debian）
2. 用 `OSX-KVM` 项目（<https://github.com/kholia/OSX-KVM>）的脚本生成 macOS 虚拟机
3. 在虚拟机里跑 OpenCore，走正常安装流程
4. 需要图形加速的话，可以给虚拟机直通一块 A 卡（**只适合单卡独占，宿主就没显示了**）

几个坑：

- 必须让 macOS 认为 `en0` 是有线网卡，否则 iCloud/App Store 登录会失败
- SMBIOS 的序列号要合法（用 OpCore 或 GenSMBIOS 生成）
- 虚拟机里没有 `VT-x` 嵌套的话，Docker 跑不起来

### 方案：VMware ESXi

也能跑 macOS，但要打 `unlocker` 补丁，且新版 ESXi 对 macOS 支持越来越差。不如 Proxmox 省心。

---

## 六、一句话总结

**服务器裸装 macOS 技术上可行，但性价比不高。** 如果你的目标是"用 macOS 做 CI、编译、跑测试"，虚拟机是更理性的选择；如果是为了显卡渲染性能，裸装 + A 卡直连才有意义。

---

## 装完检查清单

- [ ] 显卡能输出（本地或远程都行）
- [ ] 系统盘在板载 SATA 上，没有依赖阵列卡
- [ ] 风扇没有全速狂转
- [ ] 有线网络正常
- [ ] 能远程访问（SSH / VNC）
- [ ] 已关闭自动更新
- [ ] EFI 有备份

---

上一篇 → [03 全能本](03-allround-laptop.md) ｜ 下一步 → [07 安装后优化](07-post-install.md)
