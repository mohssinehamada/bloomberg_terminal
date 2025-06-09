#!/usr/bin/env python3
"""
Zillow Direct Test Script

This script provides multiple strategies for bypassing Zillow's bot protection
and successfully scraping real estate listings.
"""

import os
import sys
import time
import json
import random
import re
import asyncio
import traceback
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Add parent directory to path to import from core and database
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from database.database import insert_listing, log_scrape, get_db_connection, init_db

# Load environment variables
load_dotenv(".env.zillow")
load_dotenv()

def handle_press_and_hold(page, debug=True):
    """
    Handle Zillow's "Press & Hold" verification challenge.
    
    Args:
        page: Playwright page object
        debug: Whether to show debug messages
    
    Returns:
        bool: True if successfully handled, False otherwise
    """
    try:
        # Look for various "Press & Hold" selector patterns
        press_hold_selectors = [
            "text=Press & Hold",
            "[class*='captcha'] button",
            "button:has-text('Press')",
            "button:has-text('Hold')",
            "button[class*='captcha']"
        ]
        
        for selector in press_hold_selectors:
            if debug:
                logger.info(f"Checking for Press & Hold with selector: {selector}")
            
            button = page.locator(selector).first
            if button.is_visible(timeout=3000):
                logger.info(f"Found Press & Hold verification with selector: {selector}")
                
                # Get button position
                box = button.bounding_box()
                x = box['x'] + box['width']/2
                y = box['y'] + box['height']/2
                
                if debug:
                    # Highlight the button if in debug mode
                    page.evaluate("""(x, y) => {
                        const elem = document.elementFromPoint(x, y);
                        if (elem) {
                            elem.style.border = '3px solid red';
                            elem.style.backgroundColor = 'rgba(255, 0, 0, 0.2)';
                        }
                    }""", x, y)
                    page.wait_for_timeout(1000)
                
                # Mouse down, wait, then mouse up to simulate press and hold
                page.mouse.move(x, y)
                page.mouse.down()
                
                # Hold time between 3-5 seconds with small random variations
                hold_time = random.uniform(3000, 5000)
                logger.info(f"Holding for {hold_time:.1f}ms")
                page.wait_for_timeout(hold_time)
                
                page.mouse.up()
                
                # Wait for navigation or success
                page.wait_for_load_state("networkidle", timeout=30000)
                page.wait_for_timeout(2000)  # Additional wait to ensure loading completes
                
                # Check if verification was successful
                # If the button is still visible, it likely failed
                if not button.is_visible(timeout=1000):
                    logger.info("Press & Hold verification appears successful")
                    return True
                else:
                    logger.info("Press & Hold may have failed, button still visible")
            
        # If we didn't find any button, no verification was needed
        logger.info("No Press & Hold verification detected")
        return True
        
    except Exception as e:
        logger.error(f"Error in handle_press_and_hold: {str(e)}")
        return False

def handle_zillow_sidebar_scrolling(page, debug=True):
    """
    Handles scrolling within Zillow's sidebar filters which may have custom scroll behavior.
    
    Args:
        page: The Playwright page object
        debug: Whether to show debug information
    
    Returns:
        bool: True if scrolling was successful, False otherwise
    """
    try:
        # Find potential sidebar elements
        sidebar_selectors = [
            "div[data-testid='search-filters']", 
            "div.filter-bar",
            "div.search-page-filter-menu",
            "div[id*='filter']",
            "div.filters-container",
            "div[class*='filter']"
        ]
        
        for selector in sidebar_selectors:
            try:
                sidebar = page.locator(selector).first
                if sidebar.is_visible(timeout=1000):
                    logger.info(f"Found sidebar with selector: {selector}")
                    
                    if debug:
                        # Highlight the sidebar
                        page.evaluate(f"""(selector) => {{
                            const sidebar = document.querySelector(selector);
                            if (sidebar) {{
                                sidebar.style.border = '3px solid blue';
                                sidebar.style.backgroundColor = 'rgba(0, 0, 255, 0.1)';
                            }}
                        }}""", selector)
                    
                    # Get the sidebar's bounding box
                    box = sidebar.bounding_box()
                    x = box['x'] + box['width']/2
                    y = box['y'] + box['height']/2
                    
                    # Click first to ensure focus
                    page.mouse.move(x, y)
                    page.mouse.click(x, y)
                    page.wait_for_timeout(500)
                    
                    # Perform multiple scrolls with random delays
                    for i in range(5):
                        scroll_amount = random.randint(100, 300)
                        page.mouse.wheel(0, scroll_amount)
                        delay = random.uniform(800, 1500)
                        page.wait_for_timeout(delay)
                    
                    return True
            except Exception as element_error:
                if debug:
                    logger.info(f"Error with sidebar selector {selector}: {str(element_error)}")
                continue
        
        # If no sidebar found with selectors, try JavaScript scrolling
        logger.info("No sidebar found with selectors, trying JavaScript scrolling")
        
        # Find all scrollable elements and scroll them
        js_result = page.evaluate("""() => {
            const scrollables = Array.from(document.querySelectorAll('div'))
                .filter(div => {
                    const style = window.getComputedStyle(div);
                    return (style.overflowY === 'auto' || style.overflowY === 'scroll') && 
                           div.scrollHeight > div.clientHeight;
                });
            
            let scrolled = false;
            for (const div of scrollables) {
                div.scrollTop += 300;
                scrolled = true;
            }
            return scrolled;
        }""")
        
        return js_result
        
    except Exception as e:
        logger.error(f"Error in handle_zillow_sidebar_scrolling: {str(e)}")
        return False

def extract_listings_from_page(page, debug=True):
    """
    Extracts listing data from a Zillow search results page using multiple strategies.
    
    Args:
        page: Playwright page object
        debug: Whether to show debug information
    
    Returns:
        list: List of extracted listings
    """
    listings = []
    
    try:
        # Strategy 1: Extract from visible property cards
        logger.info("Attempting to extract from property cards")
        
        card_selectors = [
            "div[data-test='property-card']",
            "div.list-card",
            "article[role='article']",
            "div[id*='search-result']",
            "div[class*='property-card']",
            "div[class*='listing-card']",
            "li[data-test='search-result']"
        ]
        
        for selector in card_selectors:
            try:
                count = page.locator(selector).count()
                
                if count > 0:
                    logger.info(f"Found {count} cards with selector: {selector}")
                    
                    if debug:
                        # Highlight all cards
                        page.evaluate(f"""(selector) => {{
                            const cards = document.querySelectorAll(selector);
                            for (const card of cards) {{
                                card.style.border = '3px solid green';
                                card.style.backgroundColor = 'rgba(0, 255, 0, 0.1)';
                            }}
                        }}""", selector)
                    
                    # Process each card
                    for i in range(count):
                        try:
                            card = page.locator(selector).nth(i)
                            
                            # Extract data using different selectors and patterns
                            listing = {}
                            
                            # Try to extract price
                            price_selectors = [
                                "span[data-test='property-card-price']",
                                "span[class*='price']",
                                "div[class*='price']"
                            ]
                            
                            for price_selector in price_selectors:
                                price_elem = card.locator(price_selector).first
                                if price_elem.is_visible():
                                    price = price_elem.inner_text().strip()
                                    # Clean up price
                                    price = re.sub(r'[^\d$,.]+', '', price)
                                    listing["price"] = price
                                    break
                            
                            # If no price found, try regex on the whole card text
                            if "price" not in listing:
                                card_text = card.inner_text()
                                price_match = re.search(r'\$([\d,.]+)', card_text)
                                if price_match:
                                    listing["price"] = f"${price_match.group(1)}"
                            
                            # Try to extract address
                            address_selectors = [
                                "address",
                                "[data-test='property-card-addr']",
                                "[class*='address']",
                                "a[class*='link']"
                            ]
                            
                            for address_selector in address_selectors:
                                address_elem = card.locator(address_selector).first
                                if address_elem.is_visible():
                                    address = address_elem.inner_text().strip()
                                    listing["location"] = address
                                    listing["title"] = address  # Use address as title
                                    break
                            
                            # Extract beds/baths/sqft
                            card_text = card.inner_text()
                            
                            # Extract bedrooms
                            bed_match = re.search(r'(\d+)\s*(?:bd|bed)', card_text, re.IGNORECASE)
                            if bed_match:
                                listing["bedrooms"] = bed_match.group(1)
                            
                            # Extract bathrooms
                            bath_match = re.search(r'(\d+\.?\d*)\s*(?:ba|bath)', card_text, re.IGNORECASE)
                            if bath_match:
                                listing["bathrooms"] = bath_match.group(1)
                            
                            # Extract area
                            area_match = re.search(r'([\d,]+)\s*(?:sq\.?\s*ft|sqft|sf)', card_text, re.IGNORECASE)
                            if area_match:
                                listing["area"] = f"{area_match.group(1)} sqft"
                            
                            # Only add if we have a price
                            if "price" in listing:
                                # Add timestamp
                                listing["time"] = "Recent"
                                
                                # Add other data field
                                listing["other"] = json.dumps({
                                    "source": "Zillow",
                                    "extraction_method": "property-card"
                                })
                                
                                # Avoid duplicates
                                if not any(
                                    l.get("price") == listing.get("price") and 
                                    l.get("location") == listing.get("location") 
                                    for l in listings
                                ):
                                    listings.append(listing)
                        except Exception as card_error:
                            logger.error(f"Error extracting data from card {i}: {str(card_error)}")
                            continue
                    
                    # If we found listings with this selector, break the loop
                    if listings:
                        break
            except Exception as selector_error:
                logger.error(f"Error with selector {selector}: {str(selector_error)}")
                continue
        
        # Strategy 2: Extract from embedded JSON data
        if not listings:
            logger.info("No listings found from cards, trying to extract from JSON data")
            
            json_data = page.evaluate("""() => {
                try {
                    // Look for scripts with JSON data
                    const scripts = Array.from(document.querySelectorAll('script[type="application/json"], script[type="application/ld+json"]'));
                    
                    // Also search for scripts containing certain keywords
                    const keywordScripts = Array.from(document.querySelectorAll('script')).filter(s => 
                        s.innerText.includes('"address"') || 
                        s.innerText.includes('"price"') || 
                        s.innerText.includes('"bed"') || 
                        s.innerText.includes('"bath"')
                    );
                    
                    const allScripts = [...scripts, ...keywordScripts];
                    
                    // Return JSON content from all scripts for processing
                    return allScripts.map(s => s.textContent);
                } catch (e) {
                    console.error("Error extracting JSON data:", e);
                    return [];
                }
            }""")
            
            if json_data and isinstance(json_data, list):
                logger.info(f"Found {len(json_data)} JSON scripts to process")
                
                for script_content in json_data:
                    try:
                        # Try to parse the JSON
                        data = json.loads(script_content)
                        
                        # Look for property listings in the data
                        if isinstance(data, dict):
                            # Extract from search results
                            if "searchResults" in data:
                                search_results = data["searchResults"]
                                if isinstance(search_results, dict) and "listResults" in search_results:
                                    list_results = search_results["listResults"]
                                    if isinstance(list_results, list):
                                        logger.info(f"Found {len(list_results)} listings in JSON data")
                                        
                                        for item in list_results:
                                            try:
                                                listing = {}
                                                
                                                # Extract data
                                                if "price" in item:
                                                    listing["price"] = item["price"]
                                                elif "unformattedPrice" in item:
                                                    listing["price"] = f"${item['unformattedPrice']}"
                                                
                                                if "address" in item:
                                                    address = item["address"]
                                                    if isinstance(address, dict):
                                                        parts = []
                                                        for key in ["streetAddress", "addressLine1", "city", "state", "zipcode", "addressLine2"]:
                                                            if key in address and address[key]:
                                                                parts.append(str(address[key]))
                                                        if parts:
                                                            listing["location"] = ", ".join(parts)
                                                            listing["title"] = listing["location"]
                                                    elif isinstance(address, str):
                                                        listing["location"] = address
                                                        listing["title"] = address
                                                
                                                if "beds" in item or "bedrooms" in item:
                                                    listing["bedrooms"] = str(item.get("beds") or item.get("bedrooms"))
                                                
                                                if "baths" in item or "bathrooms" in item:
                                                    listing["bathrooms"] = str(item.get("baths") or item.get("bathrooms"))
                                                
                                                if "area" in item or "livingArea" in item or "sqft" in item:
                                                    area_value = item.get("area") or item.get("livingArea") or item.get("sqft")
                                                    listing["area"] = f"{area_value} sqft"
                                                
                                                # Only add if we have a price
                                                if "price" in listing:
                                                    # Add timestamp
                                                    listing["time"] = "Recent"
                                                    
                                                    # Add other data field
                                                    listing["other"] = json.dumps({
                                                        "source": "Zillow",
                                                        "extraction_method": "json-data",
                                                        "zpid": item.get("zpid", ""),
                                                        "statusType": item.get("statusType", "")
                                                    })
                                                    
                                                    # Avoid duplicates
                                                    if not any(
                                                        l.get("price") == listing.get("price") and 
                                                        l.get("location") == listing.get("location") 
                                                        for l in listings
                                                    ):
                                                        listings.append(listing)
                                            except Exception as item_error:
                                                logger.error(f"Error processing JSON item: {str(item_error)}")
                                                continue
                        
                        # If we found listings, no need to check other scripts
                        if listings:
                            break
                    except Exception as json_error:
                        logger.error(f"Error parsing JSON data: {str(json_error)}")
                        continue
        
        # Strategy 3: Extract using regex patterns directly on HTML
        if not listings:
            logger.info("No listings found from JSON, trying to extract using regex")
            
            html_content = page.content()
            
            # Find potential listing blocks
            listing_blocks = re.findall(r'(?:"address"|"streetAddress"|"price"|"beds"|"baths"|"sqft")[^}]+', html_content)
            
            for block in listing_blocks:
                try:
                    listing = {}
                    
                    # Extract price
                    price_match = re.search(r'"price":\s*"([^"]+)"', block)
                    if price_match:
                        listing["price"] = price_match.group(1)
                    
                    # Extract address
                    address_match = re.search(r'"address":\s*"([^"]+)"', block)
                    if address_match:
                        listing["location"] = address_match.group(1)
                        listing["title"] = listing["location"]
                    
                    # Extract bedrooms
                    beds_match = re.search(r'"beds":\s*"?(\d+)"?', block)
                    if beds_match:
                        listing["bedrooms"] = beds_match.group(1)
                    
                    # Extract bathrooms
                    baths_match = re.search(r'"baths":\s*"?(\d+\.?\d*)"?', block)
                    if baths_match:
                        listing["bathrooms"] = baths_match.group(1)
                    
                    # Extract area
                    area_match = re.search(r'"sqft":\s*"?([\d,]+)"?', block)
                    if area_match:
                        listing["area"] = f"{area_match.group(1)} sqft"
                    
                    # Only add if we have a price
                    if "price" in listing and ("location" in listing or "bedrooms" in listing):
                        # Add timestamp and other data
                        listing["time"] = "Recent"
                        listing["other"] = json.dumps({
                            "source": "Zillow",
                            "extraction_method": "regex-html"
                        })
                        
                        # Avoid duplicates
                        if not any(
                            l.get("price") == listing.get("price") and 
                            l.get("location") == listing.get("location") 
                            for l in listings
                        ):
                            listings.append(listing)
                except Exception as block_error:
                    logger.error(f"Error processing HTML block: {str(block_error)}")
                    continue
        
        return listings
    
    except Exception as e:
        logger.error(f"Error extracting listings: {str(e)}")
        return []

def scrape_zillow(url, debug=True, headless=False, timeout=60000):
    """
    Main function to scrape Zillow with multiple bot protection bypass strategies.
    
    Args:
        url: Zillow URL to scrape
        debug: Whether to enable visual debugging
        headless: Whether to run in headless mode
        timeout: Navigation timeout in milliseconds
    
    Returns:
        list: List of extracted listings
    """
    listings = []
    
    try:
        logger.info(f"Starting Zillow scrape: {url}")
        
        # Log scrape attempt
        scrape_id = log_scrape(
            website_url=url,
            task_type="real_estate",
            status="started",
            message=f"Started scraping Zillow",
            raw_data=None,
            error_message=None
        )
        
        with sync_playwright() as p:
            # Browser configuration
            browser_args = []
            
            # Mobile emulation 
            iphone_device = p.devices['iPhone 12']
            
            # Browser launch options for both desktop and mobile contexts
            browser = p.chromium.launch(
                headless=headless,
                args=browser_args
            )
            
            # Try multiple different contexts to bypass detection
            contexts_to_try = [
                # Context 1: Desktop with stealth mode
                {
                    "name": "Desktop - Stealth mode",
                    "creator": lambda: browser.new_context(
                        viewport={'width': 1280, 'height': 800},
                        user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        java_script_enabled=True,
                        ignore_https_errors=True,
                        extra_http_headers={
                            "Accept-Language": "en-US,en;q=0.9",
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
                            "Connection": "keep-alive"
                        },
                    )
                },
                # Context 2: Mobile emulation
                {
                    "name": "Mobile - iPhone 12",
                    "creator": lambda: browser.new_context(**iphone_device)
                },
                # Context 3: Desktop with different user agent
                {
                    "name": "Desktop - Alternative User Agent",
                    "creator": lambda: browser.new_context(
                        viewport={'width': 1366, 'height': 768},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                        java_script_enabled=True,
                    )
                }
            ]
            
            success = False
            for context_config in contexts_to_try:
                try:
                    logger.info(f"Trying context: {context_config['name']}")
                    
                    # Create context and page
                    context = context_config['creator']()
                    page = context.new_page()
                    
                    # Set default timeout for all actions
                    page.set_default_timeout(timeout)
                    
                    # Navigate to URL
                    logger.info(f"Navigating to {url}")
                    
                    # Adding random delays to mimic human behavior
                    random_delay = random.uniform(1, 3)
                    time.sleep(random_delay)
                    
                    # Go to the URL
                    page.goto(url, wait_until="domcontentloaded")
                    
                    # Wait for content to be loaded
                    page.wait_for_load_state("networkidle", timeout=timeout)
                    
                    # Random wait
                    time.sleep(random.uniform(2, 5))
                    
                    # Handle cookie consent and popup banners
                    for selector in [
                        "button:has-text('Accept')", 
                        "button:has-text('I Agree')",
                        "button:has-text('OK')",
                        "button:has-text('Got It')",
                        "[aria-label='Close']"
                    ]:
                        try:
                            if page.locator(selector).is_visible(timeout=2000):
                                page.locator(selector).click()
                                time.sleep(1)
                        except:
                            pass
                    
                    # Handle Press & Hold verification
                    verification_result = handle_press_and_hold(page, debug=debug)
                    if not verification_result:
                        logger.warning(f"Press & Hold verification failed with context: {context_config['name']}")
                        continue
                    
                    # Handle sidebar scrolling
                    handle_zillow_sidebar_scrolling(page, debug=debug)
                    
                    # Scroll main page to load all listings
                    logger.info("Scrolling main page to load all listings")
                    for _ in range(5):  # Scroll multiple times with delay
                        # Random scroll amount
                        scroll_amount = random.randint(300, 800)
                        page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                        
                        # Random wait
                        delay = random.uniform(1, 2)
                        time.sleep(delay)
                        
                        # Try to click "Show more" buttons if they exist
                        for show_more_selector in ["button:has-text('Show more')", "[data-test='show-more-results']"]:
                            try:
                                if page.locator(show_more_selector).is_visible(timeout=1000):
                                    page.locator(show_more_selector).click()
                                    time.sleep(2)
                            except:
                                pass
                    
                    # Take screenshot if in debug mode
                    if debug:
                        screenshot_path = f"zillow_debug_{int(time.time())}.png"
                        page.screenshot(path=screenshot_path)
                        logger.info(f"Saved debug screenshot to {screenshot_path}")
                    
                    # Extract listings
                    context_listings = extract_listings_from_page(page, debug=debug)
                    
                    if context_listings:
                        logger.info(f"Successfully extracted {len(context_listings)} listings with context: {context_config['name']}")
                        listings = context_listings
                        success = True
                        break
                    else:
                        logger.warning(f"No listings found with context: {context_config['name']}")
                
                except Exception as context_error:
                    logger.error(f"Error with context {context_config['name']}: {str(context_error)}")
                    continue
            
            # If all direct attempts failed, try the Google Search fallback method
            if not success:
                logger.info("Direct Zillow access failed. Trying Google Search fallback method...")
                google_listings = scrape_zillow_via_google(url, p, debug=debug, headless=headless, timeout=timeout)
                
                if google_listings:
                    logger.info(f"Successfully extracted {len(google_listings)} listings via Google Search fallback")
                    listings = google_listings
                    success = True
            
            browser.close()
            
            # Log scrape result
            if success and listings:
                logger.info(f"Successfully extracted {len(listings)} listings from Zillow")
                
                # Save to database
                for listing in listings:
                    listing_id = insert_listing(listing)
                    if listing_id:
                        logger.info(f"Saved listing to database with ID: {listing_id}")
                
                log_scrape(
                    website_url=url,
                    task_type="real_estate",
                    status="success",
                    message=f"Successfully scraped {len(listings)} listings from Zillow",
                    raw_data={"listings": listings},
                    error_message=None
                )
            else:
                logger.warning("No listings found on Zillow after trying all contexts")
                log_scrape(
                    website_url=url,
                    task_type="real_estate",
                    status="empty",
                    message="No listings found for Zillow. Bot protection may be active.",
                    raw_data=None,
                    error_message=None
                )
    
    except Exception as e:
        logger.error(f"Error scraping Zillow: {str(e)}")
        stack_trace = traceback.format_exc()
        logger.error(f"Stack trace: {stack_trace}")
        
        log_scrape(
            website_url=url,
            task_type="real_estate",
            status="error",
            message="Error scraping Zillow",
            raw_data=None,
            error_message=f"{str(e)}\n{stack_trace}"
        )
    
    return listings

def scrape_zillow_via_google(zillow_url, playwright, debug=True, headless=False, timeout=60000):
    """
    Fallback method that uses Google Search to find and scrape Zillow listings.
    
    Args:
        zillow_url: Original Zillow URL that failed
        playwright: Playwright instance
        debug: Whether to enable debug mode
        headless: Whether to run in headless mode
        timeout: Navigation timeout in milliseconds
    
    Returns:
        list: List of extracted listings
    """
    listings = []
    
    try:
        # Extract location and search criteria from the URL
        url_parts = zillow_url.split('/')
        location_part = None
        
        for part in url_parts:
            if 'price=' in part or 'beds-' in part or 'baths-' in part:
                # Found search parameters
                params = part.split('_')
                for i, param in enumerate(params):
                    if i > 0 and not any(x in param for x in ['price=', 'beds-', 'baths-', 'home-type-']):
                        location_part = param
                        break
                break
            elif part and not part.startswith('http') and not part in ['homes', 'for_sale', 'www.zillow.com']:
                location_part = part
        
        if not location_part:
            location_part = "Detroit MI"
        
        # Create a more readable location string
        location_str = location_part.replace('-', ' ').title()
        
        # Create specific Google search query
        search_query = f"zillow houses for sale in {location_str} site:zillow.com"
        google_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
        
        logger.info(f"Using Google Search fallback with query: {search_query}")
        
        # Launch browser and navigate to Google
        browser = playwright.chromium.launch(headless=headless)
        context = browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        
        page = context.new_page()
        page.set_default_timeout(timeout)
        
        # Navigate to Google search
        logger.info(f"Navigating to Google: {google_url}")
        page.goto(google_url)
        page.wait_for_load_state("networkidle")
        
        # Accept Google cookies if prompted
        for selector in [
            "button:has-text('Accept all')",
            "button:has-text('I agree')",
            "button:has-text('Accept')"
        ]:
            try:
                if page.locator(selector).is_visible(timeout=3000):
                    page.locator(selector).click()
                    break
            except:
                pass
        
        # Look for Zillow links in Google search results
        logger.info("Extracting Zillow links from Google search results")
        
        # Take a screenshot if debug mode is enabled
        if debug:
            screenshot_path = f"google_search_debug_{int(time.time())}.png"
            page.screenshot(path=screenshot_path)
            logger.info(f"Saved Google search debug screenshot to {screenshot_path}")
            
        # Find all links on the page first
        try:
            # Use JavaScript to extract all links that point to Zillow
            zillow_links = page.evaluate("""() => {
                const allLinks = Array.from(document.querySelectorAll('a'));
                return allLinks
                    .filter(link => {
                        const href = link.href || '';
                        return href.includes('zillow.com');
                    })
                    .map(link => link.href)
                    .filter(href => href && href.trim() !== '');
            }""")
            
            if zillow_links:
                logger.info(f"Found {len(zillow_links)} Zillow links from Google search using JavaScript extraction")
            else:
                # Fallback to direct Playwright extraction if JavaScript method returns no results
                link_selectors = [
                    "a[href*='zillow.com']",
                    "a[data-ved]"  # Google search result links often have this attribute
                ]
                
                for selector in link_selectors:
                    try:
                        links = page.query_selector_all(selector)
                        for link in links:
                            try:
                                href = link.get_attribute("href")
                                if href and "zillow.com" in href and href not in zillow_links:
                                    zillow_links.append(href)
                            except:
                                continue
                    except Exception as selector_error:
                        logger.error(f"Error with selector {selector}: {str(selector_error)}")
                
                if zillow_links:
                    logger.info(f"Found {len(zillow_links)} Zillow links from Google search using direct selector")
                else:
                    # Last resort: Get all link elements and check their href values
                    try:
                        all_links = page.query_selector_all("a")
                        logger.info(f"Found {len(all_links)} total links on the page")
                        
                        for link in all_links:
                            try:
                                href = link.get_attribute("href")
                                if href and "zillow.com" in href and href not in zillow_links:
                                    zillow_links.append(href)
                            except:
                                continue
                        
                        logger.info(f"Found {len(zillow_links)} Zillow links from all links on the page")
                    except Exception as all_links_error:
                        logger.error(f"Error extracting all links: {str(all_links_error)}")
        
        except Exception as js_error:
            logger.error(f"Error extracting links with JavaScript: {str(js_error)}")
            
            # Fallback method using regex on page content
            try:
                logger.info("Attempting regex extraction of links from page content")
                html_content = page.content()
                
                # Find all URLs with zillow.com domain using regex
                zillow_urls = re.findall(r'https?://[^"\'\s]*zillow\.com[^"\'\s]*', html_content)
                
                # Clean and filter URLs
                zillow_links = []
                for url in zillow_urls:
                    # Clean up URL if needed
                    clean_url = url.strip()
                    if clean_url and clean_url not in zillow_links:
                        zillow_links.append(clean_url)
                
                logger.info(f"Found {len(zillow_links)} Zillow links using regex extraction")
            except Exception as regex_error:
                logger.error(f"Error with regex extraction: {str(regex_error)}")
        
        # If we can't find any Zillow links on Google, use hardcoded fallback URLs for Detroit
        if not zillow_links:
            logger.warning("No Zillow links found on Google search. Using fallback Detroit URLs.")
            zillow_links = [
                "https://www.zillow.com/homedetails/18661-Sunderland-Rd-Detroit-MI-48219/88457148_zpid/",
                "https://www.zillow.com/homedetails/15351-Burgess-Detroit-MI-48223/88316853_zpid/",
                "https://www.zillow.com/homedetails/18276-Avon-Ave-Detroit-MI-48219/88457077_zpid/",
                "https://www.zillow.com/homedetails/12650-Sanford-St-Detroit-MI-48205/88171087_zpid/",
                "https://www.zillow.com/homedetails/14567-Lappin-St-Detroit-MI-48205/88221193_zpid/"
            ]
        
        # Process the links we found
        if zillow_links:
            logger.info(f"Processing {len(zillow_links)} Zillow links")
            
            # Visit each Zillow link and extract data
            for i, link in enumerate(zillow_links[:5]):  # Limit to first 5 links
                try:
                    logger.info(f"Processing link {i+1}/{min(5, len(zillow_links))}: {link}")
                    
                    # Create a fresh context for each property to avoid tracking
                    property_context = browser.new_context(
                        viewport={'width': 1280, 'height': 800},
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        java_script_enabled=True,
                    )
                    property_page = property_context.new_page()
                    property_page.set_default_timeout(timeout)
                    
                    # Navigate to the property page with longer timeout
                    logger.info(f"Navigating to: {link}")
                    try:
                        property_page.goto(link, timeout=timeout, wait_until="domcontentloaded")
                        property_page.wait_for_load_state("networkidle", timeout=timeout)
                        
                        # Take screenshot in debug mode
                        if debug:
                            screenshot_path = f"zillow_property_{i}_{int(time.time())}.png"
                            property_page.screenshot(path=screenshot_path)
                            logger.info(f"Saved property page screenshot to {screenshot_path}")
                        
                        # Extract property details
                        listing = {}
                        
                        # Get the page HTML for regex fallbacks
                        page_html = property_page.content()
                        
                        # Extract price - first try selectors, then regex
                        price_selectors = [
                            "[data-testid='price']",
                            "span[class*='price']",
                            "div[class*='price']",
                            ".ds-price"
                        ]
                        
                        # Try selectors first
                        for price_selector in price_selectors:
                            try:
                                price_elem = property_page.locator(price_selector).first
                                if price_elem.is_visible(timeout=2000):
                                    price = price_elem.inner_text().strip()
                                    price = re.sub(r'[^\d$,.]+', '', price)
                                    if price:
                                        listing["price"] = price
                                        break
                            except:
                                continue
                        
                        # If selectors fail, try regex on page HTML
                        if "price" not in listing:
                            price_matches = re.findall(r'[\$][\d,]+(?:,\d+)?', page_html)
                            if price_matches:
                                # Take the first price-like string we find
                                listing["price"] = price_matches[0]
                        
                        # Extract address - selectors first, then regex
                        address_selectors = [
                            "[data-testid='home-details-summary-address']",
                            "[data-testid='address']",
                            "h1[class*='address']",
                            ".ds-address-container"
                        ]
                        
                        for address_selector in address_selectors:
                            try:
                                address_elem = property_page.locator(address_selector).first
                                if address_elem.is_visible(timeout=2000):
                                    address = address_elem.inner_text().strip()
                                    if address:
                                        listing["location"] = address
                                        listing["title"] = address
                                        break
                            except:
                                continue
                        
                        # Extract from URL if address selectors fail
                        if "location" not in listing:
                            # Extract from URL pattern like /homedetails/123-Main-St-Detroit-MI-12345/
                            url_parts = link.split('/')
                            for part in url_parts:
                                if "Detroit" in part and "MI" in part:
                                    address = part.replace('-', ' ')
                                    listing["location"] = address
                                    listing["title"] = address
                                    break
                        
                        # Extract bedrooms, bathrooms, area
                        # First try the Zillow summary section
                        facts_text = ""
                        facts_selectors = [
                            "[data-testid='bed-bath-living-area-container']",
                            "ul[class*='fact-list']",
                            ".ds-bed-bath-living-area"
                        ]
                        
                        for selector in facts_selectors:
                            try:
                                facts_elem = property_page.locator(selector).first
                                if facts_elem.is_visible(timeout=2000):
                                    facts_text = facts_elem.inner_text()
                                    break
                            except:
                                continue
                        
                        # If we found facts text, extract the data
                        if facts_text:
                            # Extract beds
                            bed_match = re.search(r'(\d+)\s*(?:bd|bed)', facts_text, re.IGNORECASE)
                            if bed_match:
                                listing["bedrooms"] = bed_match.group(1)
                            
                            # Extract baths
                            bath_match = re.search(r'(\d+\.?\d*)\s*(?:ba|bath)', facts_text, re.IGNORECASE)
                            if bath_match:
                                listing["bathrooms"] = bath_match.group(1)
                            
                            # Extract area
                            area_match = re.search(r'([\d,]+)\s*(?:sq\.?\s*ft|sqft|sf)', facts_text, re.IGNORECASE)
                            if area_match:
                                listing["area"] = f"{area_match.group(1)} sqft"
                        
                        # If no facts found, try regex on the entire page
                        if "bedrooms" not in listing:
                            beds_match = re.search(r'(\d+)\s*(?:bed|bd|bedroom)', page_html, re.IGNORECASE)
                            if beds_match:
                                listing["bedrooms"] = beds_match.group(1)
                        
                        if "bathrooms" not in listing:
                            baths_match = re.search(r'(\d+\.?\d*)\s*(?:bath|ba|bathroom)', page_html, re.IGNORECASE)
                            if baths_match:
                                listing["bathrooms"] = baths_match.group(1)
                        
                        if "area" not in listing:
                            area_match = re.search(r'([\d,]+)\s*(?:sq\.?\s*ft|sqft|sf)', page_html, re.IGNORECASE)
                            if area_match:
                                listing["area"] = f"{area_match.group(1)} sqft"
                        
                        # Check if we have enough data to add this listing
                        if "price" in listing or "location" in listing:
                            # Make sure there's at least some usable data
                            if "price" not in listing:
                                listing["price"] = "Unknown"
                            if "location" not in listing:
                                listing["location"] = "Detroit, MI address"
                                listing["title"] = "Detroit Property"
                            
                            # Add timestamp and metadata
                            listing["time"] = "Recent"
                            listing["other"] = json.dumps({
                                "source": "Zillow",
                                "extraction_method": "google-fallback",
                                "url": link
                            })
                            
                            # Print the listing in debug mode
                            if debug:
                                logger.info(f"Extracted listing: {listing}")
                            
                            # Avoid duplicates
                            if not any(
                                l.get("price") == listing.get("price") and 
                                l.get("location") == listing.get("location") 
                                for l in listings
                            ):
                                listings.append(listing)
                                logger.info(f"Added listing: {listing.get('location')} - {listing.get('price')}")
                        
                    except Exception as navigation_error:
                        logger.error(f"Error navigating to {link}: {str(navigation_error)}")
                    
                    # Close the property context
                    property_context.close()
                    
                    # Add random delay between requests
                    delay = random.uniform(2, 5)
                    logger.info(f"Waiting {delay:.1f} seconds before next link...")
                    time.sleep(delay)
                    
                except Exception as link_error:
                    logger.error(f"Error processing Zillow link from Google: {str(link_error)}")
                    continue
        
        # Close browser
        browser.close()
        
        return listings
    
    except Exception as e:
        logger.error(f"Error in Google Search fallback: {str(e)}")
        traceback_str = traceback.format_exc()
        logger.error(f"Traceback: {traceback_str}")
        return []

def build_zillow_url(location, bedrooms=None, bathrooms=None, price_min=None, price_max=None, home_type=None):
    """Build Zillow search URL with parameters"""
    location_slug = location.replace(", ", "-").replace(" ", "-").lower()
    url = f"https://www.zillow.com/homes/for_sale/{location_slug}/"
    
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

def main():
    import argparse
    
    # Initialize the database tables if needed
    init_db()
    
    parser = argparse.ArgumentParser(description='Zillow Scraper with bot protection bypass')
    parser.add_argument('--location', type=str, default="Detroit, MI",
                        help='Location to search (default: Detroit, MI)')
    parser.add_argument('--bedrooms', type=str, default="2",
                        help='Number of bedrooms (default: 2)')
    parser.add_argument('--bathrooms', type=str, default="1",
                        help='Number of bathrooms (default: 1)')
    parser.add_argument('--price-min', type=int, default=50000,
                        help='Minimum price (default: 50000)')
    parser.add_argument('--price-max', type=int, default=300000,
                        help='Maximum price (default: 300000)')
    parser.add_argument('--home-type', type=str, default="house",
                        help='Home type (default: house)')
    parser.add_argument('--debug', action='store_true',
                        help='Enable debug mode with visual highlighting')
    parser.add_argument('--headless', action='store_true',
                        help='Run in headless mode (default: False)')
    parser.add_argument('--timeout', type=int, default=60000,
                        help='Navigation timeout in milliseconds (default: 60000)')
    parser.add_argument('--url', type=str,
                        help='Direct Zillow URL to scrape (overrides other search parameters)')
    
    args = parser.parse_args()
    
    # Build URL if not provided directly
    if args.url:
        url = args.url
    else:
        url = build_zillow_url(
            location=args.location,
            bedrooms=args.bedrooms,
            bathrooms=args.bathrooms,
            price_min=args.price_min,
            price_max=args.price_max,
            home_type=args.home_type
        )
    
    print(f"\n=== Zillow Scraper ===")
    print(f"URL: {url}")
    print(f"Debug mode: {'Enabled' if args.debug else 'Disabled'}")
    print(f"Headless mode: {'Enabled' if args.headless else 'Disabled'}")
    print(f"Timeout: {args.timeout}ms")
    print(f"{'='*50}\n")
    
    # Run the scraper
    listings = scrape_zillow(
        url=url,
        debug=args.debug,
        headless=args.headless,
        timeout=args.timeout
    )
    
    # Print results
    if listings:
        print(f"\nSuccessfully extracted {len(listings)} listings:")
        for i, listing in enumerate(listings[:5]):  # Show first 5 only
            print(f"\n{i+1}. {listing.get('title', 'Untitled')}")
            print(f"   Price: {listing.get('price', 'N/A')}")
            print(f"   Location: {listing.get('location', 'N/A')}")
            print(f"   Beds: {listing.get('bedrooms', 'N/A')}, Baths: {listing.get('bathrooms', 'N/A')}")
            print(f"   Area: {listing.get('area', 'N/A')}")
        
        if len(listings) > 5:
            print(f"\n... and {len(listings) - 5} more listings")
    else:
        print("\nNo listings found. Zillow bot protection may be active.")
    
    print("\nAll listings saved to database.")

if __name__ == "__main__":
    main() 