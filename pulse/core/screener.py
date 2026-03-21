"""
Stock Screener - Filter stocks by technical and fundamental criteria.

Supports:
1. Preset screeners (oversold, bullish, breakout, etc)
2. Flexible criteria (rsi<30, pe<15, etc)
3. AI-driven smart screening
4. Real-time progress tracking with Rich progress bar
"""

import asyncio
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn

from pulse.core.screener_criteria import CriteriaParser
from pulse.core.screener_filter import calculate_score, matches_criteria
from pulse.utils.constants import MIDCAP100_TICKERS, TPEX_POPULAR, TW50_TICKERS
from pulse.utils.logger import get_logger

log = get_logger(__name__)


# Import Happy Lines types for type hints
try:
    from pulse.core.models import HappyLinesIndicators, HappyZone
except ImportError:
    HappyLinesIndicators = Any
    HappyZone = Any


def load_all_tickers() -> list[str]:
    """Load all tickers (TW50 + MIDCAP + POPULAR combined)."""
    # Combine all ticker lists and remove duplicates
    all_tickers = list(set(TW50_TICKERS + MIDCAP100_TICKERS + TPEX_POPULAR))
    return sorted(all_tickers)


class ScreenPreset(str, Enum):
    """Predefined screening presets."""

    OVERSOLD = "oversold"
    OVERBOUGHT = "overbought"
    BULLISH = "bullish"
    BEARISH = "bearish"
    BREAKOUT = "breakout"
    SQUEEZE = "squeeze"
    UNDERVALUED = "undervalued"
    DIVIDEND = "dividend"
    MOMENTUM = "momentum"
    KELTNER_BREAKOUT = "keltner_breakout"
    KELTNER_HOLD = "keltner_hold"
    # Happy Lines presets
    HAPPY_OVERSOLD = "happy_oversold"  # Line 1-2
    HAPPY_OVERBOUGHT = "happy_overbought"  # Line 4-5
    HAPPY_CHEAP = "happy_cheap"  # Line 1-2
    HAPPY_EXPENSIVE = "happy_expensive"  # Line 4-5


class StockUniverse(str, Enum):
    """Stock universe for screening."""

    TW50 = "tw50"  # Taiwan 50 Index components
    MIDCAP = "midcap"  # Mid-cap 100 stocks
    POPULAR = "popular"  # Popular stocks
    ALL = "all"  # All Taiwan stocks


@dataclass
class ScreenResult:
    """Result from stock screening."""

    ticker: str
    name: str | None = None
    sector: str | None = None

    # Price data
    price: float = 0.0
    change: float = 0.0
    change_percent: float = 0.0
    volume: int = 0
    avg_volume: int = 0

    # Technical indicators
    rsi_14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None
    macd_histogram: float | None = None
    sma_20: float | None = None
    sma_50: float | None = None
    sma_200: float | None = None
    ema_9: float | None = None
    ema_21: float | None = None
    ema_55: float | None = None
    bb_upper: float | None = None
    bb_lower: float | None = None
    bb_middle: float | None = None
    stoch_k: float | None = None
    stoch_d: float | None = None

    # Keltner Channel indicators
    kc_middle: float | None = None
    kc_upper: float | None = None
    kc_lower: float | None = None
    kc_position: float | None = None  # Price position relative to KC (0-100%)
    atr_14: float | None = None

    # Happy Lines (樂活五線譜) indicators
    happy_lines: Any = None  # Complete Happy Lines data (HappyLinesIndicators)

    # Fundamental data
    pe_ratio: float | None = None
    pb_ratio: float | None = None
    roe: float | None = None
    dividend_yield: float | None = None
    market_cap: float | None = None  # in TWD
    earnings_growth: float | None = None  # YoY %
    revenue_growth: float | None = None  # YoY %

    # Support/Resistance
    support: float | None = None
    resistance: float | None = None

    # Scoring
    score: float = 0.0
    signals: list[str] = field(default_factory=list)

    @property
    def volume_ratio(self) -> float:
        """Volume vs average volume ratio."""
        if self.avg_volume > 0:
            return self.volume / self.avg_volume
        return 1.0

    @property
    def market_cap_category(self) -> str:
        """Categorize market cap: micro, small, mid, large, mega."""
        if self.market_cap is None:
            return "unknown"
        mc = self.market_cap
        if mc < 500e9:  # < 500B = micro cap
            return "micro"
        elif mc < 2e12:  # < 2T = small cap
            return "small"
        elif mc < 10e12:  # < 10T = mid cap
            return "mid"
        elif mc < 50e12:  # < 50T = large cap
            return "large"
        else:  # >= 50T = mega cap
            return "mega"

    @property
    def rsi_status(self) -> str:
        """RSI status description."""
        if self.rsi_14 is None:
            return "N/A"
        if self.rsi_14 < 30:
            return "Oversold"
        if self.rsi_14 > 70:
            return "Overbought"
        return "Neutral"

    @property
    def macd_status(self) -> str:
        """MACD status description."""
        if self.macd is None or self.macd_signal is None:
            return "N/A"
        if self.macd > self.macd_signal:
            return "Bullish"
        return "Bearish"

    @property
    def bb_width(self) -> float | None:
        """Bollinger Band width as % of middle band."""
        if self.bb_upper and self.bb_lower and self.bb_middle:
            return (self.bb_upper - self.bb_lower) / self.bb_middle * 100
        return None


class StockScreener:
    """
    Screen stocks based on technical and fundamental criteria.

    Usage:
        screener = StockScreener()

        # Using preset
        results = await screener.screen_preset(ScreenPreset.OVERSOLD)

        # Using flexible criteria
        results = await screener.screen_criteria("rsi<30 and volume>1000000")

        # AI smart screening
        results = await screener.smart_screen("尋找上漲股票")
    """

    # Preset criteria definitions
    PRESETS = {
        ScreenPreset.OVERSOLD: {
            "description": "Oversold stocks (RSI < 30)",
            "criteria": {"rsi_14": ("<", 30)},
            "sort_by": "rsi_14",
            "sort_asc": True,
        },
        ScreenPreset.OVERBOUGHT: {
            "description": "Overbought stocks (RSI > 70)",
            "criteria": {"rsi_14": (">", 70)},
            "sort_by": "rsi_14",
            "sort_asc": False,
        },
        ScreenPreset.BULLISH: {
            "description": "Bullish momentum (MACD bullish + price > SMA20)",
            "criteria": {"macd_above_signal": True, "price_above_sma20": True},
            "sort_by": "score",
            "sort_asc": False,
        },
        ScreenPreset.BEARISH: {
            "description": "Bearish momentum (MACD bearish + price < SMA20)",
            "criteria": {"macd_below_signal": True, "price_below_sma20": True},
            "sort_by": "score",
            "sort_asc": False,
        },
        ScreenPreset.BREAKOUT: {
            "description": "Potential breakout (price near resistance + volume spike)",
            "criteria": {"near_resistance": True, "volume_spike": True},
            "sort_by": "volume_ratio",
            "sort_asc": False,
        },
        ScreenPreset.SQUEEZE: {
            "description": "Bollinger Band squeeze (low volatility, ready to move)",
            "criteria": {"bb_squeeze": True},
            "sort_by": "bb_width",
            "sort_asc": True,
        },
        ScreenPreset.UNDERVALUED: {
            "description": "Fundamentally undervalued (low PE, high ROE)",
            "criteria": {"pe_ratio": ("<", 15), "roe": (">", 10)},
            "sort_by": "pe_ratio",
            "sort_asc": True,
        },
        ScreenPreset.MOMENTUM: {
            "description": "Strong momentum (RSI 50-70, MACD bullish, volume up)",
            "criteria": {
                "rsi_14": ("between", (50, 70)),
                "macd_above_signal": True,
                "volume_above_avg": True,
            },
            "sort_by": "score",
            "sort_asc": False,
        },
        ScreenPreset.KELTNER_BREAKOUT: {
            "description": "Keltner Channel Breakout - Price above KC upper band + EMA bullish",
            "criteria": {
                "kc_above_upper": True,  # Price broke above KC upper
                "kc_ema_bullish": True,  # EMA 9 > EMA 21 > EMA 55
                "volume_min": 3000000,  # Min 3M avg daily volume (liquid stocks)
            },
            "sort_by": "kc_position",
            "sort_asc": False,
        },
        ScreenPreset.KELTNER_HOLD: {
            "description": "Keltner Channel Hold - Price holding above KC upper band",
            "criteria": {
                "kc_above_upper": True,  # Price above KC upper
                "kc_above_middle": True,  # Price above KC middle
                "volume_min": 3000000,  # Min 3M avg daily volume
            },
            "sort_by": "price",
            "sort_asc": False,
        },
        # Happy Lines (樂活五線譜) presets
        ScreenPreset.HAPPY_OVERSOLD: {
            "description": "Happy Lines Oversold - Price in Line 1-2 (超跌/偏低區)",
            "criteria": {
                "happy_lines": ("exists", True),
                "happy_zone": "oversold",
            },
            "sort_by": "happy_lines.position_ratio",
            "sort_asc": True,
        },
        ScreenPreset.HAPPY_OVERBOUGHT: {
            "description": "Happy Lines Overbought - Price in Line 4-5 (偏高/過熱區)",
            "criteria": {
                "happy_lines": ("exists", True),
                "happy_zone": "overbought",
            },
            "sort_by": "happy_lines.position_ratio",
            "sort_asc": False,
        },
        ScreenPreset.HAPPY_CHEAP: {
            "description": "Happy Lines Cheap - Price below Line 2 (偏低區以下)",
            "criteria": {
                "happy_lines": ("exists", True),
                "happy_zone": "cheap",
            },
            "sort_by": "happy_lines.position_ratio",
            "sort_asc": True,
        },
        ScreenPreset.HAPPY_EXPENSIVE: {
            "description": "Happy Lines Expensive - Price above Line 4 (偏高區以上)",
            "criteria": {
                "happy_lines": ("exists", True),
                "happy_zone": "expensive",
            },
            "sort_by": "happy_lines.position_ratio",
            "sort_asc": False,
        },
    }

    def __init__(
        self,
        universe: list[str] | None = None,
        universe_type: StockUniverse | None = None,
    ):
        """
        Initialize screener with stock universe.

        Args:
            universe: Custom list of tickers. If provided, overrides universe_type.
            universe_type: Predefined universe type (TW50, MIDCAP, POPULAR, ALL).
        """
        if universe is not None:
            self.universe = universe
        elif universe_type:
            self.universe = self._get_universe(universe_type)
        else:
            self.universe = TW50_TICKERS  # Default to TW50

        self._criteria_parser = CriteriaParser(self.PRESETS)

    def _get_universe(self, universe_type: StockUniverse) -> list[str]:
        """Get stock universe based on type."""
        if universe_type == StockUniverse.TW50:
            return TW50_TICKERS
        elif universe_type == StockUniverse.MIDCAP:
            return MIDCAP100_TICKERS
        elif universe_type == StockUniverse.POPULAR:
            return TW50_TICKERS + TPEX_POPULAR  # Combined popular stocks
        elif universe_type == StockUniverse.ALL:
            return load_all_tickers()
        return TW50_TICKERS  # Default

    async def _fetch_stock_data(
        self, 
        ticker: str, 
        fetcher: Any = None, 
        analyzer: Any = None
    ) -> ScreenResult | None:
        """Fetch all data needed for screening with optimized single-fetch logic."""
        try:
            from datetime import datetime, timedelta
            import pandas as pd
            if fetcher is None:
                from pulse.core.data.stock_data_provider import StockDataProvider
                fetcher = StockDataProvider()
            if analyzer is None:
                from pulse.core.analysis.technical import TechnicalAnalyzer
                analyzer = TechnicalAnalyzer()

            # Define date range (6 months is enough for most indicators except SMA200)
            # If a preset specifically needs SMA200, we'll use 1y
            days_needed = 365 # Keep 1y for safety/SMA200, but fetch only ONCE
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_needed)
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")

            # 1. Fetch stock data ONCE (this includes history)
            stock = await fetcher.fetch_stock(
                ticker, period="1y", start_date=start_date_str, end_date=end_date_str
            )
            if not stock or not stock.history:
                return None

            result = ScreenResult(
                ticker=ticker,
                name=stock.name,
                sector=stock.sector,
                price=stock.current_price,
                change=stock.change,
                change_percent=stock.change_percent,
                volume=stock.volume,
                avg_volume=stock.avg_volume,
            )

            # 2. Convert history to DataFrame for calculations (Reuse memory)
            # This is much faster than re-fetching
            history_data = [
                {
                    "date": h.date,
                    "open": h.open,
                    "high": h.high,
                    "low": h.low,
                    "close": h.close,
                    "volume": h.volume,
                }
                for h in stock.history
            ]
            df = pd.DataFrame(history_data)
            df.set_index("date", inplace=True)
            df.columns = df.columns.str.lower()

            # 3. Calculate technical indicators from the ALREADY fetched data
            # Use the internal _calculate_indicators which takes a DataFrame
            technical = analyzer._calculate_indicators(ticker, df)

            if technical:
                result.rsi_14 = technical.rsi_14
                result.macd = technical.macd
                result.macd_signal = technical.macd_signal
                result.macd_histogram = technical.macd_histogram
                result.sma_20 = technical.sma_20
                result.sma_50 = technical.sma_50
                result.sma_200 = technical.sma_200
                result.ema_9 = technical.ema_9
                result.ema_21 = technical.ema_21
                result.ema_55 = technical.ema_55
                result.bb_upper = technical.bb_upper
                result.bb_lower = technical.bb_lower
                result.bb_middle = technical.bb_middle
                result.stoch_k = technical.stoch_k
                result.stoch_d = technical.stoch_d
                result.kc_middle = technical.kc_middle
                result.kc_upper = technical.kc_upper
                result.kc_lower = technical.kc_lower
                result.support = technical.support_1
                result.resistance = technical.resistance_1

                # 4. Calculate Happy Lines (Reuse the same DataFrame)
                happy_lines = analyzer.calculate_happy_lines(df, ticker, period=60)
                if happy_lines:
                    result.happy_lines = happy_lines

            # 5. Fetch fundamental data (Optional, still separate but could be optimized later)
            try:
                fundamental = await fetcher.fetch_fundamentals(
                    ticker, start_date=start_date_str, end_date=end_date_str
                )
                if fundamental:
                    result.pe_ratio = fundamental.pe_ratio
                    result.pb_ratio = fundamental.pb_ratio
                    result.roe = fundamental.roe
                    result.dividend_yield = fundamental.dividend_yield
                    result.market_cap = fundamental.market_cap
                    result.earnings_growth = fundamental.earnings_growth
                    result.revenue_growth = fundamental.revenue_growth
            except Exception:
                pass

            return result

        except Exception as e:
            log.error(f"Error fetching data for {ticker}: {e}")
            return None

    def _matches_criteria(
        self,
        result: ScreenResult,
        criteria: dict[str, Any],
    ) -> tuple[bool, list[str]]:
        """Check if stock matches all criteria. Delegates to screener_filter."""
        return matches_criteria(result, criteria)

    def _calculate_score(self, result: ScreenResult) -> float:
        """Calculate overall score for ranking. Delegates to screener_filter."""
        return calculate_score(result)

    def parse_criteria(self, criteria_str: str) -> dict[str, Any]:
        """Parse criteria string into dict. Delegates to CriteriaParser."""
        return self._criteria_parser.parse(criteria_str)

    async def screen_preset(
        self,
        preset: ScreenPreset,
        limit: int = 20,
    ) -> list[ScreenResult]:
        """Screen stocks using a preset."""
        preset_config = self.PRESETS.get(preset)
        if not preset_config:
            return []

        log.info(f"Screening with preset: {preset.value}")
        return await self._run_screen(
            criteria=preset_config["criteria"],
            sort_by=preset_config.get("sort_by", "score"),
            sort_asc=preset_config.get("sort_asc", False),
            limit=limit,
        )

    async def screen_criteria(
        self,
        criteria_str: str,
        limit: int = 20,
    ) -> list[ScreenResult]:
        """Screen stocks using flexible criteria string."""
        criteria = self.parse_criteria(criteria_str)
        if not criteria:
            return []

        log.info(f"Screening with criteria: {criteria}")
        return await self._run_screen(
            criteria=criteria,
            sort_by="score",
            sort_asc=False,
            limit=limit,
        )

    async def smart_screen(
        self,
        query: str,
        limit: int = 10,
    ) -> tuple[list[ScreenResult], str]:
        """Natural-language stock screening. Delegates to CriteriaParser."""
        return await self._criteria_parser.smart_parse(query, self, limit)

    async def _run_screen(
        self,
        criteria: dict[str, Any],
        sort_by: str = "score",
        sort_asc: bool = False,
        limit: int = 20,
        show_progress: bool = True,
    ) -> list[ScreenResult]:
        """Run screening with given criteria.

        Args:
            criteria: Screening criteria dictionary
            sort_by: Field to sort results by
            sort_asc: Sort ascending if True, descending if False
            limit: Maximum number of results to return
            show_progress: Show Rich progress bar if True

        Returns:
            List of matching ScreenResult objects
        """
        results = []

        # Fetch data for all stocks in parallel (with semaphore to limit concurrency)
        # Increased to 30 for better throughput
        semaphore = asyncio.Semaphore(30)

        from pulse.core.analysis.technical import TechnicalAnalyzer
        from pulse.core.data.stock_data_provider import StockDataProvider

        # Instantiate once to reuse
        fetcher = StockDataProvider()
        analyzer = TechnicalAnalyzer()

        async def fetch_with_limit(ticker: str) -> ScreenResult | None:
            async with semaphore:
                return await self._fetch_stock_data(ticker, fetcher=fetcher, analyzer=analyzer)

        log.info(f"Screening {len(self.universe)} stocks...")

        # Create progress bar
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="green", finished_style="green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            transient=not show_progress,
            disable=not show_progress,
        )

        all_results: list[ScreenResult | None | BaseException] = []

        with progress:
            task_id = progress.add_task(
                f"Screening {len(self.universe)} stocks...", total=len(self.universe)
            )

            # Process in larger batches for better efficiency
            batch_size = 30
            for i in range(0, len(self.universe), batch_size):
                batch = self.universe[i : i + batch_size]
                tasks = [fetch_with_limit(ticker) for ticker in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                all_results.extend(batch_results)
                progress.update(task_id, advance=len(batch))

        # Filter and score results
        for result in all_results:
            if isinstance(result, Exception) or result is None:
                continue

            matches, signals = self._matches_criteria(result, criteria)
            if matches:
                result.score = self._calculate_score(result)
                result.signals = signals
                results.append(result)

        # Sort results
        if sort_by == "score":
            results.sort(key=lambda x: x.score, reverse=not sort_asc)
        elif results:
            results.sort(key=lambda x: getattr(x, sort_by, None) or 0, reverse=not sort_asc)

        log.info(f"Found {len(results)} stocks matching criteria")

        return results[:limit]

    def format_results(
        self,
        results: list[ScreenResult],
        title: str = "Screening Results",
        show_details: bool = True,
    ) -> str:
        """Format screening results as text."""
        if not results:
            return "No stocks found matching criteria."

        lines = [
            title,
            f"Found {len(results)} stocks",
            "",
        ]

        if show_details:
            for i, r in enumerate(results, 1):
                rsi_str = f"{r.rsi_14:.1f}" if r.rsi_14 else "N/A"
                macd_str = r.macd_status

                lines.append(f"{i}. {r.ticker} - {r.name or 'N/A'}")
                lines.append(f"   Price: NT$ {r.price:,.0f} ({r.change_percent:+.2f}%)")
                lines.append(f"   RSI: {rsi_str} ({r.rsi_status}) | MACD: {macd_str}")

                if r.support and r.resistance:
                    lines.append(f"   Support: {r.support:,.0f} | Resistance: {r.resistance:,.0f}")

                if r.signals:
                    lines.append(f"   Signals: {', '.join(r.signals)}")

                lines.append(f"   Score: {r.score:.0f}/100")
                lines.append("")
        else:
            # Simple table format
            lines.append(
                f"{'No':<3} {'Ticker':<8} {'Price':>10} {'Change':>8} {'RSI':>6} {'Score':>6}"
            )
            lines.append("-" * 45)

            for i, r in enumerate(results, 1):
                rsi_str = f"{r.rsi_14:.1f}" if r.rsi_14 else "N/A"
                lines.append(
                    f"{i:<3} {r.ticker:<8} {r.price:>10,.0f} {r.change_percent:>+7.2f}% {rsi_str:>6} {r.score:>6.0f}"
                )

        return "\n".join(lines)
