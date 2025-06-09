import json
import logging
from typing import Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from browser_use import Agent, BrowserConfig
from browser_use.browser.browser import Browser
from browser_use.browser.context import BrowserContextConfig

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Imports for real estate (unchanged)
from database.real_estate import get_db_connection, create_table_if_not_exists, insert_listing_data, parse_int_from_text, parse_date_from_text
# Imports for interest rates
from database.interest_rates import insert_interest_rate_data, parse_float_from_text
from datetime import datetime
import uuid
import re

def generate_id():
    return uuid.uuid4().int & ((1 << 31) - 1)  # Use 32-bit range to be safe

def log_scrape(website_url, task_type, status, message, raw_data, error_message=None):
    # Ensure raw_data is a dictionary and has the expected structure
    if not isinstance(raw_data, dict):
        logger.warning(f"raw_data is not a dict: {type(raw_data)}")
        return
        
    detailed_result = raw_data.get("detailed_result")
    if not detailed_result or not isinstance(detailed_result, list):
        logger.warning(f"No valid detailed_result found or not a list: {type(detailed_result)}")
        return

    conn = get_db_connection()
    if not conn:
        logger.error("Could not connect to DB")
        return

    try:
        cursor = conn.cursor()
        
        # Original real estate logic (unchanged)
        if task_type == "real_estate":
            create_table_if_not_exists(cursor)
            for listing in detailed_result:
                if not isinstance(listing, dict):
                    logger.warning(f"Listing is not a dict: {type(listing)}")
                    continue
                
                structured_data = {
                    "id": generate_id(),
                    "title": listing.get("name", "N/A"),
                    "date": datetime.now().date(),
                    "location": listing.get("address", "N/A"),
                    "price": parse_int_from_text(listing.get("price")),
                    "bedrooms": parse_int_from_text(listing.get("number_of_beds")),
                    "bathrooms": 0,
                    "size": parse_int_from_text(listing.get("size")),
                    "other": listing.get("amenities", ""),
                    "created_at": datetime.now()
                }
                insert_listing_data(cursor, structured_data)
        
        # Interest rate logic (unchanged)
        elif task_type == "interest_rate":
            for rate in detailed_result:
                if not isinstance(rate, dict):
                    logger.warning(f"Rate entry is not a dict: {type(rate)}")
                    continue
                structured_data = {
                    "id": generate_id(),
                    "rate_type": rate.get("rate_type", rate.get("category", "Unknown Type")),
                    "rate": parse_float_from_text(rate.get("rate")),
                    "apr": parse_float_from_text(rate.get("apr", "")),
                    "institution": rate.get("institution", ""),
                    "updated": rate.get("updated", ""),
                    "source_url": website_url,
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                if structured_data["rate_type"] == "Unknown Type" or structured_data["rate"] is None:
                    logger.warning(f"Skipping invalid interest rate entry: {rate}")
                    continue
                insert_interest_rate_data(cursor, structured_data)
        
        conn.commit()
        logger.info("Data logged into DB successfully")
    except Exception as e:
        logger.error(f"Error while logging to DB: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Updated Pydantic model for request validation
class ScrapeRequest(BaseModel):
    website_url: str
    task_type: str  # "real_estate" or "interest_rate"
    location: Optional[str] = None
    additional_instructions: Optional[str] = None

class GeminiBrowserAgent:
    def __init__(self, gemini_api_key: Optional[str] = None):
        self.api_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Gemini API Key not provided or found in environment.")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",
            api_key=self.api_key,
        )

        self.browser = Browser(
            config=BrowserConfig(
                new_context_config=BrowserContextConfig(
                    viewport_expansion=0
                )
            )
        )

        logger.info("GeminiBrowserAgent initialized.")

    async def execute_task(self, websites: Dict[str, str], max_steps: int = 25, location: Optional[str] = None, additional_instructions: Optional[str] = None) -> Dict[str, Any]:
        try:
            task_description = ""
            for website, task_type in websites.items():
                if task_type == "interest_rate":
                    additional_instructions_str = f" Additional instructions: {additional_instructions}" if additional_instructions else ""
                    task_description += f"""
Go to the website {website} and retrieve the current interest rates. Perform any necessary actions (e.g., clicking buttons or navigating to rate tables) to access the rates. Extract all interest rate data as a flat JSON array of objects, each containing: rate_type, rate, apr, term, minimum_balance, currency, institution, updated, source_url. Use 'N/A' for unavailable data. Do not nest the array inside other objects or include summary text outside the array.{additional_instructions_str}
"""
                elif task_type == "real_estate":
                    location_str = f" in {location}" if location else ""
                    additional_instructions_str = f" Additional instructions: {additional_instructions}" if additional_instructions else ""
                    task_description += f"""
Go to the website {website} and search for real estate listings for homes/apartments for sale/rent{location_str}. After any redirection or search, scroll vertically downwards to the bottom of the page to ensure all listings are loaded. Continue scrolling until no new listings appear. Extract all listings with their key details (name, address, price, number of beds, size, amenities) in a structured JSON array of objects. Include all listings without arbitrary filtering unless specified in additional instructions. Ensure all fields are included, using 'N/A' for unavailable data (e.g., amenities). Do not return summary messages; only provide the JSON array.{additional_instructions_str}
"""
                else:
                    logger.warning(f"Unknown task type for {website}, skipping.")

            agent = Agent(
                task=task_description,
                llm=self.llm,
                max_actions_per_step=4,
                browser=self.browser
            )

            agent_history = await agent.run(max_steps=max_steps)
            detailed_result = []

            try:
                extracted_contents = agent_history.extracted_content()
                if extracted_contents:
                    for content in extracted_contents:
                        try:
                            # Preprocess content to extract JSON
                            json_content = content
                            if isinstance(content, str):
                                # Find the first occurrence of JSON-like content
                                match = re.search(r'(\[\s*{[\s\S]*?}\s*\]|{\s*[\s\S]*?\s*})', content, re.DOTALL)
                                if match:
                                    json_content = match.group(1)
                                elif '```json' in content:
                                    # Extract between ```json and ```
                                    match = re.search(r'```json\s*([\s\S]*?)\s*```', content, re.DOTALL)
                                    if match:
                                        json_content = match.group(1)
                                else:
                                    # Strip any prefix before JSON
                                    json_start = content.find('[')
                                    json_end = content.rfind(']') + 1
                                    if json_start != -1 and json_end > json_start:
                                        json_content = content[json_start:json_end]

                            parsed = json.loads(json_content)
                            # Handle mortgage rates for interest_rate task
                            if isinstance(parsed, dict) and "mortgage_rates" in parsed and task_type == "interest_rate":
                                rates = parsed.get("mortgage_rates", [])
                                if isinstance(rates, list):
                                    updated = parsed.get("date", "N/A")
                                    for item in rates:
                                        detailed_result.append({
                                            "rate_type": item.get("term", "Unknown Type"),
                                            "rate": item.get("rate", "N/A"),
                                            "apr": item.get("apr", "N/A"),
                                            "term": item.get("term", "N/A"),
                                            "minimum_balance": "N/A",
                                            "currency": "USD",
                                            "institution": "Bank of America",
                                            "updated": updated,
                                            "source_url": website
                                        })
                                    break
                            # Handle flat JSON array
                            elif isinstance(parsed, list) and parsed and all(isinstance(item, dict) for item in parsed):
                                # Fix relative source_url
                                for item in parsed:
                                    if item.get("source_url", "").startswith("/"):
                                        item["source_url"] = f"https://www.federalreserve.gov{item['source_url']}"
                                detailed_result = parsed
                                break
                            # Existing logic for other cases
                            elif isinstance(parsed, dict) and "interest_rates" in parsed:
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
                                detailed_result = flattened
                                break
                        except json.JSONDecodeError as e:
                            logger.warning(f"Could not parse content as JSON: {content} (Error: {str(e)})")
                            continue
                    else:
                        logger.warning("No valid JSON content found in extracted contents")
            except Exception as e:
                logger.error(f"Error extracting content: {str(e)}")
                detailed_result = []

            # Ensure we always return a consistent structure
            return {
                "status": "success" if detailed_result else "partial_success",
                "message": "Task completed successfully." if detailed_result else "Task completed but no valid data extracted.",
                "detailed_result": detailed_result
            }

        except Exception as e:
            logger.error(f"Task execution failed: {str(e)}")
            return {
                "status": "failure",
                "message": str(e),
                "detailed_result": []
            }

@app.options("/extract")
async def options_extract():
    return JSONResponse(status_code=200, content={})

@app.post("/extract")
async def extract_data(request: ScrapeRequest):
    try:
        # Initialize the agent
        agent = GeminiBrowserAgent()
        
        # Execute the task
        websites = {request.website_url: request.task_type}
        result = await agent.execute_task(
            websites=websites,
            location=request.location,
            additional_instructions=request.additional_instructions
        )

        # Log the scrape (only if result is properly structured)
        try:
            log_scrape(
                website_url=request.website_url,
                task_type=request.task_type,
                status=result.get("status", "unknown"),
                message=result.get("message", ""),
                raw_data=result
            )
        except Exception as log_error:
            logger.error(f"Failed to log to database: {log_error}")
            # Don’t fail the entire request if DB logging fails
        
        # Return the result in the format expected by frontend
        return {
            "status": result.get("status", "failure"),
            "message": result.get("message", "Unknown error"),
            "detailed_result": result.get("detailed_result", [])
        }
        
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        
        # Try to log the error (with safe parameters)
        try:
            log_scrape(
                website_url=request.website_url,
                task_type=request.task_type,
                status="error",
                message="Failed to extract data",
                raw_data={"detailed_result": []},
                error_message=str(e)
            )
        except Exception as log_error:
            logger.error(f"Failed to log error to database: {log_error}")
        
        raise HTTPException(status_code=500, detail=f"Oops! Something went wrong: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)