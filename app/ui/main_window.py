"""Main application window with multi-document tabs."""
from __future__ import annotations

import os
from typing import Dict, List, Optional

import fitz
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import (QAction, QActionGroup, QColor, QImage, QKeySequence,
                           QPixmap)
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtWidgets import (QApplication, QColorDialog, QDockWidget,
                               QFileDialog, QInputDialog, QLabel, QLineEdit,
                               QMainWindow, QMessageBox, QSlider, QTabWidget,
                               QToolBar, QToolButton, QWidget)

from .. import i18n
from ..i18n import tr, language, set_language
from ..core import annotations as annot
from ..core import compare as cmp
from ..core import convert as conv
from ..core import fonts as fonts_mod
from ..core import ocr as ocr
from ..core import page_ops as ops
from ..core.document import PdfDocument, PdfError
from ..core.editor import insert_image, insert_text_box, replace_span, text_size
from . import stamps
from .about import AboutDialog
from .dialogs import (CompareWindow, HeaderFooterDialog, ImagesToPdfDialog,
                      InsertPagesDialog, MarkupStyleDialog, MergeDialog,
                      PageNumbersDialog, PrintDialog, PropertiesDialog,
                      RotateDialog, SplitDialog, StampSettingsDialog,
                      TextEditDialog, WatermarkDialog)
from .document_tab import DocumentTab
from .icons import icon
from .panels import LeftDock, ResultsPanel
from .pdf_view import PdfView

TOOL_NAMES = ["hand", "select", "highlight", "underline", "strikeout", "note",
              "freetext", "rect", "ellipse", "line", "arrow", "stamp",
              "edittext", "insertimage"]

# concise toolbar labels (shown under the icon): key -> (zh, en)
SHORT_LABELS = {
    "act.new": ("新建", "New"),
    "act.open": ("打开", "Open"),
    "act.save": ("保存", "Save"),
    "act.prev": ("上一页", "Prev"),
    "act.next": ("下一页", "Next"),
    "act.zoom_out": ("缩小", "Zoom -"),
    "act.zoom_in": ("放大", "Zoom +"),
    "act.fit_width": ("适宽", "Width"),
    "act.fit_page": ("适页", "Page"),
    "act.find": ("查找", "Find"),
    "act.compare": ("对比", "Compare"),
    "tool.hand": ("手形", "Hand"),
    "tool.select": ("选择", "Select"),
    "tool.highlight": ("高亮", "Highlight"),
    "tool.underline": ("下划线", "Underline"),
    "tool.strikeout": ("删除线", "Strike"),
    "tool.note": ("便签", "Note"),
    "tool.freetext": ("文本框", "Text"),
    "tool.rect": ("矩形", "Rect"),
    "tool.ellipse": ("椭圆", "Ellipse"),
    "tool.line": ("直线", "Line"),
    "tool.arrow": ("箭头", "Arrow"),
    "tool.stamp": ("图章", "Stamp"),
    "tool.edittext": ("改字", "Edit"),
    "tool.insertimage": ("插图", "Image"),
}


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.resize(1400, 900)

        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setDocumentMode(True)
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.tabs.tabCloseRequested.connect(self._close_tab)
        self.setCentralWidget(self.tabs)

        self.left = LeftDock()
        self.left.thumbnails.pageActivated.connect(self._goto_page)
        self.left.outline.set_page_callback(self._goto_page)
        self.dock_left = QDockWidget()
        self.dock_left.setWidget(self.left)
        self.dock_left.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_left)

        self.results = ResultsPanel()
        self.results.hitActivated.connect(self._result_activated)
        self.dock_right = QDockWidget()
        self.dock_right.setWidget(self.results)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_right)

        self._search_hits: List[tuple] = []
        self._actions: Dict[str, QAction] = {}
        self._menus: Dict[str, object] = {}
        self._tool_actions: Dict[str, QAction] = {}

        self._build_actions()
        self._build_menus()
        self._build_toolbars()
        self._build_statusbar()
        self.retranslate()
        self._update_title()
        self._set_enabled(False)

    # ------------------------------------------------------------ current tab
    def _cur_tab(self) -> Optional[DocumentTab]:
        w = self.tabs.currentWidget()
        return w if isinstance(w, DocumentTab) else None

    def _cur_doc(self) -> Optional[PdfDocument]:
        tab = self._cur_tab()
        return tab.doc if tab else None

    def _cur_view(self) -> Optional[PdfView]:
        tab = self._cur_tab()
        return tab.view if tab else None

    def _add_tab(self, doc: PdfDocument) -> DocumentTab:
        tab = DocumentTab(doc)
        v = tab.view
        v.pageChanged.connect(lambda p, t=tab: self._on_page_changed(p, t))
        v.zoomChanged.connect(lambda z, t=tab: self._on_zoom_changed(z, t))
        v.spanPicked.connect(lambda s, t=tab: self._on_span_picked(s, t))
        v.pointPicked.connect(lambda i, dp, t=tab: self._on_point_picked(t, i, dp))
        v.rectPicked.connect(lambda i, r, tl, t=tab: self._on_rect_picked(t, i, r, tl))
        v.statusMessage.connect(lambda m, t=tab: self._on_status(m, t))
        v.aboutToModify.connect(lambda t=tab: self._update_undo_redo())
        v.annotEditRequested.connect(lambda i, x, t=tab: self._on_annot_edit(t, i, x))
        v.noteRequested.connect(lambda i, p, t=tab: self._on_note_requested(t, i, p))
        v.annotActivated.connect(lambda i, x, t=tab: self._on_annot_activated(t, i, x))
        v.stampRequested.connect(lambda i, p, t=tab: self._on_stamp_requested(t, i, p))
        idx = self.tabs.addTab(tab, tab.title())
        self.tabs.setCurrentIndex(idx)
        self._set_enabled(True)
        self._sync_current()
        return tab

    def _sync_current(self) -> None:
        tab = self._cur_tab()
        if tab:
            self.left.thumbnails.set_document(tab.doc)
            self.left.outline.set_document(tab.doc)
            self._on_page_changed(tab.view.current_page(), tab)
        else:
            self.left.thumbnails.set_document(None)
            self.left.outline.set_document(None)
            self.page_label.setText(tr("status.no_doc"))
        self._update_title()

    def _on_tab_changed(self, _idx: int) -> None:
        self.results.clear()
        self.search_label.clear()
        self._search_hits = []
        self._set_enabled(self._cur_tab() is not None)
        self._update_undo_redo()
        self._sync_current()

    def _close_tab(self, idx: int) -> None:
        w = self.tabs.widget(idx)
        if isinstance(w, DocumentTab):
            if w.doc.dirty:
                self.tabs.setCurrentIndex(idx)
                resp = QMessageBox.question(self, tr("msg.unsaved.title"),
                                            tr("msg.unsaved.body", name=w.title()),
                                            QMessageBox.Save | QMessageBox.Discard
                                            | QMessageBox.Cancel)
                if resp == QMessageBox.Cancel:
                    return
                if resp == QMessageBox.Save and not self._save_tab_doc(w):
                    return
            w.doc.close()
        self.tabs.removeTab(idx)
        w.deleteLater()
        self._set_enabled(self._cur_tab() is not None)
        self._update_undo_redo()
        if self.tabs.count() == 0:
            self._update_title()

    # ------------------------------------------------------------------ build
    def _mk(self, key, slot, icon_name="", shortcut=None, checkable=False) -> QAction:
        a = QAction(self)
        if icon_name:
            a.setIcon(icon(icon_name))
        a.triggered.connect(slot)
        if shortcut:
            a.setShortcut(shortcut)
        a.setCheckable(checkable)
        self._actions[key] = a
        return a

    def _build_actions(self) -> None:
        mk = self._mk
        mk("act.new", self.new_file, "new", QKeySequence.New)
        mk("act.open", self.open_file, "open", QKeySequence.Open)
        mk("act.save", self.save_file, "save", QKeySequence.Save)
        mk("act.save_as", self.save_file_as, "save", QKeySequence.SaveAs)
        mk("act.close", self.close_file, "close", QKeySequence.Close)
        mk("act.properties", self.show_properties, "properties")
        mk("act.print", self.print_doc, "print", QKeySequence.Print)
        mk("act.exit", self.close, "close")

        mk("act.zoom_in", lambda: self._view_call("zoom_in"), "zoom_in", QKeySequence.ZoomIn)
        mk("act.zoom_out", lambda: self._view_call("zoom_out"), "zoom_out", QKeySequence.ZoomOut)
        mk("act.fit_width", lambda: self._view_call("fit_width"), "fit_width")
        mk("act.fit_page", lambda: self._view_call("fit_page"), "fit_page")
        mk("act.actual", lambda: self._view_call("actual_size"), "actual")
        mk("act.rotate_cw", lambda: self.do_rotate(False), "rotate_cw")
        mk("act.rotate_ccw", lambda: self.do_rotate(True), "rotate_ccw")
        mk("act.next", lambda: self._view_call("goto_page", (self._view_call("current_page") + 1)), "next")
        mk("act.prev", lambda: self._view_call("goto_page", (self._view_call("current_page") - 1)), "prev")

        mk("act.edit_text", lambda: self.set_tool("edittext"), "edittext")
        mk("act.insert_image", lambda: self.set_tool("insertimage"), "insertimage")
        mk("act.insert_text", lambda: self.set_tool("freetext"), "freetext")
        mk("act.find", self.focus_search, "search", QKeySequence.Find)
        mk("act.compare", self.do_compare, "compare")
        mk("act.undo", self.do_undo, "undo", QKeySequence.Undo)
        mk("act.redo", self.do_redo, "redo", QKeySequence.Redo)

        mk("annot.markup_color", self.pick_markup_color, "highlight")
        mk("annot.pen_color", self.pick_pen_color, "ink")
        mk("annot.list", self.list_annotations, "note")
        mk("annot.stamp_settings", self.do_stamp_settings, "stamp")

        mk("pages.insert", self.do_insert_pages, "open")
        mk("pages.delete", self.do_delete_page, "close")
        mk("pages.extract", self.do_extract_pages, "save")
        mk("pages.split", self.do_split, "convert")
        mk("pages.merge", self.do_merge, "merge")
        mk("pages.move_up", lambda: self.do_move(-1), "prev")
        mk("pages.move_down", lambda: self.do_move(1), "next")
        mk("pages.rotate_all", lambda: self.do_rotate(False, force_all=True), "rotate_cw")
        mk("pages.watermark", self.do_watermark, "note")
        mk("pages.header_footer", self.do_header_footer, "freetext")
        mk("pages.page_numbers", self.do_page_numbers, "actual")

        mk("convert.pdf_to_images", self.do_pdf_to_images, "insertimage")
        mk("convert.images_to_pdf", self.do_images_to_pdf, "convert")
        mk("convert.pdf_to_text", self.do_pdf_to_text, "freetext")
        mk("convert.pdf_to_html", self.do_pdf_to_html, "freetext")
        mk("convert.pdf_to_word", self.do_pdf_to_word, "freetext")
        mk("convert.pdf_to_pdfa", self.do_pdf_to_pdfa, "save")

        mk("menu.settings", lambda: None, "settings")
        mk("menu.language", lambda: None, "language")
        mk("lang.zh", lambda: self._change_language("zh"), "")
        mk("lang.en", lambda: self._change_language("en"), "")
        mk("about.title", self.show_about, "help")

        group = QActionGroup(self)
        group.setExclusive(True)
        for name in TOOL_NAMES:
            a = self._mk(f"tool.{name}", lambda _=False, n=name: self.set_tool(n),
                         name, checkable=True)
            group.addAction(a)
            self._tool_actions[name] = a
        self._tool_actions["select"].setChecked(True)

    def _build_menus(self) -> None:
        m = self.menuBar()
        self._menus["menu.file"] = m.addMenu("")
        mf = self._menus["menu.file"]
        for k in ("act.new", "act.open", "act.save", "act.save_as", "act.close"):
            mf.addAction(self._actions[k])
        mf.addSeparator(); mf.addAction(self._actions["act.properties"])
        mf.addSeparator(); mf.addAction(self._actions["act.print"])
        mf.addSeparator(); mf.addAction(self._actions["act.exit"])

        self._menus["menu.view"] = m.addMenu("")
        mv = self._menus["menu.view"]
        for k in ("act.zoom_in", "act.zoom_out", "act.fit_width", "act.fit_page",
                  "act.actual"):
            mv.addAction(self._actions[k])
        mv.addSeparator()
        mv.addAction(self._actions["act.rotate_cw"]); mv.addAction(self._actions["act.rotate_ccw"])
        mv.addSeparator()
        mv.addAction(self._actions["act.next"]); mv.addAction(self._actions["act.prev"])
        mv.addSeparator()
        self._dock_actions = [self.dock_left.toggleViewAction(),
                              self.dock_right.toggleViewAction()]
        for a in self._dock_actions:
            mv.addAction(a)

        self._menus["menu.edit"] = m.addMenu("")
        me = self._menus["menu.edit"]
        for k in ("act.edit_text", "act.insert_image", "act.insert_text"):
            me.addAction(self._actions[k])
        me.addSeparator(); me.addAction(self._actions["act.find"])

        self._menus["menu.annotate"] = m.addMenu("")
        ma = self._menus["menu.annotate"]
        for name in ("highlight", "underline", "strikeout"):
            ma.addAction(self._tool_actions[name])
        ma.addSeparator()
        for name in ("note", "freetext", "stamp"):
            ma.addAction(self._tool_actions[name])
        ma.addSeparator()
        for name in ("line", "arrow", "rect", "ellipse"):
            ma.addAction(self._tool_actions[name])
        ma.addSeparator()
        for k in ("annot.markup_color", "annot.pen_color", "annot.stamp_settings",
                  "annot.list"):
            ma.addAction(self._actions[k])

        self._menus["menu.pages"] = m.addMenu("")
        mp = self._menus["menu.pages"]
        for k in ("pages.insert", "pages.delete", "pages.extract", "pages.split",
                  "pages.merge", "pages.move_up", "pages.move_down"):
            mp.addAction(self._actions[k])
        mp.addSeparator(); mp.addAction(self._actions["pages.rotate_all"])
        mp.addSeparator()
        for k in ("pages.watermark", "pages.header_footer", "pages.page_numbers"):
            mp.addAction(self._actions[k])

        self._menus["menu.compare"] = m.addMenu("")
        self._menus["menu.compare"].addAction(self._actions["act.compare"])

        self._menus["menu.convert"] = m.addMenu("")
        mc = self._menus["menu.convert"]
        for k in ("convert.pdf_to_images", "convert.images_to_pdf"):
            mc.addAction(self._actions[k])

        self._menus["menu.settings"] = m.addMenu("")
        self._menus["menu.language"] = self._menus["menu.settings"].addMenu("")
        lang_group = QActionGroup(self); lang_group.setExclusive(True)
        for k in ("lang.zh", "lang.en"):
            self._actions[k].setCheckable(True)
            lang_group.addAction(self._actions[k])
            self._menus["menu.language"].addAction(self._actions[k])
        self._actions["lang.en" if language() == "en" else "lang.zh"].setChecked(True)

        self._menus["menu.help"] = m.addMenu("")
        self._menus["menu.help"].addAction(self._actions["about.title"])

        # Undo / Redo buttons to the right of the Help menu
        m.addSeparator()
        m.addAction(self._actions["act.undo"])
        m.addAction(self._actions["act.redo"])

    def _short(self, key: str) -> str:
        entry = SHORT_LABELS.get(key)
        if not entry:
            return self._actions[key].text()
        return entry[0] if language() == "zh" else entry[1]

    def _tb_button(self, key: str) -> QToolButton:
        btn = QToolButton()
        btn.setDefaultAction(self._actions[key])
        btn.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        btn.setText(self._short(key))
        self._tb_buttons.append((btn, key))
        return btn

    def _build_toolbars(self) -> None:
        self._tb_buttons = []
        tb = QToolBar("Main"); tb.setMovable(False)
        tb.setIconSize(QPixmap(24, 24).size())
        self.addToolBar(tb)
        for k in ("act.new", "act.open", "act.save"):
            tb.addWidget(self._tb_button(k))
        tb.addSeparator()
        for k in ("act.prev", "act.next", "act.zoom_out", "act.zoom_in",
                  "act.fit_width", "act.fit_page"):
            tb.addWidget(self._tb_button(k))
        tb.addSeparator()
        for name in TOOL_NAMES:
            tb.addWidget(self._tb_button(f"tool.{name}"))
        tb.addSeparator()
        for k in ("act.find", "act.compare"):
            tb.addWidget(self._tb_button(k))

    def _build_statusbar(self) -> None:
        self.page_label = QLabel()
        self.statusBar().addPermanentWidget(self.page_label)
        self.search_label = QLabel()
        self.statusBar().addPermanentWidget(self.search_label)

        self.zoom_label = QLabel(tr("zoom.label", p=100))
        self.zoom_label.setMinimumWidth(48)
        self.zoom_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(10, 800)
        self.zoom_slider.setValue(100)
        self.zoom_slider.setFixedWidth(160)
        self.zoom_slider.setToolTip("Zoom")
        self.zoom_slider.valueChanged.connect(self._on_zoom_slider)
        self.statusBar().addPermanentWidget(self.zoom_slider)
        self.statusBar().addPermanentWidget(self.zoom_label)

    def _on_zoom_slider(self, value: int) -> None:
        v = self._cur_view()
        if v is not None:
            v.set_zoom(value / 100.0)

    # -------------------------------------------------------------- i18n
    def retranslate(self) -> None:
        self.setWindowTitle(tr("app.title"))
        for key, a in self._actions.items():
            a.setText(tr(key))
            if key.startswith("tool."):
                a.setToolTip(tr(key))
        for btn, key in getattr(self, "_tb_buttons", []):
            btn.setText(self._short(key))
        for key, menu in self._menus.items():
            menu.setTitle(tr(key))
        self.dock_left.setWindowTitle(tr("dock.navigation"))
        self.dock_right.setWindowTitle(tr("dock.results"))
        if getattr(self, "_dock_actions", None):
            self._dock_actions[0].setText(tr("dock.navigation"))
            self._dock_actions[1].setText(tr("dock.results"))
        self.left.setTabText(0, tr("tab.thumbnails"))
        self.left.setTabText(1, tr("tab.outline"))
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, DocumentTab):
                self.tabs.setTabText(i, w.title())
        self._sync_current_if_doc()

    def _sync_current_if_doc(self) -> None:
        tab = self._cur_tab()
        if tab:
            self._on_page_changed(tab.view.current_page(), tab)
        else:
            self.page_label.setText(tr("status.no_doc"))

    def _change_language(self, code: str) -> None:
        set_language(code)
        app = QApplication.instance()
        if app is not None:
            from .translations import apply_qt_translations
            apply_qt_translations(app, code)
        self.retranslate()

    def show_about(self) -> None:
        AboutDialog(self).exec()

    # ------------------------------------------------------------------ state
    def _set_enabled(self, enabled: bool) -> None:
        for k in ("act.save", "act.save_as", "act.close", "act.properties", "act.print",
                  "act.zoom_in", "act.zoom_out", "act.fit_width", "act.fit_page",
                  "act.actual", "act.rotate_cw", "act.rotate_ccw", "act.next",
                  "act.prev", "act.edit_text", "act.insert_image", "act.insert_text",
                  "act.find", "act.compare"):
            self._actions[k].setEnabled(enabled)
        self.zoom_slider.setEnabled(enabled)

    def _update_title(self) -> None:
        tab = self._cur_tab()
        if tab:
            name = os.path.basename(tab.doc.path) if tab.doc.path else tr("tab.untitled")
            star = "*" if tab.doc.dirty else ""
            self.setWindowTitle(f"{tr('app.title')} — {star}{name}")
            idx = self.tabs.currentIndex()
            self.tabs.setTabText(idx, f"{star}{tab.title()}")
        else:
            self.setWindowTitle(tr("app.title"))

    def _on_page_changed(self, page: int, tab: DocumentTab) -> None:
        if tab is not self._cur_tab():
            return
        self.left.thumbnails.highlight_page(page)
        self.page_label.setText(tr("status.page", n=page + 1, total=tab.doc.page_count))

    def _on_zoom_changed(self, zoom: float, tab: DocumentTab) -> None:
        if tab is self._cur_tab():
            pct = int(round(zoom * 100))
            self.zoom_label.setText(tr("zoom.label", p=pct))
            self.zoom_slider.blockSignals(True)
            self.zoom_slider.setValue(max(10, min(800, pct)))
            self.zoom_slider.blockSignals(False)
            self.statusBar().showMessage(tr("status.zoom", p=f"{pct}"), 1500)

    def _on_status(self, msg: str, tab: DocumentTab) -> None:
        if tab is self._cur_tab():
            self.statusBar().showMessage(msg, 4000)

    def _view_call(self, method: str, *args):
        v = self._cur_view()
        if v is None:
            return 0
        fn = getattr(v, method)
        return fn(*args)

    def _goto_page(self, page: int) -> None:
        v = self._cur_view()
        if v:
            v.goto_page(page)

    # ------------------------------------------------------------ undo / redo
    def do_undo(self) -> None:
        tab = self._cur_tab()
        if tab and tab.undo():
            self._refresh_tab(tab)
        self._update_undo_redo()

    def do_redo(self) -> None:
        tab = self._cur_tab()
        if tab and tab.redo():
            self._refresh_tab(tab)
        self._update_undo_redo()

    def _update_undo_redo(self) -> None:
        tab = self._cur_tab()
        self._actions["act.undo"].setEnabled(bool(tab and tab.can_undo()))
        self._actions["act.redo"].setEnabled(bool(tab and tab.can_redo()))

    # ------------------------------------------------------------------- file
    def open_file(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, tr("act.open"), "",
                                                "PDF (*.pdf);;All (*)")
        for p in paths:
            self._load(p)

    def _load(self, path: str) -> bool:
        if path in [self.tabs.widget(i).doc.path for i in range(self.tabs.count())
                    if isinstance(self.tabs.widget(i), DocumentTab)]:
            return False
        doc = PdfDocument()
        password = None
        for _ in range(3):
            try:
                doc.open(path, password)
                break
            except PdfError as exc:
                if "Password" not in str(exc):
                    QMessageBox.critical(self, tr("msg.failed"), str(exc)); return False
                password, ok = QInputDialog.getText(self, "Password", "Enter password:",
                                                    QLineEdit.Password)
                if not ok:
                    return False
        else:
            return False
        self._add_tab(doc)
        return True

    def new_file(self) -> None:
        doc = PdfDocument()
        doc.create_blank()
        self._add_tab(doc)

    def _save_tab_doc(self, tab: DocumentTab, path: Optional[str] = None,
                      force_prompt: bool = False) -> bool:
        target = None if force_prompt else (path or tab.doc.path)
        if not target:
            target, _ = QFileDialog.getSaveFileName(self, tr("act.save_as"),
                                                    tab.doc.path or "output.pdf", "PDF (*.pdf)")
            if not target:
                return False
        try:
            tab.doc.save(target)
        except PdfError as exc:
            QMessageBox.critical(self, tr("msg.failed"), str(exc)); return False
        self._update_title()
        self.statusBar().showMessage(tr("status.saved_to", p=target), 3000)
        return True

    def save_file(self) -> None:
        tab = self._cur_tab()
        if tab:
            self._save_tab_doc(tab)

    def save_file_as(self) -> None:
        tab = self._cur_tab()
        if tab:
            self._save_tab_doc(tab, force_prompt=True)

    def close_file(self) -> None:
        idx = self.tabs.currentIndex()
        if idx >= 0:
            self._close_tab(idx)

    def closeEvent(self, event) -> None:
        for i in range(self.tabs.count()):
            w = self.tabs.widget(i)
            if isinstance(w, DocumentTab) and w.doc.dirty:
                self.tabs.setCurrentIndex(i)
                resp = QMessageBox.question(
                    self, tr("msg.unsaved.title"), tr("msg.unsaved.body", name=w.title()),
                    QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel)
                if resp == QMessageBox.Cancel:
                    event.ignore()
                    return
                if resp == QMessageBox.Save and not self._save_tab_doc(w):
                    event.ignore()
                    return
        event.accept()

    def show_properties(self) -> None:
        tab = self._require_tab()
        if not tab:
            return
        dlg = PropertiesDialog(tab.doc.metadata(), tab.doc.page_count, self)
        if dlg.exec():
            tab.doc.set_metadata(dlg.values())
            self._update_title()

    # ------------------------------------------------------------------ print
    def print_doc(self) -> None:
        tab = self._require_tab()
        if not tab:
            return
        PrintDialog(tab.doc, tab.view.current_page(), self).exec()

    # ----------------------------------------------------------------- search
    def focus_search(self) -> None:
        tab = self._require_tab()
        if not tab:
            return
        text, ok = QInputDialog.getText(self, tr("act.find"), tr("act.find"))
        if not ok or not text:
            return
        self._search_hits = tab.doc.search(text)
        self.results.clear()
        for pno, rect in self._search_hits:
            page_txt = tab.doc.page(pno).get_text("text", clip=rect).strip()
            self.results.addItem(f"p{pno + 1}: {page_txt[:60]}")
        self.search_label.setText(tr("status.hits", n=len(self._search_hits)))
        if self._search_hits:
            self._result_activated(0)

    def _result_activated(self, row: int) -> None:
        v = self._cur_view()
        if v and 0 <= row < len(self._search_hits):
            v.goto_page(self._search_hits[row][0])

    # -------------------------------------------------------------- tools/mode
    def set_tool(self, name: str) -> None:
        v = self._cur_view()
        if v:
            v.tool = name
            v.apply_cursor()
        if name in self._tool_actions:
            self._tool_actions[name].setChecked(True)
        self.statusBar().showMessage(tr("status.tool", t=tr(f"tool.{name}")), 3000)

    def pick_markup_color(self) -> None:
        v = self._cur_view()
        if not v:
            return
        dlg = MarkupStyleDialog(v.span_color, v.markup_opacity, self)
        if dlg.exec():
            color, opacity = dlg.values()
            v.span_color = color
            v.markup_opacity = opacity

    def pick_pen_color(self) -> None:
        v = self._cur_view()
        c = QColorDialog.getColor()
        if v and c.isValid():
            v.pen_color = (c.redF(), c.greenF(), c.blueF())

    def list_annotations(self) -> None:
        tab = self._require_tab()
        if not tab:
            return
        page = tab.view.current_page()
        self.results.clear()
        for a in annot.list_annotations(tab.doc, page):
            self.results.addItem(f"[{a['type']}] {a['content'][:60]}")

    def do_stamp_settings(self) -> None:
        dlg = StampSettingsDialog(self)
        if dlg.exec():
            stamps.save_config(dlg.config())
            self.set_tool("stamp")

    def _on_stamp_requested(self, tab: DocumentTab, index: int, dp) -> None:
        if tab is not self._cur_tab():
            return
        try:
            res = stamps.render_stamp(stamps.load_config())
        except Exception:  # noqa: BLE001
            res = None
        if not res:
            self.do_stamp_settings()
            return
        png, w, h = res
        pt = tab.view.page_to_pdf_point(index, dp)
        rect = fitz.Rect(pt.x, pt.y, pt.x + w, pt.y + h)
        tab.push_undo()
        try:
            annot.insert_stamp_image(tab.doc, index, rect, png)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, tr("msg.failed"), str(exc)); return
        tab.view.invalidate_page(index)
        self.left.thumbnails.refresh_page(tab.doc, index)
        self._update_title()
        self._update_undo_redo()

    # --------------------------------------------------------------- editing
    def _on_span_picked(self, span, tab: DocumentTab) -> None:
        if tab is not self._cur_tab():
            return
        dlg = TextEditDialog(tr("dlg.edit.title"), span.text, None, int(span.size),
                             allow_original=True, parent=self)
        if not dlg.exec():
            return
        fv = dlg.font_name()
        ffile = fv if fonts_mod.is_font_file(fv) else None
        fname = None if ffile else fv
        if (dlg.text() != span.text or fv is not None
                or int(dlg.font_size()) != int(span.size)):
            tab.push_undo()
        try:
            replace_span(tab.doc, span, dlg.text(), fontname=fname, fontfile=ffile,
                         fontsize=dlg.font_size())
        except PdfError as exc:
            QMessageBox.critical(self, tr("msg.failed"), str(exc)); return
        tab.view.invalidate_page(span.page)
        tab.view.spans_cache.pop(span.page, None)
        self._refresh_tab(tab)

    def _on_point_picked(self, tab: DocumentTab, index: int, dp) -> None:
        if tab is not self._cur_tab():
            return
        path, _ = QFileDialog.getOpenFileName(self, tr("act.insert_image"), "",
                                              "Images (*.png *.jpg *.jpeg *.bmp *.tif)")
        if not path:
            return
        from PIL import Image
        w, h = Image.open(path).size
        rect = QRectF(dp.x(), dp.y(), 200.0, 200.0 * h / max(1, w))
        tab.push_undo()
        try:
            insert_image(tab.doc, index, tab.view.page_to_pdf_rect(index, rect), path)
        except PdfError as exc:
            QMessageBox.critical(self, tr("msg.failed"), str(exc)); return
        tab.view.invalidate_page(index)
        self.left.thumbnails.refresh_page(tab.doc, index) if tab is self._cur_tab() else None

    def _on_rect_picked(self, tab: DocumentTab, index: int, rect: QRectF, tool: str) -> None:
        if tab is not self._cur_tab():
            return
        dlg = TextEditDialog(tr("dlg.textbox.title"), "", "helv",
                             tab.view.freetext_size, parent=self)
        if not dlg.exec():
            return
        text = dlg.text()
        if not text.strip():
            return
        tl = tab.view.page_to_pdf_rect(index, rect)
        fv = dlg.font_name()
        ffile = fv if fonts_mod.is_font_file(fv) else None
        fname = fv if not ffile else "helv"
        w, h = text_size(text, fname or "helv", dlg.font_size(), ffile)
        pdf_rect = fitz.Rect(tl.x0, tl.y0, tl.x0 + w + 6, tl.y0 + h + 4)
        tab.push_undo()
        try:
            annot.add_freetext(tab.doc, index, pdf_rect, text, fontsize=dlg.font_size(),
                               fontname=(fname or "helv"), fontfile=ffile, fill=None)
        except PdfError as exc:
            QMessageBox.critical(self, tr("msg.failed"), str(exc)); return
        tab.view.invalidate_page(index)
        self.left.thumbnails.refresh_page(tab.doc, index)
        self.set_tool("select")

    def _on_note_requested(self, tab: DocumentTab, index: int, dp) -> None:
        if tab is not self._cur_tab():
            return
        text, ok = QInputDialog.getMultiLineText(self, tr("tool.note"), "", "")
        if not ok or not text.strip():
            return
        pt = tab.view.page_to_pdf_point(index, dp)
        tab.push_undo()
        try:
            annot.add_note(tab.doc, index, pt, text, tab.view.span_color)
        except PdfError as exc:
            QMessageBox.critical(self, tr("msg.failed"), str(exc)); return
        tab.view.invalidate_page(index)
        self.left.thumbnails.refresh_page(tab.doc, index)
        self._update_title()
        self._update_undo_redo()
        self.set_tool("select")

    def _on_annot_activated(self, tab: DocumentTab, index: int, xref: int) -> None:
        if tab is not self._cur_tab():
            return
        info = annot.annot_info(tab.doc, index, xref)
        if info.get("type") != "Text":
            return
        self.results.clear()
        self.results.addItem(f"[{tr('tool.note')}] {info.get('content', '')}")
        self.dock_right.show()
        self.dock_right.raise_()

    def _on_annot_edit(self, tab: DocumentTab, index: int, xref: int) -> None:
        if tab is not self._cur_tab():
            return
        info = annot.annot_info(tab.doc, index, xref)
        if info.get("type") == "Text":
            text, ok = QInputDialog.getMultiLineText(self, tr("tool.note"), "",
                                                     info.get("content", ""))
            if not ok:
                return
            tab.push_undo()
            annot.set_annot_content(tab.doc, index, xref, text)
            tab.view.invalidate_page(index)
            self.left.thumbnails.refresh_page(tab.doc, index)
            self._update_title()
            self._update_undo_redo()
            return
        if info.get("type") not in ("FreeText",):
            return
        rc = annot.annot_rect_content(tab.doc, index, xref)
        rect0 = rc[0] if rc else None
        content = rc[1] if rc else ""
        dlg = TextEditDialog(tr("dlg.textbox.title"), content, "helv", 12, parent=self)
        if not dlg.exec():
            return
        text = dlg.text()
        fv = dlg.font_name()
        ffile = fv if fonts_mod.is_font_file(fv) else None
        fname = fv if not ffile else "helv"
        w, h = text_size(text, fname or "helv", dlg.font_size(), ffile)
        x0 = rect0.x0 if rect0 else 72.0
        y0 = rect0.y0 if rect0 else 72.0
        new_rect = fitz.Rect(x0, y0, x0 + w + 6, y0 + h + 4)
        tab.push_undo()
        try:
            annot.delete_annot(tab.doc, index, xref)
            annot.add_freetext(tab.doc, index, new_rect, text, fontsize=dlg.font_size(),
                               fontname=(fname or "helv"), fontfile=ffile, fill=None)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, tr("msg.failed"), str(exc)); return
        tab.view.invalidate_page(index)
        self.left.thumbnails.refresh_page(tab.doc, index)
        self._update_title()
        self._update_undo_redo()

    # ------------------------------------------------------------------ pages
    def _require_tab(self) -> Optional[DocumentTab]:
        tab = self._cur_tab()
        if not tab:
            QMessageBox.information(self, tr("msg.no_doc.title"), tr("msg.no_doc.body"))
        return tab

    def _refresh_tab(self, tab: DocumentTab) -> None:
        page = tab.view.current_page()
        tab.view.spans_cache.clear()
        tab.view.set_document(tab.doc)
        if tab is self._cur_tab():
            self.left.thumbnails.set_document(tab.doc)
            self.left.outline.set_document(tab.doc)
            tab.view.goto_page(min(page, tab.doc.page_count - 1))
            self._on_page_changed(tab.view.current_page(), tab)
        self._update_title()
        self._update_undo_redo()

    def do_rotate(self, default_ccw: bool = False, force_all: bool = False) -> None:
        tab = self._require_tab()
        if not tab:
            return
        dlg = RotateDialog(tab.doc.page_count, tab.view.current_page(), default_ccw, self)
        if force_all:
            dlg.scope.setCurrentIndex(1)
            dlg._sync()
        if not dlg.exec():
            return
        deg = dlg.degrees()
        tab.push_undo()
        if dlg.scope_value() == "all":
            ops.rotate_all(tab.doc, deg)
        elif dlg.scope_value() == "current":
            ops.rotate_pages(tab.doc, [tab.view.current_page()], deg)
        else:
            idxs = self._parse_pages(dlg.pages_text())
            if not idxs:
                QMessageBox.warning(self, tr("msg.failed"), tr("msg.invalid_pages")); return
            ops.rotate_pages(tab.doc, idxs, deg)
        self._refresh_tab(tab)

    def do_delete_page(self) -> None:
        tab = self._require_tab()
        if not tab:
            return
        if QMessageBox.question(self, tr("pages.delete"),
                                f"{tr('pages.delete')}?") != QMessageBox.Yes:
            return
        tab.push_undo()
        try:
            ops.delete_pages(tab.doc, [tab.view.current_page()])
        except PdfError as exc:
            QMessageBox.critical(self, tr("msg.failed"), str(exc)); return
        self._refresh_tab(tab)

    def do_move(self, delta: int) -> None:
        tab = self._require_tab()
        if not tab:
            return
        src = tab.view.current_page()
        dst = src + delta
        if not (0 <= dst < tab.doc.page_count):
            return
        tab.push_undo()
        ops.move_page(tab.doc, src, dst)
        self._refresh_tab(tab)
        tab.view.goto_page(dst)

    def do_insert_pages(self) -> None:
        tab = self._require_tab()
        if not tab:
            return
        dlg = InsertPagesDialog(tab.view.current_page(), tab.doc.page_count, self)
        if not dlg.exec():
            return
        src = dlg.source_path()
        if not src or not os.path.isfile(src):
            QMessageBox.warning(self, tr("msg.failed"), tr("msg.choose_source")); return
        pages = None
        if not dlg.use_all():
            pages = self._parse_pages(dlg.pages_text())
            if not pages:
                QMessageBox.warning(self, tr("msg.failed"), tr("msg.invalid_pages")); return
        tab.push_undo()
        try:
            ops.insert_pages_from(tab.doc, src, dlg.after_page(), pages)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, tr("msg.failed"), str(exc)); return
        self._refresh_tab(tab)

    def do_extract_pages(self) -> None:
        tab = self._require_tab()
        if not tab:
            return
        text, ok = QInputDialog.getText(self, tr("pages.extract"), "1-3,5")
        if not ok or not text:
            return
        indices = self._parse_pages(text)
        if not indices:
            QMessageBox.warning(self, tr("msg.failed"), tr("msg.invalid_pages")); return
        path, _ = QFileDialog.getSaveFileName(self, tr("pages.extract"), "extracted.pdf",
                                              "PDF (*.pdf)")
        if not path:
            return
        try:
            ops.extract_pages(tab.doc, indices, path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, tr("msg.failed"), str(exc)); return
        QMessageBox.information(self, tr("msg.done"), path)

    def do_split(self) -> None:
        tab = self._require_tab()
        if not tab:
            return
        dlg = SplitDialog(tab.doc.page_count, self)
        if not dlg.exec():
            return
        out_dir = QFileDialog.getExistingDirectory(self, tr("pages.split"))
        if not out_dir:
            return
        try:
            if dlg.use_ranges():
                pairs = self._parse_ranges(dlg.ranges_text(), tab.doc.page_count)
                if not pairs:
                    QMessageBox.warning(self, tr("msg.failed"), tr("msg.invalid_pages"))
                    return
                outs = ops.split(tab.doc, out_dir, ranges=pairs)
            else:
                outs = ops.split(tab.doc, out_dir, every_n=dlg.every_n_value())
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, tr("msg.failed"), str(exc)); return
        for p in outs:
            self._load(p)
        self.statusBar().showMessage(f"{len(outs)}", 4000)

    def do_merge(self) -> None:
        dlg = MergeDialog(self)
        if not dlg.exec():
            return
        paths = dlg.paths()
        if len(paths) < 2:
            QMessageBox.warning(self, tr("msg.failed"), tr("msg.need_two"))
            return
        path, _ = QFileDialog.getSaveFileName(self, tr("pages.merge"), "merged.pdf",
                                              "PDF (*.pdf)")
        if not path:
            return
        try:
            ops.merge(paths, path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, tr("msg.failed"), str(exc)); return
        self._load(path)

    def do_watermark(self) -> None:
        tab = self._require_tab()
        if not tab:
            return
        dlg = WatermarkDialog(self)
        if not dlg.exec():
            return
        tab.push_undo()
        ops.add_watermark(tab.doc, dlg.text.text(), fontsize=dlg.size.value(),
                          color=dlg.color, opacity=dlg.opacity.value(), angle=dlg.angle.value())
        self._refresh_tab(tab)

    def do_header_footer(self) -> None:
        tab = self._require_tab()
        if not tab:
            return
        dlg = HeaderFooterDialog(self)
        if not dlg.exec():
            return
        tab.push_undo()
        ops.add_header_footer(tab.doc, dlg.header.text(), dlg.footer.text(),
                              fontsize=dlg.size.value())
        self._refresh_tab(tab)

    def do_page_numbers(self) -> None:
        tab = self._require_tab()
        if not tab:
            return
        dlg = PageNumbersDialog(self)
        if not dlg.exec():
            return
        tab.push_undo()
        ops.add_page_numbers(tab.doc, template=dlg.template.text(), start=dlg.start.value(),
                             prefix=dlg.prefix.text(), position=dlg.position_value())
        self._refresh_tab(tab)

    @staticmethod
    def _parse_pages(text: str) -> List[int]:
        out: List[int] = []
        for part in text.replace(" ", "").split(","):
            if not part:
                continue
            if "-" in part:
                a, b = part.split("-", 1)
                if a.isdigit() and b.isdigit():
                    out.extend(range(int(a) - 1, int(b)))
            elif part.isdigit():
                out.append(int(part) - 1)
        return sorted(set(i for i in out if i >= 0))

    @staticmethod
    def _parse_ranges(text: str, page_count: int) -> List[tuple]:
        pairs: List[tuple] = []
        for part in text.replace(" ", "").split(","):
            if not part:
                continue
            if "-" in part:
                a, b = part.split("-", 1)
                if a.isdigit() and b.isdigit():
                    lo, hi = int(a) - 1, int(b) - 1
                    if lo > hi:
                        lo, hi = hi, lo
                    lo = max(0, lo); hi = min(page_count - 1, hi)
                    if lo <= hi:
                        pairs.append((lo, hi))
            elif part.isdigit():
                i = int(part) - 1
                if 0 <= i < page_count:
                    pairs.append((i, i))
        return pairs

    # ---------------------------------------------------------------- compare
    def do_compare(self) -> None:
        tab = self._require_tab()
        if not tab:
            return
        if not tab.doc.path:
            QMessageBox.information(self, tr("msg.save_first.title"),
                                    tr("msg.save_first.body")); return
        other, _ = QFileDialog.getOpenFileName(self, tr("act.compare"), "", "PDF (*.pdf)")
        if not other:
            return
        self.statusBar().showMessage(tr("status.comparing"), 0)
        try:
            result = cmp.compare_pdfs(tab.doc.path, other)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, tr("msg.failed"), str(exc)); return
        self.statusBar().clearMessage()
        CompareWindow(result, self).exec()

    # ---------------------------------------------------------------- convert
    def do_pdf_to_images(self) -> None:
        tab = self._require_tab()
        if not tab:
            return
        out_dir = QFileDialog.getExistingDirectory(self, tr("convert.pdf_to_images"))
        if not out_dir:
            return
        fmt, ok = QInputDialog.getItem(self, tr("convert.pdf_to_images"), "Format",
                                       ["png", "jpg", "tiff"], 0, False)
        if not ok:
            return
        try:
            outs = conv.pdf_to_images(tab.doc, out_dir, fmt=fmt)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, tr("msg.failed"), str(exc)); return
        QMessageBox.information(self, tr("msg.done"), f"{len(outs)}")

    def do_images_to_pdf(self) -> None:
        dlg = ImagesToPdfDialog(self)
        if not dlg.exec():
            return
        paths = dlg.paths()
        if not paths:
            return
        path, _ = QFileDialog.getSaveFileName(self, tr("convert.images_to_pdf"),
                                              "images.pdf", "PDF (*.pdf)")
        if not path:
            return
        try:
            conv.images_to_pdf(paths, path, page_size=dlg.page_size_pts(),
                               fit=dlg.fit_mode())
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, tr("msg.failed"), str(exc)); return
        self._load(path)

    def _save_text(self, fn) -> None:
        tab = self._require_tab()
        if not tab:
            return
        path, _ = QFileDialog.getSaveFileName(self, tr("act.save_as"), "", "All (*)")
        if not path:
            return
        try:
            fn(tab.doc, path)
        except PdfError as exc:
            QMessageBox.critical(self, tr("msg.failed"), str(exc)); return
        QMessageBox.information(self, tr("msg.done"), path)

    def do_pdf_to_text(self) -> None:
        self._save_text(conv.pdf_to_text)

    def do_pdf_to_html(self) -> None:
        self._save_text(conv.pdf_to_html)

    def do_pdf_to_word(self) -> None:
        self._save_text(conv.pdf_to_docx)

    def do_pdf_to_pdfa(self) -> None:
        self._save_text(conv.pdf_to_pdfa)

    def _ask_lang(self) -> Optional[str]:
        langs = ocr.available_languages() or ["eng"]
        if "eng" not in langs:
            langs = ["eng"] + langs
        lang, ok = QInputDialog.getItem(self, "OCR", "Language", langs, 0, False)
        return lang if ok else None

    def do_ocr_searchable(self) -> None:
        tab = self._require_tab()
        if not tab:
            return
        lang = self._ask_lang()
        if not lang:
            return
        path, _ = QFileDialog.getSaveFileName(self, tr("convert.ocr_searchable"),
                                              "searchable.pdf", "PDF (*.pdf)")
        if not path:
            return
        self.statusBar().showMessage(tr("status.ocr_running"), 0)
        try:
            ocr.make_searchable_pdf(tab.doc, path, lang=lang)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, tr("msg.failed"), str(exc)); return
        self.statusBar().clearMessage()
        QMessageBox.information(self, tr("msg.done"), path)

    def do_ocr_text(self) -> None:
        tab = self._require_tab()
        if not tab:
            return
        lang = self._ask_lang()
        if not lang:
            return
        page = tab.view.current_page()
        try:
            text = ocr.ocr_text(tab.doc, page, lang=lang)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, tr("msg.failed"), str(exc)); return
        dlg = QInputDialog(self)
        dlg.setWindowTitle(f"OCR {page + 1}")
        dlg.setLabelText(tr("convert.ocr_text"))
        dlg.setInputMode(QInputDialog.TextInput)
        dlg.resize(600, 400)
        dlg.setTextValue(text)
        dlg.exec()
