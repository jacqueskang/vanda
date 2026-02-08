#!/usr/bin/env python3
"""
Start the web UI server and automatically open it in your default browser.
Usage: python scripts/start_web_ui.py
"""

import os
import sys
import webbrowser
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from functools import partial

PORT = 8000
HOST = "127.0.0.1"
ROOT_DIR = Path(__file__).resolve().parents[1]
WEB_DIR = ROOT_DIR / "web"


class WebUIHandler(SimpleHTTPRequestHandler):
    """Serve index.html as the default page."""

    def do_GET(self):
        # Serve the main UI directly to avoid directory issues.
        if self.path in ("/", "", "/index.html"):
            try:
                content = (WEB_DIR / "index.html").read_bytes()
            except Exception as e:
                self.send_error(404, str(e))
                return

            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        if self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        self.send_error(404, "Not found")
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        if "GET" in format or "POST" in format:
            print(f"[*] {format % args}")


def start_server():
    """Start the HTTP server."""
    server = HTTPServer((HOST, PORT), WebUIHandler)
    print(f"[+] Starting web UI server on http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[-] Shutting down server...")
        server.shutdown()


def main(skip_browser=False):
    # Check if index.html exists
    ui_file = WEB_DIR / "index.html"
    if not ui_file.exists():
        print("Error: index.html not found in web/ directory")
        print(f"Expected path: {ui_file}")
        sys.exit(1)
    
    # Start server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait a moment for server to start
    time.sleep(0.5)
    
    # Open in browser (unless skipped)
    url = f"http://{HOST}:{PORT}"
    if not skip_browser:
        print(f"[+] Opening browser at {url}...")
        webbrowser.open(url)
    
    print(f"\n============================================================")
    print(f"[*] Web UI Server Running")
    print(f"============================================================")
    print(f"[+] URL: {url}")
    print(f"[+] Press Ctrl+C to stop server")
    print(f"============================================================\n")
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[+] Server stopped")
        sys.exit(0)


if __name__ == "__main__":
    skip_browser = "--no-browser" in sys.argv or os.environ.get("SKIP_BROWSER")
    main(skip_browser=skip_browser)
