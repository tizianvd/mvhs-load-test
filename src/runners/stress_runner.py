"""
Enhanced stress test runner with improved configuration and execution.

This module provides a comprehensive test runner that can execute
various stress test configurations with proper setup and teardown.
"""

import json
import sys
import os
import platform
import subprocess
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

# Handle imports for both direct execution and module import
try:
    from ..config.profiles import WebsiteProfileManager
    from ..config.stress_config import StressTestConfigManager
except ImportError:
    # Fallback for direct execution
    sys.path.append(str(Path(__file__).parent.parent))
    from config.profiles import WebsiteProfileManager
    from config.stress_config import StressTestConfigManager


class StressTestRunner:
    """Enhanced stress test runner with configuration management."""
    
    def __init__(self, 
                 reports_dir: str = "reports",
                 metrics_dir: str = "reports/metrics"):
        """
        Initialize the stress test runner.
        
        Args:
            reports_dir: Directory for test reports
            metrics_dir: Directory for metrics files
        """
        self.reports_dir = Path(reports_dir)
        self.metrics_dir = Path(metrics_dir)
        
        # Ensure directories exist
        self.reports_dir.mkdir(exist_ok=True)
        self.metrics_dir.mkdir(exist_ok=True)
        
        # Initialize configuration managers
        self.profile_manager = WebsiteProfileManager()
        self.stress_config_manager = StressTestConfigManager()
        
        # Default configuration
        self.default_profile = "mvhs_production"
        self.default_web_port = 8089
        self.default_web_host = "0.0.0.0"
    
    def list_available_tests(self) -> None:
        """Display all available test configurations."""
        print("\n🧪 Available Stress Test Configurations:")
        print("=" * 60)
        
        try:
            test_configs = self.stress_config_manager.list_test_configs()
            
            for test_name, description in test_configs.items():
                try:
                    config = self.stress_config_manager.get_test_config(test_name)
                    users = config.get('users', 'Unknown')
                    duration = config.get('duration', 'Unknown')
                    behavior = config.get('user_behavior', 'Unknown')
                    
                    print(f"\n🔹 {test_name}")
                    print(f"   Description: {description}")
                    print(f"   Users: {users}")
                    print(f"   Duration: {duration}")
                    print(f"   Behavior: {behavior}")
                    
                except Exception as e:
                    print(f"\n🔹 {test_name}")
                    print(f"   Description: {description}")
                    print(f"   ⚠️ Configuration error: {e}")
        
        except Exception as e:
            print(f"❌ Error loading test configurations: {e}")
        
        print("\n🎭 Available User Behavior Patterns:")
        print("=" * 60)
        
        try:
            behaviors = self.stress_config_manager.list_user_behaviors()
            
            for behavior_name, description in behaviors.items():
                try:
                    behavior = self.stress_config_manager.get_user_behavior(behavior_name)
                    wait_min = behavior.get('wait_time_min', 0)
                    wait_max = behavior.get('wait_time_max', 0)
                    search_prob = behavior.get('search_probability', 0)
                    
                    print(f"\n🎭 {behavior_name}")
                    print(f"   Description: {description}")
                    print(f"   Wait Time: {wait_min}-{wait_max} seconds")
                    print(f"   Search Probability: {search_prob:.0%}")
                    
                except Exception as e:
                    print(f"\n🎭 {behavior_name}")
                    print(f"   Description: {description}")
                    print(f"   ⚠️ Configuration error: {e}")
        
        except Exception as e:
            print(f"❌ Error loading behavior configurations: {e}")
        
        print("\n🌐 Available Website Profiles:")
        print("=" * 60)
        
        try:
            profiles = self.profile_manager.list_profiles()
            
            for profile_name, description in profiles.items():
                try:
                    profile = self.profile_manager.get_profile(profile_name)
                    base_url = profile.get('base_url', 'Unknown')
                    categories = len(profile.get('categories', []))
                    
                    print(f"\n🌐 {profile_name}")
                    print(f"   Description: {description}")
                    print(f"   URL: {base_url}")
                    print(f"   Categories: {categories}")
                    
                except Exception as e:
                    print(f"\n🌐 {profile_name}")
                    print(f"   Description: {description}")
                    print(f"   ⚠️ Configuration error: {e}")
        
        except Exception as e:
            print(f"❌ Error loading website profiles: {e}")
    
    def run_test(self, 
                 test_name: str,
                 profile_name: Optional[str] = None,
                 host_override: Optional[str] = None,
                 headless: bool = True) -> bool:
        """
        Run a specific stress test configuration.
        
        Args:
            test_name: Name of the test configuration to run
            profile_name: Website profile to use (optional)
            host_override: Override the host URL (optional)
            headless: Run in headless mode (default True)
            
        Returns:
            True if test executed successfully, False otherwise
        """
        try:
            # Load test configuration
            test_config = self.stress_config_manager.get_test_config(test_name)
            
            # Set up environment variables
            self._setup_environment(test_config, profile_name, test_name)
            
            # Prepare Locust command
            locust_cmd = self._build_locust_command(
                test_config, host_override, headless, test_name
            )
            
            print(f"\n🚀 Starting {test_config.get('name', test_name)}")
            print(f"📊 Users: {test_config.get('users')}")
            print(f"⏱️ Duration: {test_config.get('duration')}")
            print(f"🎭 Behavior: {test_config.get('user_behavior')}")
            
            if profile_name:
                profile = self.profile_manager.get_profile(profile_name)
                print(f"🌐 Profile: {profile.get('name')} ({profile.get('base_url')})")
            
            print(f"💻 Command: {' '.join(locust_cmd)}")
            print("\n" + "="*60)
            
            # Execute the test
            result = subprocess.run(locust_cmd, capture_output=False)
            
            if result.returncode == 0:
                print(f"\n✅ Test '{test_name}' completed successfully!")
                self._organize_metrics_files(test_name)
                return True
            else:
                print(f"\n❌ Test '{test_name}' failed with return code {result.returncode}")
                return False
                
        except KeyError as e:
            print(f"❌ Test configuration '{test_name}' not found: {e}")
            return False
        except Exception as e:
            print(f"❌ Error running test '{test_name}': {e}")
            return False
    
    def start_web_ui(self, 
                     profile_name: Optional[str] = None,
                     host_override: Optional[str] = None,
                     port: int = None) -> bool:
        """
        Start the Locust web UI for interactive testing.
        
        Args:
            profile_name: Website profile to use (optional)
            host_override: Override the host URL (optional)  
            port: Web UI port (default 8089)
            
        Returns:
            True if web UI started successfully, False otherwise
        """
        try:
            if port is None:
                port = self.default_web_port
            
            # Set up environment
            self._setup_environment({}, profile_name, "web_ui")
            
            # Build command
            locust_cmd = [
                "locust",
                "-f", "locustfile.py",
                "--web-host", self.default_web_host,
                "--web-port", str(port)
            ]
            
            if host_override:
                locust_cmd.extend(["--host", host_override])
            elif profile_name:
                profile = self.profile_manager.get_profile(profile_name)
                locust_cmd.extend(["--host", profile.get('base_url')])
            
            print(f"\n🌐 Starting Locust Web UI...")
            print(f"📊 Port: {port}")
            print(f"🔗 URL: http://localhost:{port}")
            
            if profile_name:
                profile = self.profile_manager.get_profile(profile_name)
                print(f"🌐 Profile: {profile.get('name')} ({profile.get('base_url')})")
            
            print(f"💻 Command: {' '.join(locust_cmd)}")
            print("\n" + "="*60)
            print("🎯 Open your browser and navigate to the URL above")
            print("🛑 Press Ctrl+C to stop the web server")
            print("="*60)
            
            # Execute the command (this will block)
            result = subprocess.run(locust_cmd)
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"❌ Error starting web UI: {e}")
            return False
    
    def _setup_environment(self, 
                          test_config: Dict[str, Any],
                          profile_name: Optional[str],
                          test_name: str) -> None:
        """Set up environment variables for the test."""
        
        # Set website profile
        if profile_name:
            os.environ['WEBSITE_PROFILE'] = profile_name
        elif 'profile' in test_config:
            os.environ['WEBSITE_PROFILE'] = test_config['profile']
        else:
            os.environ['WEBSITE_PROFILE'] = self.default_profile
        
        # Set user behavior
        if 'user_behavior' in test_config:
            os.environ['USER_BEHAVIOR_TYPE'] = test_config['user_behavior']
        
        # Set test name for metrics
        os.environ['TEST_NAME'] = test_name
        
        # Set reports directory
        os.environ['REPORTS_DIR'] = str(self.reports_dir)
        os.environ['METRICS_DIR'] = str(self.metrics_dir)
    
    def _build_locust_command(self,
                             test_config: Dict[str, Any],
                             host_override: Optional[str],
                             headless: bool,
                             test_name: str) -> List[str]:
        """Build the Locust command with appropriate parameters."""
        
        cmd = ["locust", "-f", "locustfile.py"]
        
        # Add user and spawn rate configuration
        if 'users' in test_config:
            cmd.extend(["-u", str(test_config['users'])])
        
        if 'spawn_rate' in test_config:
            cmd.extend(["-r", str(test_config['spawn_rate'])])
        
        # Add duration
        if 'duration' in test_config:
            cmd.extend(["-t", test_config['duration']])
        
        # Add host
        if host_override:
            cmd.extend(["--host", host_override])
        else:
            # Get host from profile
            profile_name = os.environ.get('WEBSITE_PROFILE', self.default_profile)
            try:
                profile = self.profile_manager.get_profile(profile_name)
                cmd.extend(["--host", profile.get('base_url')])
            except Exception:
                cmd.extend(["--host", "https://www.mvhs.de"])
        
        # Add headless mode
        if headless:
            cmd.append("--headless")
        
        # Add HTML report output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        html_report = self.reports_dir / f"{test_name}_{timestamp}_report.html"
        cmd.extend(["--html", str(html_report)])
        
        # Add CSV output
        csv_prefix = self.reports_dir / f"{test_name}_{timestamp}"
        cmd.extend(["--csv", str(csv_prefix)])
        
        return cmd
    
    def _organize_metrics_files(self, test_name: str) -> None:
        """Organize metrics files into the metrics directory."""
        try:
            # Find metrics files in the current directory
            current_dir = Path(".")
            metrics_files = []
            
            patterns = [
                "*metrics*.json",
                "*metrics*.csv"
            ]
            
            for pattern in patterns:
                metrics_files.extend(current_dir.glob(pattern))
            
            # Move files to metrics directory
            moved_count = 0
            for file_path in metrics_files:
                if file_path.is_file():
                    destination = self.metrics_dir / file_path.name
                    file_path.rename(destination)
                    moved_count += 1
            
            if moved_count > 0:
                print(f"📁 Moved {moved_count} metrics files to {self.metrics_dir}")
                
        except Exception as e:
            print(f"⚠️ Warning: Could not organize metrics files: {e}")


def main():
    """Main function for command-line interface."""
    parser = argparse.ArgumentParser(
        description="MVHS Stress Test Runner v2.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.runners.stress_runner                          # List all available tests
  python -m src.runners.stress_runner light_stress             # Run light stress test
  python -m src.runners.stress_runner medium_stress --profile mvhs_production
  python -m src.runners.stress_runner web                      # Start web UI
  python -m src.runners.stress_runner web --port 8080          # Start web UI on port 8080
        """
    )
    
    parser.add_argument(
        'test_name',
        nargs='?',
        help='Name of the test configuration to run, or "web" for web UI'
    )
    
    parser.add_argument(
        '--profile',
        help='Website profile to use (default: mvhs_production)'
    )
    
    parser.add_argument(
        '--host',
        help='Override the target host URL'
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=8089,
        help='Port for web UI (default: 8089)'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode (not headless)'
    )
    
    parser.add_argument(
        '--reports-dir',
        default='reports',
        help='Directory for test reports (default: reports)'
    )
    
    args = parser.parse_args()
    
    # Initialize runner
    runner = StressTestRunner(
        reports_dir=args.reports_dir,
        metrics_dir=f"{args.reports_dir}/metrics"
    )
    
    # Handle different commands
    if not args.test_name:
        # No test specified, show available tests
        runner.list_available_tests()
        
    elif args.test_name.lower() == 'web':
        # Start web UI
        success = runner.start_web_ui(
            profile_name=args.profile,
            host_override=args.host,
            port=args.port
        )
        sys.exit(0 if success else 1)
        
    else:
        # Run specific test
        success = runner.run_test(
            test_name=args.test_name,
            profile_name=args.profile,
            host_override=args.host,
            headless=not args.interactive
        )
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
