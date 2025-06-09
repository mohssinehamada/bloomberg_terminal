# Test Variables Package

A comprehensive test variables and control variables package for the Web Agent project, designed to ensure reproducible experiments and proper experimental control.

## 📁 Package Structure

```
test_versiables/
├── __init__.py                          # Package initialization
├── test_variables.py                    # Core test variables and control settings
├── enhanced_economic_variables.py       # Real-time economic data integration
├── test_config_manager.py              # Advanced test configuration management
├── integration_example.py              # Full integration examples
├── test_integration_patch.py           # Minimal integration patches
└── README.md                           # This file
```

## 🎯 Core Concepts

### Control Variables
Variables kept constant to prevent them from influencing experimental outcomes:
- **Reproducibility Controls**: Random seeds, model temperature, timeouts
- **Browser Controls**: Viewport size, user agent, retry settings
- **Economic Controls**: CPI, unemployment rate, federal rates for data normalization

### Test Variables
Configurable parameters for different test scenarios:
- **Test Websites**: Predefined URLs for different domains
- **Test Queries**: Standard queries for reproducible testing
- **Validation Criteria**: Success thresholds and data quality metrics

## 🚀 Quick Start

### Basic Usage

```python
from test_versiables import (
    setup_test_environment,
    ReproducibilityController,
    TestWebsites,
    EconomicControlVariables
)

# Setup controlled test environment
config = setup_test_environment("my_experiment", seed=42)

# Use predefined test sites
test_site = TestWebsites.REAL_ESTATE_SITES["zillow"]

# Get economic context for data normalization
economic_context = EconomicControlVariables.get_current_economic_context()
```

### Integration with BrowserUse Gemini

```python
# In your browseruse_gemini.py, add:
from test_versiables import (
    ReproducibilityController,
    BrowserControlVariables,
    setup_test_environment
)

class GeminiBrowserAgent:
    def __init__(self, gemini_api_key=None, enable_testing=False, **kwargs):
        # ... existing code ...
        
        if enable_testing:
            # Setup controlled environment
            setup_test_environment("production_test")
            
            # Apply reproducibility controls
            ReproducibilityController.set_random_seeds()
            
            # Apply browser controls
            self.browser_config = {
                'viewport_width': BrowserControlVariables.VIEWPORT_WIDTH,
                'viewport_height': BrowserControlVariables.VIEWPORT_HEIGHT,
                'timeout': BrowserControlVariables.PAGE_LOAD_TIMEOUT
            }
            
            print("✅ Controlled testing mode enabled")
```

## 📊 Advanced Features

### Real-Time Economic Data

```python
from test_versiables import RealTimeEconomicData, EnhancedEconomicNormalizer

# Get real-time economic data (requires FRED API key)
economic_data = RealTimeEconomicData.get_real_time_data()

# Normalize prices using economic indicators
prices = [750000, 850000, 950000]
normalized_prices = EnhancedEconomicNormalizer.normalize_prices(
    prices, economic_data
)
```

### Test Configuration Manager

```python
from test_versiables import TestConfigurationManager, TestConfiguration

# Create test manager
manager = TestConfigurationManager()

# Create custom test configuration
config = TestConfiguration(
    name="custom_real_estate_test",
    description="Custom real estate extraction test",
    test_type="real_estate",
    websites=["https://www.zillow.com/san-francisco-ca/"],
    queries=["Find 3-bedroom houses under $800,000"],
    max_iterations=3,
    validation_criteria={"min_success_rate": 80, "min_items_per_query": 3}
)

manager.create_configuration(config)

# Run test suite
results = await manager.run_test_suite(["custom_real_estate_test"])

# Analyze results
analysis = manager.analyze_results(results)
```

## 🔧 Configuration Classes

### ReproducibilityController
Controls random seeds and deterministic behavior:
- `RANDOM_SEED = 42` - Default random seed
- `MODEL_TEMPERATURE = 0.1` - LLM temperature for consistency
- `set_random_seeds(seed)` - Set all random seeds

### BrowserControlVariables
Browser automation consistency:
- `VIEWPORT_WIDTH = 1920`, `VIEWPORT_HEIGHT = 1080` - Standard viewport
- `PAGE_LOAD_TIMEOUT = 30000` - Page load timeout (ms)
- `MAX_RETRIES = 3` - Retry attempts for failed operations

### TestWebsites
Predefined test websites:
- `REAL_ESTATE_SITES` - Zillow, Realtor.com, Redfin
- `FINANCIAL_SITES` - Bankrate, NerdWallet, Quicken
- `E_COMMERCE_SITES` - Amazon, eBay, Best Buy
- `NEWS_SITES` - BBC, CNN, Reuters

### EconomicControlVariables
Economic indicators for data normalization:
- `unemployment_rate` - Current unemployment rate
- `cpi_all_items` - Consumer Price Index
- `effr` - Effective Federal Funds Rate
- `monthly_gdp` - Monthly GDP estimate

## 🧪 Test Scenarios

### Predefined Test Configurations

1. **basic_real_estate**: Basic real estate extraction test
2. **financial_rates**: Financial rates extraction test
3. **performance_stress**: High-volume stress test
4. **reproducibility_test**: Consistent reproducible results test

### Running Tests

```python
# Run specific tests
results = await manager.run_test_suite([
    "basic_real_estate", 
    "financial_rates"
])

# Run all available tests
results = await manager.run_test_suite()

# Analyze results
analysis = manager.analyze_results(results)
print(f"Overall Success Rate: {analysis['summary']['overall_success_rate']}%")
```

## 📈 Data Normalization

### Economic Context Normalization

```python
# Get current economic context
economic_context = EconomicControlVariables.get_current_economic_context()

# Normalize extracted data
def normalize_listing_prices(listings, economic_context):
    current_cpi = economic_context['economic_indicators']['cpi_all_items']
    base_cpi = 307.5  # Baseline CPI
    
    for listing in listings:
        if 'price' in listing:
            listing['normalized_price'] = listing['price'] * (base_cpi / current_cpi)
            listing['economic_timestamp'] = economic_context['timestamp']
    
    return listings
```

### Market Condition Adjustments

```python
# Adjust data based on market conditions
adjusted_data = EnhancedEconomicNormalizer.adjust_for_market_conditions(
    extracted_data, economic_context
)

# Access market condition flags
market_conditions = adjusted_data['market_conditions']
print(f"Unemployment Level: {market_conditions['unemployment_level']}")
print(f"Consumer Confidence: {market_conditions['consumer_confidence']}")
```

## 🔍 Best Practices

### 1. Reproducibility
- Always set random seeds before experiments
- Use consistent model temperatures
- Document all control variables used

### 2. Data Quality
- Apply economic normalization for time-series comparisons
- Use validation criteria to ensure data quality
- Monitor success rates and adjust thresholds

### 3. Test Organization
- Use descriptive test configuration names
- Group related tests into suites
- Save and version test configurations

### 4. Performance Monitoring
- Track response times and resource usage
- Set appropriate timeouts and retry limits
- Monitor for degradation over time

## 🛠️ Integration Steps

### Step 1: Import Test Variables
Add imports to your main module:
```python
from test_versiables import (
    setup_test_environment,
    ReproducibilityController,
    BrowserControlVariables
)
```

### Step 2: Modify Agent Initialization
Add controlled testing support:
```python
def __init__(self, enable_testing=False, **kwargs):
    if enable_testing:
        setup_test_environment("my_scenario")
        ReproducibilityController.set_random_seeds()
```

### Step 3: Apply Control Variables
Use controlled parameters:
```python
# Browser settings
viewport = {
    'width': BrowserControlVariables.VIEWPORT_WIDTH,
    'height': BrowserControlVariables.VIEWPORT_HEIGHT
}

# Model settings
temperature = ReproducibilityController.MODEL_TEMPERATURE
```

### Step 4: Run Controlled Tests
Execute tests with consistent parameters:
```python
agent = GeminiBrowserAgent(enable_testing=True)
results = await agent.execute_task(test_websites, max_steps=10)
```

## 📊 Result Analysis

### Success Rate Monitoring
```python
def analyze_success_rate(results):
    total_queries = sum(r['total_queries'] for r in results.values())
    successful_queries = sum(r['successful_queries'] for r in results.values())
    
    success_rate = (successful_queries / total_queries * 100)
    
    if success_rate < 70:
        print("⚠️ Low success rate detected")
        return False
    return True
```

### Performance Tracking
```python
def track_performance(results):
    response_times = [r['average_response_time'] for r in results.values()]
    avg_time = statistics.mean(response_times)
    
    if avg_time > 30:  # seconds
        print("⚠️ High response times detected")
    
    return {
        'avg_response_time': avg_time,
        'max_response_time': max(response_times),
        'min_response_time': min(response_times)
    }
```

## 🔮 Future Enhancements

- **Machine Learning Integration**: A/B testing with ML model comparison
- **Real-Time Monitoring**: Live dashboard for test metrics
- **Advanced Analytics**: Trend analysis and anomaly detection
- **Cloud Integration**: Distributed testing across multiple environments

## 🤝 Contributing

1. Follow the existing code structure and naming conventions
2. Add comprehensive docstrings and type hints
3. Include unit tests for new functionality
4. Update this README with new features

## 📄 License

This package is part of the Web Agent project and follows the project's licensing terms. 