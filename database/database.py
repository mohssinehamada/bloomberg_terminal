import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()

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

def init_db():
    """Initialize the database with required tables"""
    conn = get_db_connection()
    if not conn:
        return
    
    try:
        with conn.cursor() as cur:
            # Check if tables exist
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('real_estate_listings', 'scrape_logs', 'financial_interest_rates');
            """)
            existing_tables = [row[0] for row in cur.fetchall()]
            logger.debug(f"Existing tables: {existing_tables}")
            
            # Create real estate listings table
            logger.debug("Creating real_estate_listings table if it doesn't exist...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS real_estate_listings (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255),
                    date VARCHAR(50),
                    location VARCHAR(100),
                    price VARCHAR(50),
                    bedrooms VARCHAR(50),
                    bathrooms VARCHAR(50),
                    size VARCHAR(50),
                    other TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create financial interest rates table
            logger.debug("Creating financial_interest_rates table if it doesn't exist...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS financial_interest_rates (
                    id SERIAL PRIMARY KEY,
                    rate_type VARCHAR(255),
                    rate VARCHAR(50),
                    apr VARCHAR(50),
                    updated VARCHAR(100),
                    institution VARCHAR(255),
                    source_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Create scrape logs table
            logger.debug("Creating scrape_logs table if it doesn't exist...")
            cur.execute("""
                CREATE TABLE IF NOT EXISTS scrape_logs (
                    id SERIAL PRIMARY KEY,
                    website_url TEXT,
                    task_type VARCHAR(50),
                    status VARCHAR(50),
                    message TEXT,
                    raw_data JSONB,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            
            # Alter existing scrape_logs table if needed
            if 'scrape_logs' in existing_tables:
                logger.debug("Checking if scrape_logs.website_url needs to be altered to TEXT...")
                # Check column type
                cur.execute("""
                    SELECT data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'scrape_logs' AND column_name = 'website_url';
                """)
                column_type = cur.fetchone()[0]
                
                if column_type.lower() != 'text':
                    logger.info(f"Altering scrape_logs.website_url from {column_type} to TEXT...")
                    cur.execute("""
                        ALTER TABLE scrape_logs 
                        ALTER COLUMN website_url TYPE TEXT;
                    """)
                    logger.info("Column type successfully changed to TEXT")
            
            # Verify table structure - all debug level
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'real_estate_listings';
            """)
            columns = cur.fetchall()
            logger.debug(f"real_estate_listings table structure: {columns}")
            
            # Verify financial_interest_rates table structure
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'financial_interest_rates';
            """)
            columns = cur.fetchall()
            logger.debug(f"financial_interest_rates table structure: {columns}")
            
            # Verify scrape_logs table structure
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'scrape_logs';
            """)
            columns = cur.fetchall()
            logger.debug(f"scrape_logs table structure: {columns}")
            
        conn.commit()
        logger.info("Database initialized successfully!")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No additional details'}")
    finally:
        conn.close()

def insert_listing(listing_data):
    """Insert a new real estate listing into the database"""
    logger.debug(f"Attempting to insert listing with data: {json.dumps(listing_data, indent=2)}")
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to get database connection")
        return False
    
    try:
        # Ensure all data is properly formatted
        processed_data = {}
        
        # Handle title
        title = listing_data.get('title')
        if title is None and 'description' in listing_data:
            title = listing_data.get('description')
        processed_data['title'] = str(title) if title is not None else ''
        
        # Handle date/time (the agent returns 'time', but our DB expects 'date')
        date_val = listing_data.get('time') or listing_data.get('date') or 'Recent'
        processed_data['date'] = str(date_val) if date_val is not None else ''
        
        # Handle location
        location = listing_data.get('location') or listing_data.get('address')
        processed_data['location'] = str(location) if location is not None else ''
        
        # Handle price
        price = listing_data.get('price')
        processed_data['price'] = str(price) if price is not None else ''
        
        # Handle bedrooms
        bedrooms = listing_data.get('bedrooms') or listing_data.get('beds')
        processed_data['bedrooms'] = str(bedrooms) if bedrooms is not None else ''
        
        # Handle bathrooms
        bathrooms = listing_data.get('bathrooms') or listing_data.get('baths')
        processed_data['bathrooms'] = str(bathrooms) if bathrooms is not None else ''
        
        # Handle size/area (the agent might return 'area', but our DB expects 'size')
        size = listing_data.get('area') or listing_data.get('size') or listing_data.get('square_footage') or listing_data.get('sqft')
        processed_data['size'] = str(size) if size is not None else ''
        
        # Handle other data
        other_fields = {}
        for key, value in listing_data.items():
            if key not in ['title', 'date', 'time', 'location', 'address', 'price', 'bedrooms', 'beds', 'bathrooms', 'baths', 'size', 'area', 'square_footage', 'sqft'] and value is not None:
                other_fields[key] = str(value)
        processed_data['other'] = json.dumps(other_fields)
        
        logger.debug(f"Processed listing data for database: {json.dumps(processed_data, indent=2)}")
        
        with conn.cursor() as cur:
            # Log the SQL query and parameters
            query = """
                INSERT INTO real_estate_listings 
                (title, date, location, price, bedrooms, bathrooms, size, other)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """
            params = (
                processed_data['title'],
                processed_data['date'],
                processed_data['location'],
                processed_data['price'],
                processed_data['bedrooms'],
                processed_data['bathrooms'],
                processed_data['size'],
                processed_data['other']
            )
            logger.debug(f"Executing SQL with parameters: {params}")
            
            cur.execute(query, params)
            listing_id = cur.fetchone()[0]
            conn.commit()
            logger.info(f"Successfully inserted listing with ID: {listing_id}")
            return listing_id
    except Exception as e:
        logger.error(f"Error inserting listing: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No additional details'}")
        conn.rollback()
        return False
    finally:
        conn.close()
        logger.debug("Database connection closed")

def log_scrape(website_url, task_type, status, message, raw_data=None, error_message=None):
    """Log a scrape attempt to the database"""
    logger.info(f"Logging scrape attempt for {website_url} with status {status}")
    conn = get_db_connection()
    if not conn:
        return False
    
    try:
        # Truncate website_url if it's too long (max 255 chars for varchar)
        truncated_url = website_url[:250] + "..." if len(website_url) > 255 else website_url
        if truncated_url != website_url:
            logger.debug(f"Truncated URL from {len(website_url)} to 253 characters")
        
        # Prepare raw_data for database storage
        processed_raw_data = None
        if raw_data:
            try:
                # If raw_data is already a string, check if it's valid JSON
                if isinstance(raw_data, str):
                    try:
                        json_obj = json.loads(raw_data)
                        processed_raw_data = raw_data
                    except json.JSONDecodeError:
                        # If not valid JSON, convert to a JSON string
                        processed_raw_data = json.dumps({"raw_string": raw_data})
                else:
                    # If raw_data is a dict with a raw_result key that's an object, convert to string first
                    if isinstance(raw_data, dict) and "raw_result" in raw_data and not isinstance(raw_data["raw_result"], (dict, list, str, int, float, bool, type(None))):
                        raw_data["raw_result"] = str(raw_data["raw_result"])
                    # Otherwise, just dump to JSON
                    processed_raw_data = json.dumps(raw_data)
                
                logger.debug(f"Processed raw_data for database storage: Type={type(processed_raw_data)}, Length={len(processed_raw_data) if processed_raw_data else 0}")
            except Exception as e:
                logger.error(f"Error processing raw_data for database: {e}")
                # Fall back to string representation
                processed_raw_data = json.dumps({"raw_string": str(raw_data)})
        
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO scrape_logs 
                (website_url, task_type, status, message, raw_data, error_message)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                truncated_url,
                task_type,
                status,
                message,
                processed_raw_data,
                error_message
            ))
            log_id = cur.fetchone()[0]
            conn.commit()
            logger.debug(f"Successfully logged scrape with ID: {log_id}")
            return log_id
    except Exception as e:
        logger.error(f"Error logging scrape: {e}")
        return False
    finally:
        conn.close()

def insert_interest_rate(rate_data, source_url):
    """Insert a financial interest rate into the database"""
    logger.debug(f"Attempting to insert interest rate with data: {json.dumps(rate_data, indent=2)}")
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to get database connection")
        return False
    
    try:
        # Ensure all data is properly formatted
        processed_data = {}
        
        # Handle rate_type
        rate_type = rate_data.get('rate_type')
        processed_data['rate_type'] = str(rate_type) if rate_type is not None else ''
        
        # Handle rate
        rate = rate_data.get('rate')
        processed_data['rate'] = str(rate) if rate is not None else ''
        
        # Handle apr
        apr = rate_data.get('apr')
        processed_data['apr'] = str(apr) if apr is not None else ''
        
        # Handle updated
        updated = rate_data.get('updated')
        processed_data['updated'] = str(updated) if updated is not None else 'Recent'
        
        # Handle institution
        institution = rate_data.get('institution')
        processed_data['institution'] = str(institution) if institution is not None else ''
        
        # Source URL
        processed_data['source_url'] = source_url
        
        logger.debug(f"Processed interest rate data for database: {json.dumps(processed_data, indent=2)}")
        
        with conn.cursor() as cur:
            # Log the SQL query and parameters
            query = """
                INSERT INTO financial_interest_rates 
                (rate_type, rate, apr, updated, institution, source_url)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING id;
            """
            params = (
                processed_data['rate_type'],
                processed_data['rate'],
                processed_data['apr'],
                processed_data['updated'],
                processed_data['institution'],
                processed_data['source_url']
            )
            logger.debug(f"Executing SQL with parameters: {params}")
            
            cur.execute(query, params)
            rate_id = cur.fetchone()[0]
            conn.commit()
            logger.info(f"Successfully inserted interest rate with ID: {rate_id}")
            return rate_id
    except Exception as e:
        logger.error(f"Error inserting interest rate: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {e.__dict__ if hasattr(e, '__dict__') else 'No additional details'}")
        conn.rollback()
        return False
    finally:
        conn.close()
        logger.debug("Database connection closed")

if __name__ == "__main__":
    init_db() 