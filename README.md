# 轻PDF编辑器 (Light PDF Editor)

一个精简版、**净室实现**的 PDF 编辑器，参考主流 PDF 编辑软件的功能自行编写，基于开源组件
**PyMuPDF (MuPDF)** + **PySide6 (Qt)**。支持中文 / English 界面。

> ⚠️ 非官方软件，仅供学习与交流使用。本软件通过 AI 复刻类似软件的功能实现，**与 Foxit/Adobe 等
> 厂商无任何关系**。如涉及侵权，请联系作者删除（QQ：10780329）。

## 功能

- **查看与导航**：连续滚动 / 多页并排、缩放（滑块 / 滚轮 / 适应宽高 / 实际大小）、缩略图、书签目录、文本搜索、打印
- **批注与标记**：高亮、下划线、删除线、便签（可输入/查看内容）、文本框、矩形、椭圆、直线、箭头、自定义**图章**（文字/图片、形状与颜色可配置）
- **页面管理**：插入（可选位置）、删除、移动、旋转（当前/全部/指定页）、提取、拆分（按页数或自定义范围）、合并（可拖动排序）、水印、页眉页脚、页码/贝茨编号
- **内容编辑**：编辑文本（改字，可改字体字号）、插入/编辑文本框（自适应大小）、插入图片
- **文档对比**：像素级可视化差异 + 文本行差异
- **转换**：PDF 转图片、图片转 PDF（多图可排序、可选页面大小 A4/A3/A5/Letter 与"适应/原始大小"）
- **打印**：仿 Foxit 打印对话框（预览全部页面、打印范围、打印处理、双面、方向、纸张、份数、打印到文件、**小册子拼版**）
- **其它**：多标签页、撤回/前进、主题（浅绿）、中文/英文切换

## 运行（源码）

```powershell
python -m pip install -r requirements.txt
python -m app.main            # 或 python -m app.main 文档.pdf
```

## 打包为 Windows 程序 / 安装包

```powershell
# 1) 生成单文件 exe
python -m PyInstaller --noconfirm --windowed --onefile --name "轻PDF编辑器" ^
  --icon icon.ico --paths . --add-data "icon.ico;." --add-data "resources;resources" ^
  run_app.py

# 2) 用 Inno Setup 生成安装程序（installer.iss 已提供）
ISCC.exe installer.iss
```

## 依赖

- Python 3.10
- PySide6、PyMuPDF、pikepdf、pypdf、Pillow、numpy（见 `requirements.txt`）
- 打包：PyInstaller、Inno Setup 7

## 许可

[MIT](LICENSE)
