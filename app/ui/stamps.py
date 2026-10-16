"""Render user-defined stamps (text or image) to PNG for page insertion."""
from __future__ import annotations

import json
from typing import Optional, Tuple

from PySide6.QtCore import QBuffer, QRectF, QSettings, Qt
from PySide6.QtGui import (QBrush, QColor, QFont, QFontDatabase, QFontMetrics,
                           QImage, QPainter, QPen)
from PySide6.QtWidgets import QApplication  # noqa: F401  (ensures GUI context)

SS = 3  # supersampling factor for crisp output

DEFAULT_CONFIG = {
    "mode": "text",
    "text": "APPROVED",
    "font": "Arial",
    "size": 24,
    "text_color": "#C00000",
    "shape": "round",          # rect | round | ellipse | none
    "border_color": "#C00000",
    "border_width": 3,
    "fill": "#FFFFFF",
    "transparent": True,
    "padding": 10,
    "image": "",
    "image_width": 160,
}

_SETTINGS = QSettings("MiniPDF", "MiniPDFEditor")


def load_config() -> dict:
    cfg = dict(DEFAULT_CONFIG)
    raw = _SETTINGS.value("stamp/config", "")
    if raw:
        try:
            cfg.update(json.loads(raw))
        except Exception:  # noqa: BLE001
            pass
    return cfg


def save_config(cfg: dict) -> None:
    _SETTINGS.setValue("stamp/config", json.dumps(cfg, ensure_ascii=False))


def _qfont(cfg: dict) -> QFont:
    name = cfg.get("font") or "Arial"
    fam = {"helv": "Arial", "tiro": "Times New Roman", "cour": "Courier New",
           "china-s": "Microsoft YaHei"}.get(name)
    if fam is None:
        if isinstance(name, str) and name.lower().endswith((".ttf", ".otf", ".ttc")):
            fid = QFontDatabase.addApplicationFont(name)
            fams = QFontDatabase.applicationFontFamilies(fid) if fid >= 0 else []
            fam = fams[0] if fams else "Arial"
        else:
            fam = name
    f = QFont(fam)
    f.setPointSizeF(float(cfg.get("size", 24)))
    return f


def _png(img: QImage) -> bytes:
    buf = QBuffer()
    buf.open(QBuffer.WriteOnly)
    img.save(buf, "PNG")
    return bytes(buf.data())


def render_text_stamp(cfg: dict) -> Tuple[bytes, float, float]:
    text = cfg.get("text", "") or ""
    font = _qfont(cfg)
    fm = QFontMetrics(font)
    lines = text.split("\n") or [""]
    tw = max((fm.horizontalAdvance(l) for l in lines), default=10)
    th = fm.height() * len(lines)
    pad = float(cfg.get("padding", 10))
    bw = float(cfg.get("border_width", 3))
    w = tw + 2 * pad + bw
    h = th + 2 * pad + bw
    img = QImage(max(1, int(w * SS)), max(1, int(h * SS)), QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.scale(SS, SS)
    shape = cfg.get("shape", "round")
    fill = None if cfg.get("transparent") else QColor(cfg.get("fill", "#FFFFFF"))
    pen = QPen(QColor(cfg.get("border_color", "#C00000")))
    pen.setWidthF(max(0.0, bw))
    rect = QRectF(bw / 2, bw / 2, w - bw, h - bw)
    if shape != "none":
        if fill is not None:
            p.setBrush(QBrush(fill))
        p.setPen(pen)
        if shape == "ellipse":
            p.drawEllipse(rect)
        elif shape == "round":
            rad = min(rect.width(), rect.height()) * 0.2
            p.drawRoundedRect(rect, rad, rad)
        else:
            p.drawRect(rect)
    p.setPen(QPen(QColor(cfg.get("text_color", "#C00000"))))
    p.setFont(font)
    y = bw / 2 + pad
    for line in lines:
        p.drawText(QRectF(bw / 2 + pad, y, tw, fm.height()), Qt.AlignCenter, line)
        y += fm.height()
    p.end()
    return _png(img), w, h


def render_image_stamp(cfg: dict) -> Optional[Tuple[bytes, float, float]]:
    path = cfg.get("image", "")
    if not path:
        return None
    src = QImage(path)
    if src.isNull():
        return None
    target_w = float(cfg.get("image_width", 160))
    target_h = target_w * src.height() / max(1, src.width())
    img = QImage(max(1, int(target_w * SS)), max(1, int(target_h * SS)),
                 QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.SmoothPixmapTransform, True)
    p.drawImage(QRectF(0, 0, img.width(), img.height()), src)
    p.end()
    return _png(img), target_w, target_h


def render_stamp(cfg: dict) -> Optional[Tuple[bytes, float, float]]:
    if cfg.get("mode") == "image":
        return render_image_stamp(cfg)
    return render_text_stamp(cfg)
