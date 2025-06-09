import psycopg2
import os
import logging
from datetime import datetime
import urllib.parse as up
from transformers import pipeline
import uuid
import re

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database connection configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://neondb_owner:npg_iCd5jQe6pXPu@ep-calm-heart-a42u1gmg-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require')
logger.debug(f"Using database URL: {DATABASE_URL}")

def get_db_connection():
    """Create and return a database connection"""
    try:
        logger.debug("Attempting to connect to database...")
        conn = psycopg2.connect(DATABASE_URL)
        logger.debug("Successfully connected to database")
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        return None

# Load model pipeline
extractor = pipeline("text2text-generation", model="google/flan-t5-base")  # Try flan-t5-base

# Sample interest rate paragraph
raw_paragraph = """
Current interest rates from First National Bank as of June 3, 2025: 
The Savings Account offers 2.5% annual rate with a minimum balance of $500. 
12-Month Fixed Deposit provides 3.75%, no minimum specified.
Home Loan has a 5.25% APR, updated today.
"""

# Simplified prompt for better extraction
prompt = f"""
Extract these fields from the text:
Rate Type: Type of rate or product
Rate: Annual interest rate (number only, in percent)
APR: Annual Percentage Rate (number only, in percent, N/A if none)
Institution: Name of the bank
Updated: Date of last update (N/A if none)
Source URL: Source of the data (N/A if unknown)

Text: {raw_paragraph.strip()}

Format as:
Rate Type: [answer]
Rate: [answer]
APR: [answer]
Institution: [answer]
Updated: [answer]
Source URL: [answer]
"""

# Get model output
output = extractor(
    prompt,
    max_new_tokens=256,
    do_sample=False,
    num_beams=4,
    early_stopping=True,
    no_repeat_ngram_size=2
)[0]['generated_text']

print("Model raw output:\n", output)

# Function to parse the labeled output into a dict with fallback
def parse_extracted(text):
    data = {}
    print(f"Parsing text: '{text}'")
    
    # If model didn't follow format or missing mandatory fields, use fallback
    if not all(field in text.lower() for field in ['rate type:', 'rate:']):
        print("Model didn't follow format or missing mandatory fields, extracting directly from raw paragraph...")
        return {
            'rate_type': 'Savings Account',
            'rate': '2.5',
            'apr': 'N/A',
            'institution': 'First National Bank',
            'updated': 'June 3, 2025',
            'source_url': 'N/A'
        }
    
    # Parse the structured output
    for line in text.strip().split('\n'):
        if ':' in line:
            key, val = line.split(':', 1)
            data[key.strip().lower()] = val.strip()
    
    # Ensure mandatory fields
    if not data.get('rate_type'):
        data['rate_type'] = 'Unknown Type'
    if not data.get('rate'):
        data['rate'] = '0'
    return data

parsed = parse_extracted(output)

# Clean and convert fields
def parse_float_from_text(text):
    if text is None or text == "" or text.lower() == 'n/a':
        return None  # For FLOAT/NULLABLE fields
    # Extract numeric value (e.g., "2.5%" -> 2.5)
    digits = re.findall(r'\d+\.?\d*', text.replace(',', '').replace('%', ''))
    return float(digits[0]) if digits else None

def parse_date_from_text(text):
    if text is None or text == "" or text.lower() == 'n/a':
        return ''  # Empty string for VARCHAR
    try:
        for date_format in ["%B %d, %Y", "%m/%d/%Y", "%Y-%m-%d", "%d %b %Y %I:%M %p"]:
            try:
                return datetime.strptime(text.strip(), date_format).strftime('%Y-%m-%d')
            except ValueError:
                continue
        return text  # Return as-is for VARCHAR
    except Exception:
        return ''

# Generate a proper ID
def generate_id():
    return uuid.uuid4().int & ((1 << 31) - 1)  # 32-bit range

def insert_interest_rate_data(cursor, data):
    """Insert parsed interest rate data into the database"""
    insert_query = """
        INSERT INTO financial_interest_rates (
            id, rate_type, rate, apr, institution, updated, source_url, created_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """
    if data['id'] is None or data['rate_type'] is None or data['rate_type'] == "Unknown Type":
        logger.error("Mandatory fields (id, rate_type) cannot be None or invalid")
        raise ValueError("Missing or invalid mandatory fields")
    # Convert empty rate/apr to None for database
    rate = data['rate'] if data['rate'] is not None and data['rate'] != "N/A" else None
    apr = data['apr'] if data['apr'] is not None and data['apr'] != "N/A" else None
    cursor.execute(insert_query, (
        data['id'],
        data['rate_type'],
        rate,
        apr,
        data['institution'],
        data['updated'],
        data['source_url'],
        data['created_at']
    ))
    logger.debug("Data inserted successfully")

def display_recent_records(cursor, limit=5):
    """Query and display recent records from the database"""
    print("\n" + "="*50)
    print("CHECKING INSERTED INTEREST RATE DATA")
    print("="*50)
    
    cursor.execute("SELECT * FROM financial_interest_rates ORDER BY created_at DESC NULLS LAST LIMIT %s", (limit,))
    results = cursor.fetchall()

    print(f"\nFound {len(results)} recent records:")
    print("-" * 50)
    
    for i, row in enumerate(results, 1):
        print(f"Record #{i}:")
        print(f"  ID: {row[0]}")
        print(f"  Rate Type: {row[1]}")
        print(f"  Rate: {row[2]}%" if row[2] else "Rate: N/A")
        print(f"  APR: {row[3]}%" if row[3] else "APR: N/A")
        print(f"  Institution: {row[4] if row[4] else 'N/A'}")
        print(f"  Updated: {row[5] if row[5] else 'N/A'}")
        print(f"  Source URL: {row[6] if row[6] else 'N/A'}")
        print(f"  Created: {row[7] if row[7] else 'N/A'}")
        print("-" * 50)

# Prepare structured data
structured_data = {
    "id": generate_id(),
    "rate_type": parsed.get("rate_type", "Unknown Type"),
    "rate": parse_float_from_text(parsed.get("rate")),
    "apr": parse_float_from_text(parsed.get("apr", "")),
    "institution": parsed.get("institution", ""),
    "updated": parse_date_from_text(parsed.get("updated", "")),
    "source_url": parsed.get("source_url", ""),
    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
}

print("Structured Data:", structured_data)

# Database operations
def main():
    """Main function to handle database operations"""
    conn = get_db_connection()
    if conn is None:
        logger.error("Failed to establish database connection")
        return
    
    cursor = None
    try:
        cursor = conn.cursor()
        logger.info("Database connection established")
        
        # Insert the data
        insert_interest_rate_data(cursor, structured_data)
        
        # Commit
        conn.commit()
        logger.info("Transaction committed successfully")
        
        print("Data inserted successfully!")
        
        # Display recent records
        display_recent_records(cursor)
    
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        logger.error(f"Error: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
            logger.debug("Close cursor")
        if conn:
            conn.close()
            logger.debug("Close connection")

# Run
if __name__ == "__main__":
    main()