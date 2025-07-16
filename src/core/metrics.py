"""
Core metrics collection and event handling.

This module provides functionality for collecting detailed performance
metrics during load tests and handling Locust events.
"""

import json
import csv
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from locust import events


class MetricsCollector:
    """Collects and manages performance metrics during load tests."""
    
    def __init__(self, output_dir: str = "reports/metrics"):
        """
        Initialize the metrics collector.
        
        Args:
            output_dir: Directory to store metrics files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.search_metrics = []
        self.request_metrics = []
        self.user_metrics = []
        self.error_metrics = []
        
        self.start_time = None
        self.test_name = None
        
        # Register event handlers
        self._register_events()
    
    def _register_events(self):
        """Register Locust event handlers for metrics collection."""
        events.test_start.add_listener(self._on_test_start)
        events.test_stop.add_listener(self._on_test_stop)
        events.request.add_listener(self._on_request)
        events.user_error.add_listener(self._on_user_error)
    
    def _on_test_start(self, environment, **kwargs):
        """Handle test start event."""
        self.start_time = datetime.now()
        self.test_name = environment.parsed_options.test_name if hasattr(environment.parsed_options, 'test_name') else "unknown"
        print(f"📊 Metrics collection started for test: {self.test_name}")
    
    def _on_test_stop(self, environment, **kwargs):
        """Handle test stop event and save metrics."""
        if self.start_time:
            end_time = datetime.now()
            duration = (end_time - self.start_time).total_seconds()
            print(f"📊 Test completed in {duration:.1f} seconds. Saving metrics...")
            self.save_all_metrics()
    
    def _on_request(self, request_type, name, response_time, response_length, exception, context, **kwargs):
        """Handle request event and collect metrics."""
        timestamp = time.time()
        
        # Collect general request metrics
        self.request_metrics.append({
            'timestamp': timestamp,
            'request_type': request_type,
            'name': name,
            'response_time': response_time,
            'response_length': response_length,
            'success': exception is None,
            'exception': str(exception) if exception else None
        })
        
        # Collect search-specific metrics
        if 'search' in name.lower() or '/suche' in name:
            self.search_metrics.append({
                'timestamp': timestamp,
                'search_term': context.get('search_term', '') if context else '',
                'response_time': response_time,
                'results_found': context.get('results_count', 0) if context else 0,
                'success': exception is None
            })
    
    def _on_user_error(self, user_instance, exception, tb, **kwargs):
        """Handle user error event."""
        self.error_metrics.append({
            'timestamp': time.time(),
            'user_class': user_instance.__class__.__name__,
            'exception_type': exception.__class__.__name__,
            'exception_message': str(exception),
            'traceback': str(tb)
        })
    
    def add_search_metric(self, search_term: str, response_time: float, results_count: int, success: bool):
        """
        Manually add a search metric.
        
        Args:
            search_term: The search term used
            response_time: Response time in milliseconds
            results_count: Number of search results found
            success: Whether the search was successful
        """
        self.search_metrics.append({
            'timestamp': time.time(),
            'search_term': search_term,
            'response_time': response_time,
            'results_found': results_count,
            'success': success
        })
    
    def add_user_metric(self, user_id: str, action: str, duration: float, success: bool):
        """
        Add a user behavior metric.
        
        Args:
            user_id: Unique identifier for the user
            action: The action performed
            duration: Duration of the action
            success: Whether the action was successful
        """
        self.user_metrics.append({
            'timestamp': time.time(),
            'user_id': user_id,
            'action': action,
            'duration': duration,
            'success': success
        })
    
    def save_all_metrics(self):
        """Save all collected metrics to files."""
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
        test_prefix = f"{self.test_name}_{timestamp_str}" if self.test_name else f"test_{timestamp_str}"
        
        # Save search metrics
        if self.search_metrics:
            self._save_search_metrics(f"{test_prefix}_search_metrics")
        
        # Save request metrics
        if self.request_metrics:
            self._save_request_metrics(f"{test_prefix}_request_metrics")
        
        # Save user metrics
        if self.user_metrics:
            self._save_user_metrics(f"{test_prefix}_user_metrics")
        
        # Save error metrics
        if self.error_metrics:
            self._save_error_metrics(f"{test_prefix}_error_metrics")
    
    def _save_search_metrics(self, filename_prefix: str):
        """Save search metrics to JSON and CSV files."""
        # JSON format
        json_file = self.output_dir / f"{filename_prefix}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.search_metrics, f, indent=2, ensure_ascii=False)
        
        # CSV format
        if self.search_metrics:
            csv_file = self.output_dir / f"{filename_prefix}.csv"
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.search_metrics[0].keys())
                writer.writeheader()
                writer.writerows(self.search_metrics)
        
        print(f"💾 Search metrics saved: {json_file}")
    
    def _save_request_metrics(self, filename_prefix: str):
        """Save request metrics to JSON and CSV files."""
        # JSON format
        json_file = self.output_dir / f"{filename_prefix}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.request_metrics, f, indent=2, ensure_ascii=False)
        
        # CSV format
        if self.request_metrics:
            csv_file = self.output_dir / f"{filename_prefix}.csv"
            with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=self.request_metrics[0].keys())
                writer.writeheader()
                writer.writerows(self.request_metrics)
        
        print(f"💾 Request metrics saved: {json_file}")
    
    def _save_user_metrics(self, filename_prefix: str):
        """Save user behavior metrics to JSON file."""
        json_file = self.output_dir / f"{filename_prefix}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.user_metrics, f, indent=2, ensure_ascii=False)
        
        print(f"💾 User metrics saved: {json_file}")
    
    def _save_error_metrics(self, filename_prefix: str):
        """Save error metrics to JSON file."""
        json_file = self.output_dir / f"{filename_prefix}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.error_metrics, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Error metrics saved: {json_file}")
    
    def get_summary_stats(self) -> Dict[str, Any]:
        """
        Get summary statistics for the current test.
        
        Returns:
            Dictionary containing summary statistics
        """
        total_requests = len(self.request_metrics)
        successful_requests = sum(1 for r in self.request_metrics if r['success'])
        
        search_count = len(self.search_metrics)
        successful_searches = sum(1 for s in self.search_metrics if s['success'])
        
        error_count = len(self.error_metrics)
        
        avg_response_time = 0
        if self.request_metrics:
            avg_response_time = sum(r['response_time'] for r in self.request_metrics) / total_requests
        
        return {
            'total_requests': total_requests,
            'successful_requests': successful_requests,
            'success_rate': successful_requests / total_requests if total_requests > 0 else 0,
            'search_count': search_count,
            'successful_searches': successful_searches,
            'search_success_rate': successful_searches / search_count if search_count > 0 else 0,
            'error_count': error_count,
            'avg_response_time': avg_response_time,
            'test_duration': (datetime.now() - self.start_time).total_seconds() if self.start_time else 0
        }


# Global metrics collector instance
metrics_collector = MetricsCollector()
