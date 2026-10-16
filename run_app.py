"""Packaging entry point for 轻PDF编辑器."""
import os
import sys


def _crash_log() -> None:
    import tempfile
    import traceback
    try:
        path = os.path.join(tempfile.gettempdir(), "lightpdf_crash.log")
        with open(path, "w", encoding="utf-8") as f:
            f.write("argv=%r\n" % (sys.argv,))
            f.write("frozen=%r meipass=%r\n" % (getattr(sys, "frozen", None),
                                               getattr(sys, "_MEIPASS", None)))
            f.write(traceback.format_exc())
    except Exception:  # noqa: BLE001
        pass


if __name__ == "__main__":
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from app.main import main
        raise SystemExit(main())
    except SystemExit:
        raise
    except BaseException:  # noqa: BLE001
        _crash_log()
        raise
