# 轻PDF编辑器 (Light PDF Editor)

一个精简版、**净室实现**的 PDF 编辑器，参考主流 PDF 编辑软件的功能自行编写，基于开源组件
**PyMuPDF (MuPDF)** + **PySide6 (Qt)**。支持中文 / English 界面。

> ⚠️ 非官方软件，仅供学习与交流使用。本软件为独立实现的精简版 PDF 编辑器，
> 与任何商业 PDF 软件厂商均无从属或合作关系。如涉及侵权，请联系作者删除（QQ：10780329）。

## 下载安装

到 [**Releases**](https://github.com/feitianhang123/lightpdf/releases/latest) 下载：

| 系统 | 文件 |
|---|---|
| Windows（64 位） | `setup.exe` |
| 银河麒麟 V10 SP1 / Linux（ARM64，飞腾 / 鲲鹏） | `lightpdf_1.0.4_arm64.deb` |

**Windows**：双击 `setup.exe` 按向导安装（默认 `C:\Program Files\轻PDF编辑器`），开始菜单出现「轻PDF编辑器」。

**银河麒麟 / Debian 系（aarch64）**：
```bash
sudo dpkg -i lightpdf_1.0.4_arm64.deb
sudo apt-get -f install     # 若提示缺依赖，自动补齐
```
之后从开始菜单启动，或终端 `lightpdf 文件.pdf`；卸载 `sudo apt-get remove lightpdf`。

## 功能

- **查看与导航**：连续滚动 / 多页并排、缩放（滑块 / 滚轮 / 适应宽高 / 实际大小）、缩略图、书签目录、文本搜索、打印
- **批注与标记**：高亮、下划线、删除线、便签（可输入/查看内容）、文本框、矩形、椭圆、直线、箭头、自定义**图章**（文字/图片、形状与颜色可配置）
- **页面管理**：插入（可选位置）、**删除（当前页或 `1-3,5,8-10` 一次删多页）**、移动、旋转（当前/全部/指定页）、提取、拆分（按页数或自定义范围）、合并（可拖动排序）、水印、页眉页脚、页码/贝茨编号
- **内容编辑**：编辑文本（改字，可改字体字号）、插入/编辑文本框（自适应大小）、**插入图片（可移动、可缩放）**
- **文档对比**：像素级可视化差异 + 文本行差异
- **转换**：PDF 转图片、图片转 PDF（多图可排序、可选页面大小 A4/A3/A5/Letter 与"适应/原始大小"）
- **打印**：完整的多栏打印设置 —— 预览（缩放 / 页尺寸 / 纸张 / 翻页滑杆）、打印范围（当前视图 / 当前页 / 所有页 / 自定义页码 / 子集奇偶 / 逆序）、打印处理（缩放「无·适合·缩小·自定义%」、平铺大页面、每张多页、小册子）、双面（长 / 短边翻转）、自动旋转 / 居中、方向、打印内容、输出、灰度 / 作为图像 / 出血标记、份数 / 逐份、打印到文件、高级 / 打印提示
- **其它**：多标签页、**单实例（再次打开 PDF 在新标签页）**、撤回/前进、主题（浅绿）、中文/英文切换

## 运行（源码）

```bash
python -m pip install -r requirements.txt
python -m app.main            # 或 python -m app.main 文档.pdf
```

## 打包

### Windows（单文件 exe + Inno Setup 安装包）

```powershell
python -m PyInstaller --noconfirm --windowed --onefile --name "轻PDF编辑器" ^
  --icon icon.ico --version-file version_info.txt --paths . ^
  --add-data "icon.ico;." --add-data "resources;resources" run_app.py
ISCC.exe installer.iss                    # 生成 安装包\setup.exe
```

### 银河麒麟 / Linux（aarch64，`.deb`）

> 必须在目标机（同架构 Linux）上构建，PyInstaller 不支持跨平台编译。

```bash
git clone https://github.com/feitianhang123/lightpdf.git && cd lightpdf
bash packaging/linux/build-kylin.sh       # 一键：按需装系统依赖 + 打包
# 产物：dist/lightpdf_1.0.4_arm64.deb
```

离线拷贝时**只需源码**（约 0.6 MB）：`app/`、`run_app.py`、`requirements.txt`、`icon.ico`、
`resources/`、`packaging/linux/`；**不要**拷 `.venv-build/`、`build/`、`dist/` 等缓存。
详单见 [`packaging/linux/README.md`](packaging/linux/README.md#离线拷贝时要拷什么不用拷什么)。

也可分步执行：`packaging/linux/install_deps.sh`（装系统依赖）→ `packaging/linux/build_deb.sh`（打包）。
版本号自动读取 `app/version.py`，无需手改脚本。详见 [`packaging/linux/README.md`](packaging/linux/README.md)。

## 更新日志

### 1.0.5

- **页面管理**：「页面」菜单原「删除当前页」升级为「**删除页面...**」，一次可删当前页**或任意多页**。
  - 范围可选「当前页」（一键删除，等价于旧功能）或「指定页面（可多页）」，
    页码支持 `1-3,5,8-10`、单页、乱序、中文逗号；自动去重、排序、忽略越界页码。
  - 对话框实时显示"将删除 N 页：1-3, 5"，并禁止删除全部页面（PDF 至少保留 1 页）。
  - 删除后仍可用「编辑 → 撤销」恢复；删除后视图自动落到有效页。
- 麒麟 / Linux 安装包需按上文在麒麟（aarch64）机器上重新构建，
  产物为 `lightpdf_1.0.5_arm64.deb`；已发布的 `lightpdf_1.0.4_arm64.deb` 不含本次改动。

### 1.0.4

- **打印**：修复**已签章 PDF 的红色印章/电子签章印不出来**的问题。
  - 根因：红章在 PDF 里是**电子签章域（Signature Widget）的注释外观流**，而打印管线用
    `annots=False` 渲染，把这一层整个丢掉了 → 预览和打印都没有章。
  - 修复：打印渲染默认**包含注释**；新增**「打印印章与电子签章」**复选框，可一键开关
    （取消勾选则只打印正文，印章不会出现在预览与结果中）。
  - 同时修掉「每张多页 / 小册子」忽略该开关的旧 bug（原先硬编码为带注释），
    现在 **预览 == 输出 == 开关状态**，全部模式一致。
- 「打印内容」默认由「文档」改为**「文档和标记」**（已签章文档打开即可看到红章）；
  下拉框与印章复选框**双向联动**，不会互相矛盾。

### 1.0.3

- **打印**：修复三个实机问题
  - 「每张多页」预览方向与实际输出不一致 —— 预览纸面不再随内容变形，**预览 == 输出**；
  - 刚打开对话框时预览不是完整页 —— 底图与缩放解耦，布局完成后重算；
  - 部分网络复合机（如 Canon iR C3020）打不出来 —— 增加降级重试与明确的排查提示。
- **打包**：新增麒麟一键脚本 `packaging/linux/build-kylin.sh`；版本号改为自动读取 `app/version.py`。

### 1.0.2

- **打印**：重做打印对话框，改为**三栏完整布局**，新增 缩放 / 每张多页 / 平铺大页面 / 小册子 /
  双面 / 方向 / 打印内容 / 输出 / 灰度 / 作为图像 / 出血标记 / 份数 / 打印到文件 等选项。

## 依赖

- Python 3.8+（Windows 建议 3.10）
- 运行：PySide6、PyMuPDF、Pillow、numpy（见 `requirements.txt`；opencv/pytesseract/pdf2docx 为可选）
- 打包：PyInstaller；Windows 另需 Inno Setup 7

## 许可

[MIT](LICENSE)
