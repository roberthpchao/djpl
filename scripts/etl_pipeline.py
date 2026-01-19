import os
import requests
import pandas as pd
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def run_product_pipeline():
    try:
        # 1. Connect to MySQL
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            database=os.getenv('DB_NAME')
        )
        cursor = conn.cursor()

        # 2. Create the Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_inventory (
                id INT PRIMARY KEY,
                title VARCHAR(255),
                category VARCHAR(100),
                price DECIMAL(10, 2),
                stock INT,
                rating DECIMAL(3, 2),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)

        # 3. EXTRACT from DummyJSON
        print("Connecting to DummyJSON API...")
        url = "https://dummyjson.com/products"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            products = data['products'] # This is the list of items
            
            # 4. TRANSFORM & LOAD
            for item in products:
                # We use "INSERT ... ON DUPLICATE KEY UPDATE" to keep our inventory fresh
                sql = """
                    INSERT INTO product_inventory (id, title, category, price, stock, rating)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        price=VALUES(price), 
                        stock=VALUES(stock), 
                        rating=VALUES(rating)
                """
                val = (
                    item['id'], 
                    item['title'], 
                    item['category'], 
                    item['price'], 
                    item['stock'], 
                    item['rating']
                )
                cursor.execute(sql, val)
                print(f"📦 Synced: {item['title']} (${item['price']})")

            conn.commit()
            print(f"\n✅ Success! {len(products)} products are now in your MySQL database.")
        else:
            print(f"❌ API Error: {response.status_code}")

    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    run_product_pipeline()