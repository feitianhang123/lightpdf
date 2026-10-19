# 在银河麒麟 V10 SP1（aarch64 / 飞腾 D3000）上构建 `.deb`

> PyInstaller **不能跨平台编译**，所以必须在**麒麟本机**（或同架构 Linux）构建。
> 下面三步即可产出并安装 `lightpdf_1.0.1_arm64.deb`。

## 1. 把整个项目目录拷到麒麟

把整个 `PDF编辑逆向软件` 目录（例如打包成 zip）复制到麒麟机器，例如放到 `~/lightpdf`。

```bash
cd ~/lightpdf
# 若从 Windows 拷贝过来，先修正 shell 脚本换行符
sed -i 's/\r$//' packaging/linux/*.sh
chmod +x packaging/linux/*.sh
```

## 2. 安装系统依赖

```bash
bash packaging/linux/install_deps.sh
```

（会 `apt-get` 安装 python3、venv、以及 Qt 运行所需的一批 `libxcb* / libgl1 / libegl1` 等库。）

## 3. 一键构建 `.deb`

```bash
bash packaging/linux/build_deb.sh
```

脚本会自动：创建虚拟环境 → 安装 PySide6 / PyMuPDF / Pillow / numpy / pyinstaller
→ 用 PyInstaller 打包（onedir）→ 组装并生成 `.deb`。

产物：`dist/lightpdf_1.0.1_arm64.deb`（x86_64 上为 `amd64`）

## 4. 安装 / 卸载

```bash
sudo dpkg -i dist/lightpdf_1.0.1_arm64.deb
sudo apt-get -f install     # 若提示缺依赖，自动补齐
```

- 安装后：开始菜单出现 **轻PDF编辑器**，也可终端直接运行 `lightpdf` 打开 PDF（`lightpdf 文件.pdf`）。
- 卸载：`sudo apt-get remove lightpdf`

## 不安装、直接试运行

```bash
./dist/lightpdf/lightpdf
```

## 常见问题

| 现象 | 处理 |
|---|---|
| `python3` 版本 < 3.8（PySide6 不支持） | 安装 Python 3.9/3.10 后再构建；或改用麒麟自带的 Python 3.8+ |
| pip 找不到 PySide6 / PyMuPDF 的 aarch64 轮子 | 升级 pip（`python -m pip install -U pip`）后重试；或指定较新版本 |
| 报错 `Failed building wheel for lxml` / `unrecognized command line option '-mno-neon'` | 旧版脚本会安装 `pikepdf`（它依赖 `lxml`，在麒麟上会源码编译失败）。已移除该依赖；请使用新版 `build_deb.sh`，或把安装命令里的 `pypdf pikepdf` 删掉、只装 `PySide6 PyMuPDF Pillow numpy pyinstaller` |
| 运行时报 `Could not load the Qt platform plugin "xcb"` | 缺 xcb 库，重跑 `install_deps.sh`；或 `sudo apt-get install libxcb-*` |
| 中文显示为方框 | 安装中文字体：`sudo apt-get install fonts-noto-cjk` |
| 缺少 OCR / Tesseract | 本功能已从菜单移除，可忽略；如需要：`sudo apt-get install tesseract-ocr tesseract-ocr-chi-sim` |

## 版本信息

- 应用版本：`1.0.1`（见 `app/version.py`）
- 包名：`lightpdf`，桌面显示名：**轻PDF编辑器**
- 架构：脚本用 `dpkg --print-architecture` 自动识别（飞腾 D3000 → `arm64`）
