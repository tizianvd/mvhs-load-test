"""
Enhanced report generator for MVHS load test results.

This module provides comprehensive reporting and analytics capabilities
for load testing results, including visualizations and insights.
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import glob
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any


class MVHSReportGenerator:
    """Generate comprehensive reports from load test data."""
    
    def __init__(self, reports_dir: str = "reports"):
        """
        Initialize the report generator.
        
        Args:
            reports_dir: Directory containing test reports and metrics
        """
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)
        
        self.metrics_dir = self.reports_dir / "metrics"
        self.metrics_dir.mkdir(exist_ok=True)
        
        # Set style for plots
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Configure matplotlib for better output
        plt.rcParams['figure.figsize'] = (12, 8)
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.grid'] = True
        plt.rcParams['grid.alpha'] = 0.3
    
    def find_latest_metrics(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Find the most recent metrics files.
        
        Returns:
            Tuple of (search_metrics_file, request_metrics_file) or (None, None)
        """
        # Search patterns for metrics files
        search_patterns = [
            str(self.metrics_dir / "*search_metrics*.json"),
            "search_metrics_*.json"
        ]
        request_patterns = [
            str(self.metrics_dir / "*request_metrics*.json"),
            "request_metrics_*.json"
        ]
        
        search_files = []
        request_files = []
        
        for pattern in search_patterns:
            search_files.extend(glob.glob(pattern))
        
        for pattern in request_patterns:
            request_files.extend(glob.glob(pattern))
        
        if not search_files or not request_files:
            print("❌ No metrics files found!")
            print(f"Searched in: {self.metrics_dir} and current directory")
            return None, None
        
        # Get the most recent files
        latest_search = max(search_files, key=os.path.getctime)
        latest_request = max(request_files, key=os.path.getctime)
        
        return latest_search, latest_request
    
    def load_metrics_data(self, search_file: str, request_file: str) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Load metrics data from JSON files.
        
        Args:
            search_file: Path to search metrics JSON file
            request_file: Path to request metrics JSON file
            
        Returns:
            Tuple of (search_dataframe, request_dataframe)
        """
        try:
            # Load search metrics
            with open(search_file, 'r', encoding='utf-8') as f:
                search_data = json.load(f)
            search_df = pd.DataFrame(search_data)
            
            # Convert timestamp to datetime
            if not search_df.empty and 'timestamp' in search_df.columns:
                search_df['datetime'] = pd.to_datetime(search_df['timestamp'], unit='s')
            
            # Load request metrics
            with open(request_file, 'r', encoding='utf-8') as f:
                request_data = json.load(f)
            request_df = pd.DataFrame(request_data)
            
            # Convert timestamp to datetime
            if not request_df.empty and 'timestamp' in request_df.columns:
                request_df['datetime'] = pd.to_datetime(request_df['timestamp'], unit='s')
            
            print(f"📊 Loaded {len(search_df)} search metrics and {len(request_df)} request metrics")
            return search_df, request_df
            
        except Exception as e:
            print(f"❌ Error loading metrics data: {e}")
            return pd.DataFrame(), pd.DataFrame()
    
    def generate_summary_report(self, search_df: pd.DataFrame, request_df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate summary statistics report.
        
        Args:
            search_df: Search metrics dataframe
            request_df: Request metrics dataframe
            
        Returns:
            Dictionary containing summary statistics
        """
        summary = {
            'test_overview': {},
            'search_metrics': {},
            'request_metrics': {},
            'performance_metrics': {}
        }
        
        # Test overview
        if not request_df.empty:
            test_start = request_df['datetime'].min()
            test_end = request_df['datetime'].max()
            test_duration = (test_end - test_start).total_seconds()
            
            summary['test_overview'] = {
                'start_time': test_start.strftime('%Y-%m-%d %H:%M:%S'),
                'end_time': test_end.strftime('%Y-%m-%d %H:%M:%S'),
                'duration_seconds': test_duration,
                'duration_minutes': test_duration / 60,
                'total_requests': len(request_df)
            }
        
        # Search metrics
        if not search_df.empty:
            successful_searches = search_df['success'].sum()
            total_searches = len(search_df)
            
            summary['search_metrics'] = {
                'total_searches': total_searches,
                'successful_searches': successful_searches,
                'search_success_rate': successful_searches / total_searches if total_searches > 0 else 0,
                'avg_search_response_time': search_df['response_time'].mean(),
                'avg_results_per_search': search_df['results_found'].mean(),
                'unique_search_terms': search_df['search_term'].nunique(),
                'most_searched_terms': search_df['search_term'].value_counts().head(10).to_dict()
            }
        
        # Request metrics
        if not request_df.empty:
            successful_requests = request_df['success'].sum()
            total_requests = len(request_df)
            
            summary['request_metrics'] = {
                'total_requests': total_requests,
                'successful_requests': successful_requests,
                'success_rate': successful_requests / total_requests if total_requests > 0 else 0,
                'avg_response_time': request_df['response_time'].mean(),
                'median_response_time': request_df['response_time'].median(),
                'p95_response_time': request_df['response_time'].quantile(0.95),
                'p99_response_time': request_df['response_time'].quantile(0.99),
                'requests_per_second': total_requests / summary['test_overview'].get('duration_seconds', 1),
                'request_types': request_df['request_type'].value_counts().to_dict(),
                'most_requested_endpoints': request_df['name'].value_counts().head(10).to_dict()
            }
        
        # Performance metrics
        if not request_df.empty:
            response_times = request_df['response_time']
            
            summary['performance_metrics'] = {
                'min_response_time': response_times.min(),
                'max_response_time': response_times.max(),
                'std_response_time': response_times.std(),
                'slow_requests_count': (response_times > 5000).sum(),  # > 5 seconds
                'very_slow_requests_count': (response_times > 10000).sum(),  # > 10 seconds
                'fast_requests_count': (response_times < 1000).sum(),  # < 1 second
            }
        
        return summary
    
    def create_visualizations(self, search_df: pd.DataFrame, request_df: pd.DataFrame, output_dir: Path):
        """
        Create visualization charts.
        
        Args:
            search_df: Search metrics dataframe
            request_df: Request metrics dataframe
            output_dir: Directory to save charts
        """
        output_dir.mkdir(exist_ok=True)
        
        # 1. Response time distribution
        if not request_df.empty:
            plt.figure(figsize=(12, 6))
            plt.hist(request_df['response_time'], bins=50, alpha=0.7, edgecolor='black')
            plt.xlabel('Response Time (ms)')
            plt.ylabel('Frequency')
            plt.title('Response Time Distribution')
            plt.grid(True, alpha=0.3)
            plt.savefig(output_dir / 'response_time_distribution.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        # 2. Response time over time
        if not request_df.empty and 'datetime' in request_df.columns:
            plt.figure(figsize=(14, 6))
            
            # Resample to get average response time per minute
            request_df.set_index('datetime')['response_time'].resample('1T').mean().plot()
            plt.xlabel('Time')
            plt.ylabel('Average Response Time (ms)')
            plt.title('Response Time Over Time')
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3)
            plt.tight_layout()
            plt.savefig(output_dir / 'response_time_timeline.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        # 3. Request success rate
        if not request_df.empty:
            success_counts = request_df['success'].value_counts()
            
            plt.figure(figsize=(8, 6))
            plt.pie(success_counts.values, labels=['Success', 'Failed'], autopct='%1.1f%%',
                   colors=['#2ecc71', '#e74c3c'])
            plt.title('Request Success Rate')
            plt.savefig(output_dir / 'request_success_rate.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        # 4. Search performance
        if not search_df.empty:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # Search response times
            ax1.hist(search_df['response_time'], bins=30, alpha=0.7, edgecolor='black')
            ax1.set_xlabel('Search Response Time (ms)')
            ax1.set_ylabel('Frequency')
            ax1.set_title('Search Response Time Distribution')
            ax1.grid(True, alpha=0.3)
            
            # Results per search
            ax2.hist(search_df['results_found'], bins=30, alpha=0.7, edgecolor='black')
            ax2.set_xlabel('Number of Results')
            ax2.set_ylabel('Frequency')
            ax2.set_title('Search Results Distribution')
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(output_dir / 'search_performance.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        # 5. Top search terms
        if not search_df.empty and 'search_term' in search_df.columns:
            top_terms = search_df['search_term'].value_counts().head(15)
            
            plt.figure(figsize=(12, 8))
            top_terms.plot(kind='barh')
            plt.xlabel('Number of Searches')
            plt.ylabel('Search Terms')
            plt.title('Most Popular Search Terms')
            plt.grid(True, alpha=0.3, axis='x')
            plt.tight_layout()
            plt.savefig(output_dir / 'top_search_terms.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        # 6. Request types breakdown
        if not request_df.empty and 'request_type' in request_df.columns:
            request_types = request_df['request_type'].value_counts()
            
            plt.figure(figsize=(10, 6))
            request_types.plot(kind='bar')
            plt.xlabel('Request Type')
            plt.ylabel('Count')
            plt.title('Request Types Distribution')
            plt.xticks(rotation=45)
            plt.grid(True, alpha=0.3, axis='y')
            plt.tight_layout()
            plt.savefig(output_dir / 'request_types.png', dpi=300, bbox_inches='tight')
            plt.close()
        
        print(f"📈 Visualizations saved to {output_dir}")
    
    def generate_html_report(self, summary: Dict[str, Any], output_file: Path):
        """
        Generate an HTML report.
        
        Args:
            summary: Summary statistics dictionary
            output_file: Path to save the HTML report
        """
        from jinja2 import Template
        
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MVHS Load Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }
        .header { background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }
        .section { margin: 20px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; }
        .metric { display: inline-block; margin: 10px; padding: 10px; background: white; border-radius: 3px; min-width: 200px; }
        .metric-value { font-size: 1.5em; font-weight: bold; color: #2c3e50; }
        .metric-label { color: #7f8c8d; }
        .charts { display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px; }
        .chart { text-align: center; }
        .chart img { max-width: 100%; height: auto; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f2f2f2; }
        .success { color: #27ae60; }
        .error { color: #e74c3c; }
        .warning { color: #f39c12; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 MVHS Load Test Report</h1>
        <p>Generated on {{ report_date }}</p>
    </div>

    <div class="section">
        <h2>📊 Test Overview</h2>
        {% if summary.test_overview %}
        <div class="metric">
            <div class="metric-value">{{ "%.1f"|format(summary.test_overview.duration_minutes) }} min</div>
            <div class="metric-label">Test Duration</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ summary.test_overview.total_requests }}</div>
            <div class="metric-label">Total Requests</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ summary.test_overview.start_time }}</div>
            <div class="metric-label">Start Time</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ summary.test_overview.end_time }}</div>
            <div class="metric-label">End Time</div>
        </div>
        {% endif %}
    </div>

    <div class="section">
        <h2>🔍 Search Performance</h2>
        {% if summary.search_metrics %}
        <div class="metric">
            <div class="metric-value">{{ summary.search_metrics.total_searches }}</div>
            <div class="metric-label">Total Searches</div>
        </div>
        <div class="metric">
            <div class="metric-value {% if summary.search_metrics.search_success_rate > 0.95 %}success{% elif summary.search_metrics.search_success_rate > 0.85 %}warning{% else %}error{% endif %}">
                {{ "%.1f"|format(summary.search_metrics.search_success_rate * 100) }}%
            </div>
            <div class="metric-label">Success Rate</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ "%.0f"|format(summary.search_metrics.avg_search_response_time) }} ms</div>
            <div class="metric-label">Avg Response Time</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ "%.1f"|format(summary.search_metrics.avg_results_per_search) }}</div>
            <div class="metric-label">Avg Results per Search</div>
        </div>
        {% endif %}
    </div>

    <div class="section">
        <h2>🌐 Request Performance</h2>
        {% if summary.request_metrics %}
        <div class="metric">
            <div class="metric-value {% if summary.request_metrics.success_rate > 0.98 %}success{% elif summary.request_metrics.success_rate > 0.90 %}warning{% else %}error{% endif %}">
                {{ "%.1f"|format(summary.request_metrics.success_rate * 100) }}%
            </div>
            <div class="metric-label">Success Rate</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ "%.0f"|format(summary.request_metrics.avg_response_time) }} ms</div>
            <div class="metric-label">Avg Response Time</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ "%.0f"|format(summary.request_metrics.p95_response_time) }} ms</div>
            <div class="metric-label">95th Percentile</div>
        </div>
        <div class="metric">
            <div class="metric-value">{{ "%.1f"|format(summary.request_metrics.requests_per_second) }}</div>
            <div class="metric-label">Requests/Second</div>
        </div>
        {% endif %}
    </div>

    <div class="section">
        <h2>📈 Performance Charts</h2>
        <div class="charts">
            <div class="chart">
                <h3>Response Time Distribution</h3>
                <img src="charts/response_time_distribution.png" alt="Response Time Distribution">
            </div>
            <div class="chart">
                <h3>Response Time Timeline</h3>
                <img src="charts/response_time_timeline.png" alt="Response Time Timeline">
            </div>
            <div class="chart">
                <h3>Request Success Rate</h3>
                <img src="charts/request_success_rate.png" alt="Request Success Rate">
            </div>
            <div class="chart">
                <h3>Search Performance</h3>
                <img src="charts/search_performance.png" alt="Search Performance">
            </div>
            <div class="chart">
                <h3>Top Search Terms</h3>
                <img src="charts/top_search_terms.png" alt="Top Search Terms">
            </div>
            <div class="chart">
                <h3>Request Types</h3>
                <img src="charts/request_types.png" alt="Request Types">
            </div>
        </div>
    </div>

    <div class="section">
        <h2>🏆 Key Insights</h2>
        <ul>
            {% if summary.request_metrics.success_rate %}
            <li {% if summary.request_metrics.success_rate > 0.98 %}class="success"{% elif summary.request_metrics.success_rate > 0.90 %}class="warning"{% else %}class="error"{% endif %}>
                Overall success rate: {{ "%.1f"|format(summary.request_metrics.success_rate * 100) }}%
            </li>
            {% endif %}
            {% if summary.request_metrics.avg_response_time %}
            <li {% if summary.request_metrics.avg_response_time < 1000 %}class="success"{% elif summary.request_metrics.avg_response_time < 3000 %}class="warning"{% else %}class="error"{% endif %}>
                Average response time: {{ "%.0f"|format(summary.request_metrics.avg_response_time) }}ms
            </li>
            {% endif %}
            {% if summary.search_metrics.search_success_rate %}
            <li {% if summary.search_metrics.search_success_rate > 0.95 %}class="success"{% elif summary.search_metrics.search_success_rate > 0.85 %}class="warning"{% else %}class="error"{% endif %}>
                Search success rate: {{ "%.1f"|format(summary.search_metrics.search_success_rate * 100) }}%
            </li>
            {% endif %}
            {% if summary.performance_metrics.slow_requests_count %}
            <li {% if summary.performance_metrics.slow_requests_count == 0 %}class="success"{% elif summary.performance_metrics.slow_requests_count < 10 %}class="warning"{% else %}class="error"{% endif %}>
                Slow requests (>5s): {{ summary.performance_metrics.slow_requests_count }}
            </li>
            {% endif %}
        </ul>
    </div>

    <div class="section">
        <h2>📋 Detailed Statistics</h2>
        <h3>Top Search Terms</h3>
        {% if summary.search_metrics and summary.search_metrics.most_searched_terms %}
        <table>
            <tr><th>Search Term</th><th>Count</th></tr>
            {% for term, count in summary.search_metrics.most_searched_terms.items() %}
            <tr><td>{{ term }}</td><td>{{ count }}</td></tr>
            {% endfor %}
        </table>
        {% endif %}

        <h3>Most Requested Endpoints</h3>
        {% if summary.request_metrics and summary.request_metrics.most_requested_endpoints %}
        <table>
            <tr><th>Endpoint</th><th>Count</th></tr>
            {% for endpoint, count in summary.request_metrics.most_requested_endpoints.items() %}
            <tr><td>{{ endpoint }}</td><td>{{ count }}</td></tr>
            {% endfor %}
        </table>
        {% endif %}
    </div>

    <footer style="margin-top: 50px; text-align: center; color: #7f8c8d;">
        <p>Generated by MVHS Load Testing Framework v2.0</p>
    </footer>
</body>
</html>
        """
        
        template = Template(html_template)
        html_content = template.render(
            summary=summary,
            report_date=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📄 HTML report saved to {output_file}")
    
    def generate_full_report(self) -> bool:
        """
        Generate a complete report with all analytics.
        
        Returns:
            True if report was generated successfully, False otherwise
        """
        try:
            # Find latest metrics files
            search_file, request_file = self.find_latest_metrics()
            if not search_file or not request_file:
                return False
            
            print(f"📊 Generating report from:")
            print(f"   Search metrics: {search_file}")
            print(f"   Request metrics: {request_file}")
            
            # Load data
            search_df, request_df = self.load_metrics_data(search_file, request_file)
            if search_df.empty and request_df.empty:
                print("❌ No data to generate report")
                return False
            
            # Generate summary
            summary = self.generate_summary_report(search_df, request_df)
            
            # Create output directory with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_dir = self.reports_dir / f"analysis_{timestamp}"
            report_dir.mkdir(exist_ok=True)
            
            charts_dir = report_dir / "charts"
            
            # Create visualizations
            self.create_visualizations(search_df, request_df, charts_dir)
            
            # Generate HTML report
            html_report = report_dir / "load_test_report.html"
            self.generate_html_report(summary, html_report)
            
            # Save summary as JSON
            summary_file = report_dir / "summary.json"
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"✅ Complete report generated in {report_dir}")
            print(f"🌐 Open {html_report} in your browser to view the report")
            
            return True
            
        except Exception as e:
            print(f"❌ Error generating report: {e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    """Main function for command-line usage."""
    if len(sys.argv) > 1:
        reports_dir = sys.argv[1]
    else:
        reports_dir = "reports"
    
    generator = MVHSReportGenerator(reports_dir)
    success = generator.generate_full_report()
    
    if success:
        print("\n🎉 Report generation completed successfully!")
    else:
        print("\n❌ Report generation failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
