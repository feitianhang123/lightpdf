"""Locate bundled resources both when running from source and when frozen."""
from __future__ import annotations

import os
import sys


def resource_path(*parts: str) -> str | None:
    """Return the first existing path for *parts* under the bundle or project root."""
    roots = []
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        roots.append(meipass)
    here = os.path.dirname(os.path.abspath(__file__))        # app/
    roots.append(os.path.dirname(here))                      # project root
    roots.append(here)
    for root in roots:
        p = os.path.join(root, *parts)
        if os.path.exists(p):
            return p
    return None


def icon_path() -> str | None:
    return resource_path("icon.ico")
