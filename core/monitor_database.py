#!/usr/bin/env python3
"""
Monitor database for new listings in real-time
"""

import sys
import os
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from database.database import get_db_connection
    print("✅ Successfully imported database functions")
except ImportError as e:
    print(f"❌ Failed to import database functions: {e}")
    sys.exit(1)

def get_listing_count():
    """Get current count of listings"""
    conn = get_db_connection()
    if not conn:
        return None
    
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM real_estate_listings")
            count = cur.fetchone()[0]
            return count
    except Exception as e:
        print(f"Error getting count: {e}")
        return None
    finally:
        conn.close()

def get_recent_listings(limit=5):
    """Get most recent listings"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, title, location, price, bedrooms, bathrooms, created_at 
                FROM real_estate_listings 
                ORDER BY created_at DESC 
                LIMIT %s
            """, (limit,))
            return cur.fetchall()
    except Exception as e:
        print(f"Error getting recent listings: {e}")
        return []
    finally:
        conn.close()

def monitor_database():
    """Monitor database for changes"""
    print("🔍 Monitoring Database for New Listings")
    print("Press Ctrl+C to stop monitoring\n")
    
    last_count = get_listing_count()
    if last_count is None:
        print("❌ Could not connect to database")
        return
    
    print(f"📊 Starting count: {last_count} listings")
    print("⏳ Waiting for new listings...\n")
    
    try:
        while True:
            time.sleep(5)  # Check every 5 seconds
            
            current_count = get_listing_count()
            if current_count is None:
                continue
            
            if current_count > last_count:
                new_listings = current_count - last_count
                print(f"🎉 {new_listings} new listing(s) added! Total: {current_count}")
                
                # Show the new listings
                recent = get_recent_listings(new_listings)
                for listing in recent:
                    print(f"   ✅ ID {listing[0]}: {listing[1][:50]}...")
                    print(f"      📍 {listing[2]} | 💰 {listing[3]} | 🏠 {listing[4]}bed/{listing[5]}bath")
                    print(f"      ⏰ {listing[6]}")
                    print()
                
                last_count = current_count
            
    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped")

if __name__ == "__main__":
    monitor_database() 