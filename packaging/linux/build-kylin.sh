#!/usr/bin/env bash
# ============================================================
#  轻PDF编辑器 · 银河麒麟 / Debian(aarch64) 一键打包 .deb
#
#  用法（在麒麟机器上，于工程根目录执行）：
#      bash packaging/linux/build-kylin.sh
#
#  产物：dist/lightpdf_<版本>_arm64.deb
#  说明：版本号自动读 app/version.py，无需手改。
# ============================================================
set -euo pipefail
cd "$(dirname "$0")/../.."          # 回到工程根目录

echo "==> 工程目录：$(pwd)"

# 0) 防御：若从 Windows 拷贝导致脚本变成 CRLF 换行，自动修正
for f in packaging/linux/*.sh; do
  sed -i 's/\r$//' "$f" 2>/dev/null || true
done

# 1) 缺 python3 / venv 时自动安装系统依赖（需要 sudo 密码）
if ! command -v python3 >/dev/null 2>&1 \
   || ! python3 -c 'import venv, ssl, ensurepip' >/dev/null 2>&1; then
  echo "==> 检测到缺少 python3 / venv，先安装系统依赖（会要 sudo 密码）"
  bash packaging/linux/install_deps.sh
fi

echo "==> python3: $(python3 -V)"
echo "==> 开始构建（首次会建虚拟环境并下载 PySide6 / PyMuPDF，约几分钟）"

# 2) 构建 .deb
bash packaging/linux/build_deb.sh

echo
echo "==> 完成！产物："
ls -lh dist/*.deb
echo
echo "安装： sudo dpkg -i dist/lightpdf_$(sed -n 's/^__version__ *= *"\([^"]*\)".*/\1/p' app/version.py)_*.deb"
