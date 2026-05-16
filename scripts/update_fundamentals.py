"""
Batch update script for Taiwan stock fundamental data.
Inspired by alingowangxr/My-TW-Coverage valuation scripts.
"""

import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
import pandas as pd
import yfinance as yf
from tqdm import tqdm

# Constants
DB_PATH = Path("tw_stock_warehouse.db")
if not DB_PATH.exists():
    DB_PATH = Path("data/tw_stock_warehouse.db")

def get_tickers_from_db():
    """Get all tickers from stock_info table."""
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        cur.execute("SELECT symbol FROM stock_info")
        tickers = [row[0] for row in cur.fetchall()]
        return tickers
    finally:
        conn.close()

def clean_ticker(ticker: str) -> str:
    """Standardize ticker for yfinance."""
    ticker = ticker.upper().strip()
    if ticker.endswith(".TW") or ticker.endswith(".TWO"):
        return ticker
    # If it's just a number, we might not know the market, 
    # but usually yfinance handles it or we've already stored it with suffix.
    return ticker

def safe_float(value):
    """Safely convert value to float."""
    try:
        if value is None or pd.isna(value):
            return None
        return float(value)
    except (ValueError, TypeError):
        return None

def fetch_yfinance_fundamentals(ticker: str):
    """Fetch fundamental data using yfinance."""
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        if not info or not info.get("currentPrice"):
            return None

        # Extract metrics (aligning with FundamentalData model)
        data = {
            "ticker": ticker.replace(".TW", "").replace(".TWO", ""),
            "pe_ratio": safe_float(info.get("trailingPE")),
            "pb_ratio": safe_float(info.get("priceToBook")),
            "ps_ratio": safe_float(info.get("priceToSalesTrailing12Months")),
            "peg_ratio": safe_float(info.get("pegRatio")),
            "ev_ebitda": safe_float(info.get("enterpriseToEbitda")),
            "roe": safe_float(info.get("returnOnEquity", 0)) * 100 if info.get("returnOnEquity") else None,
            "roa": safe_float(info.get("returnOnAssets", 0)) * 100 if info.get("returnOnAssets") else None,
            "npm": safe_float(info.get("profitMargins", 0)) * 100 if info.get("profitMargins") else None,
            "opm": safe_float(info.get("operatingMargins", 0)) * 100 if info.get("operatingMargins") else None,
            "gpm": safe_float(info.get("grossMargins", 0)) * 100 if info.get("grossMargins") else None,
            "eps": safe_float(info.get("trailingEps")),
            "bvps": safe_float(info.get("bookValue")),
            "dps": safe_float(info.get("dividendRate")),
            "revenue_growth": safe_float(info.get("revenueGrowth", 0)) * 100 if info.get("revenueGrowth") else None,
            "earnings_growth": safe_float(info.get("earningsGrowth", 0)) * 100 if info.get("earningsGrowth") else None,
            "debt_to_equity": safe_float(info.get("debtToEquity", 0)) / 100 if info.get("debtToEquity") else None,
            "current_ratio": safe_float(info.get("currentRatio")),
            "quick_ratio": safe_float(info.get("quickRatio")),
            "dividend_yield": safe_float(info.get("dividendYield", 0)) * 100 if info.get("dividendYield") else None,
            "payout_ratio": safe_float(info.get("payoutRatio", 0)) * 100 if info.get("payoutRatio") else None,
            "market_cap": safe_float(info.get("marketCap", 0)) / 1_000_000 if info.get("marketCap") else None,
            "enterprise_value": safe_float(info.get("enterpriseValue", 0)) / 1_000_000 if info.get("enterpriseValue") else None,
            "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return data
    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return None

def update_db_batch(data_list):
    """Batch insert/replace data into stock_fundamentals table."""
    if not data_list:
        return
    
    conn = sqlite3.connect(DB_PATH)
    try:
        columns = [
            "ticker", "pe_ratio", "pb_ratio", "ps_ratio", "peg_ratio", 
            "ev_ebitda", "roe", "roa", "npm", "opm", "gpm", "eps", 
            "bvps", "dps", "revenue_growth", "earnings_growth", 
            "debt_to_equity", "current_ratio", "quick_ratio", 
            "dividend_yield", "payout_ratio", "market_cap", 
            "enterprise_value", "updated_at"
        ]
        placeholders = ", ".join(["?"] * len(columns))
        sql = f"INSERT OR REPLACE INTO stock_fundamentals ({', '.join(columns)}) VALUES ({placeholders})"
        
        values = [[d.get(col) for col in columns] for d in data_list]
        conn.executemany(sql, values)
        conn.commit()
    finally:
        conn.close()

def main():
    print(f"Starting fundamental data sync to {DB_PATH}...")
    tickers = get_tickers_from_db()
    print(f"Found {len(tickers)} tickers to update.")
    
    batch_size = 20
    current_batch = []
    
    for i, ticker in enumerate(tqdm(tickers, desc="Updating Fundamentals")):
        data = fetch_yfinance_fundamentals(ticker)
        if data:
            current_batch.append(data)
        
        if len(current_batch) >= batch_size:
            update_db_batch(current_batch)
            current_batch = []
        
        # Rate limiting
        time.sleep(0.1)
    
    # Final batch
    if current_batch:
        update_db_batch(current_batch)
        
    print("\nSync complete!")

if __name__ == "__main__":
    main()
