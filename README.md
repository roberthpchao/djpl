Let’s switch to **DummyJSON**. It is one of the most reliable "practice" APIs in the world because it is designed specifically for developers to test their code.

It requires **no API keys** and is almost never down.

---

### The New Target: Product Inventory Data

We will fetch a list of **Products** (like Smartphones and Laptops). This is great for Data Engineering because it includes:

* **Dimensions:** Product Name, Category, Brand.
* **Metrics:** Price, Stock level, Rating.

### 1. Update your `.env` (No changes needed)

Keep your database credentials exactly as they are.

### 2. Update your ETL Script (`scripts/etl_pipeline.py`)

Copy and paste this new code into your `etl_pipeline.py`. I have simplified it so it creates a table called `product_inventory`.

```python
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

```

---

### 🛠️ How to run and verify

1. **Run the script:**
```bash
python scripts/etl_pipeline.py

```


2. **Verify in MySQL Workbench:**
Connect to your **Instance 95** and run:
```sql
USE de102_analytics;
SELECT category, COUNT(*), AVG(price) 
FROM product_inventory 
GROUP BY category;

```



---

### 📊 Power BI Bonus

Since you now have **Categories** (Smartphones, Fragrances, Laptops), you can create a **TreeMap** or a **Pie Chart** in Power BI showing which category has the most expensive products or the highest stock levels.

**Does this one connect for you? (You should see "Synced: iPhone 9..." in your terminal if it's working!)**

Why didn't we use mock_api.py?
We skipped it because DummyJSON is the API.

In our earlier session, you were playing both roles: you were the "Company" (Mock API) and the "Data Engineer" (ETL Script).

In this new version, DummyJSON is the "Company." You don't need to run their code because they are already running it on their own servers 24/7. You only had to write the "Data Engineer" part to go get it.
