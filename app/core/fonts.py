"""Enumerate locally installed fonts and resolve their files (cross-platform).

- Windows: registry under
  HKLM/HKCU\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Fonts
- Linux/macOS: fontconfig (`fc-list`) when available, else a directory scan
  of the usual font locations.
"""
from __future__ import annotations

import os
import subprocess
import sys
from functools import lru_cache
from typing import List, Optional, Tuple

_WIN_FONT_DIRS = [os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts"),
                  os.path.join(os.environ.get("LOCALAPPDATA", ""),
                               "Microsoft", "Windows", "Fonts")]

_UNIX_FONT_DIRS = [
    "/usr/share/fonts", "/usr/local/share/fonts",
    "/usr/share/fonts/truetype", "/usr/share/fonts/opentype",
    os.path.expanduser("~/.fonts"),
    os.path.expanduser("~/.local/share/fonts"),
    "/System/Library/Fonts", "/Library/Fonts",
    os.path.expanduser("~/Library/Fonts"),
]

_EXT = (".ttf", ".otf", ".ttc")


def _resolve_win(filename: str) -> Optional[str]:
    if os.path.isabs(filename) and os.path.isfile(filename):
        return filename
    for d in _WIN_FONT_DIRS:
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
            path = _resolve_win(data)
            if path:
                out.append((family, path))
    finally:
        try:
            winreg.CloseKey(key)  # type: ignore[name-defined]
        except Exception:  # noqa: BLE001
            pass
    return out


def _windows_fonts() -> List[Tuple[str, str]]:
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
        for d in _WIN_FONT_DIRS:
            if d and os.path.isdir(d):
                for fn in os.listdir(d):
                    if fn.lower().endswith(_EXT):
                        entries.append((os.path.splitext(fn)[0], os.path.join(d, fn)))
    return entries


def _unix_fonts() -> List[Tuple[str, str]]:
    out: List[Tuple[str, str]] = []
    try:
        r = subprocess.run(["fc-list", "--format", "%{family[0]}|%{file}\n"],
                           capture_output=True, text=True, timeout=15)
        for line in (r.stdout or "").splitlines():
            if "|" not in line:
                continue
            fam, path = line.split("|", 1)
            fam, path = fam.strip(), path.strip()
            if fam and os.path.isfile(path):
                out.append((fam, path))
    except Exception:  # noqa: BLE001
        pass
    if not out:
        for d in _UNIX_FONT_DIRS:
            if not os.path.isdir(d):
                continue
            for root, _dirs, files in os.walk(d):
                for fn in files:
                    if fn.lower().endswith(_EXT):
                        out.append((os.path.splitext(fn)[0], os.path.join(root, fn)))
    return out


@lru_cache(maxsize=1)
def system_fonts() -> List[Tuple[str, str]]:
    """Return a sorted list of (label, font file path) for installed fonts."""
    entries = _windows_fonts() if sys.platform.startswith("win") else _unix_fonts()
    seen = set()
    uniq: List[Tuple[str, str]] = []
    for fam, path in entries:
        key = fam.lower()
        if not fam or key in seen:
            continue
        seen.add(key)
        uniq.append((fam, path))
    uniq.sort(key=lambda t: t[0].lower())
    return uniq


def is_font_file(value) -> bool:
    return isinstance(value, str) and value.lower().endswith(_EXT) and os.path.isfile(value)
