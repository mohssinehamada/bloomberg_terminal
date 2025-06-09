#!/usr/bin/env python3
"""
Debug script to test database saving with actual extracted data format
"""

import sys
import os
import json
import logging

# Set up detailed logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from database.database import insert_listing, log_scrape, init_db
    print("✅ Successfully imported database functions")
except ImportError as e:
    print(f"❌ Failed to import database functions: {e}")
    sys.exit(1)

def test_with_actual_data():
    """Test database saving with the actual data format from Craigslist"""
    
    print("🔍 Testing Database Save with Actual Craigslist Data\n")
    
    # This is the actual data format from your Craigslist extraction
    sample_listings = [
        {
            "date": "5/27",
            "bedrooms": "3",
            "area_sqft": "2000",
            "location": "New York",
            "price": "$265,000",
            "description": "3/2/2, Brick, CA/CH with a Water well and Acreage close to town."
        },
        {
            "date": "5/23",
            "bedrooms": "3",
            "area_sqft": "1552",
            "location": "East New York",
            "price": "$695,000",
            "description": "Charming 1 Family Home w/ Balcony in East New York! OH 5/24 (Sat)"
        },
        {
            "date": "5/23",
            "bedrooms": "3",
            "area_sqft": "1150",
            "location": "brooklyn",
            "price": "$1,275,000",
            "description": "1 family house for sale in Kensington-Fixer Upper!"
        }
    ]
    
    print(f"Testing with {len(sample_listings)} sample listings...")
    
    saved_count = 0
    for i, listing in enumerate(sample_listings, 1):
        print(f"\n--- Testing Listing {i} ---")
        print(f"Original data: {json.dumps(listing, indent=2)}")
        
        try:
            # Add missing fields that the database expects
            processed_listing = listing.copy()
            
            # Map fields to what database expects
            if 'description' in processed_listing and 'title' not in processed_listing:
                processed_listing['title'] = processed_listing['description']
            
            if 'area_sqft' in processed_listing:
                processed_listing['area'] = processed_listing['area_sqft']
            
            # Add missing bathroom info (extract from description if possible)
            if 'bathrooms' not in processed_listing:
                desc = processed_listing.get('description', '')
                if '3/2/2' in desc:  # Format like "3/2/2" means 3 bed, 2 bath, 2 something
                    processed_listing['bathrooms'] = '2'
                else:
                    processed_listing['bathrooms'] = ''
            
            # Add source info
            processed_listing['other'] = json.dumps({
                'source_url': 'https://newyork.craigslist.org/',
                'search_criteria': '{"location": "New York", "bedrooms": "3", "bathrooms": "2", "price_max": 800000, "home_type": "house"}',
                'original_data': listing
            })
            
            print(f"Processed data: {json.dumps(processed_listing, indent=2)}")
            
            # Try to insert
            listing_id = insert_listing(processed_listing)
            if listing_id:
                saved_count += 1
                print(f"✅ Successfully saved listing {i} with ID: {listing_id}")
                print(f"   📍 {processed_listing.get('location', 'Unknown')}")
                print(f"   💰 {processed_listing.get('price', 'Unknown')}")
                print(f"   🏠 {processed_listing.get('bedrooms', '?')} bed, {processed_listing.get('bathrooms', '?')} bath")
            else:
                print(f"❌ Failed to save listing {i}")
                
        except Exception as e:
            print(f"❌ Error saving listing {i}: {e}")
            logger.exception(f"Detailed error for listing {i}")
            continue
    
    print(f"\n📊 Results:")
    print(f"   Total listings tested: {len(sample_listings)}")
    print(f"   Successfully saved: {saved_count}")
    print(f"   Success rate: {(saved_count/len(sample_listings))*100:.1f}%")
    
    return saved_count > 0

def test_data_format_variations():
    """Test different data format variations to see what works"""
    
    print("\n🔬 Testing Different Data Format Variations\n")
    
    test_cases = [
        {
            "name": "Minimal required fields",
            "data": {
                "title": "Test Property 1",
                "location": "Test Location",
                "price": "$500,000"
            }
        },
        {
            "name": "With bedrooms/bathrooms",
            "data": {
                "title": "Test Property 2", 
                "location": "Test Location",
                "price": "$600,000",
                "bedrooms": "3",
                "bathrooms": "2"
            }
        },
        {
            "name": "With area field",
            "data": {
                "title": "Test Property 3",
                "location": "Test Location", 
                "price": "$700,000",
                "bedrooms": "4",
                "bathrooms": "3",
                "area": "2000"
            }
        },
        {
            "name": "With time instead of date",
            "data": {
                "title": "Test Property 4",
                "time": "5/27",
                "location": "Test Location",
                "price": "$800,000",
                "bedrooms": "3",
                "bathrooms": "2"
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"Testing: {test_case['name']}")
        print(f"Data: {json.dumps(test_case['data'], indent=2)}")
        
        try:
            listing_id = insert_listing(test_case['data'])
            if listing_id:
                print(f"✅ Success! Saved with ID: {listing_id}")
            else:
                print(f"❌ Failed to save")
        except Exception as e:
            print(f"❌ Error: {e}")
            logger.exception(f"Error in test case: {test_case['name']}")
        
        print("-" * 50)

if __name__ == "__main__":
    print("🚀 Starting Database Save Debug Tests\n")
    
    # Initialize database
    try:
        init_db()
        print("✅ Database initialized\n")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        sys.exit(1)
    
    # Test with actual data
    success1 = test_with_actual_data()
    
    # Test format variations
    test_data_format_variations()
    
    if success1:
        print("\n🎉 Database saving is working! The issue might be in the data format or error handling.")
    else:
        print("\n❌ Database saving failed. Check the logs above for details.") 