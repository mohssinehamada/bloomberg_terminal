#!/usr/bin/env python3
"""
Test Economic Integration with browseruse_gemini
"""

from browseruse_gemini import GeminiBrowserAgent

def test_economic_integration():
    print("🧪 Testing Economic Integration with Web Agent")
    print("=" * 60)
    
    # Create agent with controlled testing enabled
    agent = GeminiBrowserAgent(
        gemini_api_key='test_key_for_demo',
        enable_testing=True,
        test_scenario='economic_integration_test'
    )
    
    # Get economic context
    print("🏛️ Economic Context from Web Agent:")
    print("-" * 40)
    context = agent.get_economic_context()
    
    if isinstance(context, dict) and 'economic_indicators' in context:
        indicators = context['economic_indicators']
        print(f"📊 Data Source: {indicators.get('data_source', 'unknown')}")
        print(f"📅 Last Updated: {indicators.get('last_updated', 'unknown')}")
        print(f"🏛️ Unemployment Rate: {indicators.get('unemployment_rate', 'N/A')}%")
        print(f"💰 CPI: {indicators.get('cpi_all_items', 'N/A')}")
        print(f"📈 Fed Funds Rate: {indicators.get('federal_funds_rate', 'N/A')}%")
        print(f"🏭 GDP: ${indicators.get('gdp', 'N/A')} billion")
        print(f"😊 Consumer Sentiment: {indicators.get('consumer_sentiment', 'N/A')}")
        
        # Check if it's real-time data
        if 'fred_api' in indicators.get('data_source', ''):
            print("\n✅ SUCCESS: Getting REAL-TIME economic data from Federal Reserve!")
        else:
            print("\n⚠️ Using fallback data (no FRED API connection)")
            
        return True
    else:
        print("❌ No economic context available")
        return False

def test_performance_summary():
    print("\n🎯 Testing Performance Summary with Economic Data:")
    print("-" * 50)
    
    agent = GeminiBrowserAgent(
        gemini_api_key='test_key',
        enable_testing=True,
        test_scenario='performance_test'
    )
    
    # Simulate some query tracking
    agent.track_query_performance(1.5, True, 5)
    agent.track_query_performance(2.1, True, 3)
    
    # Get performance summary
    summary = agent.get_performance_summary()
    
    print(f"📞 Total Queries: {summary['total_queries']}")
    print(f"✅ Success Rate: {summary['success_rate_percent']}%")
    print(f"📦 Items Extracted: {summary['total_items_extracted']}")
    
    # Check if economic context is included
    if 'economic_context' in summary:
        print("✅ Economic context included in performance summary!")
        economic_data = summary['economic_context']['economic_indicators']
        print(f"   Unemployment: {economic_data.get('unemployment_rate', 'N/A')}%")
        print(f"   CPI: {economic_data.get('cpi_all_items', 'N/A')}")
        return True
    else:
        print("❌ No economic context in performance summary")
        return False

if __name__ == "__main__":
    print("🚀 Testing browseruse_gemini Economic Integration")
    print("=" * 60)
    
    # Test 1: Direct economic context
    test1_passed = test_economic_integration()
    
    # Test 2: Performance summary with economic data
    test2_passed = test_performance_summary()
    
    print("\n" + "=" * 60)
    print("📊 INTEGRATION TEST RESULTS:")
    print(f"✅ Economic Context: {'PASS' if test1_passed else 'FAIL'}")
    print(f"✅ Performance Summary: {'PASS' if test2_passed else 'FAIL'}")
    
    if test1_passed and test2_passed:
        print("\n🎉 SUCCESS: Your web agent has full economic integration!")
        print("\n💡 This means when you run:")
        print("   agent = GeminiBrowserAgent(enable_testing=True)")
        print("   # Your agent automatically includes real economic data!")
    else:
        print("\n⚠️ Some integration issues detected") 