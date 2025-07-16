#!/usr/bin/env python3
"""
Main Locust entry point for MVHS Load Testing.

This is the main locustfile that Locust will use to run load tests.
It imports and configures all the user classes and test scenarios.
"""

import os
import sys
from pathlib import Path

# Add src directory to Python path for imports
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Import user classes
from src.users.mvhs_users import (
    MVHSNormalUser,
    MVHSActiveUser,
    MVHSPowerUser,
    MVHSBrowserUser,
    MVHSMobileUser,
    MVHSWebsiteUser  # Legacy compatibility
)

# Import configuration managers
from src.config.profiles import WebsiteProfileManager
from src.config.stress_config import StressTestConfigManager

# Import core components
from src.core.metrics import MetricsCollector

# Initialize global components
print("🚀 Initializing MVHS Load Testing Framework...")

# Initialize configuration managers
profile_manager = WebsiteProfileManager()
stress_config_manager = StressTestConfigManager()

# Display active configuration
try:
    active_profile = profile_manager.get_active_profile()
    print(f"📊 Active Profile: {active_profile.get('name', 'Unknown')}")
    print(f"🌐 Target URL: {active_profile.get('base_url', 'Not configured')}")
    
    current_behavior = stress_config_manager.get_current_user_behavior()
    print(f"🎭 User Behavior: {current_behavior.get('name', 'Unknown')}")
    
except Exception as e:
    print(f"⚠️ Configuration Warning: {e}")
    print("🔧 Using fallback configuration")

print("✅ Framework initialized successfully!")
print("\n" + "="*60)
print("📋 Available User Types:")
print("  • MVHSNormalUser - Typical browsing patterns")
print("  • MVHSActiveUser - More frequent searches")
print("  • MVHSPowerUser - Rapid, focused interactions")
print("  • MVHSBrowserUser - Casual browsing, minimal searches")
print("  • MVHSMobileUser - Touch-optimized behavior")
print("="*60)

# For Locust web UI, you can now start with:
# python -m locust --web-host=0.0.0.0 --web-port=80
