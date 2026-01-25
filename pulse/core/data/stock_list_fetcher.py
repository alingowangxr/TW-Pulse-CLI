"""Stock list fetcher for Taiwan stocks (上市/上櫃).

抓取台灣上市股票和上櫃股票的代碼清單。
"""

from datetime import datetime
from pathlib import Path
from typing import Literal

import pandas as pd

from pulse.utils.logger import get_logger

log = get_logger(__name__)

# Try to import FinMind DataLoader
try:
    from FinMind.data import DataLoader

    FINMIND_AVAILABLE = True
except ImportError:
    FINMIND_AVAILABLE = False
    log.warning("FinMind SDK not installed. Run: pip install FinMind")


class StockListFetcher:
    """Fetch Taiwan stock code lists from FinMind."""

    # Market type constants (FinMind uses lowercase 'type' column)
    MARKET_TWSE = "twse"
    MARKET_TPEX = "tpex"
    MARKET_EMERGING = "emerging"

    def __init__(self, token: str = ""):
        """
        Initialize stock list fetcher.

        Args:
            token: FinMind API token (optional, for higher rate limits)
        """
        self.token = token
        self._dl: "DataLoader | None" = None
        self._all_stocks_cache: pd.DataFrame | None = None

    @property
    def dl(self) -> "DataLoader":
        """Lazy initialization of DataLoader."""
        if self._dl is None:
            if not FINMIND_AVAILABLE:
                raise ImportError("FinMind SDK not installed. Run: pip install FinMind")
            self._dl = DataLoader()
            if self.token:
                self._dl.login_by_token(api_token=self.token)
        return self._dl

    def _fetch_all_stocks(self) -> pd.DataFrame | None:
        """
        Fetch all Taiwan stock information from FinMind.

        Returns:
            DataFrame with all stock info, or None if failed
        """
        try:
            if self._all_stocks_cache is not None:
                return self._all_stocks_cache

            log.info("Fetching Taiwan stock info from FinMind...")
            df = self.dl.taiwan_stock_info()

            if df is None or df.empty:
                log.warning("No stock info returned from FinMind")
                return None

            self._all_stocks_cache = df
            log.info(f"Fetched {len(df)} stocks from FinMind")
            return df

        except Exception as e:
            log.error(f"Error fetching stock info from FinMind: {e}")
            return None

    def _is_valid_ticker(self, stock_id: str) -> bool:
        """
        Check if stock_id is a valid regular stock (not ETF, not special codes).

        Args:
            stock_id: Stock ID to validate

        Returns:
            True if valid regular stock (4-digit, starts with non-zero)
        """
        if not stock_id:
            return False
        # Regular stocks are 4 digits starting with 1-9
        if len(stock_id) == 4 and stock_id[0].isdigit() and stock_id[0] != "0":
            return True
        return False

    def _is_etf(self, stock_id: str) -> bool:
        """Check if stock is an ETF (starts with 00)."""
        return len(stock_id) == 4 and stock_id.startswith("00")

    def _is_tpex_special(self, stock_id: str) -> bool:
        """Check if stock is a TPEx special code (starts with 6, 7, or 8)."""
        return len(stock_id) == 4 and stock_id[0] in ("6", "7", "8")

    def get_twse_stocks(self, include_etf: bool = False) -> list[dict]:
        """
        Get list of TWSE (上市) stocks.

        Args:
            include_etf: Include ETF stocks (default: False)

        Returns:
            List of dicts with ticker, name, industry
        """
        df = self._fetch_all_stocks()
        if df is None:
            return []

        # Filter for TWSE stocks - FinMind uses 'type' column with 'twse'
        if "type" in df.columns:
            twse_df = df[df["type"] == self.MARKET_TWSE]
        else:
            log.warning("No 'type' column found in FinMind data")
            return []

        stocks = []
        for _, row in twse_df.iterrows():
            stock_id = str(row.get("stock_id", ""))

            # Filter by valid ticker
            if not self._is_valid_ticker(stock_id):
                # Optionally include ETFs
                if include_etf and self._is_etf(stock_id):
                    pass  # Include
                else:
                    continue

            stocks.append(
                {
                    "ticker": stock_id,
                    "name": row.get("stock_name", ""),
                    "industry": row.get("industry_category", ""),
                    "market": "TWSE",
                }
            )

        log.info(f"Found {len(stocks)} TWSE (上市) stocks")
        return stocks

    def get_tpex_stocks(self, include_etf: bool = False) -> list[dict]:
        """
        Get list of TPEx/OTC (上櫃) stocks.

        Args:
            include_etf: Include ETF stocks (default: False)

        Returns:
            List of dicts with ticker, name, industry
        """
        df = self._fetch_all_stocks()
        if df is None:
            return []

        # Filter for TPEx stocks - FinMind uses 'type' column with 'tpex'
        if "type" in df.columns:
            tpex_df = df[df["type"] == self.MARKET_TPEX]
        else:
            log.warning("No 'type' column found in FinMind data")
            return []

        stocks = []
        for _, row in tpex_df.iterrows():
            stock_id = str(row.get("stock_id", ""))

            # TPEx regular stocks typically start with 6, 7, or 8
            # Only include valid 4-digit codes
            if not self._is_valid_ticker(stock_id):
                if include_etf and self._is_etf(stock_id):
                    pass  # Include
                else:
                    continue

            stocks.append(
                {
                    "ticker": stock_id,
                    "name": row.get("stock_name", ""),
                    "industry": row.get("industry_category", ""),
                    "market": "TPEx",
                }
            )

        log.info(f"Found {len(tpex_df)} raw TPEx rows, {len(stocks)} valid stocks")
        return stocks

    def get_emerging_stocks(self) -> list[dict]:
        """
        Get list of Emerging stocks (興櫃).

        Returns:
            List of dicts with ticker, name, industry
        """
        df = self._fetch_all_stocks()
        if df is None:
            return []

        # Filter for Emerging stocks
        if "type" in df.columns:
            emerging_df = df[df["type"] == self.MARKET_EMERGING]
        else:
            return []

        stocks = []
        for _, row in emerging_df.iterrows():
            stock_id = str(row.get("stock_id", ""))
            stocks.append(
                {
                    "ticker": stock_id,
                    "name": row.get("stock_name", ""),
                    "industry": row.get("industry_category", ""),
                    "market": "Emerging",
                }
            )

        log.info(f"Found {len(stocks)} Emerging (興櫃) stocks")
        return stocks

    def get_all_stocks(self, include_etf: bool = False, include_emerging: bool = False) -> dict:
        """
        Get all Taiwan stocks separated by market type.

        Args:
            include_etf: Include ETF stocks
            include_emerging: Include Emerging (興櫃) stocks

        Returns:
            Dict with market lists
        """
        twse_stocks = self.get_twse_stocks(include_etf=include_etf)
        tpex_stocks = self.get_tpex_stocks(include_etf=include_etf)

        result = {
            "twse": twse_stocks,
            "tpex": tpex_stocks,
            "total": len(twse_stocks) + len(tpex_stocks),
            "fetch_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }

        if include_emerging:
            result["emerging"] = self.get_emerging_stocks()
            result["total"] += len(result["emerging"])

        return result

    def save_to_json(
        self,
        filepath: str | Path | None = None,
        format: str = "detailed",
    ) -> Path:
        """
        Save stock lists to JSON file.

        Args:
            filepath: Output file path
                - None (auto): uses default based on format
                - "main": data/tw_tickers.json (tickers only, for config)
                - "listed": data/tw_codes_listed.json (TWSE, for smart_money_screener)
                - "otc": data/tw_codes_otc.json (TPEx, for smart_money_screener)
                - "detailed": data/stock_list.json (full info)
            format: Output format
                - "tickers": List of ticker strings only
                - "detailed": Full info with name, industry, market

        Returns:
            Path to saved file
        """
        import json

        # Auto-determine filepath if not specified
        if filepath is None:
            filepath = Path("data/stock_list.json")

        # Ensure data directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Get all stocks
        twse_stocks = self.get_twse_stocks()
        tpex_stocks = self.get_tpex_stocks()

        if format == "tickers":
            # Simple list of tickers only
            all_tickers = sorted(
                [s["ticker"] for s in twse_stocks] + [s["ticker"] for s in tpex_stocks]
            )
            output_data = all_tickers
        elif format == "detailed":
            # Full info format
            output_data: dict = {
                "twse_stocks": twse_stocks,
                "tpex_stocks": tpex_stocks,
                "fetch_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "summary": {
                    "twse_count": len(twse_stocks),
                    "tpex_count": len(tpex_stocks),
                    "total_count": len(twse_stocks) + len(tpex_stocks),
                },
            }
        else:
            raise ValueError(f"Unknown format: {format}")

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        log.info(f"Stock list saved to {filepath}")
        return filepath

    def save_tickers_json(self, filepath: str | Path | None = None) -> Path:
        """
        Save tickers list to JSON (compatible with config.py default).

        Args:
            filepath: Output file path (default: data/tw_tickers.json)

        Returns:
            Path to saved file
        """
        if filepath is None:
            filepath = Path("data/tw_tickers.json")

        # Get all tickers from both markets (unique)
        twse_stocks = self.get_twse_stocks()
        tpex_stocks = self.get_tpex_stocks()

        # Combine and remove duplicates (in case of overlap)
        all_tickers = sorted(set(s["ticker"] for s in twse_stocks + tpex_stocks))

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        import json

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(all_tickers, f, ensure_ascii=False, indent=2)

        log.info(f"Stock tickers saved to {filepath}")
        return filepath

    def save_listed_json(self, filepath: str | Path | None = None) -> Path:
        """
        Save TWSE listed stocks to JSON (compatible with smart_money_screener).

        Args:
            filepath: Output file path (default: data/tw_codes_listed.json)

        Returns:
            Path to saved file
        """
        if filepath is None:
            filepath = Path("data/tw_codes_listed.json")

        # smart_money_screener expects list of tickers (unique)
        twse_stocks = self.get_twse_stocks()
        tickers = sorted(set(s["ticker"] for s in twse_stocks))

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        import json

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(tickers, f, ensure_ascii=False, indent=2)

        log.info(f"TWSE listed stocks saved to {filepath}")
        return filepath

    def save_otc_json(self, filepath: str | Path | None = None) -> Path:
        """
        Save TPEx OTC stocks to JSON (compatible with smart_money_screener).

        Args:
            filepath: Output file path (default: data/tw_codes_otc.json)

        Returns:
            Path to saved file
        """
        if filepath is None:
            filepath = Path("data/tw_codes_otc.json")

        # smart_money_screener expects list of tickers (unique)
        tpex_stocks = self.get_tpex_stocks()
        tickers = sorted(set(s["ticker"] for s in tpex_stocks))

        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)

        import json

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(tickers, f, ensure_ascii=False, indent=2)

        log.info(f"TPEx OTC stocks saved to {filepath}")
        return filepath

    def save_all_for_main_program(self) -> dict:
        """
        Save all files needed by the main program.

        Returns:
            Dict with file paths
        """
        files: dict = {}

        # 1. tw_tickers.json - all tickers for config.py
        files["tw_tickers"] = str(self.save_tickers_json())

        # 2. tw_codes_listed.json - TWSE stocks for smart_money_screener
        files["tw_codes_listed"] = str(self.save_listed_json())

        # 3. tw_codes_otc.json - OTC stocks for smart_money_screener
        files["tw_codes_otc"] = str(self.save_otc_json())

        # 4. stock_list.json - detailed info
        files["stock_list"] = str(self.save_to_json())

        return files

    def save_to_csv(
        self,
        filepath_twse: str | Path | None = None,
        filepath_tpex: str | Path | None = None,
    ) -> tuple["Path | None", "Path | None"]:
        """
        Save stock lists to CSV files.

        Args:
            filepath_twse: Output file for TWSE stocks (default: data/twse_stocks.csv)
            filepath_tpex: Output file for TPEx stocks (default: data/tpex_stocks.csv)

        Returns:
            Tuple of (twse_path, tpex_path)
        """
        twse_path: "Path | None" = None
        tpex_path: "Path | None" = None

        twse_stocks = self.get_twse_stocks()

        if twse_stocks:
            if filepath_twse is None:
                filepath_twse = Path("data/twse_stocks.csv")
            twse_path = Path(filepath_twse)
            twse_path.parent.mkdir(parents=True, exist_ok=True)
            df = pd.DataFrame(twse_stocks)
            df.to_csv(twse_path, index=False, encoding="utf-8")
            log.info(f"TWSE stock list saved to {twse_path}")

        tpex_stocks = self.get_tpex_stocks()

        if tpex_stocks:
            if filepath_tpex is None:
                filepath_tpex = Path("data/tpex_stocks.csv")
            tpex_path = Path(filepath_tpex)
            tpex_path.parent.mkdir(parents=True, exist_ok=True)
            df = pd.DataFrame(tpex_stocks)
            df.to_csv(tpex_path, index=False, encoding="utf-8")
            log.info(f"TPEx stock list saved to {tpex_path}")

        return twse_path, tpex_path

    def get_tickers_only(self, market: Literal["twse", "tpex", "all"] = "all") -> list[str]:
        """
        Get simple list of stock tickers (just the codes).

        Args:
            market: 'twse', 'tpex', or 'all'

        Returns:
            List of stock ticker strings
        """
        if market == "twse":
            return [s["ticker"] for s in self.get_twse_stocks()]
        elif market == "tpex":
            return [s["ticker"] for s in self.get_tpex_stocks()]
        else:
            twse = [s["ticker"] for s in self.get_twse_stocks()]
            tpex = [s["ticker"] for s in self.get_tpex_stocks()]
            return twse + tpex
