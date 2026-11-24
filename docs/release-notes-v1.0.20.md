# 轻PDF编辑器 v1.0.20

> 精简版 PDF 编辑器 ｜ 基于 **PyMuPDF (MuPDF)** + **PySide6 (Qt)** ｜ 支持中文 / English
> 非官方软件，仅供学习交流，与任何商业 PDF 软件厂商均无从属或合作关系。

## 一句话

修复「批注 → 插入骑缝章」首次点击无响应、再次点击闪退；并修复多枚骑缝章图片相同时分组标记互相覆盖的问题。

## 本次改动

### 1. 插入骑缝章对话框无法弹出 / 二次点击闪退

v1.0.19 给骑缝章切片元组增加了第 6 项「图章序号」，用于把同一枚章的所有切片绑定成一组；但对话框预览
仍按 5 项解包：

```python
for _pi, png, sw, sh, _slot in first:   # v1.0.19 遗留：first 里已有 6 项
    ...
```

点击菜单后，`RidingStampDialog.__init__` 在构造阶段就抛出 `ValueError: too many values to unpack`，
窗口还没显示出来；异常发生在 Qt 事件槽里，再次点击会让程序直接退出。

v1.0.20 改为按下标读取 `item[1] / item[2] / item[3]`：

- 兼容 6 项（v1.0.19 起）和 5 项（旧版本）的切片结构；
- 预览不再因为元组长度变化而中断；
- 菜单点击可正常弹出「插入骑缝章」对话框。

### 2. 多枚骑缝章分组标记互相覆盖

PyMuPDF 会按图片流的内容摘要复用 PDF 图片对象。一次插入多枚骑缝章时，如果不同章的切片图片恰好完全相同
（例如都来自同一个图章、同一组切片），它们会共用同一个 xref；后一枚章写入的 `LightpdfRidingGroup`
会覆盖前一枚章的标记，导致「同章整组联动」失效。

v1.0.20 在以下三个入口为每个切片写入独立的 PNG 文本块（`LightpdfStamp`），只改变图片流摘要、不改变画面：

- 初次插入骑缝章；
- 拖动 / 属性对话框修改 Y 后重新落位；
- 未烘焙的浮层图片写回 PDF。

这样每个切片都拥有独立 xref，分组与槽位标记不再互相覆盖；多枚章可以各自独立联动。

## 验证

- 源码环境重现：构造 `RidingStampDialog` 在修复前稳定抛出 `ValueError: too many values to unpack`；修复后正常构造。
- 菜单链路：新建空白文档 → 触发「批注 → 插入骑缝章」→ 对话框正常弹出并可取消，无异常退出。
- 分组验证：10 页文档选 1–5 页、每 2 页一枚章（共 3 枚），插入后 group id 为 1/2/3，三枚互不覆盖。
- 联动验证：5 页一枚章下移 12 pt，5 片全部 +12 pt；两枚章时只移动第一枚，第二枚保持不动。
- 冻结程序核验：`app.version` 含 `1.0.20`，`app.core.annotations` / `app.ui.pdf_view` 含修复符号，全部通过。

## 安装包说明

| 文件 | 平台 | 大小（字节） | SHA-256 |
|---|---|---|---|
| `setup.exe` | Windows 64 位 | 94,208,991 | `5b83b27af19b6e9cdefb782ff2c95d1e1081bf896e6658e89a878384af0d5bac` |
| `lightpdf_1.0.20_arm64.deb` | 银河麒麟 / Linux aarch64 | 132,515,524 | `f4d08321ba38cd5efad477706df7dab7c6ac2db947650fab42be9e50ce899a17` |
| `lightpdf-linux-build-1.0.20.zip` | 麒麟本机离线构建用源码快照 | 1,286,759 | `cbfb953d122426ad8eb77c10fb47e1b510b88090951f0dd0b7b555886f889a64` |

- `setup.exe` 用 Python 3.10 + PyInstaller 6.22.3 + Inno Setup 7 重新打包。
- 麒麟 `.deb` 已由用户在 aarch64 本机重建：control 为 `Version: 1.0.20 / arm64`，并核验内嵌修复逻辑（非旧包改名）。
  - 2026-11-24 用户再次重新打包同名包（位置/文件名不变）：新包 132,515,524 B（较此前 67,303,548 B 增大，因把 PySide6/PIL 等运行库一并打进 onedir，属正常构建差异），已替换 Release 资产并核验 digest；control 仍为 1.0.20/arm64，PYZ 内 `unique_png_bytes` / `LightpdfRidingGroup` / 版本 `1.0.20` 标记齐全。
- `lightpdf-linux-build-1.0.20.zip` 为**源码快照，非安装包**，供麒麟本机离线构建。
- 已 push 并发布 GitHub Release。

**完整改动**：https://github.com/feitianhang123/lightpdf/compare/v1.0.19...v1.0.20
