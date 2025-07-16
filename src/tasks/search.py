"""
Search tasks for load testing.

This module defines search-related tasks that simulate realistic
user search behavior on educational websites.
"""

import random
import time
import urllib.parse
from typing import Dict, Any, Optional, List
from locust import task
from bs4 import BeautifulSoup
from src.core.metrics import metrics_collector


class SearchTasks:
    """Search-related tasks for website load testing."""
    
    def __init__(self, user_instance):
        """
        Initialize search tasks.
        
        Args:
            user_instance: The Locust user instance
        """
        self.user = user_instance
        self.profile = getattr(user_instance, 'profile', {})
        self.endpoints = self.profile.get('endpoints', {})
        self.search_terms = self.profile.get('search_terms', [
            "schule", "unterricht", "lehrer", "student", "abitur", "klausur",
            "ferien", "termine", "anmeldung", "kontakt", "impressum", "news"
        ])
    
    def perform_search(self, search_term: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Perform a search query.
        
        Args:
            search_term: Specific term to search for, or None for random term
            
        Returns:
            Search results data dictionary or None if failed
        """
        if search_term is None:
            search_term = random.choice(self.search_terms)
        
        search_endpoint = self.endpoints.get('search', '/suche')
        
        # Add cache-busting parameter
        cache_buster = random.randint(100, 999999)
        search_url = f"{search_endpoint}?q={urllib.parse.quote(search_term)}_cb{cache_buster}"
        
        start_time = time.time()
        
        try:
            with self.user.client.get(search_url,
                                     catch_response=True,
                                     name=f"Search: {search_term}_cb{cache_buster}") as response:
                
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    response.success()
                    
                    # Parse search results
                    results_data = self._parse_search_results(response.text, search_term)
                    
                    # Record search metrics
                    metrics_collector.add_search_metric(
                        search_term=search_term,
                        response_time=response_time,
                        results_count=results_data['results_count'],
                        success=True
                    )
                    
                    metrics_collector.add_user_metric(
                        user_id=str(id(self.user)),
                        action=f"search_{search_term}",
                        duration=response_time,
                        success=True
                    )
                    
                    return {
                        'status_code': response.status_code,
                        'search_term': f"{search_endpoint}?q={urllib.parse.quote(search_term)}_cb{cache_buster}",
                        'response_time': response_time,
                        **results_data
                    }
                else:
                    response.failure(f"Search returned status {response.status_code}")
                    
                    # Record failed search
                    metrics_collector.add_search_metric(
                        search_term=search_term,
                        response_time=response_time,
                        results_count=0,
                        success=False
                    )
                    
                    return None
                    
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            # Record failed search
            metrics_collector.add_search_metric(
                search_term=search_term,
                response_time=response_time,
                results_count=0,
                success=False
            )
            
            self.user.environment.events.user_error.fire(
                user_instance=self.user,
                exception=e,
                tb=None
            )
            return None
    
    def search_courses_by_category(self, category_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Browse courses within a specific category using MVHS category URLs.
        
        Args:
            category_id: Specific category ID to browse, or None for random category
            
        Returns:
            Category browse results data dictionary or None if failed
        """
        # MVHS category IDs from the actual API
        mvhs_categories = [
            {"id": "460-CAT-KAT1170", "name": "Barrierefrei lernen"},
            {"id": "460-CAT-KAT6294", "name": "Mensch, Politik & Gesellschaft"},
            {"id": "460-CAT-KAT19749", "name": "Debatten & Vorträge"},
            {"id": "460-CAT-KAT20978", "name": "Eltern & Familie"},
            {"id": "460-CAT-KAT1168", "name": "Haus Buchenried"},
            {"id": "460-CAT-KAT6549", "name": "Kultur, Kunst & Kreativität"},
            {"id": "460-CAT-KAT1161", "name": "Junge Volkshochschule"},
            {"id": "460-CAT-KAT20592", "name": "München – unsere Stadt"},
            {"id": "460-CAT-KAT20772", "name": "Die MVHS im HP8"},
            {"id": "460-CAT-KAT8750", "name": "Offene Akademie"},
            {"id": "460-CAT-KAT19583", "name": "Online-Programm"},
            {"id": "460-CAT-KAT17977", "name": "Programme in English"},
            {"id": "460-CAT-KAT1162", "name": "Senioren Volkshochschule"},
            {"id": "460-CAT-KAT8845", "name": "Sommer Volkshochschule"},
            {"id": "460-CAT-KAT6946", "name": "Natur, Wissenschaft & Technik"},
            {"id": "460-CAT-KAT20854", "name": "Das neue Stadtteilzentrum Riem"},
            {"id": "460-CAT-KAT6993", "name": "Gesundheit, Umwelt & Kochkultur"},
            {"id": "460-CAT-KAT1166", "name": "Studienreisen & Reisevorträge"},
            {"id": "460-CAT-KAT21027", "name": "Zeitgeschehen & Gesellschaftsfragen"},
            {"id": "460-CAT-KAT21200", "name": "Zukünfte"},
            {"id": "460-CAT-KAT21030", "name": "KI trifft echtes Denken"},
            {"id": "460-CAT-KAT20879", "name": "Überrasch mich"},
            {"id": "460-CAT-KAT7244", "name": "Sprachen"},
            {"id": "460-CAT-KAT7711", "name": "Deutsch & Integration"},
            {"id": "460-CAT-KAT7902", "name": "Jugend & Ausbildung"},
            {"id": "460-CAT-KAT7157", "name": "Weiterbildung & Beruf"},
            {"id": "460-CAT-KAT8962", "name": "IT & Digitales"}
        ]
        
        if category_id is None:
            category_data = random.choice(mvhs_categories)
            category_id = category_data["id"]
            category_name = category_data["name"]
        else:
            # Find category name for the given ID
            category_name = next((cat["name"] for cat in mvhs_categories if cat["id"] == category_id), "Unknown")
        
        # Build MVHS category URL
        category_url = f"/kurse/{category_id}"
        
        start_time = time.time()
        
        try:
            with self.user.client.get(category_url,
                                     catch_response=True,
                                     name=f"Category: {category_name}") as response:
                
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    response.success()
                    
                    results_data = self._parse_category_results(response.text, category_name)
                    
                    metrics_collector.add_search_metric(
                        search_term=f"category:{category_name}",
                        response_time=response_time,
                        results_count=results_data['results_count'],
                        success=True
                    )
                    
                    metrics_collector.add_user_metric(
                        user_id=str(id(self.user)),
                        action=f"browse_category_{category_name}",
                        duration=response_time,
                        success=True
                    )
                    
                    return {
                        'status_code': response.status_code,
                        'category_id': category_id,
                        'category_name': category_name,
                        'category_url': category_url,
                        'response_time': response_time,
                        **results_data
                    }
                else:
                    response.failure(f"Category browse returned status {response.status_code}")
                    
                    metrics_collector.add_search_metric(
                        search_term=f"category:{category_name}",
                        response_time=response_time,
                        results_count=0,
                        success=False
                    )
                    
                    return None
                    
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            metrics_collector.add_search_metric(
                search_term=f"category:{category_name}",
                response_time=response_time,
                results_count=0,
                success=False
            )
            
            self.user.environment.events.user_error.fire(
                user_instance=self.user,
                exception=e,
                tb=None
            )
            return None
    
    def search_instructor(self, instructor_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Search for courses by instructor.
        
        Args:
            instructor_name: Instructor name to search for, or None for random name
            
        Returns:
            Search results data dictionary or None if failed
        """
        if instructor_name is None:
            # Common German names for testing
            instructor_names = [
                "Schmidt", "Müller", "Weber", "Fischer", "Meyer",
                "Wagner", "Becker", "Schulz", "Hoffmann", "Schäfer"
            ]
            instructor_name = random.choice(instructor_names)
        
        instructor_endpoint = self.endpoints.get('instructor_search', '/dozent/')
        cache_buster = random.randint(100, 999999)
        search_url = f"{instructor_endpoint}?name={urllib.parse.quote(instructor_name)}_cb{cache_buster}"
        
        start_time = time.time()
        
        try:
            with self.user.client.get(search_url,
                                     catch_response=True,
                                     name=f"Instructor: {instructor_name}") as response:
                
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    response.success()
                    
                    results_data = self._parse_instructor_results(response.text, instructor_name)
                    
                    metrics_collector.add_search_metric(
                        search_term=f"instructor:{instructor_name}",
                        response_time=response_time,
                        results_count=results_data['results_count'],
                        success=True
                    )
                    
                    return {
                        'status_code': response.status_code,
                        'instructor_name': instructor_name,
                        'response_time': response_time,
                        **results_data
                    }
                else:
                    response.failure(f"Instructor search returned status {response.status_code}")
                    return None
                    
        except Exception as e:
            self.user.environment.events.user_error.fire(
                user_instance=self.user,
                exception=e,
                tb=None
            )
            return None
    
    def advanced_search(self) -> Optional[Dict[str, Any]]:
        """
        Perform an advanced search with multiple parameters.
        
        Returns:
            Search results data dictionary or None if failed
        """
        # Build advanced search parameters
        params = {}
        
        # Random search term
        if random.random() < 0.7:  # 70% chance to include search term
            params['q'] = random.choice(self.search_terms)
        
        # Random category filter
        categories = self.profile.get('categories', [])
        if categories and random.random() < 0.5:  # 50% chance to filter by category
            category = random.choice(categories)
            params['category'] = category.get('name', '')
        
        # Random date filter
        if random.random() < 0.3:  # 30% chance to filter by date
            date_filters = ['today', 'week', 'month', 'future']
            params['date'] = random.choice(date_filters)
        
        # Random price filter
        if random.random() < 0.3:  # 30% chance to filter by price
            price_filters = ['free', 'low', 'medium', 'high']
            params['price'] = random.choice(price_filters)
        
        search_endpoint = self.endpoints.get('search', '/suche')
        query_string = urllib.parse.urlencode(params)
        cache_buster = random.randint(100, 999999)
        search_url = f"{search_endpoint}?{query_string}_cb{cache_buster}"
        
        start_time = time.time()
        
        try:
            with self.user.client.get(search_url,
                                     catch_response=True,
                                     name="Advanced Search") as response:
                
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    response.success()
                    
                    results_data = self._parse_search_results(response.text, "advanced_search")
                    
                    metrics_collector.add_search_metric(
                        search_term=f"advanced:{query_string}",
                        response_time=response_time,
                        results_count=results_data['results_count'],
                        success=True
                    )
                    
                    return {
                        'status_code': response.status_code,
                        'search_type': 'advanced',
                        'parameters': params,
                        'response_time': response_time,
                        **results_data
                    }
                else:
                    response.failure(f"Advanced search returned status {response.status_code}")
                    return None
                    
        except Exception as e:
            self.user.environment.events.user_error.fire(
                user_instance=self.user,
                exception=e,
                tb=None
            )
            return None
    
    def browse_subcategory(self, subcategory_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Browse courses within a specific subcategory using MVHS subcategory URLs.
        
        Args:
            subcategory_id: Specific subcategory ID to browse, or None for random subcategory
            
        Returns:
            Subcategory browse results data dictionary or None if failed
        """
        # MVHS subcategory IDs from the actual API (depth 2+ categories)
        mvhs_subcategories = [
            # Barrierefrei lernen subcategories
            {"id": "460-CAT-KAT21105", "name": "Aktuelle Themen", "parent": "Barrierefrei lernen"},
            {"id": "460-CAT-KAT21106", "name": "Lernen & Leben", "parent": "Barrierefrei lernen"},
            {"id": "460-CAT-KAT8068", "name": "Kultur & Kreativität", "parent": "Barrierefrei lernen"},
            {"id": "460-CAT-KAT8069", "name": "Mensch, Politik & Gesellschaft", "parent": "Barrierefrei lernen"},
            {"id": "460-CAT-KAT17924", "name": "Musik & Tanz", "parent": "Barrierefrei lernen"},
            {"id": "460-CAT-KAT8071", "name": "Bewegung & Entspannung", "parent": "Barrierefrei lernen"},
            {"id": "460-CAT-KAT8075", "name": "Computer & Internet", "parent": "Barrierefrei lernen"},
            {"id": "460-CAT-KAT8073", "name": "Rund um Sprache", "parent": "Barrierefrei lernen"},
            {"id": "460-CAT-KAT8074", "name": "Deutsche Gebärdensprache", "parent": "Barrierefrei lernen"},
            {"id": "460-CAT-KAT19406", "name": "Umgang mit Schwerhörigkeit", "parent": "Barrierefrei lernen"},
            
            # Mensch, Politik & Gesellschaft subcategories
            {"id": "460-CAT-KAT6295", "name": "Politik & Gesellschaft", "parent": "Mensch, Politik & Gesellschaft"},
            {"id": "460-CAT-KAT19162", "name": "Geschichte", "parent": "Mensch, Politik & Gesellschaft"},
            {"id": "460-CAT-KAT6427", "name": "Philosophie", "parent": "Mensch, Politik & Gesellschaft"},
            {"id": "460-CAT-KAT6477", "name": "Religionen", "parent": "Mensch, Politik & Gesellschaft"},
            {"id": "460-CAT-KAT6494", "name": "Psychologie", "parent": "Mensch, Politik & Gesellschaft"},
            {"id": "460-CAT-KAT6510", "name": "Lernen & Gedächtnis", "parent": "Mensch, Politik & Gesellschaft"},
            {"id": "460-CAT-KAT19114", "name": "Studium Generale", "parent": "Mensch, Politik & Gesellschaft"},
            {"id": "460-CAT-KAT19438", "name": "Programme in English", "parent": "Mensch, Politik & Gesellschaft"},
            {"id": "460-CAT-KAT21057", "name": "Verbraucherbildung", "parent": "Mensch, Politik & Gesellschaft"},
            
            # Debatten & Vorträge subcategories
            {"id": "460-CAT-KAT20578", "name": "Politik & Gesellschaft", "parent": "Debatten & Vorträge"},
            {"id": "460-CAT-KAT20579", "name": "Geschichte", "parent": "Debatten & Vorträge"},
            {"id": "460-CAT-KAT19751", "name": "Philosophie", "parent": "Debatten & Vorträge"},
            {"id": "460-CAT-KAT19752", "name": "Religionen", "parent": "Debatten & Vorträge"},
            {"id": "460-CAT-KAT19753", "name": "Psychologie", "parent": "Debatten & Vorträge"},
            {"id": "460-CAT-KAT19754", "name": "Literatur & Film", "parent": "Debatten & Vorträge"},
            {"id": "460-CAT-KAT19755", "name": "Musik", "parent": "Debatten & Vorträge"},
            {"id": "460-CAT-KAT19756", "name": "Kunst- und Kulturgeschichte", "parent": "Debatten & Vorträge"},
            {"id": "460-CAT-KAT19757", "name": "MVHS unterwegs", "parent": "Debatten & Vorträge"},
            {"id": "460-CAT-KAT19758", "name": "Natur, Wissenschaft & Technik", "parent": "Debatten & Vorträge"},
            {"id": "460-CAT-KAT19759", "name": "Gesundheit, Umwelt & Kochkultur", "parent": "Debatten & Vorträge"},
            {"id": "460-CAT-KAT19760", "name": "Weiterbildung & Beruf", "parent": "Debatten & Vorträge"},
            {"id": "460-CAT-KAT19761", "name": "Fremdsprachige Vorträge", "parent": "Debatten & Vorträge"},
            
            # Eltern & Familie subcategories
            {"id": "460-CAT-KAT20979", "name": "Für Eltern", "parent": "Eltern & Familie"},
            {"id": "460-CAT-KAT20982", "name": "Für die ganze Familie", "parent": "Eltern & Familie"},
            
            # Haus Buchenried subcategories
            {"id": "460-CAT-KAT8087", "name": "Politik, Gesellschaft & Geschichte", "parent": "Haus Buchenried"},
            {"id": "460-CAT-KAT18795", "name": "Philosophie & Religionen", "parent": "Haus Buchenried"},
            {"id": "460-CAT-KAT20450", "name": "Naturwissenschaften", "parent": "Haus Buchenried"},
            {"id": "460-CAT-KAT18794", "name": "Psychologie", "parent": "Haus Buchenried"},
            {"id": "460-CAT-KAT8089", "name": "Kunst & Kreativität", "parent": "Haus Buchenried"},
            {"id": "460-CAT-KAT20451", "name": "Kunst- und Kulturgeschichte", "parent": "Haus Buchenried"},
            {"id": "460-CAT-KAT18796", "name": "Fotografie & Video", "parent": "Haus Buchenried"},
            {"id": "460-CAT-KAT20452", "name": "Literatur & Film", "parent": "Haus Buchenried"},
            {"id": "460-CAT-KAT18797", "name": "Schreibwerkstätten", "parent": "Haus Buchenried"},
            {"id": "460-CAT-KAT18798", "name": "Theater & Stimme", "parent": "Haus Buchenried"},
            {"id": "460-CAT-KAT8092", "name": "Musik", "parent": "Haus Buchenried"},
            {"id": "460-CAT-KAT20453", "name": "Tanz", "parent": "Haus Buchenried"},
            {"id": "460-CAT-KAT18799", "name": "Körpererfahrung & Entspannung", "parent": "Haus Buchenried"},
            {"id": "460-CAT-KAT18800", "name": "Bewegung & Ernährung", "parent": "Haus Buchenried"},
            {"id": "460-CAT-KAT8094", "name": "Beruf & Karriere", "parent": "Haus Buchenried"},
            {"id": "460-CAT-KAT8095", "name": "Sprachen am See", "parent": "Haus Buchenried"},
            {"id": "460-CAT-KAT20534", "name": "Junge Volkshochschule", "parent": "Haus Buchenried"},
            {"id": "460-CAT-KAT18744", "name": "Buchenrieder Kunstsommer", "parent": "Haus Buchenried"}
        ]
        
        if subcategory_id is None:
            subcategory_data = random.choice(mvhs_subcategories)
            subcategory_id = subcategory_data["id"]
            subcategory_name = subcategory_data["name"]
            parent_category = subcategory_data["parent"]
        else:
            # Find subcategory name and parent for the given ID
            subcategory_data = next((cat for cat in mvhs_subcategories if cat["id"] == subcategory_id), None)
            if subcategory_data:
                subcategory_name = subcategory_data["name"]
                parent_category = subcategory_data["parent"]
            else:
                subcategory_name = "Unknown"
                parent_category = "Unknown"
        
        # Build MVHS subcategory URL
        subcategory_url = f"/kurse/{subcategory_id}"
        
        start_time = time.time()
        
        try:
            with self.user.client.get(subcategory_url,
                                     catch_response=True,
                                     name=f"Subcategory: {subcategory_name}") as response:
                
                response_time = (time.time() - start_time) * 1000
                
                if response.status_code == 200:
                    response.success()
                    
                    results_data = self._parse_category_results(response.text, subcategory_name)
                    
                    metrics_collector.add_search_metric(
                        search_term=f"subcategory:{subcategory_name}",
                        response_time=response_time,
                        results_count=results_data['results_count'],
                        success=True
                    )
                    
                    metrics_collector.add_user_metric(
                        user_id=str(id(self.user)),
                        action=f"browse_subcategory_{subcategory_name}",
                        duration=response_time,
                        success=True
                    )
                    
                    return {
                        'status_code': response.status_code,
                        'subcategory_id': subcategory_id,
                        'subcategory_name': subcategory_name,
                        'parent_category': parent_category,
                        'subcategory_url': subcategory_url,
                        'response_time': response_time,
                        **results_data
                    }
                else:
                    response.failure(f"Subcategory browse returned status {response.status_code}")
                    
                    metrics_collector.add_search_metric(
                        search_term=f"subcategory:{subcategory_name}",
                        response_time=response_time,
                        results_count=0,
                        success=False
                    )
                    
                    return None
                    
        except Exception as e:
            response_time = (time.time() - start_time) * 1000
            
            metrics_collector.add_search_metric(
                search_term=f"subcategory:{subcategory_name}",
                response_time=response_time,
                results_count=0,
                success=False
            )
            
            self.user.environment.events.user_error.fire(
                user_instance=self.user,
                exception=e,
                tb=None
            )
            return None
    
    def _parse_search_results(self, html_content: str, search_term: str) -> Dict[str, Any]:
        """
        Parse search results from HTML content.
        
        Args:
            html_content: HTML content to parse
            search_term: The search term used
            
        Returns:
            Dictionary containing parsed results data
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for common result count indicators
            results_count = 0
            count_selectors = [
                '.results-count',
                '.search-results-count',
                '.anzahl-ergebnisse',
                '[class*="count"]'
            ]
            
            for selector in count_selectors:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    # Extract numbers from text
                    import re
                    numbers = re.findall(r'\d+', text)
                    if numbers:
                        results_count = int(numbers[0])
                        break
            
            # Fallback: count result items
            if results_count == 0:
                result_selectors = [
                    '.search-result',
                    '.result-item',
                    '.course-item',
                    '.kurs-item',
                    '[class*="result"]',
                    '[class*="course"]'
                ]
                
                for selector in result_selectors:
                    elements = soup.select(selector)
                    if elements:
                        results_count = len(elements)
                        break
            
            # Extract result titles for quality assessment
            result_titles = []
            title_selectors = [
                '.result-title',
                '.course-title',
                '.kurs-titel',
                'h3',
                'h4'
            ]
            
            for selector in title_selectors:
                elements = soup.select(selector)
                for element in elements[:5]:  # Limit to first 5 titles
                    title = element.get_text(strip=True)
                    if title:
                        result_titles.append(title)
            
            return {
                'results_count': results_count,
                'result_titles': result_titles,
                'has_results': results_count > 0,
                'page_size': len(html_content)
            }
            
        except Exception:
            return {
                'results_count': 0,
                'result_titles': [],
                'has_results': False,
                'page_size': len(html_content)
            }
    
    def _parse_category_results(self, html_content: str, category_name: str) -> Dict[str, Any]:
        """
        Parse category browse results from HTML content.
        
        Args:
            html_content: HTML content to parse
            category_name: The category name browsed
            
        Returns:
            Dictionary containing parsed category results
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for course listings in MVHS category pages
            courses_count = 0
            
            # Common MVHS course item selectors
            course_selectors = [
                '.course-item',
                '.kurs-item',
                '.course-card',
                '.event-item',
                '[class*="course"]',
                '[class*="kurs"]',
                '[class*="event"]',
                'article',
                '.program-item'
            ]
            
            for selector in course_selectors:
                elements = soup.select(selector)
                if elements:
                    courses_count = len(elements)
                    break
            
            # Extract course titles for quality assessment
            course_titles = []
            title_selectors = [
                '.course-title',
                '.kurs-titel',
                'h3',
                'h4',
                'h2',
                '.title',
                '[class*="title"]'
            ]
            
            for selector in title_selectors:
                elements = soup.select(selector)
                for element in elements[:5]:  # Limit to first 5 titles
                    title = element.get_text(strip=True)
                    if title and len(title) > 5:  # Filter out very short titles
                        course_titles.append(title)
            
            # Look for category description
            description = ""
            description_selectors = [
                '.category-description',
                '.beschreibung',
                '.intro',
                '.description'
            ]
            
            for selector in description_selectors:
                element = soup.select_one(selector)
                if element:
                    description = element.get_text(strip=True)[:200]  # Limit length
                    break
            
            return {
                'results_count': courses_count,
                'course_titles': course_titles,
                'category_description': description,
                'has_results': courses_count > 0,
                'page_size': len(html_content)
            }
            
        except Exception:
            return {
                'results_count': 0,
                'course_titles': [],
                'category_description': "",
                'has_results': False,
                'page_size': len(html_content)
            }
    
    def _parse_instructor_results(self, html_content: str, instructor_name: str) -> Dict[str, Any]:
        """
        Parse instructor search results from HTML content.
        
        Args:
            html_content: HTML content to parse
            instructor_name: The instructor name searched for
            
        Returns:
            Dictionary containing parsed instructor results
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for instructor profiles or course results
            instructor_count = 0
            courses_count = 0
            
            # Count instructor profiles
            instructor_selectors = [
                '.instructor-profile',
                '.dozent-profil',
                '.teacher-card',
                '[class*="instructor"]',
                '[class*="dozent"]'
            ]
            
            for selector in instructor_selectors:
                elements = soup.select(selector)
                if elements:
                    instructor_count = len(elements)
                    break
            
            # Count courses by this instructor
            course_selectors = [
                '.course-item',
                '.kurs-item',
                '[class*="course"]',
                '[class*="kurs"]'
            ]
            
            for selector in course_selectors:
                elements = soup.select(selector)
                if elements:
                    courses_count = len(elements)
                    break
            
            return {
                'results_count': instructor_count + courses_count,
                'instructor_count': instructor_count,
                'courses_count': courses_count,
                'has_results': (instructor_count + courses_count) > 0,
                'page_size': len(html_content)
            }
            
        except Exception:
            return {
                'results_count': 0,
                'instructor_count': 0,
                'courses_count': 0,
                'has_results': False,
                'page_size': len(html_content)
            }
