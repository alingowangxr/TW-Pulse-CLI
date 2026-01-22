"""
Keltner Channel Strategy - Short-term Breakout Trading

策略說明 (Strategy Description)
================================

【策略邏輯】
肯特納通道 (Keltner Channel) 是一種波動性通道指標，由 Chester Keltner 在 1960 年代開發。
它使用 EMA 作為中軌，ATR 的倍數作為上下軌，與布林通道相比對價格變動的反應更平滑。

【策略條件】
1. 買進條件 (Buy Signal):
   - 收盤價剛站上肯特納上軌 (close >= kc_upper)
   - EMA 多頭排列 (EMA 9 > EMA 21 > EMA 55)
   - 日均成交量 >= 3,000,000 股 (排除冷門股)

2. 持有條件 (Hold Signal):
   - 收盤價位於肯特納上軌之上
   - 或收盤價位於肯特納中軌之上 (保守持有)

3. 賣出條件 (Sell Signal):
   - 收盤價跌破肯特納上軌
   - 或收盤價跌破肯特納中軌 (保守止損)

【換股頻率】
- 短線操作：兩週檢視一次 (Bi-weekly rebalancing)
- 適合波段行情，不適合當日沖銷

【風險控制】
- 排除日均成交量過小標的 (成交量濾網)
- EMA 多頭排列作為趨勢確認
- 與布林通道配合確認突破有效性

【優勢】
- 順勢交易，追蹤趨勢
- 濾除噪音，減少假突破
- 明確的進場/出场規則

【劣勢】
- 盤整市場可能產生假信號
- 參數 (EMA 週期、ATR 倍數) 需要優化
- 趨勢反轉時可能造成較大虧損

作者: Pulse-CLI
版本: 1.0.0
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from pulse.core.screener import ScreenResult, StockScreener
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class KeltnerStrategySignal(str, Enum):
    """Keltner Channel Strategy Signal Types."""

    BUY = "BUY"  # 買進信號 - 剛突破上軌
    HOLD = "HOLD"  # 持有信號 - 價格在通道內/上軌之上
    SELL = "SELL"  # 賣出信號 - 跌破上軌或中軌
    WATCH = "WATCH"  # 觀察名單 - 接近上軌但未突破


@dataclass
class KeltnerStrategyResult:
    """Keltner Channel Strategy Screening Result."""

    ticker: str
    name: str | None = None
    signal: KeltnerStrategySignal = KeltnerStrategySignal.WATCH

    # Price Data
    price: float = 0.0
    change_percent: float = 0.0
    volume: int = 0
    avg_volume: int = 0

    # Keltner Channel Data
    kc_middle: float | None = None  # EMA (20)
    kc_upper: float | None = None  # EMA + 2*ATR
    kc_lower: float | None = None  # EMA - 2*ATR
    kc_position: float | None = None  # Price position relative to KC (%)

    # EMA Data for Trend Confirmation
    ema_9: float | None = None
    ema_21: float | None = None
    ema_55: float | None = None
    ema_alignment: str = "NEUTRAL"  # BULLISH, NEUTRAL, BEARISH

    # Additional Indicators for Confirmation
    rsi_14: float | None = None
    macd: float | None = None
    macd_signal: float | None = None

    # Strategy Metrics
    distance_to_upper: float = 0.0  # % distance to upper band
    distance_to_middle: float = 0.0  # % distance to middle band
    volatility_score: float = 0.0  # Based on ATR

    # Metadata
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
        return self.avg_volume >= 3_000_000

    @property
    def is_ema_bullish(self) -> bool:
        """Check if EMA is in bullish alignment."""
        if all(v is not None for v in [self.ema_9, self.ema_21, self.ema_55]):
            return self.ema_9 > self.ema_21 > self.ema_55
        return False

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
            "kc_middle": self.kc_middle,
            "kc_upper": self.kc_upper,
            "kc_lower": self.kc_lower,
            "kc_position": self.kc_position,
            "ema_9": self.ema_9,
            "ema_21": self.ema_21,
            "ema_55": self.ema_55,
            "ema_alignment": self.ema_alignment,
            "rsi_14": self.rsi_14,
            "macd": self.macd,
            "macd_signal": self.macd_signal,
            "distance_to_upper": self.distance_to_upper,
            "distance_to_middle": self.distance_to_middle,
            "volatility_score": self.volatility_score,
            "is_liquid": self.is_liquid,
            "is_ema_bullish": self.is_ema_bullish,
            "notes": self.notes,
        }


class KeltnerChannelStrategy:
    """
    Keltner Channel Breakout Strategy for Short-term Trading.

    Parameters
    ----------
    min_avg_volume : int
        Minimum average daily volume (default: 3,000,000)
    ema_periods : tuple
        EMA periods for alignment check (default: (9, 21, 55))
    atr_multiplier : float
        ATR multiplier for channel bands (default: 2.0)
    atr_period : int
        ATR period (default: 10)
    rebalance_frequency : str
        Rebalance frequency (default: "biweekly")

    Usage
    -----
    >>> strategy = KeltnerChannelStrategy()
    >>> results = await strategy.screen()
    >>> for r in results:
    ...     print(f"{r.ticker}: {r.signal.value} @ {r.price}")
    """

    # Strategy Parameters
    DEFAULT_MIN_AVG_VOLUME = 3_000_000  # 300萬股
    DEFAULT_EMA_PERIODS = (9, 21, 55)
    DEFAULT_ATR_MULTIPLIER = 2.0
    DEFAULT_ATR_PERIOD = 10
    DEFAULT_REBALANCE_FREQUENCY = "biweekly"  # biweekly, weekly, monthly

    def __init__(
        self,
        min_avg_volume: int | None = None,
        ema_periods: tuple[int, int, int] | None = None,
        atr_multiplier: float | None = None,
        atr_period: int | None = None,
        rebalance_frequency: str | None = None,
    ):
        """Initialize Keltner Channel Strategy."""
        self.min_avg_volume = min_avg_volume or self.DEFAULT_MIN_AVG_VOLUME
        self.ema_periods = ema_periods or self.DEFAULT_EMA_PERIODS
        self.atr_multiplier = atr_multiplier or self.DEFAULT_ATR_MULTIPLIER
        self.atr_period = atr_period or self.DEFAULT_ATR_PERIOD
        self.rebalance_frequency = rebalance_frequency or self.DEFAULT_REBALANCE_FREQUENCY

        self.screener = StockScreener()
        log.info(f"Initialized Keltner Channel Strategy (min_vol={self.min_avg_volume:,})")

    def _determine_signal(
        self,
        result: ScreenResult,
    ) -> tuple[KeltnerStrategySignal, list[str]]:
        """
        Determine Keltner Channel strategy signal.

        Logic:
        - BUY: Price >= KC Upper AND EMA bullish AND Liquid
        - HOLD: Price between KC Middle and KC Upper
        - SELL: Price < KC Middle (conservative) OR Price < KC Upper (aggressive)
        - WATCH: Price approaching KC Upper
        """
        signals = []
        notes = []

        # Check if we have Keltner Channel data
        if not all([result.kc_upper, result.kc_middle, result.kc_lower]):
            return KeltnerStrategySignal.WATCH, ["Missing KC data"]

        price = result.price
        kc_upper = result.kc_upper
        kc_middle = result.kc_middle
        kc_lower = result.kc_lower

        # Calculate price position relative to KC
        if kc_upper != kc_lower:
            kc_position = ((price - kc_lower) / (kc_upper - kc_lower)) * 100
        else:
            kc_position = 50.0

        # Calculate distances
        dist_to_upper = ((kc_upper - price) / price) * 100 if price > 0 else 0
        dist_to_middle = ((price - kc_middle) / price) * 100 if price > 0 else 0

        # Liquidity Check
        if result.avg_volume < self.min_avg_volume:
            return KeltnerStrategySignal.WATCH, ["低成交量"]

        # EMA Alignment Check
        ema_bullish = (
            result.ema_9
            and result.ema_21
            and result.ema_55
            and result.ema_9 > result.ema_21 > result.ema_55
        )

        # Signal Determination
        if price >= kc_upper:
            # BUY: Price broke above upper band
            if ema_bullish:
                signals.append("BUY")
                notes.append(f"突破上軌 ({kc_upper:.1f})")
                notes.append(f"EMA 多頭排列")
            else:
                signals.append("HOLD")
                notes.append(f"突破上軌，但 EMA 尚未多頭")

        elif kc_middle <= price < kc_upper:
            # HOLD: Price between middle and upper
            signals.append("HOLD")
            notes.append(f"價格在通道內 ({kc_middle:.1f} - {kc_upper:.1f})")

        elif price < kc_middle:
            # SELL: Price below middle band (conservative exit)
            signals.append("SELL")
            notes.append(f"跌破中軌 ({kc_middle:.1f})")

        else:
            # WATCH: Approaching upper band
            signals.append("WATCH")
            notes.append(f"接近上軌 ({dist_to_upper:.1f}% below)")

        # Additional confirmation signals
        if result.rsi_14:
            if result.rsi_14 > 70:
                notes.append(f"RSI 過熱 ({result.rsi_14:.0f})")
            elif result.rsi_14 < 30:
                notes.append(f"RSI 超賣 ({result.rsi_14:.0f})")

        if result.macd and result.macd_signal:
            if result.macd > result.macd_signal:
                notes.append("MACD 偏多")
            else:
                notes.append("MACD 偏空")

        return KeltnerStrategySignal(signals[0]) if signals else KeltnerStrategySignal.WATCH, notes

    def _calculate_ema_alignment(self, result: ScreenResult) -> str:
        """Calculate EMA alignment status."""
        if not all([result.ema_9, result.ema_21, result.ema_55]):
            return "N/A"

        if result.ema_9 > result.ema_21 > result.ema_55:
            return "BULLISH"
        elif result.ema_9 < result.ema_21 < result.ema_55:
            return "BEARISH"
        else:
            return "NEUTRAL"

    async def screen(
        self,
        universe: list[str] | None = None,
        limit: int = 20,
        include_watchlist: bool = False,
    ) -> list[KeltnerStrategyResult]:
        """
        Screen stocks using Keltner Channel strategy.

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
        list[KeltnerStrategyResult]
            List of screened stocks with signals and metrics
        """
        log.info("Starting Keltner Channel strategy screening...")

        # Use custom universe or default
        if universe:
            self.screener.universe = universe

        # Screen for stocks with Keltner Channel data
        try:
            results = await self.screener._run_screen(
                criteria={
                    "kc_upper": ("exists", True),  # Has KC upper band
                    "volume_min": self.min_avg_volume,
                },
                sort_by="kc_position",
                sort_asc=False,
                limit=100,  # Get more to filter
                show_progress=True,
            )
        except Exception as e:
            log.error(f"Error during screening: {e}")
            return []

        # Process results
        strategy_results: list[KeltnerStrategyResult] = []

        for result in results:
            if not result:
                continue

            signal, notes = self._determine_signal(result)

            # Filter based on include_watchlist
            if signal == KeltnerStrategySignal.WATCH and not include_watchlist:
                continue

            # Calculate additional metrics
            kc_position = None
            if result.kc_upper and result.kc_lower:
                if result.kc_upper != result.kc_lower:
                    kc_position = (
                        (result.price - result.kc_lower) / (result.kc_upper - result.kc_lower)
                    ) * 100

            dist_to_upper = 0.0
            dist_to_middle = 0.0
            if result.kc_upper and result.price > 0:
                dist_to_upper = ((result.kc_upper - result.price) / result.price) * 100
            if result.kc_middle and result.price > 0:
                dist_to_middle = ((result.price - result.kc_middle) / result.price) * 100

            strategy_result = KeltnerStrategyResult(
                ticker=result.ticker,
                name=result.name,
                signal=signal,
                price=result.price,
                change_percent=result.change_percent,
                volume=result.volume,
                avg_volume=result.avg_volume,
                kc_middle=result.kc_middle,
                kc_upper=result.kc_upper,
                kc_lower=result.kc_lower,
                kc_position=kc_position,
                ema_9=result.ema_9,
                ema_21=result.ema_21,
                ema_55=result.ema_55,
                ema_alignment=self._calculate_ema_alignment(result),
                rsi_14=result.rsi_14,
                macd=result.macd,
                macd_signal=result.macd_signal,
                distance_to_upper=dist_to_upper,
                distance_to_middle=dist_to_middle,
                volatility_score=result.atr_14 or 0.0,
                notes=notes,
            )

            strategy_results.append(strategy_result)

        # Sort by signal priority (BUY > HOLD > WATCH > SELL)
        signal_priority = {
            KeltnerStrategySignal.BUY: 0,
            KeltnerStrategySignal.HOLD: 1,
            KeltnerStrategySignal.WATCH: 2,
            KeltnerStrategySignal.SELL: 3,
        }
        strategy_results.sort(
            key=lambda x: (signal_priority.get(x.signal, 99), -x.distance_to_upper)
        )

        log.info(f"Screening complete: {len(strategy_results)} results")

        return strategy_results[:limit]

    async def screen_buy_signals(
        self, universe: list[str] | None = None, limit: int = 20
    ) -> list[KeltnerStrategyResult]:
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
        list[KeltnerStrategyResult]
            Stocks with BUY signal
        """
        results = await self.screen(universe=universe, limit=limit * 2, include_watchlist=False)
        buy_signals = [r for r in results if r.signal == KeltnerStrategySignal.BUY]
        return buy_signals[:limit]

    async def screen_hold_signals(
        self, universe: list[str] | None = None, limit: int = 20
    ) -> list[KeltnerStrategyResult]:
        """
        Screen for HOLD signals (for portfolio review).

        Parameters
        ----------
        universe : list[str], optional
            Custom list of tickers (e.g., current holdings)
        limit : int
            Maximum results

        Returns
        -------
        list[KeltnerStrategyResult]
            Stocks with HOLD signal
        """
        results = await self.screen(universe=universe, limit=limit * 2, include_watchlist=True)
        hold_signals = [
            r
            for r in results
            if r.signal in [KeltnerStrategySignal.BUY, KeltnerStrategySignal.HOLD]
        ]
        return hold_signals[:limit]

    async def screen_sell_signals(
        self, universe: list[str] | None = None, limit: int = 20
    ) -> list[KeltnerStrategyResult]:
        """
        Screen for SELL signals (for portfolio review).

        Parameters
        ----------
        universe : list[str], optional
            Custom list of tickers (e.g., current holdings)
        limit : int
            Maximum results

        Returns
        -------
        list[KeltnerStrategyResult]
            Stocks with SELL signal
        """
        results = await self.screen(universe=universe, limit=limit * 2, include_watchlist=True)
        sell_signals = [r for r in results if r.signal == KeltnerStrategySignal.SELL]
        return sell_signals[:limit]

    def get_strategy_summary(self) -> dict[str, Any]:
        """Get strategy configuration summary."""
        return {
            "strategy": "Keltner Channel Breakout",
            "version": "1.0.0",
            "parameters": {
                "min_avg_volume": self.min_avg_volume,
                "ema_periods": self.ema_periods,
                "atr_multiplier": self.atr_multiplier,
                "atr_period": self.atr_period,
                "rebalance_frequency": self.rebalance_frequency,
            },
            "buy_conditions": [
                "收盤價 >= 肯特納上軌 (kc_upper)",
                f"EMA 多頭排列 (EMA {self.ema_periods[0]} > EMA {self.ema_periods[1]} > EMA {self.ema_periods[2]})",
                f"日均成交量 >= {self.min_avg_volume:,} 股",
            ],
            "hold_conditions": [
                "收盤價在肯特納中軌與上軌之間",
                "或收盤價維持在肯特納上軌之上",
            ],
            "sell_conditions": [
                "收盤價跌破肯特納中軌 (保守止損)",
                "或收盤價跌破肯特納上軌 (積極止損)",
            ],
            "rebalance_frequency": self.rebalance_frequency,
        }


# Convenience function for quick screening
async def screen_keltner_breakout(
    universe: list[str] | None = None,
    limit: int = 20,
    buy_signals_only: bool = True,
) -> list[KeltnerStrategyResult]:
    """
    Quick screen for Keltner Channel breakout opportunities.

    Parameters
    ----------
    universe : list[str], optional
        Stock universe to screen
    limit : int
        Maximum results
    buy_signals_only : bool
        Only return BUY signals (default: True)

    Returns
    -------
    list[KeltnerStrategyResult]
        Screened stocks
    """
    strategy = KeltnerChannelStrategy()

    if buy_signals_only:
        return await strategy.screen_buy_signals(universe=universe, limit=limit)
    else:
        return await strategy.screen(universe=universe, limit=limit, include_watchlist=True)
