#!/usr/bin/env python3
"""
Simple Test Variables Usage Example

This shows how to integrate test variables with your browseruse_gemini.py
"""

import os
from test_versiables.test_variables import (
    setup_test_environment,
    ReproducibilityController,
    BrowserControlVariables,
    TestWebsites,
    EconomicControlVariables
)

def demonstrate_controlled_testing():
    """
    Simple demonstration of controlled testing setup
    """
    print("🧪 Setting up Controlled Testing Environment")
    print("=" * 50)
    
    # 1. Setup test environment with reproducibility
    test_config = setup_test_environment("simple_demo", seed=42)
    
    # 2. Show what control variables are available
    print("\n📊 Available Control Variables:")
    print(f"🎯 Random Seed: {ReproducibilityController.RANDOM_SEED}")
    print(f"🌡️  Model Temperature: {ReproducibilityController.MODEL_TEMPERATURE}")
    print(f"🖥️  Viewport: {BrowserControlVariables.VIEWPORT_WIDTH}x{BrowserControlVariables.VIEWPORT_HEIGHT}")
    
    # 3. Show test websites
    print(f"\n🏠 Real Estate Test Sites: {len(TestWebsites.REAL_ESTATE_SITES)}")
    for name, url in TestWebsites.REAL_ESTATE_SITES.items():
        print(f"   • {name}: {url}")
    
    # 4. Show economic context
    economic_context = EconomicControlVariables.get_current_economic_context()
    print(f"\n💰 Economic Context:")
    print(f"   Unemployment Rate: {economic_context['economic_indicators']['unemployment_rate']}%")
    print(f"   CPI: {economic_context['economic_indicators']['cpi_all_items']}")
    
    return test_config

def show_browseruse_integration():
    """
    Show how to integrate with browseruse_gemini.py
    """
    print("\n🤖 Integration with BrowserUse Gemini")
    print("=" * 50)
    
    print("To integrate with your browseruse_gemini.py, add this code:")
    print("""
# At the top of browseruse_gemini.py, add:
from test_versiables.test_variables import (
    ReproducibilityController,
    BrowserControlVariables,
    setup_test_environment
)

# In your GeminiBrowserAgent.__init__ method, add:
def __init__(self, gemini_api_key=None, enable_testing=False, **kwargs):
    # ... existing code ...
    
    if enable_testing:
        # Setup controlled environment
        setup_test_environment("production_test")
        
        # Set reproducible parameters
        ReproducibilityController.set_random_seeds()
        
        # Apply browser controls
        self.browser_config = {
            'viewport_width': BrowserControlVariables.VIEWPORT_WIDTH,
            'viewport_height': BrowserControlVariables.VIEWPORT_HEIGHT,
            'timeout': BrowserControlVariables.PAGE_LOAD_TIMEOUT
        }
        
        print("✅ Controlled testing mode enabled")

# Usage:
agent = GeminiBrowserAgent(
    gemini_api_key="your_key", 
    enable_testing=True  # Enable controlled testing
)
""")

def create_test_checklist():
    """
    Create a checklist for implementing controlled testing
    """
    print("\n📋 Implementation Checklist")
    print("=" * 50)
    
    checklist = [
        "✅ Test variables package created in test_versiables/",
        "✅ __init__.py file added for proper package structure", 
        "✅ ReproducibilityController for consistent random seeds",
        "✅ BrowserControlVariables for consistent browser settings",
        "✅ TestWebsites for predefined test targets",
        "✅ EconomicControlVariables for context normalization",
        "⏳ Integration with browseruse_gemini.py (next step)",
        "⏳ Add controlled testing flag to agent initialization",
        "⏳ Create test scenarios and run reproducible experiments"
    ]
    
    for item in checklist:
        print(f"   {item}")
    
    print(f"\n💡 Next Steps:")
    print("1. Add imports to your browseruse_gemini.py")
    print("2. Modify GeminiBrowserAgent.__init__ to accept enable_testing parameter")
    print("3. Apply control variables when enable_testing=True")
    print("4. Run controlled experiments with consistent parameters")

if __name__ == "__main__":
    # Run the demonstration
    test_config = demonstrate_controlled_testing()
    show_browseruse_integration()
    create_test_checklist()
    
    print(f"\n🎉 Test Variables Setup Complete!")
    print(f"Location: /Users/mouhcine/websites_agent_fellowship/web-agent/Cohort 34 - Web Agent/core/test_versiables/") 