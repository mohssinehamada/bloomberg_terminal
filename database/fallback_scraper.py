import os
import sys
import re
import json
import logging
from bs4 import BeautifulSoup
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add parent directory to path to find database module
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Import database functions - use proper import based on script location
try:
    # Try importing as a package first (when imported from another module)
    from database.database import get_db_connection, insert_listing
except ImportError:
    # When run directly from the database directory
    logger.info("Using direct import for database module")
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from database import get_db_connection, insert_listing

# Track HTML path globally
html_path = None

def extract_price(text):
    """Extract price from text"""
    if not text:
        return None
    price_match = re.search(r'\$[\d,]+', text)
    if price_match:
        return price_match.group(0)
    return None

def extract_beds_baths(text):
    """Extract bedrooms and bathrooms from text"""
    beds = None
    baths = None
    
    # Extract beds
    bed_match = re.search(r'(\d+)\s*(?:bed|bd|br)', text, re.IGNORECASE)
    if bed_match:
        beds = bed_match.group(1)
    
    # Extract baths
    bath_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:bath|ba)', text, re.IGNORECASE)
    if bath_match:
        baths = bath_match.group(1)
        
    return beds, baths

def extract_area(text):
    """Extract square footage area from text"""
    area_match = re.search(r'([\d,]+)\s*(?:sq\s*ft|sqft|sf)', text, re.IGNORECASE)
    if area_match:
        return area_match.group(0)
    return None

def process_zillow_html():
    """Process Zillow HTML to extract listings"""
    global html_path  # Make this global so we can reference it later for deletion
    
    try:
        # Get HTML content from our page manager instead of direct file access
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from database.page_manager import get_page_content
        
        html_content = get_page_content()
        if not html_content:
            logger.error("No HTML content found in page_manager!")
            return []
        
        # Check if it's a Press & Hold page
        if "Press & Hold to confirm you are a human" in html_content:
            logger.warning("This is a Zillow verification page, not property listings")
            return []
        
        soup = BeautifulSoup(html_content, 'html.parser')
        listings = []
        
        # Method 1: Look for JSON data in script tags (most reliable method)
        script_tags = soup.find_all("script", {"type": "application/json"}) + soup.find_all("script", {"type": "application/ld+json"})
        for script in script_tags:
            try:
                if script.string:
                    data = json.loads(script.string)
                    if isinstance(data, dict) and any(key in data for key in ['props', 'searchResults', 'cat1', 'searchPageSeoObject']):
                        logger.info(f"Found potentially useful JSON data")
                        # Attempt to parse various JSON structures
                        search_results = data.get('searchResults', data.get('props', {})).get('searchResults', {})
                        results = search_results.get('listResults', [])
                        if results:
                            logger.info(f"Found {len(results)} listings in JSON")
                            for result in results:
                                try:
                                    listing = {
                                        'title': result.get('statusText', 'Zillow Property'),
                                        'date': 'Recent',
                                        'location': result.get('address', ''),
                                        'price': result.get('price', ''),
                                        'bedrooms': str(result.get('beds', '')),
                                        'bathrooms': str(result.get('baths', '')),
                                        'size': f"{result.get('area', '')} sqft" if result.get('area') else '',
                                        'other': json.dumps({
                                            'zpid': result.get('zpid', ''),
                                            'statusType': result.get('statusType', ''),
                                            'variableData': result.get('variableData', {})
                                        })
                                    }
                                    listings.append(listing)
                                except Exception as e:
                                    logger.warning(f"Error processing listing from JSON: {e}")
            except Exception as e:
                logger.warning(f"Error parsing script tag: {e}")
                
        # Method 2: Look for listing cards or containers
        if not listings:
            logger.info("No listings found in JSON, trying HTML parsing")
            property_cards = soup.select('div[data-test="property-card"], .property-card, article.list-card, div.search-result')
            
            if not property_cards:
                # Try more generic selectors in case the class names have changed
                property_cards = soup.select('div[data-price], li[data-price], div[id^="zpid_"], div[data-testid="property-card"]')
            
            logger.info(f"Found {len(property_cards)} potential property cards in HTML")
            
            for card in property_cards:
                try:
                    # Extract text content from the card
                    card_text = card.get_text(' ', strip=True)
                    
                    # Try to extract data using specific selectors first
                    title_elem = card.select_one('.list-card-title, .property-card-title, .hdp__sc-12mkvhv-0')
                    address_elem = card.select_one('.list-card-addr, .property-card-address, .list-card-address')
                    price_elem = card.select_one('.list-card-price, .property-card-price, .list-card-heading')
                    
                    # Try data attributes if selectors don't work
                    price = None
                    if card.has_attr('data-price'):
                        price = f"${card['data-price']}"
                    
                    # Extract information
                    title = title_elem.get_text(strip=True) if title_elem else 'Zillow Property'
                    location = address_elem.get_text(strip=True) if address_elem else None
                    
                    if not price and price_elem:
                        price = price_elem.get_text(strip=True)
                    
                    if not price:
                        price = extract_price(card_text)
                    
                    beds, baths = extract_beds_baths(card_text)
                    area = extract_area(card_text)
                    
                    # Only add if we have at least a price or location
                    if price or location:
                        listing = {
                            'title': title,
                            'date': 'Recent',
                            'location': location or 'Unknown Location',
                            'price': price or 'Unknown Price',
                            'bedrooms': beds or '',
                            'bathrooms': baths or '',
                            'size': area or '',
                            'other': json.dumps({'source': 'html_parsing', 'raw_text': card_text[:500]})
                        }
                        listings.append(listing)
                except Exception as e:
                    logger.warning(f"Error processing property card: {e}")
        
        # Fallback method: Look for text patterns if nothing found yet
        if not listings:
            logger.info("No listings found with standard methods, trying pattern matching in text")
            paragraphs = soup.find_all(['p', 'div', 'span', 'li'])
            for p in paragraphs:
                text = p.get_text(' ', strip=True)
                price = extract_price(text)
                if price and len(text) < 300:  # Avoid very long paragraphs
                    beds, baths = extract_beds_baths(text)
                    area = extract_area(text)
                    
                    if beds or baths or area:  # Likely a property listing
                        listing = {
                            'title': 'Zillow Property',
                            'date': 'Recent',
                            'location': 'Unknown Location',
                            'price': price,
                            'bedrooms': beds or '',
                            'bathrooms': baths or '',
                            'size': area or '',
                            'other': json.dumps({'source': 'text_pattern', 'raw_text': text})
                        }
                        listings.append(listing)
        
        # Remove duplicates based on price and bedrooms/bathrooms
        unique_listings = []
        seen = set()
        for listing in listings:
            key = f"{listing['price']}_{listing['bedrooms']}_{listing['bathrooms']}"
            if key not in seen:
                seen.add(key)
                unique_listings.append(listing)
        
        logger.info(f"Extracted {len(unique_listings)} unique listings")
        return unique_listings
    except Exception as e:
        logger.error(f"Error in process_zillow_html: {e}")
        return []

def save_to_database(listings):
    """Save listings to database"""
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return 0
    
    success_count = 0
    try:
        for listing in listings:
            try:
                # Call insert_listing with just the listing data (no connection parameter)
                listing_id = insert_listing(listing)
                if listing_id:
                    success_count += 1
                    logger.info(f"Inserted listing ID {listing_id}: {listing['title']} - {listing['price']}")
            except Exception as e:
                logger.error(f"Error inserting listing: {e}")
                continue
                
        logger.info(f"Successfully inserted {success_count} out of {len(listings)} listings")
    except Exception as e:
        logger.error(f"Database error: {e}")
    
    return success_count

def delete_html_file():
    """Delete the HTML file after processing"""
    global html_path
    if html_path and os.path.exists(html_path):
        try:
            logger.info(f"Deleting processed HTML file: {html_path}")
            os.remove(html_path)
            logger.info("HTML file deleted successfully")
            return True
        except Exception as e:
            logger.error(f"Error deleting HTML file: {e}")
            return False
    return False

def process_and_save():
    """Process the HTML and save listings to database"""
    try:
        logger.info("Starting processing of saved HTML")
        
        # Process HTML to extract listings
        listings = process_zillow_html()
        
        if not listings:
            logger.warning("No listings found in the saved HTML")
            return 0, 0
        
        logger.info(f"Extracted {len(listings)} listings, saving to database")
        
        # Save listings to database
        saved_count = save_to_database(listings)
        
        # Clear the page content after processing
        from database.page_manager import clear_page_content
        clear_page_content()
        
        logger.info(f"Processing complete: found {len(listings)}, saved {saved_count}")
        return len(listings), saved_count
        
    except Exception as e:
        logger.error(f"Error in process_and_save: {e}")
        return 0, 0 