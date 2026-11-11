"""Render user-defined stamps (text or image) to PNG for page insertion.

Also provides vertical slicing for 骑缝章 (riding / perforation stamps).
"""
from __future__ import annotations

import json
import os
from typing import List, Optional, Tuple

from PySide6.QtCore import (QBuffer, QFile, QIODevice, QRectF, QSettings,
                            QStandardPaths, Qt)
from PySide6.QtGui import (QBrush, QColor, QFont, QFontDatabase, QFontMetrics,
                           QImage, QImageReader, QPainter, QPen)
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


class StampImageError(ValueError):
    """Raised when an image stamp cannot be loaded/rendered (message is user facing)."""


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
    _SETTINGS.sync()


# --------------------------------------------------------------- image files
def stamps_dir() -> str:
    """Private folder holding copies of user picked stamp images.

    Uses a fixed organisation path instead of ``AppDataLocation`` (which
    resolves to a different folder when running from source vs. the frozen
    executable, and would break saved paths after packaging).
    """
    base = QStandardPaths.writableLocation(QStandardPaths.GenericDataLocation)
    path = os.path.join(base, "MiniPDF", "MiniPDFEditor", "stamps")
    try:
        os.makedirs(path, exist_ok=True)
    except OSError:
        path = os.path.join(os.environ.get("TEMP", "."), "lightpdf-stamps")
        os.makedirs(path, exist_ok=True)
    return path


def load_source_image(path: str) -> QImage:
    """Load an image robustly (Unicode paths, EXIF rotation, odd extensions).

    ``QImage(path)`` is unreliable for non-ASCII paths on some Qt builds, so the
    bytes are handed to ``QImageReader`` through a ``QFile`` instead.
    """
    if not path or not os.path.isfile(path):
        raise StampImageError("图片文件不存在，请重新选择图章图片。")
    f = QFile(path)
    if not f.open(QIODevice.ReadOnly):
        raise StampImageError("图片文件无法读取，请检查文件权限。")
    try:
        reader = QImageReader(f)
        reader.setAutoTransform(True)
        img = reader.read()
        if img.isNull():
            raise StampImageError("不支持或已损坏的图片格式：%s" % reader.errorString())
        return img.convertToFormat(QImage.Format_ARGB32)
    finally:
        f.close()


def import_image(path: str) -> str:
    """Copy a picked image into the private stamps folder.

    The saved configuration then never depends on a file on the user's Desktop
    that may later be moved, renamed or deleted.
    """
    img = load_source_image(path)
    base = os.path.splitext(os.path.basename(path))[0] or "stamp"
    safe = "".join(c if c.isalnum() or c in "-_（）()" else "_" for c in base)[:60]
    folder = stamps_dir()
    dest = os.path.join(folder, safe + ".png")
    i = 1
    while os.path.exists(dest) and os.path.abspath(dest) != os.path.abspath(path):
        dest = os.path.join(folder, "%s_%d.png" % (safe, i))
        i += 1
    if not img.save(dest, "PNG"):
        raise StampImageError("无法保存图章图片副本。")
    return dest


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


def render_image_stamp(cfg: dict) -> Tuple[bytes, float, float]:
    path = cfg.get("image", "")
    if not path:
        raise StampImageError("还没有选择图章图片，请点「选择图片...」。")
    src = load_source_image(path)
    target_w = max(20.0, float(cfg.get("image_width", 160)))
    target_h = target_w * src.height() / max(1, src.width())
    img = QImage(max(1, int(target_w * SS)), max(1, int(target_h * SS)),
                 QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHint(QPainter.Antialiasing, True)
    p.setRenderHint(QPainter.SmoothPixmapTransform, True)
    p.scale(SS, SS)
    p.drawImage(QRectF(0, 0, target_w, target_h), src)
    p.end()
    return _png(img), target_w, target_h


def render_stamp(cfg: dict) -> Tuple[bytes, float, float]:
    """Return ``(png_bytes, width_pt, height_pt)`` or raise ``StampImageError``."""
    if cfg.get("mode") == "image":
        return render_image_stamp(cfg)
    return render_text_stamp(cfg)


def render_stamp_slices(cfg: dict, count: int, overlap: float = 0.0,
                        target_width: Optional[float] = None
                        ) -> List[Tuple[bytes, float, float]]:
    """Cut one stamp into ``count`` vertical slices for a riding stamp.

    ``overlap`` (0..0.4) widens every slice slightly so that binding/cutting
    does not break the seal.  ``target_width`` rescales the whole stamp first,
    which makes the dialog's width slider work for text stamps too.
    """
    png, _w, _h = render_stamp(cfg)
    src = QImage.fromData(png, "PNG")
    if src.isNull():
        raise StampImageError("图章渲染失败，请重新设置图章。")
    if target_width and target_width > 0:
        nw = max(1, int(round(target_width * SS)))
        nh = max(1, int(round(src.height() * nw / max(1, src.width()))))
        src = src.scaled(nw, nh, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
    full_w = float(src.width())
    full_h = float(src.height())
    n = max(1, int(count))
    unit = full_w / n
    pad = unit * max(0.0, min(0.4, float(overlap))) / 2.0
    out: List[Tuple[bytes, float, float]] = []
    for i in range(n):
        x0 = max(0.0, i * unit - pad)
        x1 = min(full_w, (i + 1) * unit + pad)
        if x1 <= x0:
            x1 = min(full_w, x0 + 1)
        piece = src.copy(int(round(x0)), 0,
                         max(1, int(round(x1 - x0))), int(full_h))
        out.append((_png(piece), (x1 - x0) / SS, full_h / SS))
    return out
