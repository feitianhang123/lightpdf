# 轻PDF编辑器 v1.0.3

> 精简版 PDF 编辑器 ｜ 基于 **PyMuPDF (MuPDF)** + **PySide6 (Qt)** ｜ 支持中文 / English
> 非官方软件，仅供学习交流，与任何商业 PDF 软件厂商均无从属或合作关系。

## 下载

| 系统 | 文件 | 大小 |
|---|---|---|
| Windows（64 位） | `setup.exe` | 89.8 MB |
| 银河麒麟 V10 SP1 / Linux（ARM64，飞腾 / 鲲鹏） | `lightpdf_1.0.3_arm64.deb` | 64.1 MB |

**Windows**：双击 `setup.exe` 按向导安装（默认 `C:\Program Files\轻PDF编辑器`），开始菜单出现「轻PDF编辑器」。

**银河麒麟 / Debian 系（aarch64）**：

```bash
sudo dpkg -i lightpdf_1.0.3_arm64.deb
sudo apt-get -f install     # 若提示缺依赖，自动补齐
```

之后从开始菜单启动，或终端 `lightpdf 文件.pdf`；卸载 `sudo apt-get remove lightpdf`。

## 本次更新

### 打印：三栏完整布局 + 三个实机问题修复

打印对话框重做为**三栏布局**：左「预览」，中「打印范围 / 打印处理」，右「双面 / 方向 / 打印内容 / 输出」。

修复三个实机问题：

- **「每张多页」预览方向与实际输出不一致** —— 根因是预览纸面被内容「撑变形」。
  现在纸面宽高比只由纸张方向决定、内容等比缩放居中，**预览 == 实际输出**；
  「方向」可选 自动 / 纵向 / 横向，自动时多页合一按网格形状判断（1×2、2×3 → 横向）。
- **刚打开对话框时预览不是完整页（要翻页才恢复正常）** —— 底图与缩放解耦，布局完成后重算。
- **部分网络复合机（如 Canon iR C3020）一直打不出来** —— 增加**降级重试**
  （第二次改用驱动默认值），失败时给出明确排查建议（方向 / 部门 ID / 先打印到文件 / 换驱动）。

完整选项：预览（缩放 / 页尺寸 / 纸张 / 翻页滑杆）· 打印范围（当前视图 / 当前页 / 所有页 /
自定义页码 `1,5-9,12` / 子集奇偶 / 逆序）· 打印处理（缩放「无·适合·缩小·自定义%」/ 平铺大页面 /
每张多页 / 小册子）· 双面（长 / 短边翻转）· 自动旋转 / 居中 · 方向 · 打印内容 · 输出 ·
灰度 / 作为图像 / 出血标记 · 份数 / 逐份 · 打印到文件。

### 打包与文档

- 新增麒麟一键打包脚本 `packaging/linux/build-kylin.sh`（按需装依赖 → 直接出 `.deb`）。
- `build_deb.sh` 版本号改为自动读取 `app/version.py`，不再硬编码。
- 新增 `.gitattributes`：源码与脚本统一 LF，避免在 Linux 上出现 `bad interpreter`。

## 完整性校验

| 文件 | 大小（字节） | SHA-256 |
|---|---|---|
| `setup.exe` | 94,147,788 | `2bb24f02cb49a4aecca798fefcbd9a8058c61ba9b948f7f2944f0a4b26ac6b96` |
| `lightpdf_1.0.3_arm64.deb` | 67,233,248 | `ddc95598d0103d60d73d6733363fdd28db4547e1a5a55e4d1c4e28ae41102fee` |

- `setup.exe` — 产品版本 **1.0.3**（Windows 64 位）
- `lightpdf_1.0.3_arm64.deb` — `Package: lightpdf` / `Version: 1.0.3` / `Architecture: arm64`（aarch64 ELF）

**完整改动**：https://github.com/feitianhang123/lightpdf/compare/v1.0.1...v1.0.3
