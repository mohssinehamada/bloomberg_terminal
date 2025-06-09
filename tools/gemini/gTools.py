import json
import re
import pandas as pd
import logging
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Any
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RateLimiter:
    """Rate limiter for API calls"""

    def __init__(self, calls_per_minute: int = 10):
        """
        Initialize rate limiter
        
        Args:
            calls_per_minute: Maximum number of calls allowed per minute
        """
        self.calls_per_minute = calls_per_minute
        self.call_timestamps = deque()
        
    def wait_if_needed(self):
        """Wait if necessary to respect rate limits"""
        now = datetime.now()
        
        # Remove timestamps older than 1 minute
        while self.call_timestamps and (now - self.call_timestamps[0]) > timedelta(minutes=1):
            self.call_timestamps.popleft()
        
        # If we've reached the limit, wait until we can make another call
        if len(self.call_timestamps) >= self.calls_per_minute:
            # Calculate sleep time based on oldest timestamp
            sleep_time = 60 - (now - self.call_timestamps[0]).total_seconds()
            if sleep_time > 0:
                logger.info(f"Rate limit reached. Waiting {sleep_time:.2f} seconds...")
                time.sleep(sleep_time + 0.1)  # Add a small buffer
        
        # Record this call
        self.call_timestamps.append(now)

def format_interest_rates(interest_rates_result: Dict[str, Any]):
    """
    Format interest rates for display
    
    Args:
        interest_rates_result: Dictionary containing interest rate information
    """
    print("\n=== FORMATTED INTEREST RATES ===\n")
    
    # Parse from raw response if needed
    if "raw_response" in interest_rates_result:
        # Extract JSON from code blocks if present
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', interest_rates_result["raw_response"])
        if json_match:
            json_str = json_match.group(1).strip()
            try:
                parsed_data = json.loads(json_str)
                if "interest_rates" in parsed_data:
                    rates_data = parsed_data["interest_rates"]
                    source_info = parsed_data.get("source_info", {})
                else:
                    print("Could not find interest rates in parsed data")
                    return
            except json.JSONDecodeError:
                print("Could not parse interest rates JSON from raw response")
                print(interest_rates_result["raw_response"])
                return
    elif "interest_rates" in interest_rates_result:
        rates_data = interest_rates_result["interest_rates"]
        source_info = interest_rates_result.get("source_info", {})
    else:
        print("No interest rates data found")
        return
    
    # Display source information if available
    if source_info:
        print("Source Information:")
        print(f"Website: {source_info.get('website', 'N/A')}")
        print(f"Last Updated: {source_info.get('last_updated', 'N/A')}")
        print("-" * 40)
    
    # Create a pandas DataFrame for display
    df = pd.DataFrame(rates_data)
    
    # Define preferred column order
    preferred_cols = ['account_type', 'rate', 'rate_type', 'terms', 'effective_date']
    
    # Reorder columns if they exist
    actual_cols = [col for col in preferred_cols if col in df.columns]
    other_cols = [col for col in df.columns if col not in preferred_cols]
    df = df[actual_cols + other_cols]
    
    # Replace None values with "N/A" for better display
    df = df.fillna("N/A")
    
    # Display as a formatted table
    try:
        # Try to display as HTML (works in Jupyter notebooks)
        from IPython.display import display, HTML
        display(HTML(df.to_html(index=False, classes="table table-striped table-hover")))
    except Exception:
        # Fall back to regular print if display HTML fails
        print("\nAccount Types and Rates:")
        print("-" * 60)
        for _, row in df.iterrows():
            print(f"• {row['account_type']}: {row['rate']}")
            
            # Print additional details if available
            details = []
            if 'rate_type' in row and row['rate_type'] != "N/A":
                details.append(f"Type: {row['rate_type']}")
            if 'terms' in row and row['terms'] != "N/A":
                details.append(f"Terms: {row['terms']}")
            if 'effective_date' in row and row['effective_date'] != "N/A":
                details.append(f"As of: {row['effective_date']}")
            
            if details:
                print(f"  {' | '.join(details)}")
            print("-" * 60)

def format_real_estate_listings(listings_result: List[Dict[str, Any]]):
    """
    Format real estate listings for display
    
    Args:
        listings_result: List of dictionaries containing property listings
    """
    print("\n=== FORMATTED REAL ESTATE LISTINGS ===\n")
    
    # Parse from raw response if needed
    if listings_result and isinstance(listings_result, list):
        if "raw_response" in listings_result[0]:
            # Extract JSON from code blocks if present
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', listings_result[0]["raw_response"])
            if json_match:
                json_str = json_match.group(1).strip()
                try:
                    listings_data = json.loads(json_str)
                except json.JSONDecodeError:
                    print("Could not parse listings JSON from raw response")
                    print(listings_result[0]["raw_response"])
                    return
            else:
                print("No valid JSON found in raw response")
                return
        elif "error" in listings_result[0]:
            print(f"Error occurred: {listings_result[0]['error']}")
            return
        else:
            listings_data = listings_result
    else:
        print("No listings data found or data is in unexpected format")
        return
    
    if not listings_data or not isinstance(listings_data, list):
        print("No listings data found or data is in unexpected format")
        return
    
    print(f"Found {len(listings_data)} listings matching your criteria\n")
    
    # Try to display as HTML table for better formatting in notebooks
    try:
        # Import for Jupyter notebook display
        from IPython.display import display, HTML
        
        # Create a list of dicts with consistent keys for DataFrame
        clean_listings = []
        for listing in listings_data:
            clean_listing = {
                "Address": listing.get("address", "N/A"),
                "Price": listing.get("price", "N/A"),
                "Type": listing.get("property_type", "N/A"),
                "Beds": listing.get("bedrooms", "N/A"),
                "Baths": listing.get("bathrooms", "N/A"),
                "Area": listing.get("square_footage", "N/A"),
                "Year": listing.get("year_built", "N/A"),
                "Features": ", ".join(listing.get("features", [])) if isinstance(listing.get("features"), list) else listing.get("features", "N/A"),
                "Contact": listing.get("contact", "N/A")
            }
            clean_listings.append(clean_listing)
        
        df = pd.DataFrame(clean_listings)
        
        # Display the styled table
        styled_df = df.style.set_properties(**{
            'text-align': 'left',
            'white-space': 'pre-wrap',
            'font-size': '12px'
        })
        display(HTML(styled_df.to_html(index=False, classes="table table-striped table-hover")))
    except Exception as e:
        # Fall back to standard printout
        for i, listing in enumerate(listings_data):
            print(f"\nProperty {i+1}:")
            print("=" * 60)
            
            # Address and price (primary info)
            print(f"{listing.get('address', 'N/A')}")
            print(f"{listing.get('price', 'N/A')}")
            
            # Main specs
            specs = []
            if listing.get('property_type', 'N/A') != 'N/A':
                specs.append(f"Type: {listing.get('property_type')}")
            if listing.get('bedrooms', 'N/A') != 'N/A':
                specs.append(f"{listing.get('bedrooms')} bed")
            if listing.get('bathrooms', 'N/A') != 'N/A':
                specs.append(f"{listing.get('bathrooms')} bath")
            if listing.get('square_footage', 'N/A') != 'N/A':
                specs.append(f"{listing.get('square_footage')}")
            if listing.get('year_built', 'N/A') != 'N/A' and listing.get('year_built') != 'N/A':
                specs.append(f"Built: {listing.get('year_built')}")
            
            print(f"{' | '.join(specs)}")
            
            # Features
            features = listing.get('features', [])
            if features and features != 'N/A':
                if isinstance(features, list):
                    print(f"Features: {', '.join(features)}")
                else:
                    print(f"Features: {features}")
            
            # Contact info
            if listing.get('contact', 'N/A') != 'N/A':
                print(f"Contact: {listing.get('contact')}")
            
            # Listing URL if available
            if 'listing_url' in listing and listing['listing_url'] != 'N/A':
                print(f"🔗 More info: {listing['listing_url']}")
            
            print("-" * 60)