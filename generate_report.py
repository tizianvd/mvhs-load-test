#!/usr/bin/env python3
"""
Advanced Report Generator for MVHS.de Load Test Results
Generates detailed analytics and visualizations from Locust test data
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


class MVHSReportGenerator:
    """Generate comprehensive reports from Locust test data"""
    
    def __init__(self, reports_dir="reports"):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(exist_ok=True)
        
        # Set style for plots
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
    def find_latest_metrics(self):
        """Find the most recent metrics files"""
        # Look in both root directory (old location) and metrics subdirectory (new location)
        search_patterns = [
            "search_metrics_*.json",
            "reports/metrics/search_metrics_*.json"
        ]
        request_patterns = [
            "request_metrics_*.json", 
            "reports/metrics/request_metrics_*.json"
        ]
        
        search_files = []
        request_files = []
        
        for pattern in search_patterns:
            search_files.extend(glob.glob(pattern))
        
        for pattern in request_patterns:
            request_files.extend(glob.glob(pattern))
        
        if not search_files or not request_files:
            print("No metrics files found. Please run the load test first.")
            return None, None
            
        latest_search = max(search_files, key=os.path.getctime)
        latest_request = max(request_files, key=os.path.getctime)
        
        return latest_search, latest_request
    
    def load_metrics_data(self, search_file=None, request_file=None):
        """Load metrics data from files"""
        if not search_file or not request_file:
            search_file, request_file = self.find_latest_metrics()
            if not search_file:
                return None, None
        
        try:
            with open(search_file, 'r') as f:
                search_data = json.load(f)
            
            with open(request_file, 'r') as f:
                request_data = json.load(f)
                
            return pd.DataFrame(search_data), pd.DataFrame(request_data)
            
        except Exception as e:
            print(f"Error loading metrics data: {e}")
            return None, None
    
    def generate_summary_report(self, search_df, request_df):
        """Generate a comprehensive summary report"""
        report = []
        report.append("MVHS.de Load Test - Comprehensive Analysis Report")
        report.append("=" * 60)
        report.append(f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Overall Statistics
        report.append("OVERALL TEST STATISTICS")
        report.append("-" * 30)
        total_requests = len(request_df)
        successful_requests = len(request_df[request_df['success'] == True])
        failed_requests = total_requests - successful_requests
        
        if total_requests > 0:
            success_rate = (successful_requests / total_requests) * 100
            avg_response_time = request_df['response_time_ms'].mean()
            median_response_time = request_df['response_time_ms'].median()
            p95_response_time = request_df['response_time_ms'].quantile(0.95)
            p99_response_time = request_df['response_time_ms'].quantile(0.99)
            
            report.append(f"Total Requests: {total_requests:,}")
            report.append(f"Successful Requests: {successful_requests:,}")
            report.append(f"Failed Requests: {failed_requests:,}")
            report.append(f"Success Rate: {success_rate:.2f}%")
            report.append(f"Average Response Time: {avg_response_time:.2f}ms")
            report.append(f"Median Response Time: {median_response_time:.2f}ms")
            report.append(f"95th Percentile: {p95_response_time:.2f}ms")
            report.append(f"99th Percentile: {p99_response_time:.2f}ms")
            
            # Data transfer statistics
            total_data = request_df['response_size_bytes'].sum()
            avg_response_size = request_df['response_size_bytes'].mean()
            report.append(f"Total Data Transferred: {total_data:,} bytes ({total_data/1024/1024:.2f} MB)")
            report.append(f"Average Response Size: {avg_response_size:.2f} bytes")
        
        report.append("")
        
        # Search-Specific Statistics
        if not search_df.empty:
            report.append("SEARCH FUNCTIONALITY ANALYSIS")
            report.append("-" * 35)
            total_searches = len(search_df)
            avg_search_time = search_df['response_time_ms'].mean()
            median_search_time = search_df['response_time_ms'].median()
            
            report.append(f"Total Search Operations: {total_searches:,}")
            report.append(f"Average Search Response Time: {avg_search_time:.2f}ms")
            report.append(f"Median Search Response Time: {median_search_time:.2f}ms")
            
            # Search term analysis
            search_term_counts = search_df['search_term'].value_counts()
            report.append(f"\nTop 10 Search Terms:")
            for term, count in search_term_counts.head(10).items():
                report.append(f"  {term}: {count} searches")
            
            # Search performance by term
            search_performance = search_df.groupby('search_term')['response_time_ms'].agg(['mean', 'count']).sort_values('mean', ascending=False)
            report.append(f"\nSlowest Search Terms (avg response time):")
            for term, stats in search_performance.head(5).iterrows():
                report.append(f"  {term}: {stats['mean']:.2f}ms (n={stats['count']})")
        
        report.append("")
        
        # Request Type Analysis
        request_type_stats = request_df.groupby('request_type').agg({
            'response_time_ms': ['count', 'mean', 'median'],
            'success': 'sum'
        }).round(2)
        
        report.append("REQUEST TYPE BREAKDOWN")
        report.append("-" * 25)
        for req_type in request_type_stats.index:
            count = request_type_stats.loc[req_type, ('response_time_ms', 'count')]
            avg_time = request_type_stats.loc[req_type, ('response_time_ms', 'mean')]
            successes = request_type_stats.loc[req_type, ('success', 'sum')]
            success_rate = (successes / count) * 100 if count > 0 else 0
            
            report.append(f"{req_type}:")
            report.append(f"  Requests: {count}")
            report.append(f"  Avg Response Time: {avg_time:.2f}ms")
            report.append(f"  Success Rate: {success_rate:.1f}%")
            report.append("")
        
        return "\n".join(report)
    
    def create_visualizations(self, search_df, request_df):
        """Create comprehensive visualizations"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create a figure with multiple subplots
        fig = plt.figure(figsize=(20, 24))
        
        # 1. Response Time Distribution
        plt.subplot(4, 2, 1)
        plt.hist(request_df['response_time_ms'], bins=50, alpha=0.7, edgecolor='black')
        plt.title('Response Time Distribution', fontsize=14, fontweight='bold')
        plt.xlabel('Response Time (ms)')
        plt.ylabel('Frequency')
        plt.grid(True, alpha=0.3)
        
        # 2. Response Time Over Time
        plt.subplot(4, 2, 2)
        request_df['timestamp'] = pd.to_datetime(request_df['timestamp'])
        request_df_sorted = request_df.sort_values('timestamp')
        plt.plot(request_df_sorted['timestamp'], request_df_sorted['response_time_ms'], alpha=0.6)
        plt.title('Response Time Over Time', fontsize=14, fontweight='bold')
        plt.xlabel('Time')
        plt.ylabel('Response Time (ms)')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        
        # 3. Success Rate by Request Type
        plt.subplot(4, 2, 3)
        success_by_type = request_df.groupby('request_type')['success'].agg(['sum', 'count'])
        success_rates = (success_by_type['sum'] / success_by_type['count'] * 100)
        bars = plt.bar(range(len(success_rates)), success_rates.values)
        plt.title('Success Rate by Request Type', fontsize=14, fontweight='bold')
        plt.xlabel('Request Type')
        plt.ylabel('Success Rate (%)')
        plt.xticks(range(len(success_rates)), success_rates.index, rotation=45, ha='right')
        plt.ylim(0, 105)
        
        # Add value labels on bars
        for bar, rate in zip(bars, success_rates.values):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1, 
                    f'{rate:.1f}%', ha='center', va='bottom')
        plt.grid(True, alpha=0.3)
        
        # 4. Average Response Time by Request Type
        plt.subplot(4, 2, 4)
        avg_time_by_type = request_df.groupby('request_type')['response_time_ms'].mean()
        bars = plt.bar(range(len(avg_time_by_type)), avg_time_by_type.values)
        plt.title('Average Response Time by Request Type', fontsize=14, fontweight='bold')
        plt.xlabel('Request Type')
        plt.ylabel('Average Response Time (ms)')
        plt.xticks(range(len(avg_time_by_type)), avg_time_by_type.index, rotation=45, ha='right')
        
        # Add value labels on bars
        for bar, time in zip(bars, avg_time_by_type.values):
            plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(avg_time_by_type.values) * 0.01, 
                    f'{time:.1f}ms', ha='center', va='bottom')
        plt.grid(True, alpha=0.3)
        
        # 5. Search Term Frequency (if search data available)
        if not search_df.empty:
            plt.subplot(4, 2, 5)
            search_counts = search_df['search_term'].value_counts().head(10)
            bars = plt.bar(range(len(search_counts)), search_counts.values)
            plt.title('Top 10 Search Terms by Frequency', fontsize=14, fontweight='bold')
            plt.xlabel('Search Terms')
            plt.ylabel('Number of Searches')
            plt.xticks(range(len(search_counts)), search_counts.index, rotation=45, ha='right')
            
            # Add value labels on bars
            for bar, count in zip(bars, search_counts.values):
                plt.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(search_counts.values) * 0.01, 
                        f'{count}', ha='center', va='bottom')
            plt.grid(True, alpha=0.3)
            
            # 6. Search Response Time vs Result Count
            plt.subplot(4, 2, 6)
            plt.scatter(search_df['result_count'], search_df['response_time_ms'], alpha=0.6)
            plt.title('Search Response Time vs Result Count', fontsize=14, fontweight='bold')
            plt.xlabel('Number of Results Found')
            plt.ylabel('Response Time (ms)')
            plt.grid(True, alpha=0.3)
        
        # 7. Response Size Distribution
        plt.subplot(4, 2, 7)
        plt.hist(request_df['response_size_bytes'], bins=50, alpha=0.7, edgecolor='black')
        plt.title('Response Size Distribution', fontsize=14, fontweight='bold')
        plt.xlabel('Response Size (bytes)')
        plt.ylabel('Frequency')
        plt.grid(True, alpha=0.3)
        
        # 8. Request Volume Over Time
        plt.subplot(4, 2, 8)
        request_df['timestamp'] = pd.to_datetime(request_df['timestamp'])
        request_df['minute'] = request_df['timestamp'].dt.floor('min')
        requests_per_minute = request_df.groupby('minute').size()
        plt.plot(requests_per_minute.index, requests_per_minute.values, marker='o')
        plt.title('Request Volume Over Time', fontsize=14, fontweight='bold')
        plt.xlabel('Time')
        plt.ylabel('Requests per Minute')
        plt.xticks(rotation=45)
        plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save the visualization
        plot_file = self.reports_dir / f'mvhs_load_test_analysis_{timestamp}.png'
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        return plot_file
    
    def generate_performance_insights(self, search_df, request_df):
        """Generate performance insights and recommendations"""
        insights = []
        insights.append("PERFORMANCE INSIGHTS & RECOMMENDATIONS")
        insights.append("=" * 45)
        insights.append("")
        
        # Response time analysis
        avg_response_time = request_df['response_time_ms'].mean()
        p95_response_time = request_df['response_time_ms'].quantile(0.95)
        
        insights.append("Response Time Analysis:")
        if avg_response_time > 2000:
            insights.append("⚠️  HIGH: Average response time exceeds 2 seconds")
            insights.append("   Recommendation: Investigate server performance and caching")
        elif avg_response_time > 1000:
            insights.append("⚠️  MEDIUM: Average response time is above 1 second")
            insights.append("   Recommendation: Consider optimization opportunities")
        else:
            insights.append("✅ GOOD: Average response time is acceptable")
        
        if p95_response_time > 5000:
            insights.append("⚠️  HIGH: 95th percentile response time exceeds 5 seconds")
            insights.append("   Recommendation: Investigate slow queries and optimize bottlenecks")
        
        insights.append("")
        
        # Success rate analysis
        success_rate = (request_df['success'].sum() / len(request_df)) * 100
        insights.append("Reliability Analysis:")
        if success_rate < 95:
            insights.append("⚠️  HIGH: Success rate is below 95%")
            insights.append("   Recommendation: Investigate and fix error-causing requests")
        elif success_rate < 99:
            insights.append("⚠️  MEDIUM: Success rate is below 99%")
            insights.append("   Recommendation: Monitor and address occasional failures")
        else:
            insights.append("✅ EXCELLENT: Success rate is above 99%")
        
        insights.append("")
        
        # Search functionality insights
        if not search_df.empty:
            search_avg = search_df['response_time_ms'].mean()
            insights.append("Search Functionality Analysis:")
            if search_avg > avg_response_time * 1.5:
                insights.append("⚠️  ATTENTION: Search operations are significantly slower than average")
                insights.append("   Recommendation: Optimize search indexing and queries")
            else:
                insights.append("✅ GOOD: Search performance is consistent with overall site performance")
            
            # Check for search terms that are consistently slow
            slow_searches = search_df.groupby('search_term')['response_time_ms'].mean().sort_values(ascending=False).head(3)
            if not slow_searches.empty and slow_searches.iloc[0] > search_avg * 1.5:
                insights.append("⚠️  Slow search terms detected:")
                for term, time in slow_searches.items():
                    insights.append(f"   - '{term}': {time:.2f}ms")
                insights.append("   Recommendation: Investigate why these terms are slow")
        
        insights.append("")
        
        # Volume insights
        total_requests = len(request_df)
        test_duration = (pd.to_datetime(request_df['timestamp']).max() - 
                        pd.to_datetime(request_df['timestamp']).min()).total_seconds()
        if test_duration > 0:
            rps = total_requests / test_duration
            insights.append("Load Handling Analysis:")
            insights.append(f"Average requests per second: {rps:.2f}")
            if rps > 50:
                insights.append("✅ EXCELLENT: Site handles high request volume well")
            elif rps > 10:
                insights.append("✅ GOOD: Site handles moderate request volume well")
            else:
                insights.append("ℹ️  INFO: Test was conducted at low request volume")
        
        return "\n".join(insights)
    
    def generate_full_report(self, search_file=None, request_file=None):
        """Generate complete report with all analysis"""
        print("Loading metrics data...")
        search_df, request_df = self.load_metrics_data(search_file, request_file)
        
        if search_df is None or request_df is None:
            print("Failed to load metrics data.")
            return
        
        print("Generating summary report...")
        summary = self.generate_summary_report(search_df, request_df)
        
        print("Creating visualizations...")
        plot_file = self.create_visualizations(search_df, request_df)
        
        print("Generating performance insights...")
        insights = self.generate_performance_insights(search_df, request_df)
        
        # Combine all reports
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.reports_dir / f'mvhs_comprehensive_report_{timestamp}.txt'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(summary)
            f.write("\n\n")
            f.write(insights)
            f.write(f"\n\nVisualization saved to: {plot_file}")
        
        print(f"\n{'='*60}")
        print("REPORT GENERATION COMPLETE")
        print(f"{'='*60}")
        print(f"Comprehensive report: {report_file}")
        print(f"Visualizations: {plot_file}")
        print(f"{'='*60}")
        
        # Also print summary to console
        print("\n" + summary)
        print("\n" + insights)
        
        return report_file, plot_file


def main():
    """Main function to run the report generator"""
    generator = MVHSReportGenerator()
    
    if len(sys.argv) > 2:
        search_file = sys.argv[1]
        request_file = sys.argv[2]
        generator.generate_full_report(search_file, request_file)
    else:
        generator.generate_full_report()


if __name__ == "__main__":
    main()
