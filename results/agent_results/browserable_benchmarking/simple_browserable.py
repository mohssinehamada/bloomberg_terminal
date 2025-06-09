import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json
import time
from bs4 import BeautifulSoup
import requests
from typing import Dict, List, Optional, Union
import logging
import re
from aryan.performance_metrics import get_performance_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Task:
    def __init__(self, description: str, steps: List[Dict]):
        self.description = description
        self.steps = steps
        self.current_step = 0
        
    def next_step(self) -> Optional[Dict]:
        if self.current_step < len(self.steps):
            step = self.steps[self.current_step]
            self.current_step += 1
            return step
        return None

class EnhancedBrowserable:
    TASKS = {
        'federal_reserve_rates': {
            'description': 'Extract Federal Reserve interest rates for a specific year',
            'steps': [
                {'action': 'open_url', 'params': {'url': 'google.com'}},
                {'action': 'type_text', 'params': {'selector': 'textarea[name="q"]', 'text': 'Federal Reserve interest rates projections {year}', 'submit': True}},
                {'action': 'wait_and_click', 'params': {'selector': 'a[href*="federalreserve.gov"]'}},
                {'action': 'extract_rates', 'params': {'year': '{year}'}}
            ]
        }
    }

    def __init__(self, gemini_api_key: str):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.current_url = None
        self.session_id = None
        self.gemini_api_key = gemini_api_key
        self.current_task = None
        
        # Initialize Gemini
        try:
            genai.configure(api_key=gemini_api_key)
            self.model = genai.GenerativeModel('gemini-pro')
        except Exception as e:
            logger.warning(f"Failed to initialize Gemini: {e}")
            self.model = None
        
        # Initialize browser state
        self.browser_state = {
            'tabs': [],
            'current_tab': None,
            'history': []
        }

    def start(self):
        """Initialize the browser session with enhanced error handling"""
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(
                headless=False,
                args=['--start-maximized']
            )
            self.context = self.browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            )
            self.page = self.context.new_page()
            self.session_id = f"session_{int(time.time())}"
            logger.info("Browser session started successfully!")
            return True
        except Exception as e:
            logger.error(f"Failed to start browser session: {e}")
            self.cleanup()
            return False

    def cleanup(self):
        """Clean up resources"""
        try:
            if self.page:
                self.page.close()
            if self.context:
                self.context.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

    def open_url(self, url: str) -> Dict:
        """Navigate to a specific URL with enhanced error handling and state tracking"""
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Add timeout and wait for network idle
            self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
            self.current_url = self.page.url
            
            # Update browser state
            self.browser_state['history'].append({
                'url': self.current_url,
                'timestamp': time.time()
            })
            
            # Get page metadata
            title = self.page.title()
            logger.info(f"Navigated to: {self.current_url} (Title: {title})")
            
            return {
                'success': True,
                'url': self.current_url,
                'title': title,
                'status': 'success'
            }
        except PlaywrightTimeoutError:
            logger.error(f"Timeout while navigating to {url}")
            return {
                'success': False,
                'error': 'timeout',
                'status': 'error'
            }
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return {
                'success': False,
                'error': str(e),
                'status': 'error'
            }

    def get_page_content(self) -> Dict:
        """Get enhanced page content with structured data"""
        try:
            # Wait for page to be fully loaded
            self.page.wait_for_load_state('domcontentloaded')
            
            # Get basic content
            content = {
                'title': self.page.title(),
                'url': self.page.url,
                'html': self.page.content(),
                'text': self.page.inner_text('body')
            }
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(content['html'], 'html.parser')
            
            # Extract structured data
            content['links'] = [{'text': a.text.strip(), 'href': a.get('href')} 
                              for a in soup.find_all('a', href=True)]
            content['forms'] = [{'id': form.get('id'), 'action': form.get('action')} 
                              for form in soup.find_all('form')]
            content['images'] = [{'src': img.get('src'), 'alt': img.get('alt')} 
                               for img in soup.find_all('img')]
            
            return content
        except Exception as e:
            logger.error(f"Error getting page content: {e}")
            return {'error': str(e)}

    def extract_table_data(self) -> Dict:
        """Extract table data from the current page"""
        try:
            tables = []
            # Get all tables from the page
            table_elements = self.page.query_selector_all('table')
            
            for idx, table in enumerate(table_elements):
                # Extract table HTML
                table_html = table.inner_html()
                
                # Parse with BeautifulSoup
                soup = BeautifulSoup(f"<table>{table_html}</table>", 'html.parser')
                
                # Extract headers
                headers = []
                for th in soup.find_all('th'):
                    headers.append(th.text.strip())
                
                # Extract rows
                rows = []
                for tr in soup.find_all('tr'):
                    row = []
                    for td in tr.find_all('td'):
                        row.append(td.text.strip())
                    if row:  # Only add non-empty rows
                        rows.append(row)
                
                tables.append({
                    'table_index': idx,
                    'headers': headers,
                    'rows': rows
                })
            
            return {
                'success': True,
                'tables': tables
            }
        except Exception as e:
            logger.error(f"Error extracting table data: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def extract_rates(self, year: str = None) -> Dict:
        """Extract interest rates with optional year filter"""
        try:
            # Get all text content
            content = self.page.content()
            soup = BeautifulSoup(content, 'html.parser')
            
            # Look for rate information
            rate_patterns = [
                r'(\d+\.?\d*)\s*%',  # Matches percentage numbers
                r'rate[s]?\s*(?:of|:)?\s*(\d+\.?\d*)\s*%',  # Matches "rate(s): X%"
                r'interest\s*rate[s]?\s*(?:of|:)?\s*(\d+\.?\d*)\s*%'  # Matches "interest rate(s): X%"
            ]
            
            rates = []
            for pattern in rate_patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    rate_value = match.group(1)
                    context = content[max(0, match.start() - 50):min(len(content), match.end() + 50)]
                    rates.append({
                        'rate': float(rate_value),
                        'context': context.strip()
                    })
            
            # Filter by year if specified
            if year:
                rates = [rate for rate in rates if year in rate['context']]
            
            return {
                'success': True,
                'rates': rates
            }
        except Exception as e:
            logger.error(f"Error extracting rates: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def wait_for_element(self, selector: str, timeout: int = 10000) -> bool:
        """Wait for an element to be visible and clickable"""
        try:
            self.page.wait_for_selector(selector, state='visible', timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            logger.error(f"Timeout waiting for element: {selector}")
            return False
        except Exception as e:
            logger.error(f"Error waiting for element: {e}")
            return False

    def click_element(self, selector: str, wait_for_navigation: bool = True) -> Dict:
        """Enhanced element clicking with navigation handling"""
        try:
            # Wait for element to be visible and clickable
            if not self.wait_for_element(selector):
                return {'success': False, 'error': 'Element not found'}
            
            if wait_for_navigation:
                with self.page.expect_navigation():
                    self.page.click(selector)
            else:
                self.page.click(selector)
            
            logger.info(f"Clicked element: {selector}")
            return {'success': True, 'status': 'clicked'}
        except Exception as e:
            logger.error(f"Error clicking element: {e}")
            return {'success': False, 'error': str(e)}

    def type_text(self, selector: str, text: str, submit: bool = False) -> Dict:
        """Enhanced text input with validation and optional submit"""
        try:
            # Wait for element to be visible and editable
            if not self.wait_for_element(selector):
                return {'success': False, 'error': 'Element not found'}
            
            # Clear existing text and type new text
            self.page.fill(selector, '')
            self.page.type(selector, text)
            
            # Submit if requested
            if submit:
                self.page.press(selector, 'Enter')
            
            logger.info(f"Typed text: {text} into {selector}")
            return {'success': True, 'status': 'typed'}
        except Exception as e:
            logger.error(f"Error typing text: {e}")
            return {'success': False, 'error': str(e)}

    def take_screenshot(self, filename: str = None) -> Optional[str]:
        """Enhanced screenshot functionality"""
        try:
            if filename is None:
                filename = f"screenshot_{int(time.time())}.png"
            
            # Take full page screenshot
            self.page.screenshot(
                path=filename,
                full_page=True,
                type='png'
            )
            
            logger.info(f"Screenshot saved as: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error taking screenshot: {e}")
            return None

    def analyze_page_with_gemini(self, query: str) -> Dict:
        """Use Gemini to analyze page content"""
        if not self.model:
            return {'success': False, 'error': 'Gemini not initialized'}
            
        try:
            # Get page content
            content = self.get_page_content()
            if 'error' in content:
                return {'success': False, 'error': content['error']}
            
            # Prepare prompt for Gemini
            prompt = f"""
            Analyze this webpage content and answer the following query:
            Query: {query}
            
            Page Title: {content['title']}
            Page URL: {content['url']}
            Main Text: {content['text'][:1000]}...
            
            Please provide a detailed analysis.
            """
            
            # Get response from Gemini
            response = self.model.generate_content(prompt)
            
            return {
                'success': True,
                'analysis': response.text,
                'query': query
            }
        except Exception as e:
            logger.error(f"Error analyzing page with Gemini: {e}")
            return {'success': False, 'error': str(e)}

    def execute_task(self, task_name: str, **kwargs) -> Dict:
        """Execute a predefined task with parameters"""
        try:
            if task_name not in self.TASKS:
                return {'success': False, 'error': f'Task {task_name} not found'}
            
            task_template = self.TASKS[task_name]
            # Format task steps with provided parameters
            steps = []
            for step in task_template['steps']:
                formatted_step = {
                    'action': step['action'],
                    'params': {
                        k: v.format(**kwargs) if isinstance(v, str) else v
                        for k, v in step['params'].items()
                    }
                }
                steps.append(formatted_step)
            
            task = Task(task_template['description'], steps)
            self.current_task = task
            
            # Execute each step
            results = []
            while (step := task.next_step()) is not None:
                logger.info(f"Executing step: {step['action']}")
                result = getattr(self, step['action'])(**step['params'])
                results.append(result)
                
                if not result.get('success', False):
                    return {
                        'success': False,
                        'error': f"Step {step['action']} failed: {result.get('error')}",
                        'partial_results': results
                    }
                
                # Add delay between steps
                time.sleep(2)
            
            return {
                'success': True,
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error executing task: {e}")
            return {'success': False, 'error': str(e)}

    def wait_and_click(self, selector: str) -> Dict:
        """Wait for element to appear and click it"""
        try:
            self.page.wait_for_selector(selector, state='visible', timeout=10000)
            self.page.click(selector)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def close(self):
        """Enhanced browser cleanup"""
        self.cleanup()
        logger.info("Browser session closed successfully")

def main():
    # Load environment variables
    load_dotenv()
    
    # Get Gemini API key from environment or user input
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if not gemini_api_key:
        gemini_api_key = input("Enter your Gemini API key (press Enter to skip): ")
    
    # Create an instance of EnhancedBrowserable
    browser = EnhancedBrowserable(gemini_api_key)
    
    try:
        # Start the browser
        if not browser.start():
            print("Failed to start browser session. Exiting...")
            return
        
        while True:
            print("\n" + "="*50)
            print("Available Commands:".center(50))
            print("="*50)
            print("1. task <task_name> [params]".ljust(30) + "- Run automated task")
            print("2. open <url>".ljust(30) + "- Open a URL")
            print("3. content".ljust(30) + "- Get page content")
            print("4. click <selector>".ljust(30) + "- Click an element")
            print("5. type <selector> <text>".ljust(30) + "- Type text")
            print("6. submit <selector> <text>".ljust(30) + "- Type and submit")
            print("7. screenshot".ljust(30) + "- Take screenshot")
            print("8. extract tables".ljust(30) + "- Extract table data")
            print("9. extract rates [year]".ljust(30) + "- Extract interest rates")
            if browser.model:
                print("10. analyze <query>".ljust(30) + "- Analyze with Gemini")
            print("11. exit".ljust(30) + "- Close and exit")
            print("\nAvailable Tasks:")
            for task_name, task_info in browser.TASKS.items():
                print(f"- {task_name}: {task_info['description']}")
            print("="*50)
            
            try:
                command = input("\nEnter command: ").strip()

                # Check for performance metrics and save if matched
                metrics_json = get_performance_metrics(command)
                if not metrics_json.startswith('{"error"'):
                    safe_query = command.replace(' ', '_').replace('/', '_')
                    filename = os.path.join(os.path.dirname(__file__), f"performance_metrics_{safe_query}.json")
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(metrics_json)
                    print(f"Performance metrics saved to {filename}")
                    continue  # Skip the rest of the loop for this command

                if command.startswith("task "):
                    parts = command[5:].strip().split()
                    task_name = parts[0]
                    params = {}
                    if len(parts) > 1:
                        params['year'] = parts[1]
                    
                    print(f"\nExecuting task: {task_name}")
                    result = browser.execute_task(task_name, **params)
                    
                    if result['success']:
                        print("\nTask completed successfully!")
                        if 'results' in result:
                            for idx, step_result in enumerate(result['results']):
                                if 'rates' in step_result:
                                    print("\nExtracted Rates:")
                                    for rate in step_result['rates']:
                                        print(f"\nRate: {rate['rate']}%")
                                        print(f"Context: {rate['context']}")
                    else:
                        print(f"\nTask failed: {result.get('error', 'Unknown error')}")
                
                elif command.startswith("open "):
                    url = command[5:].strip()
                    result = browser.open_url(url)
                    if not result['success']:
                        print(f"Error: {result.get('error', 'Unknown error')}")
                
                elif command == "content":
                    content = browser.get_page_content()
                    if 'error' in content:
                        print(f"Error: {content['error']}")
                    else:
                        print("\nPage Content:")
                        print(f"Title: {content['title']}")
                        print(f"URL: {content['url']}")
                        print("\nText Preview:")
                        print(content['text'][:500] + "...")
                
                elif command.startswith("click "):
                    selector = command[6:].strip()
                    result = browser.click_element(selector)
                    if not result['success']:
                        print(f"Error: {result.get('error', 'Unknown error')}")
                
                elif command.startswith("type "):
                    parts = command[5:].strip().split(" ", 1)
                    if len(parts) == 2:
                        selector, text = parts
                        result = browser.type_text(selector, text)
                        if not result['success']:
                            print(f"Error: {result.get('error', 'Unknown error')}")
                    else:
                        print("Invalid format. Use: type <selector> <text>")
                
                elif command.startswith("submit "):
                    parts = command[7:].strip().split(" ", 1)
                    if len(parts) == 2:
                        selector, text = parts
                        result = browser.type_text(selector, text, submit=True)
                        if not result['success']:
                            print(f"Error: {result.get('error', 'Unknown error')}")
                    else:
                        print("Invalid format. Use: submit <selector> <text>")
                
                elif command == "extract tables":
                    result = browser.extract_table_data()
                    if result['success']:
                        print("\nExtracted Tables:")
                        for table in result['tables']:
                            print(f"\nTable {table['table_index']}:")
                            print("Headers:", table['headers'])
                            print("Rows:")
                            for row in table['rows']:
                                print(row)
                    else:
                        print(f"Error: {result.get('error', 'Unknown error')}")
                
                elif command.startswith("extract rates"):
                    parts = command.split()
                    year = parts[2] if len(parts) > 2 else None
                    result = browser.extract_rates(year)
                    if result['success']:
                        print("\nExtracted Rates:")
                        for rate in result['rates']:
                            print(f"\nRate: {rate['rate']}%")
                            print(f"Context: {rate['context']}")
                    else:
                        print(f"Error: {result.get('error', 'Unknown error')}")
                
                elif command == "screenshot":
                    filename = f"screenshot_{int(time.time())}.png"
                    result = browser.take_screenshot(filename)
                    if result:
                        print(f"Screenshot saved as: {filename}")
                    else:
                        print("Failed to take screenshot")
                
                elif command.startswith("analyze ") and browser.model:
                    query = command[8:].strip()
                    result = browser.analyze_page_with_gemini(query)
                    if result['success']:
                        print("\nAnalysis:")
                        print(result['analysis'])
                    else:
                        print(f"Error: {result.get('error', 'Unknown error')}")
                
                elif command == "exit":
                    break
                
                else:
                    print("Invalid command. Please try again.")
            
            except KeyboardInterrupt:
                print("\nOperation cancelled by user")
                continue
            except Exception as e:
                print(f"Error processing command: {e}")
                continue
    
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        # Always close the browser when done
        browser.close()

if __name__ == "__main__":
    main() 