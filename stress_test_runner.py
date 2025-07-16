import json
import sys
import os
import platform
from datetime import datetime

# ============================================================================
# CONFIGURATION - Adjust these settings as needed
# ============================================================================
DEFAULT_PROFILE = "mvhs_production"  # Default website profile to use
DEFAULT_WEB_PORT = 8089              # Default port for Locust web UI
DEFAULT_WEB_HOST = "0.0.0.0"         # Bind to all interfaces for WSL access
REPORTS_DIR = "reports"              # Directory for test reports
METRICS_DIR = "metrics"              # Subdirectory for metrics files
# ============================================================================

def load_website_profiles():
    """Load website profiles configuration from JSON file"""
    try:
        with open('website_profiles.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: website_profiles.json not found!")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing website_profiles.json: {e}")
        sys.exit(1)

def get_active_profile(profile_name=None):
    """Get the active website profile configuration"""
    profiles_config = load_website_profiles()
    
    if profile_name is None:
        profile_name = os.environ.get('WEBSITE_PROFILE', DEFAULT_PROFILE)
    
    if profile_name not in profiles_config['profiles']:
        print(f"Error: Profile '{profile_name}' not found!")
        print("Available profiles:")
        for name, profile in profiles_config['profiles'].items():
            print(f"  {name}: {profile['description']}")
        sys.exit(1)
    
    return profiles_config['profiles'][profile_name], profile_name

def load_stress_config():
    """Load stress test configuration from JSON file"""
    try:
        with open('stress_test_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: stress_test_config.json not found!")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing stress_test_config.json: {e}")
        sys.exit(1)

def generate_locust_command(test_config, test_name, profile=None):
    """Generate Locust command based on stress test configuration with concurrency optimizations"""
    
    # Get the active profile
    if profile is None:
        active_profile, profile_name = get_active_profile()
    else:
        active_profile, profile_name = get_active_profile(profile)
    
    target_host = active_profile['base_url']
    
    # Get the current directory
    current_dir = os.path.abspath(os.path.dirname(__file__))
    locustfile_path = os.path.join(current_dir, "locustfile.py")
    
    # Calculate optimal processes for concurrency
    users = test_config['users']
    processes = min(4, max(1, users // 50))  # Use multiple processes for high user counts
    
    # Base command with concurrency optimizations
    cmd_parts = [
        "python", "-m", "locust",
        f"-f {locustfile_path}",
        f"--host={target_host}",
        "--headless",
        f"--users={test_config['users']}",
        f"--spawn-rate={test_config['spawn_rate']}",
        f"--run-time={test_config['duration']}"
    ]
    
    # Add process-based concurrency for high user counts (only on supported platforms)
    if users >= 100 and platform.system() != 'Windows':
        cmd_parts.append(f"--processes={processes}")
        print(f"🚀 Using {processes} processes for better concurrency with {users} users")
    elif users >= 100 and platform.system() == 'Windows':
        print(f"⚠️  High concurrency mode: {users} users on Windows (processes not supported)")
        print("💡 Consider using WSL for better performance with high user counts")
    
    # Add performance optimizations
    cmd_parts.extend([
        "--reset-stats",  # Reset stats between runs
        "--stop-timeout=60"  # Faster shutdown
    ])
    
    # Generate timestamp for unique report names
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Add reporting options with absolute paths
    reports_dir = os.path.join(current_dir, REPORTS_DIR)
    report_name = f"{test_name}_{timestamp}"
    cmd_parts.extend([
        f"--html={os.path.join(reports_dir, report_name)}_report.html",
        f"--csv={os.path.join(reports_dir, report_name)}"
    ])
    
    # Add configuration as environment variables
    env_vars = {
        'STRESS_TEST_NAME': test_name,
        'SEARCH_INTENSITY': test_config['search_intensity'],
        'SCENARIOS': ','.join(test_config['scenarios']),
        'WEBSITE_PROFILE': profile_name,
        'TARGET_HOST': target_host,
        'TIMESTAMP': timestamp,
        'PYTHONUNBUFFERED': '1'  # Force unbuffered output
    }
    
    return ' '.join(cmd_parts), env_vars

def start_locust_web_ui(port=None):
    """Start Locust web UI accessible from Windows host when running in WSL"""
    
    if port is None:
        port = DEFAULT_WEB_PORT
    
    # Get the active profile
    active_profile, profile_name = get_active_profile()
    target_host = active_profile['base_url']
    
    # Get the current directory
    current_dir = os.path.abspath(os.path.dirname(__file__))
    locustfile_path = os.path.join(current_dir, "locustfile.py")
    
    # Build command for web UI
    cmd_parts = [
        "python", "-m", "locust",
        f"-f {locustfile_path}",
        f"--host={target_host}",
        f"--web-host={DEFAULT_WEB_HOST}",  # Bind to all interfaces for WSL access
        f"--web-port={port}"
    ]
    
    command = ' '.join(cmd_parts)
    
    print("🌐 Starting Locust Web UI...")
    print(f"🎯 Target: {target_host} ({profile_name})")
    print(f"📍 Command: {command}")
    print(f"🔗 Access URLs:")
    print(f"   - From WSL: http://localhost:{port}")
    print(f"   - From Windows: http://localhost:{port}")
    
    # For WSL2, you might also need the WSL IP
    try:
        import subprocess
        result = subprocess.run(['hostname', '-I'], capture_output=True, text=True)
        if result.returncode == 0:
            wsl_ip = result.stdout.strip().split()[0]
            print(f"   - WSL IP: http://{wsl_ip}:{port}")
    except:
        pass
    
    print("\n💡 Note: Use Ctrl+C to stop the web server")
    print("-" * 60)
    
    # Set environment variables for the web UI
    os.environ['WEBSITE_PROFILE'] = profile_name
    os.environ['TARGET_HOST'] = target_host
    
    # Execute the command
    return os.system(command)

def main():
    if len(sys.argv) < 2:
        # Get current profile for display
        active_profile, profile_name = get_active_profile()
        
        print("Usage: python stress_test_runner.py <test_name|web|config|profiles>")
        print(f"\n🎯 Current Profile: {profile_name} ({active_profile['name']})")
        print(f"🌐 Target: {active_profile['base_url']}")
        print(f"📁 Reports Directory: {REPORTS_DIR}")
        print(f"🌐 Default Web Port: {DEFAULT_WEB_PORT}")
        print("\nAvailable stress tests:")
        config = load_stress_config()
        for test_name, test_config in config['stress_tests'].items():
            description = test_config.get('description', 'No description available')
            print(f"  {test_name}: {description}")
        print("\nOther commands:")
        print("  web [port]: Start Locust web UI for interactive testing")
        print("  config: Show current configuration")
        print("  profiles: Show available website profiles")
        print("  set-profile <profile_name>: Set the active profile")
        sys.exit(1)
    
    command = sys.argv[1]
    
    # Handle profiles display command
    if command == "profiles":
        profiles_config = load_website_profiles()
        active_profile, profile_name = get_active_profile()
        
        print("📋 Available Website Profiles:")
        for name, profile in profiles_config['profiles'].items():
            status = " (ACTIVE)" if name == profile_name else ""
            print(f"  {name}: {profile['description']}{status}")
            print(f"    URL: {profile['base_url']}")
            print(f"    Categories: {len(profile['categories'])} defined")
        print(f"\n💡 Set profile with: WEBSITE_PROFILE={profile_name} python stress_test_runner.py <test_name>")
        print(f"💡 Or set environment variable: export WEBSITE_PROFILE={profile_name}")
        return 0
    
    # Handle set-profile command
    if command == "set-profile":
        if len(sys.argv) < 3:
            print("Usage: python stress_test_runner.py set-profile <profile_name>")
            profiles_config = load_website_profiles()
            print("Available profiles:")
            for name in profiles_config['profiles'].keys():
                print(f"  {name}")
            sys.exit(1)
        
        profile_name = sys.argv[2]
        try:
            active_profile, _ = get_active_profile(profile_name)
            print(f"✅ Profile set to: {profile_name} ({active_profile['name']})")
            print(f"🎯 Target: {active_profile['base_url']}")
            print(f"💡 This setting is temporary. To make it permanent, set:")
            print(f"   export WEBSITE_PROFILE={profile_name}")
            os.environ['WEBSITE_PROFILE'] = profile_name
            return 0
        except SystemExit:
            return 1
    
    # Handle config display command
    if command == "config":
        active_profile, profile_name = get_active_profile()
        
        print("📋 Current Configuration:")
        print(f"  🎯 Active Profile: {profile_name} ({active_profile['name']})")
        print(f"  🌐 Target Host: {active_profile['base_url']}")
        print(f"  🌐 Web Host: {DEFAULT_WEB_HOST}")
        print(f"  🔌 Default Web Port: {DEFAULT_WEB_PORT}")
        print(f"  📁 Reports Directory: {REPORTS_DIR}")
        print(f"  📊 Metrics Directory: {METRICS_DIR}")
        print(f"  🐍 Platform: {platform.system()}")
        print(f"  📈 Performance Thresholds:")
        thresholds = active_profile.get('performance_thresholds', {})
        for key, value in thresholds.items():
            print(f"    {key}: {value}")
        return 0
    
    # Handle web UI command
    if command == "web":
        port = DEFAULT_WEB_PORT
        if len(sys.argv) > 2:
            try:
                port = int(sys.argv[2])
            except ValueError:
                print("Error: Port must be a number")
                sys.exit(1)
        return start_locust_web_ui(port)
    
    # Handle stress test commands
    test_name = command
    config = load_stress_config()
    
    if test_name not in config['stress_tests']:
        print(f"Error: Test '{test_name}' not found in configuration!")
        print("Available tests:")
        for name in config['stress_tests'].keys():
            print(f"  {name}")
        sys.exit(1)
    
    test_config = config['stress_tests'][test_name]
    
    # Get the active profile
    active_profile, profile_name = get_active_profile()
    target_host = active_profile['base_url']
    
    print(f"Running Stress Test: {test_config['name']}")
    print(f"🎯 Target: {target_host} ({profile_name})")
    print(f"Description: {test_config['description']}")
    print(f"Users: {test_config['users']}")
    print(f"Spawn Rate: {test_config['spawn_rate']} users/sec")
    print(f"Duration: {test_config['duration']}")
    print(f"Search Intensity: {test_config['search_intensity']}")
    print(f"Scenarios: {', '.join(test_config['scenarios'])}")
    print("-" * 60)
    
    # Generate command and environment variables
    command, env_vars = generate_locust_command(test_config, test_name)
    
    # Set environment variables
    for key, value in env_vars.items():
        os.environ[key] = value
    
    # Create reports and metrics directory if they don't exist
    current_dir = os.path.abspath(os.path.dirname(__file__))
    reports_dir = os.path.join(current_dir, REPORTS_DIR)
    metrics_dir = os.path.join(reports_dir, METRICS_DIR)
    os.makedirs(reports_dir, exist_ok=True)
    os.makedirs(metrics_dir, exist_ok=True)
    
    print(f"Command: {command}")
    print()
    
    # Execute the command
    exit_code = os.system(command)
    
    if exit_code == 0:
        print(f"\n✅ Stress test '{test_name}' completed successfully!")
        print("Generating comprehensive analysis report...")
        os.system("python generate_report.py")
    else:
        print(f"\n❌ Stress test '{test_name}' failed with exit code: {exit_code}")
    
    return exit_code

if __name__ == "__main__":
    main()
