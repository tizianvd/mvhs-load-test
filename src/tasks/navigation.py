"""
Website navigation tasks for load testing.

This module defines common navigation tasks that simulate realistic
user behavior when browsing educational websites.
"""

import random
import time
from typing import Dict, Any, Optional, List
from locust import task
from bs4 import BeautifulSoup
from src.core.metrics import metrics_collector


class NavigationTasks:
    """Common navigation tasks for website load testing."""
    
    def __init__(self, user_instance):
        """
        Initialize navigation tasks.
        
        Args:
            user_instance: The Locust user instance
        """
        self.user = user_instance
        self.profile = getattr(user_instance, 'profile', {})
        self.endpoints = self.profile.get('endpoints', {})
        self.categories = self.profile.get('categories', [])
    
    def visit_homepage(self) -> Optional[Dict[str, Any]]:
        """
        Visit the website homepage.
        
        Returns:
            Response data dictionary or None if failed
        """
        try:
            with self.user.client.get("/", 
                                     catch_response=True, 
                                     name="Homepage") as response:
                if response.status_code == 200:
                    response.success()
                    return {
                        'status_code': response.status_code,
                        'content_length': len(response.content),
                        'response_time': response.elapsed.total_seconds() * 1000
                    }
                else:
                    response.failure(f"Homepage returned status {response.status_code}")
                    return None
        except Exception as e:
            self.user.environment.events.user_error.fire(
                user_instance=self.user, 
                exception=e, 
                tb=None
            )
            return None
    
    def browse_categories(self) -> Optional[Dict[str, Any]]:
        """
        Browse through available course categories.
        
        Returns:
            Response data dictionary or None if failed
        """
        if not self.categories:
            return None
        
        category = random.choice(self.categories)
        category_url = category.get('url', '')
        category_name = category.get('name', 'Unknown Category')
        
        if not category_url:
            return None
        
        try:
            with self.user.client.get(category_url,
                                     catch_response=True,
                                     name=f"Category: {category_name}") as response:
                if response.status_code == 200:
                    response.success()
                    
                    # Extract course count if possible
                    course_count = self._extract_course_count(response.text)
                    
                    metrics_collector.add_user_metric(
                        user_id=str(id(self.user)),
                        action=f"browse_category_{category_name}",
                        duration=response.elapsed.total_seconds() * 1000,
                        success=True
                    )
                    
                    return {
                        'status_code': response.status_code,
                        'category': category_name,
                        'course_count': course_count,
                        'response_time': response.elapsed.total_seconds() * 1000
                    }
                else:
                    response.failure(f"Category page returned status {response.status_code}")
                    return None
        except Exception as e:
            self.user.environment.events.user_error.fire(
                user_instance=self.user,
                exception=e,
                tb=None
            )
            return None
    
    def browse_subcategories(self) -> Optional[Dict[str, Any]]:
        """
        Browse through subcategories within a main category.
        
        Returns:
            Response data dictionary or None if failed
        """
        if not self.categories:
            return None
        
        # Find a category with subcategories
        categories_with_subs = [cat for cat in self.categories if cat.get('subcategories')]
        if not categories_with_subs:
            return None
        
        category = random.choice(categories_with_subs)
        subcategory = random.choice(category['subcategories'])
        
        # Build subcategory URL
        subcategory_url = f"/kurse/{subcategory}"
        
        try:
            with self.user.client.get(subcategory_url,
                                     catch_response=True,
                                     name=f"Subcategory: {subcategory}") as response:
                if response.status_code == 200:
                    response.success()
                    
                    course_count = self._extract_course_count(response.text)
                    
                    metrics_collector.add_user_metric(
                        user_id=str(id(self.user)),
                        action=f"browse_subcategory_{subcategory}",
                        duration=response.elapsed.total_seconds() * 1000,
                        success=True
                    )
                    
                    return {
                        'status_code': response.status_code,
                        'subcategory': subcategory,
                        'course_count': course_count,
                        'response_time': response.elapsed.total_seconds() * 1000
                    }
                else:
                    response.failure(f"Subcategory page returned status {response.status_code}")
                    return None
        except Exception as e:
            self.user.environment.events.user_error.fire(
                user_instance=self.user,
                exception=e,
                tb=None
            )
            return None
    
    def view_course_details(self, course_url: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        View details of a specific course.
        
        Args:
            course_url: Specific course URL to view, or None for random course
            
        Returns:
            Response data dictionary or None if failed
        """
        if course_url is None:
            # Generate a random course URL for testing
            course_id = random.randint(1000, 999999)
            course_url = self.endpoints.get('course_detail', '/kurse//deutsch-integration/online-sommer-intensivwoche-deutsch-fuer-den-beruf-schreiben-b1-b2/uebungen-zu-verhandlungssicherem-schriftlichen-ausdruck-460-C-U665710')
        
        try:
            with self.user.client.get(course_url,
                                     catch_response=True,
                                     name="Course Details") as response:
                if response.status_code == 200:
                    response.success()
                    
                    # Extract course information
                    course_info = self._extract_course_info(response.text)
                    
                    metrics_collector.add_user_metric(
                        user_id=str(id(self.user)),
                        action="view_course_details",
                        duration=response.elapsed.total_seconds() * 1000,
                        success=True
                    )
                    
                    return {
                        'status_code': response.status_code,
                        'course_url': course_url,
                        'course_info': course_info,
                        'response_time': response.elapsed.total_seconds() * 1000
                    }
                else:
                    response.failure(f"Course details returned status {response.status_code}")
                    return None
        except Exception as e:
            self.user.environment.events.user_error.fire(
                user_instance=self.user,
                exception=e,
                tb=None
            )
            return None
    
    def visit_static_pages(self) -> Optional[Dict[str, Any]]:
        """
        Visit common static pages like contact, about, etc.
        
        Returns:
            Response data dictionary or None if failed
        """
        static_pages = [
            ("/kontakt", "Contact"),
            ("/impressum", "Impressum"),
            ("/ueber-uns", "About Us"),
            ("/datenschutzerklaerung", "Privacy Policy"),
            ("/agb", "Terms of Service"),
            ("/anmeldung-beratung", "Registration & Consultation"),
        ]
        
        page_url, page_name = random.choice(static_pages)
        
        try:
            with self.user.client.get(page_url,
                                     catch_response=True,
                                     name=f"Static: {page_name}") as response:
                if response.status_code == 200:
                    response.success()
                    
                    metrics_collector.add_user_metric(
                        user_id=str(id(self.user)),
                        action=f"visit_static_{page_name.lower().replace(' ', '_')}",
                        duration=response.elapsed.total_seconds() * 1000,
                        success=True
                    )
                    
                    return {
                        'status_code': response.status_code,
                        'page_name': page_name,
                        'response_time': response.elapsed.total_seconds() * 1000
                    }
                else:
                    response.failure(f"Static page {page_name} returned status {response.status_code}")
                    return None
        except Exception as e:
            self.user.environment.events.user_error.fire(
                user_instance=self.user,
                exception=e,
                tb=None
            )
            return None
    
    def _extract_course_count(self, html_content: str) -> int:
        """
        Extract the number of courses from page content.
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            Number of courses found, or 0 if parsing fails
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for common course count indicators
            count_selectors = [
                '.course-count',
                '.results-count',
                '.anzahl-kurse',
                '[class*="count"]',
                '[class*="anzahl"]'
            ]
            
            for selector in count_selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    # Extract numbers from text
                    import re
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        return int(numbers[0])
            
            # Fallback: count course-like elements
            course_elements = soup.select('.course, .kurs, [class*="course"], [class*="kurs"]')
            return len(course_elements)
            
        except Exception:
            return 0
    
    def _extract_course_info(self, html_content: str) -> Dict[str, Any]:
        """
        Extract course information from course detail page.
        
        Args:
            html_content: HTML content to parse
            
        Returns:
            Dictionary containing course information
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            info = {}
            
            # Extract course title
            title_selectors = ['h1', '.course-title', '.kurs-titel', '.title']
            for selector in title_selectors:
                element = soup.select_one(selector)
                if element:
                    info['title'] = element.get_text(strip=True)
                    break
            
            # Extract course price
            price_selectors = ['.price', '.preis', '.cost', '.kosten', '[class*="price"]', '[class*="preis"]']
            for selector in price_selectors:
                element = soup.select_one(selector)
                if element:
                    info['price'] = element.get_text(strip=True)
                    break
            
            # Extract course duration
            duration_selectors = ['.duration', '.dauer', '.zeit', '[class*="duration"]', '[class*="dauer"]']
            for selector in duration_selectors:
                element = soup.select_one(selector)
                if element:
                    info['duration'] = element.get_text(strip=True)
                    break
            
            return info
            
        except Exception:
            return {}
