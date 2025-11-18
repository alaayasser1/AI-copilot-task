# setup.py
import os
import urllib.request
import sqlite3

os.makedirs("data", exist_ok=True)
os.makedirs("docs", exist_ok=True)

# تحميل قاعدة البيانات
db_url = "https://raw.githubusercontent.com/jpwhite3/northwind-SQLite3/main/dist/northwind.db"
urllib.request.urlretrieve(db_url, "data/northwind.sqlite")
print("northwind.sqlite downloaded ")

# إنشاء الـ views عشان الـ SQL يبقى أسهل
conn = sqlite3.connect("data/northwind.sqlite")
c = conn.cursor()
c.executescript("""
CREATE VIEW IF NOT EXISTS orders AS SELECT * FROM Orders;
CREATE VIEW IF NOT EXISTS order_items AS SELECT * FROM "Order Details";
CREATE VIEW IF NOT EXISTS products AS SELECT * FROM Products;
CREATE VIEW IF NOT EXISTS customers AS SELECT * FROM Customers;
CREATE VIEW IF NOT EXISTS categories AS SELECT * FROM Categories;
""")
conn.commit()
conn.close()
print("views created")

# إنشاء الـ docs الأربعة
docs = {
    "docs/marketing_calendar.md": """# Northwind Marketing Calendar (1997)
## Summer Beverages 1997
- Dates: 1997-06-01 to 1997-06-30
- Notes: Focus on Beverages and Condiments.

## Winter Classics 1997
- Dates: 1997-12-01 to 1997-12-31
- Notes: Push Dairy Products and Confections for holiday gifting.
""",
    "docs/kpi_definitions.md": """# KPI Definitions
## Average Order Value (AOV)
- AOV = SUM(UnitPrice * Quantity * (1 - Discount)) / COUNT(DISTINCT OrderID)

## Gross Margin
- GM = SUM((UnitPrice - CostOfGoods) * Quantity * (1 - Discount))
- If cost is missing, approximate with category-level average (document your approach).
""",
    "docs/catalog.md": """# Catalog Snapshot
- Categories include Beverages, Condiments, Confections, Dairy Products, Grains/Cereals, Meat/Poultry, Produce, Seafood.
- Products map to categories as in the Northwind DB.
""",
    "docs/product_policy.md": """# Returns & Policy
- Perishables (Produce, Seafood, Dairy): 3–7 days.
- Beverages unopened: 14 days; opened: no returns.
- Non-perishables: 30 days.
"""
}

for path, content in docs.items():
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip() + "\n")

print("docs created ")
