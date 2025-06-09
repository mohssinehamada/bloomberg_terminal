from openai import OpenAI
import json
import time
from dotenv import load_dotenv
import os
from tools.openai.browser_tools import search_google, open_link, scrape_text
from tools.openai.extractors import extract_interest_rate, extract_estate_listings
from tools.openai.utils import save_results
import openai
    
# Load environment variables
load_dotenv()

# Set up OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

#define the agent's task
functions = [
    {
        "type": "function",
        "function": {
            "name": "search_google",
            "description":"Perform a Google search and return top URLS",
            "parameters":{ "type": "object","properties":{"query": {"type": "string"}}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "open_link",
            "description":"Navigate to URL and return page HTML",
            "parameters":{ "type": "object","properties":{"url": {"type": "string"}}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "scrape_text",
            "description":"Extract text matching a selector from HTML ",
            "parameters":{ 
                "type": "object",
                "properties":{
                    "html": {"type": "string"},
                    "selector": {"type":"string"}
                }
            }
        }
    }
]

def run_agent(task_prompt):
    print(f"\nStarting task: {task_prompt}")
    messages = [{"role":"user", "content": task_prompt}]
    results = []
    step = 1
    max_retries = 3
    retry_delay = 5  # seconds

    while True:
        print(f"\nStep {step}: Processing...")
        
        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=messages,
                    tools=functions,
                    tool_choice="auto"
                )
                break
            except openai.RateLimitError:
                if attempt < max_retries - 1:
                    print(f"Rate limit exceeded. Waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print("Max retries reached. Exiting...")
                    return
        
        message = response.choices[0].message
        print(f"AI Response: {message.content if message.content else 'No content'}")
        
        # Add the assistant's message to the history
        assistant_message = {
            "role": "assistant",
            "content": message.content
        }
        if message.tool_calls:
            assistant_message["tool_calls"] = message.tool_calls
        messages.append(assistant_message)
        
        if message.tool_calls:
            tool_call = message.tool_calls[0]
            fn_name = tool_call.function.name
            args = json.loads(tool_call.function.arguments)
            print(f"\nExecuting function: {fn_name}")
            print(f"Arguments: {args}")
            
            if fn_name == "search_google":
                print("Searching Google...")
                tool_result = search_google(args["query"])
                print("Search completed")
            elif fn_name == "open_link":
                print(f"Opening URL: {args['url']}")
                tool_result = open_link(args["url"])
                print("Page loaded")
            elif fn_name == "scrape_text":
                print(f"Scraping text with selector: {args['selector']}")
                tool_result = scrape_text(args["html"], args["selector"])
                print(f"Found {len(tool_result)} matches")
            else:
                tool_result = None
                print("Unknown function")

            # Truncate tool result if it's too large
            if isinstance(tool_result, str) and len(tool_result) > 1000:
                tool_result = tool_result[:1000] + "... [truncated]"

            # Add the tool response message
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": fn_name,
                "content": json.dumps(tool_result)
            })
            print("Function execution completed")
        else:
            content = message.content
            print("\nFinal result:")
            print(content)
            
            # Extract and save data only after we have the final content
            if "interest rate" in task_prompt.lower():
                data = extract_interest_rate(content)
            else:
                data = extract_estate_listings(content)
            results.append(data)
            save_results(results)
            print("\nCurrent results:", results)
            break
        
        step += 1
        time.sleep(2)  # Increased delay between steps

if __name__ == "__main__":
    run_agent("Get me the current mortgage interest rate from Bank of America's website at https://www.bankofamerica.com/mortgage/mortgage-rates/")