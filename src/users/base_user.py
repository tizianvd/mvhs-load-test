"""
Base user class for load testing.

This module provides the base user class that all specific user types
inherit from, with common functionality and behavior patterns.
"""

import random
import time
from locust import between, FastHttpUser
from typing import Dict, Any, Optional

from src.config.profiles import WebsiteProfileManager
from src.config.stress_config import StressTestConfigManager
from src.core.session import session_manager
from src.core.metrics import metrics_collector
from src.tasks.navigation import NavigationTasks
from src.tasks.search import SearchTasks


# German user names for realistic testing
GERMAN_FIRST_NAMES = [
    "Anna", "Ben", "Clara", "David", "Emma", "Felix", "Greta", "Hans",
    "Ingrid", "Jonas", "Klara", "Leon", "Maria", "Noah", "Olivia", "Paul",
    "Rosa", "Stefan", "Tanja", "Ulrich", "Vera", "Werner", "Andreas", "Birgit",
    "Christian", "Diana", "Erik", "Franziska", "Georg", "Heike", "Iris", "Jürgen",
    "Katharina", "Ludwig", "Marlene", "Norbert", "Otto", "Petra", "Ruth", "Sebastian",
    "Theresa", "Uwe", "Viktoria", "Wolfgang", "Yvonne", "Alexander", "Brigitte", "Christoph",
    "Dorothea", "Elias", "Frieda", "Günther", "Helena", "Isabella", "Johann", "Konstanze",
    "Lukas", "Magdalena", "Michael", "Nicole", "Peter", "Sabine", "Thomas", "Ursula"
]

GERMAN_LAST_NAMES = [
    "Müller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker",
    "Schulz", "Hoffmann", "Schäfer", "Koch", "Bauer", "Richter", "Klein", "Wolf",
    "Schröder", "Neumann", "Schwarz", "Zimmermann", "Braun", "Krüger", "Hofmann", "Hartmann",
    "Lange", "Schmitt", "Werner", "Schmitz", "Krause", "Meier", "Lehmann", "Schmid",
    "Schulze", "Maier", "Köhler", "Herrmann", "König", "Walter", "Mayer", "Huber",
    "Kaiser", "Fuchs", "Peters", "Lang", "Scholz", "Möller", "Weiß", "Jung",
    "Hahn", "Schubert", "Vogel", "Friedrich", "Keller", "Günther", "Frank", "Berger"
]


class BaseWebsiteUser(FastHttpUser):
    """Base user class for website load testing."""
    
    abstract = True  # This prevents Locust from using this class directly
    
    def __init__(self, environment):
        """Initialize the base user."""
        super().__init__(environment)
        
        # Initialize managers
        self.profile_manager = WebsiteProfileManager()
        self.stress_config_manager = StressTestConfigManager()
        
        # Load configurations
        self._load_profile()
        self._load_user_behavior()
        
        # Initialize task handlers
        self.navigation_tasks = NavigationTasks(self)
        self.search_tasks = SearchTasks(self)
        
        # User state
        self.user_id = str(id(self))
        first_name = random.choice(GERMAN_FIRST_NAMES)
        last_name = random.choice(GERMAN_LAST_NAMES)
        self.user_name = f"{first_name} {last_name}"
        self.session_start_time = time.time()
        
        # Configure HTTP client session
        self._configure_session()
    
    def _load_profile(self):
        """Load website profile configuration."""
        try:
            self.profile = self.profile_manager.get_active_profile()
            self.host = self.profile.get('base_url', 'https://www.mvhs.de')
            
            # Extract profile-specific data
            self.endpoints = self.profile.get('endpoints', {})
            self.categories = self.profile.get('categories', [])
            self.search_terms = self.profile.get('search_terms', [])
            
            # Build URL lists for easy access
            self.category_urls = [cat.get('url', '') for cat in self.categories if cat.get('url')]
            self.subcategory_urls = []
            
            for category in self.categories:
                for subcategory in category.get('subcategories', []):
                    self.subcategory_urls.append(f"/kurse/{subcategory}")
            
            print(f"👤 User initialized for {self.profile.get('name', 'Unknown')} profile")
            
        except Exception as e:
            print(f"❌ Failed to load profile: {e}")
            # Fallback to default values
            self.host = 'https://www.mvhs.de'
            self.profile = {'name': 'Fallback', 'base_url': self.host}
            self.endpoints = {}
            self.categories = []
            self.search_terms = ["test"]
            self.category_urls = []
            self.subcategory_urls = []
    
    def _load_user_behavior(self):
        """Load user behavior configuration."""
        try:
            behavior = self.stress_config_manager.get_current_user_behavior()
            
            # Only set wait times if not already defined by the child class
            if not hasattr(self.__class__, 'wait_time') or self.__class__.wait_time is None:
                wait_min = behavior.get('wait_time_min', 1)
                wait_max = behavior.get('wait_time_max', 5)
                self.wait_time = between(wait_min, wait_max)
            
            # Store behavior parameters
            self.behavior = behavior
            self.reading_time_min = behavior.get('reading_time_min', 2)
            self.reading_time_max = behavior.get('reading_time_max', 8)
            self.search_probability = behavior.get('search_probability', 0.3)

            print(f"🎭 User behavior: {behavior.get('name', 'Unknown')} "
                  f"(wait: {behavior.get('wait_time_min', 1)}-{behavior.get('wait_time_max', 5)}s, search: {self.search_probability:.0%})")
            
        except Exception as e:
            print(f"❌ Failed to load user behavior: {e}")
            # Fallback behavior - only set if not already defined
            if not hasattr(self.__class__, 'wait_time') or self.__class__.wait_time is None:
                self.wait_time = between(1, 5)
            self.behavior = {'name': 'Fallback'}
            self.reading_time_min = 2
            self.reading_time_max = 8
            self.search_probability = 0.3
    
    def _configure_session(self):
        """Configure HTTP session for this user."""
        try:
            # Get enhanced session from session manager
            session = session_manager.get_session(self.user_id)
            
            # Override Locust's default session with our enhanced one
            # Note: We can't directly replace self.client.session, 
            # but we can configure it with our settings
            if hasattr(self.client, 'session'):
                # Apply session configuration
                session_config = session_manager._session_factory.get_session_config()
                self.client.session.timeout = session_config['timeout']
                
                # Copy headers from our enhanced session
                self.client.session.headers.update(session.headers)
                
        except Exception as e:
            print(f"⚠️ Failed to configure session: {e}")
    
    def on_start(self):
        """Called when user starts testing."""
        print(f"🚀 User {self.user_name} started testing {self.host}")
        
        # Record user start
        metrics_collector.add_user_metric(
            user_id=self.user_id,
            action="user_start",
            duration=0,
            success=True
        )
        
        # Visit homepage to establish session
        self.navigation_tasks.visit_homepage()
    
    def on_stop(self):
        """Called when user stops testing."""
        session_duration = time.time() - self.session_start_time
        print(f"🛑 User {self.user_name} stopped after {session_duration:.1f} seconds")
        
        # Record user stop
        metrics_collector.add_user_metric(
            user_id=self.user_id,
            action="user_stop",
            duration=session_duration * 1000,
            success=True
        )
        
        # Clean up session
        session_manager.close_session(self.user_id)
    
    def wait_for_reading(self):
        """Simulate realistic reading/thinking time."""
        reading_time = random.uniform(self.reading_time_min, self.reading_time_max)
        print(f"⏳ User {self.user_name} waiting for {reading_time:.1f} seconds to read")
        time.sleep(reading_time)
    
    def should_perform_search(self) -> bool:
        """Determine if user should perform a search based on probability."""
        return random.random() < self.search_probability
    
    def get_random_category_url(self) -> Optional[str]:
        """Get a random category URL."""
        if self.category_urls:
            return random.choice(self.category_urls)
        return None
    
    def get_random_subcategory_url(self) -> Optional[str]:
        """Get a random subcategory URL."""
        if self.subcategory_urls:
            return random.choice(self.subcategory_urls)
        return None
    
    def refresh_profile(self):
        """Refresh user profile configuration (for dynamic changes)."""
        try:
            new_profile = self.profile_manager.get_active_profile()
            if new_profile != self.profile:
                print(f"🔄 User {self.user_id} refreshing profile")
                old_profile_name = self.profile.get('name', 'Unknown')
                new_profile_name = new_profile.get('name', 'Unknown')
                
                self.profile = new_profile
                self.host = new_profile.get('base_url', self.host)
                self.endpoints = new_profile.get('endpoints', {})
                self.categories = new_profile.get('categories', [])
                self.search_terms = new_profile.get('search_terms', [])
                
                # Rebuild URL lists
                self.category_urls = [cat.get('url', '') for cat in self.categories if cat.get('url')]
                self.subcategory_urls = []
                
                for category in self.categories:
                    for subcategory in category.get('subcategories', []):
                        self.subcategory_urls.append(f"/kurse/{subcategory}")
                
                # Reinitialize task handlers with new profile
                self.navigation_tasks = NavigationTasks(self)
                self.search_tasks = SearchTasks(self)
                
                print(f"✅ Profile updated from {old_profile_name} to {new_profile_name}")
                
        except Exception as e:
            print(f"❌ Failed to refresh profile: {e}")


def refresh_user_profile(user_instance):
    """Legacy function for refreshing user profiles."""
    if hasattr(user_instance, 'refresh_profile'):
        user_instance.refresh_profile()
