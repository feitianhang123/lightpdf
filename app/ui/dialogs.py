"""Application dialogs (localized)."""
from __future__ import annotations

import fitz
from PySide6.QtCore import QEvent, QRectF, Qt
from PySide6.QtGui import (QColor, QImage, QPageLayout, QPageSize, QPainter,
                          QPixmap, QTransform)
from PySide6.QtPrintSupport import QPrinter, QPrinterInfo
from PySide6.QtWidgets import (QAbstractItemView, QButtonGroup, QCheckBox,
                               QColorDialog, QComboBox,
                               QDialog, QDialogButtonBox, QDoubleSpinBox,
                               QFileDialog, QFormLayout, QFrame, QGridLayout,
                               QGroupBox, QHBoxLayout,
                               QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QMessageBox, QPlainTextEdit, QPushButton,
                               QRadioButton, QScrollArea, QSlider, QSpinBox,
                               QSplitter, QStackedWidget, QTextEdit,
                               QVBoxLayout, QWidget)

from ..i18n import tr
from ..core.compare import CompareResult


class WatermarkDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dlg.watermark.title"))
        self.text = QLineEdit("CONFIDENTIAL")
        self.size = QDoubleSpinBox(); self.size.setRange(6, 300); self.size.setValue(48)
        self.opacity = QDoubleSpinBox(); self.opacity.setRange(0.05, 1.0)
        self.opacity.setSingleStep(0.05); self.opacity.setValue(0.3)
        self.angle = QDoubleSpinBox(); self.angle.setRange(-90, 90); self.angle.setValue(45)
        self.color = (0.6, 0.6, 0.6)
        btn = QPushButton(tr("btn.color"))
        btn.clicked.connect(self._pick_color)
        form = QFormLayout(self)
        form.addRow(tr("dlg.watermark.text"), self.text)
        form.addRow(tr("dlg.watermark.size"), self.size)
        form.addRow(tr("dlg.watermark.opacity"), self.opacity)
        form.addRow(tr("dlg.watermark.angle"), self.angle)
        form.addRow(btn)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        form.addRow(bb)

    def _pick_color(self) -> None:
        c = QColorDialog.getColor()
        if c.isValid():
            self.color = (c.redF(), c.greenF(), c.blueF())


class HeaderFooterDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dlg.hf.title"))
        self.header = QLineEdit()
        self.footer = QLineEdit()
        self.size = QSpinBox(); self.size.setRange(6, 48); self.size.setValue(10)
        form = QFormLayout(self)
        form.addRow(tr("dlg.hf.header"), self.header)
        form.addRow(tr("dlg.hf.footer"), self.footer)
        form.addRow(tr("dlg.hf.size"), self.size)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        form.addRow(bb)


class PageNumbersDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dlg.pn.title"))
        self.template = QLineEdit("{n}")
        self.prefix = QLineEdit()
        self.start = QSpinBox(); self.start.setRange(1, 100000); self.start.setValue(1)
        self.position = QComboBox()
        self.position.addItem(tr("pos.bottom"), "bottom")
        self.position.addItem(tr("pos.top"), "top")
        form = QFormLayout(self)
        form.addRow(tr("dlg.pn.template"), self.template)
        form.addRow(tr("dlg.pn.prefix"), self.prefix)
        form.addRow(tr("dlg.pn.start"), self.start)
        form.addRow(tr("dlg.pn.position"), self.position)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        form.addRow(bb)

    def position_value(self) -> str:
        return self.position.currentData()


class SplitDialog(QDialog):
    def __init__(self, page_count: int, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dlg.split.title"))
        self.mode = QComboBox()
        self.mode.addItem(tr("split.equal"), "equal")
        self.mode.addItem(tr("split.ranges"), "ranges")
        self.mode.currentIndexChanged.connect(self._sync)

        self.every_n = QSpinBox(); self.every_n.setRange(1, max(1, page_count))
        self.every_n.setValue(1)
        self.ranges = QLineEdit()
        self.ranges.setPlaceholderText(tr("dlg.split.ranges"))
        self.ranges.setEnabled(False)

        form = QFormLayout(self)
        form.addRow(tr("dlg.split.mode"), self.mode)
        form.addRow(tr("dlg.split.every", n=page_count), self.every_n)
        form.addRow(tr("dlg.split.ranges"), self.ranges)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        form.addRow(bb)

    def _sync(self) -> None:
        custom = self.mode.currentData() == "ranges"
        self.ranges.setEnabled(custom)
        self.every_n.setEnabled(not custom)

    def use_ranges(self) -> bool:
        return self.mode.currentData() == "ranges"

    def every_n_value(self) -> int:
        return self.every_n.value()

    def ranges_text(self) -> str:
        return self.ranges.text()


class MarkupStyleDialog(QDialog):
    """Pick a markup color and its opacity."""

    def __init__(self, color, opacity: float, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dlg.markup.title"))
        self.color = tuple(color)
        self.swatch = QPushButton()
        self.swatch.setFixedHeight(24)
        self.swatch.clicked.connect(self._pick)
        self._update_swatch()

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(5, 100)
        self.slider.setValue(int(round(opacity * 100)))
        self.value_label = QLabel(f"{self.slider.value()}%")
        self.slider.valueChanged.connect(lambda v: self.value_label.setText(f"{v}%"))
        op_row = QWidget()
        ol = QHBoxLayout(op_row); ol.setContentsMargins(0, 0, 0, 0)
        ol.addWidget(self.slider); ol.addWidget(self.value_label)

        form = QFormLayout(self)
        form.addRow(tr("dlg.markup.color"), self.swatch)
        form.addRow(tr("dlg.markup.opacity"), op_row)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        form.addRow(bb)

    def _update_swatch(self) -> None:
        from PySide6.QtGui import QColor
        r, g, b = [int(c * 255) if max(self.color) <= 1 else int(c) for c in self.color]
        c = QColor(r, g, b)
        self.swatch.setStyleSheet(
            f"background:{c.name()}; border:1px solid #66BB6A; border-radius:4px;")
        self.swatch.setText("")

    def _pick(self) -> None:
        c = QColorDialog.getColor()
        if c.isValid():
            self.color = (c.redF(), c.greenF(), c.blueF())
            self._update_swatch()

    def values(self):
        return self.color, self.slider.value() / 100.0


class RotateDialog(QDialog):
    """Ask whether to rotate the current page, all pages, or selected pages."""

    def __init__(self, page_count: int, current_page: int, default_ccw: bool = False,
                 parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dlg.rotate.title"))
        self.direction = QComboBox()
        self.direction.addItem(tr("dir.cw"), "cw")
        self.direction.addItem(tr("dir.ccw"), "ccw")
        self.direction.setCurrentIndex(1 if default_ccw else 0)

        self.scope = QComboBox()
        self.scope.addItem(tr("scope.current"), "current")
        self.scope.addItem(tr("scope.all"), "all")
        self.scope.addItem(tr("scope.range"), "range")
        self.scope.currentIndexChanged.connect(self._sync)

        self.pages = QLineEdit()
        self.pages.setPlaceholderText(tr("dlg.rotate.pages"))
        self.pages.setEnabled(False)

        form = QFormLayout(self)
        form.addRow(tr("dlg.rotate.dir"), self.direction)
        form.addRow(tr("dlg.rotate.scope"), self.scope)
        form.addRow(tr("dlg.rotate.pages"), self.pages)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        form.addRow(bb)

    def _sync(self) -> None:
        self.pages.setEnabled(self.scope.currentData() == "range")

    def degrees(self) -> int:
        return -90 if self.direction.currentData() == "ccw" else 90

    def scope_value(self) -> str:
        return self.scope.currentData()

    def pages_text(self) -> str:
        return self.pages.text()


class InsertPagesDialog(QDialog):
    def __init__(self, current_page: int, page_count: int, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dlg.insert.title"))
        self.source = QLineEdit()
        browse = QPushButton(tr("dlg.insert.browse"))
        browse.clicked.connect(self._browse)
        src_row = QWidget()
        src_lay = QHBoxLayout(src_row); src_lay.setContentsMargins(0, 0, 0, 0)
        src_lay.addWidget(self.source); src_lay.addWidget(browse)

        self.mode = QComboBox()
        self.mode.addItem(tr("dlg.insert.all"), "all")
        self.mode.addItem(tr("dlg.insert.range"), "range")
        self.mode.currentIndexChanged.connect(self._sync)
        self.pages = QLineEdit()
        self.pages.setPlaceholderText(tr("dlg.rotate.pages"))
        self.pages.setEnabled(False)
        pages_row = QWidget()
        pr = QHBoxLayout(pages_row); pr.setContentsMargins(0, 0, 0, 0)
        pr.addWidget(self.mode); pr.addWidget(self.pages)

        self.after = QSpinBox()
        self.after.setRange(0, page_count)
        self.after.setValue(current_page + 1)
        self.after.setSuffix("")
        self.after_hint = QLabel(tr("dlg.insert.after_hint"))

        form = QFormLayout(self)
        form.addRow(tr("dlg.insert.source"), src_row)
        form.addRow(tr("dlg.insert.pages"), pages_row)
        form.addRow(tr("dlg.insert.after"), self.after)
        form.addRow("", self.after_hint)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        form.addRow(bb)

    def _browse(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, tr("dlg.insert.source"), "", "PDF (*.pdf)")
        if path:
            self.source.setText(path)

    def _sync(self) -> None:
        self.pages.setEnabled(self.mode.currentData() == "range")

    def source_path(self) -> str:
        return self.source.text().strip()

    def use_all(self) -> bool:
        return self.mode.currentData() == "all"

    def pages_text(self) -> str:
        return self.pages.text()

    def after_page(self) -> int:
        return self.after.value()


FONT_CHOICES = [("Times", "tiro"), ("Courier", "cour"), ("中文", "china-s")]


class TextEditDialog(QDialog):
    """Text + font + size, used for text boxes and touchup text editing."""

    def __init__(self, title: str, original: str, fontname=None, fontsize: float = 12,
                 allow_original: bool = False, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.edit = QPlainTextEdit(original)
        self.edit.setMinimumWidth(400)

        self.font_combo = QComboBox()
        self.font_combo.setMaxVisibleItems(30)
        if allow_original:
            self.font_combo.addItem(tr("dlg.edit.original"), None)
        self.font_combo.addItem(tr("dlg.edit.font_default"), "helv")
        self.font_combo.addItem("Times", "tiro")
        self.font_combo.addItem("Courier", "cour")
        self.font_combo.addItem("中文（内置）", "china-s")
        try:
            from ..core import fonts
            for label, path in fonts.system_fonts():
                self.font_combo.addItem(label, path)
        except Exception:  # noqa: BLE001
            pass
        idx = self.font_combo.findData(fontname)
        if idx >= 0:
            self.font_combo.setCurrentIndex(idx)

        self.size_spin = QSpinBox()
        self.size_spin.setRange(6, 200)
        self.size_spin.setValue(int(fontsize) if fontsize else 12)

        form = QFormLayout()
        form.addRow(tr("dlg.edit.font"), self.font_combo)
        form.addRow(tr("dlg.edit.size"), self.size_spin)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(tr("dlg.edit.label")))
        layout.addWidget(self.edit)
        layout.addLayout(form)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        layout.addWidget(bb)

    def text(self) -> str:
        return self.edit.toPlainText()

    def font_name(self):
        return self.font_combo.currentData()

    def font_size(self) -> float:
        return float(self.size_spin.value())


class PropertiesDialog(QDialog):
    FIELDS = ["title", "author", "subject", "keywords", "creator", "producer"]

    def __init__(self, meta: dict, page_count: int, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dlg.props.title"))
        self.edits = {}
        form = QFormLayout()
        for key in self.FIELDS:
            e = QLineEdit(str(meta.get(key, "") or ""))
            self.edits[key] = e
            form.addRow(key.title(), e)
        form.addRow(tr("dlg.props.pages"), QLabel(str(page_count)))
        layout = QVBoxLayout(self)
        layout.addLayout(form)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept); bb.rejected.connect(self.reject)
        layout.addWidget(bb)

    def values(self) -> dict:
        return {k: e.text() for k, e in self.edits.items()}


class CompareWindow(QDialog):
    def __init__(self, result: CompareResult, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dlg.compare.title"))
        self.resize(1100, 700)
        self.result = result

        self.page_list = QListWidget()
        self.text_changes = QTextEdit(); self.text_changes.setReadOnly(True)
        self.overlay = QLabel(); self.overlay.setAlignment(Qt.AlignCenter)
        self.overlay.setMinimumSize(400, 400)
        self.summary = QLabel()

        left = QWidget(); ll = QVBoxLayout(left)
        ll.addWidget(self.summary); ll.addWidget(self.page_list)
        right = QWidget(); rl = QVBoxLayout(right)
        rl.addWidget(self.overlay, 3)
        rl.addWidget(QLabel(tr("dlg.compare.text_diff")))
        rl.addWidget(self.text_changes, 2)

        split = QSplitter(); split.addWidget(left); split.addWidget(right)
        split.setStretchFactor(1, 2)
        layout = QVBoxLayout(self); layout.addWidget(split)

        changed = result.changed_pages
        self.summary.setText(tr("dlg.compare.summary", a=result.a_pages, b=result.b_pages,
                                c=len(changed), note=result.note))
        for pd in result.pages:
            tag = tr("dlg.compare.changed") if pd.changed_ratio > 0.0005 else tr("dlg.compare.same")
            it = QListWidgetItem(f"{pd.page + 1}  [{tag}]  {pd.changed_ratio * 100:.2f}%")
            it.setData(Qt.UserRole, pd)
            self.page_list.addItem(it)
        if self.page_list.count():
            self.page_list.setCurrentRow(0)
        self.page_list.currentItemChanged.connect(self._show_page)

    def _show_page(self, cur, _prev) -> None:
        if cur is None:
            return
        pd = cur.data(Qt.UserRole)
        pix = QPixmap()
        pix.loadFromData(pd.overlay_png or b"", "PNG")
        if not pix.isNull():
            self.overlay.setPixmap(pix.scaled(self.overlay.size(), Qt.KeepAspectRatio,
                                              Qt.SmoothTransformation))
        lines = [f"{kind} {text}" for kind, text in pd.text_changes[:400]]
        self.text_changes.setPlainText("\n".join(lines) or tr("dlg.compare.no_text"))


class PrintDialog(QDialog):
    """Foxit PDF Editor 11 打印对话框的 1:1 复刻。

    控件、文案、分组与相对布局均取自原版程序资源（DIALOG 7792 "Print" 为主，
    辅以 7785 "Advanced" / 7789 "Scale 选项" / 7794 "Batch Print" / 7795 "Page Range
    Options"），原版对话框单位 531 x 308。行为接线到 PyMuPDF + QPrinter 渲染管线：
    打印范围 / 子集 / 逆序、缩放、多页合一、小册子、平铺、双面、旋转居中、
    灰度、作为图像、出血标记等均可用。
    """

    PREVIEW_BG = "#8FB69A"       # 预览底色（浅绿，沿用原工程风格）

    def __init__(self, doc, current_page: int, parent=None) -> None:
        super().__init__(parent)
        self.doc = doc
        self.cur = current_page
        self.n = doc.page_count
        self._markup_doc = None
        self._preview_index = 0
        self._preview_base = None      # 全尺寸预览底图（与控件尺寸无关）
        self._booklet_saved = None
        self.setWindowTitle(tr("print.title"))
        self.resize(1000, 640)

        self._build()
        self._wire()
        self._sync_handling()
        self._sync_duplex()
        self._sync_range()
        self._sync_what()
        self._update_preview()

    # ================================================================ 构建界面
    def _build(self) -> None:
        top = QVBoxLayout()

        # ---- 第 1 行：&Name: [打印机] [&Properties]        [Print to file]
        r1 = QHBoxLayout()
        r1.addWidget(QLabel(tr("print.name")))
        self.printer_combo = QComboBox()
        printers = QPrinterInfo.availablePrinterNames()
        if printers:
            self.printer_combo.addItems(printers)
            dflt = QPrinterInfo.defaultPrinterName()
            if dflt in printers:
                self.printer_combo.setCurrentText(dflt)
        r1.addWidget(self.printer_combo, 1)
        self.props_btn = QPushButton(tr("print.properties"))
        r1.addWidget(self.props_btn)
        r1.addSpacing(12)
        self.tofile_check = QCheckBox(tr("print.tofile"))
        r1.addWidget(self.tofile_check)
        top.addLayout(r1)

        # ---- 第 2 行：&Copies: [n] [C&ollate] [灰度] [图像] [Bleed Marks]
        r2 = QHBoxLayout()
        r2.addWidget(QLabel(tr("print.copies")))
        self.copies_spin = QSpinBox()
        self.copies_spin.setRange(1, 999)
        self.copies_spin.setFixedWidth(64)
        r2.addWidget(self.copies_spin)
        self.collate_check = QCheckBox(tr("print.collate"))
        r2.addWidget(self.collate_check)
        r2.addSpacing(10)
        self.gray_check = QCheckBox(tr("print.print_as_grayscale"))
        self.asimage_check = QCheckBox(tr("print.print_as_image"))
        self.bleed_check = QCheckBox(tr("print.bleed_marks"))
        for w in (self.gray_check, self.asimage_check, self.bleed_check):
            r2.addWidget(w)
        r2.addStretch()
        top.addLayout(r2)

        # ---- 打印到文件（沿用原工程：勾选后出现路径）
        self.file_edit = QLineEdit()
        self.file_edit.setEnabled(False)
        self.file_btn = QPushButton("...")
        self.file_btn.setFixedWidth(32)
        self.file_btn.setEnabled(False)
        rf = QHBoxLayout()
        rf.addSpacing(60)
        rf.addWidget(self.file_edit, 1)
        rf.addWidget(self.file_btn)
        top.addLayout(rf)
        self._top_layout = top

        # ---- 主体三栏
        body = QHBoxLayout()
        body.addWidget(self._build_preview(), 3)
        body.addWidget(self._build_middle(), 4)
        body.addWidget(self._build_right(), 3)

        # ---- 底部：Advanced / Printing Tips / OK / Cancel
        foot = QHBoxLayout()
        self.adv_btn = QPushButton(tr("print.advanced"))
        self.tips_btn = QPushButton(tr("print.tips"))
        foot.addWidget(self.adv_btn)
        foot.addWidget(self.tips_btn)
        foot.addStretch()
        self.ok_btn = QPushButton(tr("print.ok"))
        self.cancel_btn = QPushButton(tr("btn.cancel"))
        self.ok_btn.setDefault(True)
        foot.addWidget(self.ok_btn)
        foot.addWidget(self.cancel_btn)

        root = QVBoxLayout(self)
        root.addLayout(top)
        root.addLayout(body, 1)
        root.addLayout(foot)

    # ---------------------------------------------------------------- 左：预览
    def _build_preview(self) -> QWidget:
        box = QGroupBox(tr("print.preview"))
        box.setMinimumWidth(248)
        box.setMaximumWidth(340)
        v = QVBoxLayout(box)

        info = QGridLayout()
        info.setHorizontalSpacing(6)
        info.setVerticalSpacing(2)
        self.zoom_edit = QLineEdit("100")
        self.zoom_edit.setFixedWidth(70)
        self.doc_size_label = QLabel("0.0 x 0.0 in")
        self.paper_size_label = QLabel("0.0 x 0.0 in")
        info.addWidget(QLabel(tr("print.zoom")), 0, 0)
        info.addWidget(self.zoom_edit, 0, 1)
        info.addWidget(QLabel(tr("print.document")), 1, 0)
        info.addWidget(self.doc_size_label, 1, 1)
        info.addWidget(QLabel(tr("print.paper_label")), 2, 0)
        info.addWidget(self.paper_size_label, 2, 1)
        v.addLayout(info)

        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(200, 180)
        self.preview_label.setScaledContents(False)
        self.preview_label.setStyleSheet(
            "background:%s;border:1px solid #4E7D57;" % self.PREVIEW_BG)
        # 控件尺寸变化时只重新缩放底图，不需要重渲染整页
        self.preview_label.installEventFilter(self)
        v.addWidget(self.preview_label, 1)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        v.addWidget(sep)

        nav1 = QHBoxLayout()
        self.prev_btn = QPushButton("<")
        self.next_btn = QPushButton(">")
        self.prev_btn.setFixedWidth(28)
        self.next_btn.setFixedWidth(28)
        self.page_indicator = QLabel("0 / 0")
        self.page_indicator.setAlignment(Qt.AlignCenter)
        nav1.addWidget(self.prev_btn)
        nav1.addWidget(self.page_indicator, 1)
        nav1.addWidget(self.next_btn)
        v.addLayout(nav1)

        nav2 = QHBoxLayout()
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(1, 1)
        nav2.addWidget(self.slider, 1)
        v.addLayout(nav2)

        self.page_edit = QLineEdit()
        self.page_edit.setPlaceholderText("1 - %d" % self.n)
        v.addWidget(self.page_edit)
        return box

    # ---------------------------------------------------------------- 中：范围/处理
    def _build_middle(self) -> QWidget:
        w = QWidget()
        w.setMinimumWidth(360)
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)

        # ---- Print Range
        rng = QGroupBox(tr("print.range"))
        rv = QVBoxLayout(rng)
        self.rb_view = QRadioButton(tr("print.range.view"))
        self.rb_current = QRadioButton(tr("print.range.current"))
        self.rb_all = QRadioButton(tr("print.range.all_pages"))
        self.rb_all.setChecked(True)
        self.range_group = QButtonGroup(self)
        for b in (self.rb_view, self.rb_current, self.rb_all):
            self.range_group.addButton(b)
            rv.addWidget(b)
        prow = QHBoxLayout()
        self.rb_pages = QRadioButton(tr("print.range.pages_label"))
        self.range_group.addButton(self.rb_pages)
        self.pages_edit = QLineEdit()
        self.pages_total = QLabel("/ %d" % self.n)
        prow.addWidget(self.rb_pages)
        prow.addWidget(self.pages_edit, 1)
        prow.addWidget(self.pages_total)
        rv.addLayout(prow)
        self.pages_sample = QLabel(tr("print.range.sample"))
        self.pages_sample.setStyleSheet("color:#888;")
        rv.addWidget(self.pages_sample)
        srow = QHBoxLayout()
        srow.addWidget(QLabel(tr("print.subset")))
        self.subset_combo = QComboBox()
        self.subset_combo.addItem(tr("print.subset.all"), "all")
        self.subset_combo.addItem(tr("print.subset.odd"), "odd")
        self.subset_combo.addItem(tr("print.subset.even"), "even")
        srow.addWidget(self.subset_combo, 1)
        rv.addLayout(srow)
        self.reverse_check = QCheckBox(tr("print.reverse"))
        rv.addWidget(self.reverse_check)
        v.addWidget(rng)

        # ---- Print Handling（4 个模式 + 各自的选项页）
        hnd = QGroupBox(tr("print.content"))
        hv = QVBoxLayout(hnd)
        hgrid = QGridLayout()
        hgrid.setHorizontalSpacing(12)
        hgrid.setVerticalSpacing(2)
        self.h_scale = QRadioButton(tr("print.handling.scale"))
        self.h_tile = QRadioButton(tr("print.handling.tile"))
        self.h_nup = QRadioButton(tr("print.handling.nup"))
        self.h_booklet = QRadioButton(tr("print.handling.booklet"))
        self.h_scale.setChecked(True)
        self.handling_group = QButtonGroup(self)
        for _i, _b in enumerate((self.h_scale, self.h_tile, self.h_nup, self.h_booklet)):
            self.handling_group.addButton(_b)
            hgrid.addWidget(_b, _i // 2, _i % 2)
        hv.addLayout(hgrid)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._page_scale())
        self.stack.addWidget(self._page_tile())
        self.stack.addWidget(self._page_nup())
        self.stack.addWidget(self._page_booklet())
        hv.addWidget(self.stack, 1)
        v.addWidget(hnd, 1)
        return w

    def _page_scale(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(2, 2, 2, 2)
        self.s_none = QRadioButton(tr("print.scale.opt.none"))
        self.s_fit = QRadioButton(tr("print.scale.opt.fit"))
        self.s_fit.setChecked(True)
        self.s_reduce = QRadioButton(tr("print.scale.opt.reduce"))
        self.scale_group = QButtonGroup(self)
        for b in (self.s_none, self.s_fit, self.s_reduce):
            self.scale_group.addButton(b)
            v.addWidget(b)
        crow = QHBoxLayout()
        self.s_custom = QRadioButton(tr("print.scale.opt.custom"))
        self.scale_group.addButton(self.s_custom)
        self.custom_edit = QLineEdit("100")
        self.custom_edit.setFixedWidth(64)
        crow.addWidget(self.s_custom)
        crow.addWidget(self.custom_edit)
        crow.addWidget(QLabel("%"))
        crow.addStretch()
        v.addLayout(crow)
        self.choose_paper = QCheckBox(tr("print.scale.choose_paper"))
        self.choose_paper.setMinimumWidth(1)
        v.addWidget(self.choose_paper)
        v.addStretch()
        return w

    def _page_tile(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(2, 2, 2, 2)
        z = QHBoxLayout()
        z.addWidget(QLabel(tr("print.tile.zoom")))
        self.tile_zoom = QLineEdit("100")
        self.tile_zoom.setFixedWidth(64)
        z.addWidget(self.tile_zoom)
        z.addWidget(QLabel("%"))
        z.addStretch()
        v.addLayout(z)
        o = QHBoxLayout()
        o.addWidget(QLabel(tr("print.tile.overlap")))
        self.tile_overlap = QLineEdit("0")
        self.tile_overlap.setFixedWidth(64)
        o.addWidget(self.tile_overlap)
        o.addStretch()
        v.addLayout(o)
        self.tile_cutmarks = QCheckBox(tr("print.tile.cutmarks"))
        self.tile_labels = QCheckBox(tr("print.tile.labels"))
        v.addWidget(self.tile_cutmarks)
        v.addWidget(self.tile_labels)
        v.addStretch()
        return w

    def _page_nup(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(2, 2, 2, 2)
        g = QHBoxLayout()
        g.addWidget(QLabel(tr("print.nup.per_sheet")))
        self.nup_combo = QComboBox()
        for k in (1, 2, 4, 6, 9, 16):
            self.nup_combo.addItem(str(k), k)
        self.nup_combo.setCurrentIndex(1)
        g.addWidget(self.nup_combo, 1)
        v.addLayout(g)
        o = QHBoxLayout()
        o.addWidget(QLabel(tr("print.nup.order")))
        self.nup_order = QComboBox()
        self.nup_order.addItem(tr("print.nup.order.h"), "h")
        self.nup_order.addItem(tr("print.nup.order.hr"), "hr")
        self.nup_order.addItem(tr("print.nup.order.v"), "v")
        self.nup_order.addItem(tr("print.nup.order.vr"), "vr")
        o.addWidget(self.nup_order, 1)
        v.addLayout(o)
        self.nup_border = QCheckBox(tr("print.nup.border"))
        v.addWidget(self.nup_border)
        v.addStretch()
        return w

    def _page_booklet(self) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(2, 2, 2, 2)
        b = QHBoxLayout()
        b.addWidget(QLabel(tr("print.booklet.binding")))
        self.booklet_binding = QComboBox()
        self.booklet_binding.addItem(tr("print.booklet.left"), "left")
        self.booklet_binding.addItem(tr("print.booklet.right"), "right")
        b.addWidget(self.booklet_binding, 1)
        v.addLayout(b)
        s = QHBoxLayout()
        s.addWidget(QLabel(tr("print.booklet.subset")))
        self.booklet_subset = QComboBox()
        self.booklet_subset.addItem(tr("print.booklet.both"), "both")
        self.booklet_subset.addItem(tr("print.booklet.front"), "front")
        self.booklet_subset.addItem(tr("print.booklet.back"), "back")
        s.addWidget(self.booklet_subset, 1)
        v.addLayout(s)
        self.booklet_autorotate = QCheckBox(tr("print.booklet.autorotate"))
        self.booklet_autorotate.setChecked(True)
        v.addWidget(self.booklet_autorotate)
        v.addStretch()
        return w

    # ---------------------------------------------------------------- 右：双面/其它
    def _build_right(self) -> QWidget:
        w = QWidget()
        w.setMinimumWidth(250)
        w.setMaximumWidth(340)
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 0, 0, 0)

        dup = QGroupBox()
        dv = QVBoxLayout(dup)
        self.duplex_check = QCheckBox(tr("print.duplex.both"))
        self.duplex_check.setMinimumWidth(1)
        dv.addWidget(self.duplex_check)
        self.flip_long = QRadioButton(tr("print.duplex.long"))
        self.flip_short = QRadioButton(tr("print.duplex.short"))
        self.flip_long.setChecked(True)
        self.flip_group = QButtonGroup(self)
        for b in (self.flip_long, self.flip_short):
            self.flip_group.addButton(b)
            dv.addWidget(b)
        self.autorotate_check = QCheckBox(tr("print.autorotate"))
        self.autorotate_check.setChecked(True)
        self.autocenter_check = QCheckBox(tr("print.autocenter"))
        self.autocenter_check.setChecked(True)
        dv.addWidget(self.autorotate_check)
        dv.addWidget(self.autocenter_check)
        v.addWidget(dup)

        ori = QGroupBox(tr("print.orientation"))
        ov = QVBoxLayout(ori)
        self.orient_combo = QComboBox()
        self.orient_combo.addItem(tr("print.orientation.auto"), "auto")
        self.orient_combo.addItem(tr("print.orientation.portrait"), "portrait")
        self.orient_combo.addItem(tr("print.orientation.landscape"), "landscape")
        ov.addWidget(self.orient_combo)
        v.addWidget(ori)

        what = QGroupBox(tr("print.what"))
        wv = QVBoxLayout(what)
        self.what_combo = QComboBox()
        self.what_combo.addItem(tr("print.what.doc"), "doc")
        self.what_combo.addItem(tr("print.what.markup"), "markup")
        self.what_combo.addItem(tr("print.what.stamps"), "stamps")
        self.what_combo.addItem(tr("print.what.formfields"), "formfields")
        wv.addWidget(self.what_combo)
        self.summarize_check = QCheckBox(tr("print.output.summarize"))
        wv.addWidget(self.summarize_check)
        v.addWidget(what)

        out = QGroupBox(tr("print.output"))
        ov2 = QVBoxLayout(out)
        self.overprint_check = QCheckBox(tr("print.output.overprint"))
        ov2.addWidget(self.overprint_check)
        v.addWidget(out)
        v.addStretch()
        return w

    # ================================================================ 信号
    def _wire(self) -> None:
        self.props_btn.clicked.connect(self._open_properties)
        self.adv_btn.clicked.connect(self._open_advanced)
        self.tips_btn.clicked.connect(self._open_tips)
        self.ok_btn.clicked.connect(self._do_print)
        self.cancel_btn.clicked.connect(self.reject)

        self.tofile_check.toggled.connect(self._sync_file)
        self.file_btn.clicked.connect(self._pick_file)

        self.prev_btn.clicked.connect(lambda: self._preview_step(-1))
        self.next_btn.clicked.connect(lambda: self._preview_step(1))
        self.slider.valueChanged.connect(self._on_slider)
        self.page_edit.returnPressed.connect(self._goto_page)

        self.handling_group.buttonClicked.connect(self._sync_handling)
        for b in (self.s_none, self.s_fit, self.s_reduce, self.s_custom):
            b.toggled.connect(self._sync_scale)
        for b in (self.rb_view, self.rb_current, self.rb_all, self.rb_pages):
            b.toggled.connect(self._sync_range)
        for w in (self.subset_combo, self.nup_combo, self.nup_order):
            w.currentIndexChanged.connect(self._update_preview)
        for w in (self.orient_combo, self.what_combo):
            w.currentIndexChanged.connect(self._update_preview)
        self.pages_edit.textChanged.connect(self._update_preview)
        self.copies_spin.valueChanged.connect(self._sync_collate)
        self.custom_edit.textChanged.connect(self._update_preview)
        self._sync_scale()

    def _sync_file(self, on: bool) -> None:
        self.file_edit.setEnabled(on)
        self.file_btn.setEnabled(on)
        if on and not self.file_edit.text():
            self.file_edit.setText(self._default_out())

    def _default_out(self) -> str:
        import os
        base = "output.pdf"
        if getattr(self.doc, "path", None):
            base = os.path.splitext(os.path.basename(self.doc.path))[0] + ".pdf"
        return base

    def _pick_file(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, tr("print.tofile"), self.file_edit.text() or self._default_out(),
            "PDF (*.pdf)")
        if path:
            self.file_edit.setText(path)

    def _sync_handling(self) -> None:
        idx = 0
        if self.h_tile.isChecked():
            idx = 1
        elif self.h_nup.isChecked():
            idx = 2
        elif self.h_booklet.isChecked():
            idx = 3
        self.stack.setCurrentIndex(idx)
        # 小册子强制双面（短边翻转）与横向，并临时禁用冲突项
        if self.h_booklet.isChecked():
            if not self._booklet_saved:
                self._booklet_saved = (self.orient_combo.currentIndex(),
                                       self.duplex_check.isChecked(),
                                       self.flip_short.isChecked())
            self.orient_combo.setCurrentIndex(self._index_of(self.orient_combo, "landscape"))
            self.duplex_check.setChecked(True)
            self.flip_short.setChecked(True)
            self.orient_combo.setEnabled(False)
            self.duplex_check.setEnabled(False)
            self.flip_long.setEnabled(False)
            self.flip_short.setEnabled(False)
        else:
            if self._booklet_saved:
                oi, dh, fs = self._booklet_saved
                self.orient_combo.setCurrentIndex(oi)
                self.duplex_check.setChecked(dh)
                self.flip_short.setChecked(fs)
                self._booklet_saved = None
            self.orient_combo.setEnabled(True)
            self.duplex_check.setEnabled(True)
            self._sync_duplex()
        self._preview_index = 0
        self._update_preview()

    def _sync_duplex(self) -> None:
        on = self.duplex_check.isChecked()
        self.flip_long.setEnabled(on)
        self.flip_short.setEnabled(on)

    def _sync_scale(self) -> None:
        self.custom_edit.setEnabled(self.s_custom.isChecked())
        self._update_preview()

    def _sync_what(self) -> None:
        # 仅“文档和标记 / 文档和图章”带批注；表单域暂按文档处理
        self._update_preview()

    def _sync_collate(self, value: int) -> None:
        self.collate_check.setEnabled(value > 1)

    def _sync_range(self) -> None:
        on = self.rb_pages.isChecked()
        self.pages_edit.setEnabled(on)
        self.pages_total.setEnabled(on)
        self.pages_sample.setEnabled(on)
        self._update_preview()

    @staticmethod
    def _index_of(combo, data) -> int:
        for i in range(combo.count()):
            if combo.itemData(i) == data:
                return i
        return -1

    # ================================================================ 取值
    def _pages(self) -> list:
        if self.rb_current.isChecked() or self.rb_view.isChecked():
            base = [self.cur]
        elif self.rb_pages.isChecked():
            base = self._parse_spec(self.pages_edit.text())
            if not base:
                base = list(range(self.n))
        else:
            base = list(range(self.n))
        sub = self.subset_combo.currentData()
        if sub == "odd":
            base = [p for p in base if (p + 1) % 2 == 1]
        elif sub == "even":
            base = [p for p in base if (p + 1) % 2 == 0]
        if self.reverse_check.isChecked():
            base = list(reversed(base))
        return base

    def _parse_spec(self, text: str) -> list:
        """解析 “1,5-9,12” 形式的页码范围（1 基），返回 0 基页码。"""
        import re
        out = []
        for part in re.split(r"[,，;；\s]+", (text or "").strip()):
            if not part:
                continue
            m = re.match(r"^(\d+)\s*-\s*(\d+)$", part)
            if m:
                a, b = int(m.group(1)), int(m.group(2))
                if a > b:
                    a, b = b, a
                out += list(range(a, b + 1))
            elif part.isdigit():
                out.append(int(part))
        seen, res = set(), []
        for p in out:
            if 1 <= p <= self.n and p not in seen:
                seen.add(p)
                res.append(p - 1)
        return sorted(res)

    def _landscape(self) -> bool:
        if self.h_booklet.isChecked():
            return True
        mode = self.orient_combo.currentData()
        if mode == "portrait":
            return False
        if mode == "landscape":
            return True
        # ---- 自动：多页合一时按“网格形状”判断（2 页并排 → 横向更接近一张纸放两页）
        if self.h_nup.isChecked() and self._pages_per_sheet() > 1:
            rows, cols = self._grid_for(self._pages_per_sheet())
            if cols != rows:
                return cols > rows
        pages = self._pages()
        if not pages:
            return False
        r = self.doc.page(pages[0]).rect
        return r.width > r.height

    def _pages_per_sheet(self) -> int:
        return int(self.nup_combo.currentData() or 1)

    def _grid_for(self, k: int):
        if k <= 1:
            return 1, 1
        if k == 2:
            return 1, 2
        if k == 4:
            return 2, 2
        if k == 6:
            return 2, 3
        if k == 9:
            return 3, 3
        return 4, 4

    def _annot_mode(self) -> bool:
        return self.what_combo.currentData() in ("markup", "stamps")

    # ================================================================ 预览
    def _markup_source(self):
        """去掉便签副本（便签永不打印），供“文档和标记”预览。"""
        if self._markup_doc is None:
            try:
                d = fitz.open("pdf", self.doc.tobytes())
                for pg in d:
                    for a in list(pg.annots() or []):
                        if a.type[1] == "Text":
                            pg.delete_annot(a)
                self._markup_doc = d
            except Exception:  # noqa: BLE001
                self._markup_doc = self.doc.doc
        return self._markup_doc

    def _render_qimage(self, pno: int, zoom: float, annots: bool) -> QImage:
        if annots:
            pix = self._markup_source().load_page(pno).get_pixmap(
                matrix=fitz.Matrix(zoom, zoom), alpha=False, annots=True)
        else:
            pix = self.doc.render(pno, zoom=zoom, alpha=False, annots=False)
        return QImage(pix.samples, pix.width, pix.height, pix.stride,
                      QImage.Format_RGB888).copy()

    def _maybe_autorotate(self, img: QImage) -> QImage:
        if self.autorotate_check.isChecked() and img.width() > img.height():
            return img.transformed(QTransform().rotate(90))
        return img

    def _booklet_sides(self, pages: list) -> list:
        seq = list(pages) + [None] * ((4 - len(pages) % 4) % 4)
        m = len(seq)
        sides = []
        for s in range(m // 4):
            sides.append([seq[m - 1 - 2 * s], seq[2 * s]])
            sides.append([seq[2 * s + 1], seq[m - 2 - 2 * s]])
        return sides

    def _booklet_output_sides(self, pages: list) -> list:
        sides = [list(s) for s in self._booklet_sides(pages)]
        if self.booklet_binding.currentData() == "right":
            sides = [[s[1], s[0]] for s in sides]
        sub = self.booklet_subset.currentData()
        if sub == "front":
            sides = sides[0::2]
        elif sub == "back":
            sides = sides[1::2]
        return sides

    def _output_items(self):
        """返回 (items, kind)。kind ∈ page/d_side/nup_side。"""
        pages = self._pages()
        if not pages:
            return [], "page"
        if self.h_booklet.isChecked():
            return self._booklet_output_sides(pages), "d_side"
        if self.h_nup.isChecked():
            k = self._pages_per_sheet()
            groups = [pages[i:i + k] for i in range(0, len(pages), k)]
            return groups, "nup_side"
        return [[p] for p in pages], "page"

    def _render_d_side(self, side, annots: bool) -> QImage:
        imgs, ref = [], None
        for pno in side:
            im = self._maybe_autorotate(self._render_qimage(pno, 1.2, annots)) \
                if pno is not None else None
            imgs.append(im)
            if ref is None and im is not None:
                ref = im
        if ref is None:
            return QImage(1, 1, QImage.Format_RGB888)
        cw, ch = ref.width(), ref.height()
        canvas = QImage(cw * 2, ch, QImage.Format_RGB888)
        canvas.fill(Qt.white)
        p = QPainter(canvas)
        for i, im in enumerate(imgs):
            if im is not None:
                p.drawImage(i * cw, 0, im)
        p.end()
        return canvas

    def _render_nup_side(self, group, annots: bool) -> QImage:
        rows, cols = self._grid_for(self._pages_per_sheet())
        imgs = [self._render_qimage(p, 0.8, annots) for p in group]
        if not imgs:
            return QImage(1, 1, QImage.Format_RGB888)
        aw = max(i.width() for i in imgs)
        ah = max(i.height() for i in imgs)
        canvas = QImage(cols * aw, rows * ah, QImage.Format_RGB888)
        canvas.fill(Qt.white)
        p = QPainter(canvas)
        cells = self._nup_cells(len(group), rows, cols)
        for im, (r, c) in zip(imgs, cells):
            x, y = c * aw, r * ah
            if self.nup_border.isChecked():
                p.setPen(QColor("#000000"))
                p.drawRect(x, y, aw - 1, ah - 1)
            p.drawImage(x + (aw - im.width()) // 2, y + (ah - im.height()) // 2, im)
        p.end()
        return canvas

    def _nup_cells(self, count: int, rows: int, cols: int):
        order = self.nup_order.currentData()
        cells = [(r, c) for r in range(rows) for c in range(cols)]
        if order == "v":
            cells = [(r, c) for c in range(cols) for r in range(rows)]
        elif order == "hr":
            cells = [(rows - 1 - r, cols - 1 - c) for r, c in cells]
        elif order == "vr":
            cells = [(rows - 1 - r, cols - 1 - c) for r, c in cells]
        return cells[:count]

    def _preview_step(self, delta: int) -> None:
        items, _ = self._output_items()
        if not items:
            return
        self._preview_index = max(0, min(len(items) - 1, self._preview_index + delta))
        self._update_preview()

    def _on_slider(self, value: int) -> None:
        self._preview_index = max(0, value - 1)
        self._update_preview(keep_slider=True)

    def _goto_page(self) -> None:
        try:
            v = int(self.page_edit.text().strip())
        except ValueError:
            return
        items, _ = self._output_items()
        self._preview_index = max(0, min(len(items) - 1, v - 1))
        self._update_preview()

    def _update_preview(self, keep_slider: bool = False) -> None:
        items, kind = self._output_items()
        self._sync_meta_labels()
        if not items:
            self.page_indicator.setText("0 / 0")
            self._preview_base = None
            self.preview_label.clear()
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            self.slider.setRange(1, 1)
            return
        self._preview_index = max(0, min(len(items) - 1, self._preview_index))
        self.page_indicator.setText("%d / %d" % (self._preview_index + 1, len(items)))
        self.prev_btn.setEnabled(self._preview_index > 0)
        self.next_btn.setEnabled(self._preview_index < len(items) - 1)
        if not keep_slider:
            self.slider.blockSignals(True)
            self.slider.setRange(1, len(items))
            self.slider.setValue(self._preview_index + 1)
            self.slider.blockSignals(False)
        annots = self._annot_mode()
        cur = items[self._preview_index]
        if kind == "d_side":
            content = self._render_d_side(cur, True)
        elif kind == "nup_side":
            content = self._render_nup_side(cur, annots)
        else:
            content = self._render_qimage(cur[0], 1.5, annots)
            if self._landscape():
                content = content.transformed(QTransform().rotate(90))
        self._preview_base = QPixmap.fromImage(self._paper_canvas(content))
        self._rescale_preview()

    def _sync_meta_labels(self) -> None:
        pages = self._pages()
        pno = pages[0] if pages else self.cur
        try:
            r = self.doc.page(pno).rect
            self.doc_size_label.setText("%.1f x %.1f in" % (r.width / 72.0, r.height / 72.0))
        except Exception:  # noqa: BLE001
            pass
        paper = self.paper_size_label_name()
        self.paper_size_label.setText(paper)

    def paper_size_label_name(self) -> str:
        # 与原版一致：此处显示纸张「尺寸」而非纸张名称
        return "11.7 x 8.3 in" if self._landscape() else "8.3 x 11.7 in"

    def _paper_canvas(self, content: QImage) -> QImage:
        """把 content 画在一张**真实比例**的纸上 —— 保证「预览 == 实际输出」。

        要害：纸面宽高比只由**纸张方向**决定，**绝不随内容拉伸**。内容按比例缩放并居中，
        内容比例与纸面不同时会出现白边 —— 这正是实际打印出来的样子（此前的 bug 是
        用 max(sw, 内容宽) 把纸面撑成了内容的形状，于是 2 页并排时预览变成横向）。
        """
        land = self._landscape()
        ar = (297.0 / 210.0) if land else (210.0 / 297.0)      # A4 宽/高
        cw, ch = max(1, content.width()), max(1, content.height())
        if cw / ch >= ar:          # 内容比纸“宽” → 以内容宽定纸宽
            sw = int(cw * 1.04)
            sh = int(round(sw / ar))
        else:                      # 内容比纸“高” → 以内容高定纸高
            sh = int(ch * 1.04)
            sw = int(round(sh * ar))
        sw, sh = max(sw, 40), max(sh, 40)
        gut = 16
        canvas = QImage(sw + 2 * gut, sh + 2 * gut, QImage.Format_RGB888)
        canvas.fill(QColor(self.PREVIEW_BG))
        p = QPainter(canvas)
        p.fillRect(gut, gut, sw, sh, Qt.white)
        p.setPen(QColor("#4E7D57"))
        p.drawRect(gut, gut, sw - 1, sh - 1)
        r = self._fit_rect(cw, ch, sw, sh)                     # 等比缩放居中
        p.drawImage(QRectF(gut + r.x(), gut + r.y(), r.width(), r.height()), content)
        p.end()
        return canvas

    def _rescale_preview(self) -> None:
        """把全尺寸底图缩放到预览框当前大小（与渲染解耦，避免首屏尺寸不对）。"""
        if self._preview_base is None or self._preview_base.isNull():
            self.preview_label.clear()
            return
        area = self.preview_label.size()
        self.preview_label.setPixmap(self._preview_base.scaled(
            max(40, area.width() - 4), max(40, area.height() - 4),
            Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def eventFilter(self, obj, ev):
        if obj is getattr(self, "preview_label", None) and ev.type() == QEvent.Resize:
            self._rescale_preview()
        return super().eventFilter(obj, ev)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._rescale_preview()        # 只重新缩放，不重渲染整页

    def showEvent(self, event):
        super().showEvent(event)
        # 布局完成后再确保一次，修正“刚打开时预览不完整”的问题
        self._update_preview()

    def done(self, result: int) -> None:
        if self._markup_doc is not None and self._markup_doc is not self.doc.doc:
            try:
                self._markup_doc.close()
            except Exception:  # noqa: BLE001
                pass
            self._markup_doc = None
        super().done(result)

    # ================================================================ 打印
    def _open_properties(self) -> None:
        """打开系统打印机属性（原版 &Properties）。"""
        name = self.printer_combo.currentText()
        if not name:
            return
        import subprocess
        import sys as _sys
        try:
            if _sys.platform.startswith("win"):
                subprocess.Popen(["rundll32.exe", "printui.dll,PrintUIEntry", "/e", "/n", name])
            else:
                QMessageBox.information(self, tr("print.properties"),
                                        tr("print.props_hint"))
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, tr("print.properties"), str(exc))

    def _open_advanced(self) -> None:
        """原版 Advanced = PCL 驱动优化（此处给出说明）。"""
        QMessageBox.information(self, tr("print.advanced"), tr("print.adv_text"))

    def _open_tips(self) -> None:
        QMessageBox.information(self, tr("print.tips"), tr("print.tips_text"))

    @staticmethod
    def _fit_rect(iw: int, ih: int, aw: int, ah: int) -> QRectF:
        if iw <= 0 or ih <= 0:
            return QRectF(0, 0, aw, ah)
        s = min(aw / iw, ah / ih)
        return QRectF((aw - iw * s) / 2, (ah - ih * s) / 2, iw * s, ih * s)

    def _scale_mode(self) -> str:
        if self.s_none.isChecked():
            return "none"
        if self.s_reduce.isChecked():
            return "reduce"
        if self.s_custom.isChecked():
            return "custom"
        return "fit"

    def _to_gray(self, img: QImage) -> QImage:
        return img.convertToFormat(QImage.Format_Grayscale8).convertToFormat(QImage.Format_RGB888)

    def _draw_bleed_marks(self, painter, vp) -> None:
        painter.save()
        painter.setPen(QColor(0, 0, 0))
        ln = max(10, vp.height() // 40)
        m = 6
        for (x, y, dx, dy) in ((m, m, 1, 1), (vp.width() - m, m, -1, 1),
                               (m, vp.height() - m, 1, -1),
                               (vp.width() - m, vp.height() - m, -1, -1)):
            painter.drawLine(x, y, x + dx * ln, y)
            painter.drawLine(x, y, x, y + dy * ln)
        painter.restore()

    def _make_printer(self, name: str, full: bool):
        """构造 QPrinter。full=False 时不施加任何页面/双面设置，完全用驱动默认值，
        用于某些驱动（如网络复合机）拒绝自定义 DEVMODE 时的降级重试。"""
        pr = QPrinter(QPrinter.HighResolution if full else QPrinter.ScreenResolution)
        if name:
            pr.setPrinterName(name)
        if self.tofile_check.isChecked():
            pr.setOutputFormat(QPrinter.PdfFormat)
            pr.setOutputFileName(self.file_edit.text() or self._default_out())
        else:
            pr.setOutputFormat(QPrinter.NativeFormat)
        try:
            pr.setDocName("lightpdf")
        except Exception:  # noqa: BLE001
            pass
        if not full:
            try:
                pr.setCopyCount(self.copies_spin.value())
            except Exception:  # noqa: BLE001
                pass
            return pr
        orient = QPageLayout.Landscape if self._landscape() else QPageLayout.Portrait
        base = pr.pageLayout()
        try:
            pr.setPageLayout(QPageLayout(base.pageSize(), orient,
                                         base.margins(), base.units()))
        except Exception:  # noqa: BLE001
            pass
        dm = QPrinter.DuplexMode
        if self.duplex_check.isChecked():
            duplex = dm.DuplexShortSide if self.flip_short.isChecked() else dm.DuplexLongSide
        else:
            duplex = dm.DuplexNone
        for fn in (lambda: pr.setDuplex(duplex),
                   lambda: pr.setCopyCount(self.copies_spin.value()),
                   lambda: pr.setCollateCopies(self.collate_check.isChecked())):
            try:
                fn()
            except Exception:  # noqa: BLE001
                pass
        return pr

    def _do_print(self) -> None:
        name = self.printer_combo.currentText()
        tofile = self.tofile_check.isChecked()
        if name and not tofile:
            try:
                if QPrinterInfo.printerInfo(name).isNull():
                    QMessageBox.warning(self, tr("print.title"),
                                        tr("print.printer_missing", name=name))
                    return
            except Exception:  # noqa: BLE001
                pass

        # 第 1 次：带完整设置；失败则第 2 次：退化为驱动默认值重试
        painter, printer = None, None
        for full in (True, False):
            printer = self._make_printer(name, full)
            painter = QPainter(printer)
            if painter.isActive():
                break
            try:
                painter.end()
            except Exception:  # noqa: BLE001
                pass
            painter = None
            if tofile:          # 导出 PDF 一般不会失败，不必重试
                break
        if painter is None or not painter.isActive():
            QMessageBox.warning(self, tr("print.title"),
                                tr("print.failed_detail",
                                   name=name or tr("print.default_printer")))
            return

        dpi = 300 if self.asimage_check.isChecked() else min(200, max(72, printer.resolution()))
        annots = self._annot_mode()
        pages = self._pages()
        try:
            if self.h_booklet.isChecked():
                self._print_sides(painter, printer, self._booklet_output_sides(pages), dpi, True)
            elif self.h_nup.isChecked():
                k = self._pages_per_sheet()
                groups = [pages[i:i + k] for i in range(0, len(pages), k)]
                self._print_sides(painter, printer, groups, dpi, False)
            elif self.h_tile.isChecked():
                self._print_tiled(painter, printer, pages, dpi, annots)
            else:
                self._print_plain(painter, printer, pages, dpi, annots)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, tr("print.title"),
                                tr("print.failed_detail",
                                   name=name or tr("print.default_printer")) + "\n\n" + str(exc))
            return
        finally:
            painter.end()
        self.accept()

    def _page_image(self, pno: int, dpi: int, annots: bool) -> QImage:
        img = self._render_qimage(pno, dpi / 72.0, annots)
        return self._to_gray(img) if self.gray_check.isChecked() else img

    def _draw_scaled(self, painter, img: QImage) -> None:
        vp = painter.viewport()
        mode = self._scale_mode()
        if mode == "none":
            painter.drawImage(0, 0, img)
            return
        if mode == "custom":
            try:
                pct = max(1, min(1000, int(self.custom_edit.text()))) / 100.0
            except ValueError:
                pct = 1.0
            w = int(img.width() * pct)
            h = int(img.height() * pct)
            painter.drawImage(self._fit_rect(w, h, vp.width(), vp.height()),
                              img.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            return
        if mode == "reduce" and img.width() <= vp.width() and img.height() <= vp.height():
            if self.autocenter_check.isChecked():
                painter.drawImage(self._fit_rect(img.width(), img.height(),
                                                 vp.width(), vp.height()), img)
            else:
                painter.drawImage(0, 0, img)
            return
        painter.drawImage(self._fit_rect(img.width(), img.height(),
                                         vp.width(), vp.height()), img)

    def _print_plain(self, painter, printer, pages, dpi: int, annots: bool) -> None:
        first = True
        for pno in pages:
            if not first:
                printer.newPage()
            first = False
            img = self._maybe_autorotate(self._page_image(pno, dpi, annots))
            self._draw_scaled(painter, img)
            if self.bleed_check.isChecked():
                self._draw_bleed_marks(painter, painter.viewport())

    def _print_sides(self, painter, printer, sides, dpi: int, booklet: bool) -> None:
        first = True
        for side in sides:
            if not first:
                printer.newPage()
            first = False
            vp = painter.viewport()
            ncell = len(side)
            for idx, pno in enumerate(side):
                if pno is None:
                    continue
                img = self._page_image(pno, dpi, True)
                if booklet:
                    img = self._maybe_autorotate(img)
                    cell = QRectF(vp.width() / 2.0, 0, vp.width() / 2.0, vp.height())
                    cell.moveLeft(idx * vp.width() / 2.0)
                else:
                    rows, cols = self._grid_for(self._pages_per_sheet())
                    cells = self._nup_cells(ncell, rows, cols)
                    r, c = cells[idx] if idx < len(cells) else (0, 0)
                    cell = QRectF(c * vp.width() / float(cols), r * vp.height() / float(rows),
                                  vp.width() / float(cols), vp.height() / float(rows))
                r = self._fit_rect(img.width(), img.height(), int(cell.width()), int(cell.height()))
                target = QRectF(cell.x() + r.x(), cell.y() + r.y(), r.width(), r.height())
                painter.drawImage(target, img)
            if self.bleed_check.isChecked():
                self._draw_bleed_marks(painter, vp)

    def _print_tiled(self, painter, printer, pages, dpi: int, annots: bool) -> None:
        try:
            zoom = max(10, min(1000, int(self.tile_zoom.text()))) / 100.0
        except ValueError:
            zoom = 1.0
        try:
            overlap = max(0.0, float(self.tile_overlap.text()))       # inch
        except ValueError:
            overlap = 0.0
        first = True
        for pno in pages:
            img = self._page_image(pno, dpi, annots)
            base = img.scaled(int(img.width() * zoom), int(img.height() * zoom),
                              Qt.KeepAspectRatio, Qt.SmoothTransformation)
            vp = painter.viewport()
            ow = int(overlap * dpi)
            step_x = max(1, vp.width() - ow)
            step_y = max(1, vp.height() - ow)
            nx = max(1, -(-base.width() // step_x))
            ny = max(1, -(-base.height() // step_y))
            for iy in range(ny):
                for ix in range(nx):
                    if not first:
                        printer.newPage()
                    first = False
                    src = QRectF(ix * step_x, iy * step_y,
                                 min(vp.width(), base.width() - ix * step_x),
                                 min(vp.height(), base.height() - iy * step_y))
                    painter.drawImage(QRectF(0, 0, src.width(), src.height()),
                                      base, src)
                    if self.tile_cutmarks.isChecked():
                        self._draw_bleed_marks(painter, vp)
                    if self.tile_labels.isChecked():
                        painter.save()
                        painter.setPen(QColor(0, 0, 0))
                        painter.drawText(6, vp.height() - 6,
                                         "%s p%d (%d,%d)" % (getattr(self.doc, "name", "doc"),
                                                             pno + 1, ix + 1, iy + 1))
                        painter.restore()


class MergeDialog(QDialog):
    """Pick several PDFs, reorder them, then merge."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dlg.merge.title"))
        self.resize(580, 440)
        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list.setDragDropMode(QAbstractItemView.InternalMove)
        self.list.setDefaultDropAction(Qt.MoveAction)
        add = QPushButton(tr("dlg.merge.add"))
        rm = QPushButton(tr("dlg.merge.remove"))
        up = QPushButton(tr("dlg.merge.up"))
        dn = QPushButton(tr("dlg.merge.down"))
        add.clicked.connect(self._add)
        rm.clicked.connect(self._remove)
        up.clicked.connect(lambda: self._move(-1))
        dn.clicked.connect(lambda: self._move(1))
        col = QVBoxLayout()
        for b in (add, rm, up, dn):
            col.addWidget(b)
        col.addStretch()
        body = QHBoxLayout()
        body.addWidget(self.list, 1)
        body.addLayout(col)
        bb = QDialogButtonBox()
        bb.addButton(tr("btn.merge"), QDialogButtonBox.AcceptRole).clicked.connect(self.accept)
        bb.addButton(tr("btn.cancel"), QDialogButtonBox.RejectRole).clicked.connect(self.reject)
        lay = QVBoxLayout(self)
        lay.addLayout(body)
        lay.addWidget(bb)

    def _add(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, tr("dlg.merge.add"), "", "PDF (*.pdf)")
        for p in paths:
            self.list.addItem(p)

    def _remove(self) -> None:
        for it in self.list.selectedItems():
            self.list.takeItem(self.list.row(it))

    def _move(self, delta: int) -> None:
        row = self.list.currentRow()
        if row < 0:
            return
        new = row + delta
        if new < 0 or new >= self.list.count():
            return
        item = self.list.takeItem(row)
        self.list.insertItem(new, item)
        self.list.setCurrentRow(new)

    def paths(self) -> list:
        return [self.list.item(i).text() for i in range(self.list.count())]


class ImagesToPdfDialog(QDialog):
    """Pick several images, reorder them, choose page size and scaling."""

    PAGE_SIZES = [("original", None), ("A4", (595.0, 842.0)), ("A3", (842.0, 1191.0)),
                  ("A5", (420.0, 595.0)), ("Letter", (612.0, 792.0))]

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("dlg.imgs2pdf.title"))
        self.resize(600, 480)
        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list.setDragDropMode(QAbstractItemView.InternalMove)
        self.list.setDefaultDropAction(Qt.MoveAction)

        add = QPushButton(tr("dlg.imgs2pdf.add"))
        rm = QPushButton(tr("dlg.merge.remove"))
        up = QPushButton(tr("dlg.merge.up"))
        dn = QPushButton(tr("dlg.merge.down"))
        add.clicked.connect(self._add)
        rm.clicked.connect(self._remove)
        up.clicked.connect(lambda: self._move(-1))
        dn.clicked.connect(lambda: self._move(1))
        col = QVBoxLayout()
        for b in (add, rm, up, dn):
            col.addWidget(b)
        col.addStretch()
        body = QHBoxLayout()
        body.addWidget(self.list, 1)
        body.addLayout(col)

        self.page_size = QComboBox()
        self.page_size.addItem(tr("ps.original"), None)
        for label, _sz in self.PAGE_SIZES[1:]:
            self.page_size.addItem(label, label)
        self.fit_combo = QComboBox()
        self.fit_combo.addItem(tr("fit.fit"), "fit")
        self.fit_combo.addItem(tr("fit.original"), "original")
        self.page_size.currentIndexChanged.connect(self._sync_fit)

        form = QFormLayout()
        form.addRow(tr("dlg.imgs2pdf.pagesize"), self.page_size)
        form.addRow(tr("dlg.imgs2pdf.fit"), self.fit_combo)

        bb = QDialogButtonBox()
        bb.addButton(tr("btn.create"), QDialogButtonBox.AcceptRole).clicked.connect(self.accept)
        bb.addButton(tr("btn.cancel"), QDialogButtonBox.RejectRole).clicked.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addLayout(body)
        lay.addLayout(form)
        lay.addWidget(bb)
        self._sync_fit()

    def _sync_fit(self) -> None:
        self.fit_combo.setEnabled(self.page_size.currentData() is not None)

    def _add(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(
            self, tr("dlg.imgs2pdf.add"), "",
            "Images (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.gif *.webp)")
        for p in paths:
            self.list.addItem(p)

    def _remove(self) -> None:
        for it in self.list.selectedItems():
            self.list.takeItem(self.list.row(it))

    def _move(self, delta: int) -> None:
        row = self.list.currentRow()
        if row < 0:
            return
        new = row + delta
        if new < 0 or new >= self.list.count():
            return
        item = self.list.takeItem(row)
        self.list.insertItem(new, item)
        self.list.setCurrentRow(new)

    def paths(self) -> list:
        return [self.list.item(i).text() for i in range(self.list.count())]

    def page_size_pts(self):
        label = self.page_size.currentData()
        if label is None:
            return None
        for name, sz in self.PAGE_SIZES:
            if name == label:
                return sz
        return None

    def fit_mode(self) -> str:
        return self.fit_combo.currentData() if self.page_size.currentData() is not None else "original"


class StampSettingsDialog(QDialog):
    """Define a text or image stamp (shape, text, colours)."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        from . import stamps
        self.stamps = stamps
        self.cfg = stamps.load_config()
        self.setWindowTitle(tr("dlg.stamp.title"))
        self.resize(560, 620)

        self.mode = QComboBox()
        self.mode.addItem(tr("stamp.text"), "text")
        self.mode.addItem(tr("stamp.image"), "image")
        self.mode.setCurrentIndex(0 if self.cfg.get("mode", "text") == "text" else 1)

        # text fields
        self.text = QPlainTextEdit(self.cfg.get("text", "APPROVED"))
        self.text.setMaximumHeight(64)
        self.font = QComboBox()
        self.font.addItem(tr("dlg.edit.font_default"), "helv")
        self.font.addItem("Times", "tiro")
        self.font.addItem("Courier", "cour")
        self.font.addItem("中文（内置）", "china-s")
        try:
            from ..core import fonts as _fonts
            for label, path in _fonts.system_fonts():
                self.font.addItem(label, label)
        except Exception:  # noqa: BLE001
            pass
        self.size = QSpinBox(); self.size.setRange(6, 300)
        self.size.setValue(int(self.cfg.get("size", 24)))
        self.shape = QComboBox()
        for key, lab in (("rect", "shape.rect"), ("round", "shape.round"),
                         ("ellipse", "shape.ellipse"), ("none", "shape.none")):
            self.shape.addItem(tr(lab), key)
        self.border_w = QSpinBox(); self.border_w.setRange(0, 40)
        self.border_w.setValue(int(self.cfg.get("border_width", 3)))
        self.padding = QSpinBox(); self.padding.setRange(0, 120)
        self.padding.setValue(int(self.cfg.get("padding", 10)))
        self.transparent = QCheckBox(tr("dlg.stamp.transparent"))
        self.transparent.setChecked(bool(self.cfg.get("transparent", True)))

        # image fields
        self.image = QLineEdit(self.cfg.get("image", ""))
        choose = QPushButton(tr("dlg.stamp.choose"))
        choose.clicked.connect(self._choose_image)
        self.image_w = QSpinBox(); self.image_w.setRange(20, 2000)
        self.image_w.setValue(int(self.cfg.get("image_width", 160)))

        # colour buttons
        self.btn_text_color = self._color_button("text_color", self.cfg.get("text_color", "#C00000"))
        self.btn_border_color = self._color_button("border_color", self.cfg.get("border_color", "#C00000"))
        self.btn_fill = self._color_button("fill", self.cfg.get("fill", "#FFFFFF"))

        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumHeight(150)
        self.preview.setStyleSheet("background:#8FB69A;border:1px solid #4E7D57;")

        form = QFormLayout()
        form.addRow(tr("dlg.stamp.type"), self.mode)
        form.addRow(tr("dlg.stamp.text"), self.text)
        form.addRow(tr("dlg.stamp.font"), self.font)
        form.addRow(tr("dlg.stamp.size"), self.size)
        form.addRow(tr("dlg.stamp.textcolor"), self.btn_text_color)
        form.addRow(tr("dlg.stamp.shape"), self.shape)
        form.addRow(tr("dlg.stamp.border"), self.btn_border_color)
        form.addRow(tr("dlg.stamp.borderw"), self.border_w)
        form.addRow(tr("dlg.stamp.fill"), self.btn_fill)
        form.addRow("", self.transparent)
        img_row = QWidget(); il = QHBoxLayout(img_row); il.setContentsMargins(0, 0, 0, 0)
        il.addWidget(self.image); il.addWidget(choose)
        form.addRow(tr("dlg.stamp.image"), img_row)
        form.addRow(tr("dlg.stamp.width"), self.image_w)

        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)

        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(QLabel(tr("dlg.stamp.preview")))
        lay.addWidget(self.preview, 1)
        lay.addWidget(bb)

        self.mode.currentIndexChanged.connect(self._sync)
        for w in (self.font, self.shape):
            w.currentIndexChanged.connect(self._refresh)
        for w in (self.size, self.border_w, self.padding, self.image_w):
            w.valueChanged.connect(self._refresh)
        self.text.textChanged.connect(self._refresh)
        self.transparent.toggled.connect(self._refresh)
        self.image.textChanged.connect(self._refresh)
        self._sync()

    def _color_button(self, key: str, initial: str):
        btn = QPushButton()
        btn.setProperty("colorkey", key)
        btn._color = QColor(initial)

        def paint():
            btn.setStyleSheet(f"background:{btn._color.name()};border:1px solid #4E7D57;")
            btn.setText(btn._color.name())
        def pick():
            c = QColorDialog.getColor(btn._color, self)
            if c.isValid():
                btn._color = c
                paint()
                self._refresh()
        btn.clicked.connect(pick)
        paint()
        return btn

    def _choose_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, tr("dlg.stamp.image"), "",
                                              "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)")
        if path:
            self.image.setText(path)

    def _sync(self) -> None:
        text_mode = self.mode.currentData() == "text"
        for w in (self.text, self.font, self.size, self.shape, self.border_w,
                  self.padding, self.transparent, self.btn_text_color):
            w.setEnabled(text_mode)
        for w in (self.image, self.image_w):
            w.setEnabled(not text_mode)
        self._refresh()

    def _collect(self) -> dict:
        return {
            "mode": self.mode.currentData(),
            "text": self.text.toPlainText(),
            "font": self.font.currentData(),
            "size": self.size.value(),
            "text_color": self.btn_text_color._color.name(),
            "shape": self.shape.currentData(),
            "border_color": self.btn_border_color._color.name(),
            "border_width": self.border_w.value(),
            "fill": self.btn_fill._color.name(),
            "transparent": self.transparent.isChecked(),
            "padding": self.padding.value(),
            "image": self.image.text().strip(),
            "image_width": self.image_w.value(),
        }

    def _refresh(self) -> None:
        try:
            res = self.stamps.render_stamp(self._collect())
        except Exception:  # noqa: BLE001
            res = None
        if not res:
            self.preview.setText("—")
            return
        png, w, h = res
        pix = QPixmap()
        pix.loadFromData(png, "PNG")
        self.preview.setPixmap(pix.scaled(max(50, self.preview.width() - 8),
                                          max(50, self.preview.height() - 8),
                                          Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def config(self) -> dict:
        return self._collect()
