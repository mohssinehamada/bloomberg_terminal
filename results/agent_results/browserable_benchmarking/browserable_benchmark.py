import time
import statistics
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
import matplotlib.pyplot as plt
import json
import os
from dotenv import load_dotenv
import pandas as pd
import logging

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from core.simple_browserable import EnhancedBrowserable

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='benchmark_results.log'
)
logger = logging.getLogger(__name__)

class BrowserableBenchmark:
    """Class to benchmark the EnhancedBrowserable functionality"""
    
    def __init__(self, gemini_api_key=None):
        self.gemini_api_key = gemini_api_key
        self.results = {
            'navigation': [],
            'element_interaction': [],
            'content_extraction': [],
            'task_execution': [],
            'error_handling': []
        }
        self.summary = {}
        
    def run_benchmarks(self, iterations=3):
        """Run all benchmarks with specified iterations"""
        logger.info(f"Starting benchmarks with {iterations} iterations")
        
        # Run each benchmark multiple times
        for i in range(iterations):
            logger.info(f"Starting iteration {i+1}/{iterations}")
            
            # Create a fresh browser instance for each test
            browser = EnhancedBrowserable(self.gemini_api_key)
            if not browser.start():
                logger.error("Failed to start browser. Skipping iteration.")
                continue
                
            try:
                # Run benchmarks
                self._benchmark_navigation(browser)
                self._benchmark_element_interaction(browser)
                self._benchmark_content_extraction(browser)
                self._benchmark_task_execution(browser)
                self._benchmark_error_handling(browser)
            finally:
                browser.close()
                
        # Generate summary statistics
        self._generate_summary()
        
        return self.results, self.summary
        
    def _benchmark_navigation(self, browser):
        """Benchmark navigation performance"""
        test_urls = [
            "google.com",
            "github.com", 
            "wikipedia.org",
            "reddit.com",
            "news.ycombinator.com"
        ]
        
        for url in test_urls:
            start_time = time.time()
            result = browser.open_url(url)
            end_time = time.time()
            
            self.results['navigation'].append({
                'url': url,
                'success': result.get('success', False),
                'time_taken': end_time - start_time,
                'result': result
            })
            
            # Brief pause between navigations
            time.sleep(1)
    
    def _benchmark_element_interaction(self, browser):
        """Benchmark element interaction performance"""
        # Navigate to Google for testing
        browser.open_url("google.com")
        time.sleep(1)
        
        # Test typing
        start_time = time.time()
        type_result = browser.type_text('textarea[name="q"]', 'Playwright Python automation')
        type_time = time.time() - start_time
        
        # Test clicking (search button)
        start_time = time.time()
        click_result = browser.click_element('input[value="Google Search"]', wait_for_navigation=True)
        click_time = time.time() - start_time
        
        self.results['element_interaction'].append({
            'type_success': type_result.get('success', False),
            'type_time': type_time,
            'click_success': click_result.get('success', False),
            'click_time': click_time
        })
    
    def _benchmark_content_extraction(self, browser):
        """Benchmark content extraction capabilities"""
        # Navigate to Wikipedia which has tables
        browser.open_url("en.wikipedia.org/wiki/Web_browser_automation")
        time.sleep(2)
        
        # Test getting page content
        start_time = time.time()
        content_result = browser.get_page_content()
        content_time = time.time() - start_time
        content_success = 'error' not in content_result
        content_size = len(json.dumps(content_result)) if content_success else 0
        
        # Test table extraction
        start_time = time.time()
        table_result = browser.extract_table_data()
        table_time = time.time() - start_time
        table_success = table_result.get('success', False)
        table_count = len(table_result.get('tables', [])) if table_success else 0
        
        self.results['content_extraction'].append({
            'content_success': content_success,
            'content_time': content_time,
            'content_size': content_size,
            'table_success': table_success,
            'table_time': table_time,
            'tables_found': table_count
        })
    
    def _benchmark_task_execution(self, browser):
        """Benchmark predefined task execution"""
        start_time = time.time()
        result = browser.execute_task('federal_reserve_rates', year='2023')
        end_time = time.time()
        
        task_success = result.get('success', False)
        rates_found = 0
        
        if task_success and 'results' in result:
            for step_result in result['results']:
                if 'rates' in step_result:
                    rates_found = len(step_result['rates'])
        
        self.results['task_execution'].append({
            'task_name': 'federal_reserve_rates',
            'success': task_success,
            'time_taken': end_time - start_time,
            'rates_found': rates_found
        })
    
    def _benchmark_error_handling(self, browser):
        """Benchmark error handling capabilities"""
        # Test with invalid URL
        invalid_url_start = time.time()
        invalid_url_result = browser.open_url("htp://invalid-url-test.xyz")
        invalid_url_time = time.time() - invalid_url_start
        
        # Test with non-existent element
        browser.open_url("google.com")
        time.sleep(1)
        
        non_existent_start = time.time()
        non_existent_result = browser.click_element('#non-existent-element-123456')
        non_existent_time = time.time() - non_existent_start
        
        self.results['error_handling'].append({
            'invalid_url_handled': not invalid_url_result.get('success', True),
            'invalid_url_time': invalid_url_time,
            'non_existent_handled': not non_existent_result.get('success', True),
            'non_existent_time': non_existent_time
        })
        
    def _generate_summary(self):
        """Generate summary statistics from benchmark results"""
        # Navigation summary
        nav_times = [r['time_taken'] for r in self.results['navigation']]
        nav_success_rate = sum(1 for r in self.results['navigation'] if r['success']) / len(self.results['navigation']) * 100
        
        # Element interaction summary
        type_times = [r['type_time'] for r in self.results['element_interaction']]
        type_success_rate = sum(1 for r in self.results['element_interaction'] if r['type_success']) / len(self.results['element_interaction']) * 100
        click_times = [r['click_time'] for r in self.results['element_interaction']]
        click_success_rate = sum(1 for r in self.results['element_interaction'] if r['click_success']) / len(self.results['element_interaction']) * 100
        
        # Content extraction summary
        content_times = [r['content_time'] for r in self.results['content_extraction']]
        content_success_rate = sum(1 for r in self.results['content_extraction'] if r['content_success']) / len(self.results['content_extraction']) * 100
        table_times = [r['table_time'] for r in self.results['content_extraction']]
        
        # Task execution summary
        task_times = [r['time_taken'] for r in self.results['task_execution']]
        task_success_rate = sum(1 for r in self.results['task_execution'] if r['success']) / len(self.results['task_execution']) * 100
        
        # Error handling summary
        invalid_url_handled_rate = sum(1 for r in self.results['error_handling'] if r['invalid_url_handled']) / len(self.results['error_handling']) * 100
        non_existent_handled_rate = sum(1 for r in self.results['error_handling'] if r['non_existent_handled']) / len(self.results['error_handling']) * 100
        
        self.summary = {
            'navigation': {
                'avg_time': statistics.mean(nav_times) if nav_times else 0,
                'success_rate': nav_success_rate,
                'min_time': min(nav_times) if nav_times else 0,
                'max_time': max(nav_times) if nav_times else 0
            },
            'element_interaction': {
                'avg_type_time': statistics.mean(type_times) if type_times else 0,
                'type_success_rate': type_success_rate,
                'avg_click_time': statistics.mean(click_times) if click_times else 0,
                'click_success_rate': click_success_rate
            },
            'content_extraction': {
                'avg_content_time': statistics.mean(content_times) if content_times else 0,
                'content_success_rate': content_success_rate,
                'avg_table_time': statistics.mean(table_times) if table_times else 0
            },
            'task_execution': {
                'avg_time': statistics.mean(task_times) if task_times else 0,
                'success_rate': task_success_rate
            },
            'error_handling': {
                'invalid_url_handled_rate': invalid_url_handled_rate,
                'non_existent_handled_rate': non_existent_handled_rate
            }
        }
    
    def plot_results(self, save_path="benchmark_results"):
        """Generate and save plots of benchmark results"""
        if not os.path.exists(save_path):
            os.makedirs(save_path)
            
        # Plot navigation times
        self._plot_navigation_times(save_path)
        
        # Plot success rates
        self._plot_success_rates(save_path)
        
        # Plot timing comparisons
        self._plot_timing_comparisons(save_path)
        
        # Create summary report
        self._create_summary_report(save_path)
        
        return f"Results saved to {save_path} directory"
        
    def _plot_navigation_times(self, save_path):
        """Plot navigation times for different URLs"""
        if not self.results['navigation']:
            return
            
        urls = [r['url'] for r in self.results['navigation']]
        times = [r['time_taken'] for r in self.results['navigation']]
        
        plt.figure(figsize=(10, 6))
        plt.bar(urls, times)
        plt.xlabel('URL')
        plt.ylabel('Time (seconds)')
        plt.title('Navigation Time by URL')
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.savefig(f"{save_path}/navigation_times.png")
        plt.close()
        
    def _plot_success_rates(self, save_path):
        """Plot success rates for different operations"""
        categories = []
        rates = []
        
        if self.summary.get('navigation'):
            categories.append('Navigation')
            rates.append(self.summary['navigation']['success_rate'])
            
        if self.summary.get('element_interaction'):
            categories.append('Typing')
            rates.append(self.summary['element_interaction']['type_success_rate'])
            categories.append('Clicking')
            rates.append(self.summary['element_interaction']['click_success_rate'])
            
        if self.summary.get('content_extraction'):
            categories.append('Content')
            rates.append(self.summary['content_extraction']['content_success_rate'])
            
        if self.summary.get('task_execution'):
            categories.append('Tasks')
            rates.append(self.summary['task_execution']['success_rate'])
            
        if self.summary.get('error_handling'):
            categories.append('Error 1')
            rates.append(self.summary['error_handling']['invalid_url_handled_rate'])
            categories.append('Error 2')
            rates.append(self.summary['error_handling']['non_existent_handled_rate'])
        
        plt.figure(figsize=(10, 6))
        plt.bar(categories, rates)
        plt.xlabel('Operation')
        plt.ylabel('Success Rate (%)')
        plt.title('Success Rates by Operation')
        plt.ylim(0, 100)
        plt.tight_layout()
        plt.savefig(f"{save_path}/success_rates.png")
        plt.close()
        
    def _plot_timing_comparisons(self, save_path):
        """Plot timing comparisons for different operations"""
        operations = []
        times = []
        
        if self.summary.get('navigation'):
            operations.append('Navigation')
            times.append(self.summary['navigation']['avg_time'])
            
        if self.summary.get('element_interaction'):
            operations.append('Typing')
            times.append(self.summary['element_interaction']['avg_type_time'])
            operations.append('Clicking')
            times.append(self.summary['element_interaction']['avg_click_time'])
            
        if self.summary.get('content_extraction'):
            operations.append('Content')
            times.append(self.summary['content_extraction']['avg_content_time'])
            operations.append('Tables')
            times.append(self.summary['content_extraction']['avg_table_time'])
            
        if self.summary.get('task_execution'):
            operations.append('Tasks')
            times.append(self.summary['task_execution']['avg_time'])
        
        plt.figure(figsize=(10, 6))
        plt.bar(operations, times)
        plt.xlabel('Operation')
        plt.ylabel('Average Time (seconds)')
        plt.title('Average Time by Operation')
        plt.tight_layout()
        plt.savefig(f"{save_path}/timing_comparisons.png")
        plt.close()
        
    def _create_summary_report(self, save_path):
        """Create a summary report in Markdown format"""
        report = "# EnhancedBrowserable Benchmark Report\n\n"
        report += f"Report generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        report += "## Summary Statistics\n\n"
        
        # Navigation stats
        report += "### Navigation Performance\n\n"
        report += "| Metric | Value |\n"
        report += "|--------|-------|\n"
        if self.summary.get('navigation'):
            report += f"| Average Time | {self.summary['navigation']['avg_time']:.2f} seconds |\n"
            report += f"| Success Rate | {self.summary['navigation']['success_rate']:.2f}% |\n"
            report += f"| Min Time | {self.summary['navigation']['min_time']:.2f} seconds |\n"
            report += f"| Max Time | {self.summary['navigation']['max_time']:.2f} seconds |\n"
        
        # Element interaction stats
        report += "\n### Element Interaction Performance\n\n"
        report += "| Metric | Value |\n"
        report += "|--------|-------|\n"
        if self.summary.get('element_interaction'):
            report += f"| Average Typing Time | {self.summary['element_interaction']['avg_type_time']:.2f} seconds |\n"
            report += f"| Type Success Rate | {self.summary['element_interaction']['type_success_rate']:.2f}% |\n"
            report += f"| Average Click Time | {self.summary['element_interaction']['avg_click_time']:.2f} seconds |\n"
            report += f"| Click Success Rate | {self.summary['element_interaction']['click_success_rate']:.2f}% |\n"
        
        # Content extraction stats
        report += "\n### Content Extraction Performance\n\n"
        report += "| Metric | Value |\n"
        report += "|--------|-------|\n"
        if self.summary.get('content_extraction'):
            report += f"| Average Content Time | {self.summary['content_extraction']['avg_content_time']:.2f} seconds |\n"
            report += f"| Content Success Rate | {self.summary['content_extraction']['content_success_rate']:.2f}% |\n"
            report += f"| Average Table Time | {self.summary['content_extraction']['avg_table_time']:.2f} seconds |\n"
        
        # Task execution stats
        report += "\n### Task Execution Performance\n\n"
        report += "| Metric | Value |\n"
        report += "|--------|-------|\n"
        if self.summary.get('task_execution'):
            report += f"| Average Time | {self.summary['task_execution']['avg_time']:.2f} seconds |\n"
            report += f"| Success Rate | {self.summary['task_execution']['success_rate']:.2f}% |\n"
        
        # Error handling stats
        report += "\n### Error Handling Performance\n\n"
        report += "| Metric | Value |\n"
        report += "|--------|-------|\n"
        if self.summary.get('error_handling'):
            report += f"| Invalid URL Handled Rate | {self.summary['error_handling']['invalid_url_handled_rate']:.2f}% |\n"
            report += f"| Non-existent Element Handled Rate | {self.summary['error_handling']['non_existent_handled_rate']:.2f}% |\n"
            
        # Raw data reference  
        report += "\n## Full Results\n\n"
        report += "Raw benchmark data is available in JSON format: [benchmark_data.json](benchmark_data.json)\n\n"
        
        # Save report
        with open(f"{save_path}/benchmark_report.md", "w") as f:
            f.write(report)
            
        # Save raw data
        with open(f"{save_path}/benchmark_data.json", "w") as f:
            json.dump(self.results, f, indent=2)

def main():
    # Load environment variables
    load_dotenv()
    
    # Get Gemini API key from environment or user input
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if not gemini_api_key:
        gemini_api_key = input("Enter your Gemini API key (press Enter to skip): ")
    
    print("\n" + "="*60)
    print("EnhancedBrowserable Benchmark".center(60))
    print("="*60)
    
    # Get benchmark options
    try:
        iterations = int(input("Enter number of iterations (default: 3): ") or 3)
    except ValueError:
        iterations = 3
        print("Invalid value. Using default: 3 iterations.")
    
    # Create and run benchmark
    benchmark = BrowserableBenchmark(gemini_api_key)
    
    print("\nStarting benchmarks. This will take several minutes...")
    print("The browser will open and navigate to different websites automatically.")
    print("Please do not interact with the browser during testing.\n")
    
    start_time = time.time()
    results, summary = benchmark.run_benchmarks(iterations=iterations)
    total_time = time.time() - start_time
    
    print(f"\nBenchmarks completed in {total_time:.2f} seconds.")
    
    # Save results
    save_path = input("Enter path to save results (default: 'benchmark_results'): ") or "benchmark_results"
    benchmark.plot_results(save_path)
    
    print(f"\nResults saved to {save_path}/ directory")
    print("\nSummary Statistics:")
    
    # Print summary stats
    if summary.get('navigation'):
        print(f"\nNavigation:")
        print(f"  Success Rate: {summary['navigation']['success_rate']:.2f}%")
        print(f"  Average Time: {summary['navigation']['avg_time']:.2f} seconds")
    
    if summary.get('element_interaction'):
        print(f"\nElement Interaction:")
        print(f"  Typing Success Rate: {summary['element_interaction']['type_success_rate']:.2f}%")
        print(f"  Clicking Success Rate: {summary['element_interaction']['click_success_rate']:.2f}%")
    
    if summary.get('task_execution'):
        print(f"\nTask Execution:")
        print(f"  Success Rate: {summary['task_execution']['success_rate']:.2f}%")
        print(f"  Average Time: {summary['task_execution']['avg_time']:.2f} seconds")
    
    print("\nComplete details available in the generated report.")

if __name__ == "__main__":
    main()