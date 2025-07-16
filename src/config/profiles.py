"""
Configuration management for website profiles.

This module handles loading and managing website profiles that define
target websites, their endpoints, categories, and test parameters.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional


class WebsiteProfileManager:
    """Manages website profile configurations."""
    
    def __init__(self, config_file: str = "config/website_profiles.json"):
        """
        Initialize the profile manager.
        
        Args:
            config_file: Path to the website profiles configuration file
        """
        self.config_file = Path(config_file)
        
        # Fallback to old location for backward compatibility
        if not self.config_file.exists():
            fallback_path = Path("website_profiles.json")
            if fallback_path.exists():
                self.config_file = fallback_path
        self._profiles = None
        self._active_profile = None
    
    def load_profiles(self) -> Dict[str, Any]:
        """
        Load website profiles from configuration file.
        
        Returns:
            Dictionary containing all website profiles
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            json.JSONDecodeError: If configuration file is invalid JSON
        """
        if self._profiles is None:
            if not self.config_file.exists():
                raise FileNotFoundError(f"Website profiles file not found: {self.config_file}")
            
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self._profiles = config.get('profiles', {})
        
        return self._profiles
    
    def get_profile(self, profile_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get a specific website profile.
        
        Args:
            profile_name: Name of the profile to retrieve. If None, uses environment variable
                         WEBSITE_PROFILE or defaults to 'mvhs_production'
            
        Returns:
            Profile configuration dictionary
            
        Raises:
            KeyError: If profile doesn't exist
        """
        profiles = self.load_profiles()
        
        if profile_name is None:
            profile_name = os.environ.get('WEBSITE_PROFILE', 'mvhs_production')
        
        if profile_name not in profiles:
            available = list(profiles.keys())
            raise KeyError(f"Profile '{profile_name}' not found. Available profiles: {available}")
        
        return profiles[profile_name]
    
    def set_active_profile(self, profile_name: str) -> None:
        """
        Set the active profile for web UI usage.
        
        Args:
            profile_name: Name of the profile to activate
            
        Raises:
            KeyError: If profile doesn't exist
        """
        profile = self.get_profile(profile_name)  # Validates profile exists
        self._active_profile = profile
        os.environ['WEBSITE_PROFILE'] = profile_name
    
    def get_active_profile(self) -> Dict[str, Any]:
        """
        Get the currently active profile.
        
        Returns:
            Active profile configuration dictionary
        """
        if self._active_profile is None:
            self._active_profile = self.get_profile()
        return self._active_profile
    
    def list_profiles(self) -> Dict[str, str]:
        """
        Get a list of all available profiles with their descriptions.
        
        Returns:
            Dictionary mapping profile names to descriptions
        """
        profiles = self.load_profiles()
        return {
            name: profile.get('description', 'No description available')
            for name, profile in profiles.items()
        }
    
    def get_base_url(self, profile_name: Optional[str] = None) -> str:
        """
        Get the base URL for a profile.
        
        Args:
            profile_name: Profile name, or None for active profile
            
        Returns:
            Base URL string
        """
        profile = self.get_profile(profile_name)
        return profile.get('base_url', '')
    
    def get_endpoints(self, profile_name: Optional[str] = None) -> Dict[str, str]:
        """
        Get the API endpoints for a profile.
        
        Args:
            profile_name: Profile name, or None for active profile
            
        Returns:
            Dictionary of endpoint names to paths
        """
        profile = self.get_profile(profile_name)
        return profile.get('endpoints', {})
    
    def get_categories(self, profile_name: Optional[str] = None) -> list:
        """
        Get the categories for a profile.
        
        Args:
            profile_name: Profile name, or None for active profile
            
        Returns:
            List of category configurations
        """
        profile = self.get_profile(profile_name)
        return profile.get('categories', [])
    
    def get_search_terms(self, profile_name: Optional[str] = None) -> list:
        """
        Get the search terms for a profile.
        
        Args:
            profile_name: Profile name, or None for active profile
            
        Returns:
            List of search terms
        """
        profile = self.get_profile(profile_name)
        return profile.get('search_terms', [
            "schule", "unterricht", "lehrer", "student", "abitur", "klausur",
            "ferien", "termine", "anmeldung", "kontakt", "impressum", "news"
        ])


# Global instance for backward compatibility
_profile_manager = WebsiteProfileManager()

def get_active_profile() -> Dict[str, Any]:
    """Get the active website profile (legacy function)."""
    return _profile_manager.get_active_profile()

def set_profile_for_web_ui(profile_name: str) -> bool:
    """Set the profile for web UI usage (legacy function)."""
    try:
        _profile_manager.set_active_profile(profile_name)
        profile = _profile_manager.get_active_profile()
        print(f"✅ Profile changed to: {profile.get('name', 'Unknown')} ({profile_name})")
        print(f"🎯 Target URL: {profile.get('base_url', 'Unknown')}")
        print(f"📂 Categories available: {len(profile.get('categories', []))}")
        return True
    except KeyError:
        return False

def get_profile_for_web_ui() -> Dict[str, Any]:
    """Get the profile for web UI usage (legacy function)."""
    return _profile_manager.get_active_profile()
