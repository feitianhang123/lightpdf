# 轻PDF编辑器 v1.0.18

> 精简版 PDF 编辑器 ｜ 基于 **PyMuPDF (MuPDF)** + **PySide6 (Qt)** ｜ 支持中文 / English
> 非官方软件，仅供学习交流，与任何商业 PDF 软件厂商均无从属或合作关系。

## 一句话

印章默认直径改为 **42 mm**（国标公章常见尺寸）；骑缝章**恢复「加盖方式」选择**，并按印刷装订习惯统一为四种标准方式。

## 本次改动

### 1. 印章默认直径 42 mm

- 图章设置与骑缝章对话框的「印章直径」默认值为 **42.0 mm**（此前为 40 mm）。
- 平滑迁移：旧版像素配置、以及 v1.0.17 保存的 40 mm 默认值，升级后自动变为 42 mm；
  用户**手动改过**的其它数值保持不变，迁移只执行一次。

### 2. 骑缝章恢复「加盖方式」，统一为四种标准方式

v1.0.17 曾把左右贴放选择去掉（固定奇偶交替），本版恢复并规范化为印刷装订常用术语：

| 选项（中） | 选项（英） | 说明 |
|---|---|---|
| 奇数页右 / 偶数页左（双面装订，标准） | Odd pages right / even pages left (standard duplex) | 双面打印装订推荐，纸张叠齐拼成完整章 |
| 奇数页左 / 偶数页右（反向双面装订） | Odd pages left / even pages right (reverse duplex) | 反向装订顺序 |
| 全部盖在右侧（单面） | All on the right edge (simplex) | 每页都贴右边缘 |
| 全部盖在左侧（单面） | All on the left edge (simplex) | 每页都贴左边缘 |

- 奇偶判断按**真实页码**（1 起始）而非组内切片序号，因此从中间页开始盖也符合"奇数页/偶数页"的字面含义。
- 位置仍只用一个「距页顶距离（mm）」控制，所有盖章页同步上下移动；预览红条按所选方式实时反映左右落位。
- 默认值仍是标准双面装订（奇数页右 / 偶数页左），与 v1.0.17 的实际行为一致。

## 验证

- 默认直径：空配置 / 旧 `image_width` 配置 / v1.0.17 的 40 mm → 全部为 42 mm；自定义 33.5 mm 保留不变。
- 四种加盖方式在 6 页文档上的左右落位逐页符合预期，各页 `top_mm=148.5` 落位 y 均为 `420.945 pt`，完全一致。
- 从第 2 页起的非 1 起始范围，按真实页码奇偶判断正确（偶-奇-偶 → 左-右-左）。
- 冻结 exe 字节码核验：版本 `1.0.18`，`insert_riding_stamp` 含 `side` 参数与 `alternate_rev` 分支，42 mm 默认值与迁移标志、去背景逻辑均在。

## 安装包说明

| 文件 | 平台 | 大小（字节） | SHA-256 |
|---|---|---|---|
| `setup.exe` | Windows 64 位 | 94,187,514 | `dc2f39b9639f8c60e8201882fc2b2ecdbae0db7faee7eca114e9269ed5dad999` |
| `lightpdf_1.0.18_arm64.deb` | 银河麒麟 / Linux aarch64 | 待构建 | 待构建 |
| `lightpdf-linux-build-1.0.18.zip` | 麒麟本机离线构建用源码快照 | 1,276,324 | `a72c6252c8d43ebdaa3a8795395df5e70fa49bdea660e3f6ee09cfb673209d01` |

- `setup.exe` 用 Python 3.10 + PyInstaller 6.22.3 + Inno Setup 7 重新打包。
- 麒麟 `.deb` 需在麒麟 aarch64 本机用 `bash packaging/linux/build-kylin.sh` 重建。
- `lightpdf-linux-build-1.0.18.zip` 为**源码快照，非安装包**，供麒麟本机离线构建。
- 当前为**本地提交**，尚未 push / 发布 GitHub Release（等用户确认）。

**完整改动**：https://github.com/feitianhang123/lightpdf/compare/v1.0.17...v1.0.18
