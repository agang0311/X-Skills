#!/usr/bin/env python3
"""
Chrome launcher for XSkills.

Starts a Chrome instance with CDP (Chrome DevTools Protocol) enabled
for Twitter automation.

Usage:
    python chrome_launcher.py                    # Start with window
    python chrome_launcher.py --headless         # Start headless
    python chrome_launcher.py --port 9223        # Specify port
    python chrome_launcher.py --restart          # Restart existing
    python chrome_launcher.py --kill             # Kill existing
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# Configuration
DEFAULT_PORT = 9222
USER_DATA_DIR = Path.home() / ".xskills" / "chrome-profile"


def is_chrome_running(port: int = DEFAULT_PORT) -> bool:
    """Check if Chrome with CDP is already running on the specified port."""
    try:
        result = subprocess.run(
            ["lsof", "-i", f":{port}"],
            capture_output=True,
            text=True
        )
        return "Chrome" in result.stdout
    except Exception:
        return False


def kill_chrome(port: int = DEFAULT_PORT) -> bool:
    """Kill Chrome process running on the specified port."""
    try:
        # Find PID
        result = subprocess.run(
            ["lsof", "-t", "-i", f":{port}"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            pids = result.stdout.strip().split("\n")
            for pid in pids:
                subprocess.run(["kill", "-9", pid], check=True)
            print(f"✅ Chrome on port {port} killed")
            return True
        else:
            print(f"ℹ️  No Chrome running on port {port}")
            return False
    except Exception as e:
        print(f"❌ Failed to kill Chrome: {e}")
        return False


def start_chrome(
    port: int = DEFAULT_PORT,
    headless: bool = False,
    user_data_dir: Path = None
) -> bool:
    """Start Chrome with CDP enabled."""
    
    if user_data_dir is None:
        user_data_dir = USER_DATA_DIR
    
    # Create user data directory
    user_data_dir.mkdir(parents=True, exist_ok=True)
    
    # Chrome command
    chrome_cmd = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        f"--remote-debugging-port={port}",
        f"--user-data-dir={user_data_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--hide-crash-restore-bubble",
    ]
    
    if headless:
        chrome_cmd.append("--headless=new")
    
    print(f"🚀 Starting Chrome (port={port}, headless={headless})...")
    print(f"📁 User data: {user_data_dir}")
    
    try:
        # Start Chrome in background
        subprocess.Popen(
            chrome_cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        # Wait for Chrome to start
        print("⏳ Waiting for Chrome to start...")
        time.sleep(3)
        
        # Verify Chrome is running
        if is_chrome_running(port):
            print(f"✅ Chrome started successfully on port {port}")
            return True
        else:
            print(f"❌ Chrome failed to start on port {port}")
            return False
            
    except Exception as e:
        print(f"❌ Failed to start Chrome: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Chrome launcher for XSkills"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"CDP port (default: {DEFAULT_PORT})"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run in headless mode"
    )
    parser.add_argument(
        "--restart",
        action="store_true",
        help="Restart existing Chrome instance"
    )
    parser.add_argument(
        "--kill",
        action="store_true",
        help="Kill existing Chrome instance"
    )
    
    args = parser.parse_args()
    
    # Handle kill command
    if args.kill:
        kill_chrome(args.port)
        return
    
    # Handle restart command
    if args.restart:
        print("🔄 Restarting Chrome...")
        kill_chrome(args.port)
        time.sleep(1)
    
    # Check if Chrome is already running
    if is_chrome_running(args.port):
        print(f"ℹ️  Chrome already running on port {args.port}")
        print(f"💡 Use --restart to restart or --kill to stop")
        return
    
    # Start Chrome
    start_chrome(
        port=args.port,
        headless=args.headless
    )


if __name__ == "__main__":
    main()
