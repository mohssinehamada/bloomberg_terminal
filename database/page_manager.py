import os
import logging
from typing import Optional
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
CURRENT_PAGE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'current_page.html')

def save_page_content(html_content: str) -> bool:
    """
    Save HTML content to the current_page.html file.
    
    Args:
        html_content: The HTML content to save
        
    Returns:
        bool: True if successfully saved, False otherwise
    """
    try:
        if not html_content:
            logger.warning("No HTML content provided to save")
            return False
            
        logger.info(f"Saving HTML content to {CURRENT_PAGE_FILE}")
        with open(CURRENT_PAGE_FILE, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Successfully saved {len(html_content)} bytes of HTML content")
        return True
    except Exception as e:
        logger.error(f"Error saving HTML content: {e}")
        return False

def get_page_content() -> Optional[str]:
    """
    Read the saved HTML content from the current_page.html file.
    
    Returns:
        str: The HTML content or None if the file doesn't exist or is empty
    """
    try:
        if not os.path.exists(CURRENT_PAGE_FILE):
            logger.warning(f"The file {CURRENT_PAGE_FILE} does not exist")
            # Create an empty file
            with open(CURRENT_PAGE_FILE, 'w', encoding='utf-8') as f:
                pass
            return None
            
        with open(CURRENT_PAGE_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if not content:
            logger.warning(f"The file {CURRENT_PAGE_FILE} is empty")
            return None
            
        logger.info(f"Successfully read {len(content)} bytes of HTML content")
        return content
    except Exception as e:
        logger.error(f"Error reading HTML content: {e}")
        return None

def clear_page_content() -> bool:
    """
    Clear the content of the current_page.html file without deleting it.
    
    Returns:
        bool: True if successfully cleared, False otherwise
    """
    try:
        logger.info(f"Clearing content of {CURRENT_PAGE_FILE}")
        with open(CURRENT_PAGE_FILE, 'w', encoding='utf-8') as f:
            pass
        
        logger.info("File content cleared successfully")
        return True
    except Exception as e:
        logger.error(f"Error clearing file content: {e}")
        return False

def initialize_file():
    """
    Initialize the current_page.html file if it doesn't exist.
    """
    try:
        if not os.path.exists(CURRENT_PAGE_FILE):
            logger.info(f"Creating empty file at {CURRENT_PAGE_FILE}")
            with open(CURRENT_PAGE_FILE, 'w', encoding='utf-8') as f:
                pass
            logger.info("File created successfully")
            return True
        else:
            logger.info(f"File {CURRENT_PAGE_FILE} already exists")
            return True
    except Exception as e:
        logger.error(f"Error initializing file: {e}")
        return False

# Initialize the file when the module is imported
initialize_file() 