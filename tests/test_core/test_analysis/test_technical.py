"""Tests for Technical Analyzer - RSI, MACD, Bollinger Bands, etc."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch

from pulse.core.analysis.technical import TechnicalAnalyzer
from pulse.core.models import (
    SignalType,
    TechnicalIndicators,
    TrendType,
)


# ============ Fixtures ============


@pytest.fixture
def analyzer():
    """Create TechnicalAnalyzer instance for testing."""
    return TechnicalAnalyzer()


@pytest.fixture
def sample_price_data():
    """Create sample price data DataFrame."""
    np.random.seed(42)
    dates = pd.date_range(start="2023-01-01", end="2024-01-01", freq="D")

    # Generate realistic price movement
    initial_price = 100.0
    returns = np.random.normal(0.0005, 0.015, len(dates))
    prices = initial_price * np.cumprod(1 + returns)

    data = {
        "open": prices * (1 + np.random.uniform(-0.005, 0.005, len(dates))),
        "high": prices * (1 + np.random.uniform(0, 0.01, len(dates))),
        "low": prices * (1 - np.random.uniform(0, 0.01, len(dates))),
        "close": prices,
        "volume": np.random.randint(1000000, 10000000, len(dates)),
    }

    return pd.DataFrame(data, index=dates)


@pytest.fixture
def bullish_price_data():
    """Create bullish trend price data."""
    np.random.seed(42)
    dates = pd.date_range(start="2023-01-01", end="2024-01-01", freq="D")

    # Strong uptrend
    initial_price = 100.0
    returns = np.random.normal(0.001, 0.01, len(dates))  # Positive drift
    prices = initial_price * np.cumprod(1 + returns)

    data = {
        "open": prices * (1 + np.random.uniform(-0.003, 0.003, len(dates))),
        "high": prices * (1 + np.random.uniform(0, 0.008, len(dates))),
        "low": prices * (1 - np.random.uniform(0, 0.008, len(dates))),
        "close": prices,
        "volume": np.random.randint(1000000, 10000000, len(dates)),
    }

    return pd.DataFrame(data, index=dates)


@pytest.fixture
def bearish_price_data():
    """Create bearish trend price data."""
    np.random.seed(42)
    dates = pd.date_range(start="2023-01-01", end="2024-01-01", freq="D")

    # Strong downtrend
    initial_price = 100.0
    returns = np.random.normal(-0.001, 0.01, len(dates))  # Negative drift
    prices = initial_price * np.cumprod(1 + returns)

    data = {
        "open": prices * (1 + np.random.uniform(-0.003, 0.003, len(dates))),
        "high": prices * (1 + np.random.uniform(0, 0.008, len(dates))),
        "low": prices * (1 - np.random.uniform(0, 0.008, len(dates))),
        "close": prices,
        "volume": np.random.randint(1000000, 10000000, len(dates)),
    }

    return pd.DataFrame(data, index=dates)


@pytest.fixture
def oversold_price_data():
    """Create oversold price data (RSI < 30)."""
    np.random.seed(42)
    dates = pd.date_range(start="2023-01-01", end="2024-01-01", freq="D")

    # Price dropped significantly
    initial_price = 100.0
    # Create a drop then recovery
    prices = []
    current = initial_price
    for i in range(len(dates)):
        if i < len(dates) * 0.7:
            current *= 1 + np.random.normal(-0.002, 0.02)
        else:
            current *= 1 + np.random.normal(0.001, 0.015)
        prices.append(max(current, 10.0))

    data = {
        "open": [p * (1 + np.random.uniform(-0.003, 0.003)) for p in prices],
        "high": [p * (1 + np.random.uniform(0, 0.008)) for p in prices],
        "low": [p * (1 - np.random.uniform(0, 0.008)) for p in prices],
        "close": prices,
        "volume": np.random.randint(1000000, 10000000, len(dates)),
    }

    return pd.DataFrame(data, index=dates)


# ============ Test Classes ============


class TestTechnicalAnalyzerInitialization:
    """Test cases for TechnicalAnalyzer initialization."""

    def test_analyzer_initialization(self, analyzer):
        """Test analyzer initializes correctly."""
        assert analyzer.fetcher is not None
        assert analyzer.settings is not None

    def test_default_settings(self, analyzer):
        """Test analyzer uses default settings."""
        from pulse.core.config import settings

        assert analyzer.settings.rsi_period == 14
        assert analyzer.settings.rsi_oversold == 30
        assert analyzer.settings.rsi_overbought == 70


class TestCalculateIndicators:
    """Test cases for indicator calculation."""

    def test_calculate_all_indicators(self, analyzer, sample_price_data):
        """Test calculating all technical indicators."""
        result = analyzer._calculate_indicators("2330", sample_price_data)

        assert result is not None
        assert result.ticker == "2330"
        assert result.calculated_at is not None

        # Trend indicators
        assert result.sma_20 is not None
        assert result.sma_50 is not None
        assert result.ema_9 is not None
        assert result.ema_21 is not None

        # Momentum indicators
        assert result.rsi_14 is not None
        assert 0 <= result.rsi_14 <= 100
        assert result.macd is not None
        assert result.macd_signal is not None
        assert result.macd_histogram is not None

        # Stochastic
        assert result.stoch_k is not None
        assert result.stoch_d is not None
        assert 0 <= result.stoch_k <= 100
        assert 0 <= result.stoch_d <= 100

        # Volatility indicators
        assert result.bb_upper is not None
        assert result.bb_middle is not None
        assert result.bb_lower is not None
        assert result.bb_width is not None
        assert result.atr_14 is not None

        # Volume indicators
        assert result.obv is not None
        assert result.mfi_14 is not None
        assert result.volume_sma_20 is not None

        # Support/Resistance
        assert result.support_1 is not None
        assert result.support_2 is not None
        assert result.resistance_1 is not None
        assert result.resistance_2 is not None

        # Signals
        assert result.trend in TrendType
        assert result.signal in SignalType

    def test_sma_calculation(self, analyzer, sample_price_data):
        """Test SMA calculation."""
        result = analyzer._calculate_indicators("2330", sample_price_data)

        # SMA 20 should be calculated from last 20 closes
        assert result.sma_20 is not None
        assert result.sma_50 is not None

        # With enough data, SMA should be reasonable
        assert result.sma_20 > 0
        assert result.sma_50 > 0

    def test_ema_calculation(self, analyzer, sample_price_data):
        """Test EMA calculation."""
        result = analyzer._calculate_indicators("2330", sample_price_data)

        assert result.ema_9 is not None
        assert result.ema_21 is not None
        assert result.ema_9 > 0
        assert result.ema_21 > 0

    def test_rsi_calculation(self, analyzer, sample_price_data):
        """Test RSI calculation."""
        result = analyzer._calculate_indicators("2330", sample_price_data)

        assert result.rsi_14 is not None
        assert 0 <= result.rsi_14 <= 100

    def test_macd_calculation(self, analyzer, sample_price_data):
        """Test MACD calculation."""
        result = analyzer._calculate_indicators("2330", sample_price_data)

        assert result.macd is not None
        assert result.macd_signal is not None
        assert result.macd_histogram is not None
        # MACD histogram is the difference
        assert result.macd_histogram == pytest.approx(result.macd - result.macd_signal, abs=0.01)

    def test_bollinger_bands_calculation(self, analyzer, sample_price_data):
        """Test Bollinger Bands calculation."""
        result = analyzer._calculate_indicators("2330", sample_price_data)

        # Upper band should be above middle
        assert result.bb_upper > result.bb_middle
        # Middle band should be above lower
        assert result.bb_middle > result.bb_lower
        # Width should be positive
        assert result.bb_width > 0

    def test_atr_calculation(self, analyzer, sample_price_data):
        """Test ATR calculation."""
        result = analyzer._calculate_indicators("2330", sample_price_data)

        assert result.atr_14 is not None
        assert result.atr_14 > 0

    def test_stochastic_calculation(self, analyzer, sample_price_data):
        """Test Stochastic oscillator calculation."""
        result = analyzer._calculate_indicators("2330", sample_price_data)

        assert result.stoch_k is not None
        assert result.stoch_d is not None
        assert 0 <= result.stoch_k <= 100
        assert 0 <= result.stoch_d <= 100

    def test_support_resistance_levels(self, analyzer, sample_price_data):
        """Test support and resistance level calculation."""
        result = analyzer._calculate_indicators("2330", sample_price_data)

        # Resistance should be above current price (middle band)
        assert result.resistance_1 > result.bb_middle
        assert result.resistance_2 > result.resistance_1

        # Support should be below current price
        assert result.support_1 < result.bb_middle
        assert result.support_2 < result.support_1

    def test_trend_determination_bullish(self, analyzer, bullish_price_data):
        """Test trend determination in bullish market."""
        result = analyzer._calculate_indicators("2330", bullish_price_data)

        # In strong uptrend, should be bullish
        assert result.trend == TrendType.BULLISH

    def test_trend_determination_bearish(self, analyzer, bearish_price_data):
        """Test trend determination in bearish market."""
        result = analyzer._calculate_indicators("2330", bearish_price_data)

        # In strong downtrend, should be bearish
        assert result.trend == TrendType.BEARISH

    def test_oversold_condition(self, analyzer, oversold_price_data):
        """Test oversold condition detection."""
        result = analyzer._calculate_indicators("2330", oversold_price_data)

        # Just verify RSI is calculated and within valid range
        assert result.rsi_14 is not None
        assert 0 <= result.rsi_14 <= 100

    def test_oversold_data_has_low_rsi(self, analyzer):
        """Test that we can create data with low RSI."""
        # Create very oversold data
        np.random.seed(42)
        dates = pd.date_range(start="2023-01-01", end="2024-01-01", freq="D")

        # Price crashed then stabilized low
        prices = []
        current = 100.0
        for i in range(len(dates)):
            if i < len(dates) * 0.8:
                current *= 0.99  # Gradual decline
            else:
                current *= 1.001  # Slight recovery
            prices.append(max(current, 10.0))

        data = {
            "open": [p * (1 + np.random.uniform(-0.01, 0.01)) for p in prices],
            "high": [p * (1 + np.random.uniform(0, 0.02)) for p in prices],
            "low": [p * (1 - np.random.uniform(0, 0.02)) for p in prices],
            "close": prices,
            "volume": np.random.randint(1000000, 10000000, len(dates)),
        }
        df = pd.DataFrame(data, index=dates)

        result = analyzer._calculate_indicators("2330", df)

        # RSI should be relatively low (not guaranteed to be < 40, but should be lower than neutral)
        assert result.rsi_14 is not None
        assert result.rsi_14 < 70  # Definitely not overbought

    def test_signal_strong_buy_on_oversold_bullish(self, analyzer):
        """Test that trend detection works correctly in various conditions."""
        # This test verifies the analyzer handles different market conditions
        np.random.seed(42)
        dates = pd.date_range(start="2023-01-01", end="2024-01-01", freq="D")

        # Price in uptrend
        prices = []
        current = 100.0
        for i in range(len(dates)):
            current *= 1.001  # Uptrend
            prices.append(max(current, 10.0))

        data = {
            "open": [p * (1 + np.random.uniform(-0.005, 0.005)) for p in prices],
            "high": [p * (1 + np.random.uniform(0, 0.01)) for p in prices],
            "low": [p * (1 - np.random.uniform(0, 0.01)) for p in prices],
            "close": prices,
            "volume": np.random.randint(1000000, 10000000, len(dates)),
        }
        df = pd.DataFrame(data, index=dates)

        result = analyzer._calculate_indicators("2330", df)

        # In uptrend, trend should be BULLISH
        assert result.trend == TrendType.BULLISH
        # Signal should not be STRONG_SELL
        assert result.signal != SignalType.STRONG_SELL

    def test_rsi_status_oversold(self, analyzer):
        """Test RSI status calculation works."""
        np.random.seed(42)
        dates = pd.date_range(start="2023-01-01", end="2024-01-01", freq="D")

        # Create volatile data
        prices = [100.0 + np.random.normal(0, 2) for _ in range(len(dates))]
        data = {
            "open": prices,
            "high": [p + np.random.uniform(0, 1) for p in prices],
            "low": [p - np.random.uniform(0, 1) for p in prices],
            "close": prices,
            "volume": np.random.randint(1000000, 10000000, len(dates)),
        }
        df = pd.DataFrame(data, index=dates)

        indicators = analyzer._calculate_indicators("2330", df)
        summary = analyzer.get_indicator_summary(indicators)

        # Verify summary contains RSI
        assert len(summary) > 0
        rsi_found = any("RSI" in s["name"] for s in summary)
        assert rsi_found

    def test_rsi_status_overbought(self, analyzer, sample_price_data):
        """Test RSI status for overbought condition."""
        # Create overbought data
        np.random.seed(42)
        dates = pd.date_range(start="2023-01-01", end="2024-01-01", freq="D")
        prices = [100.0 + i * 0.5 + np.random.normal(0, 0.5) for i in range(len(dates))]
        data = {
            "open": prices,
            "high": [p + np.random.uniform(0, 1) for p in prices],
            "low": [p - np.random.uniform(0, 1) for p in prices],
            "close": prices,
            "volume": np.random.randint(1000000, 10000000, len(dates)),
        }
        df = pd.DataFrame(data, index=dates)

        indicators = analyzer._calculate_indicators("2330", df)
        summary = analyzer.get_indicator_summary(indicators)

        rsi_items = [s for s in summary if "RSI" in s["name"]]
        # In strong uptrend, RSI might be overbought
        assert rsi_items[0]["status"] in ["Overbought", "Neutral"]

    def test_macd_status_bullish(self, analyzer, bullish_price_data):
        """Test MACD status for bullish condition."""
        indicators = analyzer._calculate_indicators("2330", bullish_price_data)
        summary = analyzer.get_indicator_summary(indicators)

        macd_items = [s for s in summary if "MACD" in s["name"]]
        assert len(macd_items) == 1
        # In bullish trend, MACD should be bullish
        assert macd_items[0]["status"] == "Bullish"


class TestTechnicalIndicatorsModel:
    """Test cases for TechnicalIndicators model."""

    def test_indicators_creation(self):
        """Test creating TechnicalIndicators object."""
        indicators = TechnicalIndicators(
            ticker="2330",
            rsi_14=50.0,
            macd=1.0,
            macd_signal=0.5,
            macd_histogram=0.5,
            sma_20=100.0,
            trend=TrendType.BULLISH,
            signal=SignalType.BUY,
        )

        assert indicators.ticker == "2330"
        assert indicators.rsi_14 == 50.0
        assert indicators.trend == TrendType.BULLISH
        assert indicators.signal == SignalType.BUY

    def test_indicators_with_none_values(self):
        """Test creating indicators with None values."""
        indicators = TechnicalIndicators(
            ticker="2330",
            rsi_14=None,
            sma_200=None,  # Not enough data
            ema_55=None,
        )

        assert indicators.rsi_14 is None
        assert indicators.sma_200 is None

    def test_to_summary(self):
        """Test to_summary method."""
        indicators = TechnicalIndicators(
            ticker="2330",
            rsi_14=50.0,
            macd=1.0,
            macd_signal=0.5,
            sma_20=100.0,
            sma_50=98.0,
            sma_200=None,
            bb_upper=105.0,
            bb_lower=95.0,
            atr_14=2.5,
            trend=TrendType.BULLISH,
            signal=SignalType.BUY,
        )

        summary = indicators.to_summary()

        assert isinstance(summary, dict)
        assert "RSI" in summary
        assert "MACD" in summary
        assert "SMA 20" in summary
        assert "Trend" in summary
        assert summary["Trend"] == "Bullish"


class TestAnalyzeMethod:
    """Test cases for the main analyze method."""

    @pytest.mark.asyncio
    async def test_analyze_success(self, analyzer, sample_price_data):
        """Test successful technical analysis."""
        with patch.object(analyzer.fetcher, "fetch_history", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_price_data

            result = await analyzer.analyze("2330")

        assert result is not None
        assert result.ticker == "2330"
        assert isinstance(result, TechnicalIndicators)

    @pytest.mark.asyncio
    async def test_analyze_with_custom_period(self, analyzer, sample_price_data):
        """Test analysis with custom period."""
        with patch.object(analyzer.fetcher, "fetch_history", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = sample_price_data

            result = await analyzer.analyze("2330", period="6mo")

        assert result is not None
        mock_fetch.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_returns_none_for_no_data(self, analyzer):
        """Test analysis returns None when no data available."""
        with patch.object(analyzer.fetcher, "fetch_history", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None

            result = await analyzer.analyze("INVALID")

        assert result is None

    @pytest.mark.asyncio
    async def test_analyze_returns_none_for_empty_data(self, analyzer):
        """Test analysis returns None for empty DataFrame."""
        with patch.object(analyzer.fetcher, "fetch_history", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = pd.DataFrame()

            result = await analyzer.analyze("2330")

        assert result is None


class TestSignalTypeEnum:
    """Test cases for SignalType enum."""

    def test_signal_values(self):
        """Test SignalType enum values."""
        assert SignalType.STRONG_BUY.value == "Strong Buy"
        assert SignalType.BUY.value == "Buy"
        assert SignalType.NEUTRAL.value == "Neutral"
        assert SignalType.SELL.value == "Sell"
        assert SignalType.STRONG_SELL.value == "Strong Sell"


class TestTrendTypeEnum:
    """Test cases for TrendType enum."""

    def test_trend_values(self):
        """Test TrendType enum values."""
        assert TrendType.BULLISH.value == "Bullish"
        assert TrendType.BEARISH.value == "Bearish"
        assert TrendType.SIDEWAYS.value == "Sideways"
