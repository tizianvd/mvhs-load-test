import random
import time
import json
import csv
import os
from datetime import datetime
from locust import HttpUser, task, between, events
import requests
import urllib3
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter


def load_website_profiles():
    """Load website profiles configuration"""
    try:
        with open('website_profiles.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def get_active_profile():
    """Get the active website profile configuration from environment"""
    profiles_config = load_website_profiles()
    if not profiles_config:
        return None
    
    profile_name = os.environ.get('WEBSITE_PROFILE', 'mvhs_production')
    return profiles_config['profiles'].get(profile_name, profiles_config['profiles']['mvhs_production'])

# Global variable to store the current profile for web UI
current_website_profile = None

def get_profile_for_web_ui():
    """Get the profile that can be dynamically changed via web UI"""
    global current_website_profile
    if current_website_profile is None:
        current_website_profile = get_active_profile()
        if current_website_profile:
            print(f"🌐 Initialized web UI profile: {current_website_profile.get('name', 'Unknown')}")
    return current_website_profile

def set_profile_for_web_ui(profile_name):
    """Set the profile for web UI usage"""
    global current_website_profile
    profiles_config = load_website_profiles()
    if profiles_config and profile_name in profiles_config['profiles']:
        current_website_profile = profiles_config['profiles'][profile_name]
        os.environ['WEBSITE_PROFILE'] = profile_name
        print(f"✅ Profile changed to: {current_website_profile.get('name', 'Unknown')} ({profile_name})")
        print(f"🎯 Target URL: {current_website_profile.get('base_url', 'Unknown')}")
        print(f"📂 Categories available: {len(current_website_profile.get('categories', []))}")
        return True
    return False

def refresh_user_profile(user_instance):
    """Refresh a user's profile configuration (called when profile changes)"""
    if not hasattr(user_instance, 'profile'):
        return
    
    new_profile = get_profile_for_web_ui()
    if new_profile and new_profile != user_instance.profile:
        print(f"🔄 Refreshing user profile from {user_instance.profile.get('name', 'Unknown')} to {new_profile.get('name', 'Unknown')}")
        user_instance.profile = new_profile
        
        # Refresh search terms
        user_instance.search_terms = new_profile.get('search_terms', [
            "schule", "unterricht", "lehrer", "student", "abitur", "klausur",
            "ferien", "termine", "anmeldung", "kontakt", "impressum", "news"
        ])
        
        # Refresh category URLs
        user_instance.category_urls = []
        user_instance.subcategory_urls = []
        
        for category in new_profile.get('categories', []):
            category_url = category.get('url', '')
            if category_url:
                user_instance.category_urls.append(category_url)
            
            for subcategory in category.get('subcategories', []):
                subcategory_url = f"/kurse/{subcategory}"
                user_instance.subcategory_urls.append(subcategory_url)
        
        # Refresh endpoints
        user_instance.endpoints = new_profile.get('endpoints', {
            'search': '/suche',
            'course_detail': '/kurse/',
            'categories': '/kurse/',
            'instructor_search': '/dozent/'
        })
        
        print(f"✅ User profile refreshed: {len(user_instance.category_urls)} categories, {len(user_instance.subcategory_urls)} subcategories")

def load_stress_config():
    """Load stress test configuration"""
    try:
        with open('stress_test_config.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def get_current_stress_config():
    """Get current stress test configuration from environment"""
    config = load_stress_config()
    profile = get_active_profile()
    
    if not config:
        return None
    
    test_name = os.environ.get('STRESS_TEST_NAME', 'medium_stress')
    search_intensity = os.environ.get('SEARCH_INTENSITY', 'medium')
    scenarios = os.environ.get('SCENARIOS', 'search,browse').split(',')
    
    return {
        'test_config': config['stress_tests'].get(test_name, config['stress_tests']['medium_stress']),
        'search_intensity': config['search_intensities'].get(search_intensity, config['search_intensities']['medium']),
        'scenarios': scenarios,
        'profile': profile
    }


class MVHSSearchUser(HttpUser):
    """
    High-concurrency Locust user class for aggressive stress testing mvhs.de
    Optimized for maximum RPS and true concurrency
    """
    
    # Default weight - will be set to 0 in realistic mode
    weight = 1
    
    # Force zero wait time for maximum concurrency
    wait_time = between(0, 0)
    
    # Increase connection pool size for better concurrency
    connection_timeout = 5.0
    network_timeout = 10.0
    
    def __init__(self, environment):
        super().__init__(environment)
        self.stress_config = get_current_stress_config()
        
        # Configure HTTP session for high concurrency
        self._configure_http_session()
    
    def _configure_http_session(self):
        """Configure HTTP session for maximum concurrency"""
        # Increase connection pool size
        adapter = HTTPAdapter(
            pool_connections=100,  # Number of connection pools
            pool_maxsize=100,      # Number of connections in each pool
            max_retries=Retry(
                total=1,
                backoff_factor=0.1,
                status_forcelist=[500, 502, 503, 504]
            )
        )
        
        # Apply adapter to both HTTP and HTTPS
        self.client.mount("http://", adapter)
        self.client.mount("https://", adapter)
        
        # Disable SSL warnings for performance (optional)
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # Set aggressive timeouts
        self.client.timeout = (self.connection_timeout, self.network_timeout)
    
    def on_start(self):
        """Called when a simulated user starts"""
        # Ensure profile is properly loaded - prioritize web UI profile, then fallback
        self.profile = None
        
        # First try to get web UI profile
        web_ui_profile = get_profile_for_web_ui()
        if web_ui_profile:
            self.profile = web_ui_profile
            print(f"🌐 Using Web UI profile: {self.profile.get('name', 'Unknown')}")
        
        # Fallback to stress config profile
        elif self.stress_config and self.stress_config.get('profile'):
            self.profile = self.stress_config['profile']
            print(f"⚙️ Using stress config profile: {self.profile.get('name', 'Unknown')}")
        
        # Final fallback to active profile
        else:
            self.profile = get_active_profile()
            if self.profile:
                print(f"🔄 Using default active profile: {self.profile.get('name', 'Unknown')}")
        
        if self.profile:
            # Use profile-specific search terms and categories
            self.search_terms = self.profile.get('search_terms', [
                "schule", "unterricht", "lehrer", "student", "abitur", "klausur",
                "ferien", "termine", "anmeldung", "kontakt", "impressum", "news"
            ])
            
            # Extract category URLs for browsing
            self.category_urls = []
            self.subcategory_urls = []
            
            categories = self.profile.get('categories', [])
            print(f"📂 Loading {len(categories)} categories for browsing")
            
            for category in categories:
                category_url = category.get('url', '')
                if category_url:
                    self.category_urls.append(category_url)
                    print(f"   ✅ Main category: {category.get('name', 'Unnamed')} -> {category_url}")
                
                # Add subcategories
                subcategories = category.get('subcategories', [])
                for subcategory in subcategories:
                    # Construct full subcategory URL
                    subcategory_url = f"/kurse/{subcategory}"
                    self.subcategory_urls.append(subcategory_url)
                    print(f"      ➡️ Subcategory: {subcategory_url}")
            
            print(f"🎯 Category browsing initialized: {len(self.category_urls)} main categories, {len(self.subcategory_urls)} subcategories")
            
            # Get endpoints from profile
            self.endpoints = self.profile.get('endpoints', {
                'search': '/suche',
                'course_detail': '/kurse/',
                'categories': '/kurse/',
                'instructor_search': '/dozent/'
            })
            
            # Configure request settings from profile
            request_settings = self.profile.get('request_settings', {})
            if 'timeout' in request_settings:
                self.client.timeout = request_settings['timeout']
            
            # Set custom headers if specified in profile
            headers = request_settings.get('headers', {})
            self.client.headers.update(headers)
        else:
            # Fallback to default values
            self.search_terms = [
                "schule", "unterricht", "lehrer", "student", "abitur", "klausur",
                "ferien", "termine", "anmeldung", "kontakt", "impressum", "news"
            ]
            self.category_urls = []
            self.subcategory_urls = []
            self.endpoints = {
                'search': '/suche',
                'course_detail': '/kurse/',
                'categories': '/kurse/',
                'instructor_search': '/dozent/'
            }
        
        # Fast pages for rotation
        self.fast_pages = ["/", "/kontakt", "/impressum", "/anmeldung-beratung", "/datenschutzerklaerung"]
        
        self.session_start_time = time.time()
        self.request_count = 0
        self.last_profile_check = time.time()
        
    def check_profile_update(self):
        """Check if profile has been updated via web UI and refresh if needed"""
        current_time = time.time()
        # Check every 30 seconds
        if current_time - self.last_profile_check > 30:
            self.last_profile_check = current_time
            refresh_user_profile(self)
    
    def get_current_profile_info(self):
        """Get current profile information for debugging"""
        if hasattr(self, 'profile') and self.profile:
            return {
                'name': self.profile.get('name', 'Unknown'),
                'base_url': self.profile.get('base_url', 'Unknown'),
                'categories_count': len(self.category_urls) if hasattr(self, 'category_urls') else 0,
                'subcategories_count': len(self.subcategory_urls) if hasattr(self, 'subcategory_urls') else 0
            }
        return {'name': 'No Profile', 'base_url': 'Unknown', 'categories_count': 0, 'subcategories_count': 0}
        
    # HIGH CONCURRENCY TASKS - Simplified for maximum RPS
    
    @task(2000)
    def ultra_spam_homepage(self):
        """Maximum concurrency homepage spam - Weight: 2000"""
        self.request_count += 1
        self.client.get("/")
    
    @task(1500)
    def ultra_spam_search(self):
        """Maximum concurrency search spam - Weight: 1500"""
        self.request_count += 1
        term = random.choice(self.search_terms)
        search_endpoint = self.endpoints.get('search', '/suche')
        cache_buster = random.randint(100000, 999999)
        # Handle different search endpoint formats
        if '?' in search_endpoint:
            search_url = f"{search_endpoint}&q={term}_cb={cache_buster}"
        else:
            search_url = f"{search_endpoint}?q={term}_cb={cache_buster}"
        self.client.get(search_url)
    
    @task(1000)
    def ultra_spam_pages(self):
        """Maximum concurrency page spam - Weight: 1000"""
        self.request_count += 1
        page = random.choice(self.fast_pages)
        self.client.get(page)
    
    @task(800)
    def rapid_fire_requests(self):
        """Rapid fire mixed requests - Weight: 800"""
        self.request_count += 1
        # Randomly choose between homepage, search, or page
        choice = random.randint(1, 3)
        if choice == 1:
            self.client.get("/")
        elif choice == 2:
            term = random.choice(self.search_terms)
            search_endpoint = self.endpoints.get('search', '/suche')
            cache_buster = random.randint(100000, 999999)
            if '?' in search_endpoint:
                search_url = f"{search_endpoint}&q={term}_cb={cache_buster}"
            else:
                search_url = f"{search_endpoint}?q={term}_cb={cache_buster}"
            self.client.get(search_url)
        else:
            page = random.choice(self.fast_pages)
            self.client.get(page)
    
    @task(600)
    def browse_main_categories(self):
        """Browse main category pages - Weight: 600"""
        self.request_count += 1
        # Periodically check for profile updates
        self.check_profile_update()
        
        if self.category_urls:
            category_url = random.choice(self.category_urls)
            print(f"🏠 Browsing main category: {category_url}")
            with self.client.get(category_url, name="browse_main_category", catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                    print(f"   ✅ Success: {response.status_code} - Size: {len(response.content)} bytes")
                else:
                    response.failure(f"Category page returned {response.status_code}")
                    print(f"   ❌ Failed: {response.status_code}")
        else:
            profile_info = self.get_current_profile_info()
            print(f"⚠️ No category URLs available for browsing")
            print(f"   Profile: {profile_info['name']} - Categories: {profile_info['categories_count']}")
            print("   Check profile configuration and ensure categories are properly loaded")
    
    @task(400)
    def browse_subcategories(self):
        """Browse subcategory pages - Weight: 400"""
        self.request_count += 1
        if self.subcategory_urls:
            subcategory_url = random.choice(self.subcategory_urls)
            print(f"📁 Browsing subcategory: {subcategory_url}")
            with self.client.get(subcategory_url, name="browse_subcategory", catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                    print(f"   ✅ Success: {response.status_code} - Size: {len(response.content)} bytes")
                else:
                    response.failure(f"Subcategory page returned {response.status_code}")
                    print(f"   ❌ Failed: {response.status_code}")
        else:
            print("⚠️ No subcategory URLs available for browsing - check profile configuration")
    
    @task(300)
    def deep_category_browsing(self):
        """Deep category browsing simulation - Weight: 300"""
        self.request_count += 1
        # Simulate user browsing from main category to subcategory
        if self.category_urls and self.subcategory_urls:
            # First visit main category
            main_category = random.choice(self.category_urls)
            print(f"🔍 Deep browsing - Main category: {main_category}")
            with self.client.get(main_category, name="deep_browse_main", catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                    print(f"   ✅ Main category success: {response.status_code}")
                    # Then visit related subcategory
                    subcategory = random.choice(self.subcategory_urls)
                    print(f"   📁 Following to subcategory: {subcategory}")
                    with self.client.get(subcategory, name="deep_browse_sub", catch_response=True) as sub_response:
                        if sub_response.status_code == 200:
                            sub_response.success()
                            print(f"      ✅ Subcategory success: {sub_response.status_code}")
                        else:
                            sub_response.failure(f"Subcategory returned {sub_response.status_code}")
                            print(f"      ❌ Subcategory failed: {sub_response.status_code}")
                else:
                    response.failure(f"Main category returned {response.status_code}")
                    print(f"   ❌ Main category failed: {response.status_code}")
        else:
            print("⚠️ Deep browsing skipped - insufficient category/subcategory URLs")
    
    @task(200)
    def realistic_category_exploration(self):
        """Realistic category exploration pattern - Weight: 200"""
        self.request_count += 1
        
        if not self.profile or not self.profile.get('categories'):
            print("⚠️ Realistic exploration skipped - no profile or categories available")
            return
            
        # Pick a random category and explore it thoroughly
        category = random.choice(self.profile['categories'])
        print(f"🎭 Realistic exploration of: {category.get('name', 'Unnamed Category')}")
        
        # Visit main category page
        main_url = category['url']
        print(f"   🏠 Visiting main category: {main_url}")
        with self.client.get(main_url, name="realistic_category_main", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
                print(f"      ✅ Main category success: {response.status_code}")
                
                # 70% chance to explore subcategories
                if random.random() < 0.7 and category.get('subcategories'):
                    subcategory_id = random.choice(category['subcategories'])
                    subcategory_url = f"/kurse/{subcategory_id}"
                    print(f"   📁 Exploring subcategory: {subcategory_url}")
                    
                    with self.client.get(subcategory_url, name="realistic_category_sub", catch_response=True) as sub_response:
                        if sub_response.status_code == 200:
                            sub_response.success()
                            print(f"      ✅ Subcategory success: {sub_response.status_code}")
                            
                            # 30% chance to do a search within the category
                            if random.random() < 0.3 and self.search_terms:
                                search_term = random.choice(self.search_terms)
                                cache_buster = random.randint(100000, 999999)
                                search_url = f"{self.endpoints.get('search', '/kurse/suche')}?q={search_term}&category={subcategory_id}_cb={cache_buster}"
                                print(f"      🔍 Category search: {search_term} in {subcategory_id}")
                                with self.client.get(search_url, name="realistic_category_search", catch_response=True) as search_response:
                                    if search_response.status_code == 200:
                                        search_response.success()
                                        print(f"         ✅ Category search success: {search_response.status_code}")
                                    else:
                                        search_response.failure(f"Category search failed: {search_response.status_code}")
                                        print(f"         ❌ Category search failed: {search_response.status_code}")
                        else:
                            sub_response.failure(f"Subcategory failed: {sub_response.status_code}")
                            print(f"      ❌ Subcategory failed: {sub_response.status_code}")
                else:
                    print("   ⏭️ Skipping subcategory exploration (random choice or no subcategories)")
            else:
                response.failure(f"Main category failed: {response.status_code}")
                print(f"   ❌ Main category failed: {response.status_code}")
    
    @task(600)
    def concurrent_burst(self):
        """Burst of concurrent requests - Weight: 600"""
        self.request_count += 1
        # Fire multiple quick requests in sequence
        endpoints = ["/", "/kontakt"]
        
        # Add search endpoint with term
        if self.search_terms:
            term = random.choice(self.search_terms)
            search_endpoint = self.endpoints.get('search', '/suche')
            cache_buster = random.randint(100000, 999999)
            if '?' in search_endpoint:
                search_url = f"{search_endpoint}&q={term}_cb={cache_buster}"
            else:
                search_url = f"{search_endpoint}?q={term}_cb={cache_buster}"
            endpoints.append(search_url)
        
        endpoint = random.choice(endpoints)
        self.client.get(endpoint)

def setup_wait_time():
    """Configure wait time and user classes based on test mode - Web UI optimized"""
    test_mode = os.environ.get('TEST_MODE', 'realistic')
    
    print(f"🎛️ Configuring test mode: {test_mode}")
    
    if test_mode == 'stress':
        # Force zero wait time for maximum concurrency in stress tests
        MVHSSearchUser.wait_time = between(0, 0)
        MVHSSearchUser.weight = 1
        # Disable MVHSRealisticUser in stress mode
        MVHSRealisticUser.weight = 0
        print("� STRESS TEST MODE ACTIVATED!")
        print("   ⚡ MVHSSearchUser: ACTIVE (zero wait time, maximum concurrency)")
        print("   👤 MVHSRealisticUser: DISABLED")
        print("   🎯 Best for: High-load testing, finding performance limits")
        print("   💡 Web UI Tip: Start with 10-20 users, increase gradually")
    else:
        # Disable MVHSSearchUser in realistic mode  
        MVHSSearchUser.weight = 0
        MVHSRealisticUser.weight = 1
        print("👤 REALISTIC MODE ACTIVATED!")
        print("   🔥 MVHSSearchUser: DISABLED") 
        print("   ⚡ MVHSRealisticUser: ACTIVE (human-like behavior)")
        print("   🎯 Best for: Normal usage simulation, functional testing")
        print("   💡 Web UI Tip: 5-50 users work well, 2-5 users/sec spawn rate")
    
    # Web UI specific recommendations
    print("\n🌐 WEB UI RECOMMENDATIONS:")
    print("   📊 Monitor the charts in real-time during tests")
    print("   🎯 Use the Dashboard (/test-dashboard) for quick configuration")
    print("   🔄 Change profiles on-the-fly via Profile Selector")
    print("   ⚙️ Adjust behavior settings without restarting Locust")
    print("   📈 Watch response times and success rates continuously")

def configure_realistic_user_class():
    """Configure the MVHSRealisticUser class with proper wait times - Web UI enhanced"""
    global MVHSRealisticUser
    
    # Get user behavior configuration
    config = load_stress_config()
    if not config or 'user_behavior' not in config:
        print("⚠️ No user behavior config found, using web-optimized defaults")
        MVHSRealisticUser.wait_time = between(1, 5)  # Faster defaults for web testing
        return
    
    behavior_type = os.environ.get('USER_BEHAVIOR', 'realistic')
    behavior = config['user_behavior'].get(behavior_type)
    
    if behavior:
        wait_min = behavior.get('wait_time_min', 2)
        wait_max = behavior.get('wait_time_max', 8)
        
        # Configure wait time at class level
        MVHSRealisticUser.wait_time = between(wait_min, wait_max)
        
        print(f"✅ MVHSRealisticUser configured: {behavior.get('name', 'Unknown')}")
        print(f"   ⏱️ Wait time: {wait_min}-{wait_max} seconds")
        print(f"   🎭 Behavior: {behavior.get('description', 'No description')}")
        
        # Web UI specific tips based on behavior
        if behavior_type == 'fast_user':
            print("   💡 Web UI Tip: Good for quick functional tests (20-100 users)")
        elif behavior_type == 'slow_user':
            print("   💡 Web UI Tip: Good for detailed analysis (5-20 users)")
        elif behavior_type == 'mobile_user':
            print("   💡 Web UI Tip: Simulates mobile users (10-30 users)")
        else:
            print("   💡 Web UI Tip: Balanced for most test scenarios (10-50 users)")
    else:
        print(f"⚠️ Unknown behavior type: {behavior_type}, using web-optimized defaults")
        MVHSRealisticUser.wait_time = between(1, 5)


# Event listeners for collecting metrics
search_metrics = []
request_metrics = []

@events.request.add_listener
def on_search_metrics(request_type, name, response_time, response_length, exception, **kwargs):
    """Collect search-specific metrics"""
    if 'search' in name.lower():
        search_metrics.append({
            'timestamp': datetime.now().isoformat(),
            'search_term': kwargs.get('search_term', 'unknown'),
            'result_count': kwargs.get('result_count', 0),
            'response_time_ms': response_time,
            'response_size_bytes': response_length
        })

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Collect all request metrics"""
    request_metrics.append({
        'timestamp': datetime.now().isoformat(),
        'request_type': request_type,
        'name': name,
        'response_time_ms': response_time,
        'response_size_bytes': response_length,
        'success': exception is None
    })

@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Generate comprehensive summary report when test stops - Web UI enhanced"""
    print("\n" + "="*70)
    print("🎯 MVHS.DE LOAD TEST SUMMARY - WEB UI ENHANCED")
    print("="*70)
    
    # Basic statistics
    total_requests = len(request_metrics)
    successful_requests = len([r for r in request_metrics if r['success']])
    failed_requests = total_requests - successful_requests
    
    # Test configuration summary
    test_mode = os.environ.get('TEST_MODE', 'realistic')
    user_behavior = os.environ.get('USER_BEHAVIOR', 'realistic')
    current_profile = os.environ.get('WEBSITE_PROFILE', 'mvhs_production')
    
    print(f"🎛️ Test Configuration:")
    print(f"   Mode: {test_mode.upper()}")
    print(f"   Behavior: {user_behavior}")
    print(f"   Profile: {current_profile}")
    print(f"   Duration: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if total_requests > 0:
        success_rate = (successful_requests / total_requests) * 100
        avg_response_time = sum(r['response_time_ms'] for r in request_metrics) / total_requests
        
        print(f"\n📊 Performance Statistics:")
        print(f"   Total Requests: {total_requests:,}")
        print(f"   Successful: {successful_requests:,} ({success_rate:.2f}%)")
        print(f"   Failed: {failed_requests:,}")
        print(f"   Average Response Time: {avg_response_time:.2f}ms")
        
        # Response time analysis
        response_times = [r['response_time_ms'] for r in request_metrics if r['success']]
        if response_times:
            response_times.sort()
            p50 = response_times[int(len(response_times) * 0.5)]
            p95 = response_times[int(len(response_times) * 0.95)]
            p99 = response_times[int(len(response_times) * 0.99)]
            
            print(f"   Response Time Percentiles:")
            print(f"     50th percentile: {p50:.2f}ms")
            print(f"     95th percentile: {p95:.2f}ms") 
            print(f"     99th percentile: {p99:.2f}ms")
        
        # Search-specific statistics
        if search_metrics:
            print(f"\n🔍 Search Performance:")
            print(f"   Search Operations: {len(search_metrics):,}")
            avg_search_time = sum(s['response_time_ms'] for s in search_metrics) / len(search_metrics)
            print(f"   Average Search Time: {avg_search_time:.2f}ms")
            
            # Most searched terms
            search_terms = [s['search_term'] for s in search_metrics if s['search_term'] != 'unknown']
            term_counts = {}
            for term in search_terms:
                term_counts[term] = term_counts.get(term, 0) + 1
            
            if term_counts:
                print(f"   Top Search Terms:")
                for term, count in sorted(term_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                    print(f"     '{term}': {count} searches")
        
        # Request type breakdown
        request_types = {}
        for r in request_metrics:
            req_type = r['name']
            if req_type not in request_types:
                request_types[req_type] = {'count': 0, 'avg_time': 0, 'total_time': 0}
            request_types[req_type]['count'] += 1
            request_types[req_type]['total_time'] += r['response_time_ms']
        
        for req_type in request_types:
            request_types[req_type]['avg_time'] = request_types[req_type]['total_time'] / request_types[req_type]['count']
        
        print(f"\n📈 Request Type Analysis:")
        for req_type, stats in sorted(request_types.items(), key=lambda x: x[1]['count'], reverse=True)[:10]:
            print(f"   {req_type}: {stats['count']} requests, {stats['avg_time']:.2f}ms avg")
    else:
        print("⚠️ No requests were made during this test")
    
    # Save detailed metrics to files with enhanced organization
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Create enhanced metrics directory structure
    metrics_dir = os.path.join('reports', 'metrics')
    os.makedirs(metrics_dir, exist_ok=True)
    
    # Create web-friendly summary
    web_summary = {
        "test_info": {
            "timestamp": timestamp,
            "mode": test_mode,
            "behavior": user_behavior,
            "profile": current_profile,
            "total_requests": total_requests,
            "success_rate": round(success_rate, 2) if total_requests > 0 else 0,
            "avg_response_time": round(avg_response_time, 2) if total_requests > 0 else 0
        },
        "search_stats": {
            "total_searches": len(search_metrics),
            "avg_search_time": round(sum(s['response_time_ms'] for s in search_metrics) / len(search_metrics), 2) if search_metrics else 0,
            "top_terms": dict(sorted(term_counts.items(), key=lambda x: x[1], reverse=True)[:10]) if 'term_counts' in locals() else {}
        }
    }
    
    # Save web summary
    web_summary_path = os.path.join(metrics_dir, f'web_summary_{timestamp}.json')
    with open(web_summary_path, 'w') as f:
        json.dump(web_summary, f, indent=2)
    
    # Save search metrics
    if search_metrics:
        search_json_path = os.path.join(metrics_dir, f'search_metrics_{timestamp}.json')
        search_csv_path = os.path.join(metrics_dir, f'search_metrics_{timestamp}.csv')
        
        with open(search_json_path, 'w') as f:
            json.dump(search_metrics, f, indent=2)
        
        with open(search_csv_path, 'w', newline='') as f:
            if search_metrics:
                writer = csv.DictWriter(f, fieldnames=search_metrics[0].keys())
                writer.writeheader()
                writer.writerows(search_metrics)
    
    # Save request metrics
    if request_metrics:
        request_json_path = os.path.join(metrics_dir, f'request_metrics_{timestamp}.json')
        request_csv_path = os.path.join(metrics_dir, f'request_metrics_{timestamp}.csv')
        
        with open(request_json_path, 'w') as f:
            json.dump(request_metrics, f, indent=2)
        
        with open(request_csv_path, 'w', newline='') as f:
            if request_metrics:
                writer = csv.DictWriter(f, fieldnames=request_metrics[0].keys())
                writer.writeheader()
                writer.writerows(request_metrics)
    
    print(f"\n💾 Detailed metrics saved to reports/metrics/:")
    print(f"   📊 web_summary_{timestamp}.json (Web UI optimized)")
    print(f"   🔍 search_metrics_{timestamp}.json/.csv")
    print(f"   📈 request_metrics_{timestamp}.json/.csv")
    print(f"\n🌐 Web UI Features:")
    print(f"   📍 Dashboard: http://localhost:8089/test-dashboard")
    print(f"   🔄 Profile Selector: http://localhost:8089/profile-selector")
    print(f"   ⚙️ Configuration: http://localhost:8089/test-config")
    print("="*70)


# ============================================================================
# WEB UI EXTENSIONS - Custom profile selector
# ============================================================================

# Store web UI instance globally
web_ui_instance = None

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Initialize web UI extensions when Locust starts"""
    global web_ui_instance
    
    # Only add web UI extensions if running in web mode
    if environment.web_ui:
        web_ui_instance = environment.web_ui
        print("🌐 MVHS Load Test - Web UI Mode Detected!")
        print("✨ Initializing enhanced web interface...")
        try:
            add_profile_routes(environment.web_ui)
            print("✅ Enhanced web UI features added successfully!")
            print("🎯 Dashboard: http://localhost:8089/test-dashboard")
            print("� Profile Selector: http://localhost:8089/profile-selector")
            print("⚙️ Configuration: http://localhost:8089/test-config")
            print("📊 API Stats: http://localhost:8089/api/stats")
            print("💡 Custom widgets will auto-inject into main UI")
            
            # Auto-inject widgets into the main UI
            try:
                inject_custom_widgets_into_main_ui(environment.web_ui)
                print("🎨 Custom widgets injection configured")
            except Exception as widget_error:
                print(f"⚠️ Widget injection setup failed: {widget_error}")
                
        except Exception as e:
            print(f"❌ Failed to add enhanced web UI features: {e}")
            print("   Standard Locust web UI will still work normally")
    else:
        print("ℹ️  Running in headless mode - no web UI detected")
        print("💡 To use enhanced web features, start with: locust --web-host=0.0.0.0")

def inject_custom_widgets_into_main_ui(web_ui):
    """Automatically inject custom widgets into the main Locust UI"""
    
    # Override the index template to include our custom widgets
    original_index = web_ui.app.view_functions.get('index')
    
    def enhanced_index():
        """Enhanced index page with custom widgets"""
        try:
            # Get the original response
            if original_index:
                response = original_index()
            else:
                response = "Locust UI"
            
            # If it's HTML, inject our widgets
            if isinstance(response, str) and '<html' in response.lower():
                # Inject widget script before closing body tag
                widget_script = """
                <script>
                // Auto-inject MVHS custom widgets
                document.addEventListener('DOMContentLoaded', function() {
                    fetch('/inject-profile-widget')
                        .then(response => response.text())
                        .then(script => {
                            const scriptElement = document.createElement('script');
                            scriptElement.innerHTML = script.replace('<script>', '').replace('</script>', '');
                            document.head.appendChild(scriptElement);
                        })
                        .catch(error => console.log('Widget injection failed:', error));
                });
                </script>
                """
                response = response.replace('</body>', widget_script + '</body>')
            
            return response
        except Exception as e:
            print(f"Enhanced index failed: {e}")
            # Fallback to original
            return original_index() if original_index else "Locust UI"
    
    # Replace the index view
    web_ui.app.view_functions['index'] = enhanced_index

def add_profile_routes(web_ui):
    """Add custom profile selector routes to the web UI"""
    
    # Get available profiles
    profiles_config = load_website_profiles()
    if not profiles_config:
        return
    
    # Add custom CSS to improve the main UI
    @web_ui.app.route("/custom-styles.css")
    def custom_styles():
        """Custom CSS for enhanced web UI"""
        from flask import Response
        css = """
        /* Enhanced Web UI Styles */
        .profile-widget {
            position: fixed;
            top: 70px;
            right: 15px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            border-radius: 10px;
            z-index: 1000;
            box-shadow: 0 6px 20px rgba(0,0,0,0.2);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 13px;
            max-width: 300px;
            border: 2px solid rgba(255,255,255,0.3);
            backdrop-filter: blur(10px);
        }
        
        .test-controls {
            position: fixed;
            top: 140px;
            right: 15px;
            background: rgba(255,255,255,0.95);
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 999;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            font-size: 12px;
            border: 1px solid #e0e0e0;
        }
        
        .quick-action-btn {
            background: #28a745;
            color: white;
            border: none;
            padding: 8px 12px;
            border-radius: 4px;
            cursor: pointer;
            margin: 2px;
            font-size: 11px;
            transition: all 0.2s;
        }
        
        .quick-action-btn:hover {
            background: #218838;
            transform: translateY(-1px);
        }
        
        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 6px;
        }
        
        .status-active { background: #28a745; }
        .status-inactive { background: #dc3545; }
        .status-warning { background: #ffc107; }
        
        /* Enhance main charts area */
        .charts-container {
            margin-top: 20px;
        }
        
        /* Better mobile responsiveness */
        @media (max-width: 768px) {
            .profile-widget, .test-controls {
                position: relative;
                right: auto;
                top: auto;
                width: 100%;
                margin: 10px 0;
            }
        }
        """
        return Response(css, mimetype='text/css')
    
    # Enhanced test route with real-time stats
    @web_ui.app.route("/test-dashboard")
    def test_dashboard():
        """Enhanced test dashboard with real-time information"""
        current_profile_name = os.environ.get('WEBSITE_PROFILE', 'mvhs_production')
        current_profile = profiles_config['profiles'].get(current_profile_name)
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>MVHS Load Test - Enhanced Dashboard</title>
            <link rel="stylesheet" href="/custom-styles.css">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background: #f8f9fa;">
            <div style="max-width: 1200px; margin: 0 auto;">
                <h1 style="color: #2c5aa0; margin-bottom: 30px;">🚀 MVHS Load Test Dashboard</h1>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 20px; margin-bottom: 30px;">
                    <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h3 style="margin-top: 0; color: #2c5aa0;">🎯 Active Profile</h3>
                        <p><strong>{current_profile['name'] if current_profile else 'Unknown'}</strong></p>
                        <p style="font-size: 12px; color: #666;">{current_profile['base_url'] if current_profile else 'Unknown'}</p>
                        <button onclick="window.open('/profile-selector', '_blank')" class="quick-action-btn">Change Profile</button>
                    </div>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h3 style="margin-top: 0; color: #2c5aa0;">⚡ Quick Actions</h3>
                        <button onclick="startQuickTest()" class="quick-action-btn">Quick Test (1min)</button><br>
                        <button onclick="startRealisticTest()" class="quick-action-btn">Realistic Test</button><br>
                        <button onclick="showTestConfig()" class="quick-action-btn">Test Config</button>
                    </div>
                    
                    <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <h3 style="margin-top: 0; color: #2c5aa0;">📊 Test Status</h3>
                        <p><span class="status-indicator status-active"></span>Web UI Active</p>
                        <p><span class="status-indicator status-warning"></span>Ready to Test</p>
                        <button onclick="window.open('/', '_blank')" class="quick-action-btn">Main Locust UI</button>
                    </div>
                </div>
                
                <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px;">
                    <h3 style="color: #2c5aa0;">🔧 Test Configuration Helper</h3>
                    <div id="config-helper">
                        <p>Select your test scenario:</p>
                        <button onclick="configureTest('realistic')" class="quick-action-btn">👤 Realistic Users (2-8s wait)</button>
                        <button onclick="configureTest('fast')" class="quick-action-btn">⚡ Fast Users (0.5-2s wait)</button>
                        <button onclick="configureTest('stress')" class="quick-action-btn">🔥 Stress Test (no wait)</button>
                        <button onclick="configureTest('mobile')" class="quick-action-btn">📱 Mobile Users (slower)</button>
                    </div>
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="/" style="color: #2c5aa0; text-decoration: none; font-weight: bold;">← Back to Main Locust Dashboard</a>
                </div>
            </div>
            
            <script>
                function startQuickTest() {{
                    alert('Quick test configuration ready! Go to main UI and start with:\\n\\n- Users: 5\\n- Spawn rate: 1/sec\\n- Duration: 1 minute');
                    window.open('/', '_blank');
                }}
                
                function startRealisticTest() {{
                    alert('Realistic test configuration ready! Go to main UI and start with:\\n\\n- Users: 10-20\\n- Spawn rate: 2/sec\\n- Duration: 5-10 minutes');
                    window.open('/', '_blank');
                }}
                
                function showTestConfig() {{
                    window.open('/test-config', '_blank');
                }}
                
                function configureTest(type) {{
                    fetch('/configure-behavior', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{'behavior': type}})
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        if (data.success) {{
                            alert('✅ Test behavior configured: ' + data.behavior_name + '\\n\\nWait time: ' + data.wait_time + '\\n\\nYou can now start your test in the main UI.');
                        }} else {{
                            alert('❌ Configuration failed: ' + data.error);
                        }}
                    }});
                }}
            </script>
        </body>
        </html>
        """
    
    # Create a custom route for the profile selector
    @web_ui.app.route("/profile-selector")
    def profile_selector():
        """Profile selector page"""
        current_profile_name = os.environ.get('WEBSITE_PROFILE', 'mvhs_production')
        current_profile = profiles_config['profiles'].get(current_profile_name)
        
        profile_options = ""
        for name, profile in profiles_config['profiles'].items():
            selected = "selected" if name == current_profile_name else ""
            profile_options += f'<option value="{name}" {selected}>{profile["name"]} ({profile["base_url"]})</option>'
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>MVHS Load Test - Profile Selector</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .header {{ background: #2c5aa0; color: white; padding: 15px; margin: -20px -20px 20px -20px; border-radius: 8px 8px 0 0; }}
                .current-profile {{ background: #e8f4f8; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 4px solid #2c5aa0; }}
                .form-group {{ margin-bottom: 15px; }}
                label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
                select, button {{ padding: 10px; font-size: 14px; border: 1px solid #ddd; border-radius: 4px; }}
                select {{ width: 100%; }}
                button {{ background: #2c5aa0; color: white; cursor: pointer; border: none; }}
                button:hover {{ background: #1e3d6f; }}
                .profile-info {{ background: #f8f9fa; padding: 10px; border-radius: 4px; margin-top: 10px; }}
                .back-link {{ margin-top: 20px; }}
                .back-link a {{ color: #2c5aa0; text-decoration: none; }}
                .back-link a:hover {{ text-decoration: underline; }}
                .alert {{ padding: 10px; margin: 10px 0; border-radius: 4px; }}
                .alert-success {{ background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }}
                .alert-danger {{ background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }}
            </style>
            <script>
                function updateProfileInfo() {{
                    const select = document.getElementById('profile-select');
                    const selectedProfile = select.value;
                    const profiles = {json.dumps(profiles_config['profiles'])};
                    const profile = profiles[selectedProfile];
                    
                    if (profile) {{
                        document.getElementById('profile-info').innerHTML = 
                            '<strong>Target URL:</strong> ' + profile.base_url + '<br>' +
                            '<strong>Description:</strong> ' + profile.description + '<br>' +
                            '<strong>Categories:</strong> ' + profile.categories.length + ' defined<br>' +
                            '<strong>Search Terms:</strong> ' + profile.search_terms.length + ' defined';
                    }}
                }}
                
                function changeProfile() {{
                    const select = document.getElementById('profile-select');
                    const selectedProfile = select.value;
                    
                    fetch('/change-profile', {{
                        method: 'POST',
                        headers: {{'Content-Type': 'application/json'}},
                        body: JSON.stringify({{'profile': selectedProfile}})
                    }})
                    .then(response => response.json())
                    .then(data => {{
                        if (data.success) {{
                            document.getElementById('alert-container').innerHTML = 
                                '<div class="alert alert-success">✅ Profile changed to: ' + data.profile_name + 
                                '<br>🎯 Target URL: ' + data.target_url + 
                                '<br><br>💡 Note: You may need to restart the test for all changes to take effect.</div>';
                            setTimeout(() => location.reload(), 2000);
                        }} else {{
                            document.getElementById('alert-container').innerHTML = 
                                '<div class="alert alert-danger">❌ Failed to change profile: ' + data.error + '</div>';
                        }}
                    }})
                    .catch(error => {{
                        document.getElementById('alert-container').innerHTML = 
                            '<div class="alert alert-danger">❌ Error changing profile: ' + error + '</div>';
                    }});
                }}
            </script>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🎯 MVHS Load Test - Website Profile Selector</h1>
                </div>
                
                <div id="alert-container"></div>
                
                <div class="current-profile">
                    <h3>📍 Current Active Profile</h3>
                    <strong>{current_profile['name'] if current_profile else 'Unknown'}</strong><br>
                    <strong>Target:</strong> {current_profile['base_url'] if current_profile else 'Unknown'}<br>
                    <strong>Description:</strong> {current_profile['description'] if current_profile else 'Unknown'}
                </div>
                
                <div class="form-group">
                    <label for="profile-select">🌐 Select Website Profile:</label>
                    <select id="profile-select" onchange="updateProfileInfo()">
                        {profile_options}
                    </select>
                </div>
                
                <div class="profile-info" id="profile-info">
                    {f'<strong>Target URL:</strong> {current_profile["base_url"]}<br><strong>Description:</strong> {current_profile["description"]}<br><strong>Categories:</strong> {len(current_profile["categories"])} defined<br><strong>Search Terms:</strong> {len(current_profile["search_terms"])} defined' if current_profile else 'No profile information available'}
                </div>
                
                <div class="form-group">
                    <button onclick="changeProfile()">🔄 Change Profile</button>
                </div>
                
                <div class="back-link">
                    <a href="/">← Back to Load Test Dashboard</a>
                </div>
            </div>
        </body>
        </html>
        """
        return html
    
    # Add route to handle profile changes
    @web_ui.app.route("/change-profile", methods=["POST"])
    def change_profile():
        """Handle profile change requests"""
        try:
            from flask import request
            data = request.get_json()
            profile_name = data.get('profile')
            
            if set_profile_for_web_ui(profile_name):
                profile = get_profile_for_web_ui()
                return {
                    "success": True,
                    "profile_name": profile['name'],
                    "target_url": profile['base_url'],
                    "message": f"Profile changed to {profile_name}"
                }
            else:
                return {"success": False, "error": f"Profile '{profile_name}' not found"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Add real-time stats API
    @web_ui.app.route("/api/stats")
    def api_stats():
        """API endpoint for real-time statistics"""
        try:
            from flask import jsonify
            stats = {
                "current_profile": os.environ.get('WEBSITE_PROFILE', 'mvhs_production'),
                "test_mode": os.environ.get('TEST_MODE', 'realistic'),
                "user_behavior": os.environ.get('USER_BEHAVIOR', 'realistic'),
                "total_requests": len(request_metrics),
                "search_requests": len(search_metrics),
                "timestamp": datetime.now().isoformat()
            }
            
            if request_metrics:
                recent_requests = request_metrics[-10:]  # Last 10 requests
                avg_response_time = sum(r['response_time_ms'] for r in recent_requests) / len(recent_requests)
                success_rate = len([r for r in recent_requests if r['success']]) / len(recent_requests) * 100
                stats.update({
                    "avg_response_time": round(avg_response_time, 2),
                    "success_rate": round(success_rate, 2)
                })
            
            return jsonify(stats)
        except Exception as e:
            return {"error": str(e)}
    
    # Add test configuration viewer
    @web_ui.app.route("/test-config")
    def test_config():
        """Display current test configuration"""
        config = load_stress_config()
        current_profile = get_profile_for_web_ui()
        current_behavior = os.environ.get('USER_BEHAVIOR', 'realistic')
        current_mode = os.environ.get('TEST_MODE', 'realistic')
        
        behavior_info = "Default settings"
        if config and 'user_behavior' in config:
            behavior_config = config['user_behavior'].get(current_behavior, {})
            behavior_info = f"{behavior_config.get('name', 'Unknown')} - Wait: {behavior_config.get('wait_time_min', 0)}-{behavior_config.get('wait_time_max', 0)}s"
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test Configuration - MVHS Load Test</title>
            <link rel="stylesheet" href="/custom-styles.css">
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 20px; background: #f8f9fa;">
            <div style="max-width: 800px; margin: 0 auto;">
                <h1 style="color: #2c5aa0;">⚙️ Current Test Configuration</h1>
                
                <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px;">
                    <h3>🎯 Target Website</h3>
                    <p><strong>Profile:</strong> {current_profile['name'] if current_profile else 'None'}</p>
                    <p><strong>URL:</strong> {current_profile['base_url'] if current_profile else 'None'}</p>
                    <p><strong>Categories:</strong> {len(current_profile['categories']) if current_profile else 0} available</p>
                    <p><strong>Search Terms:</strong> {len(current_profile['search_terms']) if current_profile else 0} available</p>
                </div>
                
                <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px;">
                    <h3>👤 User Behavior</h3>
                    <p><strong>Mode:</strong> {current_mode.title()}</p>
                    <p><strong>Behavior:</strong> {current_behavior}</p>
                    <p><strong>Details:</strong> {behavior_info}</p>
                </div>
                
                <div style="background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px;">
                    <h3>📊 Recommended Settings</h3>
                    <div style="margin: 10px 0;">
                        <strong>Light Testing:</strong> 5-10 users, 1 user/sec spawn rate, 2-5 minutes<br>
                        <em>Good for: Basic functionality testing, initial performance checks</em>
                    </div>
                    <div style="margin: 10px 0;">
                        <strong>Realistic Load:</strong> 20-50 users, 2 users/sec spawn rate, 10-30 minutes<br>
                        <em>Good for: Normal traffic simulation, performance monitoring</em>
                    </div>
                    <div style="margin: 10px 0;">
                        <strong>Stress Testing:</strong> 100+ users, 5+ users/sec spawn rate, 5-15 minutes<br>
                        <em>Good for: Finding performance limits, capacity planning</em>
                    </div>
                </div>
                
                <div style="text-align: center;">
                    <button onclick="window.open('/', '_blank')" class="quick-action-btn" style="font-size: 14px; padding: 10px 20px;">Start Testing in Main UI</button>
                </div>
                
                <div style="text-align: center; margin-top: 20px;">
                    <a href="/test-dashboard" style="color: #2c5aa0;">← Back to Dashboard</a> | 
                    <a href="/" style="color: #2c5aa0;">Main Locust UI</a>
                </div>
            </div>
        </body>
        </html>
        """
    
    # Add route for profile widget that can be embedded
    @web_ui.app.route("/profile-widget")
    def profile_widget():
        """Return an enhanced profile widget for the main UI"""
        current_profile_name = os.environ.get('WEBSITE_PROFILE', 'mvhs_production')
        profiles_config = load_website_profiles()
        current_profile = profiles_config['profiles'].get(current_profile_name) if profiles_config else None
        current_mode = os.environ.get('TEST_MODE', 'realistic')
        
        if not current_profile:
            return ""
        
        # Determine status color based on mode
        status_color = "#28a745" if current_mode == "realistic" else "#dc3545"
        mode_emoji = "👤" if current_mode == "realistic" else "🔥"
        
        return f"""
        <div id="profile-widget" class="profile-widget">
            <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px;">
                <div style="font-weight: bold; display: flex; align-items: center;">
                    🎯 <span style="margin-left: 6px;">Active Profile</span>
                </div>
                <div style="background: {status_color}; padding: 2px 6px; border-radius: 10px; font-size: 10px;">
                    {mode_emoji} {current_mode.upper()}
                </div>
            </div>
            <div style="font-weight: 600; margin-bottom: 4px;">{current_profile['name']}</div>
            <div style="font-size: 11px; opacity: 0.9; margin-bottom: 8px;">
                📍 {current_profile['base_url']}
            </div>
            <div style="font-size: 10px; opacity: 0.8; margin-bottom: 8px;">
                📂 {len(current_profile.get('categories', []))} categories • 🔍 {len(current_profile.get('search_terms', []))} search terms
            </div>
            <div style="display: flex; gap: 5px;">
                <a href="/profile-selector" style="
                    color: white; 
                    text-decoration: none; 
                    background: rgba(255,255,255,0.2); 
                    padding: 6px 10px; 
                    border-radius: 4px; 
                    font-size: 10px;
                    font-weight: 500;
                    border: 1px solid rgba(255,255,255,0.3);
                    flex: 1;
                    text-align: center;
                " target="_blank">
                    🔄 Profile
                </a>
                <a href="/test-dashboard" style="
                    color: white; 
                    text-decoration: none; 
                    background: rgba(255,255,255,0.2); 
                    padding: 6px 10px; 
                    border-radius: 4px; 
                    font-size: 10px;
                    font-weight: 500;
                    border: 1px solid rgba(255,255,255,0.3);
                    flex: 1;
                    text-align: center;
                " target="_blank">
                    ⚙️ Config
                </a>
            </div>
        </div>
        """
    
    # Add route to inject the widget into the main page
    @web_ui.app.route("/inject-profile-widget")
    def inject_profile_widget():
        """Return JavaScript to inject enhanced widgets into the main page"""
        return f"""
        <script>
        (function() {{
            // Check if widget already exists
            if (document.getElementById('profile-widget-container')) {{
                return;
            }}
            
            // Inject custom CSS
            if (!document.getElementById('custom-css')) {{
                var link = document.createElement('link');
                link.id = 'custom-css';
                link.rel = 'stylesheet';
                link.href = '/custom-styles.css';
                document.head.appendChild(link);
            }}
            
            // Create container for the widget
            var container = document.createElement('div');
            container.id = 'profile-widget-container';
            document.body.appendChild(container);
            
            // Fetch and inject the profile widget
            fetch('/profile-widget')
                .then(response => response.text())
                .then(html => {{
                    container.innerHTML = html;
                }})
                .catch(error => console.log('Profile widget load failed:', error));
            
            // Add enhanced controls widget
            var controlsContainer = document.createElement('div');
            controlsContainer.id = 'test-controls-container';
            controlsContainer.innerHTML = `
                <div class="test-controls">
                    <div style="font-weight: bold; margin-bottom: 8px; color: #2c5aa0;">⚡ Quick Actions</div>
                    <button onclick="openTestDashboard()" class="quick-action-btn">🎯 Dashboard</button>
                    <button onclick="showQuickStart()" class="quick-action-btn">🚀 Quick Start</button>
                    <button onclick="openConfig()" class="quick-action-btn">⚙️ Config</button>
                    <div style="margin-top: 8px; font-size: 10px; color: #666;">
                        <div id="stats-display">Loading stats...</div>
                    </div>
                </div>
            `;
            document.body.appendChild(controlsContainer);
            
            // Add global functions for quick actions
            window.openTestDashboard = function() {{
                window.open('/test-dashboard', '_blank');
            }};
            
            window.showQuickStart = function() {{
                alert('🚀 Quick Start Guide:\\n\\n1. Set number of users (start with 5-10)\\n2. Set spawn rate (1-2 users/sec)\\n3. Click Start Test\\n4. Monitor the charts below\\n\\n💡 Tip: Use the Dashboard for advanced configuration!');
            }};
            
            window.openConfig = function() {{
                window.open('/test-config', '_blank');
            }};
            
            // Update stats every 5 seconds
            function updateStats() {{
                fetch('/api/stats')
                    .then(response => response.json())
                    .then(data => {{
                        const statsDiv = document.getElementById('stats-display');
                        if (statsDiv && !data.error) {{
                            statsDiv.innerHTML = `
                                📊 Requests: ${{data.total_requests || 0}}<br>
                                🔍 Searches: ${{data.search_requests || 0}}<br>
                                ⏱️ Avg: ${{data.avg_response_time || 0}}ms<br>
                                ✅ Success: ${{data.success_rate || 0}}%
                            `;
                        }}
                    }})
                    .catch(error => console.log('Stats update failed:', error));
            }}
            
            // Start stats updates
            updateStats();
            setInterval(updateStats, 5000);
            
        }})();
        </script>
        """
    

class MVHSRealisticUser(HttpUser):
    """
    Realistic user behavior simulation with proper wait times
    Perfect for web UI testing with human-like interaction patterns
    """
    
    # Default weight - will be set to 0 in stress mode
    weight = 1
    
    # Default wait time - will be updated based on configuration
    wait_time = between(2, 8)
    
    # Class-level flag to prevent repeated initialization messages
    _wait_time_configured = False
    _initialization_shown = False
    
    def __init__(self, environment):
        super().__init__(environment)
        self.stress_config = get_current_stress_config()
        self.profile = get_profile_for_web_ui()
        
        # Load user behavior configuration
        self.user_behavior = self._get_user_behavior_config()
        
        # Configure wait times at class level
        self._configure_wait_times()
        
        # Configure session settings
        self._configure_http_session()
        
        # Initialize user session data
        self.search_terms = self.profile.get('search_terms', []) if self.profile else []
        self.categories = self.profile.get('categories', []) if self.profile else []
        self.endpoints = self.profile.get('endpoints', {}) if self.profile else {}
        
        # Add fallback values if profile data is missing
        if not self.search_terms:
            self.search_terms = [
                "schule", "unterricht", "lehrer", "student", "abitur", "klausur",
                "ferien", "termine", "anmeldung", "kontakt", "impressum", "news"
            ]
            print("⚠️ No search terms from profile, using defaults")
        
        if not self.categories:
            # Create minimal default categories for testing
            self.categories = [
                {
                    "name": "Kurse",
                    "url": "/kurse/",
                    "subcategories": ["allgemein", "sprachen", "it"]
                },
                {
                    "name": "Weiterbildung", 
                    "url": "/weiterbildung/",
                    "subcategories": ["beruf", "persoenlich"]
                }
            ]
            print("⚠️ No categories from profile, using defaults")
        
        if not self.endpoints:
            self.endpoints = {
                'search': '/suche',
                'course_detail': '/kurse/',
                'categories': '/kurse/',
                'instructor_search': '/dozent/'
            }
            print("⚠️ No endpoints from profile, using defaults")
        
        self.session_search_count = 0
        self.current_page_type = None
        
        # Print initialization summary only once
        if not MVHSRealisticUser._initialization_shown:
            print(f"👤 MVHSRealisticUser initialized:")
            print(f"   📝 Search terms: {len(self.search_terms)} available")
            print(f"   📂 Categories: {len(self.categories)} available") 
            print(f"   🔗 Endpoints: {len(self.endpoints)} configured")
            print(f"   🎯 Profile: {self.profile.get('name', 'None') if self.profile else 'None'}")
            
            # Print user behavior info
            if self.user_behavior:
                behavior_name = self.user_behavior.get('name', 'Unknown')
                wait_min = self.user_behavior.get('wait_time_min', 0)
                wait_max = self.user_behavior.get('wait_time_max', 0)
                print(f"👤 Realistic User initialized: {behavior_name} (wait: {wait_min}-{wait_max}s)")
            
            MVHSRealisticUser._initialization_shown = True
    
    def _get_user_behavior_config(self):
        """Get user behavior configuration"""
        config = load_stress_config()
        if not config or 'user_behavior' not in config:
            return None
        
        # Get behavior type from environment or default to realistic
        behavior_type = os.environ.get('USER_BEHAVIOR', 'realistic')
        return config['user_behavior'].get(behavior_type, config['user_behavior']['realistic'])
    
    def _configure_wait_times(self):
        """Configure wait times based on user behavior"""
        # Only configure and print once at class level
        if not MVHSRealisticUser._wait_time_configured:
            if self.user_behavior:
                wait_min = self.user_behavior.get('wait_time_min', 2)
                wait_max = self.user_behavior.get('wait_time_max', 8)
                # Set at class level to affect all instances
                MVHSRealisticUser.wait_time = between(wait_min, wait_max)
                print(f"⏱️ Wait time configured: {wait_min}-{wait_max} seconds between requests")
            else:
                # Default realistic wait times
                MVHSRealisticUser.wait_time = between(2, 8)
                print("⏱️ Default wait time: 2-8 seconds between requests")
            
            MVHSRealisticUser._wait_time_configured = True
    
    def _configure_http_session(self):
        """Configure HTTP session with reasonable settings"""
        if self.profile and 'request_settings' in self.profile:
            settings = self.profile['request_settings']
            
            # Configure retries and timeouts for realistic usage
            adapter = HTTPAdapter(
                pool_connections=10,
                pool_maxsize=20,
                max_retries=Retry(
                    total=settings.get('retry_count', 2),
                    backoff_factor=0.5,
                    status_forcelist=[500, 502, 503, 504]
                )
            )
            
            self.client.mount('http://', adapter)
            self.client.mount('https://', adapter)
            
            # Set headers
            if 'headers' in settings:
                self.client.headers.update(settings['headers'])
    
    def _reading_pause(self):
        """Simulate time spent reading page content"""
        if self.user_behavior:
            reading_min = self.user_behavior.get('reading_time_min', 5)
            reading_max = self.user_behavior.get('reading_time_max', 15)
            pause_time = random.uniform(reading_min, reading_max)
            time.sleep(pause_time)
    
    def _navigation_pause(self):
        """Simulate brief pause during navigation"""
        if self.user_behavior:
            nav_min = self.user_behavior.get('navigation_pause_min', 1)
            nav_max = self.user_behavior.get('navigation_pause_max', 3)
            pause_time = random.uniform(nav_min, nav_max)
            time.sleep(pause_time)
    
    @task(40)
    def browse_homepage(self):
        """Browse homepage and main navigation - Weight: 40"""
        print("🏠 Browsing homepage")
        with self.client.get("/", catch_response=True, name="Homepage") as response:
            if response.status_code == 200:
                self.current_page_type = "homepage"
                response.success()
                print(f"   ✅ Homepage successful: {response.status_code}")
                # Simulate reading homepage content
                self._reading_pause()
            else:
                response.failure(f"Homepage failed with status {response.status_code}")
                print(f"   ❌ Homepage failed: {response.status_code}")
    
    @task(35)
    def search_courses(self):
        """Perform realistic course searches - Weight: 35"""
        if not self.search_terms:
            print("❌ Search skipped: No search terms available!")
            return
        
        search_term = random.choice(self.search_terms)
        search_endpoint = self.endpoints.get('search', '/suche')
        cache_buster = random.randint(100000, 999999)
        
        print(f"🔍 Searching for: '{search_term}' at endpoint: {search_endpoint}")
        
        # Add realistic search delay
        if self.stress_config and 'search_intensity' in self.stress_config:
            intensity = self.stress_config['search_intensity']
            delay_min = intensity.get('search_delay_min', 1)
            delay_max = intensity.get('search_delay_max', 3)
            search_delay = random.uniform(delay_min, delay_max)
            time.sleep(search_delay)
        
        # Handle different search endpoint formats with cache buster
        if '?' in search_endpoint:
            search_url = f"{search_endpoint}&q={search_term}_cb={cache_buster}"
        else:
            search_url = f"{search_endpoint}?q={search_term}_cb={cache_buster}"
        
        with self.client.get(search_url, catch_response=True, name=f"Search: {search_term}") as response:
            if response.status_code == 200:
                self.current_page_type = "search_results"
                self.session_search_count += 1
                response.success()
                print(f"   ✅ Search successful: {response.status_code}")
                # Simulate reading search results
                self._reading_pause()
            else:
                response.failure(f"Search failed with status {response.status_code}")
                print(f"   ❌ Search failed: {response.status_code}")
    
    @task(20)
    def browse_categories(self):
        """Browse course categories realistically - Weight: 20"""
        if not self.categories:
            print("❌ Category browsing skipped: No categories available!")
            return
        
        category = random.choice(self.categories)
        category_url = category.get('url', '/kurse/')
        category_name = category.get('name', 'Unknown')
        
        print(f"📂 Browsing category: '{category_name}' at {category_url}")
        
        # Navigation pause before clicking category
        self._navigation_pause()
        
        with self.client.get(category_url, catch_response=True, name=f"Category: {category_name}") as response:
            if response.status_code == 200:
                self.current_page_type = "category"
                response.success()
                print(f"   ✅ Category browse successful: {response.status_code}")
                # Simulate browsing category content
                self._reading_pause()
            else:
                response.failure(f"Category failed with status {response.status_code}")
                print(f"   ❌ Category browse failed: {response.status_code}")
    
    @task(15)
    def browse_subcategories(self):
        """Browse subcategories with realistic behavior - Weight: 15"""
        if not self.categories:
            print("❌ Subcategory browsing skipped: No categories available!")
            return
        
        category = random.choice(self.categories)
        subcategories = category.get('subcategories', [])
        
        if subcategories:
            subcategory_id = random.choice(subcategories)
            subcategory_url = f"/kurse/{subcategory_id}"
            
            print(f"📁 Browsing subcategory: '{subcategory_id}' at {subcategory_url}")
            
            # Navigation pause
            self._navigation_pause()
            
            with self.client.get(subcategory_url, catch_response=True, name=f"Subcategory: {subcategory_id}") as response:
                if response.status_code == 200:
                    self.current_page_type = "subcategory"
                    response.success()
                    print(f"   ✅ Subcategory browse successful: {response.status_code}")
                    # Simulate browsing subcategory
                    self._reading_pause()
                else:
                    response.failure(f"Subcategory failed with status {response.status_code}")
                    print(f"   ❌ Subcategory browse failed: {response.status_code}")
        else:
            print(f"⚠️ No subcategories found in category: {category.get('name', 'Unknown')}")
    
    @task(10)
    def view_course_details(self):
        """View course details with realistic reading time - Weight: 10"""
        # This would typically follow from search results or category browsing
        # Simulate clicking on a course from current page
        if self.current_page_type in ["search_results", "category", "subcategory"]:
            # Navigation pause before viewing details
            self._navigation_pause()
            
            # Simulate course detail URL (this would be dynamic in real implementation)
            course_url = "/kurse/sample-course-12345"
            
            with self.client.get(course_url, catch_response=True, name="Course Details") as response:
                if response.status_code in [200, 404]:  # 404 is expected for sample URL
                    self.current_page_type = "course_detail"
                    response.success()
                    # Simulate reading course details carefully
                    if self.user_behavior:
                        reading_min = self.user_behavior.get('reading_time_min', 5) * 1.5  # Longer for course details
                        reading_max = self.user_behavior.get('reading_time_max', 15) * 1.5
                        reading_time = random.uniform(reading_min, reading_max)
                        time.sleep(reading_time)
                else:
                    response.failure(f"Course details failed with status {response.status_code}")
                    print(f"   ❌ Course details failed: {response.status_code}")


# ============================================================================
# INITIALIZATION - Setup user classes after they are all defined
# ============================================================================

# Setup wait time based on configuration
setup_wait_time()

# Configure realistic user class after it's been defined
configure_realistic_user_class()
