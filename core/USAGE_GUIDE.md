# 🏠 House Search Usage Guide

## 🎯 Your Specific Use Case

You want to search for: **"a house in New York with 3 bedrooms and 2 bathrooms under $800k"**

The system will automatically:
1. ✅ Extract your search criteria from natural language
2. ✅ Apply filters on real estate websites
3. ✅ Return matching properties

## 🚀 Quick Start

### Method 1: Interactive Mode (Recommended)
```bash
conda activate browser-use-env
cd "Cohort 34 - Web Agent/core"
python browseruse_gemini.py
```

When prompted:
1. Choose option `2` (Browse real estate listings)
2. Enter: `"looking for a house in new york with 3 bedrooms and 2 bathrooms under $800k"`
3. The system will extract your criteria and search automatically!

### Method 2: Demo Script
```bash
conda activate browser-use-env
cd "Cohort 34 - Web Agent/core"
python demo_house_search.py
```

This runs your exact search criteria automatically.

## 🔍 How Search Criteria Extraction Works

### Your Input:
```
"looking for a house in new york with 3 bedrooms and 2 bathrooms under $800k"
```

### Automatically Extracted:
- 📍 **Location**: New York
- 🛏️ **Bedrooms**: 3 (minimum)
- 🚿 **Bathrooms**: 2 (minimum)  
- 💰 **Max Price**: $800,000
- 🏠 **Property Type**: House

## 📝 Supported Search Formats

The system understands natural language! Try any of these:

```bash
# Basic format
"house in New York with 3 bedrooms and 2 bathrooms under $800k"

# With website specification
"Search realtor.com for a house in New York with 3 bedrooms and 2 bathrooms under $800k"

# Alternative phrasings
"Find me a 3 bed 2 bath house in NY under 800k"
"Looking for 3br/2ba house in New York under $800,000"
"I want a house in New York with at least 3 bedrooms and 2 bathrooms for under $800k"
```

## 🌐 Supported Websites

- **realtor.com** (Recommended)
- **zillow.com** 
- **trulia.com**
- **apartments.com**

## 🎛️ Advanced Usage

### Custom Search Criteria
You can specify any combination of:

- **Location**: "in Manhattan", "near Central Park", "Brooklyn NY"
- **Bedrooms**: "3 bedrooms", "at least 2 bed", "3br"
- **Bathrooms**: "2 bathrooms", "2.5 bath", "2ba"
- **Price**: "under $800k", "between $500k and $800k", "around $700k"
- **Property Type**: "house", "apartment", "condo", "townhouse"

### Example Searches:
```bash
# Apartment search
"2 bedroom apartment in Manhattan under $600k on zillow.com"

# Townhouse search  
"townhouse in Brooklyn with 3 bedrooms and 2 baths under $900k"

# Condo search
"condo in Queens with at least 1 bedroom under $400k"
```

## 🔧 What the Agent Does

1. **Navigates** to the specified real estate website
2. **Searches** for your location (New York)
3. **Applies filters**:
   - Minimum 3 bedrooms
   - Minimum 2 bathrooms  
   - Maximum price $800,000
   - Property type: House
4. **Scrolls** through listings to load more results
5. **Extracts** property data in structured format
6. **Filters** results to match your exact criteria
7. **Returns** matching properties with details

## 📊 Expected Output

```json
{
  "listings": [
    {
      "title": "Beautiful 3BR House in Queens",
      "location": "123 Main St, Queens, NY",
      "price": "$750,000",
      "bedrooms": "3",
      "bathrooms": "2",
      "area": "1,800 sq ft"
    },
    {
      "title": "Charming 4BR Home in Brooklyn", 
      "location": "456 Oak Ave, Brooklyn, NY",
      "price": "$795,000",
      "bedrooms": "4", 
      "bathrooms": "2.5",
      "area": "2,100 sq ft"
    }
  ]
}
```

## 🛠️ Troubleshooting

### If the agent gets stuck:
1. **Check the browser** - you'll see red boxes around elements
2. **Wait patiently** - real estate sites can be slow
3. **Check logs**: `tail -f browser_agent.log`

### If no results found:
1. **Try a different website** (realtor.com vs zillow.com)
2. **Broaden criteria** (increase price limit, reduce bedroom requirement)
3. **Check location spelling** (try "NY" instead of "New York")

### Common issues:
- **CAPTCHA**: The agent will try to handle it, or you can solve it manually
- **Site blocking**: Try the stealth mode or different user agent
- **Slow loading**: The agent waits for content to load automatically

## 🎯 Pro Tips

1. **Start with realtor.com** - usually most reliable
2. **Be specific with location** - "Manhattan" vs "New York City"
3. **Use round numbers** - "$800k" works better than "$799,999"
4. **Try different phrasings** if extraction isn't perfect
5. **Check the extracted criteria** before confirming the search

## 📞 Need Help?

1. Run the test: `python test_search_extraction.py`
2. Check the troubleshooting guide: `TROUBLESHOOTING.md`
3. View logs: `cat browser_agent.log`
4. Try the simple demo: `python demo_house_search.py`

---

## 🎉 Ready to Search?

Your exact command:
```bash
conda activate browser-use-env
cd "Cohort 34 - Web Agent/core"  
python browseruse_gemini.py
```

Choose option 2, then enter:
```
"looking for a house in new york with 3 bedrooms and 2 bathrooms under $800k"
```

The agent will handle the rest! 🏠✨ 