import os
import json
import logging
from typing import Optional, Dict, Any, List
import asyncio
import sys
import importlib.util
import random
import time
import re
import tempfile
import requests
import html.parser
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import google.generativeai as genai
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('browser_agent.log')
    ]
)
logger = logging.getLogger(__name__)

required_packages = ["requests", "bs4", "browser_use"]
missing_packages = []

for package in required_packages:
    if importlib.util.find_spec(package) is None:
        missing_packages.append(package)

if missing_packages:
    print(f"Missing required packages: {', '.join(missing_packages)}")
    print("Please install the missing packages with:")
    print(f"pip install {' '.join(missing_packages)}")
    sys.exit(1)

import requests
from bs4 import BeautifulSoup
import re

from dotenv import load_dotenv
from pydantic import SecretStr
from langchain_google_genai import ChatGoogleGenerativeAI

# Test Variables Integration
try:
    from test_versiables import (
        ReproducibilityController,
        BrowserControlVariables,
        EconomicControlVariables,
        setup_test_environment
    )
    # Try to import enhanced economic variables
    try:
        from test_versiables.enhanced_economic_variables import RealTimeEconomicData
        ENHANCED_ECONOMIC_AVAILABLE = True
        logger.info("✅ Enhanced economic variables loaded successfully")
    except ImportError:
        ENHANCED_ECONOMIC_AVAILABLE = False
        logger.info("ℹ️ Enhanced economic variables not available, using basic version")
    
    TEST_VARIABLES_AVAILABLE = True
    logger.info("✅ Test variables module loaded successfully")
except ImportError as e:
    TEST_VARIABLES_AVAILABLE = False
    ENHANCED_ECONOMIC_AVAILABLE = False
    logger.warning(f"⚠️ Test variables not available: {e}")

class TokenCounter:
    """Track token usage and costs for Gemini API calls"""
    
    GEMINI_PRICING = {
        "gemini-2.0-flash-exp": {
            "input_tokens_per_million": 0.075,    
            "output_tokens_per_million": 0.30,  
        },
        "gemini-1.5-pro": {
            "input_tokens_per_million": 3.50,  
            "output_tokens_per_million": 10.50, 
        },
        "gemini-1.5-flash": {
            "input_tokens_per_million": 0.075, 
            "output_tokens_per_million": 0.30, 
        }
    }
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        self.model_name = model_name
        self.session_stats = {
            "start_time": datetime.now(),
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_requests": 0,
            "total_cost": 0.0,
            "requests": []
        }
        
        self.stats_file = "token_usage_stats.json"
        self.load_stats()
    
    def count_tokens_estimate(self, text: str) -> int:
        """Estimate token count for text (rough approximation)"""
        return len(text) // 4
    
    def log_request(self, 
                   input_text: str, 
                   output_text: str, 
                   actual_input_tokens: Optional[int] = None,
                   actual_output_tokens: Optional[int] = None,
                   request_type: str = "chat") -> Dict[str, Any]:
        """Log a single API request and calculate costs"""
            
        # Use actual tokens if available, otherwise estimate
        if actual_input_tokens is not None and actual_output_tokens is not None:
            input_tokens = actual_input_tokens
            output_tokens = actual_output_tokens
            token_source = "🎯 ACTUAL"
            logger.info(f"🎯 Using ACTUAL token counts from Gemini API")
        else:
            input_tokens = self.count_tokens_estimate(input_text)
            output_tokens = self.count_tokens_estimate(output_text)
            token_source = "📊 ESTIMATED"
            logger.warning(f"📊 Using ESTIMATED token counts (Gemini API tokens not available)")
        
        pricing = self.GEMINI_PRICING.get(self.model_name, self.GEMINI_PRICING["gemini-2.0-flash-exp"])
        
        input_cost = (input_tokens / 1_000_000) * pricing["input_tokens_per_million"]
        output_cost = (output_tokens / 1_000_000) * pricing["output_tokens_per_million"]
        total_cost = input_cost + output_cost
     
        request_record = {
            "timestamp": datetime.now().isoformat(),
            "request_type": request_type,
            "model": self.model_name,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "input_cost": input_cost,
            "output_cost": output_cost,
            "total_cost": total_cost,
            "token_source": token_source,  # Track whether tokens are actual or estimated
            "actual_tokens_available": actual_input_tokens is not None and actual_output_tokens is not None,
            "input_text_preview": input_text[:200] + "..." if len(input_text) > 200 else input_text,
            "output_text_preview": output_text[:200] + "..." if len(output_text) > 200 else output_text
        }
        
        self.session_stats["total_input_tokens"] += input_tokens
        self.session_stats["total_output_tokens"] += output_tokens
        self.session_stats["total_requests"] += 1
        self.session_stats["total_cost"] += total_cost
        self.session_stats["requests"].append(request_record)
            
        logger.info(f"🔢 {token_source} Token usage - Input: {input_tokens}, Output: {output_tokens}, Cost: ${total_cost:.6f}")
        
        if self.session_stats["total_requests"] % 5 == 0:  
            self.save_stats()
        
        return request_record
    
    def get_session_summary(self) -> Dict[str, Any]:
        duration = datetime.now() - self.session_stats["start_time"]
        
        return {
            "session_duration": str(duration),
            "total_requests": self.session_stats["total_requests"],
            "total_input_tokens": self.session_stats["total_input_tokens"],
            "total_output_tokens": self.session_stats["total_output_tokens"],
            "total_tokens": self.session_stats["total_input_tokens"] + self.session_stats["total_output_tokens"],
            "total_cost": self.session_stats["total_cost"],
            "average_cost_per_request": self.session_stats["total_cost"] / max(1, self.session_stats["total_requests"]),
            "model": self.model_name
        }
    
    def print_session_summary(self):
        summary = self.get_session_summary()
        
        # Count actual vs estimated requests
        actual_count = sum(1 for req in self.session_stats["requests"] 
                          if req.get("actual_tokens_available", False))
        estimated_count = len(self.session_stats["requests"]) - actual_count
        
        print("\n" + "="*50)
        print("📊 TOKEN USAGE SUMMARY")
        print("="*50)
        print(f"🤖 Model: {summary['model']}")
        print(f"⏱️  Session Duration: {summary['session_duration']}")
        print(f"📞 Total Requests: {summary['total_requests']}")
        
        # Token source breakdown
        if actual_count > 0 and estimated_count > 0:
            print(f"🎯 Actual Token Data: {actual_count} requests")
            print(f"📊 Estimated Token Data: {estimated_count} requests")
            print(f"⚠️  MIXED DATA: Some costs are estimates, some are actual")
        elif actual_count > 0:
            print(f"🎯 ALL ACTUAL TOKEN DATA: {actual_count} requests")
            print(f"✅ Costs are based on real Gemini API token usage")
        else:
            print(f"📊 ALL ESTIMATED TOKEN DATA: {estimated_count} requests")
            print(f"⚠️  WARNING: Costs are estimates only (4 chars ≈ 1 token)")
        
        print(f"📥 Input Tokens: {summary['total_input_tokens']:,}")
        print(f"📤 Output Tokens: {summary['total_output_tokens']:,}")
        print(f"🔢 Total Tokens: {summary['total_tokens']:,}")
        print(f"💰 Total Cost: ${summary['total_cost']:.6f}")
        print(f"📊 Avg Cost/Request: ${summary['average_cost_per_request']:.6f}")
        print("="*50)
    
    def save_stats(self):
        try:
            all_stats = []
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    all_stats = json.load(f)
            
            session_data = self.session_stats.copy()
            session_data["start_time"] = session_data["start_time"].isoformat()
            session_data["end_time"] = datetime.now().isoformat()
            
            all_stats.append(session_data)
            
            if len(all_stats) > 100:
                all_stats = all_stats[-100:]
            
            with open(self.stats_file, 'w') as f:
                json.dump(all_stats, f, indent=2)
                
            logger.info(f"💾 Token usage stats saved to {self.stats_file}")
            
        except Exception as e:
            logger.error(f"❌ Error saving token stats: {e}")
    
    def load_stats(self):
        try:
            if os.path.exists(self.stats_file):
                with open(self.stats_file, 'r') as f:
                    all_stats = json.load(f)
                logger.info(f"📂 Loaded token usage history from {self.stats_file}")
            else:
                logger.info("📂 No existing token usage file found, starting fresh")
        except Exception as e:
            logger.error(f"❌ Error loading token stats: {e}")
    
    def get_total_historical_cost(self) -> float:
        try:
            if not os.path.exists(self.stats_file):
                return 0.0
            
            with open(self.stats_file, 'r') as f:
                all_stats = json.load(f)
            
            total_cost = sum(session.get("total_cost", 0) for session in all_stats)
            return total_cost
            
        except Exception as e:
            logger.error(f"❌ Error calculating historical cost: {e}")
            return 0.0
    
    def print_historical_summary(self):
        try:
            if not os.path.exists(self.stats_file):
                print("📂 No historical data available")
                return
            
            with open(self.stats_file, 'r') as f:
                all_stats = json.load(f)
            
            total_requests = sum(session.get("total_requests", 0) for session in all_stats)
            total_input_tokens = sum(session.get("total_input_tokens", 0) for session in all_stats)
            total_output_tokens = sum(session.get("total_output_tokens", 0) for session in all_stats)
            total_cost = sum(session.get("total_cost", 0) for session in all_stats)
            
            print("\n" + "="*50)
            print("📈 HISTORICAL TOKEN USAGE")
            print("="*50)
            print(f"📅 Total Sessions: {len(all_stats)}")
            print(f"📞 Total Requests: {total_requests:,}")
            print(f"📥 Total Input Tokens: {total_input_tokens:,}")
            print(f"📤 Total Output Tokens: {total_output_tokens:,}")
            print(f"🔢 Total Tokens: {(total_input_tokens + total_output_tokens):,}")
            print(f"💰 Total Historical Cost: ${total_cost:.6f}")
            print("="*50)
            
        except Exception as e:
            logger.error(f"❌ Error printing historical summary: {e}")

class TokenTrackingGeminiLLM:
    """Custom wrapper for ChatGoogleGenerativeAI that tracks actual token usage"""
    
    def __init__(self, api_key: str, model: str = "gemini-2.0-flash-exp", token_counter=None, **kwargs):
        self.api_key = api_key
        self.model = model
        self.token_counter = token_counter
        
        # Initialize the base LLM
        self.llm = ChatGoogleGenerativeAI(
            model=model,
            api_key=SecretStr(api_key),
            **kwargs
        )
        
        logger.info(f"🔢 TokenTrackingGeminiLLM initialized with model: {model}")
    
    async def ainvoke(self, messages, **kwargs):
        """Async invoke with token tracking"""
        try:
            # Convert messages to string for token counting if needed
            if isinstance(messages, list):
                input_text = "\n".join([str(msg) for msg in messages])
            else:
                input_text = str(messages)
            
            logger.debug(f"🚀 Making Gemini API call with {len(input_text)} characters")
            
            # Make the actual API call
            response = await self.llm.ainvoke(messages, **kwargs)
            
            # Extract actual token usage from response metadata if available
            actual_input_tokens = None
            actual_output_tokens = None
            
            # Try to get real token usage from response metadata
            if hasattr(response, 'response_metadata'):
                metadata = response.response_metadata
                logger.debug(f"📊 Response metadata: {metadata}")
                
                # Gemini API response structure (this may vary)
                if 'usage_metadata' in metadata:
                    usage = metadata['usage_metadata']
                    actual_input_tokens = usage.get('prompt_token_count')
                    actual_output_tokens = usage.get('candidates_token_count')
                    logger.info(f"🎯 Real token usage - Input: {actual_input_tokens}, Output: {actual_output_tokens}")
                elif 'token_usage' in metadata:
                    usage = metadata['token_usage']
                    actual_input_tokens = usage.get('prompt_tokens')
                    actual_output_tokens = usage.get('completion_tokens')
                    logger.info(f"🎯 Real token usage - Input: {actual_input_tokens}, Output: {actual_output_tokens}")
            
            # Track token usage with actual counts if available
            if self.token_counter:
                output_text = str(response.content) if hasattr(response, 'content') else str(response)
                self.token_counter.log_request(
                    input_text=input_text,
                    output_text=output_text,
                    actual_input_tokens=actual_input_tokens,
                    actual_output_tokens=actual_output_tokens,
                    request_type="gemini_api_call"
                )
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error in TokenTrackingGeminiLLM.ainvoke: {e}")
            # Track failed request
            if self.token_counter:
                self.token_counter.log_request(
                    input_text=input_text if 'input_text' in locals() else "Unknown",
                    output_text=f"Error: {e}",
                    request_type="gemini_api_error"
                )
            raise
    
    def invoke(self, messages, **kwargs):
        """Sync invoke with token tracking"""
        try:
            # Convert messages to string for token counting if needed
            if isinstance(messages, list):
                input_text = "\n".join([str(msg) for msg in messages])
            else:
                input_text = str(messages)
            
            logger.debug(f"🚀 Making Gemini API call with {len(input_text)} characters")
            
            # Make the actual API call
            response = self.llm.invoke(messages, **kwargs)
            
            # Extract actual token usage from response metadata if available
            actual_input_tokens = None
            actual_output_tokens = None
            
            # Try to get real token usage from response metadata
            if hasattr(response, 'response_metadata'):
                metadata = response.response_metadata
                logger.debug(f"📊 Response metadata: {metadata}")
                
                # Gemini API response structure (this may vary)
                if 'usage_metadata' in metadata:
                    usage = metadata['usage_metadata']
                    actual_input_tokens = usage.get('prompt_token_count')
                    actual_output_tokens = usage.get('candidates_token_count')
                    logger.info(f"🎯 Real token usage - Input: {actual_input_tokens}, Output: {actual_output_tokens}")
                elif 'token_usage' in metadata:
                    usage = metadata['token_usage']
                    actual_input_tokens = usage.get('prompt_tokens')
                    actual_output_tokens = usage.get('completion_tokens')
                    logger.info(f"🎯 Real token usage - Input: {actual_input_tokens}, Output: {actual_output_tokens}")
            
            # Track token usage with actual counts if available
            if self.token_counter:
                output_text = str(response.content) if hasattr(response, 'content') else str(response)
                self.token_counter.log_request(
                    input_text=input_text,
                    output_text=output_text,
                    actual_input_tokens=actual_input_tokens,
                    actual_output_tokens=actual_output_tokens,
                    request_type="gemini_api_call"
                )
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Error in TokenTrackingGeminiLLM.invoke: {e}")
            # Track failed request
            if self.token_counter:
                self.token_counter.log_request(
                    input_text=input_text if 'input_text' in locals() else "Unknown",
                    output_text=f"Error: {e}",
                    request_type="gemini_api_error"
                )
            raise
    
    def __getattr__(self, name):
        """Delegate other method calls to the underlying LLM"""
        return getattr(self.llm, name)

try:
    from browser_use import Agent
    from browser_use.browser.browser import Browser, BrowserConfig
    from browser_use.browser.context import BrowserContextConfig
    BROWSER_USE_AVAILABLE = True
    print("Successfully imported browser_use module")
except ImportError as e:
    print(f"Could not import browser_use module: {e}")
    print("Will run in limited mode without browser automation.")
    
    class BrowserContextConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
    
    class BrowserConfig:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
    
    class Browser:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
    
    class Agent:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
        
        async def run(self, **kwargs):
            print("Browser automation not available. Running in limited mode.")
            return {"output": "Browser automation not available. URL was generated but browsing couldn't be performed."}
    
    BROWSER_USE_AVAILABLE = False


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
try:
    from database.database import insert_listing, log_scrape, get_db_connection, insert_interest_rate, init_db
   
    print("🔧 Initializing database tables...")
    init_db()
    print("✅ Database tables ready!")
except ImportError:
    print("Could not import database module. Some functionality may be limited.")

from playwright.sync_api import sync_playwright

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GeminiBrowserAgent:
    def __init__(self, gemini_api_key: Optional[str] = None, task: Optional[str] = None, 
                 enable_testing: bool = False, test_scenario: str = "default", **kwargs):
        self.api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API Key not provided or found in environment.")

        self.task = task or "Visit a website and extract relevant data."
        
        # Initialize controlled testing if enabled
        self.controlled_testing = enable_testing
        self.test_config = None
        self.controlled_browser_config = None
        self.performance_tracker = {
            'start_time': datetime.now(),
            'queries_executed': 0,
            'successful_queries': 0,
            'total_items_extracted': 0,
            'response_times': [],
            'errors': []
        }
        
        if enable_testing and TEST_VARIABLES_AVAILABLE:
            logger.info("🧪 Enabling controlled testing mode")
            
            # Setup controlled test environment
            self.test_config = setup_test_environment(test_scenario)
            
            # Apply reproducibility controls
            ReproducibilityController.set_random_seeds()
            
            # Store controlled browser configuration
            self.controlled_browser_config = {
                'headless': BrowserControlVariables.HEADLESS_MODE,
                'viewport_width': BrowserControlVariables.VIEWPORT_WIDTH,
                'viewport_height': BrowserControlVariables.VIEWPORT_HEIGHT,
                'timeout': BrowserControlVariables.PAGE_LOAD_TIMEOUT,
                'user_agent': BrowserControlVariables.USER_AGENT,
                'max_retries': BrowserControlVariables.MAX_RETRIES,
                'retry_delay': BrowserControlVariables.RETRY_DELAY
            }
            
            logger.info(f"✅ Controlled testing enabled with scenario: {test_scenario}")
            logger.info(f"🎯 Random seed: {ReproducibilityController.RANDOM_SEED}")
            logger.info(f"🖥️ Viewport: {BrowserControlVariables.VIEWPORT_WIDTH}x{BrowserControlVariables.VIEWPORT_HEIGHT}")
        
        elif enable_testing and not TEST_VARIABLES_AVAILABLE:
            logger.warning("⚠️ Controlled testing requested but test variables not available")

        self.token_counter = TokenCounter(model_name="gemini-2.0-flash-exp")
        logger.info("🔢 Token counter initialized")

        # Apply controlled model temperature if testing is enabled
        model_temperature = (ReproducibilityController.MODEL_TEMPERATURE 
                           if self.controlled_testing and TEST_VARIABLES_AVAILABLE 
                           else kwargs.get('temperature', 0.3))

        self.llm = TokenTrackingGeminiLLM(
            api_key=self.api_key,
            model="gemini-2.0-flash-exp",
            token_counter=self.token_counter,
            temperature=model_temperature,
            **kwargs
        )
        
        if BROWSER_USE_AVAILABLE:
            logger.info("GeminiBrowserAgent initialized with browser-use")
        else:
            logger.warning("browser-use not available - agent will run in limited mode")

    def get_economic_context(self) -> Dict[str, Any]:
        """Get current economic context for data normalization"""
        if self.controlled_testing and TEST_VARIABLES_AVAILABLE:
            # Use enhanced real-time data if available, otherwise fallback to basic mock data
            if ENHANCED_ECONOMIC_AVAILABLE:
                return RealTimeEconomicData.get_real_time_data()
            else:
                return EconomicControlVariables.get_current_economic_context()
        return {"message": "Economic context not available - controlled testing not enabled"}

    def track_query_performance(self, response_time: float, success: bool, items_extracted: int = 0, error: str = None):
        """Track performance metrics for each query"""
        self.performance_tracker['queries_executed'] += 1
        self.performance_tracker['response_times'].append(response_time)
        
        if success:
            self.performance_tracker['successful_queries'] += 1
            self.performance_tracker['total_items_extracted'] += items_extracted
        
        if error:
            self.performance_tracker['errors'].append({
                'timestamp': datetime.now().isoformat(),
                'error': error,
                'query_number': self.performance_tracker['queries_executed']
            })

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for controlled testing"""
        tracker = self.performance_tracker
        duration = datetime.now() - tracker['start_time']
        
        success_rate = (tracker['successful_queries'] / tracker['queries_executed'] * 100 
                       if tracker['queries_executed'] > 0 else 0)
        
        avg_response_time = (sum(tracker['response_times']) / len(tracker['response_times']) 
                           if tracker['response_times'] else 0)
        
        avg_items_per_query = (tracker['total_items_extracted'] / tracker['successful_queries'] 
                             if tracker['successful_queries'] > 0 else 0)
        
        summary = {
            'test_duration': str(duration),
            'total_queries': tracker['queries_executed'],
            'successful_queries': tracker['successful_queries'],
            'success_rate_percent': round(success_rate, 2),
            'total_items_extracted': tracker['total_items_extracted'],
            'average_items_per_query': round(avg_items_per_query, 2),
            'average_response_time_seconds': round(avg_response_time, 3),
            'error_count': len(tracker['errors']),
            'controlled_testing_enabled': self.controlled_testing
        }
        
        if self.controlled_testing and TEST_VARIABLES_AVAILABLE:
            summary['economic_context'] = self.get_economic_context()
            summary['test_configuration'] = self.test_config
            summary['browser_config'] = self.controlled_browser_config
        
        return summary

    def print_performance_summary(self):
        """Print a formatted performance summary"""
        summary = self.get_performance_summary()
        
        print("\n" + "="*60)
        print("📊 WEB AGENT PERFORMANCE SUMMARY")
        print("="*60)
        print(f"⏱️  Test Duration: {summary['test_duration']}")
        print(f"📞 Total Queries: {summary['total_queries']}")
        print(f"✅ Successful Queries: {summary['successful_queries']}")
        print(f"📈 Success Rate: {summary['success_rate_percent']}%")
        print(f"📦 Total Items Extracted: {summary['total_items_extracted']}")
        print(f"📊 Avg Items/Query: {summary['average_items_per_query']}")
        print(f"⚡ Avg Response Time: {summary['average_response_time_seconds']}s")
        print(f"❌ Errors: {summary['error_count']}")
        
        if self.controlled_testing:
            print(f"🧪 Controlled Testing: ✅ ENABLED")
            if TEST_VARIABLES_AVAILABLE:
                print(f"🎯 Random Seed: {ReproducibilityController.RANDOM_SEED}")
                print(f"🌡️  Model Temperature: {ReproducibilityController.MODEL_TEMPERATURE}")
        else:
            print(f"🧪 Controlled Testing: ❌ DISABLED")
        
        print("="*60)

    def _count_extracted_items(self, result: Dict[str, Any]) -> int:
        """Count the number of items extracted from the result"""
        if not isinstance(result, dict):
            return 0
        
        count = 0
        
        # Count listings in real estate data
        if 'extracted_data' in result:
            for site_data in result['extracted_data'].values():
                if isinstance(site_data, list):
                    count += len(site_data)
                elif isinstance(site_data, dict) and 'listings' in site_data:
                    count += len(site_data['listings'])
        
        # Count direct listings
        if 'listings' in result:
            count += len(result['listings'])
        
        # Count output items
        if 'output' in result and isinstance(result['output'], dict):
            if 'listings' in result['output']:
                count += len(result['output']['listings'])
        
        return count

    def filter_listings(self, listings: List[Dict], criteria: Dict) -> List[Dict]:
        """Filter listings based on user criteria"""
        filtered = []
        
        for listing in listings:
            matches = True
           
            if criteria.get('price_min') and listing.get('price'):
                if listing['price'] < criteria['price_min']:
                    matches = False
            if criteria.get('price_max') and listing.get('price'):
                if listing['price'] > criteria['price_max']:
                    matches = False
            
            if criteria.get('bedrooms') and listing.get('bedrooms'):
                if listing['bedrooms'] < float(criteria['bedrooms']):
                    matches = False
            
            if criteria.get('bathrooms') and listing.get('bathrooms'):
                if listing['bathrooms'] < float(criteria['bathrooms']):
                    matches = False
           
            if criteria.get('location') and listing.get('location'):
                if criteria['location'].lower() not in listing['location'].lower():
                    matches = False
            
            if criteria.get('home_type') and listing.get('type'):
                if criteria['home_type'].lower() not in listing['type'].lower():
                    matches = False
            
            if matches:
                filtered.append(listing)
        
        return filtered

    async def execute_task(self, websites: Dict[str, str], max_steps: int = 25) -> Dict[str, Any]:
        """Execute the browsing task using browser-use Agent with BeautifulSoup fallback"""
        query_start_time = datetime.now()
        
        try:
            if not BROWSER_USE_AVAILABLE:
                logger.warning("browser-use not available, using BeautifulSoup fallback")
                result = await self._fallback_beautiful_soup(websites)
                
                # Track performance
                response_time = (datetime.now() - query_start_time).total_seconds()
                items_extracted = self._count_extracted_items(result)
                success = result.get('success', False) if isinstance(result, dict) else bool(result)
                self.track_query_performance(response_time, success, items_extracted)
                
                return result

            for url, task_type in websites.items():
                logger.info(f"Starting browser-use agent for {url} with task type: {task_type}")
                
                
                task_description = self._build_task_description(url, task_type)
                logger.info(f"Task description created: {len(task_description)} characters")
                
                
                self.token_counter.log_request(
                    input_text=task_description,
                    output_text="",  # No output yet
                    request_type=f"task_creation_{task_type}"
                )
                
                agent = None
                try:
                    from browser_use import BrowserSession
                   
                    browser_session = BrowserSession(
                        headless=False,
                        highlight_elements=True,
                        viewport_expansion=500,
                        slow_mo=100,
                        wait_between_actions=1.0,
                        user_data_dir=None  
                    )
                    
                    agent = Agent(
                        task=task_description,
                        llm=self.llm,
                        browser_session=browser_session
                    )
                    logger.info("✅ Successfully created Agent with visual browser configuration")
                    
                except Exception as e:
                    logger.error(f"❌ Failed to create Agent with BrowserSession: {e}")
                    try:
                        agent = Agent(
                            task=task_description,
                            llm=self.llm
                        )
                        logger.info("✅ Created Agent with default configuration")
                    except Exception as e2:
                        logger.error(f"❌ Failed to create Agent at all: {e2}")
                    logger.info("Falling back to BeautifulSoup due to Agent creation failure")
                    return await self._fallback_beautiful_soup(websites)

                if not agent:
                    logger.error("❌ No agent was created, falling back to BeautifulSoup")
                    return await self._fallback_beautiful_soup(websites)
                
                max_retries = 3
                retry_count = 0
                result = None
                agent_succeeded = False

                while retry_count < max_retries and not agent_succeeded:
                    try:
                        logger.info(f"🚀 Running browser-use agent attempt {retry_count + 1}/{max_retries}")
                        logger.info(f"Task preview: {task_description[:200]}...")
                        
                        
                        agent_result = await agent.run(max_steps=max_steps)
                        logger.info(f"✅ Agent completed, result type: {type(agent_result)}")
                        
                        
                        result_str = str(agent_result) if agent_result else ""
                        self.token_counter.log_request(
                            input_text=f"Agent execution for {url}",
                            output_text=result_str,
                            request_type=f"agent_execution_{task_type}"
                        )
                        
                        await asyncio.sleep(random.uniform(1, 2))
                        
                        if agent_result is not None:
                            
                            if hasattr(agent_result, 'extracted_content'):
                                content = agent_result.extracted_content()
                                if content:
                                    logger.info("✅ Agent extracted content successfully")
                                    result = {'output': content}
                                    agent_succeeded = True
                                    break
                            elif hasattr(agent_result, 'final_result'):
                                content = agent_result.final_result()
                                if content:
                                    logger.info("✅ Agent got final result successfully")
                                    result = {'output': content}
                                    agent_succeeded = True
                                    break
                            elif isinstance(agent_result, dict):
                                logger.info("✅ Agent returned dictionary result")
                                result = agent_result
                                agent_succeeded = True
                                break
                            else:
                                logger.info(f"✅ Agent returned result: {type(agent_result)}")
                                result = {'output': str(agent_result)}
                                agent_succeeded = True
                                break
                        else:
                            logger.warning(f"⚠️ Agent returned None on attempt {retry_count + 1}")
                            
                    except Exception as e:
                        logger.error(f"❌ Error in agent run attempt {retry_count + 1}: {e}")
                        logger.error(f"Error type: {type(e).__name__}")
                        retry_count += 1
                        if retry_count < max_retries:
                            wait_time = random.uniform(3, 5)
                            logger.info(f"⏳ Waiting {wait_time:.1f}s before retry...")
                            await asyncio.sleep(wait_time)
               
                if agent_succeeded and result:
                    logger.info("🎉 Browser-use agent completed successfully!")
                  
                    if task_type == "real_estate" and isinstance(result.get('output'), dict):
                        if 'listings' in result['output']:
                            search_criteria_json = os.getenv('SEARCH_CRITERIA', '{}')
                            try:
                                search_criteria = json.loads(search_criteria_json)
                                filtered_listings = self.filter_listings(
                                    result['output']['listings'], 
                                    search_criteria
                                )
                                result['output']['listings'] = filtered_listings
                                logger.info(f"✅ Filtered to {len(filtered_listings)} matching listings")
                            except Exception as filter_error:
                                logger.warning(f"⚠️ Error filtering listings: {filter_error}")
                    
                    # Track successful performance
                    response_time = (datetime.now() - query_start_time).total_seconds()
                    items_extracted = self._count_extracted_items(result)
                    self.track_query_performance(response_time, True, items_extracted)
                    
                    return result
                else:
                    logger.warning("⚠️ Browser-use agent failed after all retries, falling back to BeautifulSoup")
                    fallback_result = await self._fallback_beautiful_soup(websites)
                    
                    # Track fallback performance
                    response_time = (datetime.now() - query_start_time).total_seconds()
                    items_extracted = self._count_extracted_items(fallback_result)
                    success = fallback_result.get('success', False) if isinstance(fallback_result, dict) else bool(fallback_result)
                    error_msg = "Browser-use agent failed, used BeautifulSoup fallback"
                    self.track_query_performance(response_time, success, items_extracted, error_msg)
                    
                    return fallback_result

        except Exception as e:
            logger.error(f"❌ Unexpected error in execute_task: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            logger.info("🔄 Falling back to BeautifulSoup due to unexpected error")
            
            # Track error and fallback
            response_time = (datetime.now() - query_start_time).total_seconds()
            error_msg = f"Unexpected error: {str(e)}"
            
            try:
                fallback_result = await self._fallback_beautiful_soup(websites)
                items_extracted = self._count_extracted_items(fallback_result)
                success = fallback_result.get('success', False) if isinstance(fallback_result, dict) else bool(fallback_result)
                self.track_query_performance(response_time, success, items_extracted, error_msg)
                return fallback_result
            except Exception as fallback_error:
                # Even fallback failed
                self.track_query_performance(response_time, False, 0, f"{error_msg}; Fallback also failed: {str(fallback_error)}")
                return {"success": False, "error": str(e), "fallback_error": str(fallback_error)}

    def _build_task_description(self, url: str, task_type: str) -> str:
        """Build detailed task description for the agent"""
        base_task = f"Visit {url} and "
        
        if task_type == "real_estate":
           
            search_criteria_json = os.getenv('SEARCH_CRITERIA', '{}')
            try:
                search_criteria = json.loads(search_criteria_json)
            except:
                search_criteria = {}
            
            
            search_instructions = ""
            if search_criteria.get('location'):
                search_instructions += f"- Search for properties in {search_criteria['location']}\n"
            if search_criteria.get('bedrooms'):
                search_instructions += f"- Filter for properties with at least {search_criteria['bedrooms']} bedrooms\n"
            if search_criteria.get('bathrooms'):
                search_instructions += f"- Filter for properties with at least {search_criteria['bathrooms']} bathrooms\n"
            if search_criteria.get('price_max'):
                try:
                    price_max = int(search_criteria['price_max'])
                    search_instructions += f"- Filter for properties under ${price_max:,}\n"
                except (ValueError, TypeError):
                    search_instructions += f"- Filter for properties under ${search_criteria['price_max']}\n"
            if search_criteria.get('price_min'):
                try:
                    price_min = int(search_criteria['price_min'])
                    search_instructions += f"- Filter for properties over ${price_min:,}\n"
                except (ValueError, TypeError):
                    search_instructions += f"- Filter for properties over ${search_criteria['price_min']}\n"
            if search_criteria.get('home_type'):
                search_instructions += f"- Look specifically for {search_criteria['home_type']} properties\n"
            
            task = base_task + f"""find real estate listings that match these specific criteria:

{search_instructions}

Follow these specific steps:
1. Navigate to the website
2. If necessary, click "Accept Cookies" or any consent dialogs that appear
3. Use the search functionality to enter the location: {search_criteria.get('location', 'any location')}
4. Apply filters for:
   - Bedrooms: {search_criteria.get('bedrooms', 'any')}
   - Bathrooms: {search_criteria.get('bathrooms', 'any')}
   - Price range: Up to ${search_criteria.get('price_max', 'any')} {f"(minimum ${search_criteria.get('price_min', 0)})" if search_criteria.get('price_min') else ""}
   - Property type: {search_criteria.get('home_type', 'any').title()}
5. Wait for the listings to load fully - this is critical for sites like Zillow!
6. Scroll down slowly and deliberately to load more listings (scroll a few times with pauses)
7. Wait an additional 2-3 seconds after scrolling to ensure dynamic content loads
8. For Zillow specifically: be patient with loading and let the site settle after interactions

IMPORTANT FORM INTERACTION INSTRUCTIONS:
- When you see dropdown menus or selection lists, click on the specific option you need
- For housing type selection: Look for "{search_criteria.get('home_type', 'house')}" in the list and click on it specifically
- If you see checkboxes, click to check/uncheck them as needed
- For dropdown menus that show options like "apartment", "condo", "house", etc., click directly on "{search_criteria.get('home_type', 'house')}"
- After making selections in forms, look for "Apply" or "Search" buttons and click them
- Wait 2-3 seconds after each form interaction to let the page update
- If a dropdown is open, make sure to click on the exact option you want, not just anywhere on the dropdown

Once you have found the listings that match the criteria, your FINAL action must be to run this EXACT command:
extract_content(goal="Extract real estate listings as clean JSON", format="json")

The extracted data MUST be in this EXACT format and nothing else:
{{
  "listings": [
    {{
      "title": "Property title/name",
      "time": "When posted",
      "location": "Address/location",
      "price": "Price as string",
      "bedrooms": "Number of bedrooms",
      "bathrooms": "Number of bathrooms",
      "area": "Square footage"
    }},
    ... more listings ...
  ]
}}

CRITICAL INSTRUCTIONS:
- Your final action MUST be the extract_content action
- ONLY return the JSON object as shown above
- Do NOT include any explanation text, markdown formatting, or code blocks
- Do NOT add any text like "Here are the listings" or "The listings are:"
- Each property listing should have as many fields as possible from the format above
- Extract at least 5 listings if available that match the specified criteria
- If you encounter a captcha or blocking mechanism, try waiting 5 seconds and then gently scrolling
- Focus on finding properties that match: {search_criteria.get('location', 'any location')}, {search_criteria.get('bedrooms', 'any')} bed, {search_criteria.get('bathrooms', 'any')} bath, under ${search_criteria.get('price_max', 'any budget')}
"""
        elif task_type == "interest_rate":
            task = base_task + """find current interest rates.

Follow these specific steps:
1. Navigate to the website
2. Look for mortgage rates, loan rates, or other financial interest rates
3. Wait for the page to load fully - important for dynamic content!
4. If necessary, click "Accept Cookies" or any consent dialogs that appear
5. Look for any "View Rates" buttons and click them if needed
6. Analyze the page to identify current interest rates
7. Scroll down to ensure all rate information is loaded

Once you have found the interest rates, your FINAL action must be to run this EXACT command:
extract_content(goal="Extract current interest rates as clean JSON", format="json")

The extracted data MUST be in this EXACT format and nothing else:
{{
  "interest_rates": [
    {{
      "rate_type": "Type of rate (e.g., 30-year fixed mortgage)",
      "rate": "Interest rate percentage",
      "apr": "Annual Percentage Rate (if available)",
      "updated": "When this rate was last updated (if available)",
      "institution": "Bank or financial institution offering this rate (if available)"
    }},
    ... more rates ...
  ]
}}

CRITICAL INSTRUCTIONS:
- Your final action MUST be the extract_content action
- ONLY return the JSON object as shown above
- Do NOT include any explanation text, markdown formatting, or code blocks
- Do NOT add any text like "Here are the rates" or "The rates are:"
- Each rate should have as many fields as possible from the format above
- Extract at least 3-5 different rates if available
"""
        else:
            task = base_task + "extract relevant information."

        
        if "zillow.com" in url.lower():
            task += """
SPECIFIC INSTRUCTIONS FOR ZILLOW:
1. Use the search functionality carefully and be patient between actions
2. Scroll VERY slowly and deliberately, pausing for 2-3 seconds between scrolls
3. If you encounter a captcha, notify in the output and try a gentler approach
4. Wait longer than usual between page interactions
5. When using extract_content, focus on getting listing data, not full details
6. Make sure to let pages fully load before interactions
"""
        elif "craigslist.org" in url.lower():
            task += """
SPECIFIC INSTRUCTIONS FOR CRAIGSLIST:
1. Look for the housing section or "housing" link and click it
2. Use the search box to enter your location criteria
3. For filters, look for links or dropdowns on the left side or top of the page
4. When you see the housing type dropdown (like in your image), click specifically on "house"
5. For bedroom/bathroom filters, look for number selectors or dropdown menus
6. For price filters, look for "min price" and "max price" input fields
7. After setting all filters, click "update search" or similar button
8. Be patient with page loads as Craigslist can be slow
9. Look for listings in a list format, usually with titles, prices, and locations
"""

        
        task += """
BROWSING BEHAVIOR:
- First browse non-listing pages on the site for 30-60 seconds
- Then search with very broad criteria
- Gradually narrow your search
- Pause 2-3 seconds between each interaction
- Move the mouse randomly on the page occasionally
- Scroll at varying speeds (sometimes fast, sometimes slow)
- Sometimes click on non-essential elements like images
- Don't perform actions too quickly in sequence
"""

        return task

    async def _fallback_beautiful_soup(self, websites: Dict[str, str]) -> Dict[str, Any]:
        
        try:
            logger.info("🔄 Using BeautifulSoup fallback method")
            
            for url, task_type in websites.items():
                logger.info(f"📄 Fetching content from {url}")
                
               
                try:
                    task_description = self._build_task_description(url, task_type)
                    logger.info(f"✅ Task description created successfully")
                except Exception as desc_error:
                    logger.error(f"❌ Error creating task description: {desc_error}")
                    task_description = f"Extract content from {url}"
                
                    
                try:
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                    }
                    response = requests.get(url, headers=headers, timeout=30)
                    
                    if response.status_code != 200:
                        logger.error(f"❌ HTTP {response.status_code} for {url}")
                        return {"error": f"Failed to fetch page content. Status code: {response.status_code}"}
                    
                    logger.info(f"✅ Successfully fetched content from {url}")
                    
                except requests.RequestException as req_error:
                    logger.error(f"❌ Request error: {req_error}")
                    return {"error": f"Failed to fetch page content: {req_error}"}
                
                
                try:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    logger.info("✅ Successfully parsed HTML with BeautifulSoup")
                    
                    
                    if task_type == "real_estate":
                        content = self._extract_real_estate_content(soup, url)
                    elif task_type == "interest_rate":
                        content = self._extract_interest_rate_content(soup, url)
                    else:
                        content = self._extract_general_content(soup, url)
                    
                    if content:
                        logger.info("✅ Successfully extracted content with BeautifulSoup")
                        return {"output": content}
                    else:
                        logger.warning("⚠️ No content extracted with BeautifulSoup")
                        return {"error": "No content could be extracted from the page"}
                        
                except Exception as parse_error:
                    logger.error(f"❌ Error parsing content: {parse_error}")
                    return {"error": f"Error parsing page content: {parse_error}"}
            
            return {"error": "No valid content found in BeautifulSoup fallback method"}
            
        except Exception as e:
            logger.error(f"❌ Error in BeautifulSoup fallback method: {e}")
            logger.error(f"Error type: {type(e).__name__}")
            return {"error": f"Error in BeautifulSoup fallback method: {e}"}

    def _extract_real_estate_content(self, soup: BeautifulSoup, url: str) -> str:
        """Extract real estate content from BeautifulSoup"""
        # Implementation of extracting real estate content using BeautifulSoup
        # This is a placeholder and should be implemented based on the actual structure of the website
        return ""

    def _extract_interest_rate_content(self, soup: BeautifulSoup, url: str) -> str:
        """Extract interest rate content from BeautifulSoup"""
        # Implementation of extracting interest rate content using BeautifulSoup
        # This is a placeholder and should be implemented based on the actual structure of the website
        return ""

    def _extract_general_content(self, soup: BeautifulSoup, url: str) -> str:
        """Extract general content from BeautifulSoup"""
        # Implementation of extracting general content using BeautifulSoup
        # This is a placeholder and should be implemented based on the actual structure of the website
        return ""

def extract_search_criteria(user_input: str) -> dict:
    
    criteria = {
        'location': None,
        'bedrooms': None,
        'bathrooms': None,
        'price_min': None,
        'price_max': None,
        'home_type': None,
        'website': None
    }
    
    
    text = user_input.lower()
    
    
    website_patterns = [
        r'(?:on|at|from|search|using|through|via)\s+(?:https?://)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        r'(?:https?://)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
    ]
    
    for pattern in website_patterns:
        match = re.search(pattern, text)
        if match:
            criteria['website'] = match.group(1)
            break
    
    
    location_markers = ["in", "at", "near"]
    for marker in location_markers:
        if f" {marker} " in text:
            location_part = text.split(f" {marker} ")[1].split(" with ")[0].split(" for ")[0].split(" and ")[0].split(" on ")[0]
            criteria['location'] = location_part.strip().title()
            break
    
    
    bedroom_patterns = [
        r'(\d+)\s*bed',
        r'(\d+)\s*bedroom',
        r'(\d+)\s*br',
        r'(\d+)b\d*b'
    ]
    for pattern in bedroom_patterns:
        match = re.search(pattern, text)
        if match:
            criteria['bedrooms'] = match.group(1)
            break
    
    
    bathroom_patterns = [
        r'(\d+\.?\d*)\s*bath',
        r'(\d+\.?\d*)\s*bathroom',
        r'(\d+\.?\d*)\s*ba',
        r'\d+b(\d+\.?\d*)b'
    ]
    for pattern in bathroom_patterns:
        match = re.search(pattern, text)
        if match:
            criteria['bathrooms'] = match.group(1)
            break
    
    
    price_patterns = [
        r'under\s*\$?(\d+[k|m]?)',
        r'below\s*\$?(\d+[k|m]?)',
        r'up to\s*\$?(\d+[k|m]?)',
        r'maximum\s*\$?(\d+[k|m]?)',
        r'around\s*\$?(\d+[k|m]?)',
        r'about\s*\$?(\d+[k|m]?)',
        r'\$(\d+[k|m]?)',
        r'(\d+[k|m]?)\s*dollars'
    ]
    for pattern in price_patterns:
        match = re.search(pattern, text)
        if match:
            price = match.group(1)
            
            if price.endswith('k'):
                price = int(float(price[:-1]) * 1000)
            elif price.endswith('m'):
                price = int(float(price[:-1]) * 1000000)
            else:
                price = int(price)
            
            if any(word in text for word in ['under', 'below', 'up to', 'maximum']):
                criteria['price_max'] = price
            elif any(word in text for word in ['from', 'minimum', 'starting']):
                criteria['price_min'] = price
            else:
                
                criteria['price_max'] = price
                criteria['price_min'] = int(price * 0.8)
    
    
    home_types = {
        'house': ['house', 'home', 'single family', 'single-family'],
        'apartment': ['apartment', 'apt', 'flat'],
        'townhouse': ['townhouse', 'town house', 'townhome'],
        'condo': ['condo', 'condominium']
    }
    
    for home_type, keywords in home_types.items():
        if any(keyword in text for keyword in keywords):
            criteria['home_type'] = home_type
            break
    
    return criteria

def detect_task_type(user_input: str) -> str:
    
    text = user_input.lower()
    
    
    interest_indicators = [
        'interest rate', 'interest rates', 'mortgage rate', 'mortgage rates',
        'loan rate', 'loan rates', 'apr', 'financial rate', 'bank rate',
        'lending rate', 'borrowing rate', 'rate', 'rates'
    ]
    
    
    real_estate_indicators = [
        'house', 'home', 'apartment', 'condo', 'townhouse', 'property',
        'real estate', 'bedroom', 'bathroom', 'sqft', 'square feet',
        'buy', 'purchase', 'listing', 'for sale', 'zillow', 'realtor',
        'trulia', 'rent', 'rental'
    ]
    
    
    interest_score = sum(1 for indicator in interest_indicators if indicator in text)
    
    
    real_estate_score = sum(1 for indicator in real_estate_indicators if indicator in text)
    
    
    if interest_score > real_estate_score:
        return "interest_rate"
    else:
        return "real_estate"

def get_user_input():
    
    print("\n--- AI Browser Agent ---")
    print("Tell me what you're looking for and I'll help you find it!")
    print("\nExamples:")
    print("• 'Looking for a house in New York with 3 bedrooms and 2 bathrooms under $800k'")
    print("• 'Find me a 2 bed apartment in San Francisco around $500k'") 
    print("• 'Search for townhouses in Chicago with 2 baths on zillow.com'")
    print("• 'Looking for current mortgage interest rates'")
    print("• 'Find me loan rates from Bank of America'")
    print("• 'What are the current interest rates for home loans?'")
    
    user_input = input("\nWhat are you looking for? ").strip()
    
    if not user_input:
        print("Please enter what you're looking for.")
        return get_user_input()
    
  
    task_type = detect_task_type(user_input)
    
    if task_type == "interest_rate":
        print(f"\n🎯 I detected you're looking for interest rates!")
        
    
        website_patterns = [
            r'(?:on|at|from|search|using|through|via)\s+(?:https?://)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
            r'(?:https?://)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})',
        ]
        
        url = None
        for pattern in website_patterns:
            match = re.search(pattern, user_input.lower())
            if match:
                url = match.group(1)
                break
        
        if not url:
            print("\nWhich financial website would you like me to search?")
            print("Examples: bankofamerica.com, chase.com, wells.fargo.com, mortgagerates.com")
            url = input("Enter website: ").strip()
        
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
            
        print(f"\n🔍 I'll search for interest rates on: {url}")
        return url, task_type
        
    else:  
        print(f"\n🎯 I detected you're looking for real estate!")
        
        
        criteria = extract_search_criteria(user_input)
        
        
        os.environ['SEARCH_CRITERIA'] = json.dumps(criteria)       
        
        
        print("\n📋 Here's what I understood:")
        if criteria['location']:
            print(f"📍 Location: {criteria['location']}")
        if criteria['bedrooms']:
            print(f"🛏️  Bedrooms: {criteria['bedrooms']}+")
        if criteria['bathrooms']:
            print(f"🚿 Bathrooms: {criteria['bathrooms']}+")
        if criteria['price_min'] and criteria['price_max']:
            try:
                price_min = int(criteria['price_min'])
                price_max = int(criteria['price_max'])
                print(f"💰 Price range: ${price_min:,} - ${price_max:,}")
            except (ValueError, TypeError):
                print(f"💰 Price range: ${criteria['price_min']} - ${criteria['price_max']}")
        elif criteria['price_max']:
            try:
                price_max = int(criteria['price_max'])
                print(f"💰 Maximum price: ${price_max:,}")
            except (ValueError, TypeError):
                print(f"💰 Maximum price: ${criteria['price_max']}")
        elif criteria['price_min']:
            try:
                price_min = int(criteria['price_min'])
                print(f"💰 Minimum price: ${price_min:,}")
            except (ValueError, TypeError):
                print(f"💰 Minimum price: ${criteria['price_min']}")
        if criteria['home_type']:
            print(f"🏠 Property type: {criteria['home_type'].title()}")
        if criteria['website']:
            print(f"🌐 Website: {criteria['website']}")
        
        # Determine website
        if not criteria['website']:
            print("\n🌐 Which website would you like me to search?")
            print("Examples: zillow.com, realtor.com, trulia.com, apartments.com")
            url = input("Enter website: ").strip()
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
        else:
            url = criteria['website']
            if not url.startswith(("http://", "https://")):
                url = "https://" + url
        
        print(f"\n🔍 I'll search for properties on: {url}")
        print("\n❓ Is this correct? (y/n)")
        if input().lower().strip() == 'n':
            print("\n🔧 Let's adjust the search criteria:")
            print("(Leave blank to keep current value)")
            
            new_location = input(f"📍 Location [{criteria['location'] or 'Not specified'}]: ").strip()
            if new_location:
                criteria['location'] = new_location
            
            new_bedrooms = input(f"🛏️  Minimum bedrooms [{criteria['bedrooms'] or 'Any'}]: ").strip()
            if new_bedrooms and new_bedrooms.isdigit():
                criteria['bedrooms'] = new_bedrooms
            
            new_bathrooms = input(f"🚿 Minimum bathrooms [{criteria['bathrooms'] or 'Any'}]: ").strip()
            if new_bathrooms and (new_bathrooms.isdigit() or '.' in new_bathrooms):
                criteria['bathrooms'] = new_bathrooms
            
            new_price_min = input(f"💰 Minimum price [{criteria['price_min'] or 'Not specified'}]: ").strip()
            if new_price_min and new_price_min.isdigit():
                criteria['price_min'] = int(new_price_min)
            
            new_price_max = input(f"💰 Maximum price [{criteria['price_max'] or 'Not specified'}]: ").strip()
            if new_price_max and new_price_max.isdigit():
                criteria['price_max'] = int(new_price_max)
            
            print("\n🏠 Property type:")
            print("1. House")
            print("2. Apartment")
            print("3. Townhouse")
            print("4. Condo")
            print("5. Any")
            new_type = input(f"Choose type [{criteria['home_type'] or 'Any'}]: ").strip()
            if new_type in ['1', '2', '3', '4']:
                type_map = {'1': 'house', '2': 'apartment', '3': 'townhouse', '4': 'condo'}
                criteria['home_type'] = type_map[new_type]
        os.environ['SEARCH_CRITERIA'] = json.dumps(criteria)
    
    return url, task_type

def main():
    try:
        
        url, task_type = get_user_input()
        websites = {url: task_type}
        
        print(f"\nExecuting task: {task_type} on {url}")
        
        if not BROWSER_USE_AVAILABLE:
            print("\nError: browser-use module is not available.")
            print("Please ensure the browser-use module is installed and in your Python path.")
            return
        
        try:
            print("\nInitializing browser-use agent...")
            agent = GeminiBrowserAgent()
            
            print("\nStarting browser automation with browser-use...")
            result = asyncio.run(agent.execute_task(websites=websites))
            
            if result.get('error'):
                print(f"\nError during execution: {result['error']}")
                print("Trying fallback approach...")
                if "zillow.com" in url.lower():
                    fallback_zillow_scrape(url)
                else:
                    with sync_playwright() as p:
                        browser = p.chromium.launch(headless=False)
                        page = browser.new_page()
                        page.goto(url)
                        page.wait_for_load_state("networkidle")
                        page.screenshot(path="fallback_screenshot.png")
                        print("\nTook fallback screenshot")
                        print("\nBrowser will stay open for manual interaction.")
                        print("Press Enter in this terminal when you're done...")
                        input()  # Wait for user input before closing
                        browser.close()
            elif result.get('output'):
                print("\nTask completed successfully!")
                print("\nExtracted data:")
                
                saved_count = 0
                total_listings = 0
                
                try:
                    import json
                    
                    output_data = result['output']
                    
                    print(f"🔍 Debug: Output type is {type(output_data)}")
                    print(f"🔍 Debug: Output preview: {str(output_data)[:500]}...")
                    
                    if isinstance(output_data, str):
                        try:
                            output_data = json.loads(output_data)
                            print("✅ Successfully parsed JSON from string")
                        except Exception as parse_error:
                            print(f"❌ Failed to parse JSON: {parse_error}")
                            print("Output is a string, not JSON")
                            print(output_data)
                    
                    if isinstance(output_data, dict):
                        print(f"🔍 Debug: Dictionary keys: {list(output_data.keys())}")
                        
                        if 'listings' in output_data and isinstance(output_data['listings'], list):
                            listings = output_data['listings']
                            total_listings = len(listings)
                            print(f"Found {total_listings} listings to save to database")
                            
                            if listings:
                                print(f"🔍 Debug: First listing structure: {json.dumps(listings[0], indent=2)}")
                            
                            for i, listing in enumerate(listings, 1):
                                try:
                                    print(f"\n--- Processing Listing {i}/{total_listings} ---")
                                    print(f"🔍 Original listing data: {json.dumps(listing, indent=2)}")
                                    
                                    if 'other' in listing:
                                        if isinstance(listing['other'], str):
                                            try:
                                                other_data = json.loads(listing['other'])
                                            except:
                                                other_data = {"original_other": listing['other']}
                                        else:
                                            other_data = listing['other']
                                    else:
                                        other_data = {}
                                    
                                    other_data['source_url'] = url
                                    other_data['search_criteria'] = os.getenv('SEARCH_CRITERIA', '{}')
                                    listing['other'] = json.dumps(other_data)
                                    
                                    print(f"🔍 Processed listing data: {json.dumps(listing, indent=2)}")
                                    
                                    print(f"🔄 Attempting to save listing {i} to database...")
                                    listing_id = enhanced_insert_listing(listing)
                                    if listing_id:
                                        saved_count += 1
                                        print(f"✅ Saved listing {i}/{total_listings} to database with ID: {listing_id}")
                                        print(f"   📍 {listing.get('location', 'Unknown location')}")
                                        print(f"   💰 {listing.get('price', 'Unknown price')}")
                                        print(f"   🏠 {listing.get('bedrooms', '?')} bed, {listing.get('bathrooms', '?')} bath")
                                    else:
                                        print(f"❌ Failed to save listing {i}/{total_listings} - enhanced_insert_listing returned False")
                                        
                                except Exception as e:
                                    print(f"❌ Error saving listing {i}: {e}")
                                    import traceback
                                    print(f"❌ Traceback: {traceback.format_exc()}")
                                    continue
                                    
                            log_scrape(
                                website_url=url,
                                task_type=task_type,
                                status="success",
                                message=f"Successfully scraped {total_listings} listings, saved {saved_count} to database",
                                raw_data=output_data,
                                error_message=None
                            )
                            
                        elif any(key in output_data for key in ['results', 'data', 'items', 'properties']) and isinstance(output_data.get(next((k for k in ['results', 'data', 'items', 'properties'] if k in output_data), None)), list):
                            
                            key_found = next((k for k in ['results', 'data', 'items', 'properties'] if k in output_data), None)
                            listings = output_data[key_found]
                            total_listings = len(listings)
                            print(f"Found {total_listings} listings in '{key_found}' key to save to database")
                            
                            if listings:
                                print(f"🔍 Debug: First listing structure: {json.dumps(listings[0], indent=2)}")
                            
                            for i, listing in enumerate(listings, 1):
                                try:
                                    print(f"\n--- Processing Listing {i}/{total_listings} ---")
                                    print(f"🔍 Original listing data: {json.dumps(listing, indent=2)}")
                                    
                                    processed_listing = listing.copy()
                                    
                                    if 'description' in processed_listing and 'title' not in processed_listing:
                                        processed_listing['title'] = processed_listing['description']
                                    
                                    if 'area_sqft' in processed_listing and 'area' not in processed_listing:
                                        processed_listing['area'] = processed_listing['area_sqft']
                                    
                                    if 'bathrooms' not in processed_listing:
                                        desc = processed_listing.get('description', '')
                                        if '3/2/2' in desc or '3/2' in desc:
                                            processed_listing['bathrooms'] = '2'
                                        else:
                                            processed_listing['bathrooms'] = ''
                                    
                                    if 'other' in processed_listing:
                                        if isinstance(processed_listing['other'], str):
                                            try:
                                                other_data = json.loads(processed_listing['other'])
                                            except:
                                                other_data = {"original_other": processed_listing['other']}
                                        else:
                                            other_data = processed_listing['other']
                                    else:
                                        other_data = {}
                                    
                                    other_data['source_url'] = url
                                    other_data['search_criteria'] = os.getenv('SEARCH_CRITERIA', '{}')
                                    other_data['found_in_key'] = key_found
                                    processed_listing['other'] = json.dumps(other_data)
                                    
                                    print(f"🔍 Processed listing data: {json.dumps(processed_listing, indent=2)}")
                                    
                                    print(f"🔄 Attempting to save listing {i} to database...")
                                    listing_id = enhanced_insert_listing(processed_listing)
                                    if listing_id:
                                        saved_count += 1
                                        print(f"✅ Saved listing {i}/{total_listings} to database with ID: {listing_id}")
                                        print(f"   📍 {processed_listing.get('location', 'Unknown location')}")
                                        print(f"   💰 {processed_listing.get('price', 'Unknown price')}")
                                        print(f"   🏠 {processed_listing.get('bedrooms', '?')} bed, {processed_listing.get('bathrooms', '?')} bath")
                                    else:
                                        print(f"❌ Failed to save listing {i}/{total_listings} - enhanced_insert_listing returned False")
                                        
                                except Exception as e:
                                    print(f"❌ Error saving listing {i}: {e}")
                                    import traceback
                                    print(f"❌ Traceback: {traceback.format_exc()}")
                                    continue
                            
                            log_scrape(
                                website_url=url,
                                task_type=task_type,
                                status="success",
                                message=f"Successfully scraped {total_listings} listings from '{key_found}' key, saved {saved_count} to database",
                                raw_data=output_data,
                                error_message=None
                            )
                        elif 'interest_rates' in output_data and isinstance(output_data['interest_rates'], list):
                            
                            rates = output_data['interest_rates']
                            total_listings = len(rates)
                            print(f"Found {total_listings} interest rates to save to database")
                            
                            for i, rate in enumerate(rates, 1):
                                try:
                                    rate_id = insert_interest_rate(rate, url)
                                    if rate_id:
                                        saved_count += 1
                                        print(f"✅ Saved interest rate {i}/{total_listings} to database with ID: {rate_id}")
                                        print(f"   📊 {rate.get('rate_type', 'Unknown type')}: {rate.get('rate', 'Unknown rate')}")
                                    else:
                                        print(f"❌ Failed to save interest rate {i}/{total_listings}")
                                except Exception as e:
                                    print(f"❌ Error saving interest rate {i}: {e}")
                                    continue
                            
                            log_scrape(
                                website_url=url,
                                task_type=task_type,
                                status="success",
                                message=f"Successfully scraped {total_listings} interest rates, saved {saved_count} to database",
                                raw_data=output_data,
                                error_message=None
                            )
                        else:
                            print("⚠️ Output format not recognized for database saving")
                            print("Raw output:")
                            print(json.dumps(output_data, indent=2) if isinstance(output_data, dict) else str(output_data))
                    
                    elif isinstance(output_data, list):
                        
                        total_listings = len(output_data)
                        print(f"Found {total_listings} items in direct list to save to database")
                        
                        if output_data:
                            print(f"🔍 Debug: First item structure: {json.dumps(output_data[0], indent=2)}")
                        
                        for i, item in enumerate(output_data, 1):
                            try:
                                print(f"\n--- Processing Item {i}/{total_listings} ---")
                                print(f"🔍 Original item data: {json.dumps(item, indent=2)}")
                            
                                if isinstance(item, dict):
                                    if 'other' not in item:
                                        item['other'] = {}
                                    if isinstance(item['other'], str):
                                        try:
                                            other_data = json.loads(item['other'])
                                        except:
                                            other_data = {"original_other": item['other']}
                                    else:
                                        other_data = item['other']
                                    
                                    other_data['source_url'] = url
                                    other_data['search_criteria'] = os.getenv('SEARCH_CRITERIA', '{}')
                                    item['other'] = json.dumps(other_data)
                                    
                                    print(f"🔍 Processed item data: {json.dumps(item, indent=2)}")
                                    
                                    print(f"🔄 Attempting to save item {i} to database...")
                                    listing_id = enhanced_insert_listing(item)
                                    if listing_id:
                                        saved_count += 1
                                        print(f"✅ Saved item {i}/{total_listings} to database with ID: {listing_id}")
                                        print(f"   📍 {item.get('location', 'Unknown location')}")
                                        print(f"   💰 {item.get('price', 'Unknown price')}")
                                        print(f"   🏠 {item.get('bedrooms', '?')} bed, {item.get('bathrooms', '?')} bath")
                                    else:
                                        print(f"❌ Failed to save item {i}/{total_listings} - enhanced_insert_listing returned False")
                                else:
                                    print(f"⚠️ Item {i} is not a dictionary: {type(item)}")
                            except Exception as e:
                                print(f"❌ Error saving item {i}: {e}")
                                import traceback
                                print(f"❌ Traceback: {traceback.format_exc()}")
                                continue
                    
                    else:
                        print("⚠️ Output format not recognized for database saving")
                        print("Raw output:")
                        print(str(output_data))
                    
                    
                    if total_listings > 0:
                        print(f"\n📊 Database Summary:")
                        print(f"   Total items found: {total_listings}")
                        print(f"   Successfully saved: {saved_count}")
                        print(f"   Success rate: {(saved_count/total_listings)*100:.1f}%")
                        
                        if saved_count > 0:
                            print(f"\n🎉 Great! {saved_count} items have been saved to your Neon database!")
                            print("You can view them in your database dashboard or run check_database.py to see the data.")
                    else:
                        print("\n⚠️ No items were found to save to the database")
                        
                except Exception as e:
                    print(f"\n❌ Error processing results for database: {e}")
                    import traceback
                    traceback.print_exc()
                    
                    
                    log_scrape(
                        website_url=url,
                        task_type=task_type,
                        status="error",
                        message="Error processing results for database",
                        raw_data=None,
                        error_message=str(e)
                    )
                
                
                print("\n" + "="*60)
                print("🔢 TOKEN USAGE & COST ANALYSIS")
                print("="*60)
                
               
                agent.token_counter.print_session_summary()
                    
                    
                agent.token_counter.print_historical_summary()
                
                
                agent.token_counter.save_stats()
                
                print("\nPress Enter to close the browser...")
                input()
                
        except Exception as e:
            print(f"\nError running browser-use agent: {e}")
            print("Please ensure browser-use is properly installed and configured.")
    
    except KeyboardInterrupt:
        print("\nOperation canceled by user")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

def fallback_zillow_scrape(url):
    """Simple fallback method for Zillow when advanced_zillow_scrape fails"""
    print("\nUsing fallback method for Zillow...")
    try:
        with sync_playwright() as p:
            
            browser = p.chromium.launch(
                headless=False,  
                slow_mo=100  
            )
            
            
            context = browser.new_context(
                viewport={"width": 1366, "height": 768},
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.4 Safari/605.1.15"
            )
            
            page = context.new_page()
            
            
            page.on("console", lambda msg: print(f"BROWSER LOG: {msg.text}"))
            
            
            page.set_default_timeout(90000)  # 90 seconds
            
            try:
                
                print("First visiting Google to establish browsing history...")
                page.goto("https://www.google.com")
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(random.uniform(2000, 4000))
                
                
                search_input = page.locator("input[name='q']")
                if search_input.is_visible():
                        
                    page.evaluate("""
                    (element) => {
                        element.style.border = '3px solid red';
                        element.style.backgroundColor = 'yellow';
                    }
                    """, search_input)
                
                
                search_input.fill("zillow real estate")
                search_input.press("Enter")
                page.wait_for_load_state("networkidle")
                page.wait_for_timeout(random.uniform(3000, 5000))
                
                
                print(f"Navigating to {url}")
                page.goto(url)
                page.wait_for_load_state("networkidle")
                
               
                wait_time = random.uniform(5000, 8000)
                print(f"Waiting {wait_time/1000:.1f} seconds for page to fully load...")
                page.wait_for_timeout(wait_time)
                
                
                for selector in [
                    "button:has-text('Accept')", 
                    "button:has-text('Accept All')",
                    "button:has-text('I Agree')",
                    "button:has-text('OK')",
                    "button:has-text('Got It')",
                    "[aria-label='Close']"
                ]:
                    try:
                        if page.locator(selector).is_visible(timeout=2000):
                            print(f"Clicking {selector}...")
                            
                            page.evaluate("""
                            (selector) => {
                                const element = document.querySelector(selector);
                                if (element) {
                                    element.style.border = '3px solid red';
                                    element.style.backgroundColor = 'yellow';
                                }
                            }
                            """, selector)
                            page.wait_for_timeout(500)  # Pause to see the highlight
                            page.locator(selector).click()
                            page.wait_for_timeout(random.uniform(1000, 2000))
                    except Exception:
                        continue
                
                
                try:
                    print("Checking for Press & Hold verification...")
                    press_hold_selectors = [
                        "text=Press & Hold",
                        "button:has-text('Press')",
                        "button:has-text('Hold')",
                        "[class*='captcha'] button"
                    ]
                    
                    for selector in press_hold_selectors:
                        if page.locator(selector).is_visible(timeout=5000):
                            print(f"Found Press & Hold verification with selector: {selector}")
                            button = page.locator(selector).first
                            
                            
                            page.evaluate("""
                            (element) => {
                                element.style.border = '5px solid red';
                                element.style.backgroundColor = 'yellow';
                                console.log('Found Press & Hold button, highlighting it');
                            }
                            """, button)
                            
                            
                            page.wait_for_timeout(1000)
                            
                            box = button.bounding_box()
                            x = box['x'] + box['width']/2
                            y = box['y'] + box['height']/2
                            
                            
                            print("Performing press and hold action...")
                            page.mouse.move(x, y)
                            page.mouse.down()
                            hold_time = random.uniform(4000, 6000)
                            page.wait_for_timeout(hold_time)  
                            page.mouse.up()
                            page.wait_for_load_state("networkidle")
                            page.wait_for_timeout(3000)
                            break
                except Exception as e:
                    print(f"Error in Press & Hold handling: {e}")
                
                
                print("Performing natural browsing behavior...")
                
                
                for _ in range(3):
                    x = random.randint(100, 1200)
                    y = random.randint(100, 600)
                    page.mouse.move(x, y)
                    page.wait_for_timeout(random.uniform(500, 1500))
                
                
                print("Scrolling with varying speeds...")
                for _ in range(8):
                    
                    scroll_amount = random.randint(200, 800)
                    page.evaluate(f"window.scrollBy(0, {scroll_amount})")
                    
                    
                    wait_time = random.uniform(1000, 3000)
                    page.wait_for_timeout(wait_time)
                
                    
                print("Waiting for dynamic content to load...")
                page.wait_for_timeout(random.uniform(5000, 8000))
                
                
                screenshot_path = "zillow_screenshot.png"
                page.screenshot(path=screenshot_path)
                print(f"Took a screenshot and saved to {screenshot_path}")
                
                
                html_content = page.content()
                html_path = "zillow_page.html"
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                print(f"Saved page HTML to {html_path}")
                
                
                print("Attempting to extract property information...")
                try:
                    
                    card_selectors = [
                        "div[data-test='property-card']",
                        "div.list-card",
                        "article[role='article']",
                        "div[id*='search-result']",
                        "div[class*='property-card']",
                        "div[class*='listing-card']",
                        "li[data-test='search-result']"
                    ]
                    
                    found_cards = False
                    for selector in card_selectors:
                        count = page.locator(selector).count()
                        if count > 0:
                            print(f"Found {count} property cards with selector: {selector}")
                            found_cards = True
                            break
                
                    if found_cards:
                        print("Found property listings on the page. You can view them in the browser.")
                    else:
                        
                        captcha_indicators = [
                            "captcha",
                            "robot",
                            "automated",
                            "verify",
                            "human",
                            "bot",
                            "detection"
                        ]
                        
                        page_text = page.inner_text("body")
                        captcha_present = any(indicator in page_text.lower() for indicator in captcha_indicators)
                        
                        if captcha_present:
                            print("Bot detection or CAPTCHA detected. Manual intervention required.")
                        else:
                            print("No property cards found, but no clear bot detection either.")
                except Exception as e:
                    print(f"Error extracting property info: {e}")
                
                
                print("\nBrowser is open for you to interact with Zillow manually.")
                print("You may need to complete CAPTCHA or verification steps manually.")
                print("Press Enter in this terminal to close the browser when finished.")
                input()
                
            except Exception as e:
                print(f"Error during browsing: {e}")
            
            
            browser.close()
    except Exception as e:
        print(f"Error in fallback Zillow scraping: {e}")

def handle_press_and_hold():
    
    if not BROWSER_USE_AVAILABLE:
        print("Browser automation not available. Cannot handle Press & Hold verification.")
        return False
        
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)  
            page = browser.new_page()
            page.goto("https://www.zillow.com")
            
            
            button = page.locator("text=Press & Hold")
            if button.is_visible():
                
                box = button.bounding_box()
                x = box['x'] + box['width']/2
                y = box['y'] + box['height']/2
                
                
                page.mouse.move(x, y)
                page.mouse.down()
                page.wait_for_timeout(3000)  
                page.mouse.up()
                
                
                page.wait_for_load_state("networkidle")
                return True
            return False
    except Exception as e:
        print(f"Error in handle_press_and_hold: {e}")
        return False

def handle_zillow_sidebar_scrolling(page, max_scroll_attempts=5):
    """
    Handles scrolling within Zillow's sidebar filters.
    
    Args:
        page: The Playwright page object
        max_scroll_attempts: Maximum number of scroll attempts to make
    
    Returns:
        bool: True if scrolling was successful, False otherwise
    """
    try:
        
        sidebar_selectors = [
            "div[data-testid='search-filters']", 
            "div.filter-bar",
            "div.search-page-filter-menu",
            "div[id*='filter']",
            "div.filters-container"
        ]
        
        sidebar = None
        for selector in sidebar_selectors:
            try:
                element = page.locator(selector).first
                if element.is_visible():
                    sidebar = element
                    break
            except Exception:
                continue
                                    
        if not sidebar:
            
            sidebar = page.locator("div[class*='filter'], div[id*='filter']").first
        
        if not sidebar:
            
            sidebar = page.locator("div.overflow-auto, div.overflow-y-auto, div[style*='overflow']").first
            
        if not sidebar:
            
            return _handle_zillow_sidebar_js_scrolling(page, max_scroll_attempts)
            
        
        box = sidebar.bounding_box()
        if not box:
            return _handle_zillow_sidebar_js_scrolling(page, max_scroll_attempts)
            
        
        x = box['x'] + box['width']/2
        y = box['y'] + box['height']/2
        
        
        page.mouse.move(x, y)
        page.mouse.click(x, y)
        page.wait_for_timeout(500)  
        
        
        scroll_success = False
        for i in range(max_scroll_attempts):
            
            page.mouse.move(x, y)
            
            
            page.mouse.wheel(0, 100 * (i + 1))  
            
            
            page.wait_for_timeout(1000)  
            
            scroll_success = True
        
        return scroll_success
            
    except Exception as e:
        print(f"Error in handle_zillow_sidebar_scrolling: {e}")
        
        return _handle_zillow_sidebar_js_scrolling(page, max_scroll_attempts)

def _handle_zillow_sidebar_js_scrolling(page, max_scroll_attempts=5):
    """
    Fallback method that uses JavaScript to scroll the sidebar on Zillow.
    
    Args:
        page: The Playwright page object
        max_scroll_attempts: Maximum number of scroll attempts to make
    
    Returns:
        bool: True if scrolling was successful, False otherwise
    """
    try:
        
        js_scroll_attempts = [
            """
            const sidebar = document.querySelector('div[data-testid="search-filters"]') || 
                           document.querySelector('.filter-bar') ||
                           document.querySelector('.search-page-filter-menu') ||
                           document.querySelector('div[id*="filter"]') ||
                           document.querySelector('div[class*="filter"]');
            if (sidebar) {
                sidebar.scrollTop += 500;
                return true;
            }
            return false;
            """,
            
            
            """
            let scrolled = false;
            const scrollables = Array.from(document.querySelectorAll('div'))
                .filter(div => {
                    const style = window.getComputedStyle(div);
                    return (style.overflowY === 'auto' || style.overflowY === 'scroll') && 
                           div.scrollHeight > div.clientHeight;
                });
            
            for (const div of scrollables) {
                div.scrollTop += 200;
                scrolled = true;
            }
            return scrolled;
            """,
            
            
            """
            const filterKeywords = ['filter', 'price', 'bed', 'bath', 'home type'];
            const elements = Array.from(document.querySelectorAll('div, section, aside'));
            
            for (const elem of elements) {
                if (filterKeywords.some(keyword => elem.innerText.toLowerCase().includes(keyword))) {
                    elem.scrollTop += 300;
                    return true;
                }
            }
            return false;
            """
        ]
        
        success = False
        for i in range(max_scroll_attempts):
            for js_script in js_scroll_attempts:
                result = page.evaluate(js_script)
                if result:
                    success = True
                    page.wait_for_timeout(800)  
        
        return success
        
    except Exception as e:
        print(f"Error in _handle_zillow_sidebar_js_scrolling: {e}")
        return False

# Enhanced database functions from real_estate.py
def parse_int_from_text(text): 
    """Extract integer from text (e.g. '$3,200/month' -> 3200)"""
    if text is None or text == "": 
        return 0 
    # Extract digits from text
    digits = re.findall(r'\d+', str(text).replace(',', '')) 
    return int(digits[0]) if digits else 0

def validate_listing_data(listing_data):
    """Enhanced validation and cleaning of listing data"""
    if not isinstance(listing_data, dict):
        logger.warning(f"Invalid listing data type: {type(listing_data)}")
        return None
    
    # Create a clean copy
    cleaned_data = {}
    
    # Clean and validate title
    title = listing_data.get('title') or listing_data.get('description') or 'Untitled Listing'
    cleaned_data['title'] = str(title).strip()[:255]  # Limit to 255 chars
    
    # Clean and validate location
    location = listing_data.get('location') or listing_data.get('address') or 'Unknown Location'
    cleaned_data['location'] = str(location).strip()[:100]  # Limit to 100 chars
    
    # Clean and validate price
    price = listing_data.get('price', '')
    if isinstance(price, (int, float)):
        cleaned_data['price'] = str(int(price))
    else:
        # Extract numeric price if it's a string like "$500,000"
        price_num = parse_int_from_text(price)
        cleaned_data['price'] = str(price_num) if price_num > 0 else str(price)
    
    # Clean and validate bedrooms
    bedrooms = listing_data.get('bedrooms') or listing_data.get('beds', '')
    bedrooms_num = parse_int_from_text(bedrooms)
    cleaned_data['bedrooms'] = str(bedrooms_num) if bedrooms_num > 0 else str(bedrooms)
    
    # Clean and validate bathrooms  
    bathrooms = listing_data.get('bathrooms') or listing_data.get('baths', '')
    bathrooms_num = parse_int_from_text(bathrooms)
    cleaned_data['bathrooms'] = str(bathrooms_num) if bathrooms_num > 0 else str(bathrooms)
    
    # Clean and validate size/area
    size = (listing_data.get('area') or listing_data.get('size') or 
            listing_data.get('square_footage') or listing_data.get('sqft', ''))
    size_num = parse_int_from_text(size)
    cleaned_data['size'] = str(size_num) if size_num > 0 else str(size)
    
    # Handle date/time
    date_val = listing_data.get('time') or listing_data.get('date') or 'Recent'
    cleaned_data['date'] = str(date_val).strip()[:50]  # Limit to 50 chars
    
    # Collect other fields
    other_fields = {}
    excluded_fields = {'title', 'description', 'location', 'address', 'price', 
                      'bedrooms', 'beds', 'bathrooms', 'baths', 'size', 'area', 
                      'square_footage', 'sqft', 'date', 'time'}
    
    for key, value in listing_data.items():
        if key not in excluded_fields and value is not None:
            other_fields[key] = str(value)
    
    cleaned_data['other'] = json.dumps(other_fields)
    
    logger.debug(f"✅ Cleaned listing data: {json.dumps(cleaned_data, indent=2)}")
    return cleaned_data

def enhanced_insert_listing(listing_data):
    """Enhanced version of insert_listing with better validation and error handling"""
    try:
        # Validate and clean the data first
        cleaned_data = validate_listing_data(listing_data)
        if not cleaned_data:
            logger.error("❌ Failed to validate listing data")
            return False
        
        # Use the standard insert_listing function with cleaned data
        result = insert_listing(cleaned_data)
        
        if result:
            logger.info(f"✅ Successfully inserted listing: {cleaned_data.get('title', 'Unknown')}")
            logger.info(f"   📍 Location: {cleaned_data.get('location', 'Unknown')}")
            logger.info(f"   💰 Price: {cleaned_data.get('price', 'Unknown')}")
            logger.info(f"   🏠 {cleaned_data.get('bedrooms', '?')} bed, {cleaned_data.get('bathrooms', '?')} bath")
        else:
            logger.error(f"❌ Failed to insert listing: {cleaned_data.get('title', 'Unknown')}")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Error in enhanced_insert_listing: {e}")
        import traceback
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    main()
