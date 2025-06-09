#!/usr/bin/env python3
"""
Full Economic Integration Demo

Shows how browseruse_gemini automatically includes real-time economic data
"""

from browseruse_gemini import GeminiBrowserAgent
import json

def demo_full_economic_integration():
    print('🚀 browseruse_gemini.py with REAL-TIME Economic Data')
    print('=' * 60)
    
    # Create agent with controlled testing enabled
    agent = GeminiBrowserAgent(
        gemini_api_key='demo_key',  # Would use real key for actual tasks
        enable_testing=True,
        test_scenario='full_economic_demo'
    )
    
    print('\n📊 REAL-TIME ECONOMIC DATA (from Federal Reserve):')
    print('-' * 50)
    
    # Get economic context - this now pulls real-time data!
    context = agent.get_economic_context()
    indicators = context['economic_indicators']
    
    print(f'📡 Data Source: {indicators["data_source"]}')
    print(f'📅 Last Updated: {indicators["last_updated"][:19]}')  # Just date/time
    print(f'🏛️ Unemployment Rate: {indicators["unemployment_rate"]}%')
    print(f'💰 Consumer Price Index: {indicators["cpi_all_items"]}')
    print(f'📈 Federal Funds Rate: {indicators["federal_funds_rate"]}%')
    print(f'🏭 GDP: ${indicators["gdp"]} billion')
    print(f'😊 Consumer Sentiment: {indicators["consumer_sentiment"]}')
    print(f'🎄 Holiday Days: {indicators["holiday_days"]}')
    
    print(f'\n🔍 Data Quality: {context["data_quality"]}')
    print(f'🌎 Region: {context["region"]}')
    print(f'💵 Currency: {context["currency"]}')
    
    # Simulate some web scraping performance
    print('\n🎭 Simulating Web Agent Performance:')
    print('-' * 40)
    
    # Track some mock query performance
    agent.track_query_performance(2.5, True, 8, None)
    agent.track_query_performance(1.8, True, 12, None)
    agent.track_query_performance(3.2, False, 0, "Timeout error")
    agent.track_query_performance(2.1, True, 6, None)
    
    # Print comprehensive performance summary
    agent.print_performance_summary()
    
    # Show that economic context is included in summary
    summary = agent.get_performance_summary()
    if 'economic_context' in summary:
        print('\n🏛️ ECONOMIC CONTEXT INCLUDED IN SUMMARY!')
        print('   Your performance data now includes:')
        print('   • Real-time unemployment rate for market context')
        print('   • Current CPI for price normalization')
        print('   • Federal funds rate for financial analysis')
        print('   • Consumer sentiment for demand analysis')
        print('   • Timestamp for data correlation')
    
    print(f'\n💡 KEY INSIGHT:')
    print(f'   When you scrape data on {indicators["last_updated"][:10]},')
    print(f'   you know the economic conditions were:')
    print(f'   • Unemployment: {indicators["unemployment_rate"]}% ({"high" if indicators["unemployment_rate"] > 5 else "normal" if indicators["unemployment_rate"] > 3 else "low"})')
    print(f'   • Consumer Confidence: {indicators["consumer_sentiment"]} ({"high" if indicators["consumer_sentiment"] > 80 else "normal" if indicators["consumer_sentiment"] > 60 else "low"})')
    
    return True

if __name__ == "__main__":
    demo_full_economic_integration() 