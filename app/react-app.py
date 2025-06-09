# app.py - Flask version

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import asyncio
import time
import os
from browseruse_gemini_script import GeminiBrowserAgent

app = Flask(__name__, static_folder='./frontend/build')
CORS(app)  # Enable CORS for API requests

@app.route('/api/extract', methods=['POST'])
def extract_data():
    data = request.json
    url = data.get('url')
    task_type = data.get('taskType')
    location = data.get('location')
    additional_instructions = data.get('additionalInstructions')
    
    # Map task type to internal task identifier
    task_map = {
        "Interest Rate Extraction": "interest_rate",
        "Real Estate Listings": "real_estate"
    }
    
    # Prepare for execution
    websites = {url: task_map[task_type]}
    
    # Execute the actual task
    agent = GeminiBrowserAgent()
    result = asyncio.run(agent.execute_task(
        websites=websites, 
        location=location, 
        additional_instructions=additional_instructions
    ))
    
    return jsonify(result)

# Serve React App - catch all routes and let React router handle them
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)