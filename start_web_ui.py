#!/usr/bin/env python3
"""
Start the web UI server and automatically open it in your default browser.
Usage: python start_web_ui.py
"""

import os
import sys
import webbrowser
import threading
import time
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

PORT = 8000
HOST = "127.0.0.1"


class WebUIHandler(SimpleHTTPRequestHandler):
    """Serve web_ui.html as the default page."""
    
    def do_GET(self):
        # Serve web_ui.html for root path
        if self.path == "/" or self.path == "":
            self.path = "/web_ui.html"
        
        try:
            return super().do_GET()
        except Exception as e:
            self.send_error(404, str(e))
    
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
    # Check if web_ui.html exists
    if not os.path.exists("web_ui.html"):
        print("Error: web_ui.html not found in current directory")
        print(f"Current directory: {os.getcwd()}")
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
