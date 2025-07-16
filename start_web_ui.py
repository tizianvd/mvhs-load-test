#!/usr/bin/env python3
"""
MVHS Load Test - Enhanced Web UI Launcher (Python)
Cross-platform launcher for enhanced web mode
"""

import os
import sys
import subprocess
import time
import webbrowser
from pathlib import Path

def print_colored(text, color_code=None):
    """Print colored text (ANSI colors)"""
    if color_code:
        print(f"\033[{color_code}m{text}\033[0m")
    else:
        print(text)

def check_python():
    """Check Python version"""
    version = sys.version
    print_colored(f"✅ Found: Python {version.split()[0]}", "32")
    return True

def check_locust():
    """Check if Locust is installed"""
    try:
        import locust
        print_colored("✅ Locust is installed and ready!", "32")
        return True
    except ImportError:
        print_colored("❌ Locust not found! Installing requirements...", "33")
        return install_requirements()

def install_requirements():
    """Install requirements from requirements.txt"""
    requirements_file = Path("requirements.txt")
    
    if requirements_file.exists():
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                         check=True, capture_output=True)
            print_colored("✅ Requirements installed successfully!", "32")
            return True
        except subprocess.CalledProcessError:
            print_colored("❌ Failed to install requirements! Please run: pip install -r requirements.txt", "31")
            return False
    else:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "locust"], 
                         check=True, capture_output=True)
            print_colored("✅ Locust installed successfully!", "32")
            return True
        except subprocess.CalledProcessError:
            print_colored("❌ Failed to install Locust! Please run: pip install locust", "31")
            return False

def setup_environment():
    """Set up environment variables"""
    os.environ["TEST_MODE"] = "realistic"
    os.environ["USER_BEHAVIOR"] = "realistic"
    os.environ["WEBSITE_PROFILE"] = "mvhs_production"
    
    print_colored("🎛️ Environment configured for enhanced web mode:", "36")
    print_colored(f"   Test Mode: {os.environ['TEST_MODE']}", "37")
    print_colored(f"   User Behavior: {os.environ['USER_BEHAVIOR']}", "37")
    print_colored(f"   Website Profile: {os.environ['WEBSITE_PROFILE']}", "37")

def create_directories():
    """Create necessary directories"""
    reports_dir = Path("reports")
    logs_dir = reports_dir / "logs"
    
    reports_dir.mkdir(exist_ok=True)
    logs_dir.mkdir(exist_ok=True)
    
    if not reports_dir.exists():
        print_colored("📁 Created reports directory", "37")
    if not logs_dir.exists():
        print_colored("📁 Created logs directory", "37")

def open_browser_delayed():
    """Open browser after a delay"""
    time.sleep(3)
    try:
        webbrowser.open("http://localhost:8089")
        print_colored("🌐 Browser opened automatically!", "32")
    except Exception:
        print_colored("💡 Please manually open: http://localhost:8089", "33")

def print_banner():
    """Print startup banner"""
    print()
    print_colored("=" * 60, "36")
    print_colored("🚀 MVHS Load Test - Enhanced Web UI Launcher", "33")
    print_colored("=" * 60, "36")
    print()

def print_instructions():
    """Print usage instructions"""
    print()
    print_colored("🌐 Web Interface will be available at:", "33")
    print_colored("   📍 Main Dashboard: http://localhost:8089", None)
    print_colored("   🎯 Enhanced Dashboard: http://localhost:8089/test-dashboard", None)
    print_colored("   🔄 Profile Selector: http://localhost:8089/profile-selector", None)
    print_colored("   ⚙️ Configuration: http://localhost:8089/test-config", None)
    print_colored("   📊 Live API Stats: http://localhost:8089/api/stats", None)
    print()
    print_colored("💡 Quick Start Guide:", "33")
    print_colored("   1. Open http://localhost:8089 in your browser", "37")
    print_colored("   2. Set Number of users: 10-20 for testing", "37")
    print_colored("   3. Set Spawn rate: 2 users per second", "37")
    print_colored("   4. Click 'Start Test' and monitor the live charts", "37")
    print_colored("   5. Use the floating widgets for quick configuration", "37")
    print()
    print_colored("🔥 Enhanced Web Features:", "35")
    print_colored("   ✨ Real-time profile switching without restart", "37")
    print_colored("   ⚡ Live behavior configuration (realistic/fast/stress/mobile)", "37")
    print_colored("   📊 Enhanced analytics and reporting", "37")
    print_colored("   📱 Mobile-responsive interface", "37")
    print_colored("   🎯 Floating control widgets", "37")
    print_colored("   📈 Real-time statistics API", "37")
    print()

def main():
    """Main launcher function"""
    print_banner()
    
    # Check prerequisites
    if not check_python():
        sys.exit(1)
    
    if not check_locust():
        sys.exit(1)
    
    print()
    
    # Setup environment
    setup_environment()
    create_directories()
    
    print()
    print_instructions()
    
    # Open browser in background
    import threading
    browser_thread = threading.Thread(target=open_browser_delayed, daemon=True)
    browser_thread.start()
    
    print_colored("🚀 Launching Locust Web UI...", "32")
    print_colored("   (Press Ctrl+C to stop the server)", "37")
    print()
    
    # Generate log filename
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = f"reports/logs/locust_web_{timestamp}.log"
    print_colored(f"📝 Logging to: {log_file}", "37")
    
    try:
        # Start Locust
        subprocess.run([
            sys.executable, "-m", "locust",
            "--web-host=0.0.0.0",
            "--web-port=8089",
            f"--logfile={log_file}"
        ])
    except KeyboardInterrupt:
        print()
        print_colored("⚠️ Locust was interrupted", "33")
    except Exception as e:
        print()
        print_colored(f"❌ Error starting Locust: {e}", "31")
    finally:
        print()
        print_colored("🏁 Locust Web UI session ended.", "36")
        print_colored("📊 Check reports/ folder for detailed test results.", "37")
        print()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
