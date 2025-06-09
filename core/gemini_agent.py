import os
import json
import re
import logging
import time
import random
import hashlib
from typing import List, Dict, Any, Optional
from functools import lru_cache

import google.generativeai as genai
from bs4 import BeautifulSoup
import requests

import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tools.gemini.gTools import *

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Gemini2FlashWebAgent:
    """
    An agent that uses Google's Gemini 2.0 Flash API to autonomously browse websites and extract information.
    """
    
    def __init__(self, api_key: Optional[str] = None, calls_per_minute: int = 10):
        """
        Initialize the Gemini Web Agent with the provided API key.
        
        Args:
            api_key: Gemini API key. If None, will try to load from environment.
            calls_per_minute: Maximum API calls allowed per minute
        """
        # Get API key from parameter or environment
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        
        if not self.api_key:
            raise ValueError("Gemini API key not provided and not found in environment variables")
        
        # Configure the Gemini API client
        genai.configure(api_key=self.api_key)
        
        # Initialize with Gemini 2.0 Flash model
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        
        # Initialize session for web requests
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.67"
        })
        
        # Initialize cache for web content
        self.page_cache = {}
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter(calls_per_minute=calls_per_minute)
        
        logger.info("Gemini 2.0 Flash Web Agent initialized successfully")
    
    @lru_cache(maxsize=50)
    def browse_website(self, url: str, use_cache: bool = True) -> str:
        """
        Browse a website and return its HTML content.
        
        Args:
            url: The URL of the website to browse.
            use_cache: Whether to use cached content if available
            
        Returns:
            The HTML content of the website.
        """
        # Generate cache key based on URL
        cache_key = hashlib.md5(url.encode()).hexdigest()
        
        # Check cache first if enabled
        if use_cache and cache_key in self.page_cache:
            logger.info(f"Using cached content for URL: {url}")
            return self.page_cache[cache_key]
        
        try:
            logger.info(f"Accessing URL: {url}")
            
            # Add random delay to mimic human behavior and avoid rate limits
            delay = random.uniform(1.0, 3.0)
            time.sleep(delay)
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Cache the result
            if use_cache:
                self.page_cache[cache_key] = response.text
                
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Error accessing URL {url}: {str(e)}")
            return f"Error accessing URL: {str(e)}"
    
    def parse_html(self, html: str) -> BeautifulSoup:
        """
        Parse HTML content into a BeautifulSoup object.
        
        Args:
            html: The HTML content to parse.
            
        Returns:
            A BeautifulSoup object.
        """
        return BeautifulSoup(html, 'html.parser')
    
    def extract_text_with_structure(self, soup: BeautifulSoup) -> str:
        """
        Extract text while maintaining some structural information.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Text content with basic structure preserved
        """
        # Remove script, style, and hidden elements
        for element in soup(["script", "style", "meta", "noscript", "svg"]):
            element.extract()
        
        # Add section markers for headings
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            # Add a prefix based on the heading level
            level = int(heading.name[1])
            prefix = "#" * level + " "
            if heading.string:
                heading.string = prefix + heading.string
        
        # Add markers for tables
        for table in soup.find_all('table'):
            table_marker = soup.new_tag('p')
            table_marker.string = "[TABLE]"
            table.insert_before(table_marker)
            
            end_marker = soup.new_tag('p')
            end_marker.string = "[/TABLE]"
            table.insert_after(end_marker)
        
        # Mark list items
        for li in soup.find_all('li'):
            if li.string:
                li.string = "• " + li.string
        
        # Get text with some spacing
        text = ""
        for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'div', 'span', 'a']):
            if element.name in ['div', 'span'] and not element.text.strip():
                continue
                
            content = element.get_text(strip=True)
            if content:
                text += content + "\n\n"
        
        return text.strip()
    
    def chunk_content(self, content: str, max_chars: int = 30000) -> List[str]:
        """
        Split content into manageable chunks for API processing.
        
        Args:
            content: The content to chunk
            max_chars: Maximum characters per chunk
            
        Returns:
            List of content chunks
        """
        if len(content) <= max_chars:
            return [content]
        
        chunks = []
        
        # Try to split by double newlines (paragraphs)
        paragraphs = content.split("\n\n")
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) + 2 <= max_chars:
                if current_chunk:
                    current_chunk += "\n\n"
                current_chunk += paragraph
            else:
                # If this paragraph would exceed the limit, save current chunk and start new one
                if current_chunk:
                    chunks.append(current_chunk)
                
                # If the paragraph itself is too long, split it further
                if len(paragraph) > max_chars:
                    # Split by sentences
                    sentences = re.split(r'(?<=[.!?])\s+', paragraph)
                    current_chunk = ""
                    
                    for sentence in sentences:
                        if len(current_chunk) + len(sentence) + 1 <= max_chars:
                            if current_chunk:
                                current_chunk += " "
                            current_chunk += sentence
                        else:
                            chunks.append(current_chunk)
                            
                            # If the sentence itself is too long, split by words
                            if len(sentence) > max_chars:
                                words = sentence.split()
                                current_chunk = ""
                                
                                for word in words:
                                    if len(current_chunk) + len(word) + 1 <= max_chars:
                                        if current_chunk:
                                            current_chunk += " "
                                        current_chunk += word
                                    else:
                                        chunks.append(current_chunk)
                                        current_chunk = word
                            else:
                                current_chunk = sentence
                else:
                    current_chunk = paragraph
        
        # Add the last chunk if it's not empty
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def query_gemini(self, content: str, instruction: str) -> str:
        """
        Query the Gemini 2.0 Flash model with content and instructions.
        
        Args:
            content: The content to analyze (e.g., website text)
            instruction: What to extract or analyze from the content
            
        Returns:
            The model's response
        """
        try:
            # Apply rate limiting
            self.rate_limiter.wait_if_needed()
            
            # Check if content needs to be chunked
            content_chunks = self.chunk_content(content)
            
            if len(content_chunks) == 1:
                # Simple case - content fits in one chunk
                prompt = f"""
                CONTENT:
                {content}
                
                INSTRUCTION:
                {instruction}
                
                Please respond with only the requested information in a clear, structured format.
                """
                
                response = self.model.generate_content(prompt)
                return response.text
            else:
                # Content needs to be processed in chunks
                logger.info(f"Content split into {len(content_chunks)} chunks")
                
                chunk_results = []
                for i, chunk in enumerate(content_chunks):
                    logger.info(f"Processing chunk {i+1}/{len(content_chunks)}")
                    
                    chunk_prompt = f"""
                    CONTENT (Chunk {i+1}/{len(content_chunks)}):
                    {chunk}
                    
                    INSTRUCTION:
                    {instruction}
                    
                    This is chunk {i+1} of {len(content_chunks)} from the full content.
                    Extract any relevant information from this chunk according to the instructions.
                    Format your response as a structured JSON object.
                    """
                    
                    # Apply rate limiting between chunk processing
                    if i > 0:
                        self.rate_limiter.wait_if_needed()
                    
                    chunk_response = self.model.generate_content(chunk_prompt)
                    chunk_results.append(chunk_response.text)
                
                # Process the combined results with a final query
                self.rate_limiter.wait_if_needed()
                
                final_prompt = f"""
                I've analyzed {len(content_chunks)} chunks of content and obtained these results:

                {json.dumps(chunk_results, indent=2)}
                
                INSTRUCTION:
                {instruction}
                
                Please consolidate these chunk results into a single, comprehensive response.
                Remove any duplicates and organize the information coherently.
                Format your response as a structured JSON object.
                """
                
                final_response = self.model.generate_content(final_prompt)
                return final_response.text
        except Exception as e:
            logger.error(f"Error querying Gemini API: {str(e)}")
            return f"Error querying Gemini API: {str(e)}"
    
    def extract_financial_interest_rates(self, bank_url: str) -> Dict[str, Any]:
        """
        Extract current interest rates from a financial institution's website.
        
        Args:
            bank_url: URL of the financial institution
            
        Returns:
            Dictionary containing interest rate information
        """
        logger.info(f"Extracting interest rates from: {bank_url}")
        
        # Get and parse the webpage
        html_content = self.browse_website(bank_url)
        soup = self.parse_html(html_content)
        structured_content = self.extract_text_with_structure(soup)
        
        instruction = """
        Extract all interest rates mentioned on this financial institution's website.
        For each type of account or loan, identify:
        1. The account/loan type (e.g., Savings Account, Mortgage, CD, etc.)
        2. The current interest rate percentage
        3. Any terms or conditions associated with that rate (minimum balance, term length, etc.)
        4. The effective date or last update date for the rate, if available
        
        Format the response as a JSON object with this structure:
        {
            "interest_rates": [
                {
                    "account_type": "Account type name",
                    "rate": "X.XX%",
                    "terms": "Any relevant terms",
                    "effective_date": "Date the rate became effective or was last updated",
                    "rate_type": "Fixed/Variable/etc."
                },
                ...
            ],
            "source_info": {
                "website": "Name of the financial institution",
                "last_updated": "Date information was last updated on the website, if available"
            }
        }
        
        Include only information that's explicitly stated on the page.
        Use "N/A" for any fields where information is not available.
        """
        
        response = self.query_gemini(structured_content, instruction)
        
        # Try to parse the response as JSON
        try:
            # First try direct JSON parsing
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON from code blocks
            logger.warning("Failed to parse direct JSON response, checking for code blocks")
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)
            if json_match:
                json_str = json_match.group(1).strip()
                try:
                    result = json.loads(json_str)
                    return result
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON from code block")
            
            # If all parsing attempts fail, return the raw text response
            return {"raw_response": response}
    
    def search_estate_listings(self, real_estate_url: str, search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for real estate listings based on provided criteria.
        
        Args:
            real_estate_url: Base URL of the real estate website
            search_criteria: Dictionary containing search parameters (location, price range, etc.)
            
        Returns:
            List of matching property listings
        """
        logger.info(f"Searching real estate listings at: {real_estate_url}")
        
        # Convert search criteria to URL parameters - this will vary by website
        # This is a simplified example; real implementation would need to be tailored to the specific website
        search_params = []
        for key, value in search_criteria.items():
            if isinstance(value, list):
                value = "-".join(str(v) for v in value)
            search_params.append(f"{key}={value}")
        
        search_url = f"{real_estate_url}?{'&'.join(search_params)}"
        
        # Get and parse the webpage
        html_content = self.browse_website(search_url)
        
        # Check if the response contains an error message
        if html_content.startswith("Error accessing URL"):
            logger.error(f"Failed to access real estate URL: {search_url}")
            return [{"error": html_content}]
        
        soup = self.parse_html(html_content)
        structured_content = self.extract_text_with_structure(soup)
        
        instruction = f"""
        Extract real estate listings from this page that match these criteria:
        {json.dumps(search_criteria, indent=2)}
        
        For each property listing, extract:
        1. Property address (full address including city, state/province, zip/postal code if available)
        2. Price (including currency)
        3. Number of bedrooms
        4. Number of bathrooms
        5. Square footage/area (including units like sq ft or sq m)
        6. Property type (e.g., apartment, house, condo)
        7. Key features or amenities mentioned
        8. Year built (if available)
        9. Contact information (agent name, agency, phone, email if available)
        10. URL to the specific listing (if available)
        
        Format the response as a JSON array with this structure:
        [
            {{
                "address": "Full property address",
                "price": "Listed price with currency",
                "bedrooms": "Number of bedrooms",
                "bathrooms": "Number of bathrooms",
                "square_footage": "Area with units",
                "property_type": "Type of property",
                "features": ["feature1", "feature2", ...],
                "year_built": "Year built or N/A",
                "contact": "Agent contact info",
                "listing_url": "URL to the specific listing or N/A"
            }},
            ...
        ]
        
        Include only properties that match the search criteria.
        For any information that is not available, use the value "N/A".
        Limit the results to the 10 most relevant listings.
        """
        
        response = self.query_gemini(structured_content, instruction)
        
        # Try to parse the response as JSON
        try:
            # First try direct JSON parsing
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract JSON from code blocks
            logger.warning("Failed to parse direct JSON response, checking for code blocks")
            json_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', response)
            if json_match:
                json_str = json_match.group(1).strip()
                try:
                    result = json.loads(json_str)
                    return result
                except json.JSONDecodeError:
                    logger.warning("Failed to parse JSON from code block")
            
            # If all parsing attempts fail, return the raw text response
            return [{"raw_response": response}]

def run_example():
    """Run an example of the agent in a local environment using .env for API Key"""
    # Get API key from environment
    from dotenv import load_dotenv
    load_dotenv()  # Load environment variables from .env
    
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in .env file!")

    # Initialize agent with rate limiting
    agent = Gemini2FlashWebAgent(api_key=api_key, calls_per_minute=5)

    print("=" * 50)
    print("RUNNING GEMINI WEB AGENT EXAMPLES")
    print("=" * 50)

    # Example 1: Extract interest rates from a bank
    print("\n\n1. EXTRACTING FINANCIAL INTEREST RATES")
    print("-" * 40)
    bank_url = "https://www.federalreserve.gov/releases/h15/"
    print(f"Source: {bank_url}")

    try:
        interest_rates = agent.extract_financial_interest_rates(bank_url)

        print("\nRaw Interest Rates JSON:")
        print("-" * 22)
        print(json.dumps(interest_rates, indent=2))

        format_interest_rates(interest_rates)

    except Exception as e:
        print(f"Error extracting interest rates: {str(e)}")

    # Example 2: Search real estate listings
    print("\n\n2. SEARCHING REAL ESTATE LISTINGS")
    print("-" * 40)
    real_estate_url = "https://www.magicbricks.com/property-for-sale-rent-in-Vadodara/residential-real-estate-Vadodara"
    search_criteria = {
        "location": "Vadodara",
        "min_price": 500000,
        "max_price": 1000000,
        "min_bedrooms": 2
    }
    print(f"Source: {real_estate_url}")
    print(f"Search Criteria: {json.dumps(search_criteria, indent=2)}")

    try:
        listings = agent.search_estate_listings(real_estate_url, search_criteria)

        print("\nRaw Real Estate Listings JSON:")
        print("-" * 30)
        print(json.dumps(listings, indent=2))

        format_real_estate_listings(listings)

    except Exception as e:
        print(f"Error searching real estate listings: {str(e)}")

if __name__ == "__main__":
    # Run the example with .env config
    run_example()