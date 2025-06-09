#!/usr/bin/env python3
"""
Multi-Website Real Estate Testing Script
This script tests the GeminiBrowserAgent with multiple real estate websites and search criteria.
"""

import asyncio
import os
import time
import sys
import json
import random
import argparse
from dotenv import load_dotenv
from urllib.parse import quote_plus
import traceback

# Add parent directory to path to import from core and database
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.database import insert_listing, log_scrape, get_db_connection, init_db
from core.browseruse_gemini import GeminiBrowserAgent, handle_press_and_hold

# Load environment variables
load_dotenv(".env.zillow") # Try to load Zillow-specific env first
load_dotenv() # Fall back to default .env file

# Get API key from environment variable
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", None)
if not GEMINI_API_KEY:
    print("WARNING: You need to set your Gemini API key in .env.zillow or .env file.")
    api_key_input = input("Enter your Gemini API key to continue: ").strip()
    if api_key_input:
        GEMINI_API_KEY = api_key_input
    else:
        raise ValueError("A valid Gemini API key is required to run this script")

# Initialize the database tables if needed
init_db()

# Support different real estate websites
class RealEstateWebsite:
    def __init__(self, name, base_url, url_builder):
        self.name = name
        self.base_url = base_url
        self.url_builder = url_builder
    
    def build_url(self, location, bedrooms=None, bathrooms=None, price_min=None, price_max=None, home_type=None):
        return self.url_builder(self.base_url, location, bedrooms, bathrooms, price_min, price_max, home_type)

def build_zillow_url(base_url, location, bedrooms=None, bathrooms=None, price_min=None, price_max=None, home_type=None):
    """Build Zillow search URL with parameters"""
    location_slug = location.replace(", ", "-").replace(" ", "-").lower()
    url = f"{base_url}/homes/for_sale/{location_slug}/"
    
    params = []
    
    # Add price range
    if price_min is not None and price_max is not None:
        params.append(f"price={price_min}-{price_max}")
    elif price_min is not None:
        params.append(f"price={price_min}-")
    elif price_max is not None:
        params.append(f"price=0-{price_max}")
    
    # Add bedrooms
    if bedrooms is not None:
        params.append(f"beds-{bedrooms}")
    
    # Add bathrooms
    if bathrooms is not None:
        params.append(f"baths-{bathrooms}")
    
    # Add home type
    if home_type is not None:
        params.append(f"home-type-{home_type.lower()}")
    
    # Combine parameters
    if params:
        url += "_" + "_".join(params) + "_/"
    
    return url

def build_realtor_url(base_url, location, bedrooms=None, bathrooms=None, price_min=None, price_max=None, home_type=None):
    """Build Realtor.com search URL with parameters"""
    location_encoded = quote_plus(location)
    url = f"{base_url}/realestateandhomes-search/{location_encoded}/"
    
    params = []
    
    # Add price range
    if price_min is not None or price_max is not None:
        price_param = "price-"
        if price_min is not None:
            price_param += str(price_min)
        price_param += "-"
        if price_max is not None:
            price_param += str(price_max)
        params.append(price_param)
    
    # Add bedrooms
    if bedrooms is not None:
        bed_param = f"beds-{bedrooms}-"
        if str(bedrooms).endswith("+"):
            # Handle "3+" format
            bed_param = f"beds-{bedrooms.rstrip('+')}+-"
        params.append(bed_param)
    
    # Add bathrooms
    if bathrooms is not None:
        bath_param = f"baths-{bathrooms}-"
        if str(bathrooms).endswith("+"):
            # Handle "2+" format
            bath_param = f"baths-{bathrooms.rstrip('+')}+-"
        params.append(bath_param)
    
    # Add home type
    if home_type is not None:
        home_type_map = {
            "house": "single-family-home",
            "apartment": "apartment",
            "condo": "condo",
            "townhouse": "townhome"
        }
        mapped_type = home_type_map.get(home_type.lower(), "single-family-home")
        params.append(f"property-{mapped_type}")
    
    # Combine parameters
    if params:
        url += "/".join(params)
    
    return url

def build_trulia_url(base_url, location, bedrooms=None, bathrooms=None, price_min=None, price_max=None, home_type=None):
    """Build Trulia search URL with parameters"""
    location_slug = location.replace(", ", "_").replace(" ", "_").lower()
    url = f"{base_url}/{location_slug}/"
    
    params = []
    
    # Add bedrooms
    if bedrooms is not None:
        if str(bedrooms).endswith("+"):
            # Handle "3+" format
            min_beds = bedrooms.rstrip("+")
            params.append(f"beds-{min_beds}p")
        else:
            params.append(f"beds-{bedrooms}")
    
    # Add bathrooms
    if bathrooms is not None:
        if str(bathrooms).endswith("+"):
            # Handle "2+" format
            min_baths = bathrooms.rstrip("+")
            params.append(f"baths-{min_baths}p")
        else:
            params.append(f"baths-{bathrooms}")
    
    # Add price range
    if price_min is not None or price_max is not None:
        price_param = "price-"
        if price_min is not None:
            price_param += str(price_min)
        price_param += "-"
        if price_max is not None:
            price_param += str(price_max)
        params.append(price_param)
    
    # Add home type
    if home_type is not None:
        home_type_map = {
            "house": "single-family-home",
            "apartment": "apartment",
            "condo": "condo",
            "townhouse": "townhome"
        }
        mapped_type = home_type_map.get(home_type.lower(), "single-family-home")
        params.append(f"type-{mapped_type}")
    
    # Combine parameters
    if params:
        url += "_".join(params) + "/"
    
    return url

def build_redfin_url(base_url, location, bedrooms=None, bathrooms=None, price_min=None, price_max=None, home_type=None):
    """Build Redfin search URL with parameters"""
    location_encoded = quote_plus(location)
    url = f"{base_url}/city/{location_encoded}"
    
    params = []
    
    # Add price range
    if price_min is not None or price_max is not None:
        if price_min is not None and price_max is not None:
            params.append(f"min-price={price_min}")
            params.append(f"max-price={price_max}")
        elif price_min is not None:
            params.append(f"min-price={price_min}")
        elif price_max is not None:
            params.append(f"max-price={price_max}")
    
    # Add bedrooms
    if bedrooms is not None:
        if str(bedrooms).endswith("+"):
            min_beds = bedrooms.rstrip("+")
            params.append(f"min-beds={min_beds}")
        else:
            params.append(f"min-beds={bedrooms}")
            params.append(f"max-beds={bedrooms}")
    
    # Add bathrooms
    if bathrooms is not None:
        if str(bathrooms).endswith("+"):
            min_baths = bathrooms.rstrip("+")
            params.append(f"min-baths={min_baths}")
        else:
            params.append(f"min-baths={bathrooms}")
            params.append(f"max-baths={bathrooms}")
    
    # Add home type
    if home_type is not None:
        home_type_map = {
            "house": "type=house",
            "apartment": "type=apartment",
            "condo": "type=condo",
            "townhouse": "type=townhouse"
        }
        mapped_type = home_type_map.get(home_type.lower())
        if mapped_type:
            params.append(mapped_type)
    
    # Combine parameters
    if params:
        url += "?" + "&".join(params)
    
    return url

# Define the websites we'll test
WEBSITES = [
    RealEstateWebsite("Zillow", "https://www.zillow.com", build_zillow_url),
    RealEstateWebsite("Realtor", "https://www.realtor.com", build_realtor_url),
    RealEstateWebsite("Trulia", "https://www.trulia.com", build_trulia_url),
    RealEstateWebsite("Redfin", "https://www.redfin.com", build_redfin_url),
]

# Define test cases with various search criteria
TEST_CASES = [
    {
        "name": "Budget Homes in Detroit",
        "location": "Detroit, MI",
        "bedrooms": "2",
        "bathrooms": "1",
        "price_min": 50000,
        "price_max": 200000,
        "home_type": "house"
    },
    {
        "name": "Luxury Homes in Miami",
        "location": "Miami, FL",
        "bedrooms": "4+",
        "bathrooms": "3+",
        "price_min": 1000000,
        "price_max": 5000000,
        "home_type": "house"
    },
    {
        "name": "Apartments in New York",
        "location": "New York, NY",
        "bedrooms": "1",
        "bathrooms": "1",
        "price_min": 500000,
        "price_max": 1500000,
        "home_type": "apartment"
    },
    {
        "name": "Family Houses in Austin",
        "location": "Austin, TX",
        "bedrooms": "3",
        "bathrooms": "2",
        "price_min": 300000,
        "price_max": 700000,
        "home_type": "house"
    },
    {
        "name": "Condos in San Francisco",
        "location": "San Francisco, CA",
        "bedrooms": "2",
        "bathrooms": "2",
        "price_min": 800000,
        "price_max": 2000000,
        "home_type": "condo"
    },
    {
        "name": "Townhouses in Denver",
        "location": "Denver, CO",
        "bedrooms": "2",
        "bathrooms": "2+",
        "price_min": 400000,
        "price_max": 800000,
        "home_type": "townhouse"
    },
]

async def enhanced_zillow_scrape(browser_agent, url, max_retries=3):
    """
    Enhanced Zillow scraping with multiple retry attempts and specialized bot-bypassing strategies
    """
    print(f"Starting enhanced Zillow scraping with {max_retries} retry attempts...")
    
    for attempt in range(1, max_retries + 1):
        try:
            print(f"Attempt {attempt}/{max_retries} to scrape Zillow")
            
            # Use the existing advanced_zillow_scrape method with a wrapper to add retries
            try:
                # Call the agent's advanced_zillow_scrape method which already handles the page and verification
                listings = await run_browser_agent_method(browser_agent.advanced_zillow_scrape, url)
                
                # If we got listings, return them
                if listings and len(listings) > 0:
                    print(f"Successfully extracted {len(listings)} listings on attempt {attempt}")
                    return listings
                else:
                    print(f"No listings found on attempt {attempt}, continuing...")
            except Exception as e:
                print(f"Error in attempt {attempt}: {str(e)}")
                if attempt < max_retries:
                    # If more attempts are available, continue to the next one
                    delay = random.uniform(5, 10) * attempt  # Exponential backoff
                    print(f"Waiting {delay:.1f} seconds before retry...")
                    await asyncio.sleep(delay)
                else:
                    # If this was the last attempt, try the direct_scrape_website method
                    print("All attempts with advanced_zillow_scrape failed, trying direct_scrape_website...")
                    return await run_browser_agent_method(browser_agent.direct_scrape_website, url)
        except Exception as outer_e:
            print(f"Outer error in attempt {attempt}: {str(outer_e)}")
            if attempt < max_retries:
                delay = random.uniform(5, 10) * attempt
                print(f"Waiting {delay:.1f} seconds before retry...")
                await asyncio.sleep(delay)
            else:
                print(f"All {max_retries} attempts failed. Last error: {str(outer_e)}")
                raise
    
    # This will only execute if all retries fail but no exception is raised
    print("No listings found after all retry attempts")
    return []

async def scrape_website(browser_agent, website, test_case):
    """Scrape a specific website with given test case parameters"""
    start_time = time.time()
    
    # Build the URL for this test case
    url = website.build_url(
        test_case["location"],
        test_case.get("bedrooms"),
        test_case.get("bathrooms"),
        test_case.get("price_min"),
        test_case.get("price_max"),
        test_case.get("home_type")
    )
    
    print(f"\n{'='*80}")
    print(f"Testing: {test_case['name']} on {website.name}")
    print(f"URL: {url}")
    print(f"{'='*80}")
    
    # Log the start of the scrape
    scrape_id = log_scrape(
        website_url=url,
        task_type="real_estate",
        status="started",
        message=f"Started scraping {website.name} for {test_case['name']}",
        raw_data=None,
        error_message=None
    )
    
    try:
        # Choose the appropriate scraping method
        if website.name.lower() == "zillow":
            print(f"Using specialized enhanced_zillow_scrape method for {website.name}")
            # For Zillow, use our enhanced scraper with retries and specialized bypassing
            try:
                listings = await enhanced_zillow_scrape(browser_agent, url)
                print(f"Enhanced Zillow scrape completed. Got {len(listings) if listings else 0} listings")
            except Exception as zillow_error:
                # Log the specific error
                print(f"Error during enhanced_zillow_scrape: {str(zillow_error)}")
                print("Attempting fallback to advanced_zillow_scrape method...")
                # Try fallback to the advanced scraper
                try:
                    listings = await run_browser_agent_method(browser_agent.advanced_zillow_scrape, url)
                    print(f"Advanced Zillow scrape completed. Got {len(listings) if listings else 0} listings")
                except Exception as advanced_error:
                    print(f"Error during advanced_zillow_scrape: {str(advanced_error)}")
                    print("Attempting fallback to direct_scrape_website method...")
                    # Try fallback to the direct scraper as last resort
                    listings = await run_browser_agent_method(browser_agent.direct_scrape_website, url)
                    print(f"Direct scrape fallback completed. Got {len(listings) if listings else 0} listings")
        else:
            print(f"Using direct_scrape_website method for {website.name}")
            # For other sites, use the direct scraper
            listings = await run_browser_agent_method(browser_agent.direct_scrape_website, url)
            print(f"Direct scrape completed. Got {len(listings) if listings else 0} listings")
        
        # Save results to database
        if listings and len(listings) > 0:
            print(f"Found {len(listings)} listings")
            for listing in listings:
                # Add source website to the listing
                if "other" in listing:
                    other_data = json.loads(listing["other"])
                    other_data["website"] = website.name
                    listing["other"] = json.dumps(other_data)
                else:
                    listing["other"] = json.dumps({"website": website.name})
                
                # Insert into database
                listing_id = insert_listing(listing)
                if listing_id:
                    print(f"Saved listing to database with ID: {listing_id}")
            
            # Log the successful scrape
            log_scrape(
                website_url=url,
                task_type="real_estate",
                status="success",
                message=f"Successfully scraped {len(listings)} listings from {website.name}",
                raw_data={"listings": listings},
                error_message=None
            )
        else:
            print(f"No listings found for {website.name}")
            # Log more details about the empty result
            message = f"No listings found for {website.name}. Check if bot protection is active or selectors need updating."
            if website.name.lower() == "zillow":
                message += " Zillow may require enhanced bot protection bypass methods."
            
            log_scrape(
                website_url=url,
                task_type="real_estate",
                status="empty",
                message=message,
                raw_data=None,
                error_message=None
            )
    except Exception as e:
        error_message = str(e)
        print(f"Error scraping {website.name}: {error_message}")
        # Add detailed error logging
        stack_trace = traceback.format_exc()
        print(f"Stack trace: {stack_trace}")
        
        # Log the error with more details
        log_scrape(
            website_url=url,
            task_type="real_estate",
            status="error",
            message=f"Error scraping {website.name}",
            raw_data=None,
            error_message=f"{error_message}\n{stack_trace}"
        )
    
    elapsed_time = time.time() - start_time
    print(f"Time taken: {elapsed_time:.2f} seconds")
    return elapsed_time

async def run_browser_agent_method(method, url):
    """Run a synchronous browser agent method in a separate thread"""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, method, url)

async def run_test_case(test_case, websites=None, debug=False, headless=False, timeout=30000):
    """Run a single test case across all specified websites"""
    # Create browser agent instance with debug settings from command line
    browser_agent = GeminiBrowserAgent(
        gemini_api_key=GEMINI_API_KEY, 
        debug=debug, 
        headless=headless,
        timeout=timeout
    )
    
    # If no websites specified, use all websites
    if websites is None:
        websites = WEBSITES
    
    results = {}
    
    for website in websites:
        try:
            elapsed_time = await scrape_website(browser_agent, website, test_case)
            results[website.name] = {
                "status": "completed",
                "elapsed_time": elapsed_time
            }
            
            # Add a delay between websites to avoid rate limiting
            delay = random.uniform(3.0, 7.0)
            print(f"Waiting {delay:.1f} seconds before next website...")
            await asyncio.sleep(delay)
            
        except Exception as e:
            print(f"Error testing {website.name}: {str(e)}")
            results[website.name] = {
                "status": "error",
                "error": str(e)
            }
    
    return results

async def run_all_tests(test_cases=None, websites=None, debug=False, headless=False, timeout=30000):
    """Run all test cases across all websites"""
    # If no test cases specified, use all test cases
    if test_cases is None:
        test_cases = TEST_CASES
    
    all_results = {}
    
    for i, test_case in enumerate(test_cases):
        print(f"\n[{i+1}/{len(test_cases)}] Running test case: {test_case['name']}")
        results = await run_test_case(test_case, websites, debug=debug, headless=headless, timeout=timeout)
        all_results[test_case['name']] = results
        
        # Add a delay between test cases
        if i < len(test_cases) - 1:
            delay = random.uniform(5.0, 10.0)
            print(f"\nWaiting {delay:.1f} seconds before next test case...")
            await asyncio.sleep(delay)
    
    return all_results

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Test real estate websites with different search criteria')
    parser.add_argument('--website', '-w', choices=[w.name.lower() for w in WEBSITES], 
                        help='Specific website to test (default: all)')
    parser.add_argument('--test-case', '-t', type=int, 
                        help='Specific test case index to run (0-based, default: all)')
    parser.add_argument('--list', '-l', action='store_true',
                        help='List all available test cases and exit')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='Enable debug mode with visual highlighting of elements')
    parser.add_argument('--headless', action='store_true',
                        help='Run in headless mode (no browser UI)')
    parser.add_argument('--timeout', type=int, default=30000,
                        help='Browser navigation timeout in milliseconds (default: 30000)')
    return parser.parse_args()

def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Print available test cases if requested
    if args.list:
        print("\nAvailable test cases:")
        for i, test_case in enumerate(TEST_CASES):
            print(f"[{i}] {test_case['name']}")
            print(f"    Location: {test_case['location']}")
            print(f"    Bedrooms: {test_case.get('bedrooms', 'Any')}")
            print(f"    Bathrooms: {test_case.get('bathrooms', 'Any')}")
            
            # Fix the f-string with backslash issue
            if 'price_min' not in test_case and 'price_max' not in test_case:
                price_display = "Any"
            else:
                min_price = test_case.get("price_min", "Any")
                max_price = test_case.get("price_max", "Any")
                price_display = f"{min_price}-{max_price}"
            print(f"    Price: {price_display}")
            
            print(f"    Home Type: {test_case.get('home_type', 'Any')}")
        print("\nAvailable websites:")
        for website in WEBSITES:
            print(f"- {website.name}")
        return
    
    # Filter websites if specified
    selected_websites = None
    if args.website:
        website_name = args.website.lower()
        selected_websites = [w for w in WEBSITES if w.name.lower() == website_name]
        if not selected_websites:
            print(f"Error: Website '{args.website}' not found")
            return
    
    # Filter test cases if specified
    selected_test_cases = None
    if args.test_case is not None:
        if args.test_case < 0 or args.test_case >= len(TEST_CASES):
            print(f"Error: Test case index {args.test_case} is out of range (0-{len(TEST_CASES)-1})")
            return
        selected_test_cases = [TEST_CASES[args.test_case]]
    
    # Run the selected tests
    try:
        print("\n=== Multi-Website Real Estate Testing ===")
        
        # Show what we're going to test
        if selected_websites:
            print(f"Testing website(s): {', '.join(w.name for w in selected_websites)}")
        else:
            print(f"Testing all {len(WEBSITES)} websites")
        
        if selected_test_cases:
            print(f"Running test case: {selected_test_cases[0]['name']}")
        else:
            print(f"Running all {len(TEST_CASES)} test cases")
        
        # Show debug mode status
        if args.debug:
            print("Debug mode: ENABLED (visual highlighting)")
        else:
            print("Debug mode: DISABLED")
            
        if args.headless:
            print("Headless mode: ENABLED (no browser UI)")
        else:
            print("Headless mode: DISABLED (browser UI visible)")
        
        # Show timeout setting
        print(f"Browser timeout: {args.timeout}ms")
        
        # Run the tests
        results = asyncio.run(run_all_tests(
            selected_test_cases, 
            selected_websites,
            debug=args.debug,
            headless=args.headless,
            timeout=args.timeout
        ))
        
        # Print summary
        print("\n=== Test Results Summary ===")
        for test_name, test_results in results.items():
            print(f"\n{test_name}:")
            for website_name, website_result in test_results.items():
                if website_result.get("status") == "completed":
                    print(f"  {website_name}: Completed in {website_result.get('elapsed_time', 0):.2f} seconds")
                else:
                    print(f"  {website_name}: Error - {website_result.get('error', 'Unknown error')}")
        
        print("\nAll tests completed. Results saved to database.")
        
    except KeyboardInterrupt:
        print("\nTesting interrupted by user.")
    except Exception as e:
        print(f"\nError during testing: {str(e)}")

if __name__ == "__main__":
    main()