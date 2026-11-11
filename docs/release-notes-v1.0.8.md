# 轻PDF编辑器 v1.0.8

> 精简版 PDF 编辑器 ｜ 基于 **PyMuPDF (MuPDF)** + **PySide6 (Qt)** ｜ 支持中文 / English
> 非官方软件，仅供学习交流，与任何商业 PDF 软件厂商均无从属或合作关系。

## 调整：下拉菜单与输入框的外框、高度完全统一

v1.0.6 曾把下拉菜单做成「淡绿底 + 2px 粗绿框 + 加粗文字」，还给「拆分方式」
单独放大到 30px。实测下来这样虽然醒目，但和同一表单里的输入框摆在一起显得突兀，
而且各行高低不齐。本版按反馈改成：**外框完全一致，高度完全一致，只靠底色与箭头区分**。

| | v1.0.6 / v1.0.7 | v1.0.8 |
|---|---|---|
| 下拉菜单外框 | `2px` 粗绿框、圆角 5px | **与输入框相同**：`1px` 细边、圆角 4px |
| 下拉菜单文字 | `font-weight: 600` 加粗 | 常规字重 |
| 展开的选项列表 | `2px` 粗绿框 | `1px` 细边 |
| 控件高度 | 输入框 30px、数字框 33px、拆分方式 30px | **全部 33px**，误差 0 |
| 区分方式 | 粗框 + 加粗 | 淡绿底 + 右侧绿色箭头按钮区 + 深绿向下三角 |

![拆分方式下拉菜单](preview/07_拆分方式下拉菜单.png)

![输入框与下拉菜单对比](preview/08_输入框与下拉菜单对比.png)

### 实现要点

- `app/ui/theme.py`：把 `QLineEdit` / `QComboBox` / `QSpinBox` / `QDoubleSpinBox`
  合并成同一条规则，共用 `border: 1px solid`、`border-radius: 4px`、`padding: 3px 6px`
  与固定内容高度；多行文本框（`QPlainTextEdit` / `QTextEdit`）沿用同一外框但高度仍由内容决定。
- `QSpinBox` 的上下按钮会让 Qt 的 `sizeHint()` 额外多算 3px。若直接用 `max-height`
  压平，上下小三角会被裁成两条横线；改为给它单独减 3px 的 `min-height`，
  并显式指定 `::up-button` / `::down-button` 尺寸，高度对齐的同时箭头完整。
- `_arrow_rules()`（原 `_combo_arrow_rules()`）在运行时绘制三张三角 PNG：
  下拉框的下三角，以及数字框的上 / 下三角，避免 Qt 用 CSS border 画三角时变成实心方块，
  也避免多余的原生灰色箭头。打包后无需附带任何图片资源。
- `app/ui/dialogs.py`：移除 `SplitDialog.mode` 的 `splitMode` 对象名，不再单独放大；
  悬浮提示「点击右侧箭头展开下拉菜单，选择拆分方式」保留。

## 下载

| 系统 | 文件 |
|---|---|
| Windows（64 位） | `setup.exe` |
| 银河麒麟 V10 SP1 / Linux（ARM64，飞腾 / 鲲鹏） | `lightpdf_1.0.8_arm64.deb` |

> ⚠️ PyInstaller 不支持跨平台编译，麒麟安装包**必须在麒麟（aarch64）本机重新构建**：
> `bash packaging/linux/build-kylin.sh`，产物 `dist/lightpdf_1.0.8_arm64.deb`。
> 已发布的 `lightpdf_1.0.4_arm64.deb` 不含 v1.0.5 ~ v1.0.8 的改动。
> 也可直接把工程根目录的 `lightpdf-linux-build-1.0.8.zip` 拷到麒麟解压后构建。

## 完整性校验

| 文件 | 大小（字节） | SHA-256 |
|---|---|---|
| `setup.exe` | 94,163,414 | `a3e0a27a8b9224f42d4cf91ba28d03dd48558d54782a2b68747d5d0b8188254b` |

- `setup.exe` — 产品版本 **1.0.8**（Windows 64 位）

## 回归验证

- 全局 QSS 断言：无 `border: 2px`、无 `font-weight: 600`、无 `#splitMode` 特殊高度规则，
  三条箭头规则齐全。
- 13 个对话框中的 **19 个下拉框**逐个渲染检查，右侧箭头按钮区均有可见深绿三角，
  文字区无多余灰色箭头。
- 13 个对话框中的 **54 个单行输入类控件** `sizeHint()` 全部为 33px（33..33），
  真实布局高度同样全部 33px；拆分 / 删除页面 / 旋转对话框内的混合控件逐行核对通过。
- 展开列表、禁用态、数字框上下三角、旋转页骑缝章、图片图章、多页删除与撤销、
  主窗口端到端流程全部复测通过；`app/` 全量 `compileall` 通过。

**完整改动**：https://github.com/feitianhang123/lightpdf/compare/v1.0.7...v1.0.8
