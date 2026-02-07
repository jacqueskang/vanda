#!/usr/bin/env python3
"""
All-in-one launcher: Start business team + web UI with one command
Usage: python run.py
"""

import os
import sys
import subprocess
import time
import webbrowser
import signal
from pathlib import Path


def _pick_python() -> str:
    venv_python = Path("venv") / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    try:
        if venv_python.exists():
            return str(venv_python.resolve())
    except Exception:
        pass
    return sys.executable


def _print_log_tail(log_path: Path, lines: int = 40) -> None:
    if not log_path.exists():
        return
    try:
        content = log_path.read_text(encoding="utf-8", errors="ignore").splitlines()
        tail = content[-lines:] if len(content) > lines else content
        if tail:
            print(f"\n--- {log_path.name} (last {len(tail)} lines) ---")
            for line in tail:
                print(line)
    except Exception:
        return


def main():
    print("=" * 60)
    print("[*] AI BUSINESS TEAM - Full Stack Launcher")
    print("=" * 60)
    
    # Check if required files exist
    required_files = ["business_team.py", "web_ui.html", "start_web_ui.py"]
    for filename in required_files:
        if not os.path.exists(filename):
            print(f"[-] Error: {filename} not found")
            sys.exit(1)
    
    print("[+] Required files found")
    print()
    
    python_cmd = _pick_python()

    business_log = Path("business_team.log")
    webui_log = Path("web_ui.log")

    # Start business_team.py
    print("[*] Starting business team backend...")
    try:
        business_log_fp = business_log.open("w", encoding="utf-8")
        business_team_proc = subprocess.Popen(
            [python_cmd, "business_team.py"],
            stdout=business_log_fp,
            stderr=business_log_fp,
            stdin=subprocess.DEVNULL
        )
        print("[+] Business team started")
    except Exception as e:
        print(f"[-] Failed to start business team: {e}")
        sys.exit(1)
    
    time.sleep(3)
    
    # Start web UI
    print("[*] Starting web UI server...")
    try:
        webui_log_fp = webui_log.open("w", encoding="utf-8")
        web_ui_proc = subprocess.Popen(
            [python_cmd, "start_web_ui.py", "--no-browser"],
            stdout=webui_log_fp,
            stderr=webui_log_fp,
            stdin=subprocess.DEVNULL
        )
        print("[+] Web UI started")
    except Exception as e:
        print(f"[-] Failed to start web UI: {e}")
        business_team_proc.terminate()
        try:
            business_log_fp.close()
        except Exception:
            pass
        sys.exit(1)
    
    time.sleep(1)
    
    print()
    print("=" * 60)
    print("[+] BOTH SERVERS RUNNING!")
    print("=" * 60)
    print("[*] Business Team: http://127.0.0.1:8088")
    print("[*] Web UI: http://127.0.0.1:8000")
    print()
    print("[+] Browser should open automatically...")
    print("[+] Press Ctrl+C to stop all servers")
    print("=" * 60)
    print()
    
    # Open browser
    webbrowser.open("http://127.0.0.1:8000")
    
    # Wait for processes
    def signal_handler(sig, frame):
        print("\n[*] Shutting down...")
        business_team_proc.terminate()
        web_ui_proc.terminate()
        
        try:
            business_team_proc.wait(timeout=3)
        except:
            business_team_proc.kill()
        
        try:
            web_ui_proc.wait(timeout=3)
        except:
            web_ui_proc.kill()
        
        try:
            business_log_fp.close()
            webui_log_fp.close()
        except Exception:
            pass
        print("[+] All servers stopped")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Keep running
    try:
        while True:
            if business_team_proc.poll() is not None:
                print("[-] Business team process ended")
                _print_log_tail(business_log)
                web_ui_proc.terminate()
                sys.exit(1)
            
            if web_ui_proc.poll() is not None:
                print("[-] Web UI process ended")
                _print_log_tail(webui_log)
                business_team_proc.terminate()
                sys.exit(1)
            
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()
