# 08 · 命令行工具 `hk`

v2.0 新增。不用开网页、不用装依赖，**纯 Python 标准库**，离线就能跑。

它回答四个问题：**我这台能装吗？装哪个版本？怎么装？卡住了怎么办？**

---

## 安装

仓库里有 `hk/` 目录，不需要 pip 安装。在仓库根目录直接跑：

```bash
python -m hk --help
```

Windows 上双击 `hk.bat`，或者：

```bat
python -m hk check --cpu i5-10210U --gpu "UHD 620" --wifi AX201 --storage nvme
```

> 要求 Python 3.9+。没有任何第三方依赖。

---

## check：能不能装

```bash
python -m hk check --cpu i5-10210U --gpu "UHD 620" --gpu MX250 \
                   --wifi AX201 --storage nvme --platform laptop
```

输出：

```
判定结果
  可以装，建议 macOS Tahoe；范围 10.13 – 26

  ✅ CPU｜i5-10210U
      10 代是最舒服的一档
  ✅ 显卡｜UHD 620
      Comet/Coffee Lake 核显，最成熟的一档
  ⚠️  显卡｜MX250（将被禁用）
      MX 系列笔记本独显没有 macOS 驱动，装上也用不了
      → 在 EFI 里加 disable-gpu，不影响核显输出
  ⚠️  无线｜AX201
      Intel，能上网；隔空投送不可用
      → 想要隔空投送/接力就换 Broadcom 卡
```

参数：

| 参数 | 说明 |
|---|---|
| `--cpu` | CPU 型号，越具体越好 |
| `--gpu` | 显卡，**可以重复给多个**：`--gpu "UHD 620" --gpu RTX3060` |
| `--wifi` | 无线网卡型号 |
| `--ethernet` | 有线网卡（可选） |
| `--storage` | `nvme` / `sata` / `vmd` / `raid` |
| `--platform` | `laptop` / `desktop` / `server` |
| `--json` | 输出 JSON，方便脚本消费 |

### 判定规则（就三条）

1. **有没有能驱动显示的 GPU** —— 没有就装不了，这是硬门槛。
2. **那块卡支持到哪个系统** —— 决定版本上限。
3. **有没有结构性阻塞** —— VMD/RAID、EPYC 平台这类，先解决再谈。

有核显但独显无解时，结论是「**可以装，独显会被禁用**」，不是「装不了」。这是很多人搞混的地方。

---

## plan：生成安装计划

```bash
python -m hk plan --platform laptop --cpu i5-10210U --gpu "UHD 620"
```

输出是**按你的情况裁剪过**的步骤，每步都有「为什么」和「完成标准」：

- 笔记本才有电池、触摸板、亮度那几节
- 台式机才有双系统时间同步
- 服务器才有风扇和 iDRAC
- 你的独显无解时，才会提醒加 `disable-gpu`

不想要文档全文，就想要一张能打勾的清单——用这个。

---

## bios：设置清单

```bash
python -m hk bios --vendor lenovo
```

支持 `lenovo` / `dell` / `hp` / `asus` / `msi` / `gigabyte` / `supermicro`，
外加一份**所有机型都要改**的通用项。

带进入方式和启动菜单键，不用再翻文档找 F2 还是 F12。

---

## troubleshoot：按现象查

```bash
python -m hk troubleshoot 黑屏
python -m hk troubleshoot        # 不带关键词，列出全部
```

覆盖十种高频现象：卡 logo、黑屏、禁行符号、看不到硬盘、无法安装、进不去系统、
没声音、键鼠失灵、睡眠异常、分辨率不对。

---

## matrix / usb

```bash
python -m hk matrix    # 核显、独显的支持区间一览
python -m hk usb       # U 盘制作清单（含 macrecovery 命令）
```

---

## 在脚本里用

```bash
python -m hk check --cpu i5-10400 --gpu "RX 6600" --platform desktop --json
```

```json
{
  "ok": true,
  "headline": "可以装，建议 macOS Tahoe；范围 12.2 – 26",
  "macos": [12, 2],
  "findings": [
    {"level": "ok", "part": "CPU", "title": "i5-10400", "detail": "…", "fix": ""}
  ]
}
```

`ok` 为 false 时退出码仍然是 0（判定完成即成功），要看结论请读 `ok` 字段。

---

## 它不做什么

- **不检测真实硬件**。参数要你自己填；想自动检测用 `tools/OpCore-Simplify` 导出报告。
- **不生成 EFI**。那是 OpCore 的活，`hk` 只告诉你该不该做、做到哪一步。
- **不保证能装**。判定基于「macOS 有没有原生驱动」，不覆盖你机器上所有奇怪情况。
