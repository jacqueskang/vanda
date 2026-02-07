#!/usr/bin/env python3
"""
All-in-one launcher: Start business team + web UI with one command
Usage: python scripts/run.py
"""

import os
import sys
import subprocess
import time
import webbrowser
import signal
from pathlib import Path


def _pick_python(project_root: Path) -> str:
    venv_python = project_root / "venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
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
    
    project_root = Path(__file__).resolve().parents[1]
    scripts_dir = project_root / "scripts"
    web_dir = project_root / "web"

    # Check if required files exist
    required_files = [
        scripts_dir / "business_team.py",
        web_dir / "web_ui.html",
    ]
    for file_path in required_files:
        if not file_path.exists():
            print(f"[-] Error: {file_path} not found")
            sys.exit(1)
    
    print("[+] Required files found")
    print()
    
    python_cmd = _pick_python(project_root)

    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    business_log = logs_dir / "business_team.log"

    # Start business_team.py
    print("[*] Starting business team backend...")
    try:
        business_log_fp = business_log.open("w", encoding="utf-8")
        business_team_proc = subprocess.Popen(
            [python_cmd, str(scripts_dir / "business_team.py")],
            stdout=business_log_fp,
            stderr=business_log_fp,
            stdin=subprocess.DEVNULL,
            cwd=str(project_root),
        )
        print("[+] Business team started")
    except Exception as e:
        print(f"[-] Failed to start business team: {e}")
        sys.exit(1)
    
    time.sleep(3)
    
    print()
    print("=" * 60)
    print("[+] SERVER RUNNING!")
    print("=" * 60)
    print("[*] Business Team: http://127.0.0.1:8088")
    print("[*] Web UI: http://127.0.0.1:8088/")
    print()
    print("[+] Browser should open automatically...")
    print("[+] Press Ctrl+C to stop all servers")
    print("=" * 60)
    print()
    
    # Open browser (with graceful fallback if not available)
    try:
        webbrowser.open("http://127.0.0.1:8088/")
    except Exception:
        pass
    
    # Wait for processes
    def signal_handler(sig, frame):
        print("\n[*] Shutting down...")
        business_team_proc.terminate()
        
        try:
            business_team_proc.wait(timeout=3)
        except:
            business_team_proc.kill()
        
        try:
            business_log_fp.close()
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
                sys.exit(1)
            
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()
