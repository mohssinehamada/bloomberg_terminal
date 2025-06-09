"""
Example Integration: Using Test Variables with BrowserUse Gemini

This file demonstrates how to integrate the test_variables.py module
with your existing browseruse_gemini.py for controlled testing.
"""

from .test_variables import (
    ReproducibilityController,
    BrowserControlVariables, 
    TestWebsites,
    EconomicControlVariables,
    setup_test_environment
)
from browseruse_gemini import GeminiBrowserAgent
import asyncio
import json
from datetime import datetime

class ControlledBrowserAgent(GeminiBrowserAgent):
    """
    Enhanced GeminiBrowserAgent with controlled testing capabilities
    """
    
    def __init__(self, test_scenario: str = "standard", **kwargs):
        # Setup controlled test environment
        self.test_config = setup_test_environment(test_scenario)
        
        # Apply browser control variables
        self.browser_config = {
            'headless': BrowserControlVariables.HEADLESS_MODE,
            'viewport_width': BrowserControlVariables.VIEWPORT_WIDTH,
            'viewport_height': BrowserControlVariables.VIEWPORT_HEIGHT,
            'timeout': BrowserControlVariables.PAGE_LOAD_TIMEOUT,
            'user_agent': BrowserControlVariables.USER_AGENT
        }
        
        # Initialize parent with controlled temperature
        super().__init__(**kwargs)
        
        # Override model temperature for reproducibility
        if hasattr(self, 'llm'):
            self.llm.temperature = ReproducibilityController.MODEL_TEMPERATURE
    
    async def run_controlled_test(self, test_type: str = "real_estate", 
                                max_iterations: int = 3) -> Dict[str, Any]:
        """
        Run a controlled test with predefined parameters
        """
        print(f"🧪 Running controlled test: {test_type}")
        
        # Get test websites based on type
        if test_type == "real_estate":
            websites = TestWebsites.REAL_ESTATE_SITES
            test_queries = [
                "Find 3-bedroom houses under $800,000",
                "Show me condos with parking",
                "Find properties with a pool"
            ]
        elif test_type == "financial":
            websites = TestWebsites.FINANCIAL_SITES
            test_queries = [
                "What are current 30-year mortgage rates?",
                "Find the best refinancing rates",
                "Show me FHA loan rates"
            ]
        else:
            websites = {"test_site": "https://example.com"}
            test_queries = ["Extract main content"]
        
        results = {
            "test_type": test_type,
            "start_time": datetime.now().isoformat(),
            "test_config": self.test_config,
            "economic_context": EconomicControlVariables.get_current_economic_context(),
            "iterations": [],
            "summary": {}
        }
        
        # Run multiple iterations for statistical significance
        for i in range(max_iterations):
            print(f"📊 Iteration {i+1}/{max_iterations}")
            
            iteration_results = {
                "iteration": i+1,
                "timestamp": datetime.now().isoformat(),
                "queries": []
            }
            
            # Test each query
            for query_idx, query in enumerate(test_queries[:2]):  # Limit for demo
                print(f"🔍 Testing query: {query}")
                
                try:
                    # Use first website for testing
                    website_url = list(websites.values())[0]
                    test_websites = {"test_site": website_url}
                    
                    # Execute the task with controlled parameters
                    query_result = await self.execute_task(
                        websites=test_websites,
                        max_steps=10  # Controlled step limit
                    )
                    
                    query_result.update({
                        "query": query,
                        "query_index": query_idx,
                        "controlled_parameters": {
                            "max_steps": 10,
                            "temperature": ReproducibilityController.MODEL_TEMPERATURE,
                            "timeout": BrowserControlVariables.DEFAULT_TIMEOUT
                        }
                    })
                    
                    iteration_results["queries"].append(query_result)
                    
                except Exception as e:
                    print(f"❌ Error in query {query_idx}: {str(e)}")
                    iteration_results["queries"].append({
                        "query": query,
                        "query_index": query_idx,
                        "error": str(e),
                        "success": False
                    })
            
            results["iterations"].append(iteration_results)
        
        # Calculate summary statistics
        results["summary"] = self._calculate_test_summary(results)
        results["end_time"] = datetime.now().isoformat()
        
        # Save results for analysis
        self._save_test_results(results, test_type)
        
        return results
    
    def _calculate_test_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate summary statistics from test results"""
        total_queries = 0
        successful_queries = 0
        total_items_extracted = 0
        
        for iteration in results["iterations"]:
            for query_result in iteration["queries"]:
                total_queries += 1
                if query_result.get("success", False):
                    successful_queries += 1
                    # Count extracted items
                    extracted_data = query_result.get("extracted_data", {})
                    if isinstance(extracted_data, dict):
                        for site_data in extracted_data.values():
                            if isinstance(site_data, list):
                                total_items_extracted += len(site_data)
        
        success_rate = (successful_queries / total_queries * 100) if total_queries > 0 else 0
        avg_items_per_query = (total_items_extracted / successful_queries) if successful_queries > 0 else 0
        
        return {
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "success_rate_percent": round(success_rate, 2),
            "total_items_extracted": total_items_extracted,
            "avg_items_per_successful_query": round(avg_items_per_query, 2),
            "controlled_variables_applied": True,
            "reproducibility_seed": ReproducibilityController.RANDOM_SEED
        }
    
    def _save_test_results(self, results: Dict[str, Any], test_type: str):
        """Save test results to file for analysis"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"test_results_{test_type}_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"💾 Test results saved to: {filename}")
        except Exception as e:
            print(f"⚠️ Failed to save test results: {e}")

# Example usage functions
async def run_reproducibility_test():
    """Example: Run the same test multiple times to verify reproducibility"""
    print("🔬 Running Reproducibility Test")
    print("=" * 50)
    
    agent = ControlledBrowserAgent(test_scenario="reproducibility_test")
    
    # Run the same test twice with the same seed
    results1 = await agent.run_controlled_test("real_estate", max_iterations=1)
    
    # Reset with same seed
    ReproducibilityController.set_random_seeds(42)
    results2 = await agent.run_controlled_test("real_estate", max_iterations=1)
    
    # Compare results
    print("\n📊 Reproducibility Check:")
    print(f"Test 1 Success Rate: {results1['summary']['success_rate_percent']}%")
    print(f"Test 2 Success Rate: {results2['summary']['success_rate_percent']}%")
    
    return results1, results2

async def run_comparative_analysis():
    """Example: Compare performance across different economic contexts"""
    print("📈 Running Comparative Analysis")
    print("=" * 50)
    
    # Test with different economic contexts
    contexts = [
        {"unemployment_rate": 3.5, "effr": 5.0},  # Good economy
        {"unemployment_rate": 6.0, "effr": 2.0},  # Recession scenario
    ]
    
    results = []
    
    for i, context in enumerate(contexts):
        print(f"\n🏛️ Testing Economic Context {i+1}: {context}")
        
        # Update economic data
        EconomicControlVariables.MOCK_ECONOMIC_DATA.update(context)
        
        agent = ControlledBrowserAgent(test_scenario=f"economic_test_{i+1}")
        result = await agent.run_controlled_test("financial", max_iterations=1)
        result["economic_context_test"] = context
        results.append(result)
    
    return results

if __name__ == "__main__":
    print("🧪 Controlled Browser Agent Testing")
    print("=" * 50)
    
    async def main():
        # Example 1: Basic controlled test
        agent = ControlledBrowserAgent()
        results = await agent.run_controlled_test("real_estate", max_iterations=2)
        
        print("\n📋 Test Summary:")
        print(f"Success Rate: {results['summary']['success_rate_percent']}%")
        print(f"Total Items Extracted: {results['summary']['total_items_extracted']}")
        print(f"Average Items per Query: {results['summary']['avg_items_per_successful_query']}")
        
        # Example 2: Reproducibility test
        # await run_reproducibility_test()
        
        # Example 3: Comparative analysis
        # await run_comparative_analysis()
    
    # Run the examples
    asyncio.run(main()) 