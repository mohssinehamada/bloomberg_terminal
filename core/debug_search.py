#!/usr/bin/env python3
"""
Debug script to trace search criteria through the entire process
"""

import asyncio
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def debug_search():
    """Debug the search process step by step"""
    
    try:
        from browseruse_gemini import GeminiBrowserAgent, extract_search_criteria
        
        print("🔍 DEBUG: Search Criteria Process\n")
        
        # Step 1: User input
        user_input = "looking for a house in new york with 3 bedrooms and 2 bathrooms under $800k"
        print(f"1️⃣ User input: '{user_input}'")
        
        # Step 2: Extract criteria
        criteria = extract_search_criteria(user_input)
        print(f"2️⃣ Extracted criteria: {json.dumps(criteria, indent=2)}")
        
        # Step 3: Store in environment
        os.environ['SEARCH_CRITERIA'] = json.dumps(criteria)
        print(f"3️⃣ Stored in environment: {os.environ.get('SEARCH_CRITERIA')}")
        
        # Step 4: Verify environment retrieval
        retrieved = os.getenv('SEARCH_CRITERIA', '{}')
        print(f"4️⃣ Retrieved from environment: {retrieved}")
        
        try:
            parsed = json.loads(retrieved)
            print(f"5️⃣ Parsed JSON: {json.dumps(parsed, indent=2)}")
        except Exception as e:
            print(f"❌ JSON parsing error: {e}")
            return
        
        # Step 5: Create agent and build task description
        agent = GeminiBrowserAgent()
        url = "https://www.realtor.com"
        task_type = "real_estate"
        
        print(f"6️⃣ Building task description for: {url}")
        task_description = agent._build_task_description(url, task_type)
        
        # Step 6: Check task description content
        print("\n" + "="*80)
        print("7️⃣ FINAL TASK DESCRIPTION:")
        print("="*80)
        print(task_description)
        print("="*80)
        
        # Step 7: Verify location is in task description
        location_checks = [
            ("New York", "New York" in task_description),
            ("any location", "any location" in task_description),
            ("location: New York", "location: New York" in task_description),
            ("enter the location: New York", "enter the location: New York" in task_description)
        ]
        
        print("\n8️⃣ LOCATION VERIFICATION:")
        for check_text, found in location_checks:
            status = "✅" if found else "❌"
            print(f"{status} '{check_text}': {found}")
        
        # Step 8: Run a minimal agent test
        print("\n9️⃣ Running minimal agent test...")
        websites = {url: task_type}
        
        # Just create the agent and check the task description it would use
        print("🔍 Agent would use this task description:")
        actual_task = agent._build_task_description(url, task_type)
        
        if "New York" in actual_task:
            print("✅ SUCCESS: Agent task description contains 'New York'")
        else:
            print("❌ PROBLEM: Agent task description does NOT contain 'New York'")
            
        print("\n🎯 If you're still seeing 'any' in the browser, it might be:")
        print("   - The website defaulting to 'any' despite agent instructions")
        print("   - Browser cache showing old results")
        print("   - Agent not following the task description properly")
        print("   - Website-specific behavior overriding the search")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_search()) 