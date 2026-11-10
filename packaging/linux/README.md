# 在银河麒麟 V10 SP1（aarch64 / 飞腾 D3000）上构建 `.deb`

> PyInstaller **不能跨平台编译**，所以必须在**麒麟本机**（或同架构 Linux）构建。
> 下面三步即可产出并安装 `lightpdf_1.0.5_arm64.deb`。
>
> 版本号已改为**自动读取 `app/version.py`**（`build_deb.sh` 不再硬编码），以后升版本只改那一处。

## 0. 最快路径：一条命令

本仓库已包含全部源码。在麒麟机上 clone（或拷贝）后直接跑：

```bash
git clone https://github.com/feitianhang123/lightpdf.git
cd lightpdf
bash packaging/linux/build-kylin.sh        # 缺依赖会自动装，然后直接打包
# 产物：dist/lightpdf_1.0.5_arm64.deb
```

`build-kylin.sh` 会自动完成：修正 CRLF 换行 → 缺 `python3`/`venv` 时先装系统依赖 →
调用 `build_deb.sh`（建虚拟环境 → 装 PySide6/PyMuPDF → PyInstaller 打包 → 组装 `.deb`）。

### 离线拷贝时：要拷什么、不用拷什么

`build-kylin.sh` 只依赖**源码 + 三个脚本 + 图标/资源**，其余全是可重建的缓存。整个工作区
有 1.2 GB，但真正需要拷的只有约 **0.6 MB**（50 多个文件）。

**✅ 必须拷贝**（工程根目录）

| 路径 | 用途 |
|---|---|
| `packaging/linux/` | `build-kylin.sh`、`build_deb.sh`、`install_deps.sh`、`lightpdf.png` |
| `app/` | 全部 Python 源码（含 `version.py`，**版本号从这里读**） |
| `run_app.py` | PyInstaller 打包入口 |
| `requirements.txt` | 依赖声明 |
| `icon.ico`、`resources/` | 图标与「关于」页资源（`--add-data` 用） |

**❌ 不要拷贝**（要么自动重建，要么与 Linux 无关）

| 路径 | 原因 |
|---|---|
| `.venv-build/` | 625 MB 的 Linux 虚拟环境，`build_deb.sh` 开头就 `rm -rf` 重建 |
| `build/`、`dist/` | 265 MB + 315 MB 的旧构建产物，重新打包时会清掉 |
| `*__pycache__/` | 字节码缓存 |
| `*.deb` / `setup.exe` | 旧安装包，不是构建输入 |

> 💡 **最省事的做法**：工程根目录下的 **`lightpdf-linux-build-1.0.5.zip`**（0.6 MB）已经
> 按上面的清单打好包（`.sh` 已转 LF）。拷它过去解压即用：
> ```bash
> unzip lightpdf-linux-build-1.0.5.zip -d ~/lightpdf && cd ~/lightpdf
> bash packaging/linux/build-kylin.sh
> ```
>
> 也可以直接 `git clone` 仓库 —— 仓库里不含 `.venv-build/`、`build/`、`dist/`。
> 只想单独装系统依赖时：`bash packaging/linux/install_deps.sh`。

## 1. 把整个项目目录拷到麒麟

把整个项目目录（例如打包成 zip）复制到麒麟机器，例如放到 `~/lightpdf`。

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

产物：`dist/lightpdf_1.0.5_arm64.deb`（x86_64 上为 `amd64`）

## 4. 安装 / 卸载

```bash
sudo dpkg -i dist/lightpdf_1.0.5_arm64.deb
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

- 应用版本：`1.0.5`（见 `app/version.py`）
- 包名：`lightpdf`，桌面显示名：**轻PDF编辑器**
- 架构：脚本用 `dpkg --print-architecture` 自动识别（飞腾 D3000 → `arm64`）
