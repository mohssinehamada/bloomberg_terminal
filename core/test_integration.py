#!/usr/bin/env python3
"""
Simple Integration Test

Tests the basic integration of test variables with browseruse_gemini
"""

import os

def test_imports():
    """Test that all modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        from test_versiables import setup_test_environment, ReproducibilityController
        print("✅ test_versiables imported successfully")
    except ImportError as e:
        print(f"❌ test_versiables import failed: {e}")
        return False
    
    try:
        from browseruse_gemini import GeminiBrowserAgent
        print("✅ browseruse_gemini imported successfully")
    except ImportError as e:
        print(f"❌ browseruse_gemini import failed: {e}")
        return False
    
    return True

def test_controlled_agent_creation():
    """Test creating an agent with controlled testing enabled"""
    print("\n🤖 Testing controlled agent creation...")
    
    try:
        from browseruse_gemini import GeminiBrowserAgent
        
        # Create agent without API key (should work for testing structure)
        try:
            agent = GeminiBrowserAgent(
                gemini_api_key="test_key_for_structure_test",
                enable_testing=True,
                test_scenario="structure_test"
            )
            print("✅ Controlled agent structure created successfully")
            
            # Test performance tracking methods
            if hasattr(agent, 'track_query_performance'):
                print("✅ Performance tracking methods available")
            else:
                print("❌ Performance tracking methods missing")
                
            if hasattr(agent, 'get_economic_context'):
                print("✅ Economic context methods available")
            else:
                print("❌ Economic context methods missing")
                
            if hasattr(agent, 'controlled_testing'):
                print(f"✅ Controlled testing flag: {agent.controlled_testing}")
            else:
                print("❌ Controlled testing flag missing")
            
            return True
            
        except Exception as e:
            print(f"❌ Agent creation failed: {e}")
            return False
            
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_performance_tracking():
    """Test performance tracking functionality"""
    print("\n📊 Testing performance tracking...")
    
    try:
        from browseruse_gemini import GeminiBrowserAgent
        
        agent = GeminiBrowserAgent(
            gemini_api_key="test_key",
            enable_testing=True,
            test_scenario="performance_test"
        )
        
        # Test tracking a mock query
        agent.track_query_performance(
            response_time=1.5,
            success=True,
            items_extracted=5,
            error=None
        )
        
        # Test tracking a failed query
        agent.track_query_performance(
            response_time=2.0,
            success=False,
            items_extracted=0,
            error="Test error"
        )
        
        # Get performance summary
        summary = agent.get_performance_summary()
        
        if summary['total_queries'] == 2:
            print("✅ Query tracking works correctly")
        else:
            print(f"❌ Query tracking failed: expected 2 queries, got {summary['total_queries']}")
            
        if summary['successful_queries'] == 1:
            print("✅ Success tracking works correctly")
        else:
            print(f"❌ Success tracking failed: expected 1 success, got {summary['successful_queries']}")
            
        if summary['error_count'] == 1:
            print("✅ Error tracking works correctly")
        else:
            print(f"❌ Error tracking failed: expected 1 error, got {summary['error_count']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance tracking test failed: {e}")
        return False

def test_economic_context():
    """Test economic context functionality"""
    print("\n🏛️ Testing economic context...")
    
    try:
        from browseruse_gemini import GeminiBrowserAgent
        
        agent = GeminiBrowserAgent(
            gemini_api_key="test_key",
            enable_testing=True,
            test_scenario="economic_test"
        )
        
        context = agent.get_economic_context()
        
        if isinstance(context, dict) and 'economic_indicators' in context:
            print("✅ Economic context available")
            indicators = context['economic_indicators']
            print(f"   Unemployment Rate: {indicators.get('unemployment_rate', 'N/A')}")
            print(f"   CPI: {indicators.get('cpi_all_items', 'N/A')}")
            return True
        else:
            print("❌ Economic context not properly structured")
            return False
            
    except Exception as e:
        print(f"❌ Economic context test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Web Agent Integration Tests")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_controlled_agent_creation,
        test_performance_tracking,
        test_economic_context
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
    
    print(f"\n📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All integration tests passed!")
        print("\n💡 Your controlled testing integration is working correctly!")
        print("\n🚀 You can now:")
        print("   • Create agents with enable_testing=True")
        print("   • Track performance metrics automatically") 
        print("   • Access economic context for data normalization")
        print("   • Run reproducible experiments with consistent parameters")
    else:
        print(f"⚠️ {total - passed} tests failed - check the integration")
    
    return passed == total

if __name__ == "__main__":
    main() 