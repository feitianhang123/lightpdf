# 轻PDF编辑器 v1.0.10

> 精简版 PDF 编辑器 ｜ 基于 **PyMuPDF (MuPDF)** + **PySide6 (Qt)** ｜ 支持中文 / English
> 非官方软件，仅供学习交流，与任何商业 PDF 软件厂商均无从属或合作关系。

## 一句话

**修复保存 bug**：打开一个 PDF、改完点「保存」不再弹出
`Save failed: save to original must be incremental`。本版是纯修复版本，界面与功能不变。

## 问题现象

用「文件 → 打开」载入已有 PDF，做任何修改（编辑文字、插图章、删页、旋转页等）后按
`Ctrl+S` 或工具栏「保存」，弹出错误框：

```
失败
Save failed: save to original must be incremental
```

另存为到新文件不受影响，所以之前不容易察觉。

## 根因

`app/core/document.py` 的 `PdfDocument.save()` 对「保存到当前打开的文件」也走了
`doc.save(target, garbage=3, deflate=True)` 全量重写。PyMuPDF 1.28 明确禁止把文档全量写回它自己
正在读取的文件，抛出 `ValueError: save to original must be incremental`。

简单地改成增量保存并不能根治：本项目每次撤销 / 重做都会用 `restore_bytes()` 把文档换成
`fitz.open("pdf", bytes)` 内存副本，这种文档没有原始文件，增量保存会报
`incremental needs original file`。此外纯增量保存会不断往文件尾部追加修订，无法执行
`garbage=3` 清理，反复保存后文件会越来越大。

## 修复方式

`PdfDocument.save()` 现在区分两种情况：

| 场景 | 处理 |
|---|---|
| 保存到**新路径**（另存为、首次保存） | 保持原来的全量 `doc.save(...)` |
| 保存回**当前文件** | 内存序列化 → 同目录临时文件 → 关闭旧文档释放 Windows 文件句柄 → 原子替换 → 重新打开，使编辑会话继续绑定已保存的文件 |
| 显式 `incremental=True` 且 MuPDF 仍持有真实文件 | 仍走原生增量保存（可选快路径） |

细节：

- 序列化保留 `garbage=3`（清理已删除对象）与 `deflate=True`（压缩），也保留
  `encryption=PDF_ENCRYPT_KEEP`，加密 PDF 保存后仍是加密的、原密码有效。
- 重新打开时若文档需要密码，会用打开时保存的密码重新认证。
- 若写入失败（例如文件只读），会尽量恢复内存文档并抛出明确错误，**不会破坏原文件**，
  编辑会话仍可继续使用或另存为。
- 临时文件保存在目标文件同目录、以 `.lightpdf-` 开头，成功或失败后都会清理。
- `app/ui/main_window.py` 与界面、菜单、i18n 均未改动；v1.0.9 的浮动图片 / 印章交互保持原样。

## 覆盖场景与验证

`44` 项回归断言全部通过，`app/` 全量 `compileall` 通过：

- 修改后保存回原文件、连续多次保存、内容逐次落盘且不异常膨胀。
- 撤销 / 重做后的内存文档再保存；显式增量保存后再全量保存。
- 另存为后继续 `Ctrl+S`（后续修改写入新文件，原文件不被改动）。
- 加密 PDF（AES-256）保存后仍加密、密码有效、修改已写入。
- 删页后保存、中文 / 带空格路径、只读文件保存失败时不破坏文件。
- 主窗口端到端：浮动图片在保存前烘焙、文本与图片均落盘、无错误弹框。
- 保存后重新点选刚写进 PDF 的图片，移动后再次保存成功（v1.0.9 功能未回退）。

## 安装包说明

| 文件 | 平台 | 大小（字节） | SHA-256 |
|---|---|---|---|
| `setup.exe` | Windows 64 位 | 94,174,184 | `47649d3ddbccab36dbd587c883d683ed7bf9d008ff3e4a60e8e87413d19c6959` |
| `lightpdf_1.0.10_arm64.deb` | 银河麒麟 / Linux aarch64 | 待构建 | 待构建 |

- `setup.exe` 已重打包为 **1.0.10**（产品版本资源 `1.0.10`），包含上述修复。
- **麒麟 `.deb` 尚未重建**：仓库里现有的 `lightpdf_1.0.9_arm64.deb` 不含本次修复。
  需在麒麟 aarch64 本机执行 `bash packaging/linux/build-kylin.sh` 生成
  `lightpdf_1.0.10_arm64.deb`；离线源码快照 `lightpdf-linux-build-1.0.10.zip` 已同步更新。
- UI 保持现状，未做任何视觉改动（用户 2026-11-13 确认）。

**完整改动**：https://github.com/feitianhang123/lightpdf/compare/v1.0.9...v1.0.10
