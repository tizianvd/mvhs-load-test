"""
MVHS-specific user classes for load testing.

This module provides specialized user classes that simulate different
types of users interacting with the MVHS website.
"""

import random
import time
from locust import task, between

from src.users.base_user import BaseWebsiteUser


class MVHSNormalUser(BaseWebsiteUser):
    """Normal user with typical browsing patterns."""
    
    wait_time = between(10, 15)  # Wait 2-5 seconds between tasks
    weight = 0  # This user type is 3x more likely to be chosen
    
    @task(2)
    def browse_homepage(self):
        """Visit the homepage (high priority)."""
        self.navigation_tasks.visit_homepage()
        self.wait_for_reading()
    
    @task(2)
    def browse_categories(self):
        """Browse course categories."""
        result = self.navigation_tasks.browse_categories()
        if result:
            self.wait_for_reading()
    
    @task(2)
    def perform_simple_search(self):
        """Perform a simple search."""
        if self.should_perform_search():
            result = self.search_tasks.perform_search()
            if result and result.get('has_results'):
                self.wait_for_reading()
    
    @task(0)
    def view_course_details(self):
        """View course details."""
        result = self.navigation_tasks.view_course_details()
        if result:
            self.wait_for_reading()
    
    @task(1)
    def visit_static_pages(self):
        """Visit static informational pages."""
        result = self.navigation_tasks.visit_static_pages()
        if result:
            self.wait_for_reading()


class MVHSActiveUser(BaseWebsiteUser):
    """Active user with more frequent searches and interactions."""
    
    wait_time = between(5, 15) 
    weight = 16 
    
    @task(11)
    def perform_search(self):
        """Perform searches frequently."""
        result = self.search_tasks.perform_search()
        if result and result.get('has_results'):
            # Might look at first few results
            if random.random() < 0.6:
                self.navigation_tasks.view_course_details()
            self.wait_for_reading()
    
    @task(4)
    def browse_categories_thoroughly(self):
        """Browse categories and subcategories."""
        result = self.navigation_tasks.browse_categories()
        if result:
            # Often continues to subcategories
            if random.random() < 0.5:
                self.navigation_tasks.browse_subcategories()
            self.wait_for_reading()
    
    @task(3)
    def search_by_category(self):
        """Search within specific categories."""
        result = self.search_tasks.search_courses_by_category()
        if result:
            self.wait_for_reading()
    
    @task(1)
    def browse_homepage(self):
        """Visit homepage."""
        self.navigation_tasks.visit_homepage()

    @task(1)
    def visit_static_pages(self):
        """Visit static informational pages."""
        result = self.navigation_tasks.visit_static_pages()
        if result:
            self.wait_for_reading()

    
    @task(0)
    def search_instructor(self):
        """Search for courses by instructor."""
        result = self.search_tasks.search_instructor()
        if result:
            self.wait_for_reading()


class MVHSPowerUser(BaseWebsiteUser):
    """Power user with rapid, focused interactions."""
    
    wait_time = between(0.5, 2)  # Very fast interactions
    weight = 0  # Less common but intensive
    
    @task(5)
    def intensive_search(self):
        """Perform intensive search activities."""
        # Multiple searches in sequence
        search_count = random.randint(1, 3)
        for _ in range(search_count):
            search_type = random.choice([
                'simple', 
                'category'
                # 'instructor', 
                # 'advanced'
            ])
            
            if search_type == 'simple':
                self.search_tasks.perform_search()
            elif search_type == 'category':
                self.search_tasks.search_courses_by_category()
            elif search_type == 'instructor':
                self.search_tasks.search_instructor()
            elif search_type == 'advanced':
                self.search_tasks.advanced_search()
            
            # Brief pause between searches
            if search_count > 1:
                self.wait()
    
    @task(3)
    def deep_category_browsing(self):
        """Browse deeply through categories and subcategories."""
        # Browse main category
        self.navigation_tasks.browse_categories()
        
        # Almost always continues to subcategories
        if random.random() < 0.8:
            self.navigation_tasks.browse_subcategories()
            
            # Might view course details
            if random.random() < 0.6:
                self.navigation_tasks.view_course_details()
    
    @task(2)
    def advanced_search_patterns(self):
        """Use advanced search features."""
        result = self.search_tasks.advanced_search()
        if result and result.get('has_results'):
            # Power users often check multiple results
            for _ in range(random.randint(1, 3)):
                if random.random() < 0.7:
                    self.navigation_tasks.view_course_details()
                    time.sleep(random.uniform(0.5, 1.5))
    
    @task(1)
    def rapid_navigation(self):
        """Rapid navigation through different sections."""
        # Quick sequence of navigation actions
        actions = [
            self.navigation_tasks.visit_homepage,
            self.navigation_tasks.browse_categories,
            self.navigation_tasks.visit_static_pages,
            self.navigation_tasks.view_course_details
        ]
        
        # Perform 2-3 actions rapidly
        selected_actions = random.sample(actions, k=random.randint(2, 3))
        for action in selected_actions:
            action()
            time.sleep(random.uniform(0.2, 0.8))


class MVHSBrowserUser(BaseWebsiteUser):
    """Casual browser with minimal search activity."""
    
    wait_time = between(3, 8)  # Slower, more contemplative
    weight = 0  # Common casual user
    
    @task(4)
    def casual_browsing(self):
        """Casual browsing behavior."""
        self.navigation_tasks.visit_homepage()
        self.wait_for_reading()
        
        # Might browse one category
        if random.random() < 0.6:
            self.navigation_tasks.browse_categories()
            self.wait_for_reading()
    
    @task(2)
    def occasional_search(self):
        """Occasional simple search."""
        if random.random() < 0.4:  # Lower search probability
            result = self.search_tasks.perform_search()
            if result:
                self.wait_for_reading()
                
                # Rarely looks at results in detail
                if random.random() < 0.3:
                    self.navigation_tasks.view_course_details()
                    self.wait_for_reading()
    
    @task(2)
    def visit_info_pages(self):
        """Visit informational pages."""
        self.navigation_tasks.visit_static_pages()
        self.wait_for_reading()
    
    @task(1)
    def view_courses(self):
        """Occasionally view course details."""
        if random.random() < 0.5:
            result = self.navigation_tasks.view_course_details()
            if result:
                self.wait_for_reading()


class MVHSMobileUser(BaseWebsiteUser):
    """Mobile user with touch-optimized behavior patterns."""
    
    wait_time = between(1.5, 4)  # Slightly different timing for mobile
    weight = 0  # Mobile users are common
    
    def on_start(self):
        """Configure for mobile-like behavior."""
        super().on_start()
        
        # Add mobile-specific headers
        if hasattr(self.client, 'session'):
            self.client.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1'
            })
    
    @task(3)
    def mobile_homepage_browsing(self):
        """Mobile-optimized homepage browsing."""
        self.navigation_tasks.visit_homepage()
        # Mobile users might spend more time on homepage
        self.wait_for_reading()
    
    @task(3)
    def mobile_search(self):
        """Mobile search patterns (often shorter queries)."""
        if self.should_perform_search():
            # Mobile users often use shorter search terms
            short_terms = [term for term in self.search_terms if len(term) <= 8]
            if short_terms:
                search_term = random.choice(short_terms)
                result = self.search_tasks.perform_search(search_term)
                if result:
                    self.wait_for_reading()
    
    @task(2)
    def mobile_category_browsing(self):
        """Mobile category browsing (simplified)."""
        result = self.navigation_tasks.browse_categories()
        if result:
            # Mobile users less likely to browse subcategories
            if random.random() < 0.3:
                self.navigation_tasks.browse_subcategories()
            self.wait_for_reading()
    
    @task(1)
    def mobile_course_viewing(self):
        """Mobile course detail viewing."""
        result = self.navigation_tasks.view_course_details()
        if result:
            # Shorter reading time on mobile
            reading_time = random.uniform(1, 4)
            time.sleep(reading_time)


# Legacy compatibility - the main user class that was in the original locustfile.py
class MVHSWebsiteUser(MVHSNormalUser):
    """Main MVHS website user (legacy compatibility)."""
    weight = 0
