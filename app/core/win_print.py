# -*- coding: utf-8 -*-
"""Windows 原生 GDI 打印（ctypes）。

背景：Qt 的 QPrinter 在部分驱动（如 iR C3020 网络复合机）上设置的纸张方向 / 双面
不会写进驱动的 DEVMODE，驱动改用自身默认（横向 / 单面），出现“方向怎么选都横向、
双面翻转无效”。本模块用 ctypes 直接构造完整 DEVMODE（含驱动私有数据），通过
CreateDC 交给驱动，方向 / 双面 / 纸张完全受控——与 Foxit 的打印方式一致。

设计：调用方先用 Qt 逻辑把每一页排成一张“整纸画布”QImage（含页边距、缩放、居中），
本模块只负责把这些位图按 1:1 贴到打印机可打印区域，不参与内容布局。

仅 Windows 使用；非 Windows 由调用方走原 QPrinter 路径。
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes

# ---- DEVMODEW（基础 220 字节，驱动私有数据由 DocumentProperties 补齐）----
class DEVMODEW(ctypes.Structure):
    _fields_ = [
        ("dmDeviceName", wintypes.WCHAR * 32),
        ("dmSpecVersion", wintypes.WORD),
        ("dmDriverVersion", wintypes.WORD),
        ("dmSize", wintypes.WORD),
        ("dmDriverExtra", wintypes.WORD),
        ("dmFields", wintypes.DWORD),
        ("dmOrientation", ctypes.c_short),
        ("dmPaperSize", ctypes.c_short),
        ("dmPaperLength", ctypes.c_short),
        ("dmPaperWidth", ctypes.c_short),
        ("dmScale", ctypes.c_short),
        ("dmCopies", ctypes.c_short),
        ("dmDefaultSource", ctypes.c_short),
        ("dmPrintQuality", ctypes.c_short),
        ("dmColor", ctypes.c_short),
        ("dmDuplex", ctypes.c_short),
        ("dmYResolution", ctypes.c_short),
        ("dmTTOption", ctypes.c_short),
        ("dmCollate", ctypes.c_short),
        ("dmFormName", wintypes.WCHAR * 32),
        ("dmLogPixels", wintypes.WORD),
        ("dmBitsPerPel", wintypes.DWORD),
        ("dmPelsWidth", wintypes.DWORD),
        ("dmPelsHeight", wintypes.DWORD),
        ("dmDisplayFlags", wintypes.DWORD),
        ("dmDisplayFrequency", wintypes.DWORD),
        ("dmICMMethod", wintypes.DWORD),
        ("dmICMIntent", wintypes.DWORD),
        ("dmMediaType", wintypes.DWORD),
        ("dmDitherType", wintypes.DWORD),
        ("dmReserved1", wintypes.DWORD),
        ("dmReserved2", wintypes.DWORD),
        ("dmPanningWidth", wintypes.DWORD),
        ("dmPanningHeight", wintypes.DWORD),
    ]


class PRINTER_DEFAULTS(ctypes.Structure):
    _fields_ = [
        ("pDatatype", wintypes.LPWSTR),
        ("pDevMode", ctypes.c_void_p),
        ("DesiredAccess", wintypes.DWORD),
    ]


class DOCINFOW(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_int),
        ("lpszDocName", wintypes.LPCWSTR),
        ("lpszOutput", wintypes.LPCWSTR),
        ("lpszDatatype", wintypes.LPCWSTR),
        ("fwType", wintypes.DWORD),
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


# ---- 常量 ----
DM_OUT_BUFFER = 2
DM_ORIENTATION = 0x1
DM_PAPERSIZE = 0x2
DM_DUPLEX = 0x1000
DM_COPIES = 0x8
DMORIENT_PORTRAIT = 1
DMORIENT_LANDSCAPE = 2
DMDUP_SIMPLEX = 1
DMDUP_LONGEDGE = 2       # DMDUP_HORIZONTAL
DMDUP_SHORTEDGE = 3      # DMDUP_VERTICAL
DMPAPER_A4 = 9
PRINTER_ACCESS_USE = 0x8
HORZRES, VERTRES = 8, 10
LOGPIXELSX, LOGPIXELSY = 88, 90
PHYSICALOFFSETX, PHYSICALOFFSETY = 112, 113
DIB_RGB_COLORS = 0
SRCCOPY = 0x00CC0020
BI_RGB = 0

_winspool = ctypes.windll.LoadLibrary("winspool.drv")
_gdi32 = ctypes.windll.gdi32

_winspool.OpenPrinterW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(wintypes.HANDLE), ctypes.c_void_p]
_winspool.OpenPrinterW.restype = wintypes.BOOL
_winspool.DocumentPropertiesW.argtypes = [wintypes.HWND, wintypes.HANDLE, wintypes.LPCWSTR,
    ctypes.c_void_p, ctypes.c_void_p, wintypes.LONG]
_winspool.DocumentPropertiesW.restype = wintypes.LONG
_winspool.ClosePrinter.argtypes = [wintypes.HANDLE]
_gdi32.CreateDCW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR, ctypes.c_void_p]
_gdi32.CreateDCW.restype = wintypes.HDC
_gdi32.DeleteDC.argtypes = [wintypes.HDC]
_gdi32.GetDeviceCaps.argtypes = [wintypes.HDC, ctypes.c_int]
_gdi32.GetDeviceCaps.restype = ctypes.c_int
_gdi32.StartDocW.argtypes = [wintypes.HDC, ctypes.POINTER(DOCINFOW)]
_gdi32.StartDocW.restype = ctypes.c_int
_gdi32.StartPage.argtypes = [wintypes.HDC]
_gdi32.StartPage.restype = ctypes.c_int
_gdi32.EndPage.argtypes = [wintypes.HDC]
_gdi32.EndPage.restype = ctypes.c_int
_gdi32.EndDoc.argtypes = [wintypes.HDC]
_gdi32.EndDoc.restype = ctypes.c_int
_gdi32.AbortDoc.argtypes = [wintypes.HDC]
_gdi32.StretchDIBits.argtypes = [
    wintypes.HDC, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
    ctypes.c_void_p, ctypes.c_void_p, wintypes.UINT, wintypes.DWORD]
_gdi32.StretchDIBits.restype = ctypes.c_int


def is_available() -> bool:
    return hasattr(ctypes, "windll")


class CanvasPrinter:
    """逐页画布适配器：QPrinter 的轻量替身，供打印布局代码原样复用。

    关键：QPainter 必须由本类持有，newPage() 时 end() 当前画布、begin() 新画布。
    v1.0.22 初版让调用方自己 QPainter(canvas.canvas)，newPage() 只换 _current，
    painter 一直画在第一张 QImage 上 —— 实测「4 页只有最后一页有内容」。
    """

    def __init__(self, width: int, height: int, dpi: int = 300):
        from PySide6.QtGui import QImage, QPainter
        self.width = int(width)
        self.height = int(height)
        self._dpi = int(dpi)
        self.pages = []
        self._current = QImage(self.width, self.height, QImage.Format_RGB32)
        self._current.fill(0xFFFFFFFF)
        self.painter = QPainter(self._current)   # 由本类持有，换页时切换设备

    @property
    def canvas(self):
        return self._current

    def resolution(self):
        return self._dpi

    def newPage(self):
        from PySide6.QtGui import QImage
        hints = self.painter.renderHints()
        self.pages.append(self._current)
        self.painter.end()                  # 结束上一页的绘制
        self._current = QImage(self.width, self.height, QImage.Format_RGB32)
        self._current.fill(0xFFFFFFFF)
        self.painter.begin(self._current)   # 关键：切到新画布，否则后续页全画到第一页
        self.painter.setRenderHints(hints)

    def finish(self):
        self.painter.end()
        self.pages.append(self._current)
        return self.pages


def _build_devmode(printer: str, landscape: bool, duplex: str, copies: int):
    """打开打印机并取得含驱动私有数据的完整 DEVMODE。返回 (hprinter, buf, dm)。"""
    hprinter = wintypes.HANDLE()
    defaults = PRINTER_DEFAULTS(None, None, PRINTER_ACCESS_USE)
    if not _winspool.OpenPrinterW(printer, ctypes.byref(hprinter), ctypes.byref(defaults)):
        raise OSError(f"OpenPrinter failed: {printer}")
    # 部分驱动查询大小为 -1；统一分配足够大的缓冲（iR C3020 实测 220+968）。
    buf = ctypes.create_string_buffer(8192)
    ret = _winspool.DocumentPropertiesW(None, hprinter, printer, buf, None, DM_OUT_BUFFER)
    if ret < 0:
        _winspool.ClosePrinter(hprinter)
        raise OSError(f"DocumentProperties failed: {printer} (ret={ret})")
    dm = ctypes.cast(buf, ctypes.POINTER(DEVMODEW)).contents
    dm.dmOrientation = DMORIENT_LANDSCAPE if landscape else DMORIENT_PORTRAIT
    dm.dmPaperSize = DMPAPER_A4
    dm.dmDuplex = {"none": DMDUP_SIMPLEX, "long": DMDUP_LONGEDGE,
                   "short": DMDUP_SHORTEDGE}.get(duplex, DMDUP_SIMPLEX)
    dm.dmFields |= DM_ORIENTATION | DM_PAPERSIZE | DM_DUPLEX
    if copies and copies > 0:
        dm.dmCopies = int(copies)
        dm.dmFields |= DM_COPIES
    return hprinter, buf, dm


def _stretch_image(hdc, qimage, x, y, w, h) -> bool:
    """把调用方已转成 ARGB32 的 QImage 以 32bpp top-down DIB 贴到 DC。

    源数据指针在 StretchDIBits 返回后仍可能被驱动引用（尤其 EndPage 阶段），
    因此调用方必须保证 qimage 存活到 EndDoc 之后；这里不再 convertToFormat
    制造临时对象（v1.0.22 初版每页临时对象析构导致前面页空白）。
    """
    img = qimage
    bi = BITMAPINFOHEADER()
    bi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bi.biWidth = img.width()
    bi.biHeight = -img.height()   # 负高度 = top-down，行序与 QImage 一致
    bi.biPlanes = 1
    bi.biBitCount = 32
    bi.biCompression = BI_RGB
    bi.biSizeImage = 0
    size = img.sizeInBytes()
    bits = img.bits()   # 可写缓冲（constBits 可能是只读 memoryview）
    # 兼容 bits() 返回 voidptr（有 setsize）或 memoryview 两种 PySide6 版本
    if hasattr(bits, "setsize"):
        bits.setsize(size)
        ptr = bits
    else:
        # memoryview：取其缓冲首地址，避免整幅拷贝
        ptr = ctypes.addressof(ctypes.c_char.from_buffer(bits))
    ok = _gdi32.StretchDIBits(
        hdc, x, y, w, h, 0, 0, img.width(), img.height(),
        ptr, ctypes.byref(bi), DIB_RGB_COLORS, SRCCOPY)
    return ok != 0 and ok != -1


def printable_rect(hdc):
    """返回打印机 DC 的可打印区域（像素）：(x, y, w, h)。"""
    ox = _gdi32.GetDeviceCaps(hdc, PHYSICALOFFSETX)
    oy = _gdi32.GetDeviceCaps(hdc, PHYSICALOFFSETY)
    pw = _gdi32.GetDeviceCaps(hdc, HORZRES)
    ph = _gdi32.GetDeviceCaps(hdc, VERTRES)
    return ox, oy, max(1, pw - 2 * ox), max(1, ph - 2 * oy)


def measure(printer: str, landscape: bool):
    """返回 (可打印区域像素宽, 高, 画布每英寸像素数)。

    画布尺寸按打印机可打印区域像素，DPI 由物理纸张尺寸反推，保证“实际大小”
    模式的物理英寸换算正确。
    """
    hprinter, buf, dm = _build_devmode(printer, landscape, "none", 1)
    hdc = None
    try:
        hdc = _gdi32.CreateDCW(None, printer, None, buf)
        if not hdc:
            raise OSError(f"CreateDC failed: {printer}")
        _x, _y, w, h = printable_rect(hdc)
        # LOGPIXELSX 是设备每英寸像素数，即画布 DPI（可打印区域像素/英寸）
        canvas_dpi = float(_gdi32.GetDeviceCaps(hdc, LOGPIXELSX)) or 300.0
        canvas_dpi = max(72.0, min(2400.0, canvas_dpi))
        return w, h, canvas_dpi
    finally:
        if hdc:
            _gdi32.DeleteDC(hdc)
        _winspool.ClosePrinter(hprinter)


def print_images(printer: str, images, *, landscape: bool, duplex: str = "none",
                 copies: int = 1, doc_name: str = "lightpdf") -> None:
    """用 GDI 把 QImage 列表逐页送到打印机。

    images: 每页一张“整纸画布”QImage（调用方已排好版）。
    landscape: 纸张方向；duplex: none/long/short；copies: 份数。
    成功返回 None；失败抛 OSError/RuntimeError。
    """
    hprinter, buf, dm = _build_devmode(printer, landscape, duplex, copies)
    hdc = None
    started = False
    try:
        hdc = _gdi32.CreateDCW(None, printer, None, buf)
        if not hdc:
            raise OSError(f"CreateDC failed: {printer}")
        docinfo = DOCINFOW()
        docinfo.cbSize = ctypes.sizeof(DOCINFOW)
        docinfo.lpszDocName = doc_name
        job = _gdi32.StartDocW(hdc, ctypes.byref(docinfo))
        if job <= 0:
            raise OSError(f"StartDoc failed: {printer}")
        started = True
        x, y, w, h = printable_rect(hdc)
        # 一次性转换并持有所有页的 ARGB32 位图，直到 EndDoc 之后才释放。
        # iR C3020 等驱动在 EndPage / EndDoc 阶段才真正读取 StretchDIBits 的源数据，
        # 若每页临时 QImage 在 _stretch_image 返回时析构，前面页就会打印成空白。
        from PySide6.QtGui import QImage as _QImage
        dib_images = [im.convertToFormat(_QImage.Format_ARGB32) for im in images]
        for img in dib_images:
            if _gdi32.StartPage(hdc) <= 0:
                raise OSError("StartPage failed")
            if not _stretch_image(hdc, img, x, y, w, h):
                # 贴图失败也结束本页，避免 DC 状态错乱
                _gdi32.EndPage(hdc)
                raise OSError("StretchDIBits failed")
            if _gdi32.EndPage(hdc) <= 0:
                raise OSError("EndPage failed")
        if _gdi32.EndDoc(hdc) <= 0:
            raise OSError("EndDoc failed")
        started = False
        # dib_images 的引用一直保持到这里，确保所有页 DIB 源数据到 EndDoc 都有效
        del dib_images
    finally:
        if hdc:
            if started:
                try:
                    _gdi32.AbortDoc(hdc)
                except Exception:
                    pass
            _gdi32.DeleteDC(hdc)
        _winspool.ClosePrinter(hprinter)
