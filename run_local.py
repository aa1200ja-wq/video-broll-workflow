import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path


PORT = 8765
URL = f"http://127.0.0.1:{PORT}"


def _root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def _already_running() -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.25)
        return sock.connect_ex(("127.0.0.1", PORT)) == 0


def _open_browser() -> None:
    time.sleep(1.2)
    webbrowser.open(URL)


def _show_error(message: str) -> None:
    log = _root() / "BrollWorkflow-error.log"
    log.write_text(message, encoding="utf-8")
    if os.name == "nt":
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, message, "B-roll Workflow", 0x10)
    else:
        print(message)


def main() -> None:
    root = _root()
    os.chdir(root)
    if _already_running():
        webbrowser.open(URL)
        return
    sys.path.insert(0, str(root / "apps" / "server"))
    from app.main import app
    import uvicorn
    threading.Thread(target=_open_browser, daemon=True).start()
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning", log_config=None)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        _show_error(f"啟動失敗：{type(exc).__name__}: {exc}")
