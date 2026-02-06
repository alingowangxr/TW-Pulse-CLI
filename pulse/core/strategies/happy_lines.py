"""
Happy Lines Strategy (樂活五線譜策略)

策略說明 (Strategy Description)
================================

【策略邏輯】
樂活五線譜是一種基於統計分佈的股價位階判斷工具，將股價分為五個區域：
- 第5線 (過熱區): 中軌 + 2σ
- 第4線 (偏高區): 中軌 + 1σ
- 第3線 (平衡區): 中軌 (N日移動平均)
- 第2線 (偏低區): 中軌 - 1σ
- 第1線 (超跌區): 中軌 - 2σ

【策略條件】
1. 買進條件 (Buy Signal):
   - 股價處於第1線或第2線區域 (超跌/偏低)
   - 趨勢為多頭或盤整 (非空頭)
   - 日均成交量 >= 1,000,000 股

2. 持有條件 (Hold Signal):
   - 股價在第2-4線之間
   - 或已進場且趨勢仍偏多

3. 賣出條件 (Sell Signal):
   - 股價突破第5線 (過熱)
   - 或股價跌破第3線且趨勢轉空

【優勢】
- 統計基礎，客觀判斷位階
- 適合波段操作與長期投資
- 可與其他策略搭配使用

【參數說明】
- period: 計算週期 (預設120日，可選20/60/120/240日)
- min_avg_volume: 最低日均成交量 (預設100萬股)

作者: Pulse-CLI
版本: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from pulse.core.models import HappyLinesIndicators, HappyZone, SignalType, TrendType
from pulse.core.screener import ScreenResult, StockScreener
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class HappyLinesSignal(str, Enum):
    """Happy Lines strategy signal types."""

    STRONG_BUY = "STRONG_BUY"  # 強烈買進 - 超跌區且趨勢轉強
    BUY = "BUY"  # 買進 - 偏低區
    HOLD = "HOLD"  # 持有 - 平衡區或趨勢持續
    SELL = "SELL"  # 賣出 - 偏高區
    STRONG_SELL = "STRONG_SELL"  # 強烈賣出 - 過熱區
    WATCH = "WATCH"  # 觀察 - 等待明確訊號


@dataclass
class HappyLinesStrategyResult:
    """Happy Lines strategy screening result."""

    ticker: str
    name: str | None = None
    signal: HappyLinesSignal = HappyLinesSignal.WATCH

    # Price Data
    price: float = 0.0
    change_percent: float = 0.0
    volume: int = 0
    avg_volume: int = 0

    # Happy Lines Data
    line_1: float | None = None  # 超跌線
    line_2: float | None = None  # 偏低線
    line_3: float | None = None  # 平衡線
    line_4: float | None = None  # 偏高線
    line_5: float | None = None  # 過熱線
    position_ratio: float = 0.0  # 位階百分比 (0-100%)
    zone: HappyZone = HappyZone.BALANCED

    # Technical Data
    rsi_14: float | None = None
    trend: TrendType = TrendType.SIDEWAYS

    # Strategy Metrics
    distance_to_line1: float = 0.0  # % distance to line 1 (oversold)
    distance_to_line5: float = 0.0  # % distance to line 5 (overbought)

    # Metadata
    period: int = 60  # 計算週期
    screened_at: datetime = field(default_factory=datetime.now)
    notes: list[str] = field(default_factory=list)

    @property
    def volume_ratio(self) -> float:
        """Volume vs average volume ratio."""
        if self.avg_volume > 0:
            return self.volume / self.avg_volume
        return 1.0

    @property
    def is_liquid(self) -> bool:
        """Check if stock meets minimum liquidity criteria."""
        return self.avg_volume >= 1_000_000

    @property
    def is_near_support(self) -> bool:
        """Check if price is near support (Line 1-2)."""
        return self.zone in [HappyZone.OVERSOLD, HappyZone.UNDERVALUED]

    @property
    def is_near_resistance(self) -> bool:
        """Check if price is near resistance (Line 4-5)."""
        return self.zone in [HappyZone.OVERVALUED, HappyZone.OVERBOUGHT]

    @property
    def line_width(self) -> float:
        """Calculate total channel width."""
        if self.line_5 and self.line_1:
            return self.line_5 - self.line_1
        return 0.0

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for display/export."""
        return {
            "ticker": self.ticker,
            "name": self.name,
            "signal": self.signal.value,
            "price": self.price,
            "change_percent": self.change_percent,
            "volume": self.volume,
            "avg_volume": self.avg_volume,
            "line_1": self.line_1,
            "line_2": self.line_2,
            "line_3": self.line_3,
            "line_4": self.line_4,
            "line_5": self.line_5,
            "position_ratio": self.position_ratio,
            "zone": self.zone.value,
            "rsi_14": self.rsi_14,
            "trend": self.trend.value,
            "distance_to_line1": self.distance_to_line1,
            "distance_to_line5": self.distance_to_line5,
            "period": self.period,
            "is_liquid": self.is_liquid,
            "is_near_support": self.is_near_support,
            "is_near_resistance": self.is_near_resistance,
            "notes": self.notes,
        }


class HappyLinesStrategy:
    """
    Happy Lines (樂活五線譜) Strategy for position-based trading.

    Parameters
    ----------
    period : int
        Calculation period (default: 60, options: 20, 60, 120, 240)
    min_avg_volume : int
        Minimum average daily volume (default: 1,000,000)

    Usage
    -----
    >>> strategy = HappyLinesStrategy(period=60)
    >>> results = await strategy.screen()
    >>> for r in results:
    ...     print(f"{r.ticker}: {r.signal.value} @ {r.price} ({r.zone.value})")
    """

    # Strategy Parameters
    DEFAULT_PERIOD = 120  # 120日為預設週期
    DEFAULT_MIN_AVG_VOLUME = 1_000_000  # 100萬股

    # Valid periods
    VALID_PERIODS = [20, 60, 120, 240]

    def __init__(
        self,
        period: int | None = None,
        min_avg_volume: int | None = None,
    ):
        """Initialize Happy Lines Strategy."""
        self.period = period or self.DEFAULT_PERIOD
        if self.period not in self.VALID_PERIODS:
            log.warning(f"Invalid period {period}, using default {self.DEFAULT_PERIOD}")
            self.period = self.DEFAULT_PERIOD

        self.min_avg_volume = min_avg_volume or self.DEFAULT_MIN_AVG_VOLUME
        self.screener = StockScreener()

        log.info(
            f"Initialized Happy Lines Strategy (period={self.period}, min_vol={self.min_avg_volume:,})"
        )

    def _determine_signal(
        self,
        result: ScreenResult,
    ) -> tuple[HappyLinesSignal, list[str]]:
        """
        Determine Happy Lines strategy signal.

        Logic:
        - STRONG_BUY: Price in oversold zone (Line 1) + Bullish trend
        - BUY: Price in undervalued zone (Line 2) or oversold + sideways
        - HOLD: Price in balanced zone or favorable trend continuation
        - SELL: Price in overvalued zone (Line 4) + bearish trend
        - STRONG_SELL: Price in overbought zone (Line 5)
        - WATCH: Unclear signals
        """
        notes = []

        # Check liquidity
        if result.avg_volume < self.min_avg_volume:
            return HappyLinesSignal.WATCH, ["成交量過低"]

        # Get Happy Lines data from screener result
        if not hasattr(result, "happy_lines") or not result.happy_lines:
            return HappyLinesSignal.WATCH, ["無五線譜數據"]

        happy = result.happy_lines
        zone = happy.zone
        trend = happy.trend

        # Signal determination based on zone
        if zone == HappyZone.OVERSOLD:
            if trend == TrendType.BULLISH:
                notes.append(f"超跌區 ({happy.position_ratio:.1f}%) + 多頭趨勢")
                return HappyLinesSignal.STRONG_BUY, notes
            else:
                notes.append(f"超跌區 ({happy.position_ratio:.1f}%) - 等待趨勢確認")
                return HappyLinesSignal.BUY, notes

        elif zone == HappyZone.UNDERVALUED:
            if trend in [TrendType.BULLISH, TrendType.SIDEWAYS]:
                notes.append(f"偏低區 ({happy.position_ratio:.1f}%) - 可分批布局")
                return HappyLinesSignal.BUY, notes
            else:
                notes.append(f"偏低區但趨勢偏空 - 觀望")
                return HappyLinesSignal.WATCH, notes

        elif zone == HappyZone.BALANCED:
            notes.append(f"平衡區 ({happy.position_ratio:.1f}%) - 觀望")
            return HappyLinesSignal.HOLD, notes

        elif zone == HappyZone.OVERVALUED:
            if trend == TrendType.BEARISH:
                notes.append(f"偏高區 ({happy.position_ratio:.1f}%) + 空頭趨勢")
                return HappyLinesSignal.SELL, notes
            else:
                notes.append(f"偏高區 ({happy.position_ratio:.1f}%) - 可分批獲利")
                return HappyLinesSignal.HOLD, notes

        elif zone == HappyZone.OVERBOUGHT:
            notes.append(f"過熱區 ({happy.position_ratio:.1f}%) - 考慮減碼")
            return HappyLinesSignal.STRONG_SELL, notes

        return HappyLinesSignal.WATCH, notes

    async def screen(
        self,
        universe: list[str] | None = None,
        limit: int = 20,
        include_watchlist: bool = False,
    ) -> list[HappyLinesStrategyResult]:
        """
        Screen stocks using Happy Lines strategy.

        Parameters
        ----------
        universe : list[str], optional
            Custom list of tickers to screen
        limit : int
            Maximum number of results to return
        include_watchlist : bool
            Include WATCH signals in results (default: False)

        Returns
        -------
        list[HappyLinesStrategyResult]
            List of screened stocks with signals and metrics
        """
        log.info(f"Starting Happy Lines strategy screening (period={self.period})...")

        # Use custom universe or default
        if universe:
            self.screener.universe = universe

        # Screen for stocks with Happy Lines data
        try:
            results = await self.screener._run_screen(
                criteria={
                    "happy_lines": ("exists", True),
                    "volume_min": self.min_avg_volume,
                },
                sort_by="happy_position_ratio",
                sort_asc=True,  # Sort by lowest position ratio (most oversold first)
                limit=100,
                show_progress=True,
            )
        except Exception as e:
            log.error(f"Error during screening: {e}")
            return []

        # Process results
        strategy_results: list[HappyLinesStrategyResult] = []

        for result in results:
            if not result:
                continue

            signal, notes = self._determine_signal(result)

            # Filter based on include_watchlist
            if signal == HappyLinesSignal.WATCH and not include_watchlist:
                continue

            # Get Happy Lines data
            happy = getattr(result, "happy_lines", None)
            if not happy:
                continue

            strategy_result = HappyLinesStrategyResult(
                ticker=result.ticker,
                name=result.name,
                signal=signal,
                price=result.price,
                change_percent=result.change_percent,
                volume=result.volume,
                avg_volume=result.avg_volume,
                line_1=happy.line_1,
                line_2=happy.line_2,
                line_3=happy.line_3,
                line_4=happy.line_4,
                line_5=happy.line_5,
                position_ratio=happy.position_ratio,
                zone=happy.zone,
                rsi_14=result.rsi_14,
                trend=happy.trend,
                distance_to_line1=happy.distance_to_line1,
                distance_to_line5=happy.distance_to_line5,
                period=self.period,
                notes=notes,
            )

            strategy_results.append(strategy_result)

        # Sort by signal priority
        signal_priority = {
            HappyLinesSignal.STRONG_BUY: 0,
            HappyLinesSignal.BUY: 1,
            HappyLinesSignal.HOLD: 2,
            HappyLinesSignal.WATCH: 3,
            HappyLinesSignal.SELL: 4,
            HappyLinesSignal.STRONG_SELL: 5,
        }
        strategy_results.sort(key=lambda x: (signal_priority.get(x.signal, 99), x.position_ratio))

        log.info(f"Screening complete: {len(strategy_results)} results")

        return strategy_results[:limit]

    async def screen_buy_signals(
        self, universe: list[str] | None = None, limit: int = 20
    ) -> list[HappyLinesStrategyResult]:
        """
        Screen for BUY signals only.

        Parameters
        ----------
        universe : list[str], optional
            Custom list of tickers
        limit : int
            Maximum results

        Returns
        -------
        list[HappyLinesStrategyResult]
            Stocks with BUY or STRONG_BUY signal
        """
        results = await self.screen(universe=universe, limit=limit * 2, include_watchlist=False)
        buy_signals = [
            r for r in results if r.signal in [HappyLinesSignal.BUY, HappyLinesSignal.STRONG_BUY]
        ]
        return buy_signals[:limit]

    async def screen_sell_signals(
        self, universe: list[str] | None = None, limit: int = 20
    ) -> list[HappyLinesStrategyResult]:
        """
        Screen for SELL signals only.

        Parameters
        ----------
        universe : list[str], optional
            Custom list of tickers (e.g., current holdings)
        limit : int
            Maximum results

        Returns
        -------
        list[HappyLinesStrategyResult]
            Stocks with SELL or STRONG_SELL signal
        """
        results = await self.screen(universe=universe, limit=limit * 2, include_watchlist=True)
        sell_signals = [
            r for r in results if r.signal in [HappyLinesSignal.SELL, HappyLinesSignal.STRONG_SELL]
        ]
        return sell_signals[:limit]

    async def screen_oversold(
        self, universe: list[str] | None = None, limit: int = 20
    ) -> list[HappyLinesStrategyResult]:
        """
        Screen for oversold stocks (Line 1-2).

        Parameters
        ----------
        universe : list[str], optional
            Custom list of tickers
        limit : int
            Maximum results

        Returns
        -------
        list[HappyLinesStrategyResult]
            Stocks in oversold or undervalued zones
        """
        results = await self.screen(universe=universe, limit=limit * 2, include_watchlist=True)
        oversold = [r for r in results if r.zone in [HappyZone.OVERSOLD, HappyZone.UNDERVALUED]]
        return oversold[:limit]

    async def screen_overbought(
        self, universe: list[str] | None = None, limit: int = 20
    ) -> list[HappyLinesStrategyResult]:
        """
        Screen for overbought stocks (Line 4-5).

        Parameters
        ----------
        universe : list[str], optional
            Custom list of tickers
        limit : int
            Maximum results

        Returns
        -------
        list[HappyLinesStrategyResult]
            Stocks in overvalued or overbought zones
        """
        results = await self.screen(universe=universe, limit=limit * 2, include_watchlist=True)
        overbought = [r for r in results if r.zone in [HappyZone.OVERVALUED, HappyZone.OVERBOUGHT]]
        return overbought[:limit]

    def get_strategy_summary(self) -> dict[str, Any]:
        """Get strategy configuration summary."""
        return {
            "strategy": "Happy Lines (樂活五線譜)",
            "version": "1.0.0",
            "parameters": {
                "period": self.period,
                "min_avg_volume": self.min_avg_volume,
            },
            "five_lines": {
                "line_5": f"過熱線 (中軌 + 2σ) - 考慮減碼/停利",
                "line_4": f"偏高線 (中軌 + 1σ) - 分批獲利",
                "line_3": f"平衡線 (中軌, {self.period}日移動平均) - 觀望",
                "line_2": f"偏低線 (中軌 - 1σ) - 分批布局",
                "line_1": f"超跌線 (中軌 - 2σ) - 考慮進場/加碼",
            },
            "buy_conditions": [
                f"股價處於超跌區 (<= 第1線) 或偏低區 (<= 第2線)",
                f"趨勢為多頭或盤整",
                f"日均成交量 >= {self.min_avg_volume:,} 股",
            ],
            "sell_conditions": [
                "股價突破過熱區 (>= 第5線)",
                "或股價跌破平衡線且趨勢轉空",
            ],
            "period_options": self.VALID_PERIODS,
        }


# Convenience function for quick screening
async def screen_happy_lines(
    universe: list[str] | None = None,
    limit: int = 20,
    period: int = 60,
    buy_signals_only: bool = True,
) -> list[HappyLinesStrategyResult]:
    """
    Quick screen for Happy Lines opportunities.

    Parameters
    ----------
    universe : list[str], optional
        Stock universe to screen
    limit : int
        Maximum results
    period : int
        Calculation period (20, 60, 120, 240)
    buy_signals_only : bool
        Only return BUY signals (default: True)

    Returns
    -------
    list[HappyLinesStrategyResult]
        Screened stocks
    """
    strategy = HappyLinesStrategy(period=period)

    if buy_signals_only:
        return await strategy.screen_buy_signals(universe=universe, limit=limit)
    else:
        return await strategy.screen(universe=universe, limit=limit, include_watchlist=True)
