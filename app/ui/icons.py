"""Self-drawn vector icons (original artwork) rendered from inline SVG."""
from __future__ import annotations

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer

PRIMARY = "#2E7D32"

_H = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
      'stroke="{c}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">')

ICONS: dict[str, str] = {
    "new": _H + '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/>'
                 '<path d="M14 3v5h5"/><path d="M12 12v5M9.5 14.5h5"/></svg>',
    "open": _H + '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/></svg>',
    "save": _H + '<path d="M5 3h11l3 3v15H5z"/><path d="M8 3v6h7V3"/>'
                 '<rect x="8" y="13" width="8" height="6"/></svg>',
    "print": _H + '<path d="M7 8V3h10v5"/><rect x="4" y="8" width="16" height="8" rx="1"/>'
                  '<path d="M7 14h10v7H7z"/></svg>',
    "close": _H + '<path d="M6 6l12 12M18 6L6 18"/></svg>',
    "properties": _H + '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3'
                       'M4.9 4.9l2.1 2.1M17 17l2.1 2.1M19.1 4.9L17 7M7 17l-2.1 2.1"/></svg>',
    "zoom_in": _H + '<circle cx="11" cy="11" r="6"/><path d="M20 20l-4.5-4.5M11 8v6M8 11h6"/></svg>',
    "zoom_out": _H + '<circle cx="11" cy="11" r="6"/><path d="M20 20l-4.5-4.5M8 11h6"/></svg>',
    "fit_width": _H + '<path d="M3 5v14M21 5v14"/><path d="M7 12h10"/>'
                      '<path d="M10 9l-3 3 3 3M14 9l3 3-3 3"/></svg>',
    "fit_page": _H + '<rect x="4" y="4" width="16" height="16" rx="1"/>'
                     '<path d="M8 12h8M11 9l-3 3 3 3M13 9l3 3-3 3"/></svg>',
    "actual": _H + '<rect x="3" y="8" width="18" height="8" rx="1"/>'
                   '<path d="M7 8v3M11 8v4M15 8v3M19 8v4"/></svg>',
    "rotate_cw": _H + '<path d="M20 11a8 8 0 1 1-2.3-5.7"/><path d="M20 4v5h-5"/></svg>',
    "rotate_ccw": _H + '<path d="M4 11a8 8 0 1 0 2.3-5.7"/><path d="M4 4v5h5"/></svg>',
    "prev": _H + '<path d="M15 6l-6 6 6 6"/></svg>',
    "next": _H + '<path d="M9 6l6 6-6 6"/></svg>',
    "select": _H + '<path d="M5 3l7 17 2.5-6.5L21 11z"/></svg>',
    "highlight": _H + '<path d="M4 20h16"/><path d="M9 16l-3-3 7-7 3 3z"/><path d="M13 6l3 3"/></svg>',
    "underline": _H + '<path d="M7 4v7a5 5 0 0 0 10 0V4"/><path d="M5 20h14"/></svg>',
    "strikeout": _H + '<path d="M16 7c-1-1.5-2.5-2-4-2-2 0-3.5 1-3.5 2.5S10 10 12 10.5s3.5 1 3.5 2.5S14 16 12 16c-1.5 0-3-.5-4-2"/>'
                      '<path d="M4 12h16"/></svg>',
    "note": _H + '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4"/><path d="M9 12h6M9 15h6"/></svg>',
    "freetext": _H + '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M8 9h8M12 9v7"/></svg>',
    "ink": _H + '<path d="M3 21l3.5-1L20 6.5 17.5 4 4 17.5z"/><path d="M14 6.5l3.5 3.5"/></svg>',
    "rect": _H + '<rect x="4" y="5" width="16" height="14" rx="1"/></svg>',
    "ellipse": _H + '<ellipse cx="12" cy="12" rx="8" ry="6"/></svg>',
    "line": _H + '<path d="M4 20L20 4"/></svg>',
    "arrow": _H + '<path d="M4 20L20 4M20 4h-7M20 4v7"/></svg>',
    "stamp": _H + '<path d="M12 3a2 2 0 0 0-2 2c0 1.5-2 3-2 7h8c0-4-2-5.5-2-7a2 2 0 0 0-2-2z"/>'
                  '<rect x="5" y="14" width="14" height="3" rx="1"/><path d="M4 20h16"/></svg>',
    "edittext": _H + '<path d="M4 6h9M8.5 6v13"/><path d="M15 20l1.5-4.5 4.5 4.5-4.5 1.5z"/></svg>',
    "whiteout": _H + '<path d="M8 20H4l-1-3 10-10 5 5-6 6z"/><path d="M9 7l5 5"/></svg>',
    "insertimage": _H + '<rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="8.5" cy="9" r="1.5"/>'
                        '<path d="M21 16l-5-5-4 4-2-2-4 4"/></svg>',
    "compare": _H + '<rect x="3" y="4" width="8" height="16" rx="1"/><rect x="13" y="4" width="8" height="16" rx="1"/>'
                    '<path d="M7 10l-2 2 2 2M17 10l2 2-2 2"/></svg>',
    "convert": _H + '<path d="M4 8h13M14 5l3 3-3 3"/><path d="M20 16H7M10 13l-3 3 3 3"/></svg>',
    "ocr": _H + '<path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3"/>'
                '<path d="M8 10h8M8 13h5"/></svg>',
    "search": _H + '<circle cx="11" cy="11" r="7"/><path d="M20 20l-4.5-4.5"/></svg>',
    "settings": _H + '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3'
                     'M4.9 4.9l2.1 2.1M17 17l2.1 2.1M19.1 4.9L17 7M7 17l-2.1 2.1"/></svg>',
    "language": _H + '<circle cx="12" cy="12" r="9"/>'
                     '<path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/></svg>',
    "help": _H + '<circle cx="12" cy="12" r="9"/><path d="M9.5 9a2.5 2.5 0 0 1 4.6 1.5c0 1.5-2 2-2 3.5"/>'
                 '<path d="M12 17h.01"/></svg>',
    "merge": _H + '<path d="M8 3v6a4 4 0 0 0 4 4h4"/><path d="M16 3v6a4 4 0 0 1-4 4H8"/>'
                  '<path d="M16 13l3 3-3 3"/></svg>',
    "undo": _H + '<path d="M4 9h9a5 5 0 0 1 0 10H8"/><path d="M7 5L3 9l4 4"/></svg>',
    "redo": _H + '<path d="M20 9h-9a5 5 0 0 0 0 10h5"/><path d="M17 5l4 4-4 4"/></svg>',
    "hand": _H + '<path d="M7 12V6.5a1.4 1.4 0 0 1 2.8 0V11"/>'
                 '<path d="M9.8 11V4.8a1.4 1.4 0 0 1 2.8 0V11"/>'
                 '<path d="M12.6 11V5.4a1.4 1.4 0 0 1 2.8 0V11.5"/>'
                 '<path d="M15.4 11.8V8a1.4 1.4 0 0 1 2.8 0v7.2a5.6 5.6 0 0 1-5.6 5.6h-1'
                 'a4.6 4.6 0 0 1-3.6-1.7l-3.3-4.2a1.5 1.5 0 0 1 2.4-1.8L8 14.5"/></svg>',
}

_CACHE: dict[tuple, QIcon] = {}


def _render(svg: str, size: int) -> QPixmap:
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    pm = QPixmap(size, size)
    pm.fill(Qt.transparent)
    painter = QPainter(pm)
    renderer.render(painter)
    painter.end()
    return pm


def icon(name: str, color: str = PRIMARY) -> QIcon:
    key = (name, color)
    if key in _CACHE:
        return _CACHE[key]
    svg = ICONS.get(name)
    qicon = QIcon()
    if svg:
        colored = svg.replace("{c}", color)
        for size in (16, 20, 24, 32, 48, 64):
            qicon.addPixmap(_render(colored, size))
    _CACHE[key] = qicon
    return qicon
