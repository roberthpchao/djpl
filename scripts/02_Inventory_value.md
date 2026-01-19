We will use the **same `dummyjson` website**.

It is the perfect choice for this exercise because it already provides the two "raw" ingredients we need: **Price** and **Stock**.

In a real Data Engineering job, businesses often don't just want the raw numbers from an API; they want **Derived Metrics** (numbers calculated by you). By calculating the "Inventory Value," you are moving from a "Data Mover" to a "Data Transformer."

---

### The Goal

We are going to create a new column in your database called `inventory_value`.
The logic is simple:


### 🛠️ Step 1: Update the MySQL Table

First, we need to tell MySQL to make room for this new piece of information. Open **MySQL Workbench** and run this command:

```sql
USE de102_analytics;

ALTER TABLE product_inventory 
ADD COLUMN inventory_value DECIMAL(15, 2);

```

---

### 🛠️ Step 2: Update the ETL Script

Now, we update the Python script to perform the math before the data is saved. I’ve removed the "flair" (emojis) so you can see what professional, clean terminal output looks like.

**Update the loop in your `etl_pipeline.py` with this logic:**

```python
# ... inside the products loop ...
for item in products:
    # 1. Capture the raw data
    p_id = item['id']
    title = item['title']
    category = item['category']
    price = item['price']
    stock = item['stock']
    rating = item['rating']

    # 2. THE TRANSFORMATION: Calculate the new metric
    inv_value = price * stock

    # 3. THE LOAD: Add the new value to the SQL query
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
    print(f"Processed: {title} | Total Value: ${inv_value:,.2f}")

```

---

### Why is this important?

Imagine your boss asks: *"Which category of products represents our biggest financial risk if the warehouse burns down?"*

* **Without this step:** You have to do the math inside Power BI every time.
* **With this step:** The math is already done. Power BI just has to display it. This makes your dashboards much faster.

---

### 🚀 Try it out

1. Run the `ALTER TABLE` command in MySQL Workbench.
2. Update and run your `scripts/etl_pipeline.py`.
3. Check the results in MySQL:
```sql
SELECT title, price, stock, inventory_value 
FROM product_inventory 
ORDER BY inventory_value DESC;

```



**my mistakes indent**

This is a classic "Ghost in the Machine" moment in Data Engineering! If your terminal showed the "Total Value" prices (meaning Python did the math correctly), but MySQL shows `NULL`, it usually means one of two things:

1. **The Update Trap:** Since you already had data in the table from the previous run, the script performed an **UPDATE** instead of an **INSERT**. If the logic in the `UPDATE` part has a tiny mismatch, it won't fill those empty holes.
2. **Indentation:** In Python, if the `conn.commit()` or the `cursor.execute()` is not indented perfectly inside the `for` loop, it might only save the very last item or fail to save at all.

Let's fix this with a **"Clean Slate"** approach.

---

### 🛠️ Step 1: Wipe the Table (The Clean Slate)

Before running the script again, let's empty the table so we can see a fresh "INSERT" happen. Open **MySQL Workbench** and run this:

```sql
USE de102_analytics;

-- This empties the data but keeps the columns/structure
TRUNCATE TABLE product_inventory; 

-- Verify it is empty
SELECT * FROM product_inventory;

```

---

### 🛠️ Step 2: The Corrected Python Code

I have fixed the indentation and added the `inventory_value` to the `CREATE TABLE` statement inside the script. This ensures that even if you deleted the database, the script would recreate it perfectly with the new column.

**Copy this into your `etl_pipeline_invalue.py`:**

```python
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

```

---

### 🔍 Why did your first attempt return NULL?

In your previous snippet, if the `conn.commit()` was indented differently, or if the `ON DUPLICATE KEY UPDATE` was looking for a value that hadn't been "sent" yet in the `VALUES()` function, it results in a `NULL`.

**A common "Oops" in MySQL:** If you add a column in Workbench but don't define it in your Python `INSERT` statement, MySQL just shrugs and puts a `NULL` there. By using the `TRUNCATE` command in Step 1, we force Python to do a brand new `INSERT` for every row.

---

### 🚀 Try it now

1. Run the `TRUNCATE` command in Workbench.
2. Run `python etl_pipeline_invalue.py`.
3. Go back to Workbench and run:
```sql
SELECT title, price, stock, inventory_value FROM product_inventory;

```

