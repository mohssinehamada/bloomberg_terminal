#!/usr/bin/env python3
"""
Test script for the get_user_input function in browseruse_gemini.py
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from core.browseruse_gemini import get_user_input
except ImportError:
    print("Could not import get_user_input from browseruse_gemini.py")
    sys.exit(1)

def main():
    print("\n=== Testing get_user_input function ===\n")
    
    try:
        # Get user input
        url, task_type = get_user_input()
        
        # Print results
        print("\n=== Results ===")
        print(f"URL: {url}")
        print(f"Task Type: {task_type}")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"\nError during test: {str(e)}")

if __name__ == "__main__":
    main() 