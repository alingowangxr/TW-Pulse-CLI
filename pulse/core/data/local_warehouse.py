import asyncio
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd

from pulse.core.config import settings
from pulse.core.models import OHLCV, StockData
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class LocalWarehouseFetcher:
    """Read stock data from a local SQLite warehouse."""

    def __init__(self, db_path: str | Path | None = None):
        configured_path = db_path or settings.data.local_warehouse_db or self._discover_db_path()
        self.db_path = Path(configured_path) if configured_path else None

    def _discover_db_path(self) -> Path | None:
        candidates = [
            settings.base_dir / "data" / "local_warehouse" / "tw_stock_warehouse.db",
            Path(r"D:\code\global-stock-data-warehouse\tw_stock_warehouse.db"),
        ]

        for candidate in candidates:
            if candidate.exists():
                return candidate
        return None

    @property
    def is_available(self) -> bool:
        return self.db_path is not None and self.db_path.exists()

    def _normalize_ticker(self, ticker: str) -> str:
        return ticker.upper().strip()

    def _clean_ticker(self, ticker: str) -> str:
        normalized = self._normalize_ticker(ticker)
        if normalized.endswith(".TW"):
            return normalized[:-3]
        if normalized.endswith(".TWO"):
            return normalized[:-4]
        return normalized

    def _candidate_symbols(self, ticker: str) -> list[str]:
        normalized = self._normalize_ticker(ticker)
        candidates: list[str] = []

        def add(symbol: str) -> None:
            if symbol and symbol not in candidates:
                candidates.append(symbol)

        add(normalized)
        if normalized.endswith(".TW") or normalized.endswith(".TWO"):
            add(self._clean_ticker(normalized))
        else:
            add(f"{normalized}.TW")
            add(f"{normalized}.TWO")

        return candidates

    def _period_to_days(self, period: str) -> int | None:
        mapping = {
            "1d": 1,
            "5d": 7,
            "1mo": 31,
            "3mo": 93,
            "6mo": 186,
            "1y": 365,
            "2y": 730,
            "5y": 1825,
        }
        period = period.lower().strip()
        if period == "max":
            return None
        return mapping.get(period, 365)

    def _resolve_date_range(
        self,
        period: str,
        start_date: str | None,
        end_date: str | None,
    ) -> tuple[str | None, str | None]:
        if end_date is None:
            end_date = datetime.now().strftime("%Y-%m-%d")
        if start_date is not None:
            return start_date, end_date

        days = self._period_to_days(period)
        if days is None:
            return None, end_date

        parsed_end = datetime.strptime(end_date, "%Y-%m-%d")
        start_date = (parsed_end - timedelta(days=days)).strftime("%Y-%m-%d")
        return start_date, end_date

    def _connect(self) -> sqlite3.Connection:
        if not self.is_available:
            raise FileNotFoundError("Local warehouse database is not available")
        assert self.db_path is not None
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _resolve_symbol_sync(self, ticker: str) -> str | None:
        if not self.is_available:
            return None

        candidates = self._candidate_symbols(ticker)
        try:
            with self._connect() as conn:
                cur = conn.cursor()
                for symbol in candidates:
                    cur.execute("SELECT symbol FROM stock_info WHERE symbol = ? LIMIT 1", (symbol,))
                    row = cur.fetchone()
                    if row:
                        return str(row["symbol"])

                for symbol in candidates:
                    cur.execute(
                        "SELECT symbol FROM stock_prices WHERE symbol = ? LIMIT 1",
                        (symbol,),
                    )
                    row = cur.fetchone()
                    if row:
                        return str(row["symbol"])
        except Exception as e:
            log.debug(f"Failed to resolve local warehouse symbol for {ticker}: {e}")

        return None

    def _fetch_stock_info_sync(self, symbol: str) -> dict[str, Any]:
        if not self.is_available:
            return {}

        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute(
                    """
                    SELECT symbol, name, sector, market, updated_at
                    FROM stock_info
                    WHERE symbol = ?
                    LIMIT 1
                    """,
                    (symbol,),
                )
                row = cur.fetchone()
                return dict(row) if row else {}
        except Exception as e:
            log.debug(f"Failed to fetch local stock info for {symbol}: {e}")
            return {}

    def get_status(self) -> dict[str, Any]:
        """Return a lightweight summary of the local warehouse."""
        if not self.is_available:
            return {
                "available": False,
                "db_path": None,
                "tables": [],
                "error": "local warehouse database not found",
            }

        try:
            with self._connect() as conn:
                cur = conn.cursor()
                cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
                tables = [row[0] for row in cur.fetchall()]

                status: dict[str, Any] = {
                    "available": True,
                    "db_path": str(self.db_path),
                    "tables": tables,
                }

                if "stock_info" in tables:
                    cur.execute("SELECT COUNT(*) FROM stock_info")
                    status["info_rows"] = int(cur.fetchone()[0])
                    cur.execute("SELECT DISTINCT market FROM stock_info ORDER BY market")
                    status["markets"] = [row[0] for row in cur.fetchall()]

                if "stock_prices" in tables:
                    cur.execute("SELECT COUNT(*) FROM stock_prices")
                    status["price_rows"] = int(cur.fetchone()[0])
                    cur.execute("SELECT COUNT(DISTINCT symbol) FROM stock_prices")
                    status["symbols"] = int(cur.fetchone()[0])
                    cur.execute("SELECT MIN(date), MAX(date) FROM stock_prices")
                    min_date, max_date = cur.fetchone()
                    status["date_range"] = {"min": min_date, "max": max_date}

                return status
        except Exception as e:
            log.debug(f"Failed to read local warehouse status: {e}")
            return {
                "available": False,
                "db_path": str(self.db_path),
                "tables": [],
                "error": str(e),
            }

    def _fetch_history_sync(
        self,
        ticker: str,
        period: str = "1y",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame | None:
        symbol = self._resolve_symbol_sync(ticker)
        if not symbol:
            return None

        resolved_start, resolved_end = self._resolve_date_range(period, start_date, end_date)

        sql = """
            SELECT date, symbol, open, high, low, close, volume
            FROM stock_prices
            WHERE symbol = ?
        """
        params: list[Any] = [symbol]
        if resolved_start and resolved_end:
            sql += " AND date BETWEEN ? AND ?"
            params.extend([resolved_start, resolved_end])
        sql += " ORDER BY date ASC"

        try:
            with self._connect() as conn:
                df = pd.read_sql_query(sql, conn, params=params)
        except Exception as e:
            log.debug(f"Failed to read local warehouse history for {ticker}: {e}")
            return None

        if df.empty:
            return None

        df.columns = [c.lower() for c in df.columns]
        df["date"] = pd.to_datetime(df["date"])
        return df

    def _fetch_stock_sync(
        self,
        ticker: str,
        period: str = "1y",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> StockData | None:
        df = self._fetch_history_sync(ticker, period=period, start_date=start_date, end_date=end_date)
        if df is None or df.empty:
            return None

        symbol = str(df.iloc[-1]["symbol"])
        info = self._fetch_stock_info_sync(symbol)

        history: list[OHLCV] = []
        for _, row in df.iterrows():
            try:
                history.append(
                    OHLCV(
                        date=pd.to_datetime(row["date"]).to_pydatetime(),
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=int(row["volume"]),
                    )
                )
            except Exception:
                continue

        if not history:
            return None

        latest = history[-1]
        previous = history[-2] if len(history) > 1 else latest
        current_price = latest.close
        previous_close = previous.close
        change = current_price - previous_close
        change_percent = (change / previous_close * 100) if previous_close else 0.0

        week_52_data = df.tail(252) if len(df) >= 252 else df
        week_52_high = float(week_52_data["high"].max()) if not week_52_data.empty else 0.0
        week_52_low = float(week_52_data["low"].min()) if not week_52_data.empty else 0.0
        avg_volume = int(df["volume"].tail(20).mean()) if not df["volume"].empty else 0

        return StockData(
            ticker=self._clean_ticker(symbol),
            name=info.get("name"),
            sector=info.get("sector"),
            industry=info.get("sector"),
            current_price=current_price,
            previous_close=previous_close,
            change=change,
            change_percent=change_percent,
            volume=latest.volume,
            avg_volume=avg_volume,
            day_low=latest.low,
            day_high=latest.high,
            week_52_low=week_52_low,
            week_52_high=week_52_high,
            history=history,
        )

    def _build_stock_from_history_sync(
        self,
        ticker: str,
        df: pd.DataFrame,
    ) -> StockData | None:
        if df is None or df.empty:
            return None

        local_df = df.copy()
        local_df.columns = [str(col).lower() for col in local_df.columns]
        if "symbol" in local_df.columns:
            symbol = str(local_df.iloc[-1]["symbol"])
        else:
            symbol = self._candidate_symbols(ticker)[0]

        info = self._fetch_stock_info_sync(symbol)

        history: list[OHLCV] = []
        for _, row in local_df.iterrows():
            try:
                history.append(
                    OHLCV(
                        date=pd.to_datetime(row["date"]).to_pydatetime(),
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=int(row["volume"]),
                    )
                )
            except Exception:
                continue

        if not history:
            return None

        latest = history[-1]
        previous = history[-2] if len(history) > 1 else latest
        current_price = latest.close
        previous_close = previous.close
        change = current_price - previous_close
        change_percent = (change / previous_close * 100) if previous_close else 0.0

        week_52_data = local_df.tail(252) if len(local_df) >= 252 else local_df
        week_52_high = float(week_52_data["high"].max()) if not week_52_data.empty else 0.0
        week_52_low = float(week_52_data["low"].min()) if not week_52_data.empty else 0.0
        avg_volume = int(local_df["volume"].tail(20).mean()) if not local_df["volume"].empty else 0

        return StockData(
            ticker=self._clean_ticker(symbol),
            name=info.get("name"),
            sector=info.get("sector"),
            industry=info.get("sector"),
            current_price=current_price,
            previous_close=previous_close,
            change=change,
            change_percent=change_percent,
            volume=latest.volume,
            avg_volume=avg_volume,
            day_low=latest.low,
            day_high=latest.high,
            week_52_low=week_52_low,
            week_52_high=week_52_high,
            history=history,
        )

    async def fetch_history(
        self,
        ticker: str,
        period: str = "1y",
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> pd.DataFrame | None:
        if not self.is_available:
            return None
        return await asyncio.to_thread(
            self._fetch_history_sync,
            ticker,
            period,
            start_date,
            end_date,
        )

    async def fetch_stock(
        self,
        ticker: str,
        period: str = "1y",
        start_date: str | None = None,
        end_date: str | None = None,
        history_df: pd.DataFrame | None = None,
    ) -> StockData | None:
        if not self.is_available:
            return None
        if history_df is not None and not history_df.empty:
            return await asyncio.to_thread(self._build_stock_from_history_sync, ticker, history_df)
        return await asyncio.to_thread(
            self._fetch_stock_sync,
            ticker,
            period,
            start_date,
            end_date,
        )
