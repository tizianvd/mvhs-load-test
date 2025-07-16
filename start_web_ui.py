#!/usr/bin/env python3
"""
Quick start script for MVHS Load Testing with Locust Web UI.

This script provides an easy way to start the Locust web interface
for interactive load testing of the MVHS website.
"""

import os
import sys
import subprocess
import webbrowser
from pathlib import Path
import multiprocessing

def check_dependencies():
    """Check if required dependencies are installed."""
    required_modules = [
        'locust',
        'requests', 
        'bs4',  # beautifulsoup4 
        'pandas',
        'matplotlib'
    ]
    
    missing_modules = []
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            missing_modules.append(module)
    
    if missing_modules:
        print("❌ Missing required dependencies:")
        for module in missing_modules:
            print(f"   - {module}")
        print("\n💡 To install dependencies, run:")
        print("   pip install --user -r requirements.txt")
        return False
    
    return True

def main():
    """Start the Locust web UI for interactive load testing."""
    
    print("🌐 MVHS Load Testing - Locust Web UI Launcher")
    print("="*50)
    
    # Check if we're in the right directory
    if not Path("locustfile.py").exists():
        print("❌ Error: locustfile.py not found!")
        print("   Please run this script from the project root directory.")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Default configuration
    host = "0.0.0.0"
    port = 8080
    target_url = "https://www.mvhs.de"
    processes = multiprocessing.cpu_count()  # Use all available CPU cores
    
    # Build the Locust command
    cmd = [
        "python3", "-m", "locust",
        "--web-host", host,
        "--web-port", str(port),
        "--host", target_url,
        "--processes", str(processes)
    ]
    
    print(f"🚀 Starting Locust Web UI...")
    print(f"📊 Web Interface: http://localhost:{port}")
    print(f"🎯 Target URL: {target_url}")
    print(f"⚡ Processes: {processes} (using all CPU cores)")
    print(f"💻 Command: {' '.join(cmd)}")
    print()
    print("🎯 Instructions:")
    print("   1. Wait for the web interface to start")
    print("   2. Open your browser to the URL above")
    print("   3. Configure your test parameters:")
    print("      - Number of users (start with 10-50)")
    print("      - Spawn rate (start with 2-5 users/sec)")
    print("      - Host URL (pre-configured)")
    print("   4. Click 'Start swarming' to begin the test")
    print()
    print("🛑 Press Ctrl+C to stop the web server")
    print("="*50)
    
    try:
        # Try to open browser automatically after a short delay
        import threading
        def open_browser():
            import time
            time.sleep(3)  # Wait 3 seconds for server to start
            try:
                webbrowser.open(f"http://localhost:{port}")
                print(f"🌐 Opened browser to http://localhost:{port}")
            except:
                pass  # Fail silently if browser can't be opened
        
        # Start browser opener in background
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # Start Locust
        subprocess.run(cmd)
        
    except KeyboardInterrupt:
        print("\n🛑 Shutting down Locust Web UI...")
    except FileNotFoundError:
        print("❌ Error: Python or Locust not found!")
        print("   Please ensure Python is installed and Locust is available:")
        print("   pip install locust")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
