"""Centralized data provider to fetch stock data from FinMind (primary) or yfinance (fallback)."""

from typing import List, Optional

import pandas as pd

from pulse.core.models import StockData, FundamentalData
from pulse.utils.logger import get_logger
from pulse.core.data.finmind_data import FinMindFetcher
from pulse.core.data.yfinance import YFinanceFetcher

log = get_logger(__name__)


class StockDataProvider:
    """
    Provides stock data by attempting to fetch from FinMind first, then falling back to yfinance.
    """

    def __init__(self, finmind_token: str = ""):
        self.finmind_fetcher = FinMindFetcher(token=finmind_token)
        self.yfinance_fetcher = (
            YFinanceFetcher()
        )  # YFinanceFetcher already configured for TW market

    async def fetch_stock(
        self,
        ticker: str,
        period: str = "3mo",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> StockData | None:
        """
        Fetches stock data for a ticker.

        Attempts FinMind first, then yfinance.
        FinMind uses start_date/end_date, yfinance uses period.
        """
        # Try FinMind first
        if start_date and end_date:
            data = await self.finmind_fetcher.fetch_stock(ticker, start_date, end_date)
            if data:
                log.debug(f"Fetched {ticker} from FinMind.")
                return data
            else:
                log.warning(f"FinMind failed for {ticker}, trying yfinance...")

        # Fallback to yfinance if FinMind fails or dates not provided
        # YFinance uses 'period' parameter
        data = await self.yfinance_fetcher.fetch_stock(ticker, period)
        if data:
            log.debug(f"Fetched {ticker} from yfinance (fallback).")
            return data

        log.error(f"Failed to fetch {ticker} from both FinMind and yfinance.")
        return None

    async def fetch_fundamentals(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> FundamentalData | None:
        """
        Fetches fundamental data for a ticker.

        Attempts FinMind first, then yfinance.
        """
        # Try FinMind first
        if start_date and end_date:
            data = await self.finmind_fetcher.fetch_fundamentals(ticker, start_date, end_date)
            if data:
                log.debug(f"Fetched fundamentals for {ticker} from FinMind.")
                return data
            else:
                log.warning(f"FinMind failed for fundamentals of {ticker}, trying yfinance...")

        # Fallback to yfinance
        data = await self.yfinance_fetcher.fetch_fundamentals(ticker)
        if data:
            log.debug(f"Fetched fundamentals for {ticker} from yfinance (fallback).")
            return data

        log.error(f"Failed to fetch fundamentals for {ticker} from both FinMind and yfinance.")
        return None

    async def fetch_multiple(
        self,
        tickers: List[str],
        period: str = "3mo",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[StockData]:
        """
        Fetches data for multiple tickers.

        Attempts FinMind first, then yfinance for each ticker.
        """
        # Try FinMind first for multiple stocks
        if start_date and end_date:
            finmind_results = await self.finmind_fetcher.fetch_multiple(
                tickers, start_date, end_date
            )
            if len(finmind_results) == len(tickers):  # All fetched successfully
                log.debug(f"Fetched {len(tickers)} stocks from FinMind.")
                return finmind_results
            elif finmind_results:  # Some fetched, try fallback for others
                log.warning(
                    f"FinMind only fetched {len(finmind_results)}/{len(tickers)} stocks. Trying yfinance for missing ones."
                )
                fetched_tickers = {s.ticker for s in finmind_results}
                remaining_tickers = [t for t in tickers if t not in fetched_tickers]
                yfinance_results = await self.yfinance_fetcher.fetch_multiple(
                    remaining_tickers, period
                )
                return finmind_results + yfinance_results
            else:
                log.warning(
                    f"FinMind failed for all {len(tickers)} stocks, trying yfinance for all."
                )

        # Fallback to yfinance for all if FinMind completely failed or dates not provided
        yfinance_results = await self.yfinance_fetcher.fetch_multiple(tickers, period)
        if yfinance_results:
            log.debug(f"Fetched {len(yfinance_results)} stocks from yfinance (fallback).")
            return yfinance_results

        log.error(f"Failed to fetch multiple tickers from both FinMind and yfinance.")
        return []

    async def fetch_history(
        self,
        ticker: str,
        period: str = "3mo",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame | None:
        """
        Fetches historical data as DataFrame.

        Attempts FinMind first, then yfinance.
        """
        # Try FinMind first
        if start_date and end_date:
            df = await self.finmind_fetcher.fetch_history(ticker, start_date, end_date)
            if df is not None and not df.empty:
                log.debug(f"Fetched history for {ticker} from FinMind.")
                return df
            else:
                log.warning(f"FinMind failed for history of {ticker}, trying yfinance...")

        # Fallback to yfinance
        df = self.yfinance_fetcher.get_history_df(
            ticker, period
        )  # yfinance fetch_history is async wrapper
        if df is not None and not df.empty:
            log.debug(f"Fetched history for {ticker} from yfinance (fallback).")
            return df

        log.error(f"Failed to fetch history for {ticker} from both FinMind and yfinance.")
        return None

    async def fetch_index(
        self,
        index_name: str,
        period: str = "3mo",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> StockData | None:
        """
        Fetches market index data.

        Attempts FinMind first, then yfinance.
        """
        # Try FinMind first
        if start_date and end_date:
            data = await self.finmind_fetcher.fetch_index(index_name, start_date, end_date)
            if data:
                log.debug(f"Fetched index {index_name} from FinMind.")
                return data
            else:
                log.warning(f"FinMind failed for index {index_name}, trying yfinance...")

        # Fallback to yfinance
        data = await self.yfinance_fetcher.fetch_index(index_name, period)
        if data:
            log.debug(f"Fetched index {index_name} from yfinance (fallback).")
            return data

        log.error(f"Failed to fetch index {index_name} from both FinMind and yfinance.")
        return None

    async def fetch_institutional_investors(
        self,
        ticker: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame | None:
        """
        Fetches institutional investor data.

        Attempts FinMind first. No fallback to yfinance as it doesn't provide this data.
        """
        if start_date and end_date:
            df = await self.finmind_fetcher.fetch_institutional_investors(
                ticker, start_date, end_date
            )
            if df is not None and not df.empty:
                log.debug(f"Fetched institutional investor data for {ticker} from FinMind.")
                return df
            else:
                log.warning(f"FinMind failed for institutional investor data of {ticker}.")

        log.warning(
            f"Institutional investor data for {ticker} not available from FinMind or yfinance (not supported)."
        )
        return None
