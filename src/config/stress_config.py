"""
Stress test configuration management.

This module handles loading and managing stress test configurations
that define user behavior patterns, test durations, and load parameters.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class StressTestConfigManager:
    """Manages stress test configurations."""
    
    def __init__(self, config_file: str = "config/stress_test_config.json"):
        """
        Initialize the stress test config manager.
        
        Args:
            config_file: Path to the stress test configuration file
        """
        self.config_file = Path(config_file)
        
        # Fallback to old location for backward compatibility
        if not self.config_file.exists():
            fallback_path = Path("stress_test_config.json")
            if fallback_path.exists():
                self.config_file = fallback_path
        self._config = None
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load stress test configuration from file.
        
        Returns:
            Dictionary containing stress test configuration
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            json.JSONDecodeError: If configuration file is invalid JSON
        """
        if self._config is None:
            if not self.config_file.exists():
                # Return default configuration if file doesn't exist
                self._config = self._get_default_config()
            else:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
        
        return self._config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default stress test configuration."""
        return {
            "test_configurations": {
                "light_stress": {
                    "name": "Light Stress Test",
                    "description": "Light stress test for basic load verification",
                    "users": 5,
                    "spawn_rate": 1,
                    "duration": "1m",
                    "user_behavior": "normal_user"
                },
                "medium_stress": {
                    "name": "Medium Stress Test", 
                    "description": "Medium stress test for moderate load testing",
                    "users": 25,
                    "spawn_rate": 2,
                    "duration": "5m",
                    "user_behavior": "active_user"
                },
                "heavy_stress": {
                    "name": "Heavy Stress Test",
                    "description": "Heavy stress test for high load scenarios",
                    "users": 50,
                    "spawn_rate": 5,
                    "duration": "10m",
                    "user_behavior": "power_user"
                }
            },
            "user_behavior": {
                "normal_user": {
                    "name": "Normal User",
                    "description": "Typical user browsing patterns",
                    "wait_time_min": 2,
                    "wait_time_max": 5,
                    "reading_time_min": 3,
                    "reading_time_max": 8,
                    "search_probability": 0.3
                },
                "active_user": {
                    "name": "Active User",
                    "description": "More engaged user with frequent interactions",
                    "wait_time_min": 1,
                    "wait_time_max": 3,
                    "reading_time_min": 2,
                    "reading_time_max": 5,
                    "search_probability": 0.5
                },
                "power_user": {
                    "name": "Power User",
                    "description": "Heavy user with rapid interactions",
                    "wait_time_min": 0.5,
                    "wait_time_max": 2,
                    "reading_time_min": 1,
                    "reading_time_max": 3,
                    "search_probability": 0.7
                }
            }
        }
    
    def get_test_config(self, test_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific test.
        
        Args:
            test_name: Name of the test configuration
            
        Returns:
            Test configuration dictionary
            
        Raises:
            KeyError: If test configuration doesn't exist
        """
        config = self.load_config()
        test_configs = config.get('test_configurations', {})
        
        if test_name not in test_configs:
            available = list(test_configs.keys())
            raise KeyError(f"Test '{test_name}' not found. Available tests: {available}")
        
        return test_configs[test_name]
    
    def get_user_behavior(self, behavior_name: str) -> Dict[str, Any]:
        """
        Get user behavior configuration.
        
        Args:
            behavior_name: Name of the behavior configuration
            
        Returns:
            Behavior configuration dictionary
            
        Raises:
            KeyError: If behavior configuration doesn't exist
        """
        config = self.load_config()
        behaviors = config.get('user_behavior', {})
        
        if behavior_name not in behaviors:
            available = list(behaviors.keys())
            raise KeyError(f"Behavior '{behavior_name}' not found. Available behaviors: {available}")
        
        return behaviors[behavior_name]
    
    def list_test_configs(self) -> Dict[str, str]:
        """
        Get a list of all available test configurations.
        
        Returns:
            Dictionary mapping test names to descriptions
        """
        config = self.load_config()
        test_configs = config.get('test_configurations', {})
        return {
            name: test_config.get('description', 'No description available')
            for name, test_config in test_configs.items()
        }
    
    def list_user_behaviors(self) -> Dict[str, str]:
        """
        Get a list of all available user behaviors.
        
        Returns:
            Dictionary mapping behavior names to descriptions
        """
        config = self.load_config()
        behaviors = config.get('user_behavior', {})
        return {
            name: behavior.get('description', 'No description available')
            for name, behavior in behaviors.items()
        }
    
    def set_user_behavior_env(self, behavior_name: str) -> None:
        """
        Set user behavior for current session via environment variable.
        
        Args:
            behavior_name: Name of the behavior to set
            
        Raises:
            KeyError: If behavior doesn't exist
        """
        # Validate behavior exists
        self.get_user_behavior(behavior_name)
        os.environ['USER_BEHAVIOR_TYPE'] = behavior_name
    
    def get_current_user_behavior(self) -> Dict[str, Any]:
        """
        Get the currently configured user behavior.
        
        Returns:
            Current user behavior configuration
        """
        behavior_name = os.environ.get('USER_BEHAVIOR_TYPE', 'normal_user')
        return self.get_user_behavior(behavior_name)


# Global instance for backward compatibility  
_stress_config_manager = StressTestConfigManager()

def load_stress_config() -> Dict[str, Any]:
    """Load stress test configuration (legacy function)."""
    return _stress_config_manager.load_config()
