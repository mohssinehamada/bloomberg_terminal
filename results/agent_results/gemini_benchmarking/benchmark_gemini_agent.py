import time
import statistics
import json
from datetime import datetime
import os

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../')))

from core.gemini_agent import Gemini2FlashWebAgent

def benchmark_agent():
    """Benchmark the Gemini2FlashWebAgent performance and save results to JSON"""
    # Get API key from environment
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env
    
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file!")

    # Initialize agent with rate limiting
    agent = Gemini2FlashWebAgent(api_key=api_key, calls_per_minute=5)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    benchmark_results = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "model": "gemini-2.0-flash",
            "rate_limit": 5
        },
        "interest_rates": {
            "tests": [],
            "summary": {}
        },
        "real_estate": {
            "tests": [],
            "summary": {}
        }
    }

    print("=" * 50)
    print("BENCHMARKING GEMINI WEB AGENT")
    print("=" * 50)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Benchmark parameters
    iterations = 3
    test_urls = [
        "https://www.federalreserve.gov/releases/h15/",
        "https://www.bankrate.com/banking/savings/rates/",
        "https://www.nerdwallet.com/best/banking/savings-rates"
    ]
    
    # Benchmark interest rate extraction
    interest_rate_times = []
    
    for iteration in range(iterations):
        for url in test_urls:
            print(f"\nBenchmarking URL: {url} (Iteration {iteration+1}/{iterations})")
            
            start_time = time.time()
            try:
                result = agent.extract_financial_interest_rates(url)
                execution_time = time.time() - start_time
                interest_rate_times.append(execution_time)
                print(f"Completed in {execution_time:.2f} seconds")
                
                # Add to benchmark results
                benchmark_results["interest_rates"]["tests"].append({
                    "url": url,
                    "iteration": iteration + 1,
                    "execution_time_seconds": execution_time,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                error_msg = str(e)
                print(f"Error: {error_msg}")
                
                # Add failed test to benchmark results
                benchmark_results["interest_rates"]["tests"].append({
                    "url": url,
                    "iteration": iteration + 1,
                    "execution_time_seconds": time.time() - start_time,
                    "timestamp": datetime.now().isoformat(),
                    "status": "failed",
                    "error": error_msg
                })
    
    # Real estate benchmark
    real_estate_url = "https://www.magicbricks.com/property-for-sale-rent-in-Vadodara/residential-real-estate-Vadodara"
    search_criteria_options = [
        {"location": "Vadodara", "min_price": 500000, "max_price": 1000000, "min_bedrooms": 2},
        {"location": "Vadodara", "min_price": 1000000, "max_price": 2000000, "min_bedrooms": 3},
        {"location": "Vadodara", "min_price": 2000000, "max_price": 3000000, "min_bedrooms": 4}
    ]
    
    real_estate_times = []
    
    for iteration in range(iterations):
        for criteria in search_criteria_options:
            print(f"\nBenchmarking Real Estate Search (Iteration {iteration+1}/{iterations})")
            print(f"Criteria: {json.dumps(criteria, indent=2)}")
            
            start_time = time.time()
            try:
                result = agent.search_estate_listings(real_estate_url, criteria)
                execution_time = time.time() - start_time
                real_estate_times.append(execution_time)
                print(f"Completed in {execution_time:.2f} seconds")
                
                # Add to benchmark results
                benchmark_results["real_estate"]["tests"].append({
                    "url": real_estate_url,
                    "criteria": criteria,
                    "iteration": iteration + 1,
                    "execution_time_seconds": execution_time,
                    "timestamp": datetime.now().isoformat(),
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                error_msg = str(e)
                print(f"Error: {error_msg}")
                
                # Add failed test to benchmark results
                benchmark_results["real_estate"]["tests"].append({
                    "url": real_estate_url,
                    "criteria": criteria,
                    "iteration": iteration + 1,
                    "execution_time_seconds": time.time() - start_time,
                    "timestamp": datetime.now().isoformat(),
                    "status": "failed",
                    "error": error_msg
                })
    
    # Calculate and add summary statistics
    if interest_rate_times:
        benchmark_results["interest_rates"]["summary"] = {
            "total_executions": len(interest_rate_times),
            "average_time": statistics.mean(interest_rate_times),
            "min_time": min(interest_rate_times),
            "max_time": max(interest_rate_times),
            "standard_deviation": statistics.stdev(interest_rate_times) if len(interest_rate_times) > 1 else 0
        }
    
    if real_estate_times:
        benchmark_results["real_estate"]["summary"] = {
            "total_executions": len(real_estate_times),
            "average_time": statistics.mean(real_estate_times),
            "min_time": min(real_estate_times),
            "max_time": max(real_estate_times),
            "standard_deviation": statistics.stdev(real_estate_times) if len(real_estate_times) > 1 else 0
        }
    
    # Generate filename with timestamp
    filename = f"gemini_web_agent_benchmark_{timestamp}.json"
    
    # Save results to JSON file
    with open(filename, 'w') as f:
        json.dump(benchmark_results, f, indent=2)
    
    print("\n" + "=" * 50)
    print("BENCHMARK SUMMARY")
    print("=" * 50)
    
    print("\nInterest Rate Extraction:")
    if interest_rate_times:
        print(f"Total executions: {len(interest_rate_times)}")
        print(f"Average time: {statistics.mean(interest_rate_times):.2f} seconds")
        print(f"Min time: {min(interest_rate_times):.2f} seconds")
        print(f"Max time: {max(interest_rate_times):.2f} seconds")
        if len(interest_rate_times) > 1:
            print(f"Standard deviation: {statistics.stdev(interest_rate_times):.2f} seconds")
    else:
        print("No successful executions")
    
    print("\nReal Estate Search:")
    if real_estate_times:
        print(f"Total executions: {len(real_estate_times)}")
        print(f"Average time: {statistics.mean(real_estate_times):.2f} seconds")
        print(f"Min time: {min(real_estate_times):.2f} seconds")
        print(f"Max time: {max(real_estate_times):.2f} seconds")
        if len(real_estate_times) > 1:
            print(f"Standard deviation: {statistics.stdev(real_estate_times):.2f} seconds")
    else:
        print("No successful executions")
    
    print(f"\nEnd time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\nResults saved to: {filename}")

if __name__ == "__main__":
    # Run the benchmarks
    benchmark_agent()