from __future__ import annotations

import argparse
import sys
import time
from urllib.parse import urljoin

import requests


def wait_for_server(base_url: str, timeout_s: float = 10.0, interval_s: float = 0.3) -> bool:
    deadline = time.time() + timeout_s
    probe_urls = [
        base_url,
        urljoin(base_url.rstrip("/") + "/", "static/icons/aifrac.png"),
    ]

    while time.time() < deadline:
        for u in probe_urls:
            try:
                r = requests.get(u, timeout=1.5)
                if r.status_code < 500:
                    return True
            except Exception:
                pass
        time.sleep(interval_s)

    return False


def _safe_call(obj, method: str, *args, **kwargs):
    fn = getattr(obj, method, None)
    if callable(fn):
        return fn(*args, **kwargs)
    return None


class DesktopApi:
    def __init__(self, base_url: str, chat_width: int, chat_height: int, chat_topmost: bool):
        self.base_url = base_url
        self.chat_width = chat_width
        self.chat_height = chat_height
        self.chat_topmost = chat_topmost
        self._chat_window = None

    def _on_chat_closed(self):
        # pywebview triggers this when the native window is actually closed.
        self._chat_window = None

    def open_chat(self):
        import webview

        if self._chat_window is not None:
            # If user closed the window via the title-bar, pywebview keeps the Python object,
            # but the native window is gone. The closed event is set in that case.
            try:
                if getattr(self._chat_window, "events", None) and self._chat_window.events.closed.is_set():
                    self._chat_window = None
                else:
                    _safe_call(self._chat_window, "show")
                    _safe_call(self._chat_window, "restore")
                    _safe_call(self._chat_window, "bring_to_front")
                    return True
            except Exception:
                self._chat_window = None

        chat_url = self.base_url
        sep = "&" if "?" in chat_url else "?"
        chat_url = f"{chat_url}{sep}desktop=1"

        self._chat_window = webview.create_window(
            title="Agent Chat",
            url=chat_url,
            width=self.chat_width,
            height=self.chat_height,
            resizable=True,
            on_top=self.chat_topmost,
        )
        try:
            self._chat_window.events.closed += self._on_chat_closed
        except Exception:
            # Best-effort; if events are not available in some backend, reopening is still handled above.
            pass
        return True

    def close_chat(self):
        if self._chat_window is None:
            return True
        _safe_call(self._chat_window, "destroy")
        self._chat_window = None
        return True

    def toggle_chat(self):
        if self._chat_window is None:
            return self.open_chat()

        if _safe_call(self._chat_window, "hide") is not None:
            return True
        _safe_call(self._chat_window, "minimize")
        return True


def _ball_html(base_url: str, size: int) -> str:
    icon_url = urljoin(base_url.rstrip("/") + "/", "static/icons/aifrac.png")
    return f"""<!doctype html>
<html lang=\"zh-CN\">
<head>
  <meta charset=\"utf-8\"/>
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\"/>
  <title>Agent</title>
  <style>
    :root {{ color-scheme: dark; }}
        html, body {{ width: 100%; height: 100%; margin: 0; background: transparent; overflow: hidden; }}
        body {{ display: flex; align-items: center; justify-content: center; }}
        .ball {{
            width: 100%; height: 100%;
            border-radius: 50%;
            overflow: hidden;
            background: rgba(22, 26, 34, 0.92);
            border: 1px solid rgba(34, 39, 55, 0.95);
            display: flex; align-items: center; justify-content: center;
            box-shadow: 0 10px 30px rgba(0,0,0,.35);
            user-select: none;
            cursor: pointer;
        }}
        .ball:active {{ transform: scale(0.98); }}
        img {{ width: {int(size*0.64)}px; height: {int(size*0.64)}px; border-radius: 10px; object-fit: contain; }}
  </style>
</head>
<body>
  <div class=\"ball\" id=\"ball\" title=\"点击打开聊天\">
    <img src=\"{icon_url}\" alt=\"Aifrac\" />
  </div>
  <script>
    function ready(fn) {{
      if (document.readyState !== 'loading') fn();
      else document.addEventListener('DOMContentLoaded', fn);
    }}
    ready(() => {{
      const el = document.getElementById('ball');
      el.addEventListener('click', async () => {{
        if (window.pywebview && window.pywebview.api) {{
          try {{ await window.pywebview.api.open_chat(); }} catch (e) {{ console.error(e); }}
        }}
      }});
    }});
  </script>
</body>
</html>"""


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Launch a floating-ball desktop shell. Click the ball to open the chat popup (wraps existing Flask UI)."
    )
    parser.add_argument("--url", default="http://127.0.0.1:5001/", help="Flask UI URL")
    parser.add_argument("--wait", type=float, default=10.0, help="Seconds to wait for Flask to be ready")

    parser.add_argument("--ball-size", type=int, default=44)
    parser.add_argument(
        "--gui",
        default="qt",
        choices=["qt", "winforms"],
        help="pywebview GUI backend. Use 'qt' for better transparency on Windows (requires PyQt6).",
    )
    parser.add_argument("--chat-width", type=int, default=420)
    parser.add_argument("--chat-height", type=int, default=720)
    parser.add_argument("--chat-topmost", action="store_true")
    args = parser.parse_args()

    base_url = args.url

    if args.wait and args.wait > 0:
        ok = wait_for_server(base_url, timeout_s=args.wait)
        if not ok:
            print(f"Flask not reachable at {base_url}. Please start start.py first.", file=sys.stderr)
            return 2

    try:
        import webview  # pywebview
    except Exception as e:
        print(
            "pywebview is not installed or not available.\n"
            "Install it in the current venv: python -m pip install pywebview\n"
            f"Details: {e}",
            file=sys.stderr,
        )
        return 3

    api = DesktopApi(
        base_url=base_url,
        chat_width=args.chat_width,
        chat_height=args.chat_height,
        chat_topmost=args.chat_topmost,
    )

    webview.create_window(
        title="Agent",
        html=_ball_html(base_url, args.ball_size),
        width=args.ball_size,
        height=args.ball_size,
        resizable=False,
        frameless=True,
        easy_drag=True,
        on_top=True,
        js_api=api,
        background_color="#000000",
        transparent=True,
    )

    # Prefer Qt backend for transparent windows on Windows.
    webview.start(gui=args.gui)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
