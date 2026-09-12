"""Desktop launcher and entrypoint for Local Document Signer.

Provides automatic port selection, a native companion control window,
automatic browser launch, and graceful shutdown.
"""

import argparse
from pathlib import Path
import socket
import sys
import threading
import time
import webbrowser

# Special handling for frozen word conversion subprocess
if len(sys.argv) > 1 and sys.argv[1] == "--convert-word":
    from word_conversion import run_word
    run_word(*sys.argv[2:])
    sys.exit(0)

# Attach to parent console if available (allows CLI output even in windowed PE mode)
if sys.platform == "win32":
    try:
        import ctypes
        if ctypes.windll.kernel32.AttachConsole(-1):
            # Reopen stdout/stderr to parent console
            sys.stdout = open("CONOUT$", "w", encoding="utf-8", errors="replace")
            sys.stderr = open("CONOUT$", "w", encoding="utf-8", errors="replace")
    except Exception:
        pass

from werkzeug.serving import make_server
from app import app, get_bundle_dir


def find_free_port(start_port=5050, max_attempts=50):
    """Find the first available port on 127.0.0.1 starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                probe.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    raise RuntimeError(f"Could not find an available port in range {start_port}-{start_port + max_attempts}.")


class ServerThread(threading.Thread):
    """Run Werkzeug server in a background daemon thread."""

    def __init__(self, host, port):
        super().__init__(daemon=True)
        self.host = host
        self.port = port
        self.server = make_server(host, port, app, threaded=True)
        self._is_running = True

    def run(self):
        try:
            self.server.serve_forever()
        except Exception:
            pass
        finally:
            self._is_running = False

    def shutdown(self):
        if self._is_running:
            self.server.shutdown()
            self._is_running = False


def launch_gui(url, server_thread):
    """Create a polished native companion window using Tkinter."""
    import tkinter as tk
    from tkinter import ttk

    root = tk.Tk()
    root.title("Local Document Signer")
    root.geometry("450x330")
    root.minsize(420, 310)
    root.configure(bg="#f5f5f7")

    # Try setting window icon
    bundle_dir = get_bundle_dir()
    for icon_name in ("app_icon.ico", "app_icon.png"):
        icon_path = bundle_dir / icon_name
        if not icon_path.is_file():
            icon_path = Path(__file__).resolve().parent / icon_name
        if icon_path.is_file():
            try:
                if icon_path.suffix == ".ico":
                    root.iconbitmap(str(icon_path))
                break
            except Exception:
                pass

    # Center window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f"{width}x{height}+{x}+{y}")

    # Top container
    content = tk.Frame(root, bg="#f5f5f7", padx=24, pady=20)
    content.pack(fill="both", expand=True)

    # Header section
    title_label = tk.Label(
        content,
        text="Local Document Signer",
        font=("Segoe UI", 15, "bold"),
        fg="#1d1d1f",
        bg="#f5f5f7",
    )
    title_label.pack(anchor="w")

    subtitle_label = tk.Label(
        content,
        text="Secure in-browser document signing on your computer",
        font=("Segoe UI", 9),
        fg="#6e6e73",
        bg="#f5f5f7",
    )
    subtitle_label.pack(anchor="w", pady=(2, 14))

    # Status Card Frame
    card = tk.Frame(content, bg="#ffffff", bd=1, relief="solid", padx=16, pady=14)
    card.configure(highlightbackground="#e5e5ea", highlightthickness=1)
    card.pack(fill="x", pady=(0, 16))

    # Status indicator row
    status_row = tk.Frame(card, bg="#ffffff")
    status_row.pack(fill="x")

    badge = tk.Label(
        status_row,
        text="● Active",
        font=("Segoe UI", 9, "bold"),
        fg="#34c759",
        bg="#f0fdf4",
        padx=8,
        pady=2,
    )
    badge.pack(side="left")

    url_display = tk.Label(
        card,
        text=url,
        font=("Consolas", 11, "bold"),
        fg="#1d1d1f",
        bg="#ffffff",
    )
    url_display.pack(anchor="w", pady=(10, 0))

    # Action Buttons
    button_row = tk.Frame(content, bg="#f5f5f7")
    button_row.pack(fill="x", pady=(0, 14))

    def open_browser():
        webbrowser.open(url)

    def copy_url():
        root.clipboard_clear()
        root.clipboard_append(url)
        copy_btn.config(text="Copied!")
        root.after(1800, lambda: copy_btn.config(text="Copy URL"))

    def close_app():
        server_thread.shutdown()
        root.destroy()

    open_btn = tk.Button(
        button_row,
        text="🌐 Open in Browser",
        font=("Segoe UI", 9, "bold"),
        bg="#0071e3",
        fg="#ffffff",
        activebackground="#0077ed",
        activeforeground="#ffffff",
        relief="flat",
        padx=12,
        pady=7,
        cursor="hand2",
        command=open_browser,
    )
    open_btn.pack(side="left", fill="x", expand=True, padx=(0, 6))

    copy_btn = tk.Button(
        button_row,
        text="Copy URL",
        font=("Segoe UI", 9),
        bg="#ffffff",
        fg="#1d1d1f",
        activebackground="#f5f5f7",
        activeforeground="#1d1d1f",
        relief="groove",
        padx=10,
        pady=7,
        cursor="hand2",
        command=copy_url,
    )
    copy_btn.pack(side="left", padx=3)

    stop_btn = tk.Button(
        button_row,
        text="Stop & Exit",
        font=("Segoe UI", 9),
        bg="#fee2e2",
        fg="#ff3b30",
        activebackground="#fecaca",
        activeforeground="#d70015",
        relief="flat",
        padx=10,
        pady=7,
        cursor="hand2",
        command=close_app,
    )
    stop_btn.pack(side="right", padx=(6, 0))

    # Privacy Guarantee Footer
    footer = tk.Label(
        content,
        text="🔒 100% Private: All processing is local. No documents leave your PC.",
        font=("Segoe UI", 8),
        fg="#86868b",
        bg="#f5f5f7",
    )
    footer.pack(side="bottom", anchor="center")

    root.protocol("WM_DELETE_WINDOW", close_app)
    root.mainloop()


def main():
    parser = argparse.ArgumentParser(description="Local Document Signer")
    parser.add_argument("--port", type=int, default=0, help="Port to listen on (default: auto-detect 5050+)")
    parser.add_argument("--cli", action="store_true", help="Run in command line mode without desktop companion window")
    parser.add_argument("--no-browser", action="store_true", help="Do not open browser automatically on launch")
    args = parser.parse_args()

    port = args.port if args.port > 0 else find_free_port(5050)
    host = "127.0.0.1"
    url = f"http://{host}:{port}"

    server_thread = ServerThread(host, port)
    server_thread.start()

    print(f"\n==========================================")
    print(f"  Local Document Signer is running!")
    print(f"  URL: {url}")
    print(f"==========================================\n")

    if not args.no_browser:
        # Give server a moment to start before opening browser
        threading.Timer(0.4, lambda: webbrowser.open(url)).start()

    if args.cli:
        print("Running in CLI mode. Press Ctrl+C to terminate.")
        try:
            while server_thread.is_alive():
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            server_thread.shutdown()
            server_thread.join(timeout=2)
            print("Server stopped.")
    else:
        try:
            launch_gui(url, server_thread)
        except Exception as e:
            # Fallback to CLI if GUI fails (e.g. headless environment)
            print(f"Desktop GUI unavailable ({e}). Running in CLI mode.")
            try:
                while server_thread.is_alive():
                    time.sleep(0.5)
            except KeyboardInterrupt:
                pass
            finally:
                server_thread.shutdown()
                server_thread.join(timeout=2)


if __name__ == "__main__":
    main()
