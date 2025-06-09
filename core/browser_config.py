#!/usr/bin/env python3
"""
Browser configuration settings for browser-use
"""

from browser_use.browser.browser import Browser, BrowserConfig
from browser_use.browser.context import BrowserContextConfig

def get_browser_config(headless=False, slow_mo=100):
    """
    Get a browser configuration for browser-use
    
    Args:
        headless (bool): Whether to run browser in headless mode
        slow_mo (int): Delay in milliseconds between actions
    
    Returns:
        Browser: Configured browser instance
    """
    return Browser(
        config=BrowserConfig(
            new_context_config=BrowserContextConfig(
                viewport_expansion=1,  # Make boundary boxes visible
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.2 Safari/605.1.15"
            ),
            headless=headless,  # Run in visible mode by default
            show_browser_boundary=True,  # Show boundary boxes
            slow_mo=slow_mo  # Add delay to make actions visible
        )
    )

def get_stealth_browser_config():
    """
    Get a stealth browser configuration for sites that detect automation
    
    Returns:
        Browser: Stealth configured browser instance
    """
    return Browser(
        config=BrowserConfig(
            new_context_config=BrowserContextConfig(
                viewport_expansion=0,  # No boundary boxes for stealth
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            headless=False,  # Visible browser
            show_browser_boundary=False,  # No boundary boxes
            slow_mo=200  # Slower actions to appear more human
        )
    ) 