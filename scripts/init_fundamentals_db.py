import sqlite3
import os
from pathlib import Path

def init_fundamentals_table():
    db_path = Path("tw_stock_warehouse.db")
    if not db_path.exists():
        db_path = Path("data/tw_stock_warehouse.db")
    
    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        return

    conn = sqlite3.connect(db_path)
    try:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS stock_fundamentals (
                ticker TEXT PRIMARY KEY,
                pe_ratio REAL,
                pb_ratio REAL,
                ps_ratio REAL,
                peg_ratio REAL,
                ev_ebitda REAL,
                roe REAL,
                roa REAL,
                npm REAL,
                opm REAL,
                gpm REAL,
                eps REAL,
                bvps REAL,
                dps REAL,
                revenue_growth REAL,
                earnings_growth REAL,
                debt_to_equity REAL,
                current_ratio REAL,
                quick_ratio REAL,
                dividend_yield REAL,
                payout_ratio REAL,
                market_cap REAL,
                enterprise_value REAL,
                updated_at TEXT
            )
        ''')
        print(f"Successfully created/verified stock_fundamentals table in {db_path}")
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_fundamentals_table()
