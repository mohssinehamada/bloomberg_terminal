import os
import json
import logging
from typing import Optional, Dict, Any, List
import asyncio
import random
import time

from dotenv import load_dotenv
from pydantic import SecretStr
from langchain_google_genai import ChatGoogleGenerativeAI

from browser_use import Agent, BrowserConfig
from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContextConfig

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

class GeminiBrowserAgent:
    def __init__(self, gemini_api_key: Optional[str] = None, task: Optional[str] = None, **kwargs):
        self.api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API Key not provided or found in environment.")

        self.task = task or "Visit a website and extract relevant data."

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            api_key=SecretStr(self.api_key),
            **kwargs
        )

        self.browser = Browser(
            config=BrowserConfig(
                new_context_config=BrowserContextConfig(
                    viewport_expansion=0,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                    stealth_mode=True
                )
            )
        )

        logger.info("GeminiBrowserAgent initialized.")

    def generate_text_gemini(self, prompt: str) -> str:
        try:
            response = self.llm.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini text generation error: {str(e)}")
            return f"Error: {str(e)}"

    async def analyze_with_gemini(self, content: str, instruction: str) -> Dict[str, Any]:
        try:
            prompt = f"""
CONTENT:
{content}

INSTRUCTION:
{instruction}

Respond with a structured JSON object with your analysis.
"""
            response = self.llm.generate_content(prompt)
            try:
                return json.loads(response.text.strip())
            except json.JSONDecodeError:
                logger.warning("Could not parse JSON. Returning raw response.")
                return {"raw_response": response.text}
        except Exception as e:
            logger.error(f"Gemini analysis failed: {str(e)}")
            return {"error": str(e)}

    async def execute_task(self, websites: Dict[str, str], max_steps: int = 25, location: Optional[str] = None, additional_instructions: Optional[str] = None) -> Dict[str, Any]:
        try:
            task_description = ""
            for website, task_type in websites.items():
                if task_type == "interest_rate":
                    additional_instructions_str = f" Additional instructions: {additional_instructions}" if additional_instructions else ""
                    task_description += f"Go to the website {website} and retrieve the current interest rates. Perform any necessary actions (e.g., clicking buttons or navigating to rate tables) as specified in additional instructions. Extract all interest rate data (e.g., rate type, rate, term, minimum balance, currency) in a structured JSON array of objects, combining all relevant categories (e.g., saving deposits, fixed deposits, loans). Ensure all fields are included, using 'N/A' for unavailable data. Do not return summary messages; only provide the JSON array.{additional_instructions_str}\n"
                elif task_type == "real_estate":
                    location_str = f" in {location}" if location else ""
                    additional_instructions_str = f" Additional instructions: {additional_instructions}" if additional_instructions else ""
                    task_description += f"Go to the website {website} and search for real estate listings for homes/apartments for sale/rent{location_str}. After any redirection or search, scroll vertically downwards to the bottom of the page to ensure all listings are loaded. Continue scrolling until no new listings appear. Extract all listings with their key details (name, address, price, number of beds, size, amenities) in a structured JSON array of objects. Include all listings without arbitrary filtering unless specified in additional instructions. Ensure all fields are included, using 'N/A' for unavailable data (e.g., amenities). Do not return summary messages; only provide the JSON array.{additional_instructions_str}\n"
                else:
                    logger.warning(f"Unknown task type for {website}, skipping.")

            agent = Agent(
                task=task_description,
                llm=self.llm,
                max_actions_per_step=4,
                browser=self.browser
            )

            agent_history = await agent.run(max_steps=max_steps, wait_for_network_idle=True)
            
            logger.debug(f"Agent history type: {type(agent_history)}")
            logger.debug(f"Agent history content: {agent_history}")
            
            detailed_result = "No detailed result available."
            try:
                extracted_contents = agent_history.get('extracted_content', [])
                logger.debug(f"Extracted contents: {extracted_contents}")
                if extracted_contents:
                    for content in extracted_contents:
                        try:
                            parsed = json.loads(content)
                            if isinstance(parsed, dict) and "interest_rates" in parsed:
                                # Flatten interest rate data into a single array
                                flattened = []
                                for category, data in parsed["interest_rates"].items():
                                    if isinstance(data, list):
                                        for item in data:
                                            item["category"] = category.replace("_", " ").title()
                                            flattened.append(item)
                                    elif isinstance(data, dict):
                                        for subcat, subdata in data.items():
                                            for item in subdata:
                                                item["category"] = f"{category.replace('_', ' ').title()} - {subcat.replace('_', ' ').title()}"
                                                flattened.append(item)
                                detailed_result = json.dumps(flattened, indent=2)
                                break
                            elif isinstance(parsed, list) and parsed and all(isinstance(item, dict) for item in parsed):
                                detailed_result = json.dumps(parsed, indent=2)
                                break
                        except json.JSONDecodeError:
                            continue
                    else:
                        detailed_result = extracted_contents[-1] if extracted_contents else "No valid data extracted."
            except Exception as e:
                logger.error(f"Error extracting content: {str(e)}")
                detailed_result = f"Error extracting content: {str(e)}"
            
            time.sleep(random.uniform(1, 3))  # Random delay between actions
            
            return {
                "status": "success",
                "message": "Task completed successfully.",
                "detailed_result": detailed_result
            }

        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}")
            return {
                "status": "failure",
                "message": str(e),
                "detailed_result": None
            }

def get_user_input():
    print("\n--- Browser Automation with Gemini ---")
    print("Select a task:")
    print("1. Extract financial interest rates")
    print("2. Browse real estate listings")
    
    while True:
        choice = input("\nEnter your choice (1 or 2): ").strip()
        if choice in ["1", "2"]:
            break
        print("Invalid choice. Please enter 1 or 2.")
    
    url = input("\nEnter the website URL to visit: ").strip()
    
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
        print(f"URL updated to: {url}")
    
    task_type = "interest_rate" if choice == "1" else "real_estate"
    
    location = None
    additional_instructions = None
    if task_type == "real_estate":
        location = input("\nEnter the location (e.g., Mumbai, India): ").strip()
    additional_instructions = input("\nEnter additional instructions (e.g., For real estate: 'Focus on apartments with 2+ bedrooms'; For interest rates: 'Click View Rates button') [optional, press Enter to skip]: ").strip() or None
    
    return url, task_type, location, additional_instructions

def main():
    try:
        url, task_type, location, additional_instructions = get_user_input()
        websites = {url: task_type}
        print(f"\nExecuting task: {task_type} on {url}" + (f" for location: {location}" if location else "") + (f" with instructions: {additional_instructions}" if additional_instructions else ""))
        agent = GeminiBrowserAgent()
        result = asyncio.run(agent.execute_task(websites=websites, location=location, additional_instructions=additional_instructions))
        logging.info(f"Task Result: {result}")
        print(f"\nTask completed with status: {result['status']}")
    except KeyboardInterrupt:
        logging.warning("Execution interrupted by user.")
        print("\nOperation canceled by user.")
    except Exception as e:
        logging.error(f"Execution failed: {e}")
        print(f"\nAn error occurred: {str(e)}")

if __name__ == "__main__":
    main()
