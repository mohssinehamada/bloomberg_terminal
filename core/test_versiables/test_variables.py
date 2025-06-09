"""
Test Variables and Control Variables for Web Agent Testing

This module contains control variables, test configurations, and experimental parameters
for the web-agent project. These variables are kept separate from the main implementation
to ensure reproducibility and proper experimental control.

Based on research methodology best practices for control variables in data analysis.
"""

import random
import numpy as np
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

# =============================================================================
# REPRODUCIBILITY CONTROL VARIABLES
# =============================================================================

class ReproducibilityController:
    """Control variables for ensuring reproducible experiments"""
    
    # Random seed for reproducibility
    RANDOM_SEED = 42
    
    # Model temperature for consistent LLM behavior
    MODEL_TEMPERATURE = 0.1
    
    # Timeout values (in seconds)
    DEFAULT_TIMEOUT = 30
    LONG_TIMEOUT = 60
    SHORT_TIMEOUT = 10
    
    @classmethod
    def set_random_seeds(cls, seed: Optional[int] = None):
        """Set all random seeds for reproducibility"""
        if seed is None:
            seed = cls.RANDOM_SEED
            
        random.seed(seed)
        np.random.seed(seed)
        os.environ['PYTHONHASHSEED'] = str(seed)
        
        # For torch if available
        try:
            import torch
            torch.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
        except ImportError:
            pass
            
        print(f"🎯 Random seeds set to: {seed}")

# =============================================================================
# BROWSER CONTROL VARIABLES
# =============================================================================

class BrowserControlVariables:
    """Control variables for browser automation consistency"""
    
    # Browser settings
    HEADLESS_MODE = True
    BROWSER_TYPE = "chromium"  # chromium, firefox, webkit
    VIEWPORT_WIDTH = 1920
    VIEWPORT_HEIGHT = 1080
    
    # Network settings
    USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    
    # Wait times (milliseconds)
    PAGE_LOAD_TIMEOUT = 30000
    ELEMENT_TIMEOUT = 5000
    SCROLL_DELAY = 1000
    
    # Retry settings
    MAX_RETRIES = 3
    RETRY_DELAY = 2.0

# =============================================================================
# TEST WEBSITE CONFIGURATIONS
# =============================================================================

class TestWebsites:
    """Test websites for different types of extraction tasks"""
    
    REAL_ESTATE_SITES = {
        "zillow": "https://www.zillow.com/san-francisco-ca/",
        "realtor": "https://www.realtor.com/realestateandhomes-search/San-Francisco_CA",
        "redfin": "https://www.redfin.com/city/17151/CA/San-Francisco"
    }
    
    FINANCIAL_SITES = {
        "bankrate": "https://www.bankrate.com/mortgages/mortgage-rates/",
        "nerdwallet": "https://www.nerdwallet.com/mortgages/mortgage-rates",
        "quicken": "https://www.quickenloans.com/mortgage-rates"
    }
    
    E_COMMERCE_SITES = {
        "amazon": "https://www.amazon.com/s?k=laptop",
        "ebay": "https://www.ebay.com/sch/i.html?_nkw=laptop",
        "best_buy": "https://www.bestbuy.com/site/searchpage.jsp?st=laptop"
    }
    
    NEWS_SITES = {
        "bbc": "https://www.bbc.com/news",
        "cnn": "https://www.cnn.com/",
        "reuters": "https://www.reuters.com/"
    }

# =============================================================================
# ECONOMIC CONTROL VARIABLES (from your context)
# =============================================================================

class EconomicControlVariables:
    """Economic indicators that can affect web scraping results"""
    
    # These would typically be loaded from external APIs or datasets
    CONTROL_VARIABLES = [
        'unemployment_rate',
        'cpi_all_items', 
        'holiday_days',
        'effr',  # Effective Federal Funds Rate
        'monthly_gdp'
    ]
    
    # Mock data for testing - in production, load from actual sources
    MOCK_ECONOMIC_DATA = {
        "unemployment_rate": 3.7,  # Current US unemployment rate %
        "cpi_all_items": 307.5,    # Consumer Price Index
        "holiday_days": 0,         # Number of federal holidays this month
        "effr": 5.25,             # Federal funds rate %
        "monthly_gdp": 25000000    # Monthly GDP estimate (millions)
    }
    
    @classmethod
    def get_current_economic_context(cls) -> Dict[str, Any]:
        """Get current economic context for analysis normalization"""
        return {
            "timestamp": datetime.now().isoformat(),
            "economic_indicators": cls.MOCK_ECONOMIC_DATA,
            "data_source": "mock_data_for_testing",
            "region": "US",
            "currency": "USD"
        }

# =============================================================================
# TEST SCENARIOS AND EXPERIMENTAL CONDITIONS
# =============================================================================

class TestScenarios:
    """Predefined test scenarios for consistent experimentation"""
    
    REAL_ESTATE_QUERIES = [
        "Find 3-bedroom houses under $800,000 in San Francisco",
        "Show me condos with parking near downtown",
        "Find properties with a pool and garden",
        "Show rental properties under $3000/month",
        "Find houses built after 2010 with garage"
    ]
    
    FINANCIAL_QUERIES = [
        "What are current 30-year mortgage rates?",
        "Find the best refinancing rates available",
        "Show me FHA loan rates",
        "What are jumbo loan rates today?",
        "Compare fixed vs adjustable mortgage rates"
    ]
    
    E_COMMERCE_QUERIES = [
        "Find laptops under $1000 with good reviews",
        "Show me wireless headphones on sale",
        "Find gaming laptops with RTX graphics",
        "Show budget smartphones under $300",
        "Find tablets suitable for drawing"
    ]

# =============================================================================
# PERFORMANCE MONITORING VARIABLES
# =============================================================================

class PerformanceMetrics:
    """Variables for tracking and controlling performance metrics"""
    
    # Thresholds for performance monitoring
    MAX_RESPONSE_TIME_SECONDS = 30
    MAX_TOKEN_USAGE_PER_REQUEST = 10000
    MAX_COST_PER_REQUEST_USD = 0.50
    
    # Success rate thresholds
    MIN_SUCCESS_RATE_PERCENT = 80
    MIN_DATA_ACCURACY_PERCENT = 90
    
    # Resource usage limits
    MAX_MEMORY_USAGE_MB = 1024
    MAX_CPU_USAGE_PERCENT = 80

# =============================================================================
# EXPERIMENTAL CONDITIONS
# =============================================================================

class ExperimentalConditions:
    """Control different experimental conditions for A/B testing"""
    
    # Different LLM model configurations
    MODEL_CONFIGS = {
        "conservative": {
            "temperature": 0.1,
            "max_tokens": 1000,
            "model": "gemini-2.0-flash-exp"
        },
        "balanced": {
            "temperature": 0.3,
            "max_tokens": 2000,
            "model": "gemini-2.0-flash-exp"
        },
        "creative": {
            "temperature": 0.7,
            "max_tokens": 3000,
            "model": "gemini-1.5-pro"
        }
    }
    
    # Different browser strategies
    BROWSER_STRATEGIES = {
        "fast": {
            "headless": True,
            "disable_images": True,
            "disable_javascript": False,
            "timeout": 15
        },
        "standard": {
            "headless": True,
            "disable_images": False,
            "disable_javascript": False,
            "timeout": 30
        },
        "thorough": {
            "headless": False,
            "disable_images": False,
            "disable_javascript": False,
            "timeout": 60
        }
    }

# =============================================================================
# TEST DATA VALIDATION
# =============================================================================

class ValidationControls:
    """Control variables for data validation and quality assurance"""
    
    # Required fields for different data types
    REQUIRED_REAL_ESTATE_FIELDS = [
        'price', 'address', 'bedrooms', 'bathrooms', 'square_feet'
    ]
    
    REQUIRED_FINANCIAL_FIELDS = [
        'rate', 'type', 'term', 'provider', 'last_updated'
    ]
    
    REQUIRED_PRODUCT_FIELDS = [
        'name', 'price', 'rating', 'availability', 'seller'
    ]
    
    # Data quality thresholds
    MIN_EXTRACTED_ITEMS = 3
    MAX_EXTRACTED_ITEMS = 50
    MIN_FIELD_COMPLETION_RATE = 0.8  # 80% of required fields must be present

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def setup_test_environment(scenario: str = "standard", seed: Optional[int] = None):
    """Setup controlled test environment"""
    print(f"🧪 Setting up test environment: {scenario}")
    
    # Set reproducibility controls
    ReproducibilityController.set_random_seeds(seed)
    
    # Log environment setup
    environment_config = {
        "scenario": scenario,
        "timestamp": datetime.now().isoformat(),
        "seed": seed or ReproducibilityController.RANDOM_SEED,
        "browser_config": BrowserControlVariables.__dict__,
        "economic_context": EconomicControlVariables.get_current_economic_context()
    }
    
    # Save config for reproducibility
    with open(f"test_environment_{scenario}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json", 'w') as f:
        json.dump(environment_config, f, indent=2, default=str)
    
    print(f"✅ Test environment '{scenario}' ready")
    return environment_config

def get_test_config(test_type: str) -> Dict[str, Any]:
    """Get configuration for specific test type"""
    configs = {
        "real_estate": {
            "websites": TestWebsites.REAL_ESTATE_SITES,
            "queries": TestScenarios.REAL_ESTATE_QUERIES,
            "required_fields": ValidationControls.REQUIRED_REAL_ESTATE_FIELDS,
            "model_config": ExperimentalConditions.MODEL_CONFIGS["balanced"]
        },
        "financial": {
            "websites": TestWebsites.FINANCIAL_SITES,
            "queries": TestScenarios.FINANCIAL_QUERIES,
            "required_fields": ValidationControls.REQUIRED_FINANCIAL_FIELDS,
            "model_config": ExperimentalConditions.MODEL_CONFIGS["conservative"]
        },
        "ecommerce": {
            "websites": TestWebsites.E_COMMERCE_SITES,
            "queries": TestScenarios.E_COMMERCE_QUERIES,
            "required_fields": ValidationControls.REQUIRED_PRODUCT_FIELDS,
            "model_config": ExperimentalConditions.MODEL_CONFIGS["creative"]
        }
    }
    
    return configs.get(test_type, configs["real_estate"])

# =============================================================================
# MAIN TESTING INTERFACE
# =============================================================================

if __name__ == "__main__":
    # Example usage
    print("🧪 Web Agent Test Variables Module")
    print("=" * 50)
    
    # Setup test environment
    config = setup_test_environment("standard")
    
    # Show available test configurations
    print("\n📋 Available Test Configurations:")
    for test_type in ["real_estate", "financial", "ecommerce"]:
        test_config = get_test_config(test_type)
        print(f"  • {test_type}: {len(test_config['websites'])} websites, {len(test_config['queries'])} queries")
    
    # Show economic context
    economic_context = EconomicControlVariables.get_current_economic_context()
    print(f"\n📊 Economic Context: {economic_context['economic_indicators']}")
    
    print("\n✅ Test variables module ready for import!") 