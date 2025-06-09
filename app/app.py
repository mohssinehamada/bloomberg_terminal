import gradio as gr
import asyncio
import time
import json
from browseruse_gemini_script import GeminiBrowserAgent

def browser_task(url, task_type, location=None, additional_instructions=None, progress=gr.Progress(track_tqdm=True)):
    try:
        # Create a queue for status updates
        status_updates = []
        
        progress(0.1, desc="Initializing browser agent...")
        status_updates.append("🚀 Initializing browser agent...")
        
        start_time = time.time()
        agent = GeminiBrowserAgent()
        
        # Map task type to internal task identifier
        task_map = {
            "Interest Rate Extraction": "interest_rate",
            "Real Estate Listings": "real_estate"
        }
        
        # Prepare for execution
        websites = {url: task_map[task_type]}
        progress(0.2, desc="Launching browser...")
        status_updates.append("🌐 Launching browser and navigating to URL...")
        
        # Add execution steps to the status updates
        progress(0.3, desc="Analyzing webpage...")
        status_updates.append("🔍 Analyzing webpage structure...")
        
        progress(0.4, desc="Executing extraction...")
        status_updates.append("⚙️ Executing data extraction task...")
        
        # Execute the actual task
        result = asyncio.run(agent.execute_task(
            websites=websites, 
            location=location, 
            additional_instructions=additional_instructions
        ))
        
        progress(0.9, desc="Processing results...")
        status_updates.append("📊 Processing extracted data...")
        
        # Calculate execution time
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Process and format results
        if result["status"] == "success":
            status_updates.append("✅ Task completed successfully")
            formatted_result = format_extraction_results(result["detailed_result"], task_type, location)
        else:
            status_updates.append("❌ Task encountered issues")
            formatted_result = "No detailed results available."
        
        progress(1.0, desc="Complete!")
        
        # Build the final output
        execution_steps = "\n".join([f"**Step {i+1}**: {update}" for i, update in enumerate(status_updates)])
        
        formatted_output = f"""
## Task Summary
**Status**: {result['status'].capitalize()}  
**Message**: {result['message']}  
**Execution Time**: {execution_time:.2f} seconds  

## Execution Steps
{execution_steps}

## Extracted Data
{formatted_result}
"""
        return formatted_output

    except Exception as e:
        formatted_output = f"""
## Task Summary
**Status**: Failed  
**Message**: Task failed: {str(e)}  
**Execution Time**: N/A  

## Error Details
```
{str(e)}
```

Please check your URL and try again. Make sure the website is accessible and contains the data you're looking for.
"""
        return formatted_output

def format_extraction_results(detailed_result, task_type, location):
    """Format the extraction results based on task type"""
    try:
        # First try to find and extract JSON data
        json_start = detailed_result.find("[{")
        json_end = detailed_result.rfind("}]") + 2
        
        if json_start != -1 and json_end != -1:
            json_str = detailed_result[json_start:json_end]
            try:
                data = json.loads(json_str)
                
                # If we successfully parsed JSON data
                if isinstance(data, list) and data and all(isinstance(item, dict) for item in data):
                    if task_type == "Real Estate Listings":
                        return format_real_estate_data(data, location)
                    else:  # Interest Rate Extraction
                        return format_interest_rate_data(data)
            except json.JSONDecodeError:
                # If JSON parsing failed, we'll fall back to returning the raw output
                pass
        
        # If no JSON data found, check for other structured data in the text
        if task_type == "Interest Rate Extraction" and "Interest rate data" in detailed_result:
            # Try to extract tabular data from text
            return format_text_based_interest_rate(detailed_result)
        
        # If all else fails, return the detailed result as is
        return f"```\n{detailed_result}\n```"
        
    except Exception as e:
        return f"Error formatting results: {str(e)}\n\nRaw output:\n```\n{detailed_result}\n```"

def format_real_estate_data(data, location):
    """Format real estate listing data into a readable table"""
    location_str = f" in {location}" if location else ""
    result = f"### Real Estate Listings{location_str}\n\n"
    
    for idx, item in enumerate(data, 1):
        name = item.get('name', 'Unnamed Listing')
        address = item.get('address', 'N/A')
        price = item.get('price', 'N/A')
        if price and price != 'N/A':
            # Clean up price string and format with commas
            price = price.replace(',', '').replace('₹', '').strip()
            try:
                price = f"₹{int(float(price)):,} INR"
            except ValueError:
                price = f"₹{price} INR"
        
        beds = item.get('beds', 'N/A')
        size = item.get('size', 'N/A')
        amenities = item.get('amenities', 'None')
        
        result += f"#### {idx}. {name}\n"
        result += f"**Address**: {address}\n"
        result += f"**Price**: {price}\n"
        result += f"**Beds**: {beds}\n"
        result += f"**Size**: {size}\n"
        result += f"**Amenities**: {amenities}\n\n"
        result += "---\n\n"
    
    return result

def format_interest_rate_data(data):
    """Format interest rate data into readable tables"""
    result = "### Interest Rate Data\n\n"
    
    for category_data in data:
        category = category_data.get('category', 'Uncategorized')
        result += f"#### {category}\n\n"
        
        # Create a markdown table for each category
        headers = []
        values = []
        
        for key, value in category_data.items():
            if key != 'category':
                headers.append(key.replace('_', ' ').title())
                values.append(str(value))
        
        if headers:
            # Create table header
            result += "| " + " | ".join(headers) + " |\n"
            result += "| " + " | ".join(["---" for _ in headers]) + " |\n"
            
            # Create table row
            result += "| " + " | ".join(values) + " |\n\n"
        else:
            result += "_No data available for this category_\n\n"
    
    return result

def format_text_based_interest_rate(text):
    """Extract and format interest rate information from text output"""
    result = "### Interest Rate Data\n\n"
    
    # Look for patterns indicating rate information
    lines = text.split('\n')
    current_category = None
    category_data = []
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Check if this line is a category header
        if line.startswith('**') and line.endswith('**'):
            # If we have collected data for a previous category, add it to the result
            if current_category and category_data:
                result += f"#### {current_category}\n\n"
                result += "\n".join(category_data)
                result += "\n\n---\n\n"
                category_data = []
                
            current_category = line.strip('*')
        elif ':' in line and current_category:
            # This looks like a key-value pair
            category_data.append(line)
    
    # Add the last category if there is one
    if current_category and category_data:
        result += f"#### {current_category}\n\n"
        result += "\n".join(category_data)
        result += "\n\n"
    
    return result

# ----------------------------
# Improved Dark & Centered CSS
# ----------------------------
custom_css = """
body {
    background-color: #121212 !important;
    font-family: 'Segoe UI', 'Roboto', sans-serif;
    color: #f0f0f0;
    padding-top: 40px !important;
    margin: 0;
}

.gradio-container {
    max-width: 95vw !important; /* responsive width */
    width: 100%;
    margin: 0 auto;
    padding: 0 20px;
    box-sizing: border-box;
}

h1, h2, h3, label, .gr-markdown {
    color: #f0f0f0 !important;
}

h1 { font-size: 1.8rem !important; }
h2 { font-size: 1.5rem !important; }
h3 { font-size: 1.3rem !important; }
h4 { font-size: 1.1rem !important; }

.gr-textbox input, .gr-dropdown select {
    font-size: 1rem;
}

.gr-box {
    background-color: #1e1e1e !important;
    border: 1px solid #333 !important;
    border-radius: 10px !important;
    padding: 1rem !important;
}

/* Start Task button */
button {
    background-color: #4caf50 !important;
    color: white !important;
    border-radius: 8px !important;
    padding: 0.6rem 1.2rem !important;
    font-weight: 500;
    font-size: 15px;
    border: none !important;
    transition: all 0.3s ease;
}

button:hover {
    background-color: #66bb6a !important;
    transform: translateY(-2px);
}

/* Status section */
.status-box {
    border: 1px solid #444;
    border-radius: 10px;
    padding: 15px;
    background-color: #1e1e1e;
    margin-bottom: 20px;
    color: #ddd !important;
}

/* Output box */
#result-box {
    border: 1px solid #444;
    border-radius: 10px;
    padding: 18px;
    background-color: #1e1e1e;
    margin-top: 20px;
    color: #f0f0f0 !important;
    white-space: pre-wrap;
    font-size: 1rem;
    max-height: 800px;
    overflow-y: auto;
}

/* Tables styling */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 15px 0;
}

table, th, td {
    border: 1px solid #555;
}

th {
    background-color: #2a2a2a;
    padding: 8px;
    text-align: left;
}

td {
    padding: 8px;
    background-color: #1a1a1a;
}

/* Code blocks */
code, pre {
    background-color: #2a2a2a !important;
    border-radius: 4px;
    padding: 2px 4px;
    font-family: 'Courier New', monospace;
}

pre {
    padding: 10px;
    overflow-x: auto;
}

/* Footer cleanup */
footer {
    margin-top: 60px !important;
    border-top: 1px solid #333 !important;
    padding-top: 10px !important;
    font-size: 0.9rem !important;
    color: #888 !important;
}

/* Footer links as text */
footer button, footer .svelte-1ipelgc {
    background: none !important;
    border: none !important;
    color: #4caf50 !important;
    font-weight: 500;
    box-shadow: none !important;
    padding: 0 !important;
    margin-right: 15px;
    cursor: pointer;
    font-size: 0.9rem;
}

footer button:hover, footer .svelte-1ipelgc:hover {
    color: #81c784 !important;
    text-decoration: underline !important;
}

/* Ensure modals like settings work right */
dialog, .gr-modal, .gr-dialog {
    max-width: 100% !important;
    width: 600px !important;
    background-color: #1e1e1e !important;
    color: #f0f0f0 !important;
    border-radius: 12px !important;
    padding: 20px;
    overflow: auto !important;
}

/* Progress bar styling */
.progress-container {
    width: 100%;
    background-color: #333;
    border-radius: 4px;
    margin: 10px 0;
}

.progress-bar {
    height: 8px;
    background-color: #4caf50;
    width: 0%;
    border-radius: 4px;
    transition: width 0.3s ease;
}

/* Add some highlighting for important info */
.highlight {
    color: #4caf50;
    font-weight: bold;
}

/* Tips section */
.tips-box {
    background-color: rgba(76, 175, 80, 0.1);
    border-left: 3px solid #4caf50;
    padding: 10px 15px;
    margin: 15px 0;
    border-radius: 0 5px 5px 0;
}
"""

# -------------------
# User Interface
# -------------------
with gr.Blocks(css=custom_css, theme=gr.themes.Soft()) as demo:
    gr.Markdown(
        """
# 📊 Web Data Extractor Pro: Interest Rates & Real Estate Listings

This tool allows you to extract structured data from public websites.  
You can extract **bank interest rates** or **real estate listings** with detailed information.

### 🌟 Features
- Step-by-step extraction process visibility
- Structured data formatting for easy reading
- Support for additional extraction instructions
        """
    )

    with gr.Tabs():
        with gr.TabItem("Extraction Tool"):
            with gr.Row():
                with gr.Column(scale=2):
                    url_input = gr.Textbox(
                        label="Website URL",
                        placeholder="https://example.com/path",
                        info="Provide a valid URL with the information you want to extract"
                    )
                
                with gr.Column(scale=1):
                    task_type = gr.Dropdown(
                        choices=["Interest Rate Extraction", "Real Estate Listings"],
                        label="Task Type",
                        value="Interest Rate Extraction",
                        info="Choose what type of data to retrieve"
                    )
            
            with gr.Row():
                with gr.Column():
                    location_input = gr.Textbox(
                        label="Location",
                        placeholder="e.g., Mumbai, India",
                        info="Provide the location for real estate listings",
                        visible=False
                    )
                
                with gr.Column():
                    additional_instructions_input = gr.Textbox(
                        label="Additional Instructions (Optional)",
                        placeholder="e.g., Click 'View Rates' button if needed, or navigate to relevant tabs",
                        info="Specify any custom extraction instructions to help the agent",
                        visible=True,
                    )
            
            with gr.Row():
                tips_md = gr.Markdown(
                    """
                    <div class="tips-box">
                    <strong>💡 Tips for better extraction:</strong>
                    <ul>
                      <li>For interest rates, provide the exact page containing the rate tables</li>
                      <li>For real estate, additional instructions like "Filter for 2+ bedroom apartments" can help</li>
                      <li>If data isn't appearing, try adding instructions like "Click on 'View Details' button"</li>
                    </ul>
                    </div>
                    """,
                    elem_id="tips-box"
                )
            
            with gr.Row():
                submit_btn = gr.Button("Start Extraction", variant="primary")
            
            output = gr.Markdown(elem_id="result-box")
        
        with gr.TabItem("Help & About"):
            gr.Markdown(
                """
                ## How to Use This Tool

                ### For Interest Rate Extraction:
                1. Enter the URL of a banking website that shows interest rates
                2. Select "Interest Rate Extraction" from the dropdown
                3. Add any additional instructions (like "Click on Base Rate tab")
                4. Click "Start Extraction"

                ### For Real Estate Listings:
                1. Enter the URL of a real estate listing page
                2. Select "Real Estate Listings" from the dropdown
                3. Enter the location information (e.g., "Mumbai, India")
                4. Add any filtering instructions if needed
                5. Click "Start Extraction"

                ### Troubleshooting:
                - If no data appears, try a more specific URL that directly shows the data
                - Add instructions like "Scroll down to view all results" or "Click on expand buttons"
                - Some websites may have anti-scraping measures that prevent extraction
                """
            )

    def update_inputs_visibility(task_type):
        is_real_estate = task_type == "Real Estate Listings"
        return (
            gr.update(visible=is_real_estate),
            gr.update(visible=True)
        )

    task_type.change(
        fn=update_inputs_visibility,
        inputs=task_type,
        outputs=[location_input, additional_instructions_input]
    )

    submit_btn.click(
        fn=browser_task,
        inputs=[url_input, task_type, location_input, additional_instructions_input],
        outputs=[output]
    )

if __name__ == "__main__":
    demo.launch(share=True)