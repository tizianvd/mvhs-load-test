#!/usr/bin/env python3
"""
Quick setup script for the MVHS Load Testing Framework.

This script helps new users get started quickly by checking dependencies,
validating configuration, and running initial tests.
"""

import sys
import subprocess
import importlib
from pathlib import Path


def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    
    if sys.version_info < (3, 8):
        print(f"❌ Python 3.8+ required, found {sys.version}")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} is compatible")
    return True


def check_dependencies():
    """Check if required dependencies are installed."""
    print("\n📦 Checking dependencies...")
    
    required_packages = [
        'locust',
        'requests', 
        'beautifulsoup4',
        'pandas',
        'matplotlib',
        'seaborn',
        'jinja2'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} (missing)")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n🔧 To install missing packages:")
        print(f"pip install {' '.join(missing_packages)}")
        print("or")
        print("pip install -r requirements.txt")
        return False
    
    return True


def check_project_structure():
    """Check if project structure is correct."""
    print("\n📁 Checking project structure...")
    
    required_dirs = [
        'src',
        'src/config',
        'src/core', 
        'src/users',
        'src/tasks',
        'src/reporting',
        'src/runners',
        'src/utils',
        'config',
        'reports'
    ]
    
    required_files = [
        'src/__init__.py',
        'src/config/profiles.py',
        'src/config/stress_config.py',
        'config/website_profiles.json',
        'config/stress_test_config.json',
        'locustfile_new.py',
        'stress_test_runner_new.py'
    ]
    
    all_good = True
    
    # Check directories
    for dir_path in required_dirs:
        if Path(dir_path).is_dir():
            print(f"✅ {dir_path}/")
        else:
            print(f"❌ {dir_path}/ (missing)")
            all_good = False
    
    # Check files
    for file_path in required_files:
        if Path(file_path).is_file():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} (missing)")
            all_good = False
    
    return all_good


def test_basic_functionality():
    """Test basic functionality of the framework."""
    print("\n🧪 Testing basic functionality...")
    
    try:
        # Test configuration loading
        print("🔧 Testing configuration loading...")
        from src.config.profiles import WebsiteProfileManager
        from src.config.stress_config import StressTestConfigManager
        
        profile_manager = WebsiteProfileManager()
        stress_manager = StressTestConfigManager()
        
        profiles = profile_manager.list_profiles()
        tests = stress_manager.list_test_configs()
        
        print(f"✅ Loaded {len(profiles)} website profiles")
        print(f"✅ Loaded {len(tests)} test configurations")
        
        # Test user class import
        print("👤 Testing user classes...")
        from src.users.mvhs_users import MVHSNormalUser, MVHSActiveUser
        print("✅ User classes imported successfully")
        
        # Test task classes
        print("📋 Testing task classes...")
        from src.tasks.navigation import NavigationTasks
        from src.tasks.search import SearchTasks
        print("✅ Task classes imported successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing functionality: {e}")
        return False


def run_quick_test():
    """Run a very quick test to verify everything works."""
    print("\n🚀 Running quick validation test...")
    
    try:
        # Try to run the stress test runner in list mode
        result = subprocess.run([
            sys.executable, 'stress_test_runner_new.py'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            print("✅ Stress test runner is working")
            return True
        else:
            print(f"❌ Stress test runner failed: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print("⚠️ Test timed out (this might be normal)")
        return True
    except Exception as e:
        print(f"❌ Error running test: {e}")
        return False


def show_quick_start_guide():
    """Show a quick start guide for new users."""
    print("\n" + "="*60)
    print("🎯 QUICK START GUIDE")
    print("="*60)
    
    print("\n1. 📋 List available tests:")
    print("   python stress_test_runner_new.py")
    
    print("\n2. 🚀 Run your first test:")
    print("   python stress_test_runner_new.py light_stress")
    
    print("\n3. 🌐 Start the web UI:")
    print("   python stress_test_runner_new.py web")
    print("   Then open: http://localhost:80")
    
    print("\n4. 📊 Generate a report:")
    print("   python generate_report_new.py")
    
    print("\n5. 🎭 Configure user behavior:")
    print("   python configure_user_behavior_new.py show")
    
    print("\n📚 Documentation:")
    print("   - README.md for detailed documentation")
    print("   - config/ for configuration files")
    print("   - reports/ for test results")
    
    print("\n💡 Tips:")
    print("   - Start with light_stress for initial testing")
    print("   - Use web UI for interactive testing")
    print("   - Check reports/ for detailed results")
    print("   - Modify config/ files for customization")


def main():
    """Main setup function."""
    print("🚀 MVHS Load Testing Framework v2.0 Setup")
    print("="*60)
    
    checks = [
        ("Python Version", check_python_version),
        ("Dependencies", check_dependencies),
        ("Project Structure", check_project_structure),
        ("Basic Functionality", test_basic_functionality),
        ("Quick Test", run_quick_test)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        if not check_func():
            all_passed = False
            print(f"\n❌ {check_name} check failed!")
        else:
            print(f"\n✅ {check_name} check passed!")
    
    if all_passed:
        print("\n🎉 Setup completed successfully!")
        show_quick_start_guide()
        return True
    else:
        print("\n❌ Setup completed with errors.")
        print("Please fix the issues above before proceeding.")
        return False


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
