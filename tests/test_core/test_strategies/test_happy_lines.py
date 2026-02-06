"""Tests for Happy Lines (樂活五線譜) strategy."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from pulse.core.strategies.happy_lines import (
    HappyLinesStrategy,
    HappyLinesSignal,
    HappyLinesStrategyResult,
    screen_happy_lines,
)
from pulse.core.models import HappyLinesIndicators, HappyZone, SignalType, TrendType


class TestHappyLinesStrategyResult:
    """Test HappyLinesStrategyResult dataclass."""

    def test_basic_creation(self):
        """Test creating a basic result."""
        result = HappyLinesStrategyResult(
            ticker="2330",
            name="台積電",
            price=1000.0,
        )
        assert result.ticker == "2330"
        assert result.name == "台積電"
        assert result.price == 1000.0

    def test_volume_ratio(self):
        """Test volume_ratio property."""
        result = HappyLinesStrategyResult(
            ticker="2330",
            volume=2_000_000,
            avg_volume=1_000_000,
        )
        assert result.volume_ratio == 2.0

        # Test with zero avg_volume
        result2 = HappyLinesStrategyResult(ticker="2330")
        assert result2.volume_ratio == 1.0

    def test_is_liquid(self):
        """Test is_liquid property."""
        result = HappyLinesStrategyResult(
            ticker="2330",
            avg_volume=2_000_000,
        )
        assert result.is_liquid is True

        result2 = HappyLinesStrategyResult(
            ticker="2330",
            avg_volume=500_000,
        )
        assert result2.is_liquid is False

    def test_is_near_support(self):
        """Test is_near_support property."""
        result = HappyLinesStrategyResult(
            ticker="2330",
            zone=HappyZone.OVERSOLD,
        )
        assert result.is_near_support is True

        result2 = HappyLinesStrategyResult(
            ticker="2330",
            zone=HappyZone.OVERBOUGHT,
        )
        assert result2.is_near_support is False

    def test_is_near_resistance(self):
        """Test is_near_resistance property."""
        result = HappyLinesStrategyResult(
            ticker="2330",
            zone=HappyZone.OVERBOUGHT,
        )
        assert result.is_near_resistance is True

        result2 = HappyLinesStrategyResult(
            ticker="2330",
            zone=HappyZone.UNDERVALUED,
        )
        assert result2.is_near_resistance is False

    def test_line_width(self):
        """Test line_width property."""
        result = HappyLinesStrategyResult(
            ticker="2330",
            line_1=800,
            line_5=1200,
        )
        assert result.line_width == 400

        result2 = HappyLinesStrategyResult(ticker="2330")
        assert result2.line_width == 0.0

    def test_to_dict(self):
        """Test to_dict method."""
        result = HappyLinesStrategyResult(
            ticker="2330",
            name="台積電",
            price=1000.0,
            zone=HappyZone.BALANCED,
        )
        d = result.to_dict()
        assert d["ticker"] == "2330"
        assert d["name"] == "台積電"
        assert d["price"] == 1000.0


class TestHappyLinesStrategy:
    """Test HappyLinesStrategy class."""

    def test_default_initialization(self):
        """Test default initialization."""
        strategy = HappyLinesStrategy()
        assert strategy.period == 120
        assert strategy.min_avg_volume == 1_000_000

    def test_custom_initialization(self):
        """Test custom initialization."""
        strategy = HappyLinesStrategy(period=120, min_avg_volume=2_000_000)
        assert strategy.period == 120
        assert strategy.min_avg_volume == 2_000_000

    def test_invalid_period_fallback(self):
        """Test that invalid period falls back to default."""
        strategy = HappyLinesStrategy(period=50)  # Invalid period
        assert strategy.period == 120  # Should fallback to default

    def test_valid_periods(self):
        """Test all valid periods."""
        for period in HappyLinesStrategy.VALID_PERIODS:
            strategy = HappyLinesStrategy(period=period)
            assert strategy.period == period

    @pytest.mark.asyncio
    async def test_screen_buy_signals(self):
        """Test screen_buy_signals method."""
        strategy = HappyLinesStrategy()

        # Mock the screen method
        mock_results = [
            HappyLinesStrategyResult(
                ticker="2330",
                signal=HappyLinesSignal.BUY,
                zone=HappyZone.UNDERVALUED,
            ),
            HappyLinesStrategyResult(
                ticker="2454",
                signal=HappyLinesSignal.STRONG_BUY,
                zone=HappyZone.OVERSOLD,
            ),
            HappyLinesStrategyResult(
                ticker="2317",
                signal=HappyLinesSignal.HOLD,
                zone=HappyZone.BALANCED,
            ),
        ]

        with patch.object(strategy, "screen", AsyncMock(return_value=mock_results)):
            results = await strategy.screen_buy_signals(limit=10)

            assert len(results) == 2
            assert all(
                r.signal in [HappyLinesSignal.BUY, HappyLinesSignal.STRONG_BUY] for r in results
            )

    @pytest.mark.asyncio
    async def test_screen_sell_signals(self):
        """Test screen_sell_signals method."""
        strategy = HappyLinesStrategy()

        mock_results = [
            HappyLinesStrategyResult(
                ticker="2330",
                signal=HappyLinesSignal.SELL,
                zone=HappyZone.OVERVALUED,
            ),
            HappyLinesStrategyResult(
                ticker="2454",
                signal=HappyLinesSignal.STRONG_SELL,
                zone=HappyZone.OVERBOUGHT,
            ),
            HappyLinesStrategyResult(
                ticker="2317",
                signal=HappyLinesSignal.HOLD,
                zone=HappyZone.BALANCED,
            ),
        ]

        with patch.object(strategy, "screen", AsyncMock(return_value=mock_results)):
            results = await strategy.screen_sell_signals(limit=10)

            assert len(results) == 2
            assert all(
                r.signal in [HappyLinesSignal.SELL, HappyLinesSignal.STRONG_SELL] for r in results
            )

    @pytest.mark.asyncio
    async def test_screen_oversold(self):
        """Test screen_oversold method."""
        strategy = HappyLinesStrategy()

        mock_results = [
            HappyLinesStrategyResult(
                ticker="2330",
                zone=HappyZone.OVERSOLD,
            ),
            HappyLinesStrategyResult(
                ticker="2454",
                zone=HappyZone.UNDERVALUED,
            ),
            HappyLinesStrategyResult(
                ticker="2317",
                zone=HappyZone.BALANCED,
            ),
        ]

        with patch.object(strategy, "screen", AsyncMock(return_value=mock_results)):
            results = await strategy.screen_oversold(limit=10)

            assert len(results) == 2
            assert all(r.zone in [HappyZone.OVERSOLD, HappyZone.UNDERVALUED] for r in results)

    @pytest.mark.asyncio
    async def test_screen_overbought(self):
        """Test screen_overbought method."""
        strategy = HappyLinesStrategy()

        mock_results = [
            HappyLinesStrategyResult(
                ticker="2330",
                zone=HappyZone.OVERBOUGHT,
            ),
            HappyLinesStrategyResult(
                ticker="2454",
                zone=HappyZone.OVERVALUED,
            ),
            HappyLinesStrategyResult(
                ticker="2317",
                zone=HappyZone.BALANCED,
            ),
        ]

        with patch.object(strategy, "screen", AsyncMock(return_value=mock_results)):
            results = await strategy.screen_overbought(limit=10)

            assert len(results) == 2
            assert all(r.zone in [HappyZone.OVERBOUGHT, HappyZone.OVERVALUED] for r in results)

    def test_get_strategy_summary(self):
        """Test get_strategy_summary method."""
        strategy = HappyLinesStrategy()
        summary = strategy.get_strategy_summary()

        assert summary["strategy"] == "Happy Lines (樂活五線譜)"
        assert "version" in summary
        assert "parameters" in summary
        assert "five_lines" in summary
        assert "buy_conditions" in summary
        assert "sell_conditions" in summary
        assert "period_options" in summary


class TestHappyLinesSignal:
    """Test HappyLinesSignal enum."""

    def test_signal_values(self):
        """Test signal enum values."""
        assert HappyLinesSignal.STRONG_BUY.value == "STRONG_BUY"
        assert HappyLinesSignal.BUY.value == "BUY"
        assert HappyLinesSignal.HOLD.value == "HOLD"
        assert HappyLinesSignal.SELL.value == "SELL"
        assert HappyLinesSignal.STRONG_SELL.value == "STRONG_SELL"
        assert HappyLinesSignal.WATCH.value == "WATCH"


class TestScreenHappyLinesFunction:
    """Test screen_happy_lines convenience function."""

    @pytest.mark.asyncio
    async def test_buy_signals_only(self):
        """Test buy_signals_only parameter."""
        mock_results = [
            HappyLinesStrategyResult(
                ticker="2330",
                signal=HappyLinesSignal.BUY,
            ),
        ]

        with patch.object(
            HappyLinesStrategy, "screen_buy_signals", AsyncMock(return_value=mock_results)
        ):
            results = await screen_happy_lines(buy_signals_only=True)
            assert len(results) == 1

    @pytest.mark.asyncio
    async def test_all_signals(self):
        """Test with buy_signals_only=False."""
        mock_results = [
            HappyLinesStrategyResult(
                ticker="2330",
                signal=HappyLinesSignal.BUY,
            ),
            HappyLinesStrategyResult(
                ticker="2454",
                signal=HappyLinesSignal.HOLD,
            ),
        ]

        with patch.object(HappyLinesStrategy, "screen", AsyncMock(return_value=mock_results)):
            results = await screen_happy_lines(buy_signals_only=False)
            assert len(results) == 2


class TestHappyLinesIntegration:
    """Integration tests for Happy Lines strategy."""

    def test_strategy_with_happy_lines_indicators(self):
        """Test that strategy works with HappyLinesIndicators model."""
        happy = HappyLinesIndicators(
            ticker="2330",
            line_1=800,
            line_2=900,
            line_3=1000,
            line_4=1100,
            line_5=1200,
            current_price=950,
            position_ratio=25.0,
            zone=HappyZone.UNDERVALUED,
            trend=TrendType.BULLISH,
            signal=SignalType.BUY,
        )

        # Verify properties
        assert happy.line_width == 400
        assert happy.is_near_support is True
        assert happy.is_near_resistance is False

        # Verify summary
        summary = happy.to_summary()
        assert summary["當前價格"] == 950
        assert summary["位階"] == "偏低區"
        assert summary["位階百分比"] == "25.0%"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
