"""
Enhanced Economic Variables with Real-Time Data Integration

This module provides enhanced economic control variables that can pull
real-time data from APIs for more accurate market context.
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os

class RealTimeEconomicData:
    """Enhanced economic control variables with real-time data"""
    
    # API endpoints for real economic data
    FRED_API_BASE = "https://api.stlouisfed.org/fred/series/observations"
    
    # FRED (Federal Reserve Economic Data) series IDs
    ECONOMIC_SERIES = {
        "unemployment_rate": "UNRATE",
        "cpi_all_items": "CPIAUCSL",
        "federal_funds_rate": "FEDFUNDS",
        "gdp": "GDP",
        "consumer_sentiment": "UMCSENT"
    }
    
    # Fallback data when API is unavailable
    FALLBACK_DATA = {
        "unemployment_rate": 3.7,
        "cpi_all_items": 307.5,
        "holiday_days": 0,
        "effr": 5.25,
        "monthly_gdp": 25000000,
        "consumer_sentiment": 69.1,
        "data_source": "fallback_mock_data",
        "last_updated": "2024-01-01"
    }
    
    @classmethod
    def get_real_time_data(cls, api_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch real-time economic data from FRED API
        
        Args:
            api_key: FRED API key (get from https://fred.stlouisfed.org/docs/api/api_key.html)
        
        Returns:
            Dictionary with current economic indicators
        """
        if not api_key:
            api_key = os.getenv('FRED_API_KEY')
        
        if not api_key:
            print("⚠️  No FRED API key found, using fallback data")
            return cls._add_metadata(cls.FALLBACK_DATA.copy())
        
        try:
            economic_data = {}
            
            for indicator, series_id in cls.ECONOMIC_SERIES.items():
                value = cls._fetch_latest_value(series_id, api_key)
                if value is not None:
                    economic_data[indicator] = value
                else:
                    economic_data[indicator] = cls.FALLBACK_DATA.get(indicator, 0)
            
            # Add holiday calculation
            economic_data["holiday_days"] = cls._calculate_holiday_days()
            economic_data["data_source"] = "fred_api_real_time"
            economic_data["last_updated"] = datetime.now().isoformat()
            
            return cls._add_metadata(economic_data)
            
        except Exception as e:
            print(f"⚠️  Error fetching real-time data: {e}")
            print("   Using fallback data instead")
            return cls._add_metadata(cls.FALLBACK_DATA.copy())
    
    @classmethod
    def _fetch_latest_value(cls, series_id: str, api_key: str) -> Optional[float]:
        """Fetch the latest value for a FRED series"""
        try:
            # Get data from last 12 months to ensure we get recent data
            end_date = datetime.now().strftime('%Y-%m-%d')
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
            
            params = {
                'series_id': series_id,
                'api_key': api_key,
                'file_type': 'json',
                'observation_start': start_date,
                'observation_end': end_date,
                'sort_order': 'desc',
                'limit': 1
            }
            
            response = requests.get(cls.FRED_API_BASE, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            observations = data.get('observations', [])
            
            if observations and observations[0]['value'] != '.':
                return float(observations[0]['value'])
                
        except Exception as e:
            print(f"   Failed to fetch {series_id}: {e}")
        
        return None
    
    @classmethod
    def _calculate_holiday_days(cls) -> int:
        """Calculate number of federal holidays in current month"""
        # Simplified calculation - in production, use a proper holiday library
        from datetime import date
        
        # Major US federal holidays (simplified)
        current_month = date.today().month
        current_year = date.today().year
        
        holidays = [
            (1, 1),   # New Year's Day
            (7, 4),   # Independence Day
            (12, 25), # Christmas Day
            # Add more holidays as needed
        ]
        
        return sum(1 for month, day in holidays if month == current_month)
    
    @classmethod
    def _add_metadata(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add metadata to economic data"""
        return {
            "timestamp": datetime.now().isoformat(),
            "economic_indicators": data,
            "region": "US",
            "currency": "USD",
            "data_quality": "real_time" if "fred_api" in data.get("data_source", "") else "mock",
            "control_variables_list": list(cls.ECONOMIC_SERIES.keys()) + ["holiday_days"]
        }

class EnhancedEconomicNormalizer:
    """Normalize data using economic control variables"""
    
    @staticmethod
    def normalize_prices(prices: list, economic_context: Dict[str, Any], 
                        base_cpi: float = 307.5) -> list:
        """
        Normalize prices using CPI adjustment
        
        Args:
            prices: List of prices to normalize
            economic_context: Economic context from RealTimeEconomicData
            base_cpi: Base CPI for normalization (default: current baseline)
        
        Returns:
            List of normalized prices
        """
        current_cpi = economic_context['economic_indicators'].get('cpi_all_items', base_cpi)
        adjustment_factor = base_cpi / current_cpi
        
        return [price * adjustment_factor for price in prices]
    
    @staticmethod
    def adjust_for_market_conditions(data: Dict[str, Any], 
                                   economic_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Adjust extracted data based on economic conditions
        
        Args:
            data: Extracted data (e.g., real estate listings, rates)
            economic_context: Economic context for adjustments
        
        Returns:
            Data with economic adjustments applied
        """
        adjusted_data = data.copy()
        indicators = economic_context['economic_indicators']
        
        # Example adjustments based on economic indicators
        unemployment_rate = indicators.get('unemployment_rate', 3.7)
        consumer_sentiment = indicators.get('consumer_sentiment', 69.1)
        
        # Add market condition flags
        adjusted_data['market_conditions'] = {
            'unemployment_level': 'high' if unemployment_rate > 5.0 else 'normal' if unemployment_rate > 3.0 else 'low',
            'consumer_confidence': 'high' if consumer_sentiment > 80 else 'normal' if consumer_sentiment > 60 else 'low',
            'market_context': 'recession_risk' if unemployment_rate > 6.0 else 'stable',
            'economic_timestamp': economic_context['timestamp']
        }
        
        return adjusted_data

# Example usage and testing
if __name__ == "__main__":
    print("🏛️ Enhanced Economic Variables Demo")
    print("=" * 50)
    
    # Test real-time data fetching
    economic_data = RealTimeEconomicData.get_real_time_data()
    
    print("📊 Current Economic Context:")
    for key, value in economic_data['economic_indicators'].items():
        if isinstance(value, (int, float)):
            print(f"   {key}: {value}")
        else:
            print(f"   {key}: {value}")
    
    print(f"\n🔄 Data Source: {economic_data['economic_indicators']['data_source']}")
    print(f"📅 Last Updated: {economic_data['economic_indicators']['last_updated']}")
    
    # Test normalization
    sample_prices = [750000, 850000, 950000]
    normalized_prices = EnhancedEconomicNormalizer.normalize_prices(
        sample_prices, economic_data
    )
    
    print(f"\n💰 Price Normalization Example:")
    for orig, norm in zip(sample_prices, normalized_prices):
        change = ((norm/orig - 1) * 100)
        print(f"   ${orig:,} → ${norm:,.0f} ({change:+.1f}%)")
    
    # Test market condition adjustment
    sample_data = {"listings": ["house1", "house2"], "average_price": 800000}
    adjusted_data = EnhancedEconomicNormalizer.adjust_for_market_conditions(
        sample_data, economic_data
    )
    
    print(f"\n🏦 Market Conditions:")
    conditions = adjusted_data['market_conditions']
    for key, value in conditions.items():
        if key != 'economic_timestamp':
            print(f"   {key}: {value}") 