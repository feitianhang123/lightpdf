"""Render user-defined stamps (text or image) to PNG for page insertion.

Also provides vertical slicing for 骑缝章 (riding / perforation stamps).
"""
from __future__ import annotations

import json
import os
from typing import List, Tuple

import numpy as np
from PySide6.QtCore import (QBuffer, QFile, QIODevice, QRectF, QSettings,
                            QStandardPaths, Qt)
from PySide6.QtGui import (QBrush, QColor, QFont, QFontDatabase, QFontMetrics,
                           QImage, QImageReader, QPainter, QPen)
from PySide6.QtWidgets import QApplication  # noqa: F401  (ensures GUI context)

SS = 3  # supersampling factor for crisp output

# Physical-unit conversion: PDF page coordinates are points (1/72 inch).
PT_PER_MM = 72.0 / 25.4
MM_PER_PT = 25.4 / 72.0

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
    # "stamp_diameter_mm" is the diameter of the RED seal itself, not the
    # uploaded photo's canvas size.  "remove_bg" strips the photo background
    # and crops to the ink before sizing (see prepare_stamp_image).
    "stamp_diameter_mm": 40.0,
    "remove_bg": True,
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
    # migrate legacy pixel width -> physical diameter (an old 160px image was
    # written at 72dpi, i.e. ~56.4 mm; keep that apparent size after upgrade).
    if "stamp_diameter_mm" not in cfg:
        legacy = float(cfg.pop("image_width", 160)) * MM_PER_PT
        cfg["stamp_diameter_mm"] = round(legacy, 1)
    cfg.pop("image_width", None)
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


# ------------------------------------------------------- background removal
def _rgba_array(img: QImage) -> np.ndarray:
    """QImage(ARGB32/RGBA8888) -> numpy HxWx4 array in R,G,B,A byte order.

    ``Format_ARGB32`` stores bytes as B,G,R,A on little-endian machines, so we
    first convert to ``Format_RGBA8888`` whose byte layout is guaranteed R,G,B,A.
    bytesPerLine is honoured (Qt may pad rows).
    """
    img = img.convertToFormat(QImage.Format_RGBA8888)
    w, h = img.width(), img.height()
    bpl = img.bytesPerLine()
    buf = np.frombuffer(img.constBits(), dtype=np.uint8, count=bpl * h)
    arr = buf.reshape(h, bpl)[:, : w * 4].reshape(h, w, 4)
    return arr.copy()


def _array_image(arr: np.ndarray) -> QImage:
    """numpy HxWx4 (R,G,B,A) -> QImage ARGB32."""
    h, w = arr.shape[:2]
    src = np.ascontiguousarray(arr, dtype=np.uint8)
    img = QImage(w, h, QImage.Format_RGBA8888)
    bpl = img.bytesPerLine()
    if bpl == w * 4:
        dst = np.frombuffer(img.bits(), dtype=np.uint8, count=bpl * h).reshape(h, w, 4)
        dst[:] = src
    else:
        for y in range(h):
            row = np.frombuffer(img.bits(), dtype=np.uint8,
                                count=bpl * h)[y * bpl:y * bpl + w * 4]
            row[:] = src[y].reshape(-1)
    return img.convertToFormat(QImage.Format_ARGB32)


def remove_background(img: QImage, *, red_boost: bool = True) -> QImage:
    """Strip a photo's flat background, keeping the (red) seal ink.

    Algorithm (numpy-only — cv2 is intentionally excluded from the frozen
    build): find low-saturation bright background pixels from the image border,
    mark everything close to that colour as transparent, then keep pixels that
    are either dark or clearly red.  Anti-aliased edges get proportional alpha
    so the seal does not acquire a jagged halo.  On failure the original image
    is returned unchanged (never silently destroys a stamp).
    """
    arr = _rgba_array(img)
    h, w = arr.shape[:2]
    if h < 2 or w < 2:
        return img
    rgb = arr[:, :, :3].astype(np.int32)
    a0 = arr[:, :, 3].astype(np.float32)
    mx = rgb.max(axis=2)
    mn = rgb.min(axis=2)
    sat = mx - mn                        # 0 = grey/white
    lum = (0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2])

    # Estimate background colour from a border ring (median of 4 edges).
    ring = np.concatenate([
        rgb[0, :, :], rgb[-1, :, :], rgb[:, 0, :], rgb[:, -1, :]], axis=0)
    bg = np.median(ring, axis=0).astype(np.int32)
    dist = np.sqrt(((rgb - bg) ** 2).sum(axis=2))

    # Ink = far from background AND (dark or saturated or red-dominant).
    # White/grey paper sitting near bg becomes transparent; faint shadows get
    # a soft alpha instead of a hard cut.
    ink_score = np.maximum.reduce([
        (dist - 26.0) * 2.6,               # colour difference from paper
        (205.0 - lum) * 1.6,               # dark strokes / black seal
        (sat - 34.0) * 1.8,                # saturated colour ink
    ])
    if red_boost:
        red_dom = (rgb[:, :, 0] - np.maximum(rgb[:, :, 1], rgb[:, :, 2]))
        ink_score = np.maximum(ink_score, (red_dom - 24.0) * 2.2)
    alpha = np.clip(ink_score, 0.0, 255.0)
    # Respect any transparency already present in the source.
    alpha = np.minimum(alpha, a0)

    # Keep only the largest useful ink cluster by dropping isolated specks:
    # zero out alpha below a small threshold, then crop to remaining content.
    arr[:, :, 3] = alpha.astype(np.uint8)
    ys, xs = np.where(alpha > 40)
    if ys.size < max(12, int(w * h * 0.0002)):
        return img                       # detection found nothing — keep source
    x0, x1 = max(0, int(xs.min()) - 2), min(w, int(xs.max()) + 3)
    y0, y1 = max(0, int(ys.min()) - 2), min(h, int(ys.max()) + 3)
    return _array_image(arr[y0:y1, x0:x1])


def red_seal_diameter_px(img: QImage) -> float:
    """Diameter (px) of the red ink region = the *larger* side of its bbox.

    Uses a permissive red-dominance test so dark-red seal edges are included.
    Returns 0 when there is no obvious red ink (e.g. a black signature stamp).
    """
    arr = _rgba_array(img)
    if arr.shape[0] < 2 or arr.shape[1] < 2:
        return 0.0
    rgb = arr[:, :, :3].astype(np.int32)
    r, g, b = rgb[:, :, 0], rgb[:, :, 1], rgb[:, :, 2]
    red = (arr[:, :, 3] > 40) & (r > 90) & (r - g > 38) & (r - b > 38)
    ys, xs = np.where(red)
    if ys.size < 8:
        return 0.0
    return float(max(xs.max() - xs.min() + 1, ys.max() - ys.min() + 1))


# Processed images are cached: live preview re-renders on every spin change and
# a 4000x3000 photo must not be re-analysed each time.
_IMAGE_CACHE: dict = {}


def _cached_image(path: str, remove_bg: bool) -> QImage:
    try:
        mtime = os.path.getmtime(path)
    except OSError:
        mtime = 0
    key = (path, bool(remove_bg), mtime)
    hit = _IMAGE_CACHE.get(key)
    if hit is not None:
        return hit
    if len(_IMAGE_CACHE) > 12:
        _IMAGE_CACHE.clear()
    src = load_source_image(path)
    out = remove_background(src) if remove_bg else src
    _IMAGE_CACHE[key] = out
    return out


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
    """Render an image stamp sized by the RED SEAL diameter, in points.

    ``stamp_diameter_mm`` refers to the physical diameter of the red ink, not
    the uploaded photo's canvas.  When ``remove_bg`` is on, the photo's paper
    background is stripped and the image is cropped to the ink first, so the
    whole (cropped) image is exactly the seal.  The image is then scaled so the
    red region measures ``stamp_diameter_mm``.  Returns ``(png, w_pt, h_pt)``.
    """
    path = cfg.get("image", "")
    if not path:
        raise StampImageError("还没有选择图章图片，请点「选择图片...」。")
    src = _cached_image(path, bool(cfg.get("remove_bg", True)))

    diameter_mm = max(5.0, float(cfg.get("stamp_diameter_mm", 40.0)))
    diameter_pt = diameter_mm * PT_PER_MM

    # If the image still has margins around the red ink (background removal
    # off / failed, or a photo with a border), scale by the red region's share
    # of the canvas so the *red diameter* equals the requested size.
    red_px = red_seal_diameter_px(src)
    canvas_px = float(max(src.width(), src.height()))
    ratio = (red_px / canvas_px) if red_px > 0 else 1.0
    ratio = min(1.0, max(0.05, ratio))

    target_w = diameter_pt / ratio                       # pt
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


_SLICE_CACHE: dict = {}


def render_stamp_slices(cfg: dict, count: int, overlap: float = 0.0
                        ) -> List[Tuple[bytes, float, float]]:
    """Cut one stamp into ``count`` vertical slices for a riding stamp.

    ``overlap`` (0..0.4) widens every slice slightly so that binding/cutting
    does not break the seal.  The seal's physical size now comes solely from
    ``cfg['stamp_diameter_mm']`` (see render_stamp), so no separate width
    argument is needed.  Results are cached so live-preview of a 100-page
    document stays responsive.
    """
    key = (json.dumps(cfg, sort_keys=True, ensure_ascii=False), int(count),
           float(overlap))
    hit = _SLICE_CACHE.get(key)
    if hit is not None:
        return hit
    png, _w, _h = render_stamp(cfg)
    src = QImage.fromData(png, "PNG")
    if src.isNull():
        raise StampImageError("图章渲染失败，请重新设置图章。")
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
    if len(_SLICE_CACHE) > 16:
        _SLICE_CACHE.clear()
    _SLICE_CACHE[key] = out
    return out
