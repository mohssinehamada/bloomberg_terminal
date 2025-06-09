The Gradio Web App *(Browseruse enabled)*

A powerful web scraping tool built with Gradio that uses Google's Gemini API and BrowserUse for intelligent web interaction and data extraction.

### Prerequisites

1. Python 3.7+
2. Google Gemini API Key

### Installation

1. Install required dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install
```

3. Run the application:
```bash
python app.py
```

4. Set up your Gemini API key:
   - Create a `.env` file in the app directory
   - Add your API key: `GEMINI_API_KEY=your_api_key_here`

### Features

#### Core Capabilities
- **Interest Rate Extraction**
  - Extracts structured interest rate data from banking websites
  - Supports multiple rate categories (savings, fixed deposits, loans)
  - Handles dynamic content loading and navigation

- **Real Estate Listings**
  - Extracts property details including:
    - Property name and address
    - Price (formatted in INR)
    - Number of bedrooms
    - Property size
    - Available amenities

#### Technical Features
- Intelligent web interaction using Gemini API
- Automated browser control with Playwright
- Progress tracking and status updates
- Structured JSON data output
- Error handling and recovery
- Custom extraction instructions support

### Usage

1. Access the web interface at the provided URL

2. For Interest Rate Extraction:
   - Enter the banking website URL
   - Select "Interest Rate Extraction"
   - Add any specific instructions (e.g., "Click View Rates button")

3. For Real Estate Listings:
   - Enter the real estate website URL
   - Select "Real Estate Listings"
   - Specify location (e.g., "Mumbai, India")
   - Add filtering instructions if needed

### Implementation Details

- Built with Gradio for the web interface
- Uses BrowserUse for browser automation
- Integrates Google's Gemini API for intelligent web interaction
- Implements async/await for efficient operation
- Supports custom extraction instructions

### Notes

- The tool requires a stable internet connection
- Some websites may have anti-scraping measures
- Processing time varies based on website complexity
- Results are formatted in structured JSON for easy parsing

### Troubleshooting

If you encounter issues:
1. Ensure your Gemini API key is correctly set
2. Check your internet connection
3. Verify the target website is accessible
4. Try adding more specific extraction instructions
5. Check the console for detailed error messages
