"""
Advanced Test Configuration Manager

This module provides comprehensive test configuration management,
including test suite execution, result analysis, and A/B testing capabilities.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import asyncio
import statistics

@dataclass
class TestConfiguration:
    """Configuration for a specific test scenario"""
    name: str
    description: str
    test_type: str  # 'real_estate', 'financial', 'ecommerce', etc.
    websites: List[str]
    queries: List[str]
    max_iterations: int = 3
    max_steps_per_query: int = 10
    model_config: Dict[str, Any] = None
    browser_config: Dict[str, Any] = None
    economic_context_required: bool = True
    validation_criteria: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.model_config is None:
            self.model_config = {"temperature": 0.1, "max_tokens": 2000}
        if self.browser_config is None:
            self.browser_config = {"headless": True, "timeout": 30000}
        if self.validation_criteria is None:
            self.validation_criteria = {"min_success_rate": 80, "min_items_per_query": 3}

@dataclass 
class TestResult:
    """Results from a test execution"""
    config_name: str
    start_time: str
    end_time: str
    total_queries: int
    successful_queries: int
    success_rate: float
    total_items_extracted: int
    average_response_time: float
    errors: List[str]
    economic_context: Dict[str, Any]
    detailed_results: List[Dict[str, Any]]

class TestConfigurationManager:
    """Manages test configurations and execution"""
    
    def __init__(self, config_dir: str = "test_configs"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self.results_dir = Path("test_results")
        self.results_dir.mkdir(exist_ok=True)
        
        # Load existing configurations
        self.configurations: Dict[str, TestConfiguration] = {}
        self._load_configurations()
    
    def create_configuration(self, config: TestConfiguration) -> None:
        """Create and save a new test configuration"""
        self.configurations[config.name] = config
        self._save_configuration(config)
    
    def get_predefined_configurations(self) -> Dict[str, TestConfiguration]:
        """Get a set of predefined test configurations"""
        configs = {
            "basic_real_estate": TestConfiguration(
                name="basic_real_estate",
                description="Basic real estate extraction test",
                test_type="real_estate",
                websites=["https://www.zillow.com/san-francisco-ca/"],
                queries=[
                    "Find 3-bedroom houses under $800,000",
                    "Show me condos with parking",
                    "Find properties with a pool"
                ],
                max_iterations=3,
                validation_criteria={"min_success_rate": 70, "min_items_per_query": 2}
            ),
            
            "financial_rates": TestConfiguration(
                name="financial_rates",
                description="Financial rates extraction test",
                test_type="financial",
                websites=["https://www.bankrate.com/mortgages/mortgage-rates/"],
                queries=[
                    "What are current 30-year mortgage rates?",
                    "Find the best refinancing rates",
                    "Show me FHA loan rates"
                ],
                max_iterations=2,
                model_config={"temperature": 0.05, "max_tokens": 1500},  # More conservative for financial data
                validation_criteria={"min_success_rate": 85, "min_items_per_query": 1}
            ),
            
            "performance_stress": TestConfiguration(
                name="performance_stress",
                description="High-volume performance stress test",
                test_type="real_estate",
                websites=[
                    "https://www.zillow.com/san-francisco-ca/",
                    "https://www.realtor.com/realestateandhomes-search/San-Francisco_CA"
                ],
                queries=[
                    "Find all 2-bedroom apartments",
                    "Show me houses under $1M",
                    "Find condos with city views",
                    "Show luxury properties",
                    "Find properties near schools"
                ],
                max_iterations=5,
                max_steps_per_query=15,
                validation_criteria={"min_success_rate": 60, "min_items_per_query": 5}
            ),
            
            "reproducibility_test": TestConfiguration(
                name="reproducibility_test",
                description="Test for consistent reproducible results",
                test_type="real_estate",
                websites=["https://www.zillow.com/san-francisco-ca/"],
                queries=["Find 3-bedroom houses under $800,000"],
                max_iterations=5,  # Run same test multiple times
                model_config={"temperature": 0.0, "max_tokens": 1000},  # Deterministic
                validation_criteria={"min_success_rate": 90, "result_consistency": 0.95}
            )
        }
        
        # Save predefined configurations
        for config in configs.values():
            self.create_configuration(config)
        
        return configs
    
    async def run_test_suite(self, config_names: List[str] = None) -> Dict[str, TestResult]:
        """Run a suite of tests"""
        if config_names is None:
            config_names = list(self.configurations.keys())
        
        results = {}
        
        for config_name in config_names:
            if config_name not in self.configurations:
                print(f"⚠️  Configuration '{config_name}' not found, skipping")
                continue
            
            print(f"🧪 Running test: {config_name}")
            result = await self._execute_test(self.configurations[config_name])
            results[config_name] = result
            
            # Save individual result
            self._save_test_result(result)
        
        # Generate summary report
        self._generate_summary_report(results)
        
        return results
    
    async def _execute_test(self, config: TestConfiguration) -> TestResult:
        """Execute a single test configuration"""
        start_time = datetime.now()
        
        # Simulate test execution (replace with actual test logic)
        detailed_results = []
        errors = []
        total_items = 0
        successful_queries = 0
        response_times = []
        
        for iteration in range(config.max_iterations):
            for query_idx, query in enumerate(config.queries):
                try:
                    # Simulate query execution
                    query_start = datetime.now()
                    
                    # Simulate processing time
                    await asyncio.sleep(0.1)
                    
                    # Simulate results (replace with actual browseruse_gemini execution)
                    items_found = max(0, config.validation_criteria.get("min_items_per_query", 3) + 
                                    (iteration % 3 - 1))  # Simulate some variation
                    
                    query_end = datetime.now()
                    response_time = (query_end - query_start).total_seconds()
                    response_times.append(response_time)
                    
                    if items_found >= config.validation_criteria.get("min_items_per_query", 1):
                        successful_queries += 1
                        total_items += items_found
                    
                    detailed_results.append({
                        "iteration": iteration + 1,
                        "query_index": query_idx,
                        "query": query,
                        "items_found": items_found,
                        "response_time": response_time,
                        "success": items_found >= config.validation_criteria.get("min_items_per_query", 1)
                    })
                    
                except Exception as e:
                    errors.append(f"Query {query_idx} iteration {iteration + 1}: {str(e)}")
        
        end_time = datetime.now()
        
        total_queries = len(config.queries) * config.max_iterations
        success_rate = (successful_queries / total_queries * 100) if total_queries > 0 else 0
        avg_response_time = statistics.mean(response_times) if response_times else 0
        
        # Get economic context
        from .test_variables import EconomicControlVariables
        economic_context = EconomicControlVariables.get_current_economic_context()
        
        return TestResult(
            config_name=config.name,
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            total_queries=total_queries,
            successful_queries=successful_queries,
            success_rate=round(success_rate, 2),
            total_items_extracted=total_items,
            average_response_time=round(avg_response_time, 3),
            errors=errors,
            economic_context=economic_context,
            detailed_results=detailed_results
        )
    
    def analyze_results(self, results: Dict[str, TestResult]) -> Dict[str, Any]:
        """Analyze test results and generate insights"""
        analysis = {
            "summary": {
                "total_tests": len(results),
                "overall_success_rate": 0,
                "best_performing_test": None,
                "worst_performing_test": None,
                "average_response_time": 0
            },
            "performance_comparison": {},
            "trend_analysis": {},
            "recommendations": []
        }
        
        if not results:
            return analysis
        
        # Calculate overall metrics
        success_rates = [r.success_rate for r in results.values()]
        response_times = [r.average_response_time for r in results.values()]
        
        analysis["summary"]["overall_success_rate"] = round(statistics.mean(success_rates), 2)
        analysis["summary"]["average_response_time"] = round(statistics.mean(response_times), 3)
        
        # Find best and worst performing tests
        best_test = max(results.items(), key=lambda x: x[1].success_rate)
        worst_test = min(results.items(), key=lambda x: x[1].success_rate)
        
        analysis["summary"]["best_performing_test"] = {
            "name": best_test[0], 
            "success_rate": best_test[1].success_rate
        }
        analysis["summary"]["worst_performing_test"] = {
            "name": worst_test[0], 
            "success_rate": worst_test[1].success_rate
        }
        
        # Performance comparison
        for name, result in results.items():
            analysis["performance_comparison"][name] = {
                "success_rate": result.success_rate,
                "items_per_query": result.total_items_extracted / result.total_queries if result.total_queries > 0 else 0,
                "response_time": result.average_response_time,
                "error_count": len(result.errors)
            }
        
        # Generate recommendations
        if analysis["summary"]["overall_success_rate"] < 70:
            analysis["recommendations"].append("Overall success rate is low. Consider adjusting model parameters or browser settings.")
        
        if statistics.stdev(success_rates) > 20:
            analysis["recommendations"].append("High variance in success rates. Review test configurations for consistency.")
        
        if any(len(r.errors) > 0 for r in results.values()):
            analysis["recommendations"].append("Some tests have errors. Review error logs for debugging.")
        
        return analysis
    
    def _load_configurations(self) -> None:
        """Load configurations from disk"""
        for config_file in self.config_dir.glob("*.json"):
            try:
                with open(config_file, 'r') as f:
                    config_data = json.load(f)
                config = TestConfiguration(**config_data)
                self.configurations[config.name] = config
            except Exception as e:
                print(f"⚠️  Failed to load config {config_file}: {e}")
    
    def _save_configuration(self, config: TestConfiguration) -> None:
        """Save configuration to disk"""
        config_file = self.config_dir / f"{config.name}.json"
        with open(config_file, 'w') as f:
            json.dump(asdict(config), f, indent=2)
    
    def _save_test_result(self, result: TestResult) -> None:
        """Save test result to disk"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = self.results_dir / f"{result.config_name}_{timestamp}.json"
        with open(result_file, 'w') as f:
            json.dump(asdict(result), f, indent=2, default=str)
    
    def _generate_summary_report(self, results: Dict[str, TestResult]) -> None:
        """Generate a summary report of all test results"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.results_dir / f"test_suite_summary_{timestamp}.json"
        
        analysis = self.analyze_results(results)
        
        summary_data = {
            "generated_at": datetime.now().isoformat(),
            "test_results": {name: asdict(result) for name, result in results.items()},
            "analysis": analysis
        }
        
        with open(report_file, 'w') as f:
            json.dump(summary_data, f, indent=2, default=str)
        
        print(f"📊 Summary report saved to: {report_file}")

# Example usage
if __name__ == "__main__":
    async def demo():
        print("🔧 Test Configuration Manager Demo")
        print("=" * 50)
        
        # Create manager
        manager = TestConfigurationManager()
        
        # Create predefined configurations
        configs = manager.get_predefined_configurations()
        print(f"✅ Created {len(configs)} predefined test configurations")
        
        # Run a subset of tests
        test_names = ["basic_real_estate", "financial_rates"]
        print(f"\n🧪 Running tests: {test_names}")
        
        results = await manager.run_test_suite(test_names)
        
        # Analyze results
        analysis = manager.analyze_results(results)
        
        print(f"\n📊 Test Results Summary:")
        print(f"   Overall Success Rate: {analysis['summary']['overall_success_rate']}%")
        print(f"   Best Test: {analysis['summary']['best_performing_test']['name']} ({analysis['summary']['best_performing_test']['success_rate']}%)")
        print(f"   Average Response Time: {analysis['summary']['average_response_time']}s")
        
        print(f"\n💡 Recommendations:")
        for rec in analysis['recommendations']:
            print(f"   • {rec}")
    
    asyncio.run(demo()) 