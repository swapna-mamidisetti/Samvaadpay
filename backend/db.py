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
                ("Classic Black Sneakers", "shoes", "black", "8", 45.0, 10),
                ("Black Running Shoes", "shoes", "black", "9", 60.0, 5),
                ("White Canvas Shoes", "shoes", "white", "8", 30.0, 12),
                ("Brown Leather Boots", "shoes", "brown", "8", 85.0, 3),
                ("Blue Denim Jacket", "clothing", "blue", "M", 55.0, 7),
            ],
        )
    conn.commit()
    conn.close()

def search_products(category=None, color=None, size=None, max_price=None):
    query = "SELECT * FROM products WHERE stock > 0"
    params = []
    if category: query += " AND category = ?"; params.append(category)
    if color: query += " AND color = ?"; params.append(color)
    if size: query += " AND size = ?"; params.append(size)
    if max_price: query += " AND price <= ?"; params.append(max_price)
    conn = get_conn()
    rows = [dict(r) for r in conn.execute(query, params).fetchall()]
    conn.close()
    return rows

def reduce_stock(product_id):
    conn = get_conn()
    conn.execute("UPDATE products SET stock = stock - 1 WHERE id = ? AND stock > 0", (product_id,))
    conn.commit()
    conn.close()