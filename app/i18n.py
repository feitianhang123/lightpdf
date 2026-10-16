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
        "zh": "轻PDF编辑器\n\n软件为通过类似软件的功能通过 AI 编译，如涉及到侵权请联系作者。\nQQ：10780329\n请作者喝咖啡：",
        "en": "Light PDF Editor\n\nThis software was built with AI by replicating the features of similar "
              "software. If it infringes any rights, please contact the author.\n"
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
    "dlg.markup.title": {"zh": "标记样式", "en": "Markup Style"},
    "dlg.markup.color": {"zh": "颜色", "en": "Color"},
    "dlg.markup.opacity": {"zh": "不透明度 (%)", "en": "Opacity (%)"},
    "zoom.label": {"zh": "{p}%", "en": "{p}%"},

    # pages menu
    "pages.insert": {"zh": "从 PDF 插入页面...", "en": "Insert Pages from PDF..."},
    "pages.delete": {"zh": "删除当前页", "en": "Delete Current Page"},
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
