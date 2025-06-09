#!/usr/bin/env python3
"""
Demo: Test Variables Integration with Web Agent

This script demonstrates how to use the test_variables.py module
for controlled testing of your web agent.
"""

import asyncio
import os
from test_versiables.test_variables import (
    setup_test_environment,
    ReproducibilityController,
    TestWebsites,
    EconomicControlVariables
)

def demo_test_variables():
    """
    Demonstrate the test variables functionality
    """
    print("🧪 Web Agent Test Variables Demo")
    print("=" * 50)
    
    # 1. Setup controlled test environment
    print("\n1️⃣ Setting up controlled test environment...")
    test_config = setup_test_environment("demo_scenario", seed=42)
    
    # 2. Show reproducibility controls
    print("\n2️⃣ Reproducibility Controls:")
    print(f"   🎯 Random Seed: {ReproducibilityController.RANDOM_SEED}")
    print(f"   🌡️  Model Temperature: {ReproducibilityController.MODEL_TEMPERATURE}")
    print(f"   ⏰ Default Timeout: {ReproducibilityController.DEFAULT_TIMEOUT}s")
    
    # 3. Show browser control variables
    print("\n3️⃣ Browser Control Variables:")
    from test_versiables.test_variables import BrowserControlVariables
    print(f"   🖥️  Viewport: {BrowserControlVariables.VIEWPORT_WIDTH}x{BrowserControlVariables.VIEWPORT_HEIGHT}")
    print(f"   👤 User Agent: {BrowserControlVariables.USER_AGENT[:50]}...")
    print(f"   ⏱️  Page Load Timeout: {BrowserControlVariables.PAGE_LOAD_TIMEOUT}ms")
    
    # 4. Show test websites
    print("\n4️⃣ Test Websites Available:")
    print(f"   🏠 Real Estate Sites: {len(TestWebsites.REAL_ESTATE_SITES)} sites")
    for name, url in TestWebsites.REAL_ESTATE_SITES.items():
        print(f"      • {name}: {url}")
    
    print(f"   💰 Financial Sites: {len(TestWebsites.FINANCIAL_SITES)} sites")
    for name, url in TestWebsites.FINANCIAL_SITES.items():
        print(f"      • {name}: {url}")
    
    # 5. Show economic context
    print("\n5️⃣ Economic Control Variables:")
    economic_context = EconomicControlVariables.get_current_economic_context()
    for key, value in economic_context['economic_indicators'].items():
        print(f"   📊 {key}: {value}")
    
    return test_config

async def demo_with_browseruse_agent():
    """
    Demonstrate integration with browseruse_gemini (if available)
    """
    print("\n🤖 Testing Integration with BrowserUse Agent")
    print("=" * 50)
    
    try:
        # Try to import the browseruse_gemini module
        from browseruse_gemini import GeminiBrowserAgent
        
        print("✅ BrowserUse Gemini module found!")
        
        # Setup controlled environment
        setup_test_environment("integration_demo")
        
        # Create agent (you would need API key for real testing)
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            print("⚠️  GEMINI_API_KEY not found in environment")
            print("   Set your API key to run full integration test")
            return
        
        print("🚀 Creating controlled browser agent...")
        
        # This is how you would create a controlled agent
        agent = GeminiBrowserAgent(gemini_api_key=api_key)
        
        # Apply control variables
        ReproducibilityController.set_random_seeds(42)
        
        print("✅ Agent created with controlled parameters")
        print("   Ready for controlled testing!")
        
        # Example controlled test (commented out to avoid actual execution)
        """
        test_websites = {"zillow": TestWebsites.REAL_ESTATE_SITES["zillow"]}
        result = await agent.execute_task(test_websites, max_steps=5)
        print(f"Test completed: {result.get('success', False)}")
        """
        
    except ImportError as e:
        print("⚠️  BrowserUse Gemini module not available")
        print(f"   Error: {e}")
        print("   Test variables can still be used independently")

def demo_data_preprocessing():
    """
    Demonstrate data preprocessing with control variables
    """
    print("\n📊 Data Preprocessing with Control Variables")
    print("=" * 50)
    
    # Simulate some extracted data
    sample_data = {
        "listings": [
            {"price": 750000, "bedrooms": 3, "location": "San Francisco"},
            {"price": 850000, "bedrooms": 2, "location": "Palo Alto"}
        ],
        "timestamp": "2024-01-15T10:30:00"
    }
    
    print("📋 Original Data:")
    print(f"   {len(sample_data['listings'])} listings found")
    
    # Add economic context for normalization
    economic_context = EconomicControlVariables.get_current_economic_context()
    
    # Simulate price normalization based on economic indicators
    cpi = economic_context['economic_indicators']['cpi_all_items']
    unemployment = economic_context['economic_indicators']['unemployment_rate']
    
    print("\n🏛️ Economic Context Applied:")
    print(f"   CPI: {cpi} (price normalization factor)")
    print(f"   Unemployment Rate: {unemployment}% (market condition indicator)")
    
    # Normalize prices (example calculation)
    normalized_data = sample_data.copy()
    for listing in normalized_data['listings']:
        # Simple normalization example (not real economic calculation)
        original_price = listing['price']
        normalized_price = original_price * (307.5 / cpi)  # Normalize to baseline CPI
        listing['normalized_price'] = int(normalized_price)
        listing['market_adjustment'] = f"{((normalized_price/original_price - 1) * 100):.1f}%"
    
    print("\n📈 Normalized Data:")
    for listing in normalized_data['listings']:
        print(f"   ${listing['price']:,} → ${listing['normalized_price']:,} ({listing['market_adjustment']})")
    
    return normalized_data

def create_test_report():
    """
    Create a test report showing all controlled variables
    """
    print("\n📄 Test Environment Report")
    print("=" * 50)
    
    from datetime import datetime
    import json
    
    report = {
        "test_report": {
            "generated_at": datetime.now().isoformat(),
            "environment": "demo",
            "reproducibility_controls": {
                "random_seed": ReproducibilityController.RANDOM_SEED,
                "model_temperature": ReproducibilityController.MODEL_TEMPERATURE,
                "timeouts": {
                    "default": ReproducibilityController.DEFAULT_TIMEOUT,
                    "long": ReproducibilityController.LONG_TIMEOUT,
                    "short": ReproducibilityController.SHORT_TIMEOUT
                }
            },
            "browser_controls": {
                "headless": BrowserControlVariables.HEADLESS_MODE,
                "viewport": f"{BrowserControlVariables.VIEWPORT_WIDTH}x{BrowserControlVariables.VIEWPORT_HEIGHT}",
                "max_retries": BrowserControlVariables.MAX_RETRIES
            },
            "economic_context": EconomicControlVariables.get_current_economic_context(),
            "test_sites_available": {
                "real_estate": len(TestWebsites.REAL_ESTATE_SITES),
                "financial": len(TestWebsites.FINANCIAL_SITES)
            }
        }
    }
    
    # Save report
    filename = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"📁 Test report saved to: {filename}")
    return report

async def main():
    """
    Run all demos
    """
    print("🎯 Starting Web Agent Test Variables Demo")
    
    # Demo 1: Basic test variables
    demo_test_variables()
    
    # Demo 2: Integration demo
    await demo_with_browseruse_agent()
    
    # Demo 3: Data preprocessing
    demo_data_preprocessing()
    
    # Demo 4: Create test report
    create_test_report()
    
    print("\n✅ Demo completed!")
    print("💡 You can now use these test variables in your web agent for:")
    print("   • Reproducible experiments")
    print("   • Controlled A/B testing")
    print("   • Performance benchmarking")
    print("   • Economic context normalization")

if __name__ == "__main__":
    asyncio.run(main()) 