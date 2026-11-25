# 轻PDF编辑器 v1.0.22

> 精简版 PDF 编辑器 ｜ 基于 **PyMuPDF (MuPDF)** + **PySide6 (Qt)** ｜ 支持中文 / English
> 非官方软件，仅供学习交流，与任何商业 PDF 软件厂商均无从属或合作关系。

## 一句话

彻底修复 Windows 上打印方向 / 双面翻转设置不生效——改用 Windows 原生 GDI 直接打印，与 Foxit 的打印方式一致。

## 本次改动

v1.0.21 在 Qt的 `QPrinter` 层面修正了方向设置，但 iR C3020 等网络复合机驱动**不会把 Qt 传来的方向 / 双面参数写进驱动 DEVMODE**，打印时仍用打印机自身默认（横向 / 单面），所以出现「方向怎么选都打在横向 A4 上、长边短边翻转无效」。

实测确认：这台 iR C3020 的驱动默认 DEVMODE 就是 `Orientation=2`（横向）。用完整 DEVMODE（含驱动私有数据）创建设备上下文后，方向 / 双面完全受控（纵向 DC 9440×13548、横向 13548×9440）。

### 修复方案：Windows 原生 GDI 打印

- 新增 `app/core/win_print.py`：用 ctypes 直接调用 Windows  spooler / GDI API：
  - `OpenPrinterW` + `DocumentPropertiesW` 取得**含驱动私有数据的完整 DEVMODE**；
  - 显式设置 `dmOrientation`（纵 / 横）、`dmDuplex`（单面 / 长边 / 短边）、`dmPaperSize=A4`，并置上对应 `dmFields`；
  - `CreateDCW` 把这份 DEVMODE 交给驱动，`StartDocW` → 每页 `StartPage` → `StretchDIBits` → `EndPage` → `EndDoc` 打印。
- `PrintDialog` 新增 `_do_print_gdi()`：Windows 物理打印走 GDI 路径；打印到文件 / 非 Windows 仍走原 QPrinter 路径。
  - 内容布局**完全复用**现有 `_print_plain` / `_print_sides` / `_print_tiled` 逻辑（通过一个轻量画布适配器），只是把成品画布贴到打印机 DC，因此之前修好的缩放 / 小册子 / N-up / 平铺不受影响。
  - 画布按 200 DPI A4 生成（1654×2339 / 2339×1654），避免按设备原生分辨率产生超大位图。
- v1.0.21 的 `_apply_orientation()` / 双面信号接线保留，作为非 GDI 路径的兜底。

## 验证

- DEVMODE 控制：iR C3020 上 `portrait/landscape × none/long/short` 六种组合，方向 / 双面值全部正确写入，设备上下文尺寸随方向变化（纵向 9440×13548、横向 13548×9440）。
- 贴图正确性：用 `CreateDIBSection` 读回验证 `StretchDIBits` 写入的像素，白底 `FFFFFF`、色块 `281EDC`（RGB 220,30,40 的 BGR）完全正确。
- 集成验证：模拟打印 4 页文档，纵向画布 1654×2339、横向 2339×1654；双面 short / long / none 参数全部正确传递。
- 冻结程序核验：`app.version`=`1.0.22`、`app.core.win_print` 模块已打入、GDI 修复符号齐全。

## 安装包说明

| 文件 | 平台 | 大小（字节） | SHA-256 |
|---|---|---|---|
| `setup.exe` | Windows 64 位 | 94,217,680 | `44d9cf05ed9baad0cac3ca401e0ec9565aeb07cbfc2111f1cdeea24a9c253206` |
| `lightpdf_1.0.22_arm64.deb` | 银河麒麟 / Linux aarch64 | 待麒麟本机重建 | 待生成 |
| `lightpdf-linux-build-1.0.22.zip` | 麒麟本机离线构建用源码快照 | 1,292,441 | `53515b22537909a31e11e78047f81f46c97f86f1f5b075843dc9a032e3f239a9` |

- 本次打印修复为 **Windows 专属**（GDI 打印）；麒麟版本身不走 Windows 驱动，不受此问题影响，可按需重建 1.0.22 保持版本一致。
- `lightpdf-linux-build-1.0.22.zip` 为**源码快照，非安装包**，供麒麟本机离线构建，内含全部修复代码。
- 当前为**本地提交**，尚未 push / 发布 GitHub Release（等用户确认）。
