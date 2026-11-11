import sqlite3

DB_PATH = "store.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            color TEXT,
            size TEXT,
            price REAL NOT NULL,
            stock INTEGER NOT NULL DEFAULT 0
        )
    """)
    if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        conn.executemany(
            "INSERT INTO products (name, category, color, size, price, stock) VALUES (?,?,?,?,?,?)",
                        [
                # Shoes
                ("Classic Black Sneakers", "shoes", "black", "8", 45.0, 10),
                ("Black Running Shoes", "shoes", "black", "9", 60.0, 5),
                ("Black Canvas Shoes", "shoes", "black", "8", 35.0, 8),
                ("Black Casual Shoes", "shoes", "black", "8", 49.0, 6),
                ("Black Sports Shoes", "shoes", "black", "7", 40.0, 9),
                ("Black Formal Shoes", "shoes", "black", "9", 75.0, 4),
                ("Black Leather Loafers", "shoes", "black", "8", 65.0, 5),
                ("Black High-Top Sneakers", "shoes", "black", "10", 55.0, 6),
                ("Black Sandals", "shoes", "black", "8", 22.0, 15),
                ("White Canvas Shoes", "shoes", "white", "8", 30.0, 12),
                ("White Running Shoes", "shoes", "white", "9", 58.0, 7),
                ("White Leather Sneakers", "shoes", "white", "8", 70.0, 5),
                ("White Slip-On Shoes", "shoes", "white", "7", 28.0, 10),
                ("Brown Leather Boots", "shoes", "brown", "8", 85.0, 3),
                ("Brown Casual Loafers", "shoes", "brown", "9", 55.0, 5),
                ("Brown Sandals", "shoes", "brown", "8", 25.0, 12),
                ("Red Running Shoes", "shoes", "red", "8", 52.0, 4),
                ("Blue Sports Shoes", "shoes", "blue", "9", 48.0, 6),
                ("Grey Walking Shoes", "shoes", "grey", "8", 42.0, 8),
                # Clothing
                ("Blue Denim Jacket", "clothing", "blue", "M", 55.0, 7),
                ("Black Leather Jacket", "clothing", "black", "L", 120.0, 2),
                ("Black Cotton T-Shirt", "clothing", "black", "M", 15.0, 20),
                ("White Cotton T-Shirt", "clothing", "white", "L", 15.0, 25),
                ("Red Cotton T-Shirt", "clothing", "red", "M", 16.0, 14),
                ("Navy Polo Shirt", "clothing", "blue", "M", 25.0, 11),
                ("Blue Denim Jeans", "clothing", "blue", "32", 45.0, 10),
                ("Black Formal Trousers", "clothing", "black", "32", 35.0, 7),
                ("Black Hoodie", "clothing", "black", "L", 40.0, 8),
                ("Grey Hoodie", "clothing", "grey", "M", 38.0, 9),
                ("Green Hoodie", "clothing", "green", "L", 42.0, 5),
                                ("Red Cotton Kurta", "clothing", "red", "M", 30.0, 6),
                ("Blue Cotton Kurta", "clothing", "blue", "L", 32.0, 5),
                ("Black Kurta", "clothing", "black", "M", 34.0, 4),
            ],
        )
    conn.commit()
    conn.close()

def search_products(category=None, color=None, size=None, max_price=None, keyword=None):
    query = "SELECT * FROM products WHERE stock > 0"
    params = []
    if category: query += " AND category = ?"; params.append(category)
    if color: query += " AND color = ?"; params.append(color)
    if size: query += " AND size = ?"; params.append(size)
    if max_price: query += " AND price <= ?"; params.append(max_price)
    if keyword:
        k = keyword.lower().strip()
        if k in ("kurti", "kurthi", "kurtha", "kurtas", "kurthis"):
            k = "kurta"
        if len(k) > 3 and k.endswith("s"):
            k = k[:-1]
        query += " AND LOWER(name) LIKE ?"
        params.append(f"%{k}%")
    conn = get_conn()
    rows = [dict(r) for r in conn.execute(query, params).fetchall()]
    conn.close()
    return rows
def reduce_stock(product_id):
    conn = get_conn()
    conn.execute("UPDATE products SET stock = stock - 1 WHERE id = ? AND stock > 0", (product_id,))
    conn.commit()
    conn.close()