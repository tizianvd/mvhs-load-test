#!/usr/bin/env python3
"""
MVHS Load Test User Behavior Configurator
Configure realistic wait times and user behavior patterns for load testing
"""

import os
import json
import sys
from pathlib import Path

def load_stress_config():
    """Load stress test configuration"""
    try:
        with open('stress_test_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("❌ Error: stress_test_config.json not found!")
        return None

def show_available_behaviors():
    """Show all available user behavior configurations"""
    config = load_stress_config()
    if not config or 'user_behavior' not in config:
        print("❌ No user behavior configurations found!")
        return
    
    print("\n🎭 Available User Behavior Patterns:")
    print("=" * 50)
    
    for behavior_id, behavior in config['user_behavior'].items():
        name = behavior.get('name', 'Unknown')
        description = behavior.get('description', 'No description')
        wait_min = behavior.get('wait_time_min', 0)
        wait_max = behavior.get('wait_time_max', 0)
        
        print(f"\n🔹 {behavior_id}")
        print(f"   Name: {name}")
        print(f"   Description: {description}")
        print(f"   Wait Time: {wait_min}-{wait_max} seconds between requests")
        
        if 'reading_time_min' in behavior:
            reading_min = behavior.get('reading_time_min', 0)
            reading_max = behavior.get('reading_time_max', 0)
            print(f"   Reading Time: {reading_min}-{reading_max} seconds on pages")

def set_user_behavior(behavior_type):
    """Set user behavior for current session"""
    config = load_stress_config()
    if not config or 'user_behavior' not in config:
        print("❌ Configuration not available!")
        return False
    
    if behavior_type not in config['user_behavior']:
        print(f"❌ Unknown behavior type: {behavior_type}")
        print("Available types:", list(config['user_behavior'].keys()))
        return False
    
    # Set environment variable
    os.environ['USER_BEHAVIOR'] = behavior_type
    os.environ['TEST_MODE'] = 'realistic' if behavior_type != 'stress_test' else 'stress'
    
    behavior = config['user_behavior'][behavior_type]
    name = behavior.get('name', 'Unknown')
    wait_min = behavior.get('wait_time_min', 0)
    wait_max = behavior.get('wait_time_max', 0)
    
    print(f"✅ User behavior set to: {name}")
    print(f"⏱️ Wait time: {wait_min}-{wait_max} seconds between requests")
    
    return True

def start_webui_with_behavior(behavior_type='realistic'):
    """Start Locust Web UI with specific behavior"""
    if not set_user_behavior(behavior_type):
        return
    
    print(f"\n🌐 Starting Locust Web UI with {behavior_type} behavior...")
    print("📍 URL: http://localhost:8089")
    print("\n⚠️  IMPORTANT: In the Locust Web UI:")
    print("   1. Select 'MVHSRealisticUser' as the User class")
    print("   2. Start with 5-10 users for realistic simulation")
    print("   3. Use spawn rate of 1-2 users per second")
    print("\n🎯 Target website: https://www.mvhs.de")
    print("\nPress Ctrl+C to stop the test")
    print("-" * 50)
    
    # Start Locust
    os.system("python -m locust --web-host=0.0.0.0 --web-port=8089")

def main():
    """Main function"""
    print("🎭 MVHS Load Test - User Behavior Configurator")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("\nUsage:")
        print("  python configure_user_behavior.py show              - Show available behaviors")
        print("  python configure_user_behavior.py set <behavior>    - Set user behavior")
        print("  python configure_user_behavior.py start [behavior]  - Start Web UI with behavior")
        print("\nExample:")
        print("  python configure_user_behavior.py start realistic")
        print("  python configure_user_behavior.py start mobile_user")
        print("  python configure_user_behavior.py start slow_user")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'show':
        show_available_behaviors()
    
    elif command == 'set':
        if len(sys.argv) < 3:
            print("❌ Please specify behavior type")
            show_available_behaviors()
            return
        behavior_type = sys.argv[2]
        set_user_behavior(behavior_type)
    
    elif command == 'start':
        behavior_type = sys.argv[2] if len(sys.argv) > 2 else 'realistic'
        start_webui_with_behavior(behavior_type)
    
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main()
