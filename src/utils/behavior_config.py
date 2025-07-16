"""
User behavior configuration utilities.

This module provides utilities for configuring and managing user behavior
patterns for load testing scenarios.
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

from src.config.stress_config import StressTestConfigManager


class UserBehaviorConfigurator:
    """Manages user behavior configuration for load testing."""
    
    def __init__(self):
        """Initialize the behavior configurator."""
        self.config_manager = StressTestConfigManager()
    
    def show_available_behaviors(self) -> None:
        """Display all available user behavior configurations."""
        try:
            behaviors = self.config_manager.list_user_behaviors()
            
            print("\n🎭 Available User Behavior Patterns:")
            print("=" * 50)
            
            for behavior_id, description in behaviors.items():
                try:
                    behavior = self.config_manager.get_user_behavior(behavior_id)
                    
                    name = behavior.get('name', 'Unknown')
                    wait_min = behavior.get('wait_time_min', 0)
                    wait_max = behavior.get('wait_time_max', 0)
                    reading_min = behavior.get('reading_time_min', 0)
                    reading_max = behavior.get('reading_time_max', 0)
                    search_prob = behavior.get('search_probability', 0)
                    
                    print(f"\n🔹 {behavior_id}")
                    print(f"   Name: {name}")
                    print(f"   Description: {description}")
                    print(f"   Wait Time: {wait_min}-{wait_max} seconds between requests")
                    print(f"   Reading Time: {reading_min}-{reading_max} seconds on pages")
                    print(f"   Search Probability: {search_prob:.0%}")
                    
                except Exception as e:
                    print(f"\n🔹 {behavior_id}")
                    print(f"   Description: {description}")
                    print(f"   ⚠️ Error loading details: {e}")
                    
        except Exception as e:
            print(f"❌ Error loading behavior configurations: {e}")
    
    def set_user_behavior(self, behavior_type: str) -> bool:
        """
        Set user behavior for current session.
        
        Args:
            behavior_type: Name of the behavior configuration to set
            
        Returns:
            True if behavior was set successfully, False otherwise
        """
        try:
            # Validate behavior exists
            behavior = self.config_manager.get_user_behavior(behavior_type)
            
            # Set environment variable
            self.config_manager.set_user_behavior_env(behavior_type)
            
            # Display confirmation
            name = behavior.get('name', 'Unknown')
            description = behavior.get('description', 'No description')
            wait_min = behavior.get('wait_time_min', 0)
            wait_max = behavior.get('wait_time_max', 0)
            
            print(f"✅ User behavior set to: {name}")
            print(f"📝 Description: {description}")
            print(f"⏱️ Wait Time: {wait_min}-{wait_max} seconds between requests")
            
            if 'reading_time_min' in behavior:
                reading_min = behavior.get('reading_time_min', 0)
                reading_max = behavior.get('reading_time_max', 0)
                print(f"📖 Reading Time: {reading_min}-{reading_max} seconds on pages")
            
            if 'search_probability' in behavior:
                search_prob = behavior.get('search_probability', 0)
                print(f"🔍 Search Probability: {search_prob:.0%}")
            
            print(f"\n🌍 Environment variable USER_BEHAVIOR_TYPE set to: {behavior_type}")
            print("This setting will be used by new load test sessions.")
            
            return True
            
        except KeyError:
            print(f"❌ Behavior type '{behavior_type}' not found!")
            print("\nAvailable behavior types:")
            behaviors = self.config_manager.list_user_behaviors()
            for behavior_id in behaviors.keys():
                print(f"  - {behavior_id}")
            return False
            
        except Exception as e:
            print(f"❌ Error setting user behavior: {e}")
            return False
    
    def get_current_behavior(self) -> Optional[Dict[str, Any]]:
        """
        Get the currently configured user behavior.
        
        Returns:
            Current behavior configuration or None if not set
        """
        try:
            current_behavior = self.config_manager.get_current_user_behavior()
            return current_behavior
        except Exception as e:
            print(f"❌ Error getting current behavior: {e}")
            return None
    
    def show_current_behavior(self) -> None:
        """Display the currently configured user behavior."""
        try:
            behavior = self.get_current_behavior()
            if not behavior:
                print("❌ No user behavior currently configured")
                return
            
            behavior_name = os.environ.get('USER_BEHAVIOR_TYPE', 'default')
            name = behavior.get('name', 'Unknown')
            description = behavior.get('description', 'No description')
            
            print(f"\n🎭 Current User Behavior: {name} ({behavior_name})")
            print("=" * 50)
            print(f"📝 Description: {description}")
            
            if 'wait_time_min' in behavior and 'wait_time_max' in behavior:
                wait_min = behavior['wait_time_min']
                wait_max = behavior['wait_time_max']
                print(f"⏱️ Wait Time: {wait_min}-{wait_max} seconds between requests")
            
            if 'reading_time_min' in behavior and 'reading_time_max' in behavior:
                reading_min = behavior['reading_time_min']
                reading_max = behavior['reading_time_max']
                print(f"📖 Reading Time: {reading_min}-{reading_max} seconds on pages")
            
            if 'search_probability' in behavior:
                search_prob = behavior['search_probability']
                print(f"🔍 Search Probability: {search_prob:.0%}")
            
        except Exception as e:
            print(f"❌ Error displaying current behavior: {e}")
    
    def create_custom_behavior(self, 
                             behavior_id: str,
                             name: str,
                             description: str,
                             wait_time_min: float = 1.0,
                             wait_time_max: float = 5.0,
                             reading_time_min: float = 2.0,
                             reading_time_max: float = 8.0,
                             search_probability: float = 0.3) -> bool:
        """
        Create a custom user behavior configuration.
        
        Args:
            behavior_id: Unique identifier for the behavior
            name: Human-readable name
            description: Description of the behavior
            wait_time_min: Minimum wait time between requests
            wait_time_max: Maximum wait time between requests
            reading_time_min: Minimum reading time on pages
            reading_time_max: Maximum reading time on pages
            search_probability: Probability of performing searches (0.0-1.0)
            
        Returns:
            True if behavior was created successfully, False otherwise
        """
        try:
            # Load current configuration
            config = self.config_manager.load_config()
            
            # Create new behavior
            new_behavior = {
                'name': name,
                'description': description,
                'wait_time_min': wait_time_min,
                'wait_time_max': wait_time_max,
                'reading_time_min': reading_time_min,
                'reading_time_max': reading_time_max,
                'search_probability': search_probability
            }
            
            # Add to configuration
            if 'user_behavior' not in config:
                config['user_behavior'] = {}
            
            config['user_behavior'][behavior_id] = new_behavior
            
            # Save back to file
            config_file = self.config_manager.config_file
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # Clear cached config to force reload
            self.config_manager._config = None
            
            print(f"✅ Custom behavior '{behavior_id}' created successfully!")
            print(f"📝 Name: {name}")
            print(f"📖 Description: {description}")
            print(f"⏱️ Wait Time: {wait_time_min}-{wait_time_max} seconds")
            print(f"📖 Reading Time: {reading_time_min}-{reading_time_max} seconds")
            print(f"🔍 Search Probability: {search_probability:.0%}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating custom behavior: {e}")
            return False
    
    def compare_behaviors(self, behavior1: str, behavior2: str) -> None:
        """
        Compare two user behavior configurations.
        
        Args:
            behavior1: First behavior to compare
            behavior2: Second behavior to compare
        """
        try:
            beh1 = self.config_manager.get_user_behavior(behavior1)
            beh2 = self.config_manager.get_user_behavior(behavior2)
            
            print(f"\n🔄 Behavior Comparison: {behavior1} vs {behavior2}")
            print("=" * 60)
            
            # Compare key metrics
            metrics = [
                ('name', 'Name'),
                ('description', 'Description'),
                ('wait_time_min', 'Min Wait Time'),
                ('wait_time_max', 'Max Wait Time'),
                ('reading_time_min', 'Min Reading Time'),
                ('reading_time_max', 'Max Reading Time'),
                ('search_probability', 'Search Probability')
            ]
            
            for key, label in metrics:
                val1 = beh1.get(key, 'N/A')
                val2 = beh2.get(key, 'N/A')
                
                if key == 'search_probability':
                    if val1 != 'N/A':
                        val1 = f"{val1:.0%}"
                    if val2 != 'N/A':
                        val2 = f"{val2:.0%}"
                
                print(f"{label:20} | {str(val1):25} | {str(val2):25}")
            
        except KeyError as e:
            print(f"❌ Behavior not found: {e}")
        except Exception as e:
            print(f"❌ Error comparing behaviors: {e}")


def main():
    """Main function for command-line usage."""
    configurator = UserBehaviorConfigurator()
    
    if len(sys.argv) == 1:
        # No arguments, show available behaviors
        configurator.show_available_behaviors()
        print("\n💡 Usage:")
        print("  python -m src.utils.behavior_config show           # Show available behaviors")
        print("  python -m src.utils.behavior_config current        # Show current behavior")
        print("  python -m src.utils.behavior_config set <behavior> # Set behavior")
        
    elif len(sys.argv) == 2:
        command = sys.argv[1].lower()
        
        if command == 'show':
            configurator.show_available_behaviors()
        elif command == 'current':
            configurator.show_current_behavior()
        else:
            # Assume it's a behavior name to set
            success = configurator.set_user_behavior(command)
            sys.exit(0 if success else 1)
    
    elif len(sys.argv) == 3:
        command = sys.argv[1].lower()
        behavior_type = sys.argv[2]
        
        if command == 'set':
            success = configurator.set_user_behavior(behavior_type)
            sys.exit(0 if success else 1)
        else:
            print(f"❌ Unknown command: {command}")
            sys.exit(1)
    
    else:
        print("❌ Too many arguments")
        sys.exit(1)


if __name__ == "__main__":
    main()
