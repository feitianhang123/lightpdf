"""About dialog with donation QR codes."""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QHBoxLayout, QLabel,
                               QVBoxLayout, QWidget)

from ..i18n import tr
from ..paths import resource_path


class AboutDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("about.title"))
        self.setMinimumWidth(460)

        text = QLabel(tr("about.body"))
        text.setWordWrap(True)
        text.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        layout = QVBoxLayout(self)
        layout.addWidget(text)

        qr_row = QHBoxLayout()
        qr_row.addStretch()
        for caption, fname in ((tr("about.wechat"), "resources/donate_wechat.jpg"),
                               (tr("about.alipay"), "resources/donate_alipay.png")):
            qr_row.addWidget(self._qr_block(caption, fname))
        qr_row.addStretch()
        layout.addLayout(qr_row)

        bb = QDialogButtonBox(QDialogButtonBox.Ok)
        bb.accepted.connect(self.accept)
        layout.addWidget(bb)

    def _qr_block(self, caption: str, rel: str) -> QWidget:
        box = QWidget()
        v = QVBoxLayout(box)
        v.setContentsMargins(6, 6, 6, 6)
        img = QLabel()
        img.setAlignment(Qt.AlignCenter)
        img.setFixedSize(190, 190)
        img.setStyleSheet("border:1px solid #4E7D57;background:#ffffff;")
        path = resource_path(*rel.split("/"))
        if path:
            pix = QPixmap(path)
            if not pix.isNull():
                img.setPixmap(pix.scaled(184, 184, Qt.KeepAspectRatio,
                                         Qt.SmoothTransformation))
        cap = QLabel(caption)
        cap.setAlignment(Qt.AlignCenter)
        v.addWidget(img)
        v.addWidget(cap)
        return box
