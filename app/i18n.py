"""Minimal i18n with runtime language switching. Default language: Chinese."""
from __future__ import annotations

from PySide6.QtCore import QSettings

_SETTINGS = QSettings("MiniPDF", "MiniPDFEditor")
DEFAULT_LANG = "zh"

_LANG = DEFAULT_LANG

STRINGS: dict[str, dict[str, str]] = {
    # app / menus
    "app.title": {"zh": "轻PDF编辑器", "en": "Light PDF Editor"},
    "menu.file": {"zh": "文件", "en": "File"},
    "menu.edit": {"zh": "编辑", "en": "Edit"},
    "menu.view": {"zh": "视图", "en": "View"},
    "menu.annotate": {"zh": "批注", "en": "Annotate"},
    "menu.pages": {"zh": "页面", "en": "Pages"},
    "menu.compare": {"zh": "对比", "en": "Compare"},
    "menu.convert": {"zh": "转换", "en": "Convert"},
    "menu.settings": {"zh": "设置", "en": "Settings"},
    "menu.help": {"zh": "帮助", "en": "Help"},
    "menu.language": {"zh": "语言", "en": "Language"},
    "lang.zh": {"zh": "中文", "en": "中文 (Chinese)"},
    "lang.en": {"zh": "English", "en": "English"},
    "about.title": {"zh": "关于", "en": "About"},
    "about.body": {
        "zh": "轻PDF编辑器\n\n一个精简版的 PDF 编辑器，基于 PyMuPDF (MuPDF) + PySide6 (Qt) 独立实现。\n仅供学习与交流使用；如涉及侵权请联系作者。\nQQ：10780329\n请作者喝咖啡：",
        "en": "Light PDF Editor\n\nA trimmed PDF editor, independently implemented with PyMuPDF (MuPDF) + PySide6 (Qt).\n"
              "For learning and evaluation only; if it infringes any rights, please contact the author.\n"
              "QQ: 10780329\nBuy the author a coffee:"},
    "about.wechat": {"zh": "微信", "en": "WeChat"},
    "about.alipay": {"zh": "支付宝", "en": "Alipay"},

    # file actions
    "act.new": {"zh": "新建", "en": "New"},
    "act.open": {"zh": "打开...", "en": "Open..."},
    "act.save": {"zh": "保存", "en": "Save"},
    "act.save_as": {"zh": "另存为...", "en": "Save As..."},
    "act.close": {"zh": "关闭", "en": "Close"},
    "act.properties": {"zh": "文档属性...", "en": "Properties..."},
    "act.print": {"zh": "打印...", "en": "Print..."},
    "act.exit": {"zh": "退出", "en": "Exit"},

    # view actions
    "act.zoom_in": {"zh": "放大", "en": "Zoom In"},
    "act.zoom_out": {"zh": "缩小", "en": "Zoom Out"},
    "act.fit_width": {"zh": "适应宽度", "en": "Fit Width"},
    "act.fit_page": {"zh": "适应页面", "en": "Fit Page"},
    "act.actual": {"zh": "实际大小", "en": "Actual Size"},
    "act.rotate_cw": {"zh": "顺时针旋转", "en": "Rotate CW"},
    "act.rotate_ccw": {"zh": "逆时针旋转", "en": "Rotate CCW"},
    "act.next": {"zh": "下一页", "en": "Next Page"},
    "act.prev": {"zh": "上一页", "en": "Previous Page"},

    # edit actions
    "act.edit_text": {"zh": "编辑文本（改字）", "en": "Edit Text (touchup)"},
    "act.insert_image": {"zh": "插入图片...", "en": "Insert Image..."},
    "act.insert_text": {"zh": "插入文本框", "en": "Insert Text Box"},
    "act.whiteout": {"zh": "涂抹擦除", "en": "White-out / Erase"},
    "act.find": {"zh": "查找...", "en": "Find..."},
    "act.compare": {"zh": "与...对比", "en": "Compare with..."},
    "act.undo": {"zh": "撤回", "en": "Undo"},
    "act.redo": {"zh": "前进", "en": "Redo"},
    "msg.unsaved.title": {"zh": "未保存的修改", "en": "Unsaved changes"},
    "msg.unsaved.body": {"zh": "“{name}”已被修改，是否保存？",
                         "en": "“{name}” has unsaved changes. Save it?"},

    # print dialog
    "print.title": {"zh": "打印", "en": "Print"},
    "print.printer": {"zh": "打印机", "en": "Printer"},
    "print.advanced": {"zh": "高级选项...", "en": "Advanced..."},
    "print.range": {"zh": "打印范围", "en": "Print Range"},
    "print.range.all": {"zh": "全部", "en": "All"},
    "print.range.current": {"zh": "当前页", "en": "Current page"},
    "print.range.pages": {"zh": "页面", "en": "Pages"},
    "print.to": {"zh": "到", "en": "to"},
    "print.content": {"zh": "打印处理", "en": "Print Handling"},
    "print.content.doc": {"zh": "文档", "en": "Document"},
    "print.content.markup": {"zh": "文档和标记", "en": "Document and Markups"},
    "print.scale": {"zh": "页面缩放", "en": "Page Scaling"},
    "print.scale.fit": {"zh": "适合可打印区域", "en": "Fit to printable area"},
    "print.scale.none": {"zh": "实际大小", "en": "Actual size"},
    "print.scale.shrink": {"zh": "缩小过大页面", "en": "Shrink oversized pages"},
    "print.duplex": {"zh": "双面打印", "en": "Print on Both Sides"},
    "print.duplex.simplex": {"zh": "单面", "en": "Simplex"},
    "print.duplex.long": {"zh": "双面（长边翻转）", "en": "Flip on long edge"},
    "print.duplex.short": {"zh": "双面（短边翻转）", "en": "Flip on short edge"},
    "print.orientation": {"zh": "方向", "en": "Orientation"},
    "print.orientation.auto": {"zh": "自动", "en": "Auto"},
    "print.orientation.portrait": {"zh": "纵向", "en": "Portrait"},
    "print.orientation.landscape": {"zh": "横向", "en": "Landscape"},
    "print.paper": {"zh": "纸张大小", "en": "Paper Size"},
    "print.paper.auto": {"zh": "打印机默认", "en": "Printer default"},
    "print.copies": {"zh": "份数", "en": "Copies"},
    "print.collate": {"zh": "逐份打印", "en": "Collate"},
    "print.tofile": {"zh": "打印到文件", "en": "Print to file"},
    "print.preview": {"zh": "预览", "en": "Preview"},
    "print.button": {"zh": "打印", "en": "Print"},
    "btn.cancel": {"zh": "取消", "en": "Cancel"},
    "print.no_printer": {"zh": "未找到可用打印机。", "en": "No printer available."},
    "print.failed": {"zh": "打印失败。", "en": "Printing failed."},

    # tools
    "tool.hand": {"zh": "手形", "en": "Hand"},
    "tool.select": {"zh": "选择", "en": "Select"},
    "tool.highlight": {"zh": "高亮", "en": "Highlight"},
    "tool.underline": {"zh": "下划线", "en": "Underline"},
    "tool.strikeout": {"zh": "删除线", "en": "Strikeout"},
    "tool.note": {"zh": "便签", "en": "Note"},
    "tool.freetext": {"zh": "文本框", "en": "Free Text"},
    "tool.ink": {"zh": "手绘", "en": "Ink"},
    "tool.rect": {"zh": "矩形", "en": "Rectangle"},
    "tool.ellipse": {"zh": "椭圆", "en": "Ellipse"},
    "tool.line": {"zh": "直线", "en": "Line"},
    "tool.arrow": {"zh": "箭头", "en": "Arrow"},
    "tool.stamp": {"zh": "图章", "en": "Stamp"},
    "tool.edittext": {"zh": "编辑文本", "en": "Edit Text"},
    "tool.whiteout": {"zh": "涂抹", "en": "White-out"},
    "tool.insertimage": {"zh": "插入图片", "en": "Insert Image"},

    # annotate extras
    "annot.markup_color": {"zh": "标记颜色与透明度...", "en": "Markup Color & Opacity..."},
    "annot.pen_color": {"zh": "选择画笔颜色...", "en": "Choose Pen Color..."},
    "annot.list": {"zh": "列出批注", "en": "List Annotations"},
    "annot.stamp_settings": {"zh": "图章设置...", "en": "Stamp Settings..."},
    "annot.riding_stamp": {"zh": "插入骑缝章...", "en": "Insert Riding Stamp..."},
    "dlg.stamp.title": {"zh": "图章设置", "en": "Stamp Settings"},
    "dlg.stamp.type": {"zh": "类型", "en": "Type"},
    "stamp.text": {"zh": "文字图章", "en": "Text stamp"},
    "stamp.image": {"zh": "图片图章", "en": "Image stamp"},
    "dlg.stamp.text": {"zh": "文字内容", "en": "Text"},
    "dlg.stamp.font": {"zh": "字体", "en": "Font"},
    "dlg.stamp.size": {"zh": "字号", "en": "Font size"},
    "dlg.stamp.textcolor": {"zh": "文字颜色", "en": "Text color"},
    "dlg.stamp.shape": {"zh": "形状", "en": "Shape"},
    "shape.rect": {"zh": "矩形", "en": "Rectangle"},
    "shape.round": {"zh": "圆角矩形", "en": "Rounded"},
    "shape.ellipse": {"zh": "椭圆", "en": "Ellipse"},
    "shape.none": {"zh": "无边框", "en": "None"},
    "dlg.stamp.border": {"zh": "边框颜色", "en": "Border color"},
    "dlg.stamp.borderw": {"zh": "边框宽度", "en": "Border width"},
    "dlg.stamp.fill": {"zh": "填充颜色", "en": "Fill color"},
    "dlg.stamp.transparent": {"zh": "透明背景", "en": "Transparent"},
    "dlg.stamp.image": {"zh": "图章图片", "en": "Stamp image"},
    "dlg.stamp.choose": {"zh": "选择图片...", "en": "Choose image..."},
    "dlg.stamp.width": {"zh": "显示宽度", "en": "Display width"},
    "dlg.stamp.preview": {"zh": "预览", "en": "Preview"},
    "dlg.stamp.image_hint": {
        "zh": "选择图片后会自动切换为「图片图章」；图片会保存到软件配置目录，之后移动或删除原文件也不影响使用。",
        "en": "Picking a file switches the type to 'Image stamp' automatically. The image is copied into the app's settings folder, so moving or deleting the original file is safe.",
    },
    "dlg.stamp.imported": {
        "zh": "原图：{name}（已保存到软件配置目录）",
        "en": "Source: {name} (copied into the app's settings folder)",
    },

    # riding / perforation stamp (骑缝章)
    "dlg.riding.title": {"zh": "插入骑缝章", "en": "Insert Riding Stamp"},
    "dlg.riding.source": {"zh": "图章来源", "en": "Stamp source"},
    "dlg.riding.use_config": {
        "zh": "使用当前图章设置（文字图章 / 图片图章）",
        "en": "Use current stamp settings (text / image)",
    },
    "dlg.riding.use_file": {"zh": "本次另选图片...", "en": "Pick another image for this job..."},
    "dlg.riding.no_file": {"zh": "未选择图片，请点「选择图片...」。", "en": "No image chosen. Click 'Choose image...' first."},
    "dlg.riding.scope": {"zh": "页面范围", "en": "Pages"},
    "dlg.riding.from_current": {"zh": "从当前页到末页", "en": "From current page to the end"},
    "dlg.riding.range": {"zh": "指定页面（如 1-3,5,8-10）", "en": "Selected pages (e.g. 1-3,5,8-10)"},
    "dlg.riding.group": {"zh": "每枚章覆盖页数", "en": "Pages per seal"},
    "dlg.riding.group_auto": {"zh": "自动（所有页共用一枚章）", "en": "Auto (one seal for all pages)"},
    "dlg.riding.side": {"zh": "贴放位置", "en": "Edge"},
    "dlg.riding.side_alternate": {
        "zh": "左右交替（双面打印，推荐）",
        "en": "Alternate left / right (duplex, recommended)",
    },
    "dlg.riding.side_right": {"zh": "全部贴右侧（单面打印）", "en": "All on the right edge (simplex)"},
    "dlg.riding.side_left": {"zh": "全部贴左侧", "en": "All on the left edge"},
    "dlg.riding.vpos": {"zh": "垂直位置", "en": "Vertical position"},
    "dlg.riding.v_middle": {"zh": "垂直居中", "en": "Center"},
    "dlg.riding.v_top": {"zh": "靠上", "en": "Top"},
    "dlg.riding.v_bottom": {"zh": "靠下", "en": "Bottom"},
    "dlg.riding.v_custom": {"zh": "自定义", "en": "Custom"},
    "dlg.riding.vpercent": {"zh": "垂直偏移", "en": "Vertical offset"},
    "dlg.riding.width": {"zh": "印章总宽度", "en": "Seal width"},
    "dlg.riding.margin": {"zh": "距页边距离", "en": "Distance from edge"},
    "dlg.riding.overlap": {"zh": "切片重叠补偿", "en": "Slice overlap"},
    "dlg.riding.reverse": {
        "zh": "从图章右侧开始切片（反向装订）",
        "en": "Start slicing from the right side of the seal",
    },
    "dlg.riding.no_pages": {
        "zh": "没有选中有效页面，请检查页面范围。",
        "en": "No valid pages selected. Check the page range.",
    },
    "dlg.riding.info": {
        "zh": "共 {n} 页 → {groups} 枚章，每枚切 {g} 片，每片约 {w} × {h} pt。",
        "en": "{n} pages -> {groups} seal(s), {g} slices each, about {w} x {h} pt per slice.",
    },
    "dlg.riding.hint": {
        "zh": "上方是切片拼接还原效果，下方是各页落位示意（红条）。双面打印请用「左右交替」，纸张叠齐即可拼出完整印章；插入后可用「编辑 → 撤销」一次恢复。",
        "en": "Top: the reassembled seal. Bottom: where each slice lands on the pages (red bars). For duplex printing use 'Alternate'; stacking the sheets rebuilds the full seal. One Undo reverts everything.",
    },
    "msg.riding_done": {
        "zh": "已在 {n} 页插入骑缝章，可用「编辑 → 撤销」恢复。",
        "en": "Riding stamp placed on {n} pages. Use Edit > Undo to revert.",
    },
    "msg.stamp_invalid": {
        "zh": "当前图章无法使用：{reason}\n请在「图章设置」中重新选择。",
        "en": "The current stamp cannot be used: {reason}\nPlease fix it in Stamp Settings.",
    },

    # editable image / stamp objects (size & position)
    "act.object_props": {"zh": "调整图片 / 印章...", "en": "Size && Position..."},
    "dlg.object.title": {"zh": "调整大小与位置", "en": "Size & Position"},
    "dlg.object.x": {"zh": "水平位置 X (pt)", "en": "Left X (pt)"},
    "dlg.object.y": {"zh": "垂直位置 Y (pt)", "en": "Top Y (pt)"},
    "dlg.object.width": {"zh": "宽度 (pt)", "en": "Width (pt)"},
    "dlg.object.height": {"zh": "高度 (pt)", "en": "Height (pt)"},
    "dlg.object.aspect": {"zh": "锁定宽高比", "en": "Lock aspect ratio"},
    "dlg.object.delete": {"zh": "删除此对象", "en": "Delete this object"},
    "dlg.object.hint": {
        "zh": "也可直接在页面上操作：拖动移动、拖动八个控制点缩放（按住 Shift 自由缩放）、方向键微调（Shift 加速）、Delete 删除。",
        "en": "On the page: drag to move, drag any of the eight handles to resize (hold Shift for free resize), arrow keys to nudge (Shift for bigger steps), Delete to remove.",
    },
    "dlg.object.kind_image": {"zh": "图片", "en": "image"},
    "dlg.object.kind_stamp": {"zh": "图章", "en": "stamp"},
    "msg.object_inserted": {
        "zh": "已插入{kind}：拖动可移动，拖动蓝色控制点可缩放，双击可精确调整；保存时写入 PDF。",
        "en": "{kind} added: drag to move, drag the blue handles to resize, double-click for exact values. It is written into the PDF on save.",
    },
    "msg.object_selected": {
        "zh": "已选中页面上的图片 / 印章，现在可拖动调整位置或双击调整大小。",
        "en": "Selected an embedded image / stamp. Drag to reposition or double-click to resize.",
    },
    "msg.object_none": {
        "zh": "请先在页面上单击选中一个图片或图章（出现蓝色控制点）后再使用此命令。",
        "en": "Click an image or stamp on the page first (blue handles appear), then use this command.",
    },
    "status.object_tip": {
        "zh": "拖动移动 · 控制点缩放 · 双击精确调整 · Delete 删除",
        "en": "Drag to move · handles to resize · double-click for exact values · Delete to remove",
    },
    "dlg.markup.title": {"zh": "标记样式", "en": "Markup Style"},
    "dlg.markup.color": {"zh": "颜色", "en": "Color"},
    "dlg.markup.opacity": {"zh": "不透明度 (%)", "en": "Opacity (%)"},
    "zoom.label": {"zh": "{p}%", "en": "{p}%"},

    # pages menu
    "pages.insert": {"zh": "从 PDF 插入页面...", "en": "Insert Pages from PDF..."},
    "pages.delete": {"zh": "删除页面...", "en": "Delete Pages..."},
    "pages.extract": {"zh": "提取页面...", "en": "Extract Pages..."},
    "pages.split": {"zh": "拆分...", "en": "Split..."},
    "pages.merge": {"zh": "合并 PDF...", "en": "Merge PDFs..."},
    "pages.move_up": {"zh": "页面上移", "en": "Move Page Up"},
    "pages.move_down": {"zh": "页面下移", "en": "Move Page Down"},
    "pages.rotate_all": {"zh": "全部页面顺时针旋转", "en": "Rotate All Pages CW"},
    "pages.watermark": {"zh": "水印...", "en": "Watermark..."},
    "pages.header_footer": {"zh": "页眉页脚...", "en": "Header & Footer..."},
    "pages.page_numbers": {"zh": "页码 / 贝茨编号...", "en": "Page Numbers / Bates..."},

    # convert menu
    "convert.pdf_to_images": {"zh": "PDF 转图片...", "en": "PDF to Images..."},
    "convert.images_to_pdf": {"zh": "图片转 PDF...", "en": "Images to PDF..."},
    "convert.pdf_to_text": {"zh": "PDF 转文本...", "en": "PDF to Text..."},
    "convert.pdf_to_html": {"zh": "PDF 转 HTML...", "en": "PDF to HTML..."},
    "convert.pdf_to_word": {"zh": "PDF 转 Word...", "en": "PDF to Word..."},
    "convert.pdf_to_pdfa": {"zh": "PDF 转 PDF/A...", "en": "PDF to PDF/A..."},
    "convert.ocr_searchable": {"zh": "OCR 转可搜索 PDF...", "en": "OCR -> Searchable PDF..."},
    "convert.ocr_text": {"zh": "OCR 转文本...", "en": "OCR -> Text..."},

    # status bar
    "status.no_doc": {"zh": "未打开文档", "en": "No document"},
    "status.page": {"zh": "第 {n} / {total} 页", "en": "Page {n} / {total}"},
    "status.zoom": {"zh": "缩放 {p}%", "en": "Zoom {p}%"},
    "status.hits": {"zh": "{n} 处匹配", "en": "{n} hits"},
    "status.tool": {"zh": "工具：{t}", "en": "Tool: {t}"},
    "status.saved": {"zh": "已保存", "en": "Saved."},
    "status.saved_to": {"zh": "已保存到 {p}", "en": "Saved to {p}"},
    "status.comparing": {"zh": "正在对比...", "en": "Comparing..."},
    "status.ocr_running": {"zh": "正在 OCR...", "en": "Running OCR..."},

    # docks / panels
    "dock.navigation": {"zh": "导航", "en": "Navigation"},
    "dock.results": {"zh": "搜索 / 批注", "en": "Search / Annotations"},
    "tab.thumbnails": {"zh": "缩略图", "en": "Thumbnails"},
    "tab.outline": {"zh": "书签目录", "en": "Outline"},
    "page.label": {"zh": "第 {n} 页", "en": "Page {n}"},
    "btn.color": {"zh": "颜色...", "en": "Color..."},

    # dialogs
    "dlg.watermark.title": {"zh": "添加水印", "en": "Add Watermark"},
    "dlg.watermark.text": {"zh": "文字", "en": "Text"},
    "dlg.watermark.size": {"zh": "字号", "en": "Font size"},
    "dlg.watermark.opacity": {"zh": "不透明度", "en": "Opacity"},
    "dlg.watermark.angle": {"zh": "角度", "en": "Angle"},
    "dlg.hf.title": {"zh": "页眉页脚", "en": "Header & Footer"},
    "dlg.hf.header": {"zh": "页眉文字", "en": "Header text"},
    "dlg.hf.footer": {"zh": "页脚文字", "en": "Footer text"},
    "dlg.hf.size": {"zh": "字号", "en": "Font size"},
    "dlg.pn.title": {"zh": "插入页码 / 贝茨编号", "en": "Insert Page Numbers / Bates"},
    "dlg.pn.template": {"zh": "模板 ({n}, {total})", "en": "Template ({n}, {total})"},
    "dlg.pn.prefix": {"zh": "前缀（贝茨）", "en": "Prefix (Bates)"},
    "dlg.pn.start": {"zh": "起始编号", "en": "Start number"},
    "dlg.pn.position": {"zh": "位置", "en": "Position"},
    "pos.bottom": {"zh": "底部", "en": "bottom"},
    "pos.top": {"zh": "顶部", "en": "top"},
    "dlg.split.title": {"zh": "拆分文档", "en": "Split Document"},
    "dlg.split.every": {"zh": "每个文件页数 (1..{n})", "en": "Pages per file (1..{n})"},
    "dlg.split.mode": {"zh": "拆分方式", "en": "Split by"},
    "dlg.split.mode_tip": {
        "zh": "点击右侧箭头展开下拉菜单，选择拆分方式",
        "en": "Click the arrow to open the drop-down list and pick a split mode"},
    "split.equal": {"zh": "按页数均分", "en": "Equal pages"},
    "split.ranges": {"zh": "自定义范围", "en": "Custom ranges"},
    "dlg.split.ranges": {"zh": "范围（如 1-3,4-8,9）", "en": "Ranges (e.g. 1-3,4-8,9)"},
    "dlg.edit.title": {"zh": "编辑文本", "en": "Edit Text"},
    "dlg.edit.label": {"zh": "编辑文字后点击“确定”：", "en": "Edit the text run, then Apply:"},
    "dlg.textbox.title": {"zh": "文本框", "en": "Text Box"},
    "dlg.edit.font": {"zh": "字体", "en": "Font"},
    "dlg.edit.size": {"zh": "字号", "en": "Font size"},
    "dlg.edit.original": {"zh": "保持原字体", "en": "Keep original"},
    "dlg.edit.font_default": {"zh": "默认", "en": "Default"},
    "print.content.booklet": {"zh": "小册子", "en": "Booklet"},
    "print.booklet.binding": {"zh": "小册子装订", "en": "Booklet binding"},
    "print.booklet.left": {"zh": "左装订（向左翻）", "en": "Left (flip left)"},
    "print.booklet.right": {"zh": "右装订（向右翻）", "en": "Right (flip right)"},
    "print.booklet.subset": {"zh": "打印面", "en": "Booklet subset"},
    "print.booklet.both": {"zh": "双面", "en": "Both sides"},
    "print.booklet.front": {"zh": "仅正面", "en": "Front side only"},
    "print.booklet.back": {"zh": "仅背面", "en": "Back side only"},
    "print.booklet.autorotate": {"zh": "自动旋转页面", "en": "Auto-rotate pages"},
    # --- 打印对话框（多栏布局）文案
    "print.name": {"zh": "名称:", "en": "&Name:"},
    "print.properties": {"zh": "属性", "en": "&Properties"},
    "print.ok": {"zh": "确定", "en": "OK"},
    "print.props_hint": {"zh": "打印机属性由操作系统管理。", "en": "Printer settings are managed by your operating system."},
    "print.print_as_grayscale": {"zh": "灰度打印", "en": "Print as grayscale"},
    "print.print_as_image": {"zh": "作为图像打印", "en": "Print as image"},
    "print.bleed_marks": {"zh": "出血标记", "en": "Bleed Marks"},
    "print.zoom": {"zh": "缩放:", "en": "Zoom:"},
    "print.document": {"zh": "文档:", "en": "Document:"},
    "print.paper_label": {"zh": "纸张:", "en": "Paper:"},
    "print.range.view": {"zh": "当前视图", "en": "Current view"},
    "print.range.all_pages": {"zh": "所有页面", "en": "All pages"},
    "print.range.pages_label": {"zh": "页面:", "en": "Pa&ges:"},
    "print.range.sample": {"zh": "示例: 1,5-9,12", "en": "Sample: 1,5-9,12"},
    "print.subset": {"zh": "子集:", "en": "Su&bset:"},
    "print.subset.all": {"zh": "范围内全部页面", "en": "All Pages in Range"},
    "print.subset.odd": {"zh": "仅奇数页", "en": "Odd pages only"},
    "print.subset.even": {"zh": "仅偶数页", "en": "Even pages only"},
    "print.reverse": {"zh": "逆序打印", "en": "R&everse pages"},
    "print.handling.scale": {"zh": "缩放", "en": "&Scale"},
    "print.handling.tile": {"zh": "平铺大页面", "en": "Tile &Large Pages"},
    "print.handling.nup": {"zh": "每张多页", "en": "&Multiple Pages Per Sheet"},
    "print.handling.booklet": {"zh": "小册子", "en": "Boo&klet"},
    "print.scale.opt.none": {"zh": "无", "en": "None"},
    "print.scale.opt.fit": {"zh": "适合打印机边距", "en": "&Fit to printer margins"},
    "print.scale.opt.reduce": {"zh": "缩小到打印机边距", "en": "Re&duce to printer margins"},
    "print.scale.opt.custom": {"zh": "自定义比例", "en": "Custom scale"},
    "print.scale.choose_paper": {"zh": "按 PDF 页面大小选择纸张来源", "en": "Choose paper source by PDF page si&ze"},
    "print.tile.zoom": {"zh": "页面缩放", "en": "Page Zoom"},
    "print.tile.overlap": {"zh": "重叠 (英寸)", "en": "Overlap (in)"},
    "print.tile.cutmarks": {"zh": "裁切标记", "en": "Cut Marks"},
    "print.tile.labels": {"zh": "标签", "en": "Labels"},
    "print.nup.per_sheet": {"zh": "每张纸页数", "en": "Pages per sheet"},
    "print.nup.order": {"zh": "页面顺序", "en": "Page order"},
    "print.nup.order.h": {"zh": "水平", "en": "Horizontal"},
    "print.nup.order.hr": {"zh": "水平反转", "en": "Horizontal Reversed"},
    "print.nup.order.v": {"zh": "垂直", "en": "Vertical"},
    "print.nup.order.vr": {"zh": "垂直反转", "en": "Vertical Reversed"},
    "print.nup.border": {"zh": "打印页面边框", "en": "Print page border"},
    "print.duplex.both": {"zh": "在纸张双面打印", "en": "Print on both sides of paper"},
    "print.autorotate": {"zh": "自动旋转", "en": "Auto-&Rotate"},
    "print.autocenter": {"zh": "自动居中", "en": "Auto-Center"},
    "print.what": {"zh": "打印内容", "en": "Print &What"},
    "print.what.doc": {"zh": "文档", "en": "Document"},
    "print.what.markup": {"zh": "文档和标记", "en": "Document and Markups"},
    "print.what.stamps": {"zh": "文档和图章", "en": "Document and Stamps"},
    "print.what.formfields": {"zh": "仅表单域", "en": "Form Fields only"},
    "print.signature": {"zh": "打印印章与电子签章", "en": "Print stamps and signatures"},
    "print.signature.tip": {
        "zh": "勾选后打印文档中的红色印章、电子签章、图章、批注等「注释」内容；\n"
              "取消勾选则只打印文档正文（印章不会出现在预览和打印结果中）。",
        "en": "When checked, prints annotations such as red seals, digital signatures,\n"
              "stamps and comments. When unchecked, only the document body is printed."},
    "print.output": {"zh": "输出", "en": "Output"},
    "print.output.summarize": {"zh": "汇总注释", "en": "Summarize Comments"},
    "print.output.overprint": {"zh": "模拟叠印", "en": "Simulate Overprinting"},
    "print.tips": {"zh": "打印提示", "en": "Printing Tips"},
    "print.tips_text": {
        "zh": "· 双面打印需打印机支持；\n· 小册子会自动启用横向与短边翻转；\n· 缩放选“无”时按 100% 输出；\n· 打印时间较长时可勾选“作为图像打印”。",
        "en": "\u00b7 Duplex requires printer support.\n\u00b7 Booklet forces landscape + short-edge flip.\n\u00b7 \"None\" scale prints at 100%.\n\u00b7 Tick \"Print as image\" if normal printing fails."},
    "print.adv_text": {
        "zh": "高级 (PCL 优化)：用于自动检测支持 PCL 的打印机并优化打印速度，\n具体取决于打印机驱动。本软件沿用系统打印驱动。",
        "en": "Advanced (PCL optimization): auto-detects PCL-capable printers to speed up\nprinting; this depends on your printer driver. This build uses the system driver."},
    # --- 打印失败提示（针对网络复合机等驱动）
    "print.default_printer": {"zh": "默认打印机", "en": "default printer"},
    "print.printer_missing": {
        "zh": "找不到打印机“{name}”：它可能已离线、被移除，或需要重新添加。\n请在“属性”里确认后再试。",
        "en": "Printer \"{name}\" is unavailable: it may be offline, removed, or needs re-adding.\nPlease check via Properties and retry."},
    "print.failed_detail": {
        "zh": "无法向“{name}”提交打印任务。\n\n可依次尝试：\n"
              "· 在“方向”里切换横向 / 纵向（部分驱动不接受自定义纸张设置）；\n"
              "· 若为网络复合机（如 Canon iR 系列），检查设备是否开启了“部门 ID / 安全打印 / PIN”；\n"
              "· 勾选“打印到文件”先导出 PDF，确认内容无误；\n"
              "· 换用该打印机的另一套驱动（PCL6 / PS / UFR II）。",
        "en": "Could not submit the print job to \"{name}\".\n\nTry, in order:\n"
              "- switch Orientation between Landscape / Portrait (some drivers reject custom page setup);\n"
              "- on network MFPs (e.g. Canon iR series) check Department ID / secure print / PIN settings;\n"
              "- tick \"Print to file\" to export a PDF first and verify the output;\n"
              "- try another driver for that printer (PCL6 / PS / UFR II)."},
    "dlg.merge.title": {"zh": "合并 PDF", "en": "Merge PDFs"},
    "dlg.merge.add": {"zh": "添加...", "en": "Add..."},
    "dlg.merge.remove": {"zh": "移除", "en": "Remove"},
    "dlg.merge.up": {"zh": "上移", "en": "Move Up"},
    "dlg.merge.down": {"zh": "下移", "en": "Move Down"},
    "btn.merge": {"zh": "合并", "en": "Merge"},
    "btn.create": {"zh": "生成", "en": "Create"},
    "dlg.imgs2pdf.title": {"zh": "图片转 PDF", "en": "Images to PDF"},
    "dlg.imgs2pdf.add": {"zh": "添加图片...", "en": "Add images..."},
    "dlg.imgs2pdf.pagesize": {"zh": "页面大小", "en": "Page size"},
    "ps.original": {"zh": "原始图片尺寸", "en": "Original image size"},
    "dlg.imgs2pdf.fit": {"zh": "缩放方式", "en": "Scaling"},
    "fit.fit": {"zh": "适应大小", "en": "Fit to page"},
    "fit.original": {"zh": "保留原始大小", "en": "Original size"},
    "msg.need_two": {"zh": "至少需要两个 PDF 文件。", "en": "At least two PDF files are required."},
    "dlg.props.title": {"zh": "文档属性", "en": "Document Properties"},
    "dlg.props.pages": {"zh": "页数", "en": "Pages"},
    "dlg.compare.title": {"zh": "对比结果", "en": "Compare Result"},
    "dlg.compare.text_diff": {"zh": "文本差异：", "en": "Text differences:"},
    "dlg.compare.no_text": {"zh": "（无文本差异）", "en": "(no textual differences)"},
    "dlg.compare.summary": {"zh": "页数：{a} 对比 {b}；有变化页：{c}。 {note}",
                            "en": "Pages: {a} vs {b}. Changed pages: {c}. {note}"},
    "dlg.compare.changed": {"zh": "有变化", "en": "CHANGED"},
    "dlg.compare.same": {"zh": "相同", "en": "same"},

    # messages
    "msg.no_doc.title": {"zh": "未打开文档", "en": "No document"},
    "msg.no_doc.body": {"zh": "请先打开一个 PDF 文件。", "en": "Open a PDF first."},
    "msg.save_first.title": {"zh": "请先保存", "en": "Save first"},
    "msg.save_first.body": {"zh": "对比前请先保存当前文档。", "en": "Save the current document before comparing."},
    "msg.failed": {"zh": "失败", "en": "Failed"},
    "msg.done": {"zh": "完成", "en": "Done"},
    "msg.choose_source": {"zh": "请选择源 PDF 文件。", "en": "Choose a source PDF file."},
    "msg.invalid_pages": {"zh": "页面范围无效。", "en": "Invalid page range."},
    "tab.untitled": {"zh": "未命名", "en": "Untitled"},

    # rotate dialog
    "dlg.rotate.title": {"zh": "旋转页面", "en": "Rotate Pages"},
    "dlg.rotate.dir": {"zh": "方向", "en": "Direction"},
    "dir.cw": {"zh": "顺时针 90°", "en": "Clockwise 90°"},
    "dir.ccw": {"zh": "逆时针 90°", "en": "Counter-clockwise 90°"},
    "dlg.rotate.scope": {"zh": "范围", "en": "Scope"},
    "scope.current": {"zh": "当前页", "en": "Current page"},
    "scope.all": {"zh": "全部页面", "en": "All pages"},
    "scope.range": {"zh": "指定页面", "en": "Selected pages"},
    "dlg.rotate.pages": {"zh": "页面（如 1-3,5）", "en": "Pages (e.g. 1-3,5)"},

    # delete pages dialog
    "dlg.delete.title": {"zh": "删除页面", "en": "Delete Pages"},
    "dlg.delete.scope": {"zh": "范围", "en": "Scope"},
    "dlg.delete.range": {"zh": "指定页面（可多页）", "en": "Selected pages (multiple)"},
    "dlg.delete.pages": {"zh": "页面（如 1-3,5,8-10）", "en": "Pages (e.g. 1-3,5,8-10)"},
    "dlg.delete.ok": {"zh": "删除", "en": "Delete"},
    "dlg.delete.total": {"zh": "文档共 {n} 页。", "en": "The document has {n} pages."},
    "dlg.delete.summary": {"zh": "将删除 {n} 页：{pages}", "en": "Will delete {n} page(s): {pages}"},
    "dlg.delete.summary_one": {"zh": "将删除第 {n} 页", "en": "Will delete page {n}"},
    "dlg.delete.summary_none": {"zh": "请输入要删除的页面范围。", "en": "Enter the page range to delete."},
    "dlg.delete.keep_one": {
        "zh": "不能删除全部页面，至少要保留 1 页。",
        "en": "Cannot delete every page; at least one page must remain."},
    "dlg.delete.ignored": {
        "zh": "（已自动忽略无效或超出范围的页码）",
        "en": "(invalid or out-of-range pages were ignored)"},
    "dlg.delete.undo_hint": {
        "zh": "删除后可用「编辑 → 撤销」恢复。",
        "en": "You can restore it later with Edit → Undo."},

    # insert pages dialog
    "dlg.insert.title": {"zh": "插入页面", "en": "Insert Pages"},
    "dlg.insert.source": {"zh": "源 PDF", "en": "Source PDF"},
    "dlg.insert.browse": {"zh": "浏览...", "en": "Browse..."},
    "dlg.insert.pages": {"zh": "页面", "en": "Pages"},
    "dlg.insert.all": {"zh": "全部页面", "en": "All pages"},
    "dlg.insert.range": {"zh": "指定范围", "en": "Range"},
    "dlg.insert.after": {"zh": "插入位置", "en": "Insert position"},
    "dlg.insert.after_hint": {"zh": "在第 N 页之后（0 = 最前面）",
                              "en": "After page N (0 = at the beginning)"},
}


def load_language() -> str:
    global _LANG
    code = _SETTINGS.value("language", DEFAULT_LANG)
    _LANG = code if code in ("zh", "en") else DEFAULT_LANG
    return _LANG


def set_language(code: str) -> None:
    global _LANG
    if code in ("zh", "en"):
        _LANG = code
        _SETTINGS.setValue("language", code)


def language() -> str:
    return _LANG


def tr(key: str, **fmt) -> str:
    entry = STRINGS.get(key)
    if not entry:
        return key
    text = entry.get(_LANG) or entry.get(DEFAULT_LANG) or key
    if fmt:
        try:
            return text.format(**fmt)
        except Exception:  # noqa: BLE001
            return text
    return text
