"""Entry point for the Light PDF Editor (single-instance, multi-tab)."""
from __future__ import annotations

import json
import os
import sys

from PySide6.QtGui import QIcon
from PySide6.QtNetwork import QLocalServer, QLocalSocket
from PySide6.QtWidgets import QApplication

from . import i18n
from .paths import icon_path
from .ui.main_window import MainWindow
from .ui.theme import apply_theme
from .ui.translations import apply_qt_translations

SERVER_NAME = "LightPDFEditor.SingleInstance.v1"


def _open_files() -> list:
    return [a for a in sys.argv[1:] if a and os.path.isfile(a)]


def _send_to_running(paths: list) -> bool:
    """If another instance is running, hand it the file paths and return True."""
    sock = QLocalSocket()
    sock.connectToServer(SERVER_NAME)
    if not sock.waitForConnected(400):
        return False
    try:
        sock.write(json.dumps(paths).encode("utf-8"))
        sock.flush()
        sock.waitForBytesWritten(1000)
        sock.disconnectFromServer()
    except Exception:  # noqa: BLE001
        pass
    return True


def _start_server(win: MainWindow) -> QLocalServer:
    server = QLocalServer(win)
    if not server.listen(SERVER_NAME):
        QLocalServer.removeServer(SERVER_NAME)
        server.listen(SERVER_NAME)

    def on_connection() -> None:
        conn = server.nextPendingConnection()
        if conn is None:
            return

        def on_ready() -> None:
            raw = bytes(conn.readAll()).decode("utf-8", "ignore")
            conn.disconnectFromServer()
            try:
                paths = json.loads(raw)
            except Exception:  # noqa: BLE001
                paths = []
            if isinstance(paths, list):
                for p in paths:
                    if isinstance(p, str) and os.path.isfile(p):
                        win._load(p)
            win.raise_()
            win.activateWindow()

        conn.readyRead.connect(on_ready)
        conn.disconnected.connect(conn.deleteLater)

    server.newConnection.connect(on_connection)
    return server


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("轻PDF编辑器")
    app.setOrganizationName("MiniPDF")

    ic = icon_path()
    if ic:
        app.setWindowIcon(QIcon(ic))

    i18n.load_language()
    apply_qt_translations(app, i18n.language())
    apply_theme(app)

    files = _open_files()

    # Single instance: hand off to the already-running window and exit.
    if _send_to_running(files):
        return 0

    win = MainWindow()
    if ic:
        win.setWindowIcon(QIcon(ic))
    _start_server(win)
    win.show()
    for f in files:
        win._load(f)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
