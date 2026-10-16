"""Application dialogs (localized)."""
from __future__ import annotations

import fitz
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import (QColor, QImage, QPageLayout, QPageSize, QPainter,
                          QPixmap, QTransform)
from PySide6.QtPrintSupport import QPrinter, QPrinterInfo
from PySide6.QtWidgets import (QAbstractItemView, QButtonGroup, QCheckBox,
                               QColorDialog, QComboBox,
                               QDialog, QDialogButtonBox, QDoubleSpinBox,
                               QFileDialog, QFormLayout, QGroupBox, QHBoxLayout,
                               QLabel, QLineEdit, QListWidget, QListWidgetItem,
                               QMessageBox, QPlainTextEdit, QPushButton,
                               QRadioButton, QScrollArea, QSlider, QSpinBox,
                               QSplitter, QTextEdit, QVBoxLayout, QWidget)

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
    """A Foxit-style print dialog: preview + range + handling + duplex +
    orientation + paper + output."""

    def __init__(self, doc, current_page: int, parent=None) -> None:
        super().__init__(parent)
        self.doc = doc
        self.cur = current_page
        self.n = doc.page_count
        self.setWindowTitle(tr("print.title"))
        self.resize(820, 560)

        # ----- options
        self.printer_combo = QComboBox()
        printers = QPrinterInfo.availablePrinterNames()
        if printers:
            self.printer_combo.addItems(printers)
            default = QPrinterInfo.defaultPrinterName()
            if default in printers:
                self.printer_combo.setCurrentText(default)

        self.range_combo = QComboBox()
        self.range_combo.addItem(tr("print.range.all"), "all")
        self.range_combo.addItem(tr("print.range.current"), "current")
        self.range_combo.addItem(tr("print.range.pages"), "pages")
        self.from_spin = QSpinBox(); self.from_spin.setRange(1, max(1, self.n))
        self.from_spin.setValue(max(1, current_page + 1))
        self.to_spin = QSpinBox(); self.to_spin.setRange(1, max(1, self.n))
        self.to_spin.setValue(max(1, current_page + 1))

        self.content_combo = QComboBox()
        self.content_combo.addItem(tr("print.content.doc"), "doc")
        self.content_combo.addItem(tr("print.content.markup"), "markup")
        self.content_combo.addItem(tr("print.content.booklet"), "booklet")
        self.content_combo.setCurrentIndex(0)   # default: document only

        self.booklet_binding = QComboBox()
        self.booklet_binding.addItem(tr("print.booklet.left"), "left")
        self.booklet_binding.addItem(tr("print.booklet.right"), "right")
        self.booklet_subset = QComboBox()
        self.booklet_subset.addItem(tr("print.booklet.both"), "both")
        self.booklet_subset.addItem(tr("print.booklet.front"), "front")
        self.booklet_subset.addItem(tr("print.booklet.back"), "back")
        self.booklet_autorotate = QCheckBox(tr("print.booklet.autorotate"))
        self.booklet_autorotate.setChecked(True)

        self.scale_combo = QComboBox()
        self.scale_combo.addItem(tr("print.scale.fit"), "fit")
        self.scale_combo.addItem(tr("print.scale.none"), "none")
        self.scale_combo.addItem(tr("print.scale.shrink"), "shrink")

        self.duplex_combo = QComboBox()
        self.duplex_combo.addItem(tr("print.duplex.simplex"), "simplex")
        self.duplex_combo.addItem(tr("print.duplex.long"), "long")
        self.duplex_combo.addItem(tr("print.duplex.short"), "short")

        self.orient_combo = QComboBox()
        self.orient_combo.addItem(tr("print.orientation.auto"), "auto")
        self.orient_combo.addItem(tr("print.orientation.portrait"), "portrait")
        self.orient_combo.addItem(tr("print.orientation.landscape"), "landscape")

        self.paper_combo = QComboBox()
        self.paper_combo.addItem(tr("print.paper.auto"), None)
        self.paper_combo.addItem("A4", QPageSize.A4)
        self.paper_combo.addItem("Letter", QPageSize.Letter)
        self.paper_combo.addItem("A3", QPageSize.A3)
        self.paper_combo.addItem("A5", QPageSize.A5)

        self.copies_spin = QSpinBox(); self.copies_spin.setRange(1, 99)
        self.collate_check = QCheckBox(tr("print.collate"))

        self.tofile_check = QCheckBox(tr("print.tofile"))
        self.file_edit = QLineEdit(); self.file_edit.setEnabled(False)
        self.file_btn = QPushButton("...")
        self.file_btn.setEnabled(False); self.file_btn.setFixedWidth(32)
        self.file_btn.clicked.connect(self._pick_file)
        self.tofile_check.toggled.connect(self._sync_file)

        # ----- preview (one whole page, with prev/next)
        self._markup_doc = None
        self._preview_index = 0
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setMinimumSize(320, 420)
        self.preview_label.setStyleSheet("background:#8FB69A;border:1px solid #4E7D57;")
        self.prev_btn = QPushButton("\u25c0")
        self.next_btn = QPushButton("\u25b6")
        self.prev_btn.setFixedWidth(44)
        self.next_btn.setFixedWidth(44)
        self.prev_btn.clicked.connect(lambda: self._preview_step(-1))
        self.next_btn.clicked.connect(lambda: self._preview_step(1))
        self.page_indicator = QLabel("0 / 0")
        self.page_indicator.setAlignment(Qt.AlignCenter)
        self.page_indicator.setMinimumWidth(64)

        # ----- layout
        opts = QGroupBox(tr("print.title"))
        form = QFormLayout(opts)
        self.adv_btn = QPushButton(tr("print.advanced"))
        self.adv_btn.clicked.connect(self._open_advanced)
        prow = QWidget()
        pl = QHBoxLayout(prow); pl.setContentsMargins(0, 0, 0, 0)
        pl.addWidget(self.printer_combo)
        pl.addWidget(self.adv_btn)
        form.addRow(tr("print.printer"), prow)
        form.addRow(tr("print.range"), self.range_combo)
        rng = QWidget(); rl = QHBoxLayout(rng); rl.setContentsMargins(0, 0, 0, 0)
        rl.addWidget(self.from_spin); rl.addWidget(QLabel(tr("print.to"))); rl.addWidget(self.to_spin)
        form.addRow("", rng)
        form.addRow(tr("print.content"), self.content_combo)
        form.addRow(tr("print.booklet.binding"), self.booklet_binding)
        form.addRow("", self.booklet_autorotate)
        form.addRow(tr("print.scale"), self.scale_combo)
        form.addRow(tr("print.duplex"), self.duplex_combo)
        form.addRow(tr("print.orientation"), self.orient_combo)
        form.addRow(tr("print.paper"), self.paper_combo)
        form.addRow(tr("print.copies"), self.copies_spin)
        form.addRow("", self.collate_check)
        form.addRow("", self.tofile_check)
        fp = QWidget(); fl = QHBoxLayout(fp); fl.setContentsMargins(0, 0, 0, 0)
        fl.addWidget(self.file_edit); fl.addWidget(self.file_btn)
        form.addRow("", fp)

        left = QGroupBox(tr("print.preview"))
        nav = QHBoxLayout()
        nav.addStretch()
        nav.addWidget(self.prev_btn)
        nav.addWidget(self.page_indicator)
        nav.addWidget(self.next_btn)
        nav.addStretch()
        ll = QVBoxLayout(left)
        ll.addWidget(self.preview_label, 1)
        ll.addLayout(nav)

        body = QHBoxLayout()
        body.addWidget(left, 3)
        body.addWidget(opts, 4)

        buttons = QDialogButtonBox()
        self.print_btn = buttons.addButton(tr("print.button"), QDialogButtonBox.AcceptRole)
        buttons.addButton(tr("btn.cancel"), QDialogButtonBox.RejectRole)
        buttons.accepted.connect(self._do_print)
        buttons.rejected.connect(self.reject)

        root = QVBoxLayout(self)
        root.addLayout(body)
        root.addWidget(buttons)

        for w in (self.range_combo, self.content_combo, self.scale_combo,
                  self.duplex_combo, self.orient_combo, self.paper_combo,
                  self.from_spin, self.to_spin):
            sig = getattr(w, "currentIndexChanged", None) or w.valueChanged
            sig.connect(self._update_preview)
        self._sync_range()
        self.range_combo.currentIndexChanged.connect(self._sync_range)
        self.content_combo.currentIndexChanged.connect(self._sync_booklet_opts)
        self._sync_booklet_opts()
        self._update_preview()

    # ---------------------------------------------------------------- helpers
    def _sync_range(self) -> None:
        enabled = self.range_combo.currentData() == "pages"
        self.from_spin.setEnabled(enabled)
        self.to_spin.setEnabled(enabled)

    def _sync_file(self, on: bool) -> None:
        self.file_edit.setEnabled(on)
        self.file_btn.setEnabled(on)
        if on and not self.file_edit.text():
            self.file_edit.setText(self._default_out())

    def _default_out(self) -> str:
        base = "output.pdf"
        if getattr(self.doc, "path", None):
            import os
            base = os.path.splitext(os.path.basename(self.doc.path))[0] + ".pdf"
        return base

    def _pick_file(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, tr("print.tofile"),
                                              self.file_edit.text() or self._default_out(),
                                              "PDF (*.pdf)")
        if path:
            self.file_edit.setText(path)

    def _open_advanced(self) -> None:
        """Open the selected printer's own settings/preferences dialog."""
        name = self.printer_combo.currentText()
        if not name:
            return
        import subprocess
        import sys as _sys
        try:
            if _sys.platform.startswith("win"):
                subprocess.Popen(["rundll32.exe", "printui.dll,PrintUIEntry",
                                  "/e", "/n", name])
            else:
                QMessageBox.information(
                    self, tr("print.advanced"),
                    "Printer-specific settings are managed by your operating system.")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, tr("print.advanced"), str(exc))

    @staticmethod
    def _index_of(combo, data) -> int:
        for i in range(combo.count()):
            if combo.itemData(i) == data:
                return i
        return -1

    def _sync_booklet_opts(self) -> None:
        on = self.content_combo.currentData() == "booklet"
        self.booklet_binding.setEnabled(on)
        self.booklet_subset.setEnabled(on)
        self.booklet_autorotate.setEnabled(on)
        # Booklet forces landscape paper and duplex (short-edge flip).
        if on:
            if not getattr(self, "_booklet_saved", None):
                self._booklet_saved = (self.orient_combo.currentIndex(),
                                       self.duplex_combo.currentIndex())
            self.orient_combo.setCurrentIndex(self._index_of(self.orient_combo, "landscape"))
            self.duplex_combo.setCurrentIndex(self._index_of(self.duplex_combo, "short"))
            self.orient_combo.setEnabled(False)
            self.duplex_combo.setEnabled(False)
        else:
            saved = getattr(self, "_booklet_saved", None)
            if saved:
                self.orient_combo.setCurrentIndex(saved[0])
                self.duplex_combo.setCurrentIndex(saved[1])
                self._booklet_saved = None
            self.orient_combo.setEnabled(True)
            self.duplex_combo.setEnabled(True)

    def _booklet_output_sides(self, pages: list) -> list:
        """Apply binding direction and subset to the imposed sides."""
        sides = [list(s) for s in self._booklet_sides(pages)]
        if self.booklet_binding.currentData() == "right":
            sides = [[s[1], s[0]] for s in sides]
        sub = self.booklet_subset.currentData()
        if sub == "front":
            sides = sides[0::2]
        elif sub == "back":
            sides = sides[1::2]
        return sides

    def _maybe_autorotate(self, img: QImage) -> QImage:
        if self.booklet_autorotate.isChecked() and img.width() > img.height():
            return img.transformed(QTransform().rotate(90))
        return img

    def _booklet_sides(self, pages: list) -> list:
        """Saddle-stitch imposition: list of sides, each [left, right] (None=blank)."""
        seq = list(pages) + [None] * ((4 - len(pages) % 4) % 4)
        n = len(seq)
        sides = []
        for s in range(n // 4):
            sides.append([seq[n - 1 - 2 * s], seq[2 * s]])      # front
            sides.append([seq[2 * s + 1], seq[n - 2 - 2 * s]])  # back
        return sides

    def _pages(self) -> list:
        mode = self.range_combo.currentData()
        if mode == "current":
            return [self.cur]
        if mode == "pages":
            a, b = self.from_spin.value() - 1, self.to_spin.value() - 1
            if a > b:
                a, b = b, a
            return list(range(max(0, a), min(self.n - 1, b) + 1))
        return list(range(self.n))

    def _landscape(self) -> bool:
        if self.content_combo.currentData() == "booklet":
            return True
        mode = self.orient_combo.currentData()
        if mode == "portrait":
            return False
        if mode == "landscape":
            return True
        pages = self._pages()
        if not pages:
            return False
        r = self.doc.page(pages[0]).rect
        return r.width > r.height

    # ---------------------------------------------------------------- preview
    def _markup_source(self):
        """A copy of the document with sticky notes removed (notes never print)."""
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

    def _preview_items(self):
        """Return (items, booklet). Normal: each item is a single page number.
        Booklet: each item is one imposed side [left, right]."""
        pages = self._pages()
        if not pages:
            return [], False
        if self.content_combo.currentData() == "booklet":
            return self._booklet_output_sides(pages), True
        return [[p] for p in pages], False

    def _render_side_image(self, side, annots: bool) -> QImage:
        ref = None
        imgs = []
        for pno in side:
            im = (self._maybe_autorotate(self._render_qimage(pno, 1.2, annots))
                  if pno is not None else None)
            imgs.append(im)
            if ref is None and im is not None:
                ref = im
        if ref is None:
            return QImage(1, 1, QImage.Format_RGB888)
        w, h = ref.width(), ref.height()
        canvas = QImage(w * 2, h, QImage.Format_RGB888)
        canvas.fill(Qt.white)
        p = QPainter(canvas)
        for idx, im in enumerate(imgs):
            if im is not None:
                p.drawImage(idx * w, 0, im)
        p.end()
        return canvas

    def _preview_step(self, delta: int) -> None:
        items, _ = self._preview_items()
        if not items:
            return
        self._preview_index = max(0, min(len(items) - 1, self._preview_index + delta))
        self._update_preview()

    def _update_preview(self) -> None:
        items, booklet = self._preview_items()
        if not items:
            self.page_indicator.setText("0 / 0")
            self.preview_label.clear()
            self.prev_btn.setEnabled(False)
            self.next_btn.setEnabled(False)
            return
        self._preview_index = max(0, min(len(items) - 1, self._preview_index))
        self.page_indicator.setText(f"{self._preview_index + 1} / {len(items)}")
        self.prev_btn.setEnabled(self._preview_index > 0)
        self.next_btn.setEnabled(self._preview_index < len(items) - 1)
        annots = self.content_combo.currentData() == "markup"
        if booklet:
            content = self._render_side_image(items[self._preview_index], True)
        else:
            content = self._render_qimage(items[self._preview_index][0], 1.5, annots)
            if self._landscape():
                content = content.transformed(QTransform().rotate(90))
        qpix = QPixmap.fromImage(self._paper_canvas(content))
        area = self.preview_label.size()
        self.preview_label.setPixmap(qpix.scaled(
            max(50, area.width() - 4), max(50, area.height() - 4),
            Qt.KeepAspectRatio, Qt.SmoothTransformation))

    PREVIEW_BG = "#8FB69A"   # tinted backdrop so the white page stands out

    def _paper_canvas(self, content: QImage) -> QImage:
        """Draw the content on a sheet whose aspect matches the output paper
        (landscape for booklet), over a tinted backdrop."""
        land = self._landscape()
        ar = (297.0 / 210.0) if land else (210.0 / 297.0)
        if land:
            sw = int(content.width() * 1.06)
            sh = int(sw / ar)
        else:
            sh = int(content.height() * 1.06)
            sw = int(sh * ar)
        sw = max(sw, content.width() + 4)
        sh = max(sh, content.height() + 4)
        gut = 16
        canvas = QImage(sw + 2 * gut, sh + 2 * gut, QImage.Format_RGB888)
        canvas.fill(QColor(self.PREVIEW_BG))
        p = QPainter(canvas)
        p.fillRect(gut, gut, sw, sh, Qt.white)
        p.setPen(QColor("#4E7D57"))
        p.drawRect(gut, gut, sw - 1, sh - 1)
        p.drawImage(gut + (sw - content.width()) // 2,
                    gut + (sh - content.height()) // 2, content)
        p.end()
        return canvas

    def done(self, result: int) -> None:
        if self._markup_doc is not None and self._markup_doc is not self.doc.doc:
            try:
                self._markup_doc.close()
            except Exception:  # noqa: BLE001
                pass
            self._markup_doc = None
        super().done(result)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_preview()

    # ------------------------------------------------------------------ print
    def _do_print(self) -> None:
        printer = QPrinter(QPrinter.HighResolution)
        if self.printer_combo.currentText():
            printer.setPrinterName(self.printer_combo.currentText())
        # Configure the output device first: switching output format can reset
        # the page layout, so set it before applying orientation/page size.
        if self.tofile_check.isChecked():
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(self.file_edit.text() or self._default_out())
        else:
            printer.setOutputFormat(QPrinter.NativeFormat)

        booklet = self.content_combo.currentData() == "booklet"
        orient = (QPageLayout.Landscape if (booklet or self._landscape())
                  else QPageLayout.Portrait)
        paper = self.paper_combo.currentData()
        base = printer.pageLayout()
        page_size = QPageSize(paper) if paper is not None else base.pageSize()
        try:
            printer.setPageLayout(QPageLayout(page_size, orient, base.margins(),
                                              base.units()))
        except Exception:  # noqa: BLE001
            pass
        dm = QPrinter.DuplexMode
        if booklet:
            duplex = dm.DuplexShortSide           # booklet requires duplex, short-edge
        else:
            duplex = {"simplex": dm.DuplexNone, "long": dm.DuplexLongSide,
                      "short": dm.DuplexShortSide}.get(self.duplex_combo.currentData(),
                                                       dm.DuplexNone)
        try:
            printer.setDuplex(duplex)
        except Exception:  # noqa: BLE001
            pass
        printer.setCopyCount(self.copies_spin.value())
        try:
            printer.setCollateCopies(self.collate_check.isChecked())
        except Exception:  # noqa: BLE001
            pass

        from PySide6.QtGui import QPainter
        painter = QPainter(printer)
        if not painter.isActive():
            QMessageBox.warning(self, tr("print.title"), tr("print.failed"))
            return
        dpi = min(200, max(72, printer.resolution()))   # bounded raster size
        scale = self.scale_combo.currentData()
        content = self.content_combo.currentData()
        annots = content == "markup"
        pages = self._pages()
        try:
            if content == "booklet":
                self._print_booklet(painter, printer, pages, dpi)
            else:
                first = True
                for pno in pages:
                    if not first:
                        printer.newPage()
                    first = False
                    self._draw_page(painter, self._page_image(pno, dpi, annots), scale)
        finally:
            painter.end()
        self.accept()

    def _page_image(self, pno: int, dpi: int, annots: bool) -> QImage:
        return self._render_qimage(pno, dpi / 72.0, annots)

    @staticmethod
    def _fit_rect(iw: int, ih: int, aw: int, ah: int) -> QRectF:
        """Largest centred rect (keep aspect) fitting an iw x ih image in aw x ah."""
        if iw <= 0 or ih <= 0:
            return QRectF(0, 0, aw, ah)
        s = min(aw / iw, ah / ih)
        dw, dh = iw * s, ih * s
        return QRectF((aw - dw) / 2, (ah - dh) / 2, dw, dh)

    def _draw_page(self, painter, img: QImage, scale: str) -> None:
        vp = painter.viewport()
        if scale == "none" or (scale == "shrink" and img.width() <= vp.width()
                               and img.height() <= vp.height()):
            painter.drawImage(0, 0, img)
            return
        # Scale during painting (no huge intermediate QImage allocation).
        painter.drawImage(self._fit_rect(img.width(), img.height(),
                                         vp.width(), vp.height()), img)

    def _print_booklet(self, painter, printer, pages, dpi: int) -> None:
        """Saddle-stitch imposition: two logical pages per sheet side."""
        sides = self._booklet_output_sides(pages)
        first = True
        for side in sides:
            if not first:
                printer.newPage()
            first = False
            vp = painter.viewport()
            half = vp.width() // 2
            for idx, pno in enumerate(side):
                if pno is None:
                    continue
                img = self._maybe_autorotate(self._page_image(pno, dpi, True))
                r = self._fit_rect(img.width(), img.height(), half, vp.height())
                painter.drawImage(
                    QRectF(idx * half + r.x(), r.y(), r.width(), r.height()), img)


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
