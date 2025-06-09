#!/usr/bin/env python3
"""
Simple script to check what's in the database tables
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import get_db_connection
import json

def check_database():
    """Check what's in the database tables"""
    conn = get_db_connection()
    if not conn:
        print("❌ Failed to connect to database")
        return
    
    try:
        with conn.cursor() as cur:
            
            print("🔍 SCRAPE LOGS:")
            print("=" * 50)
            cur.execute("""
                SELECT id, website_url, task_type, status, message, created_at 
                FROM scrape_logs 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            logs = cur.fetchall()
            
            if logs:
                for log in logs:
                    print(f"ID: {log[0]}")
                    print(f"URL: {log[1]}")
                    print(f"Type: {log[2]}")
                    print(f"Status: {log[3]}")
                    print(f"Message: {log[4]}")
                    print(f"Created: {log[5]}")
                    print("-" * 30)
            else:
                print("No scrape logs found")
            
            
            print("\n🏠 REAL ESTATE LISTINGS:")
            print("=" * 50)
            cur.execute("""
                SELECT id, title, location, price, bedrooms, bathrooms, created_at 
                FROM real_estate_listings 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            listings = cur.fetchall()
            
            if listings:
                for listing in listings:
                    print(f"ID: {listing[0]}")
                    print(f"Title: {listing[1]}")
                    print(f"Location: {listing[2]}")
                    print(f"Price: {listing[3]}")
                    print(f"Bedrooms: {listing[4]}")
                    print(f"Bathrooms: {listing[5]}")
                    print(f"Created: {listing[6]}")
                    print("-" * 30)
            else:
                print("No real estate listings found")
            
           
            print("\n💰 INTEREST RATES:")
            print("=" * 50)
            cur.execute("""
                SELECT id, rate_type, rate, apr, institution, created_at 
                FROM financial_interest_rates 
                ORDER BY created_at DESC 
                LIMIT 5
            """)
            rates = cur.fetchall()
            
            if rates:
                for rate in rates:
                    print(f"ID: {rate[0]}")
                    print(f"Type: {rate[1]}")
                    print(f"Rate: {rate[2]}")
                    print(f"APR: {rate[3]}")
                    print(f"Institution: {rate[4]}")
                    print(f"Created: {rate[5]}")
                    print("-" * 30)
            else:
                print("No interest rates found")
            
           
            print("\n📊 TABLE COUNTS:")
            print("=" * 50)
            
            cur.execute("SELECT COUNT(*) FROM scrape_logs")
            scrape_count = cur.fetchone()[0]
            print(f"Scrape logs: {scrape_count}")
            
            cur.execute("SELECT COUNT(*) FROM real_estate_listings")
            listing_count = cur.fetchone()[0]
            print(f"Real estate listings: {listing_count}")
            
            cur.execute("SELECT COUNT(*) FROM financial_interest_rates")
            rate_count = cur.fetchone()[0]
            print(f"Interest rates: {rate_count}")
            
            
            print("\n🔍 LATEST SCRAPE RAW DATA:")
            print("=" * 50)
            cur.execute("""
                SELECT raw_data, error_message 
                FROM scrape_logs 
                WHERE task_type = 'real_estate'
                ORDER BY created_at DESC 
                LIMIT 1
            """)
            latest = cur.fetchone()
            
            if latest and latest[0]:
                print("Raw data structure:")
                try:
                    if isinstance(latest[0], str):
                        raw_data = json.loads(latest[0])
                    else:
                        raw_data = latest[0]
                    print(json.dumps(raw_data, indent=2, default=str))
                except:
                    print(f"Raw data (string): {latest[0]}")
                
                if latest[1]:
                    print(f"\nError message: {latest[1]}")
            else:
                print("No recent real estate scrape data found")
                
    except Exception as e:
        print(f"❌ Error checking database: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        conn.close()

if __name__ == "__main__":
    check_database() 