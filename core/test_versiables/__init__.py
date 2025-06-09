"""
Test Variables Package for Web Agent

This package contains control variables, test configurations, 
and experimental parameters for the web-agent project.
"""

from .test_variables import (
    ReproducibilityController,
    BrowserControlVariables,
    TestWebsites,
    EconomicControlVariables,
    setup_test_environment
)

# Import enhanced modules
try:
    from .enhanced_economic_variables import (
        RealTimeEconomicData,
        EnhancedEconomicNormalizer
    )
    from .test_config_manager import (
        TestConfiguration,
        TestResult,
        TestConfigurationManager
    )
    ENHANCED_FEATURES_AVAILABLE = True
except ImportError:
    ENHANCED_FEATURES_AVAILABLE = False

__version__ = "1.1.0"
__all__ = [
    "ReproducibilityController",
    "BrowserControlVariables", 
    "TestWebsites",
    "EconomicControlVariables",
    "setup_test_environment"
]

# Add enhanced features if available
if ENHANCED_FEATURES_AVAILABLE:
    __all__.extend([
        "RealTimeEconomicData",
        "EnhancedEconomicNormalizer",
        "TestConfiguration",
        "TestResult", 
        "TestConfigurationManager"
    ]) 