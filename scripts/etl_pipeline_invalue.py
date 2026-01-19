import os
import requests
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

def run_product_pipeline():
    try:
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASS'),
            database=os.getenv('DB_NAME')
        )
        cursor = conn.cursor()

        # Added inventory_value to the creation script for safety
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_inventory (
                id INT PRIMARY KEY,
                title VARCHAR(255),
                category VARCHAR(100),
                price DECIMAL(10, 2),
                stock INT,
                rating DECIMAL(3, 2),
                inventory_value DECIMAL(15, 2),
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)

        print("Connecting to DummyJSON API...")
        url = "https://dummyjson.com/products"
        response = requests.get(url)
        
        if response.status_code == 200:
            products = response.json()['products']
            
            for item in products:
                # 1. Capture & Transform
                p_id = item['id']
                title = item['title']
                category = item['category']
                price = item['price']
                stock = item['stock']
                rating = item['rating']
                inv_value = price * stock # The calculation

                # 2. Load
                sql = """
                    INSERT INTO product_inventory (id, title, category, price, stock, rating, inventory_value)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE 
                        price=VALUES(price), 
                        stock=VALUES(stock), 
                        inventory_value=VALUES(inventory_value)
                """
                val = (p_id, title, category, price, stock, rating, inv_value)
                
                cursor.execute(sql, val)
                print(f"Processed: {title} | Value: ${inv_value:,.2f}")

            # 3. COMMIT (Make sure this is OUTSIDE the for loop but INSIDE the if block)
            conn.commit()
            print(f"Success! {len(products)} products synced.")
        else:
            print(f"API Error: {response.status_code}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    run_product_pipeline()