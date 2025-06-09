"""
Integration Patch for browseruse_gemini.py

This file shows the minimal modifications needed to integrate test variables
into your existing browseruse_gemini.py without major refactoring.
"""

# Add these imports at the top of browseruse_gemini.py
from test_variables import (
    ReproducibilityController,
    BrowserControlVariables,
    EconomicControlVariables,
    setup_test_environment
)

# Modify the GeminiBrowserAgent.__init__ method
class ModifiedGeminiBrowserAgent:
    """
    Shows how to modify the existing GeminiBrowserAgent class
    """
    
    def __init__(self, gemini_api_key=None, task=None, 
                 enable_controlled_testing=False, test_scenario="standard", **kwargs):
        
        # Original initialization code stays the same...
        
        # Add controlled testing support
        if enable_controlled_testing:
            print("🧪 Enabling controlled testing mode")
            
            # Setup test environment
            self.test_config = setup_test_environment(test_scenario)
            
            # Apply reproducibility controls
            ReproducibilityController.set_random_seeds()
            
            # Override model temperature for consistency
            if hasattr(self, 'llm') and hasattr(self.llm, 'temperature'):
                self.llm.temperature = ReproducibilityController.MODEL_TEMPERATURE
                print(f"🎯 Model temperature set to {ReproducibilityController.MODEL_TEMPERATURE}")
            
            # Store browser control variables for use in browser setup
            self.controlled_browser_config = {
                'headless': BrowserControlVariables.HEADLESS_MODE,
                'viewport': {
                    'width': BrowserControlVariables.VIEWPORT_WIDTH,
                    'height': BrowserControlVariables.VIEWPORT_HEIGHT
                },
                'timeout': BrowserControlVariables.PAGE_LOAD_TIMEOUT,
                'user_agent': BrowserControlVariables.USER_AGENT
            }
            
            print("✅ Controlled testing mode enabled")
        else:
            self.test_config = None
            self.controlled_browser_config = None

    def get_economic_context(self):
        """
        Add this method to get current economic context for analysis
        """
        return EconomicControlVariables.get_current_economic_context()

    def preprocess_with_controls(self, data):
        """
        Add this method to preprocess data with control variables
        """
        if not hasattr(self, 'test_config') or self.test_config is None:
            return data
        
        # Apply economic control variables normalization
        economic_context = self.get_economic_context()
        
        # Add economic context to the data
        if isinstance(data, dict):
            data['economic_context'] = economic_context
            data['test_configuration'] = self.test_config
        
        return data

# Example of how to use the modified class:
def create_controlled_agent(api_key, test_mode=True):
    """
    Factory function to create a controlled testing agent
    """
    if test_mode:
        return ModifiedGeminiBrowserAgent(
            gemini_api_key=api_key,
            enable_controlled_testing=True,
            test_scenario="real_estate_analysis"
        )
    else:
        return ModifiedGeminiBrowserAgent(gemini_api_key=api_key)

# Simple test runner that can be added to browseruse_gemini.py
async def run_controlled_test_simple(agent, test_type="real_estate"):
    """
    Simple test runner that uses control variables
    """
    print(f"🧪 Running controlled test: {test_type}")
    
    # Get test websites
    from test_variables import TestWebsites
    
    if test_type == "real_estate":
        test_site = list(TestWebsites.REAL_ESTATE_SITES.values())[0]
        test_query = "Find 3-bedroom houses under $800,000"
    else:
        test_site = "https://example.com"
        test_query = "Extract main content"
    
    # Apply controlled parameters
    websites = {"test_site": test_site}
    
    # Run with controlled settings
    result = await agent.execute_task(websites, max_steps=10)
    
    # Add control variable context to results
    if hasattr(agent, 'get_economic_context'):
        result['economic_context'] = agent.get_economic_context()
    
    if hasattr(agent, 'test_config'):
        result['test_config'] = agent.test_config
    
    return result

if __name__ == "__main__":
    print("🔧 Test Integration Patch")
    print("Add these modifications to your browseruse_gemini.py:")
    print("1. Import test_variables module")
    print("2. Add enable_controlled_testing parameter to __init__")
    print("3. Add get_economic_context() method")
    print("4. Add preprocess_with_controls() method")
    print("5. Use create_controlled_agent() factory function") 