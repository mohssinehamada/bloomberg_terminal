import os
import sys
import asyncio
import json
import logging
import time
from typing import Dict, List, Any
import random

# Add the parent directory to the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.browseruse_gemini import GeminiBrowserAgent, handle_zillow_sidebar_scrolling
from playwright.sync_api import sync_playwright

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('zillow_test_results.log')
    ]
)
logger = logging.getLogger(__name__)

# Zillow search parameters
LOCATIONS = [
    "New York, NY",
    "Los Angeles, CA",
    "Chicago, IL",
    "San Francisco, CA",
    "Austin, TX"
]

BEDROOMS = ["1", "2", "3", "4+"]
BATHROOMS = ["1", "2", "3+"]
PRICE_RANGES = [
    "0-300000",
    "300000-600000",
    "600000-900000",
    "900000-1500000"
]

HOME_TYPES = [
    "Houses",
    "Apartments",
    "Condos",
    "Townhomes"
]

def build_zillow_search_url(
    location: str, 
    min_price: str = None, 
    max_price: str = None, 
    bedrooms: str = None, 
    bathrooms: str = None, 
    home_type: str = None
) -> str:
    """
    Build a Zillow search URL with the given parameters.
    
    Args:
        location: Location to search in (city, state)
        min_price: Minimum price (optional)
        max_price: Maximum price (optional)
        bedrooms: Number of bedrooms (optional)
        bathrooms: Number of bathrooms (optional)
        home_type: Type of home (optional)
        
    Returns:
        str: Zillow search URL
    """
    # Base Zillow URL
    base_url = "https://www.zillow.com/homes/"
    
    # Format the location for the URL
    location_slug = location.replace(", ", "-").replace(" ", "-").lower()
    url = f"{base_url}for_sale/{location_slug}/"
    
    # Add query parameters
    params = []
    
    if min_price and max_price:
        params.append(f"price={min_price}-{max_price}")
    elif min_price:
        params.append(f"price={min_price}-")
    elif max_price:
        params.append(f"price=-{max_price}")
    
    if bedrooms:
        params.append(f"beds-{bedrooms}")
    
    if bathrooms:
        params.append(f"baths-{bathrooms}")
    
    if home_type:
        params.append(f"home-type-{home_type.lower()}")
    
    # Add query parameters to URL
    if params:
        url += "_" + "_".join(params) + "_/"
    
    return url

def parse_price_range(price_range: str) -> tuple:
    """Parse a price range string into min and max values."""
    if "-" in price_range:
        parts = price_range.split("-")
        return parts[0], parts[1]
    return None, None

async def test_agent_with_criteria(criteria: Dict[str, str]) -> Dict[str, Any]:
    """
    Test the agent with the given search criteria.
    
    Args:
        criteria: Dictionary of search criteria
        
    Returns:
        Dict: Results of the test
    """
    try:
        # Build the Zillow URL
        min_price, max_price = parse_price_range(criteria.get("price_range", ""))
        url = build_zillow_search_url(
            location=criteria["location"],
            min_price=min_price,
            max_price=max_price,
            bedrooms=criteria.get("bedrooms"),
            bathrooms=criteria.get("bathrooms"),
            home_type=criteria.get("home_type")
        )
        
        logger.info(f"Testing with URL: {url}")
        logger.info(f"Criteria: {criteria}")
        
        # Create a dedicated test function that just tests the scrolling
        test_sidebar_scrolling(url, criteria)
        
        # Initialize the agent
        agent = GeminiBrowserAgent()
        
        # Execute the task
        start_time = time.time()
        result = await agent.execute_task(websites={url: "real_estate"})
        elapsed_time = time.time() - start_time
        
        # Process and return the results
        success = bool(result and result.get('output'))
        listings_count = 0
        
        if success and isinstance(result.get('output'), dict) and 'listings' in result['output']:
            listings_count = len(result['output']['listings'])
        elif success and isinstance(result.get('output'), str) and 'listings' in result['output']:
            # Try to parse JSON from the output string
            try:
                parsed = json.loads(result['output'])
                if 'listings' in parsed:
                    listings_count = len(parsed['listings'])
            except:
                pass
        
        test_result = {
            "criteria": criteria,
            "url": url,
            "success": success,
            "listings_count": listings_count,
            "elapsed_time": elapsed_time,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        logger.info(f"Test completed: Success={success}, Listings={listings_count}, Time={elapsed_time:.2f}s")
        return test_result
    
    except Exception as e:
        logger.error(f"Error testing with criteria {criteria}: {e}")
        return {
            "criteria": criteria,
            "error": str(e),
            "success": False,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }

def test_sidebar_scrolling(url, criteria):
    """
    Test specifically the sidebar scrolling functionality on Zillow.
    
    Args:
        url: The Zillow URL to test
        criteria: The search criteria used
    """
    logger.info(f"Testing sidebar scrolling on {url}")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  # Visible browser for debugging
            page = browser.new_page(
                viewport={"width": 1280, "height": 720},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36"
            )
            
            # Navigate to Zillow
            logger.info(f"Navigating to {url}")
            page.goto(url)
            page.wait_for_load_state("networkidle")
            
            # Take a screenshot before scrolling
            screenshot_path = f"zillow_before_scroll_{time.strftime('%Y%m%d_%H%M%S')}.png"
            page.screenshot(path=screenshot_path)
            logger.info(f"Saved screenshot before scrolling: {screenshot_path}")
            
            # Handle any popups or cookie banners
            for selector in ["button:has-text('Accept')", "button:has-text('I Agree')", "button:has-text('OK')"]:
                try:
                    if page.locator(selector).is_visible(timeout=2000):
                        page.locator(selector).click()
                        page.wait_for_timeout(1000)
                except:
                    pass
            
            # Test the sidebar scrolling function
            sidebar_scrolled = handle_zillow_sidebar_scrolling(page)
            
            # Take a screenshot after scrolling
            screenshot_path = f"zillow_after_scroll_{time.strftime('%Y%m%d_%H%M%S')}.png"
            page.screenshot(path=screenshot_path)
            logger.info(f"Saved screenshot after scrolling: {screenshot_path}")
            
            # Log the result
            if sidebar_scrolled:
                logger.info("✅ Successfully scrolled sidebar")
            else:
                logger.warning("❌ Failed to scroll sidebar")
            
            # Close the browser
            browser.close()
            
            return sidebar_scrolled
            
    except Exception as e:
        logger.error(f"Error testing sidebar scrolling: {e}")
        return False

async def run_test_suite(num_tests: int = 5) -> List[Dict[str, Any]]:
    """
    Run a test suite with different combinations of search criteria.
    
    Args:
        num_tests: Number of test combinations to run
        
    Returns:
        List: List of test results
    """
    results = []
    
    # Generate random combinations of search criteria
    test_combinations = []
    
    for _ in range(num_tests):
        criteria = {
            "location": random.choice(LOCATIONS),
            "price_range": random.choice(PRICE_RANGES),
            "bedrooms": random.choice(BEDROOMS),
            "bathrooms": random.choice(BATHROOMS),
            "home_type": random.choice(HOME_TYPES)
        }
        test_combinations.append(criteria)
    
    # Run each test
    for criteria in test_combinations:
        logger.info(f"Starting test with criteria: {criteria}")
        result = await test_agent_with_criteria(criteria)
        results.append(result)
        
        # Save results after each test
        with open("zillow_test_results.json", "w") as f:
            json.dump(results, f, indent=2)
        
        # Add delay between tests
        delay = random.uniform(5, 10)
        logger.info(f"Waiting {delay:.2f} seconds before next test...")
        await asyncio.sleep(delay)
    
    return results

def run_specific_tests():
    """Run specific predefined tests to check challenging search combinations."""
    specific_tests = [
        {
            "location": "New York, NY",
            "price_range": "0-1500000",
            "bedrooms": "1",
            "bathrooms": "1",
            "home_type": "Apartments",
            "description": "Small apartments in New York City"
        },
        {
            "location": "San Francisco, CA",
            "price_range": "900000-1500000",
            "bedrooms": "3",
            "bathrooms": "2+",
            "home_type": "Houses",
            "description": "Luxury homes in San Francisco"
        },
        {
            "location": "Austin, TX",
            "price_range": "300000-600000",
            "bedrooms": "4+",
            "bathrooms": "3+",
            "home_type": "Houses",
            "description": "Large family homes in Austin"
        },
    ]
    
    async def run_tests():
        results = []
        for test in specific_tests:
            description = test.pop("description")
            logger.info(f"Running test: {description}")
            result = await test_agent_with_criteria(test)
            result["description"] = description
            results.append(result)
        return results
    
    return asyncio.run(run_tests())

def run_sidebar_test():
    """Run just the sidebar scroll test on a predefined URL."""
    test = {
        "location": "New York, NY",
        "price_range": "0-1500000",
        "bedrooms": "1",
        "bathrooms": "1",
        "home_type": "Apartments",
    }
    
    # Build the URL
    min_price, max_price = parse_price_range(test.get("price_range", ""))
    url = build_zillow_search_url(
        location=test["location"],
        min_price=min_price,
        max_price=max_price,
        bedrooms=test.get("bedrooms"),
        bathrooms=test.get("bathrooms"),
        home_type=test.get("home_type")
    )
    
    print(f"\nTesting sidebar scrolling on {url}")
    result = test_sidebar_scrolling(url, test)
    
    if result:
        print("✅ Successfully tested sidebar scrolling")
    else:
        print("❌ Failed sidebar scrolling test")
    
    print("\nCheck the generated screenshots to see the results.")

def main():
    """Main entry point."""
    print("\n=== Zillow Web Agent Test Suite ===")
    print("1. Run random test combinations")
    print("2. Run specific predefined tests")
    print("3. Run a custom test")
    print("4. Test only sidebar scrolling")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    if choice == "1":
        num_tests = int(input("Enter number of random test combinations to run: "))
        results = asyncio.run(run_test_suite(num_tests))
        
        # Print summary
        success_count = sum(1 for r in results if r["success"])
        print(f"\nCompleted {len(results)} tests. Success rate: {success_count}/{len(results)}")
        
    elif choice == "2":
        results = run_specific_tests()
        
        # Print summary
        for result in results:
            status = "✅ Success" if result["success"] else "❌ Failed"
            listings = result.get("listings_count", 0)
            description = result.get("description", "")
            print(f"{status} - {description}: Found {listings} listings")
            
    elif choice == "3":
        # Custom test
        print("\n--- Custom Test ---")
        location = input("Enter location (e.g., 'New York, NY'): ")
        price_min = input("Enter minimum price (leave blank for none): ")
        price_max = input("Enter maximum price (leave blank for none): ")
        bedrooms = input("Enter number of bedrooms (e.g., '2', '3+', or leave blank): ")
        bathrooms = input("Enter number of bathrooms (e.g., '2', '3+', or leave blank): ")
        home_type = input("Enter home type (e.g., 'Houses', 'Apartments', or leave blank): ")
        
        price_range = ""
        if price_min and price_max:
            price_range = f"{price_min}-{price_max}"
        
        criteria = {
            "location": location,
            "price_range": price_range,
            "bedrooms": bedrooms or None,
            "bathrooms": bathrooms or None,
            "home_type": home_type or None
        }
        
        # Remove None values
        criteria = {k: v for k, v in criteria.items() if v is not None}
        
        # Run the test
        result = asyncio.run(test_agent_with_criteria(criteria))
        
        # Print result
        print("\nTest Result:")
        print(f"URL: {result['url']}")
        print(f"Success: {'Yes' if result['success'] else 'No'}")
        print(f"Listings found: {result.get('listings_count', 0)}")
        print(f"Time taken: {result.get('elapsed_time', 0):.2f} seconds")
    
    elif choice == "4":
        run_sidebar_test()
    
    else:
        print("Invalid choice.")

if __name__ == "__main__":
    main() 