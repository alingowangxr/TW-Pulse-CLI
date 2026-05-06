"""FinMind data fetcher for Taiwan stocks (primary data source)."""

from datetime import datetime, timedelta

import pandas as pd

from pulse.core.models import OHLCV, FundamentalData, StockData
from pulse.utils.logger import get_logger

log = get_logger(__name__)

# Try to import FinMind DataLoader
try:
    from FinMind.data import DataLoader

    FINMIND_AVAILABLE = True
except ImportError:
    FINMIND_AVAILABLE = False
    log.warning("FinMind SDK not installed. Run: pip install FinMind")


class FinMindFetcher:
    """Fetch stock data from FinMind API for Taiwan stocks."""

    # Taiwan market indices mapping
    INDEX_MAPPING = {
        "TAIEX": ("TAIEX", "Taiwan Weighted Index"),
        "TWII": ("TAIEX", "Taiwan Weighted Index"),
        "^TWII": ("TAIEX", "Taiwan Weighted Index"),
        "TPEX": ("TPEx", "Taiwan OTC Index"),
        "OTC": ("TPEx", "Taiwan OTC Index"),
    }

    # Quota status tracking
    _quota_exceeded: bool = False
    _quota_error_message: str = ""
    _request_count: int = 0
    _quota_limit: int = 1000  # Default quota limit per day
    _last_request_time: datetime | None = None

    @classmethod
    def is_quota_exceeded(cls) -> bool:
        """Check if FinMind quota has been exceeded."""
        return cls._quota_exceeded

    @classmethod
    def get_quota_status(cls) -> dict:
        """Get current quota status.

        Returns:
            Dictionary with quota information
        """
        return {
            "exceeded": cls._quota_exceeded,
            "request_count": cls._request_count,
            "quota_limit": cls._quota_limit,
            "remaining": max(0, cls._quota_limit - cls._request_count),
            "error_message": cls._quota_error_message,
        }

    @classmethod
    def reset_quota_status(cls) -> None:
        """Reset quota status (for testing or manual reset)."""
        cls._quota_exceeded = False
        cls._quota_error_message = ""
        cls._request_count = 0

    @classmethod
    def set_quota_exceeded(cls, message: str = "FinMind API quota exceeded") -> None:
        """Mark FinMind quota as exceeded."""
        cls._quota_exceeded = True
        cls._quota_error_message = message
        log.warning(message)

    @classmethod
    def increment_request_count(cls) -> None:
        """Increment the request counter for quota tracking."""
        cls._request_count += 1
        cls._last_request_time = datetime.now()

    @classmethod
    def set_quota_limit(cls, limit: int) -> None:
        """Set the daily quota limit.

        Args:
            limit: Maximum number of requests per day
        """
        cls._quota_limit = limit
        log.info(f"FinMind quota limit set to {limit} requests/day")

    def __init__(self, token: str = ""):
        """
        Initialize FinMind fetcher.

        Args:
            token: FinMind API token (optional, for higher rate limits)
        """
        self.token = token
        self._dl: DataLoader | None = None
        self._stock_info_cache: pd.DataFrame | None = None

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

    def _format_stock_id(self, ticker: str) -> str:
        """
        Format ticker to FinMind stock_id format.

        Args:
            ticker: Stock ticker (e.g., "2330", "2330.TW")

        Returns:
            Formatted stock_id (e.g., "2330")
        """
        ticker = ticker.upper().strip()
        # Remove .TW or .TWO suffix if present
        if ticker.endswith(".TW"):
            ticker = ticker[:-3]
        elif ticker.endswith(".TWO"):
            ticker = ticker[:-4]
        return ticker

    def _get_stock_info(self, stock_id: str) -> dict:
        """
        Get stock info from cache or API.

        Args:
            stock_id: Stock ID (e.g., "2330")

        Returns:
            Dict with stock_name, industry_category, type
        """
        try:
            if self._stock_info_cache is None:
                self._stock_info_cache = self.dl.taiwan_stock_info()

            if self._stock_info_cache is not None and not self._stock_info_cache.empty:
                match = self._stock_info_cache[self._stock_info_cache["stock_id"] == stock_id]
                if not match.empty:
                    row = match.iloc[0]
                    return {
                        "name": row.get("stock_name", ""),
                        "industry": row.get("industry_category", ""),
                        "type": row.get("type", ""),
                    }
        except Exception as e:
            log.debug(f"Failed to get stock info for {stock_id}: {e}")

        return {"name": None, "industry": None, "type": None}

    def _check_quota_error(self, error: Exception) -> bool:
        """
        Check if an error is a quota-related error.

        Args:
            error: The exception to check

        Returns:
            True if this is a quota error, False otherwise
        """
        error_str = str(error).lower()

        # Common quota error indicators
        quota_indicators = [
            "quota",
            "rate limit",
            "too many requests",
            "429",
            "請求次數",
            "配額",
            "api limit",
            "exceeded",
            "limit exceeded",
        ]

        return any(indicator in error_str for indicator in quota_indicators)

    @staticmethod
    def _safe_float(value) -> float | None:
        """Convert a value to float when possible."""
        if value is None or value == "":
            return None
        try:
            if pd.isna(value):
                return None
        except Exception:
            pass
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _safe_ratio(cls, numerator, denominator, multiplier: float = 1.0) -> float | None:
        """Safely compute a ratio."""
        numerator_value = cls._safe_float(numerator)
        denominator_value = cls._safe_float(denominator)
        if numerator_value is None or denominator_value in (None, 0):
            return None
        return numerator_value / denominator_value * multiplier

    @staticmethod
    def _normalize_metric_name(name: str) -> str:
        """Normalize statement metric names for fuzzy matching."""
        if not name:
            return ""
        return (
            str(name)
            .strip()
            .lower()
            .replace(" ", "")
            .replace("_", "")
            .replace("-", "")
            .replace("（", "(")
            .replace("）", ")")
        )

    def _get_latest_statement_snapshot(self, df: pd.DataFrame | None) -> dict[str, float]:
        """Collapse FinMind long-form statements into a latest-period metric mapping."""
        if df is None or df.empty:
            return {}

        local_df = df.copy()
        date_col = None
        for candidate in ["date", "release_date"]:
            if candidate in local_df.columns:
                date_col = candidate
                break

        if date_col is not None:
            latest_date = local_df[date_col].astype(str).max()
            local_df = local_df[local_df[date_col].astype(str) == latest_date]

        metric_col = next((col for col in ["type", "account", "item"] if col in local_df.columns), None)
        value_col = next((col for col in ["value", "amount"] if col in local_df.columns), None)
        if metric_col is None or value_col is None:
            return {}

        snapshot: dict[str, float] = {}
        for _, row in local_df.iterrows():
            metric_name = self._normalize_metric_name(row.get(metric_col, ""))
            metric_value = self._safe_float(row.get(value_col))
            if metric_name and metric_value is not None:
                snapshot[metric_name] = metric_value
        return snapshot

    def _find_metric_value(
        self,
        snapshot: dict[str, float],
        include_keywords: list[str],
        exclude_keywords: list[str] | None = None,
    ) -> float | None:
        """Find the first metric whose normalized name matches the keyword filters."""
        exclude_keywords = exclude_keywords or []
        normalized_include = [self._normalize_metric_name(k) for k in include_keywords]
        normalized_exclude = [self._normalize_metric_name(k) for k in exclude_keywords]

        for metric_name, value in snapshot.items():
            if all(keyword in metric_name for keyword in normalized_include) and not any(
                keyword in metric_name for keyword in normalized_exclude
            ):
                return value
        return None

    def _extract_statement_metrics(self, df: pd.DataFrame | None, metric_aliases: list[list[str]]) -> float | None:
        """Extract a metric from FinMind long-form statements using keyword aliases."""
        snapshot = self._get_latest_statement_snapshot(df)
        if not snapshot:
            return None

        for alias in metric_aliases:
            value = self._find_metric_value(snapshot, alias)
            if value is not None:
                return value
        return None

    def _extract_latest_eps(self, financial_df: pd.DataFrame | None) -> float | None:
        """Extract the most recent EPS value from FinMind financial statements."""
        if financial_df is None or financial_df.empty:
            return None

        local_df = financial_df.copy()
        metric_col = "type" if "type" in local_df.columns else None
        value_col = "value" if "value" in local_df.columns else None
        date_col = "date" if "date" in local_df.columns else None
        if metric_col is None or value_col is None:
            return None

        if date_col is not None:
            local_df = local_df.sort_values(date_col)

        eps_rows = local_df[
            local_df[metric_col]
            .astype(str)
            .str.contains("eps|每股盈餘", case=False, regex=True, na=False)
        ]
        if eps_rows.empty:
            return None

        return self._safe_float(eps_rows.iloc[-1].get(value_col))

    def _extract_earnings_growth(self, financial_df: pd.DataFrame | None) -> float | None:
        """Estimate earnings growth from the last two EPS observations."""
        if financial_df is None or financial_df.empty or "type" not in financial_df.columns:
            return None

        eps_rows = financial_df[
            financial_df["type"].astype(str).str.contains("eps|每股盈餘", case=False, regex=True, na=False)
        ].copy()
        if eps_rows.empty or "value" not in eps_rows.columns:
            return None

        if "date" in eps_rows.columns:
            eps_rows = eps_rows.sort_values("date")

        eps_values = [self._safe_float(v) for v in eps_rows["value"].tolist()]
        eps_values = [v for v in eps_values if v is not None]
        if len(eps_values) < 2 or eps_values[-2] == 0:
            return None

        return (eps_values[-1] - eps_values[-2]) / abs(eps_values[-2]) * 100

    async def fetch_stock(
        self,
        ticker: str,
        start_date: str,
        end_date: str = "",
    ) -> StockData | None:
        """
        Fetch stock data for a ticker from FinMind.

        Args:
            ticker: Stock ticker (e.g., "2330")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today

        Returns:
            StockData object or None if failed
        """
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        formatted_ticker = self._format_stock_id(ticker)

        # Check if quota was exceeded previously
        if self.__class__._quota_exceeded:
            log.debug(f"Skipping FinMind fetch for {ticker} - quota exceeded")
            return None

        try:
            log.debug(f"Fetching {formatted_ticker} from FinMind...")
            self.__class__.increment_request_count()

            # Get daily price data
            df = self.dl.taiwan_stock_daily(
                stock_id=formatted_ticker,
                start_date=start_date,
                end_date=end_date,
            )

            if df is None or df.empty:
                log.warning(f"No data found for {ticker} from FinMind")
                return None

            # Get stock info
            stock_info = self._get_stock_info(formatted_ticker)

            # Convert to OHLCV list using vectorized operations
            records = df.to_dict("records")
            history = [
                OHLCV(
                    date=pd.to_datetime(r["date"]),
                    open=float(r.get("open", 0) or 0),
                    high=float(r.get("max", r.get("high", 0)) or 0),
                    low=float(r.get("min", r.get("low", 0)) or 0),
                    close=float(r.get("close", 0) or 0),
                    volume=int(r.get("Trading_Volume", 0) or 0),
                )
                for r in records
            ]

            if not history:
                log.warning(f"No valid OHLCV data for {ticker}")
                return None

            # Sort by date
            history.sort(key=lambda x: x.date)

            # Get latest and previous data
            latest = history[-1]
            prev = history[-2] if len(history) > 1 else latest

            current_price = latest.close
            previous_close = prev.close
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0.0

            # Calculate 52-week high/low (approximately 252 trading days)
            week_52_data = history[-252:] if len(history) >= 252 else history
            week_52_high = max(h.high for h in week_52_data) if week_52_data else 0.0
            week_52_low = min(h.low for h in week_52_data) if week_52_data else 0.0

            # Calculate average volume (20-day)
            recent_volumes = [h.volume for h in history[-20:]]
            avg_volume = int(sum(recent_volumes) / len(recent_volumes)) if recent_volumes else 0

            return StockData(
                ticker=formatted_ticker,
                name=stock_info.get("name"),
                sector=stock_info.get("industry"),
                industry=stock_info.get("industry"),
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
                market_cap=None,  # FinMind doesn't provide this directly
                shares_outstanding=None,
                history=history,
            )

        except Exception as e:
            # Check if this is a quota-related error
            if self._check_quota_error(e):
                self.__class__.set_quota_exceeded(f"FinMind quota exceeded: {e}")
                log.warning(f"FinMind quota exceeded for {ticker}, will fallback to yfinance")
            else:
                log.error(f"Error fetching {ticker} from FinMind: {e}")
            return None

    async def fetch_fundamentals(
        self,
        ticker: str,
        start_date: str,
        end_date: str = "",
    ) -> FundamentalData | None:
        """
        Fetch fundamental data for a ticker from FinMind.

        Args:
            ticker: Stock ticker (e.g., "2330")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today

        Returns:
            FundamentalData object or None if failed
        """
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        formatted_ticker = self._format_stock_id(ticker)

        try:
            log.debug(f"Fetching fundamentals for {formatted_ticker} from FinMind...")

            # Get PER/PBR data
            per_pbr_df = self.dl.taiwan_stock_per_pbr(
                stock_id=formatted_ticker,
                start_date=start_date,
                end_date=end_date,
            )

            pe_ratio = None
            pb_ratio = None
            dividend_yield = None

            if per_pbr_df is not None and not per_pbr_df.empty:
                # Get latest values
                latest = per_pbr_df.iloc[-1]
                pe_ratio = float(latest.get("PER", 0)) if latest.get("PER") else None
                pb_ratio = float(latest.get("PBR", 0)) if latest.get("PBR") else None
                dividend_yield = (
                    float(latest.get("dividend_yield", 0)) if latest.get("dividend_yield") else None
                )

            # Try to get financial statement data for more metrics
            roe = None
            roa = None
            eps = None
            revenue_growth = None
            earnings_growth = None
            npm = None
            opm = None
            gpm = None
            bvps = None
            dps = None
            debt_to_equity = None
            current_ratio = None
            quick_ratio = None
            payout_ratio = None
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            quarter_start = f"{max(2000, start_dt.year - 2)}-Q1"
            quarter_end = f"{datetime.now().year}-Q4"

            try:
                # Use a wider window so we can compute recent trends and ratios.
                financial_df = self.dl.taiwan_stock_financial_statement(
                    stock_id=formatted_ticker,
                    start_date=quarter_start,
                    end_date=quarter_end,
                )

                if financial_df is not None and not financial_df.empty:
                    eps = self._extract_latest_eps(financial_df)
                    earnings_growth = self._extract_earnings_growth(financial_df)
                    roe = self._extract_statement_metrics(
                        financial_df,
                        [["roe"], ["權益報酬率"], ["股東權益報酬率"]],
                    )
                    roa = self._extract_statement_metrics(
                        financial_df,
                        [["roa"], ["資產報酬率"]],
                    )
                    npm = self._extract_statement_metrics(
                        financial_df,
                        [["net", "profit", "margin"], ["稅後", "淨利率"], ["淨利率"]],
                    )
                    opm = self._extract_statement_metrics(
                        financial_df,
                        [["operating", "margin"], ["營業利益率"], ["營業利率"]],
                    )
                    gpm = self._extract_statement_metrics(
                        financial_df,
                        [["gross", "margin"], ["毛利率"]],
                    )

            except Exception as e:
                log.debug(f"Failed to get financial statements for {ticker}: {e}")

            try:
                balance_df = self.dl.taiwan_stock_balance_sheet(
                    stock_id=formatted_ticker,
                    start_date=quarter_start,
                    end_date=quarter_end,
                )
                balance_snapshot = self._get_latest_statement_snapshot(balance_df)

                current_assets = self._find_metric_value(
                    balance_snapshot,
                    ["current", "assets"],
                ) or self._find_metric_value(balance_snapshot, ["流動資產"])
                current_liabilities = self._find_metric_value(
                    balance_snapshot,
                    ["current", "liabilities"],
                ) or self._find_metric_value(balance_snapshot, ["流動負債"])
                inventory = self._find_metric_value(balance_snapshot, ["inventory"]) or self._find_metric_value(
                    balance_snapshot, ["存貨"]
                )
                total_liabilities = self._find_metric_value(
                    balance_snapshot,
                    ["total", "liabilities"],
                    exclude_keywords=["current"],
                ) or self._find_metric_value(balance_snapshot, ["負債總額"])
                total_equity = self._find_metric_value(
                    balance_snapshot,
                    ["total", "equity"],
                ) or self._find_metric_value(balance_snapshot, ["權益總額"]) or self._find_metric_value(
                    balance_snapshot, ["股東權益總額"]
                )
                book_value_per_share = self._find_metric_value(
                    balance_snapshot,
                    ["book", "value", "per", "share"],
                ) or self._find_metric_value(balance_snapshot, ["每股", "淨值"])

                current_ratio = self._safe_ratio(current_assets, current_liabilities)
                if current_ratio is not None:
                    current_ratio = round(current_ratio, 4)

                if current_assets is not None and current_liabilities not in (None, 0):
                    quick_assets = current_assets - (inventory or 0.0)
                    quick_ratio = self._safe_ratio(quick_assets, current_liabilities)
                    if quick_ratio is not None:
                        quick_ratio = round(quick_ratio, 4)

                debt_to_equity = self._safe_ratio(total_liabilities, total_equity)
                if debt_to_equity is not None:
                    debt_to_equity = round(debt_to_equity, 4)

                bvps = self._safe_float(book_value_per_share)
            except Exception as e:
                log.debug(f"Failed to get balance sheet data for {ticker}: {e}")

            try:
                # Fetch cash flow to keep the FinMind dataset coverage aligned with the
                # documented fundamentals package, even if we do not expose a direct field yet.
                self.dl.taiwan_stock_cash_flow_statement(
                    stock_id=formatted_ticker,
                    start_date=quarter_start,
                    end_date=quarter_end,
                )
            except Exception as e:
                log.debug(f"Failed to get cash flow data for {ticker}: {e}")

            try:
                dividend_df = self.dl.taiwan_stock_dividend_result(
                    stock_id=formatted_ticker,
                    start_date=(datetime.now() - timedelta(days=365 * 5)).strftime("%Y-%m-%d"),
                    end_date=end_date,
                )
                if dividend_df is not None and not dividend_df.empty:
                    sort_columns = [col for col in ["year", "season"] if col in dividend_df.columns]
                    if sort_columns:
                        dividend_df = dividend_df.sort_values(sort_columns)
                    latest_dividend = dividend_df.iloc[-1]
                    cash_dividend = self._safe_float(latest_dividend.get("cash_dividend")) or 0.0
                    stock_dividend = self._safe_float(latest_dividend.get("stock_dividend")) or 0.0
                    dps = cash_dividend + stock_dividend
                    dividend_eps = self._safe_float(latest_dividend.get("eps"))
                    if payout_ratio is None:
                        payout_ratio = self._safe_ratio(cash_dividend, dividend_eps, multiplier=100)
            except Exception as e:
                log.debug(f"Failed to get dividend data for {ticker}: {e}")

            try:
                revenue_df = self.dl.taiwan_stock_month_revenue(
                    stock_id=formatted_ticker,
                    start_date=(datetime.now() - timedelta(days=365 * 2)).strftime("%Y-%m-%d"),
                    end_date=end_date,
                )
                if revenue_df is not None and not revenue_df.empty:
                    local_revenue_df = revenue_df.copy()
                    sort_columns = [
                        col
                        for col in ["date", "revenue_year", "revenue_month"]
                        if col in local_revenue_df.columns
                    ]
                    if sort_columns:
                        local_revenue_df = local_revenue_df.sort_values(sort_columns)

                    revenue_col = next(
                        (
                            col
                            for col in ["revenue", "month_revenue", "monthly_revenue"]
                            if col in local_revenue_df.columns
                        ),
                        None,
                    )
                    if revenue_col:
                        revenues = [
                            self._safe_float(v) for v in local_revenue_df[revenue_col].tolist()
                        ]
                        revenues = [v for v in revenues if v is not None]
                        if len(revenues) >= 13 and revenues[-13] != 0:
                            revenue_growth = (revenues[-1] - revenues[-13]) / abs(revenues[-13]) * 100
                        elif len(revenues) >= 2 and revenues[-2] != 0:
                            revenue_growth = (revenues[-1] - revenues[-2]) / abs(revenues[-2]) * 100
            except Exception as e:
                log.debug(f"Failed to get monthly revenue for {ticker}: {e}")

            return FundamentalData(
                ticker=formatted_ticker,
                pe_ratio=pe_ratio,
                pb_ratio=pb_ratio,
                ps_ratio=None,  # Not available from FinMind
                peg_ratio=None,
                ev_ebitda=None,
                roe=roe,
                roa=roa,
                npm=npm,
                opm=opm,
                gpm=gpm,
                eps=eps,
                bvps=bvps,
                dps=dps,
                revenue_growth=revenue_growth,
                earnings_growth=earnings_growth,
                debt_to_equity=debt_to_equity,
                current_ratio=current_ratio,
                quick_ratio=quick_ratio,
                dividend_yield=dividend_yield,
                payout_ratio=payout_ratio,
                market_cap=None,
                enterprise_value=None,
            )

        except Exception as e:
            log.error(f"Error fetching fundamentals for {ticker} from FinMind: {e}")
            return None

    async def fetch_multiple(
        self,
        tickers: list[str],
        start_date: str,
        end_date: str = "",
    ) -> list[StockData]:
        """
        Fetch data for multiple tickers from FinMind.

        Args:
            tickers: List of stock tickers
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today

        Returns:
            List of StockData objects
        """
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        results: list[StockData] = []

        # Format all tickers
        formatted_tickers = [self._format_stock_id(t) for t in tickers]

        try:
            log.debug(f"Fetching {len(formatted_tickers)} stocks from FinMind...")

            # FinMind supports batch fetching with stock_id_list
            df = self.dl.taiwan_stock_daily(
                stock_id="",
                start_date=start_date,
                end_date=end_date,
                stock_id_list=formatted_tickers,
            )

            if df is None or df.empty:
                log.warning("No data returned from FinMind batch fetch")
                # Fallback to individual fetching
                for ticker in tickers:
                    data = await self.fetch_stock(ticker, start_date, end_date)
                    if data:
                        results.append(data)
                return results

            # Group by stock_id and process each
            for stock_id in df["stock_id"].unique():
                stock_df = df[df["stock_id"] == stock_id]
                stock_info = self._get_stock_info(stock_id)

                # Convert to OHLCV list
                history: list[OHLCV] = []
                for _, row in stock_df.iterrows():
                    try:
                        ohlcv = OHLCV(
                            date=pd.to_datetime(row["date"]),
                            open=float(row.get("open", 0)),
                            high=float(row.get("max", 0)),
                            low=float(row.get("min", 0)),
                            close=float(row.get("close", 0)),
                            volume=int(row.get("Trading_Volume", 0)),
                        )
                        history.append(ohlcv)
                    except Exception:
                        continue

                if not history:
                    continue

                history.sort(key=lambda x: x.date)

                latest = history[-1]
                prev = history[-2] if len(history) > 1 else latest

                current_price = latest.close
                previous_close = prev.close
                change = current_price - previous_close
                change_percent = (change / previous_close * 100) if previous_close else 0.0

                week_52_data = history[-252:] if len(history) >= 252 else history
                week_52_high = max(h.high for h in week_52_data) if week_52_data else 0.0
                week_52_low = min(h.low for h in week_52_data) if week_52_data else 0.0

                recent_volumes = [h.volume for h in history[-20:]]
                avg_volume = int(sum(recent_volumes) / len(recent_volumes)) if recent_volumes else 0

                stock_data = StockData(
                    ticker=stock_id,
                    name=stock_info.get("name"),
                    sector=stock_info.get("industry"),
                    industry=stock_info.get("industry"),
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
                    market_cap=None,
                    shares_outstanding=None,
                    history=history,
                )
                results.append(stock_data)

        except Exception as e:
            log.error(f"Error in batch fetch from FinMind: {e}")
            # Fallback to individual fetching
            for ticker in tickers:
                data = await self.fetch_stock(ticker, start_date, end_date)
                if data:
                    results.append(data)

        return results

    async def fetch_history(
        self,
        ticker: str,
        start_date: str,
        end_date: str = "",
    ) -> pd.DataFrame | None:
        """
        Fetch historical data as DataFrame from FinMind.

        Args:
            ticker: Stock ticker (e.g., "2330")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today

        Returns:
            DataFrame with OHLCV data (columns: open, high, low, close, volume)
        """
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        formatted_ticker = self._format_stock_id(ticker)

        try:
            log.debug(f"Fetching history for {formatted_ticker} from FinMind...")

            df = self.dl.taiwan_stock_daily(
                stock_id=formatted_ticker,
                start_date=start_date,
                end_date=end_date,
            )

            if df is None or df.empty:
                log.warning(f"No history data found for {ticker}")
                return None

            # Rename columns to standard OHLCV format
            df = df.rename(
                columns={
                    "max": "high",
                    "min": "low",
                    "Trading_Volume": "volume",
                }
            )

            # Ensure required columns exist
            required_cols = ["date", "open", "high", "low", "close", "volume"]
            for col in required_cols:
                if col not in df.columns:
                    log.warning(f"Missing column {col} in FinMind data")
                    return None

            # Set date as index
            df["date"] = pd.to_datetime(df["date"])
            df = df.set_index("date")

            # Select only OHLCV columns and ensure lowercase
            df = df[["open", "high", "low", "close", "volume"]]
            df.columns = df.columns.str.lower()

            # Sort by date
            df = df.sort_index()

            return df

        except Exception as e:
            log.error(f"Error fetching history for {ticker} from FinMind: {e}")
            return None

    async def fetch_index(
        self,
        index_name: str,
        start_date: str,
        end_date: str = "",
    ) -> StockData | None:
        """
        Fetch market index data from FinMind.

        Args:
            index_name: Index name (TAIEX, TPEX, ^TWII)
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today

        Returns:
            StockData object with index data, or None if failed
        """
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        index_name = index_name.upper().strip()

        # Map index name to FinMind index_id
        if index_name in self.INDEX_MAPPING:
            finmind_index_id, display_name = self.INDEX_MAPPING[index_name]
        else:
            log.warning(f"Unknown index: {index_name}")
            return None

        try:
            log.debug(f"Fetching index {finmind_index_id} from FinMind...")

            # Get index data
            df = self.dl.taiwan_stock_total_return_index(
                index_id=finmind_index_id,
                start_date=start_date,
                end_date=end_date,
            )

            if df is None or df.empty:
                log.warning(f"No data found for index {index_name}")
                return None

            # Convert to OHLCV list (index only has price, not full OHLCV)
            history: list[OHLCV] = []
            for _, row in df.iterrows():
                try:
                    price = float(row.get("price", 0))
                    ohlcv = OHLCV(
                        date=pd.to_datetime(row["date"]),
                        open=price,
                        high=price,
                        low=price,
                        close=price,
                        volume=0,  # Index doesn't have volume
                    )
                    history.append(ohlcv)
                except Exception:
                    continue

            if not history:
                log.warning(f"No valid data for index {index_name}")
                return None

            # Sort by date
            history.sort(key=lambda x: x.date)

            latest = history[-1]
            prev = history[-2] if len(history) > 1 else latest

            current_price = latest.close
            previous_close = prev.close
            change = current_price - previous_close
            change_percent = (change / previous_close * 100) if previous_close else 0.0

            week_52_data = history[-252:] if len(history) >= 252 else history
            week_52_high = max(h.high for h in week_52_data) if week_52_data else 0.0
            week_52_low = min(h.low for h in week_52_data) if week_52_data else 0.0

            return StockData(
                ticker=index_name,
                name=display_name,
                sector="Index",
                industry="Market Index",
                current_price=current_price,
                previous_close=previous_close,
                change=change,
                change_percent=change_percent,
                volume=0,
                avg_volume=0,
                day_low=latest.low,
                day_high=latest.high,
                week_52_low=week_52_low,
                week_52_high=week_52_high,
                market_cap=None,
                shares_outstanding=None,
                history=history,
            )

        except Exception as e:
            log.error(f"Error fetching index {index_name} from FinMind: {e}")
            return None

    async def fetch_institutional_investors(
        self,
        ticker: str,
        start_date: str,
        end_date: str = "",
    ) -> pd.DataFrame | None:
        """
        Fetch institutional investor data for a ticker from FinMind.

        Args:
            ticker: Stock ticker (e.g., "2330")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today

        Returns:
            DataFrame with institutional investor data or None if failed.
            Columns: date, stock_id, name, buy, sell
            Names include: Foreign_Investor, Investment_Trust, Dealer_self, Dealer_Hedging
        """
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        formatted_ticker = self._format_stock_id(ticker)

        try:
            log.debug(
                f"Fetching institutional investor data for {formatted_ticker} from FinMind..."
            )

            df = self.dl.taiwan_stock_institutional_investors(
                stock_id=formatted_ticker,
                start_date=start_date,
                end_date=end_date,
            )

            if df is None or df.empty:
                log.warning(f"No institutional investor data found for {ticker}")
                return None

            return df

        except KeyError as e:
            if str(e) == "'data'":
                # FinMind API quota exceeded
                error_msg = (
                    f"FinMind API quota exceeded. "
                    f"法人買賣超數據查詢已達每日上限。"
                    f"請等待明日配額重置，或前往 https://finmindtrade.com/ 取得 API Token。"
                )
                log.error(error_msg)
                FinMindFetcher.set_quota_exceeded(error_msg)
                return None
            else:
                log.error(
                    f"Error fetching institutional investor data for {ticker} from FinMind: {e}"
                )
                return None
        except Exception as e:
            log.error(f"Error fetching institutional investor data for {ticker} from FinMind: {e}")
            return None

    async def fetch_margin_trading(
        self,
        ticker: str,
        start_date: str,
        end_date: str = "",
    ) -> pd.DataFrame | None:
        """
        Fetch margin trading (融资融券) data for a ticker from FinMind.

        Args:
            ticker: Stock ticker (e.g., "2330")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today

        Returns:
            DataFrame with margin trading data or None if failed.
        """
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        formatted_ticker = self._format_stock_id(ticker)

        try:
            log.debug(f"Fetching margin trading data for {formatted_ticker} from FinMind...")

            df = self.dl.taiwan_stock_margin_purchase_short_sale(
                stock_id=formatted_ticker,
                start_date=start_date,
                end_date=end_date,
            )

            if df is None or df.empty:
                log.warning(f"No margin trading data found for {ticker}")
                return None

            return df

        except Exception as e:
            log.error(f"Error fetching margin trading data for {ticker} from FinMind: {e}")
            return None

    async def fetch_foreign_shareholding(
        self,
        ticker: str,
        start_date: str,
        end_date: str = "",
    ) -> pd.DataFrame | None:
        """
        Fetch foreign investor shareholding data for a ticker from FinMind.

        Args:
            ticker: Stock ticker (e.g., "2330")
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today

        Returns:
            DataFrame with foreign shareholding data or None if failed.
        """
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        formatted_ticker = self._format_stock_id(ticker)

        try:
            log.debug(f"Fetching foreign shareholding data for {formatted_ticker} from FinMind...")

            df = self.dl.taiwan_stock_shareholding(
                stock_id=formatted_ticker,
                start_date=start_date,
                end_date=end_date,
            )

            if df is None or df.empty:
                log.warning(f"No foreign shareholding data found for {ticker}")
                return None

            return df

        except Exception as e:
            log.error(f"Error fetching foreign shareholding data for {ticker} from FinMind: {e}")
            return None

    async def fetch_financial_statements(
        self,
        ticker: str,
        year: int | None = None,
        quarter: int | None = None,
    ) -> dict | None:
        """
        Fetch detailed financial statement data for a ticker from FinMind.

        Args:
            ticker: Stock ticker (e.g., "2330")
            year: Financial year (defaults to latest available)
            quarter: Financial quarter (1-4, defaults to latest)

        Returns:
            Dict with income statement, balance sheet, and cash flow data
            or None if failed.
        """
        formatted_ticker = self._format_stock_id(ticker)

        try:
            log.debug(f"Fetching financial statements for {formatted_ticker} from FinMind...")

            # Determine date range
            if year is None:
                year = datetime.now().year - 1  # Use last completed year
            if quarter is None:
                quarter = 4  # Use Q4 by default

            start_date = f"{year}-Q1"
            end_date = f"{year}-Q{quarter}"

            # Get income statement
            income_df = self.dl.taiwan_stock_income_statement(
                stock_id=formatted_ticker,
                start_date=start_date,
                end_date=end_date,
            )

            # Get balance sheet
            balance_df = self.dl.taiwan_stock_balance_sheet(
                stock_id=formatted_ticker,
                start_date=start_date,
                end_date=end_date,
            )

            # Get cash flow
            cashflow_df = self.dl.taiwan_stock_cash_flow_statement(
                stock_id=formatted_ticker,
                start_date=start_date,
                end_date=end_date,
            )

            result = {
                "ticker": formatted_ticker,
                "year": year,
                "quarter": quarter,
                "income_statement": income_df.to_dict("records")
                if income_df is not None and not income_df.empty
                else [],
                "balance_sheet": balance_df.to_dict("records")
                if balance_df is not None and not balance_df.empty
                else [],
                "cash_flow": cashflow_df.to_dict("records")
                if cashflow_df is not None and not cashflow_df.empty
                else [],
            }

            return (
                result
                if result["income_statement"] or result["balance_sheet"] or result["cash_flow"]
                else None
            )

        except Exception as e:
            log.error(f"Error fetching financial statements for {ticker} from FinMind: {e}")
            return None

    async def fetch_dividend_info(
        self,
        ticker: str,
        years: int = 5,
    ) -> list[dict] | None:
        """
        Fetch dividend history for a ticker from FinMind.

        Args:
            ticker: Stock ticker (e.g., "2330")
            years: Number of years of dividend history (default 5)

        Returns:
            List of dividend records or None if failed.
        """
        formatted_ticker = self._format_stock_id(ticker)

        try:
            log.debug(f"Fetching dividend info for {formatted_ticker} from FinMind...")

            # Calculate date range
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_year = datetime.now().year - years
            start_date = f"{start_year}-01-01"

            df = self.dl.taiwan_stock_dividend_result(
                stock_id=formatted_ticker,
                start_date=start_date,
                end_date=end_date,
            )

            if df is None or df.empty:
                log.warning(f"No dividend data found for {ticker}")
                return None

            # Convert to list of dicts
            dividends = []
            for _, row in df.iterrows():
                dividends.append(
                    {
                        "ticker": formatted_ticker,
                        "year": row.get("year", ""),
                        "season": row.get("season", ""),
                        "cash_dividend": row.get("cash_dividend", 0),
                        "stock_dividend": row.get("stock_dividend", 0),
                        "ex_dividend_date": row.get("ex_dividend_date", ""),
                        "payment_date": row.get("payment_date", ""),
                        "earnings_per_share": row.get("eps", 0),
                    }
                )

            return dividends

        except Exception as e:
            log.error(f"Error fetching dividend info for {ticker} from FinMind: {e}")
            return None

    async def fetch_company_info(
        self,
        ticker: str,
    ) -> dict | None:
        """
        Fetch company profile information from FinMind.

        Args:
            ticker: Stock ticker (e.g., "2330")

        Returns:
            Dict with company info (name, industry, address, website, etc.)
            or None if failed.
        """
        formatted_ticker = self._format_stock_id(ticker)

        try:
            log.debug(f"Fetching company info for {formatted_ticker} from FinMind...")

            # Get basic info
            stock_info = self._get_stock_info(formatted_ticker)

            # Try to get more detailed info from Taiwan Stock Info dataset
            try:
                info_df = self.dl.taiwan_stock_info()
                if info_df is not None and not info_df.empty:
                    match = info_df[info_df["stock_id"] == formatted_ticker]
                    if not match.empty:
                        row = match.iloc[0]
                        stock_info.update(
                            {
                                "listing_date": row.get("listing_date", None),
                                "delisting_date": row.get("delisting_date", None),
                                "chairman": row.get("chairman", None),
                                "manager": row.get("manager", None),
                                "registered_capital": row.get("registered_capital", None),
                                "paid_in_capital": row.get("paid_in_capital", None),
                                "address": row.get("address", None),
                                "website": row.get("website", None),
                            }
                        )
            except Exception as e:
                log.debug(f"Could not fetch detailed company info: {e}")

            return stock_info if stock_info.get("name") else None

        except Exception as e:
            log.error(f"Error fetching company info for {ticker} from FinMind: {e}")
            return None

    async def fetch_tpex_stocks(
        self,
        limit: int = 100,
    ) -> list[dict] | None:
        """
        Fetch list of TPEX (OTC) stocks from FinMind.

        Args:
            limit: Maximum number of stocks to return

        Returns:
            List of dicts with ticker, name, and industry for TPEX stocks
        """
        try:
            log.debug("Fetching TPEX stock list from FinMind...")

            info_df = self.dl.taiwan_stock_info()
            if info_df is None or info_df.empty:
                return None

            # Filter for TPEX stocks (typically have market="上櫃" or similar)
            # In FinMind, TPEX stocks are identified by their market type
            if "market" in info_df.columns:
                tpex_df = info_df[info_df["market"] == "上櫃"]
            elif "type" in info_df.columns:
                # Alternative: filter by type containing "TPE" or similar
                tpex_df = info_df[info_df["type"].str.contains("TPE", na=False)]
            else:
                # Default: return all stocks (will filter later)
                tpex_df = info_df

            if tpex_df.empty:
                return None

            stocks = []
            for _, row in tpex_df.head(limit).iterrows():
                stocks.append(
                    {
                        "ticker": row.get("stock_id", ""),
                        "name": row.get("stock_name", ""),
                        "industry": row.get("industry_category", ""),
                        "market": row.get("market", "OTC"),
                    }
                )

            return stocks

        except Exception as e:
            log.error(f"Error fetching TPEX stock list from FinMind: {e}")
            return None
