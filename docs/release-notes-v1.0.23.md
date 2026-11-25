# 轻PDF编辑器 v1.0.23

> 精简版 PDF 编辑器 ｜ 基于 **PyMuPDF (MuPDF)** + **PySide6 (Qt)** ｜ 支持中文 / English
> 非官方软件，仅供学习交流，与任何商业 PDF 软件厂商均无从属或合作关系。

## 一句话

修复 v1.0.22 原生 GDI 打印路径下「**多页文档只有最后一页有内容、前面页全空白**」的问题。

## 本次改动

v1.0.22 改用 Windows 原生 GDI 打印后，用户实测 4 页文档双面打印只出 2 张纸，但只有一面有内容，
前三页虽然走纸却没有印上任何东西。排查确认是两个问题叠加：

### 1. 换页时 QPainter 没有切换到新画布

`CanvasPrinter.newPage()` 旧实现只把当前 QImage 存入列表、替换 `self._current`，
但绘制用的 `QPainter` 仍绑定在第一张 QImage 上，所有页内容都画到同一张画布，
其余画布保持全白。现在 `CanvasPrinter` 自行持有 QPainter，`newPage()` 时先 `end()` 当前画布、
`begin()` 新画布，并保留 render hints；调用方直接取 `canvas.painter` 使用。

### 2. DIB 位图源数据过早释放

`_stretch_image()` 里 `convertToFormat()` 产生的临时 QImage 在函数返回时即被析构。
iR C3020 等驱动在 `EndPage` / `EndDoc` 阶段才真正读取 `StretchDIBits` 的源数据，
源位图已失效就会导致前面页打印成空白。现在 `print_images()` 预先把所有页转换成 ARGB32
并持有到 `EndDoc` 之后才释放。

## 验证

- 4 页画布换页测试：4 张画布各自的色块正确、其余区域白底无污染（4/4 PASS）。
- DIB 生命周期静态检查：转换后的位图引用覆盖 `EndDoc`。
- GDI 端到端测试：4 页作业全部成功提交（StartPage / StretchDIBits / EndPage 均成功）。
- v1.0.22 已完成的验证继续有效：DEVMODE 方向 / 双面六种组合受控、
  `StretchDIBits` 像素读回正确、冻结程序含 `app.core.win_print`。

## 安装包说明

| 文件 | 平台 | 大小（字节） | SHA-256 |
|---|---|---|---|
| `setup.exe` | Windows 64 位 | 94,217,593 | `9f343d8851a8a631df3cf01e4b741b40217b2df19819b5756587cf4312570b2d` |
| `lightpdf_1.0.23_arm64.deb` | 银河麒麟 / Linux aarch64 | 仍为 1.0.20（可按需重建） | — |
| `lightpdf-linux-build-1.0.23.zip` | 麒麟本机离线构建用源码快照 | 1,295,340 | `ac4f90ec6367d0fc7691a957b1a93e6f3a5f5b0f7ec3595f3f38b4b60e5d7685` |

- 本次修复为 **Windows 专属**；麒麟版本身不走 Windows 驱动，不受此问题影响，可按需重建 1.0.23 保持版本一致。
- `lightpdf-linux-build-1.0.23.zip` 为**源码快照，非安装包**，供麒麟本机离线构建，内含全部修复代码。
- 当前为**本地提交**，尚未 push / 发布 GitHub Release（等用户实测确认）。
