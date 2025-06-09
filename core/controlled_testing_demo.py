#!/usr/bin/env python3
"""
Controlled Testing Demo for Web Agent

This script demonstrates the controlled testing capabilities integrated
into the browseruse_gemini module with performance monitoring.
"""

import asyncio
import os
import json
from datetime import datetime
from browseruse_gemini import GeminiBrowserAgent
from test_versiables import TestWebsites, ReproducibilityController

async def demo_controlled_testing():
    """Demonstrate controlled testing with performance monitoring"""
    print("🧪 Web Agent Controlled Testing Demo")
    print("=" * 60)
    
    # Check if API key is available
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("⚠️ GEMINI_API_KEY not found in environment")
        print("Please set your Gemini API key to run this demo")
        return
    
    # Test 1: Agent with controlled testing enabled
    print("\n1️⃣ Creating Agent with Controlled Testing ENABLED")
    controlled_agent = GeminiBrowserAgent(
        gemini_api_key=api_key,
        enable_testing=True,
        test_scenario="demo_controlled_test"
    )
    
    # Test 2: Agent without controlled testing
    print("\n2️⃣ Creating Agent with Controlled Testing DISABLED")
    regular_agent = GeminiBrowserAgent(
        gemini_api_key=api_key,
        enable_testing=False
    )
    
    # Test websites from our controlled test variables
    test_websites = {
        "zillow_demo": "https://www.zillow.com/san-francisco-ca/"
    }
    
    print(f"\n🏠 Test Website: {list(test_websites.values())[0]}")
    
    # Run controlled test
    print("\n3️⃣ Running CONTROLLED test...")
    print("🎯 Using reproducible parameters:")
    print(f"   Random Seed: {ReproducibilityController.RANDOM_SEED}")
    print(f"   Model Temperature: {ReproducibilityController.MODEL_TEMPERATURE}")
    
    try:
        controlled_result = await controlled_agent.execute_task(
            websites=test_websites,
            max_steps=5  # Limited steps for demo
        )
        print("✅ Controlled test completed")
        
        # Show performance summary
        controlled_agent.print_performance_summary()
        
    except Exception as e:
        print(f"❌ Controlled test failed: {e}")
        controlled_result = {"error": str(e)}
    
    # Run regular test for comparison
    print("\n4️⃣ Running REGULAR test for comparison...")
    
    try:
        regular_result = await regular_agent.execute_task(
            websites=test_websites,
            max_steps=5  # Limited steps for demo
        )
        print("✅ Regular test completed")
        
        # Show performance summary
        regular_agent.print_performance_summary()
        
    except Exception as e:
        print(f"❌ Regular test failed: {e}")
        regular_result = {"error": str(e)}
    
    # Compare results
    print("\n5️⃣ Comparing Results")
    print("=" * 40)
    
    controlled_summary = controlled_agent.get_performance_summary()
    regular_summary = regular_agent.get_performance_summary()
    
    print("🧪 CONTROLLED vs 🆓 REGULAR:")
    print(f"Success Rate: {controlled_summary['success_rate_percent']}% vs {regular_summary['success_rate_percent']}%")
    print(f"Items Extracted: {controlled_summary['total_items_extracted']} vs {regular_summary['total_items_extracted']}")
    print(f"Response Time: {controlled_summary['average_response_time_seconds']}s vs {regular_summary['average_response_time_seconds']}s")
    print(f"Errors: {controlled_summary['error_count']} vs {regular_summary['error_count']}")
    
    # Show economic context if available
    if controlled_summary.get('economic_context'):
        print("\n📊 Economic Context (Controlled Test):")
        economic_data = controlled_summary['economic_context']['economic_indicators']
        print(f"   Unemployment Rate: {economic_data['unemployment_rate']}%")
        print(f"   CPI: {economic_data['cpi_all_items']}")
        print(f"   Federal Funds Rate: {economic_data['effr']}%")
    
    # Save detailed results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"controlled_testing_results_{timestamp}.json"
    
    detailed_results = {
        "timestamp": datetime.now().isoformat(),
        "controlled_test": {
            "performance_summary": controlled_summary,
            "result_preview": str(controlled_result)[:500] + "..." if len(str(controlled_result)) > 500 else str(controlled_result)
        },
        "regular_test": {
            "performance_summary": regular_summary,
            "result_preview": str(regular_result)[:500] + "..." if len(str(regular_result)) > 500 else str(regular_result)
        },
        "comparison": {
            "controlled_testing_advantage": {
                "reproducible": True,
                "seed_controlled": controlled_summary.get('controlled_testing_enabled', False),
                "economic_context_available": 'economic_context' in controlled_summary
            }
        }
    }
    
    with open(results_file, 'w') as f:
        json.dump(detailed_results, f, indent=2, default=str)
    
    print(f"\n💾 Detailed results saved to: {results_file}")

async def demo_reproducibility_test():
    """Demonstrate reproducibility by running the same test multiple times"""
    print("\n🔬 Reproducibility Test")
    print("=" * 40)
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("⚠️ GEMINI_API_KEY not found - skipping reproducibility test")
        return
    
    results = []
    test_websites = {"test_site": TestWebsites.REAL_ESTATE_SITES["zillow"]}
    
    # Run the same test 3 times with controlled parameters
    for i in range(3):
        print(f"\n🧪 Reproducibility Test Run {i+1}/3")
        
        # Create new agent with same controlled parameters
        agent = GeminiBrowserAgent(
            gemini_api_key=api_key,
            enable_testing=True,
            test_scenario=f"reproducibility_test_{i+1}"
        )
        
        try:
            result = await agent.execute_task(test_websites, max_steps=3)
            summary = agent.get_performance_summary()
            results.append(summary)
            print(f"   Success Rate: {summary['success_rate_percent']}%")
            print(f"   Items Extracted: {summary['total_items_extracted']}")
            
        except Exception as e:
            print(f"   ❌ Test {i+1} failed: {e}")
            results.append({"error": str(e)})
    
    # Analyze reproducibility
    print(f"\n📊 Reproducibility Analysis:")
    success_rates = [r.get('success_rate_percent', 0) for r in results if 'error' not in r]
    items_extracted = [r.get('total_items_extracted', 0) for r in results if 'error' not in r]
    
    if success_rates:
        avg_success_rate = sum(success_rates) / len(success_rates)
        avg_items = sum(items_extracted) / len(items_extracted)
        
        print(f"   Average Success Rate: {avg_success_rate:.1f}%")
        print(f"   Average Items Extracted: {avg_items:.1f}")
        print(f"   Success Rate Variance: {max(success_rates) - min(success_rates):.1f}%")
        
        if max(success_rates) - min(success_rates) <= 10:
            print("   ✅ Good reproducibility (variance ≤ 10%)")
        else:
            print("   ⚠️ High variance - check control variables")
    else:
        print("   ❌ All tests failed - cannot assess reproducibility")

async def demo_multiple_test_scenarios():
    """Demo different test scenarios with controlled variables"""
    print("\n🎭 Multiple Test Scenarios Demo")
    print("=" * 40)
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("⚠️ GEMINI_API_KEY not found - skipping scenario tests")
        return
    
    scenarios = [
        {
            "name": "conservative_test",
            "description": "Conservative model settings for financial data",
            "websites": {"bankrate": TestWebsites.FINANCIAL_SITES["bankrate"]}
        },
        {
            "name": "standard_test", 
            "description": "Standard settings for real estate",
            "websites": {"zillow": TestWebsites.REAL_ESTATE_SITES["zillow"]}
        }
    ]
    
    scenario_results = {}
    
    for scenario in scenarios:
        print(f"\n🎬 Scenario: {scenario['name']}")
        print(f"📝 Description: {scenario['description']}")
        
        agent = GeminiBrowserAgent(
            gemini_api_key=api_key,
            enable_testing=True,
            test_scenario=scenario['name']
        )
        
        try:
            result = await agent.execute_task(scenario['websites'], max_steps=3)
            summary = agent.get_performance_summary()
            scenario_results[scenario['name']] = summary
            
            print(f"   Success Rate: {summary['success_rate_percent']}%")
            print(f"   Items: {summary['total_items_extracted']}")
            print(f"   Time: {summary['average_response_time_seconds']}s")
            
        except Exception as e:
            print(f"   ❌ Scenario failed: {e}")
            scenario_results[scenario['name']] = {"error": str(e)}
    
    # Compare scenarios
    print(f"\n📈 Scenario Comparison:")
    for name, result in scenario_results.items():
        if 'error' not in result:
            print(f"   {name}: {result['success_rate_percent']}% success, {result['total_items_extracted']} items")

async def main():
    """Run all demo tests"""
    print("🚀 Starting Web Agent Controlled Testing Demos")
    print("=" * 60)
    
    # Demo 1: Basic controlled testing
    await demo_controlled_testing()
    
    # Demo 2: Reproducibility test
    await demo_reproducibility_test()
    
    # Demo 3: Multiple scenarios
    await demo_multiple_test_scenarios()
    
    print("\n🎉 All demos completed!")
    print("\n💡 Key Takeaways:")
    print("   • Controlled testing provides reproducible results")
    print("   • Performance monitoring tracks success rates and response times")
    print("   • Economic context enables data normalization")
    print("   • Multiple scenarios can be tested with consistent parameters")
    print("\n📊 Check the generated JSON files for detailed analysis")

if __name__ == "__main__":
    asyncio.run(main()) 