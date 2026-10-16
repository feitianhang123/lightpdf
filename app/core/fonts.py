"""Enumerate locally installed fonts and resolve their files.

Windows fonts are registered under
  HKLM/HKCU\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts
as  "<Family> (<Type>)" -> "<file name or full path>".
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import List, Optional, Tuple

_FONT_DIRS = [os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"),
              os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts")]


def _resolve(filename: str) -> Optional[str]:
    if os.path.isabs(filename) and os.path.isfile(filename):
        return filename
    for d in _FONT_DIRS:
        if d and os.path.isfile(os.path.join(d, filename)):
            return os.path.join(d, filename)
    return None


def _reg_entries(root, subkey: str) -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    try:
        import winreg
        key = winreg.OpenKey(root, subkey)
    except Exception:  # noqa: BLE001
        return out
    try:
        i = 0
        while True:
            try:
                name, data, _ = winreg.EnumValue(key, i)
            except OSError:
                break
            i += 1
            if not isinstance(data, str):
                continue
            family = name.split(" (")[0].strip()
            path = _resolve(data)
            if path:
                out.append((family, path))
    finally:
        try:
            winreg.CloseKey(key)
        except Exception:  # noqa: BLE001
            pass
    return out


@lru_cache(maxsize=1)
def system_fonts() -> List[Tuple[str, str]]:
    """Return a sorted list of (label, font file path) for installed fonts."""
    entries: List[Tuple[str, str]] = []
    try:
        import winreg
        entries += _reg_entries(winreg.HKEY_CURRENT_USER,
                                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts")
        entries += _reg_entries(winreg.HKEY_LOCAL_MACHINE,
                                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts")
    except Exception:  # noqa: BLE001
        pass
    if not entries:
        # fallback: scan the fonts directory
        for d in _FONT_DIRS:
            if d and os.path.isdir(d):
                for fn in os.listdir(d):
                    if fn.lower().endswith((".ttf", ".otf", ".ttc")):
                        entries.append((os.path.splitext(fn)[0], os.path.join(d, fn)))
    seen = set()
    uniq: List[Tuple[str, str]] = []
    for fam, path in entries:
        key = fam.lower()
        if key in seen:
            continue
        seen.add(key)
        uniq.append((fam, path))
    uniq.sort(key=lambda t: t[0].lower())
    return uniq


def is_font_file(value) -> bool:
    return isinstance(value, str) and value.lower().endswith((".ttf", ".otf", ".ttc")) \
        and os.path.isfile(value)
