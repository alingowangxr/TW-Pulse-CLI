import sqlite3
from pathlib import Path

DB_PATH = Path("tw_stock_warehouse.db")
if not DB_PATH.exists():
    DB_PATH = Path("data/tw_stock_warehouse.db")

def verify():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        cur.execute("SELECT count(*) as count FROM stock_fundamentals")
        print(f"Total rows in stock_fundamentals: {cur.fetchone()['count']}")
        
        cur.execute("SELECT * FROM stock_fundamentals LIMIT 2")
        rows = cur.fetchall()
        for row in rows:
            print(dict(row))
    finally:
        conn.close()

if __name__ == "__main__":
    verify()
