"""Technical analysis engine."""

from datetime import datetime

import pandas as pd

try:
    from ta.momentum import RSIIndicator, StochasticOscillator
    from ta.trend import MACD, EMAIndicator, SMAIndicator
    from ta.volatility import AverageTrueRange, BollingerBands
    from ta.volume import MFIIndicator, OnBalanceVolumeIndicator

    HAS_TA = True
except ImportError:
    HAS_TA = False

from pulse.core.config import settings
from pulse.core.data.stock_data_provider import StockDataProvider
from pulse.core.models import (
    HappyLinesIndicators,
    HappyZone,
    SignalType,
    TechnicalIndicators,
    TrendType,
)
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class TechnicalAnalyzer:
    """Technical analysis engine using ta library."""

    def __init__(self):
        """Initialize technical analyzer."""
        self.fetcher = StockDataProvider()
        self.settings = settings.analysis

    async def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame | None:
        """
        Calculate technical indicators for entire DataFrame (for backtest).

        Args:
            df: DataFrame with OHLCV data

        Returns:
            DataFrame with added technical indicator columns
        """
        if not HAS_TA:
            log.error("ta library not installed. Run: pip install ta")
            return None

        try:
            df = df.copy()

            # Ensure column names are lowercase
            df.columns = df.columns.str.lower()

            close = df["close"]
            high = df["high"]
            low = df["low"]
            volume = df["volume"]

            # Calculate indicators
            # RSI
            rsi = RSIIndicator(close, window=14)
            df["RSI_14"] = rsi.rsi()

            # Moving Averages
            df["MA_50"] = SMAIndicator(close, window=50).sma_indicator()
            df["MA_200"] = SMAIndicator(close, window=200).sma_indicator()

            # MACD
            macd = MACD(close)
            df["MACD"] = macd.macd()
            df["MACD_signal"] = macd.macd_signal()
            df["MACD_hist"] = macd.macd_diff()

            # Bollinger Bands
            bb = BollingerBands(close, window=20, window_dev=2)
            df["BB_upper"] = bb.bollinger_hband()
            df["BB_middle"] = bb.bollinger_mavg()
            df["BB_lower"] = bb.bollinger_lband()

            # ATR
            atr = AverageTrueRange(high, low, close, window=14)
            df["ATR"] = atr.average_true_range()

            # EMA for crossover strategies
            df["EMA_9"] = EMAIndicator(close, window=9).ema_indicator()
            df["EMA_21"] = EMAIndicator(close, window=21).ema_indicator()

            # MA_20 for strategies
            df["MA_20"] = SMAIndicator(close, window=20).sma_indicator()

            # Volume SMA for volume confirmation
            df["Volume_SMA_20"] = SMAIndicator(volume.astype(float), window=20).sma_indicator()

            # ADX (Average Directional Index)
            df["ADX"] = self._calculate_adx_series(high, low, close, n=14)

            # Bollinger Band width for squeeze detection
            df["BB_width"] = bb.bollinger_wband()

            return df

        except Exception as e:
            log.error(f"Error calculating indicators: {e}")
            return None

    async def analyze(
        self,
        ticker: str,
        period: str = "1y",
    ) -> TechnicalIndicators | None:
        """
        Perform full technical analysis on a stock.

        Args:
            ticker: Stock ticker
            period: Historical data period

        Returns:
            TechnicalIndicators object or None
        """
        if not HAS_TA:
            log.error("ta library not installed. Run: pip install ta")
            return None

        from datetime import datetime, timedelta

        # Define date range for fetching data (e.g., 1 year history)
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        # Get historical data
        df = await self.fetcher.fetch_history(
            ticker, period, start_date=start_date_str, end_date=end_date_str
        )

        if df is None or df.empty:
            log.warning(f"No data available for {ticker}")
            return None

        try:
            return self._calculate_indicators(ticker, df)
        except Exception as e:
            log.error(f"Error calculating indicators for {ticker}: {e}")
            return None

    def _calculate_indicators(
        self,
        ticker: str,
        df: pd.DataFrame,
    ) -> TechnicalIndicators:
        """Calculate all technical indicators."""
        # Ensure we have the required columns
        df = df.copy()

        # Get latest values
        close = df["close"]
        high = df["high"]
        low = df["low"]
        volume = df["volume"]

        latest_close = float(close.iloc[-1])

        # === Trend Indicators ===

        # SMA
        sma_20 = SMAIndicator(close, window=20).sma_indicator().iloc[-1]
        sma_50 = SMAIndicator(close, window=50).sma_indicator().iloc[-1]
        sma_200 = (
            SMAIndicator(close, window=200).sma_indicator().iloc[-1] if len(df) >= 200 else None
        )

        # EMA
        ema_9 = EMAIndicator(close, window=9).ema_indicator().iloc[-1]
        ema_21 = EMAIndicator(close, window=21).ema_indicator().iloc[-1]
        ema_55 = EMAIndicator(close, window=55).ema_indicator().iloc[-1] if len(df) >= 55 else None

        # === Momentum Indicators ===

        # RSI
        rsi = RSIIndicator(close, window=14)
        rsi_14 = float(rsi.rsi().iloc[-1])

        # MACD
        macd_indicator = MACD(close)
        macd_val = float(macd_indicator.macd().iloc[-1])
        macd_signal = float(macd_indicator.macd_signal().iloc[-1])
        macd_histogram = float(macd_indicator.macd_diff().iloc[-1])

        # Stochastic
        stoch = StochasticOscillator(high, low, close)
        stoch_k = float(stoch.stoch().iloc[-1])
        stoch_d = float(stoch.stoch_signal().iloc[-1])

        # === Volatility Indicators ===

        # Bollinger Bands
        bb = BollingerBands(close, window=20, window_dev=2)
        bb_upper = float(bb.bollinger_hband().iloc[-1])
        bb_middle = float(bb.bollinger_mavg().iloc[-1])
        bb_lower = float(bb.bollinger_lband().iloc[-1])
        bb_width = float(bb.bollinger_wband().iloc[-1])

        # ATR
        atr = AverageTrueRange(high, low, close, window=14)
        atr_14 = float(atr.average_true_range().iloc[-1])

        # Keltner Channel
        kc_middle, kc_upper, kc_lower = self._calculate_keltner_channel(close, high, low)

        # === Volume Indicators ===

        # OBV
        obv = OnBalanceVolumeIndicator(close, volume)
        obv_val = float(obv.on_balance_volume().iloc[-1])

        # MFI
        mfi = MFIIndicator(high, low, close, volume, window=14)
        mfi_14 = float(mfi.money_flow_index().iloc[-1])

        # === Advanced Momentum Indicators ===

        # ADX (Average Directional Index) - Manual implementation
        adx_val, adx_pos, adx_neg = self._calculate_adx(high, low, close, n=14)

        # CCI (Commodity Channel Index) - Manual implementation
        cci_val = self._calculate_cci(high, low, close, n=20)

        # Ichimoku Cloud (一目均衡表)
        ichimoku = self._calculate_ichimoku(df)

        # Volume SMA
        volume_sma = SMAIndicator(volume.astype(float), window=20).sma_indicator().iloc[-1]

        # === Support/Resistance ===
        support_1, support_2, resistance_1, resistance_2 = self._calculate_support_resistance(df)

        # === Determine Trend and Signal ===
        trend = self._determine_trend(latest_close, sma_20, sma_50, sma_200, ema_9, ema_21)
        signal = self._determine_signal(
            rsi_14, macd_val, macd_signal, stoch_k, stoch_d, latest_close, bb_upper, bb_lower, trend
        )

        return TechnicalIndicators(
            ticker=ticker,
            calculated_at=datetime.now(),
            sma_20=float(sma_20) if pd.notna(sma_20) else None,
            sma_50=float(sma_50) if pd.notna(sma_50) else None,
            sma_200=float(sma_200) if sma_200 and pd.notna(sma_200) else None,
            ema_9=float(ema_9) if pd.notna(ema_9) else None,
            ema_21=float(ema_21) if pd.notna(ema_21) else None,
            ema_55=float(ema_55) if ema_55 and pd.notna(ema_55) else None,
            rsi_14=rsi_14,
            macd=macd_val,
            macd_signal=macd_signal,
            macd_histogram=macd_histogram,
            stoch_k=stoch_k,
            stoch_d=stoch_d,
            bb_upper=bb_upper,
            bb_middle=bb_middle,
            bb_lower=bb_lower,
            bb_width=bb_width,
            atr_14=atr_14,
            # Keltner Channel
            kc_middle=kc_middle,
            kc_upper=kc_upper,
            kc_lower=kc_lower,
            obv=obv_val,
            mfi_14=mfi_14,
            volume_sma_20=float(volume_sma) if pd.notna(volume_sma) else None,
            # Advanced momentum indicators
            adx=adx_val,
            adx_pos=adx_pos,
            adx_neg=adx_neg,
            cci=cci_val,
            # Ichimoku Cloud
            ichimoku_tenkan=ichimoku.get("tenkan"),
            ichimoku_kijun=ichimoku.get("kijun"),
            ichimoku_senkou_a=ichimoku.get("senkou_a"),
            ichimoku_senkou_b=ichimoku.get("senkou_b"),
            ichimoku_chikou=ichimoku.get("chikou"),
            support_1=support_1,
            support_2=support_2,
            resistance_1=resistance_1,
            resistance_2=resistance_2,
            trend=trend,
            signal=signal,
        )

    def _calculate_support_resistance(
        self,
        df: pd.DataFrame,
        window: int = 20,
    ) -> tuple:
        """Calculate support and resistance levels using pivot points."""
        recent = df.tail(window)

        high = recent["high"].max()
        low = recent["low"].min()
        close = recent["close"].iloc[-1]

        # Pivot point
        pivot = (high + low + close) / 3

        # Support levels
        support_1 = (2 * pivot) - high
        support_2 = pivot - (high - low)

        # Resistance levels
        resistance_1 = (2 * pivot) - low
        resistance_2 = pivot + (high - low)

        return (
            float(support_1),
            float(support_2),
            float(resistance_1),
            float(resistance_2),
        )

    def _calculate_ichimoku(self, df: pd.DataFrame) -> dict[str, float | None]:
        """
        Calculate Ichimoku Cloud (一目均衡表) indicators.

        Tenkan-sen (Conversion Line): (Highest High + Lowest Low) / 2 for 9 periods
        Kijun-sen (Base Line): (Highest High + Lowest Low) / 2 for 26 periods
        Senkou Span A (Leading Span A): (Tenkan + Kijun) / 2, plotted 26 periods ahead
        Senkou Span B (Leading Span B): (Highest High + Lowest Low) / 2 for 52 periods, plotted 26 ahead
        Chikou Span (Lagging Span): Close plotted 26 periods behind

        Returns:
            Dictionary with tenkan, kijun, senkou_a, senkou_b, chikou
        """
        high = df["high"]
        low = df["low"]
        close = df["close"]

        # Need sufficient data for Ichimoku calculations (at least 52 periods)
        # Senkou Span A/B are plotted 26 periods ahead

        try:
            # Tenkan-sen (Conversion Line) - 9 periods
            tenkan_high = high.rolling(window=9).max()
            tenkan_low = low.rolling(window=9).min()
            tenkan = (tenkan_high + tenkan_low) / 2

            # Kijun-sen (Base Line) - 26 periods
            kijun_high = high.rolling(window=26).max()
            kijun_low = low.rolling(window=26).min()
            kijun = (kijun_high + kijun_low) / 2

            # Senkou Span B (Leading Span B) - 52 periods
            senkou_b_high = high.rolling(window=52).max()
            senkou_b_low = low.rolling(window=52).min()
            senkou_b = (senkou_b_high + senkou_b_low) / 2

            # Senkou Span A (Leading Span A) - plotted 26 periods ahead
            senkou_a = (tenkan + kijun) / 2

            # Get latest values (shifted 26 periods ahead for leading indicators)
            latest_tenkan = float(tenkan.iloc[-1]) if len(tenkan) > 0 else None
            latest_kijun = float(kijun.iloc[-1]) if len(kijun) > 0 else None
            latest_senkou_a = float(senkou_a.iloc[-26]) if len(senkou_a) > 26 else None
            latest_senkou_b = float(senkou_b.iloc[-26]) if len(senkou_b) > 26 else None
            latest_chikou = float(close.iloc[-26]) if len(close) > 26 else None

            return {
                "tenkan": latest_tenkan,
                "kijun": latest_kijun,
                "senkou_a": latest_senkou_a,
                "senkou_b": latest_senkou_b,
                "chikou": latest_chikou,
            }
        except Exception:
            return {
                "tenkan": None,
                "kijun": None,
                "senkou_a": None,
                "senkou_b": None,
                "chikou": None,
            }

    def _calculate_adx_series(
        self, high: pd.Series, low: pd.Series, close: pd.Series, n: int = 14
    ) -> pd.Series:
        """
        Calculate ADX (Average Directional Index) as a Series for backtesting.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            n: Period for calculation

        Returns:
            ADX Series
        """
        try:
            # Calculate True Range (TR)
            prev_close = close.shift(1)
            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

            # Calculate +DM and -DM
            plus_dm = high.diff()
            minus_dm = -low.diff()

            # Only consider positive values for +DM, negative for -DM
            plus_dm = plus_dm.where(plus_dm > minus_dm, 0)
            plus_dm = plus_dm.where(plus_dm > 0, 0)
            minus_dm = minus_dm.where(minus_dm > plus_dm, 0)
            minus_dm = minus_dm.where(minus_dm > 0, 0)

            # Smooth using rolling mean
            atr = tr.rolling(window=n).mean()
            plus_di = (plus_dm.rolling(window=n).mean() / atr) * 100
            minus_di = (minus_dm.rolling(window=n).mean() / atr) * 100

            # Calculate DX
            dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100

            # Calculate ADX (smoothed DX)
            adx = dx.rolling(window=n).mean()

            return adx
        except Exception:
            return pd.Series([None] * len(high), index=high.index)

    def _calculate_adx(
        self, high: pd.Series, low: pd.Series, close: pd.Series, n: int = 14
    ) -> tuple[float | None, float | None, float | None]:
        """
        Calculate ADX (Average Directional Index) and +/- DI.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            n: Period for calculation

        Returns:
            Tuple of (adx, plus_di, minus_di)
        """
        try:
            # Calculate True Range (TR)
            prev_close = close.shift(1)
            tr1 = high - low
            tr2 = abs(high - prev_close)
            tr3 = abs(low - prev_close)
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

            # Calculate +DM and -DM
            plus_dm = high.diff()
            minus_dm = -low.diff()

            # Only consider positive values for +DM, negative for -DM
            plus_dm = plus_dm.where(plus_dm > minus_dm, 0)
            plus_dm = plus_dm.where(plus_dm > 0, 0)
            minus_dm = minus_dm.where(minus_dm > plus_dm, 0)
            minus_dm = minus_dm.where(minus_dm > 0, 0)

            # Smooth using rolling mean
            atr = tr.rolling(window=n).mean()
            plus_di = (plus_dm.rolling(window=n).mean() / atr) * 100
            minus_di = (minus_dm.rolling(window=n).mean() / atr) * 100

            # Calculate DX
            dx = (abs(plus_di - minus_di) / (plus_di + minus_di)) * 100

            # Calculate ADX (smoothed DX)
            adx = dx.rolling(window=n).mean()

            return (
                float(adx.iloc[-1]) if len(adx) > 0 and not pd.isna(adx.iloc[-1]) else None,
                float(plus_di.iloc[-1])
                if len(plus_di) > 0 and not pd.isna(plus_di.iloc[-1])
                else None,
                float(minus_di.iloc[-1])
                if len(minus_di) > 0 and not pd.isna(minus_di.iloc[-1])
                else None,
            )
        except Exception:
            return None, None, None

    def _calculate_cci(
        self, high: pd.Series, low: pd.Series, close: pd.Series, n: int = 20
    ) -> float | None:
        """
        Calculate CCI (Commodity Channel Index).

        CCI = (Typical Price - SMA of TP) / (0.015 * Mean Deviation)

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            n: Period for calculation

        Returns:
            CCI value or None
        """
        try:
            # Typical Price
            tp = (high + low + close) / 3

            # SMA of Typical Price
            tp_sma = tp.rolling(window=n).mean()

            # Mean Deviation
            mean_dev = tp.rolling(window=n).apply(lambda x: abs(x - x.mean()).mean(), raw=True)

            # CCI
            cci = (tp - tp_sma) / (0.015 * mean_dev)

            return float(cci.iloc[-1]) if len(cci) > 0 and not pd.isna(cci.iloc[-1]) else None
        except Exception:
            return None

    def _calculate_keltner_channel(
        self,
        close: pd.Series,
        high: pd.Series,
        low: pd.Series,
        ema_period: int = 20,
        atr_period: int = 10,
        atr_multiplier: float = 2.0,
    ) -> tuple[float | None, float | None, float | None]:
        """
        Calculate Keltner Channel indicators.

        Keltner Channel consists of:
        - Middle Line: EMA of close price
        - Upper Band: EMA + (ATR * multiplier)
        - Lower Band: EMA - (ATR * multiplier)

        Args:
            close: Close prices
            high: High prices
            low: Low prices
            ema_period: Period for EMA (default 20)
            atr_period: Period for ATR (default 10)
            atr_multiplier: ATR multiplier for bands (default 2.0)

        Returns:
            Tuple of (kc_middle, kc_upper, kc_lower)
        """
        try:
            # Calculate EMA for middle band
            ema = EMAIndicator(close, window=ema_period)
            kc_middle = float(ema.ema_indicator().iloc[-1])

            # Calculate ATR for band width
            atr = AverageTrueRange(high, low, close, window=atr_period)
            atr_value = atr.average_true_range()

            # Calculate upper and lower bands
            kc_upper = kc_middle + (atr_value.iloc[-1] * atr_multiplier)
            kc_lower = kc_middle - (atr_value.iloc[-1] * atr_multiplier)

            return (
                float(kc_middle) if kc_middle and not pd.isna(kc_middle) else None,
                float(kc_upper) if not pd.isna(kc_upper) else None,
                float(kc_lower) if not pd.isna(kc_lower) else None,
            )
        except Exception:
            return None, None, None

    def _determine_trend(
        self,
        price: float,
        sma_20: float,
        sma_50: float,
        sma_200: float | None,
        ema_9: float,
        ema_21: float,
    ) -> TrendType:
        """Determine overall trend direction."""
        bullish_signals = 0
        bearish_signals = 0

        # Price vs SMAs
        if price > sma_20:
            bullish_signals += 1
        else:
            bearish_signals += 1

        if price > sma_50:
            bullish_signals += 1
        else:
            bearish_signals += 1

        if sma_200 and price > sma_200:
            bullish_signals += 2  # More weight
        elif sma_200:
            bearish_signals += 2

        # EMA crossover
        if ema_9 > ema_21:
            bullish_signals += 1
        else:
            bearish_signals += 1

        # SMA alignment
        if sma_20 > sma_50:
            bullish_signals += 1
        else:
            bearish_signals += 1

        if bullish_signals >= bearish_signals + 2:
            return TrendType.BULLISH
        elif bearish_signals >= bullish_signals + 2:
            return TrendType.BEARISH
        else:
            return TrendType.SIDEWAYS

    def _determine_signal(
        self,
        rsi: float,
        macd: float,
        macd_signal: float,
        stoch_k: float,
        stoch_d: float,
        price: float,
        bb_upper: float,
        bb_lower: float,
        trend: TrendType,
    ) -> SignalType:
        """Determine trading signal."""
        buy_signals = 0
        sell_signals = 0

        # RSI
        if rsi < 30:
            buy_signals += 2  # Oversold
        elif rsi < 40:
            buy_signals += 1
        elif rsi > 70:
            sell_signals += 2  # Overbought
        elif rsi > 60:
            sell_signals += 1

        # MACD
        if macd > macd_signal:
            buy_signals += 1
        else:
            sell_signals += 1

        # Stochastic
        if stoch_k < 20 and stoch_k > stoch_d:
            buy_signals += 1
        elif stoch_k > 80 and stoch_k < stoch_d:
            sell_signals += 1

        # Bollinger Bands
        if price < bb_lower:
            buy_signals += 1
        elif price > bb_upper:
            sell_signals += 1

        # Trend influence
        if trend == TrendType.BULLISH:
            buy_signals += 1
        elif trend == TrendType.BEARISH:
            sell_signals += 1

        # Determine final signal
        diff = buy_signals - sell_signals

        if diff >= 4:
            return SignalType.STRONG_BUY
        elif diff >= 2:
            return SignalType.BUY
        elif diff <= -4:
            return SignalType.STRONG_SELL
        elif diff <= -2:
            return SignalType.SELL
        else:
            return SignalType.NEUTRAL

    def get_indicator_summary(
        self,
        indicators: TechnicalIndicators,
    ) -> list[dict]:
        """
        Generate human-readable indicator summary.

        Args:
            indicators: TechnicalIndicators object

        Returns:
            List of indicator summaries
        """
        summary = []

        # RSI
        if indicators.rsi_14:
            rsi_status = (
                "Oversold"
                if indicators.rsi_14 < 30
                else "Overbought"
                if indicators.rsi_14 > 70
                else "Neutral"
            )
            summary.append(
                {
                    "name": "RSI (14)",
                    "value": f"{indicators.rsi_14:.2f}",
                    "status": rsi_status,
                }
            )

        # MACD
        if indicators.macd is not None and indicators.macd_signal is not None:
            macd_status = "Bullish" if indicators.macd > indicators.macd_signal else "Bearish"
            summary.append(
                {
                    "name": "MACD",
                    "value": f"{indicators.macd:.2f}",
                    "status": macd_status,
                }
            )

        # Moving Averages
        if indicators.sma_20:
            summary.append(
                {
                    "name": "SMA 20",
                    "value": f"{indicators.sma_20:,.0f}",
                    "status": "",
                }
            )

        if indicators.sma_50:
            summary.append(
                {
                    "name": "SMA 50",
                    "value": f"{indicators.sma_50:,.0f}",
                    "status": "",
                }
            )

        # Bollinger Bands
        if indicators.bb_upper and indicators.bb_lower:
            summary.append(
                {
                    "name": "BB Upper",
                    "value": f"{indicators.bb_upper:,.0f}",
                    "status": "",
                }
            )
            summary.append(
                {
                    "name": "BB Lower",
                    "value": f"{indicators.bb_lower:,.0f}",
                    "status": "",
                }
            )

        # Trend & Signal
        summary.append(
            {
                "name": "Trend",
                "value": indicators.trend.value,
                "status": "",
            }
        )
        summary.append(
            {
                "name": "Signal",
                "value": indicators.signal.value,
                "status": "",
            }
        )

        return summary

    def calculate_happy_lines(
        self,
        df: pd.DataFrame,
        ticker: str,
        period: int = 60,
    ) -> HappyLinesIndicators | None:
        """Calculate Happy Lines (樂活五線譜) indicators.

        五線譜是一種基於統計分佈的股價位階判斷工具：
        - 第3線 (平衡線): N日收盤價的移動平均
        - 第5線 (過熱線): 中軌 + (N日標準差 × 2.0)
        - 第1線 (超跌線): 中軌 - (N日標準差 × 2.0)
        - 第4線 (偏高線): 中軌 + (N日標準差 × 1.0)
        - 第2線 (偏低線): 中軌 - (N日標準差 × 1.0)

        Args:
            df: DataFrame with OHLCV data
            ticker: Stock ticker symbol
            period: Calculation period (default: 60 days)

        Returns:
            HappyLinesIndicators object or None if calculation fails
        """
        try:
            if df is None or df.empty or len(df) < period:
                log.warning(f"Insufficient data for Happy Lines calculation: {ticker}")
                return None

            # Ensure column names are lowercase
            df = df.copy()
            df.columns = df.columns.str.lower()

            close = df["close"]
            current_price = float(close.iloc[-1])

            # Calculate moving average (中軌)
            ma = close.rolling(window=period).mean()
            line_3 = float(ma.iloc[-1])

            # Calculate standard deviation
            std = close.rolling(window=period).std()
            std_dev = float(std.iloc[-1])

            # Calculate five lines
            line_5 = line_3 + (std_dev * 2.0)  # 過熱線
            line_4 = line_3 + (std_dev * 1.0)  # 偏高線
            line_2 = line_3 - (std_dev * 1.0)  # 偏低線
            line_1 = line_3 - (std_dev * 2.0)  # 超跌線

            # Calculate position ratio (0-100%)
            if line_5 != line_1:
                position_ratio = ((current_price - line_1) / (line_5 - line_1)) * 100
                position_ratio = max(0, min(100, position_ratio))  # Clamp to 0-100
            else:
                position_ratio = 50.0

            # Determine zone
            zone = self._determine_happy_zone(current_price, line_1, line_2, line_3, line_4, line_5)

            # Calculate distances
            distance_to_line1 = ((current_price - line_1) / line_1) * 100 if line_1 > 0 else 0
            distance_to_line5 = (
                ((line_5 - current_price) / current_price) * 100 if current_price > 0 else 0
            )

            # Determine trend
            trend = self._determine_happy_trend(close, period)

            # Determine signal
            signal = self._determine_happy_signal(zone, trend)

            return HappyLinesIndicators(
                ticker=ticker,
                line_1=line_1,
                line_2=line_2,
                line_3=line_3,
                line_4=line_4,
                line_5=line_5,
                current_price=current_price,
                position_ratio=position_ratio,
                zone=zone,
                period=period,
                std_dev=std_dev,
                distance_to_line1=distance_to_line1,
                distance_to_line5=distance_to_line5,
                trend=trend,
                signal=signal,
            )

        except Exception as e:
            log.error(f"Error calculating Happy Lines for {ticker}: {e}")
            return None

    def _determine_happy_zone(
        self,
        price: float,
        line_1: float,
        line_2: float,
        line_3: float,
        line_4: float,
        line_5: float,
    ) -> HappyZone:
        """Determine which zone the price is in."""
        if price >= line_5:
            return HappyZone.OVERBOUGHT
        elif price >= line_4:
            return HappyZone.OVERVALUED
        elif price >= line_2:
            return HappyZone.BALANCED
        elif price >= line_1:
            return HappyZone.UNDERVALUED
        else:
            return HappyZone.OVERSOLD

    def _determine_happy_trend(self, close: pd.Series, period: int) -> TrendType:
        """Determine trend direction based on price vs moving average."""
        try:
            ma = close.rolling(window=period).mean()
            current_price = float(close.iloc[-1])
            current_ma = float(ma.iloc[-1])

            # Also check shorter term trend
            short_ma = close.rolling(window=20).mean()
            current_short_ma = float(short_ma.iloc[-1])

            if current_price > current_ma and current_price > current_short_ma:
                return TrendType.BULLISH
            elif current_price < current_ma and current_price < current_short_ma:
                return TrendType.BEARISH
            else:
                return TrendType.SIDEWAYS
        except Exception:
            return TrendType.SIDEWAYS

    def _determine_happy_signal(self, zone: HappyZone, trend: TrendType) -> SignalType:
        """Determine trading signal based on zone and trend."""
        # Buy signals: oversold/undervalued zones
        if zone in [HappyZone.OVERSOLD, HappyZone.UNDERVALUED]:
            if trend == TrendType.BULLISH:
                return SignalType.STRONG_BUY
            elif trend == TrendType.SIDEWAYS:
                return SignalType.BUY
            else:
                return SignalType.NEUTRAL  # Wait for trend reversal

        # Sell signals: overbought/overvalued zones
        elif zone in [HappyZone.OVERBOUGHT, HappyZone.OVERVALUED]:
            if trend == TrendType.BEARISH:
                return SignalType.STRONG_SELL
            elif trend == TrendType.SIDEWAYS:
                return SignalType.SELL
            else:
                return SignalType.NEUTRAL  # Wait for trend reversal

        # Balanced zone
        else:
            return SignalType.NEUTRAL

    async def analyze_happy_lines(
        self,
        ticker: str,
        period: str = "1y",
        lookback_period: int = 60,
    ) -> HappyLinesIndicators | None:
        """Perform Happy Lines analysis on a stock.

        Args:
            ticker: Stock ticker symbol
            period: Historical data period
            lookback_period: Calculation period for Happy Lines (default: 60 days)

        Returns:
            HappyLinesIndicators object or None
        """
        from datetime import datetime, timedelta

        # Define date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=365)
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        # Get historical data
        df = await self.fetcher.fetch_history(
            ticker, period, start_date=start_date_str, end_date=end_date_str
        )

        if df is None or df.empty:
            log.warning(f"No data available for {ticker}")
            return None

        return self.calculate_happy_lines(df, ticker, period=lookback_period)
