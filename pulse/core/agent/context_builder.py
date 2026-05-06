"""
ContextBuilder - Fetches real market data and assembles AgentContext.

Extracted from SmartAgent to keep data-fetching logic self-contained.
"""

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from pulse.utils.logger import get_logger

if TYPE_CHECKING:
    from collections.abc import Callable

log = get_logger(__name__)


class ContextBuilder:
    """Fetches stock data and assembles AgentContext for AI analysis."""

    def __init__(self) -> None:
        self._fetcher = None  # Lazy-loaded YFinanceFetcher shared across methods

    def _get_fetcher(self):
        if self._fetcher is None:
            from pulse.core.data.yfinance import YFinanceFetcher
            self._fetcher = YFinanceFetcher()
        return self._fetcher

    async def fetch_stock_data(self, ticker: str) -> dict[str, Any] | None:
        """Fetch real stock data from yfinance."""
        try:
            fetcher = self._get_fetcher()
            stock = await fetcher.fetch_stock(ticker)

            if not stock:
                return None

            return {
                "ticker": stock.ticker,
                "name": stock.name,
                "sector": stock.sector,
                "current_price": stock.current_price,
                "previous_close": stock.previous_close,
                "change": stock.change,
                "change_percent": stock.change_percent,
                "volume": stock.volume,
                "avg_volume": stock.avg_volume,
                "day_high": stock.day_high,
                "day_low": stock.day_low,
                "week_52_high": stock.week_52_high,
                "week_52_low": stock.week_52_low,
                "market_cap": stock.market_cap,
            }
        except Exception as e:
            log.error(f"Error fetching stock data for {ticker}: {e}")
            return None

    async def fetch_technical(self, ticker: str) -> dict[str, Any] | None:
        """Fetch technical analysis data."""
        try:
            from pulse.core.analysis.technical import TechnicalAnalyzer

            analyzer = TechnicalAnalyzer()
            indicators = await analyzer.analyze(ticker)

            if not indicators:
                return None

            return {
                "rsi_14": indicators.rsi_14,
                "macd": indicators.macd,
                "macd_signal": indicators.macd_signal,
                "macd_histogram": indicators.macd_histogram,
                "sma_20": indicators.sma_20,
                "sma_50": indicators.sma_50,
                "sma_200": indicators.sma_200,
                "ema_9": indicators.ema_9,
                "ema_21": indicators.ema_21,
                "bb_upper": indicators.bb_upper,
                "bb_middle": indicators.bb_middle,
                "bb_lower": indicators.bb_lower,
                "stoch_k": indicators.stoch_k,
                "stoch_d": indicators.stoch_d,
                "atr_14": indicators.atr_14,
                "support_1": indicators.support_1,
                "resistance_1": indicators.resistance_1,
                "trend": indicators.trend.value if indicators.trend else None,
                "signal": indicators.signal.value if indicators.signal else None,
            }
        except Exception as e:
            log.error(f"Error fetching technical data for {ticker}: {e}")
            return None

    async def fetch_fundamental(self, ticker: str) -> dict[str, Any] | None:
        """Fetch fundamental data."""
        try:
            from pulse.core.data.stock_data_provider import StockDataProvider

            provider = StockDataProvider()
            fund = await provider.fetch_fundamentals(
                ticker,
                start_date=(datetime.now() - timedelta(days=365 * 5)).strftime("%Y-%m-%d"),
                end_date=datetime.now().strftime("%Y-%m-%d"),
            )

            if not fund:
                return None

            return {
                "pe_ratio": fund.pe_ratio,
                "pb_ratio": fund.pb_ratio,
                "ps_ratio": fund.ps_ratio,
                "peg_ratio": fund.peg_ratio,
                "ev_ebitda": fund.ev_ebitda,
                "roe": fund.roe,
                "roa": fund.roa,
                "npm": fund.npm,
                "opm": fund.opm,
                "gpm": fund.gpm,
                "debt_to_equity": fund.debt_to_equity,
                "current_ratio": fund.current_ratio,
                "quick_ratio": fund.quick_ratio,
                "dividend_yield": fund.dividend_yield,
                "payout_ratio": fund.payout_ratio,
                "eps": fund.eps,
                "bvps": fund.bvps,
                "dps": fund.dps,
                "revenue_growth": fund.revenue_growth,
                "earnings_growth": fund.earnings_growth,
                "market_cap": fund.market_cap,
                "enterprise_value": fund.enterprise_value,
            }
        except Exception as e:
            log.error(f"Error fetching fundamental data for {ticker}: {e}")
            return None

    async def generate_chart(self, ticker: str, period: str = "3mo") -> str | None:
        """Generate price chart as PNG file."""
        try:
            from pulse.core.chart_generator import ChartGenerator

            df = self._get_fetcher().get_history_df(ticker, period)

            if df is None or df.empty:
                return None

            dates = df.index.strftime("%Y-%m-%d").tolist()
            prices = df["close"].tolist()
            volumes = df["volume"].tolist() if "volume" in df.columns else None

            generator = ChartGenerator()
            filepath = generator.price_chart(ticker, dates, prices, volumes, period)

            return filepath
        except Exception as e:
            log.error(f"Error generating chart for {ticker}: {e}")
            return None

    async def generate_forecast(
        self, ticker: str, days: int = 7, mode: str = "fast"
    ) -> dict[str, Any] | None:
        """Generate price forecast with PNG chart."""
        try:
            from pulse.core.chart_generator import ChartGenerator
            from pulse.core.forecasting import PriceForecaster

            df = self._get_fetcher().get_history_df(ticker, "6mo")

            if df is None or df.empty:
                return None

            prices = df["close"].tolist()
            dates = df.index.strftime("%Y-%m-%d").tolist()

            forecaster = PriceForecaster()
            result = await forecaster.forecast(ticker, prices, dates, days, mode=mode)

            if not result:
                return None

            generator = ChartGenerator()
            filepath = generator.forecast_chart(
                ticker=ticker,
                dates=dates,
                historical=prices,
                forecast=result.predictions,
                lower_bound=result.lower_bound,
                upper_bound=result.upper_bound,
                forecast_days=days,
            )

            return {
                "summary": forecaster.format_forecast(result),
                "filepath": filepath,
                "result": result,
            }
        except Exception as e:
            log.error(f"Error generating forecast for {ticker}: {e}")
            return None

    async def gather_context(
        self,
        intent: str,
        tickers: list[str],
        progress_callback: "Callable | None" = None,
    ) -> "AgentContext":
        """
        Gather all relevant data based on intent.
        This is where we fetch REAL data before AI analysis.
        """
        import asyncio

        from pulse.core.smart_agent import AgentContext

        ctx = AgentContext(
            intent=intent,
            tickers=tickers,
            ticker=tickers[0] if tickers else None,
        )

        if not tickers:
            return ctx

        primary_ticker = tickers[0]

        if progress_callback:
            await progress_callback(f"正在取得 {primary_ticker} 股票數據...")
        ctx.stock_data = await self.fetch_stock_data(primary_ticker)

        if not ctx.stock_data:
            ctx.error = f"無法取得 {primary_ticker} 的數據"
            return ctx

        need_technical = intent in ["analyze", "technical", "recommendation"]
        need_fundamental = intent in ["analyze", "fundamental", "recommendation"]

        if need_technical and need_fundamental:
            if progress_callback:
                await progress_callback(f"正在計算 {primary_ticker} 技術與基本面數據...")
            ctx.technical_data, ctx.fundamental_data = await asyncio.gather(
                self.fetch_technical(primary_ticker),
                self.fetch_fundamental(primary_ticker),
            )
        elif need_technical:
            if progress_callback:
                await progress_callback(f"正在計算 {primary_ticker} 技術指標...")
            ctx.technical_data = await self.fetch_technical(primary_ticker)
        elif need_fundamental:
            if progress_callback:
                await progress_callback(f"正在取得 {primary_ticker} 基本面數據...")
            ctx.fundamental_data = await self.fetch_fundamental(primary_ticker)

        if intent == "compare" and len(tickers) >= 2:
            if progress_callback:
                await progress_callback(f"正在取得比較數據...")
            stocks = await asyncio.gather(
                *[self.fetch_stock_data(t) for t in tickers[:4]]
            )
            ctx.comparison_data = [s for s in stocks if s is not None]

        return ctx
