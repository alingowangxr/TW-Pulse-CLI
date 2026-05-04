# -*- coding: utf-8 -*-
import os, io, time, random, sqlite3, requests
import urllib3
import pandas as pd
import yfinance as yf
from yfinance import shared as yf_shared
from io import StringIO
from datetime import datetime
from tqdm import tqdm

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

try:
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# ========== 1. 環境設定 ==========
MARKET_CODE = "tw-share"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "tw_stock_warehouse.db")

def log(msg: str):
    print(f"{pd.Timestamp.now():%H:%M:%S}: {msg}", flush=True)

# ========== 2. 資料庫初始化 ==========
def init_db():
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute('''CREATE TABLE IF NOT EXISTS stock_prices (
                            date TEXT, symbol TEXT, open REAL, high REAL, 
                            low REAL, close REAL, volume INTEGER,
                            PRIMARY KEY (date, symbol))''')
        conn.execute('''CREATE TABLE IF NOT EXISTS stock_info (
                            symbol TEXT PRIMARY KEY, name TEXT, sector TEXT, market TEXT, updated_at TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS stock_exclusions (
                            symbol TEXT PRIMARY KEY, reason TEXT, updated_at TEXT)''')
    finally:
        conn.close()

# ========== 3. 獲取台股清單 (完整網址，過濾邏輯) ==========
def get_tw_stock_list(summary_only=False):
    url_configs = [
    {'name': 'listed', 'url': 'https://isin.twse.com.tw/isin/class_main.jsp?market=1&issuetype=1&Page=1&chklike=Y', 'suffix': '.TW'},
    {'name': 'dr', 'url': 'https://isin.twse.com.tw/isin/class_main.jsp?owncode=&stockname=&isincode=&market=1&issuetype=J&industry_code=&Page=1&chklike=Y', 'suffix': '.TW'},
    {'name': 'otc', 'url': 'https://isin.twse.com.tw/isin/class_main.jsp?market=2&issuetype=4&Page=1&chklike=Y', 'suffix': '.TWO'},
    {'name': 'etf', 'url': 'https://isin.twse.com.tw/isin/class_main.jsp?owncode=&stockname=&isincode=&market=1&issuetype=I&industry_code=&Page=1&chklike=Y', 'suffix': '.TW'},
    {'name': 'rotc', 'url': 'https://isin.twse.com.tw/isin/class_main.jsp?owncode=&stockname=&isincode=&market=E&issuetype=R&industry_code=&Page=1&chklike=Y', 'suffix': '.TWO'},
    {'name': 'tw_innovation', 'url': 'https://isin.twse.com.tw/isin/class_main.jsp?owncode=&stockname=&isincode=&market=C&issuetype=C&industry_code=&Page=1&chklike=Y', 'suffix': '.TW'},
    {'name': 'otc_innovation', 'url': 'https://isin.twse.com.tw/isin/class_main.jsp?owncode=&stockname=&isincode=&market=A&issuetype=C&industry_code=&Page=1&chklike=Y', 'suffix': '.TWO'},
]

    
    if not summary_only:
        log(f"📡 獲取台股清單 (自動跳過權證分類)...")
    conn = sqlite3.connect(DB_PATH)
    stock_list = []
    fetch_failures = 0
    excluded_symbols = {
        row[0] for row in conn.execute("SELECT symbol FROM stock_exclusions")
    }
    
    for cfg in url_configs:
        # 💡 核心過濾：如果名稱包含 'warrant'，直接跳過不解析、不存入資料庫
        if 'warrant' in cfg['name']:
            log(f"⏭️  跳過分類: {cfg['name']}")
            continue
            
        try:
            resp = requests.get(cfg['url'], timeout=15, verify=False)
            dfs = pd.read_html(StringIO(resp.text), header=0)
            if not dfs: continue
            df = dfs[0]
            
            for _, row in df.iterrows():
                code = str(row['有價證券代號']).strip()
                name = str(row['有價證券名稱']).strip()
                sector = str(row.get('產業別', 'Unknown')).strip()
                
                if code.isalnum() and len(code) >= 4:
                    symbol = f"{code}{cfg['suffix']}"
                    if symbol in excluded_symbols:
                        continue
                    conn.execute("""
                        INSERT OR REPLACE INTO stock_info (symbol, name, sector, market, updated_at) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (symbol, name, sector, cfg['name'], datetime.now().strftime("%Y-%m-%d")))
                    stock_list.append((symbol, name))
        except Exception as e:
            fetch_failures += 1
            if not summary_only:
                log(f"⚠️ {cfg['name']} 獲取失敗: {e}")
            
    conn.commit()
    conn.close()
    return list(set(stock_list)), fetch_failures

def mark_symbol_excluded(conn, symbol, reason):
    conn.execute("""
        INSERT OR REPLACE INTO stock_exclusions (symbol, reason, updated_at)
        VALUES (?, ?, ?)
    """, (symbol, reason, datetime.now().strftime("%Y-%m-%d")))

def should_exclude_from_error(error_text: str) -> bool:
    if not error_text:
        return False

    text = error_text.lower()
    exclude_markers = [
        "no price data found",
        "possibly delisted",
        "no timezone found",
    ]
    return any(marker in text for marker in exclude_markers)

# ========== 4. 下載邏輯 (單執行緒穩定版) ==========
def download_one_stable(symbol, mode, start_date=None, end_date=None):
    if start_date is None:
        start_date = "2023-01-01" if mode == 'hot' else "1993-01-04"
    try:
        ticker_key = symbol.upper()
        yf_shared._ERRORS.pop(ticker_key, None)
        # 強制單執行緒，防止記憶體污染
        df = yf.download(symbol, start=start_date, end=end_date, progress=False, timeout=20, 
                         auto_adjust=True, threads=False)
        error_text = yf_shared._ERRORS.get(ticker_key)
        if df is None or df.empty:
            return None, error_text
        
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        
        df.reset_index(inplace=True)
        df.columns = [c.lower() for c in df.columns]
        df['date'] = pd.to_datetime(df['date']).dt.tz_localize(None).dt.strftime('%Y-%m-%d')
        df_final = df[['date', 'open', 'high', 'low', 'close', 'volume']].copy()
        df_final['symbol'] = symbol
        return df_final, error_text
    except Exception as e:
        return None, str(e)

# ========== 5. 主流程 ==========
def run_sync(
    mode='hot',
    start_date=None,
    end_date=None,
    max_workers=None,
    progress_every=100,
    summary_only=True,
):
    start_time = time.time()
    init_db()
    
    items, fetch_failures = get_tw_stock_list(summary_only=summary_only)
    if not items:
        log("❌ 無法獲取股票清單")
        return {"success": 0, "has_changed": False}

    log(f"🚀 開始同步 TW | 排除權證後剩餘: {len(items)} 檔 | 模式: {mode}")

    success_count = 0
    fail_list = []
    excluded_count = 0
    conn = sqlite3.connect(DB_PATH, timeout=60)
    
    iterator = items if summary_only else tqdm(items, desc="TW同步")
    for index, (symbol, name) in enumerate(iterator, start=1):
        df_res, error_text = download_one_stable(symbol, mode, start_date=start_date, end_date=end_date)
        if df_res is not None:
            df_res.to_sql('stock_prices', conn, if_exists='append', index=False, 
                          method=lambda table, conn, keys, data_iter: 
                          conn.executemany(f"INSERT OR REPLACE INTO {table.name} ({', '.join(keys)}) VALUES ({', '.join(['?']*len(keys))})", data_iter))
            success_count += 1
        else:
            fail_list.append(symbol)
            if should_exclude_from_error(error_text):
                mark_symbol_excluded(conn, symbol, error_text[:255])
                excluded_count += 1
            elif not summary_only:
                log(f"⚠️ 下載失敗但不加入排除名單: {symbol}")
        time.sleep(0.05)

        if progress_every and (index % progress_every == 0 or index == len(items)):
            log(f"📈 進度：{index}/{len(items)}")
    
    conn.commit()
    if not summary_only:
        log(f"🧹 優化資料庫 (VACUUM)...")
    conn.execute("VACUUM")
    conn.close()

    duration = (time.time() - start_time) / 60
    log(
        f"📊 同步完成！成功: {success_count}/{len(items)} | "
        f"排除: {excluded_count} | 清單抓取失敗: {fetch_failures} | "
        f"耗時: {duration:.1f} 分鐘"
    )
    
    return {"success": success_count, "total": len(items), "fail_list": fail_list, "has_changed": success_count > 0}

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Download TW stock warehouse data")
    parser.add_argument(
        "--mode",
        choices=["hot", "full"],
        default="hot",
        help="Download mode: hot (recent data) or full (full history)",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=100,
        help="Print a progress line every N symbols (default: 100)",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print per-symbol downloader output",
    )
    args = parser.parse_args()

    run_sync(
        mode=args.mode,
        progress_every=args.progress_every,
        summary_only=not args.verbose,
    )

