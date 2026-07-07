import sqlite3
import pandas as pd
from src.config import DB_PATH

def get_connection():
    return sqlite3.connect(DB_PATH)

def get_current_inventory():
    conn = get_connection()
    query = """
        SELECT i.store_id, s.name as store_name, s.city,
               i.product_id, p.name as product_name, p.category, p.weight_kg,
               i.quantity, i.last_updated
        FROM inventory i
        JOIN stores s ON i.store_id = s.store_id
        JOIN products p ON i.product_id = p.product_id
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_sales_history(store_id, product_id, days=30):
    conn = get_connection()
    query = """
        SELECT quantity, sale_date
        FROM sales_history
        WHERE store_id = ? AND product_id = ?
        ORDER BY sale_date DESC
        LIMIT ?
    """
    df = pd.read_sql_query(query, conn, params=(store_id, product_id, days))
    conn.close()
    return df

def get_shipping_costs(origin, destination):
    conn = get_connection()
    query = """
        SELECT * FROM shipping_costs
        WHERE origin_city = ? AND destination_city = ?
    """
    df = pd.read_sql_query(query, conn, params=(origin, destination))
    conn.close()
    return df

def get_store_city(store_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT city FROM stores WHERE store_id = ?", (store_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None

def get_product_weight(product_id):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT weight_kg FROM products WHERE product_id = ?", (product_id,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else 1.0
