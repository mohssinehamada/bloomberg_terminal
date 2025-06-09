#!/usr/bin/env python3
"""
Demo script showing how to search for a house in New York with specific criteria
"""

import asyncio
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the GeminiBrowserAgent
from browseruse_gemini import GeminiBrowserAgent, extract_search_criteria

async def demo_house_search():
    """Demo searching for a house with specific criteria"""
    
    print("🏠 Demo: Searching for a house in New York")
    print("=" * 50)
    
    # Your specific search criteria
    user_input = "looking for a house in new york with 3 bedrooms and 2 bathrooms under $800k"
    print(f"Search request: '{user_input}'")
    
    # Extract criteria using the built-in function
    criteria = extract_search_criteria(user_input)
    
    print("\n✅ Extracted search criteria:")
    print(f"📍 Location: {criteria['location']}")
    print(f"🛏️  Bedrooms: {criteria['bedrooms']}")
    print(f"🚿 Bathrooms: {criteria['bathrooms']}")
    print(f"💰 Maximum price: ${criteria['price_max']:,}")
    print(f"🏠 Property type: {criteria['home_type'].title()}")
    
    # Store criteria for the agent to use
    os.environ['SEARCH_CRITERIA'] = json.dumps(criteria)
    
    # Choose a website (you can change this)
    website = "https://www.realtor.com"
    print(f"\n🌐 Searching on: {website}")
    
    # Create the agent
    try:
        print("\n🤖 Initializing browser agent...")
        agent = GeminiBrowserAgent()
        
        # Prepare the search
        websites = {website: "real_estate"}
        
        print("\n🚀 Starting search...")
        print("The browser will open and the agent will:")
        print("1. Navigate to realtor.com")
        print("2. Search for properties in New York")
        print("3. Apply filters for 3+ bedrooms, 2+ bathrooms")
        print("4. Filter for properties under $800,000")
        print("5. Extract matching listings")
        
        # Run the search
        result = await agent.execute_task(websites=websites, max_steps=20)
        
        # Display results
        if result.get('error'):
            print(f"\n❌ Error: {result['error']}")
        elif result.get('output'):
            print("\n✅ Search completed successfully!")
            
            # Check if we got listings
            if isinstance(result['output'], dict) and 'listings' in result['output']:
                listings = result['output']['listings']
                print(f"\n📋 Found {len(listings)} matching properties:")
                
                for i, listing in enumerate(listings[:5], 1):  # Show first 5
                    print(f"\n{i}. {listing.get('title', 'No title')}")
                    print(f"   📍 Location: {listing.get('location', 'N/A')}")
                    print(f"   💰 Price: {listing.get('price', 'N/A')}")
                    print(f"   🛏️  Bedrooms: {listing.get('bedrooms', 'N/A')}")
                    print(f"   🚿 Bathrooms: {listing.get('bathrooms', 'N/A')}")
                    if listing.get('area'):
                        print(f"   📐 Area: {listing.get('area')}")
            else:
                print("\n📄 Raw result:")
                print(str(result['output'])[:500] + "..." if len(str(result['output'])) > 500 else str(result['output']))
        else:
            print("\n❌ No results returned")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure you have:")
        print("1. Activated the conda environment: conda activate browser-use-env")
        print("2. Set your GEMINI_API_KEY in the .env file")
        print("3. Installed all dependencies")

def main():
    """Main function"""
    print("🎯 House Search Demo")
    print("This demo will search for: 'house in New York with 3 bedrooms and 2 bathrooms under $800k'")
    print("\nPress Enter to start the search, or Ctrl+C to cancel...")
    
    try:
        input()
        asyncio.run(demo_house_search())
    except KeyboardInterrupt:
        print("\n👋 Demo cancelled")
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == "__main__":
    main() 