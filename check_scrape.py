import os
import sys
from datetime import datetime

# Add parent directory to path to find database module
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import database functions
from database.database import get_db_connection

def check_recent_listings():
    """Check for recent listings in the database"""
    conn = get_db_connection()
    if not conn:
        print("Failed to connect to database")
        return
    
    try:
        with conn.cursor() as cur:
            # Check recent listings (last hour)
            cur.execute("SELECT COUNT(*) FROM real_estate_listings WHERE created_at >= NOW() - INTERVAL '1 hour'")
            recent_count = cur.fetchone()[0]
            print(f"Listings added in the last hour: {recent_count}")
            
            # Get most recent 5 listings
            cur.execute("""
                SELECT id, title, location, price, bedrooms, bathrooms, created_at 
                FROM real_estate_listings 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            rows = cur.fetchall()
            
            if rows:
                print("\nMost recent listings:")
                for row in rows:
                    print(f"ID: {row[0]}, Title: {row[1]}, Location: {row[2]}, Price: {row[3]}, Created: {row[6]}")
            else:
                print("\nNo listings found in the database.")
                
            # Check recent scrape logs
            cur.execute("""
                SELECT id, website_url, status, created_at, message
                FROM scrape_logs
                ORDER BY created_at DESC
                LIMIT 5
            """)
            logs = cur.fetchall()
            
            if logs:
                print("\nRecent scrape attempts:")
                for log in logs:
                    print(f"ID: {log[0]}, URL: {log[1]}, Status: {log[2]}, Time: {log[3]}, Message: {log[4]}")
            else:
                print("\nNo scrape logs found.")
    except Exception as e:
        print(f"Error querying database: {e}")
    finally:
        conn.close()

def check_html_file():
    """Check the content of last_scraped_page.html if it exists"""
    html_path = "last_scraped_page.html"
    if os.path.exists(html_path):
        file_size = os.path.getsize(html_path) / 1024  # KB
        modified_time = datetime.fromtimestamp(os.path.getmtime(html_path))
        print(f"\nLast scraped page HTML:")
        print(f"- File size: {file_size:.2f} KB")
        print(f"- Last modified: {modified_time}")
        
        # Check if the file contains certain patterns
        with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        # Check for common indicators
        contains_zillow = "zillow" in content.lower()
        contains_listings = "price" in content.lower() and "bed" in content.lower()
        contains_captcha = "captcha" in content.lower() or "robot" in content.lower() or "bot" in content.lower()
        contains_press_hold = "press" in content.lower() and "hold" in content.lower()
        
        print("Content analysis:")
        print(f"- Contains Zillow content: {contains_zillow}")
        print(f"- Contains listing data: {contains_listings}")
        print(f"- Contains CAPTCHA/bot detection: {contains_captcha}")
        print(f"- Contains Press & Hold verification: {contains_press_hold}")
    else:
        print("\nNo last_scraped_page.html file found.")

if __name__ == "__main__":
    print("Checking for recent scraping activity...\n")
    check_recent_listings()
    check_html_file() 