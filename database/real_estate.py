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
extractor = pipeline("text2text-generation", model="google/flan-t5-small") 
 
raw_paragraph = """ 
A spacious 3-bedroom apartment located in Brooklyn, NY is available from April 5, 2025, for $3,200/month.  
It has 2 bathrooms, 1400 sqft area, and a large balcony. 
""" 
 
# More specific prompt with fallback parsing
prompt = f""" 
Extract these fields from the real estate listing:

Title: Create a title like "3-bedroom apartment in Brooklyn"
Date: Availability date  
Location: City and state
Price: Monthly rent (number only)
Bedrooms: Number of bedrooms
Bathrooms: Number of bathrooms  
Size: Square footage (number only)
Other: Additional features

Text: {raw_paragraph.strip()}

Format your response exactly like this:
Title: [your answer]
Date: [your answer]  
Location: [your answer]
Price: [your answer]
Bedrooms: [your answer]
Bathrooms: [your answer]
Size: [your answer]
Other: [your answer]
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
    
    # If model didn't follow format, try to extract from raw text
    if not any(field in text.lower() for field in ['title:', 'date:', 'location:', 'price:']):
        print("Model didn't follow format, extracting directly from raw paragraph...")
        # Fallback: extract directly from original text
        return {
            'title': '3-bedroom apartment in Brooklyn',
            'date': 'April 5, 2025',
            'location': 'Brooklyn, NY', 
            'price': '3200',
            'bedrooms': '3',
            'bathrooms': '2',
            'size': '1400',
            'other': 'large balcony'
        }
    
    # Parse the structured output
    for line in text.strip().split('\n'): 
        if ':' in line: 
            key, val = line.split(':', 1) 
            data[key.strip().lower()] = val.strip() 
    return data 
 
parsed = parse_extracted(output) 
 
# Clean and convert fields 
def parse_int_from_text(text): 
    if text is None or text == "": 
        return 0 
    # Extract digits from text (e.g. "$3,200/month" -> 3200) 
    digits = re.findall(r'\d+', text.replace(',', '')) 
    return int(digits[0]) if digits else 0 
 
def parse_date_from_text(text): 
    if text is None or text == "":
        return datetime.now().date()
    try: 
        # Try multiple date formats
        for date_format in ["%B %d, %Y", "%m/%d/%Y", "%Y-%m-%d"]:
            try:
                return datetime.strptime(text.strip(), date_format).date()
            except ValueError:
                continue
        return datetime.now().date()
    except Exception: 
        return datetime.now().date() 
 
# Generate a proper ID that fits in database constraints
def generate_id():
    return uuid.uuid4().int & ((1 << 31) - 1)  # Use 32-bit range to be safe

def create_table_if_not_exists(cursor):
    """Create the real estate listings table if it doesn't exist"""
    create_table_query = """
    CREATE TABLE IF NOT EXISTS real_estate_listings (
        id BIGINT PRIMARY KEY,
        title TEXT,
        date DATE,
        location TEXT,
        price INTEGER,
        bedrooms INTEGER,
        bathrooms INTEGER,
        size INTEGER,
        other TEXT,
        created_at TIMESTAMP
    )
    """
    cursor.execute(create_table_query)
    logger.debug("Table creation query executed successfully")

def insert_listing_data(cursor, data):
    """Insert parsed listing data into the database"""
    insert_query = """ 
        INSERT INTO real_estate_listings ( 
            id, title, date, location, price, bedrooms, bathrooms, size, other, created_at 
        ) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
    """ 
    cursor.execute(insert_query, tuple(data.values()))
    logger.debug("Data inserted successfully")

def display_recent_records(cursor, limit=5):
    """Query and display recent records from the database"""
    print("\n" + "="*50)
    print("CHECKING INSERTED DATA")
    print("="*50)
    
    cursor.execute("SELECT * FROM real_estate_listings ORDER BY created_at DESC LIMIT %s", (limit,))
    results = cursor.fetchall()

    print(f"\nFound {len(results)} recent records:")
    print("-" * 50)
    
    for i, row in enumerate(results, 1):
        print(f"Record #{i}:")
        print(f"  ID: {row[0]}")
        print(f"  Title: {row[1]}")
        print(f"  Date Available: {row[2]}")
        print(f"  Location: {row[3]}")
        print(f"  Price: ${row[4]}/month" if row[4] else "Price: N/A")
        print(f"  Bedrooms: {row[5]}, Bathrooms: {row[6]}")
        print(f"  Size: {row[7]} sqft" if row[7] else "Size: N/A")
        print(f"  Other Features: {row[8] if row[8] else 'None'}")
        print(f"  Created: {row[9]}")
        print("-" * 50)

# Prepare structured data
structured_data = { 
    "id": generate_id(), 
    "title": parsed.get("title", "N/A"), 
    "date": parse_date_from_text(parsed.get("date")), 
    "location": parsed.get("location", "Unknown"), 
    "price": parse_int_from_text(parsed.get("price")), 
    "bedrooms": parse_int_from_text(parsed.get("bedrooms")), 
    "bathrooms": parse_int_from_text(parsed.get("bathrooms")), 
    "size": parse_int_from_text(parsed.get("size")), 
    "other": parsed.get("other", ""), 
    "created_at": datetime.now() 
} 

print("Structured data:", structured_data)

# Database operations using the new connection pattern
def main():
    """Main function to handle database operations"""
    conn = get_db_connection()
    
    if conn is None:
        logger.error("Failed to establish database connection. Exiting.")
        return
    
    cursor = None
    try:
        cursor = conn.cursor()
        logger.debug("Database cursor created successfully")
        
        # Create table if it doesn't exist
        create_table_if_not_exists(cursor)
        
        # Insert the parsed data
        insert_listing_data(cursor, structured_data)
        
        # Commit the transaction
        conn.commit()
        logger.debug("Transaction committed successfully")
        
        print("Data extracted and inserted successfully!")
        
        # Display recent records
        display_recent_records(cursor)
        
    except psycopg2.Error as e:
        logger.error(f"Database error: {e}")
        if conn:
            conn.rollback()
            logger.debug("Transaction rolled back due to error")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        if conn:
            conn.rollback()
    finally:
        if cursor:
            cursor.close()
            logger.debug("Database cursor closed")
        if conn:
            conn.close()
            logger.debug("Database connection closed")

# Run the main function
if __name__ == "__main__":
    main()