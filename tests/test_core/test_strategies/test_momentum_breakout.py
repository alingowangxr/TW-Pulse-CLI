"""Tests for Momentum Breakout Strategy."""

import pytest
from datetime import datetime

from pulse.core.strategies.momentum_breakout import MomentumBreakoutStrategy
from pulse.core.strategies.base import SignalAction


class TestMomentumBreakoutStrategy:
    """Test MomentumBreakoutStrategy class."""

    def test_strategy_initialization(self):
        """Test strategy initialization with default parameters."""
        strategy = MomentumBreakoutStrategy()

        assert strategy.name == "動量突破策略"
        assert strategy.ticker == ""
        assert strategy.prev_macd is None
        assert strategy.prev_macd_signal is None

    @pytest.mark.asyncio
    async def test_strategy_initialize(self):
        """Test strategy initialization method."""
        strategy = MomentumBreakoutStrategy()
        await strategy.initialize("2330", 1_000_000, {})

        assert strategy.ticker == "2330"
        assert strategy.state is not None
        assert strategy.state.cash == 1_000_000
        assert strategy.config["adx_entry_threshold"] == 25
        assert strategy.config["adx_exit_threshold"] == 20
        assert strategy.config["volume_multiplier"] == 1.5
        assert strategy.config["trailing_stop_pct"] == 0.15

    @pytest.mark.asyncio
    async def test_strategy_initialize_custom_config(self):
        """Test strategy initialization with custom config."""
        strategy = MomentumBreakoutStrategy()
        await strategy.initialize(
            "2330",
            1_000_000,
            {
                "adx_entry_threshold": 30,
                "adx_exit_threshold": 25,
                "volume_multiplier": 2.0,
                "trailing_stop_pct": 0.20,
            },
        )

        assert strategy.config["adx_entry_threshold"] == 30
        assert strategy.config["adx_exit_threshold"] == 25
        assert strategy.config["volume_multiplier"] == 2.0
        assert strategy.config["trailing_stop_pct"] == 0.20

    @pytest.mark.asyncio
    async def test_no_signal_without_conditions(self):
        """Test no signal when conditions not met."""
        strategy = MomentumBreakoutStrategy()
        await strategy.initialize("2330", 1_000_000, {})

        bar = {
            "date": datetime.now(),
            "open": 100,
            "high": 105,
            "low": 98,
            "close": 102,
            "volume": 1000,
        }
        indicators = {
            "adx": 20,  # Below threshold
            "macd": 1.0,
            "macd_signal": 0.5,
            "volume_sma_20": 1000,
        }

        signal = await strategy.on_bar(bar, indicators)
        assert signal is None

    @pytest.mark.asyncio
    async def test_buy_signal_on_momentum_breakout(self):
        """Test buy signal on momentum breakout conditions."""
        strategy = MomentumBreakoutStrategy()
        await strategy.initialize("2330", 1_000_000, {})

        # First bar to set previous MACD values (below signal)
        bar1 = {
            "date": datetime.now(),
            "open": 100,
            "high": 105,
            "low": 98,
            "close": 102,
            "volume": 2000,
        }
        indicators1 = {
            "adx": 30,
            "macd": -0.5,  # Below signal
            "macd_signal": 0.5,
            "volume_sma_20": 1000,
        }
        await strategy.on_bar(bar1, indicators1)

        # Second bar with golden cross
        bar2 = {
            "date": datetime.now(),
            "open": 100,
            "high": 108,
            "low": 99,
            "close": 106,
            "volume": 2000,  # 2x average = above 1.5x
        }
        indicators2 = {
            "adx": 30,  # Above 25
            "macd": 1.0,  # Now above signal (golden cross)
            "macd_signal": 0.5,
            "volume_sma_20": 1000,
        }

        signal = await strategy.on_bar(bar2, indicators2)

        assert signal is not None
        assert signal.action == SignalAction.BUY
        assert "動量突破進場" in signal.reason

    @pytest.mark.asyncio
    async def test_sell_signal_on_trailing_stop(self):
        """Test sell signal on trailing stop."""
        strategy = MomentumBreakoutStrategy()
        await strategy.initialize("2330", 1_000_000, {})

        # Simulate having a position
        strategy.state.positions = 1
        strategy.state.total_shares = 1000
        strategy.peak_price = 100  # Peak at 100

        bar = {
            "date": datetime.now(),
            "open": 82,
            "high": 85,
            "low": 80,
            "close": 84,  # 16% drop from peak (below 15% trailing stop)
            "volume": 1000,
        }
        indicators = {
            "adx": 25,
            "macd": 0.5,
            "macd_signal": 0.3,
            "volume_sma_20": 1000,
        }

        signal = await strategy.on_bar(bar, indicators)

        assert signal is not None
        assert signal.action == SignalAction.SELL
        assert "移動停利" in signal.reason

    @pytest.mark.asyncio
    async def test_sell_signal_on_adx_weakness(self):
        """Test sell signal when ADX shows trend weakness."""
        strategy = MomentumBreakoutStrategy()
        await strategy.initialize("2330", 1_000_000, {})

        # Simulate having a position
        strategy.state.positions = 1
        strategy.state.total_shares = 1000
        strategy.peak_price = 100

        bar = {
            "date": datetime.now(),
            "open": 95,
            "high": 98,
            "low": 94,
            "close": 96,
            "volume": 1000,
        }
        indicators = {
            "adx": 15,  # Below 20 (exit threshold)
            "macd": 0.5,
            "macd_signal": 0.3,
            "volume_sma_20": 1000,
        }

        signal = await strategy.on_bar(bar, indicators)

        assert signal is not None
        assert signal.action == SignalAction.SELL
        assert "ADX 趨勢轉弱" in signal.reason

    @pytest.mark.asyncio
    async def test_sell_signal_on_macd_death_cross(self):
        """Test sell signal on MACD death cross."""
        strategy = MomentumBreakoutStrategy()
        await strategy.initialize("2330", 1_000_000, {})

        # Simulate having a position with previous MACD above signal
        strategy.state.positions = 1
        strategy.state.total_shares = 1000
        strategy.peak_price = 100
        strategy.prev_macd = 1.0
        strategy.prev_macd_signal = 0.5

        bar = {
            "date": datetime.now(),
            "open": 95,
            "high": 98,
            "low": 94,
            "close": 96,
            "volume": 1000,
        }
        indicators = {
            "adx": 25,
            "macd": 0.3,  # Now below signal (death cross)
            "macd_signal": 0.5,
            "volume_sma_20": 1000,
        }

        signal = await strategy.on_bar(bar, indicators)

        assert signal is not None
        assert signal.action == SignalAction.SELL
        assert "MACD 死亡交叉" in signal.reason

    def test_macd_golden_cross_detection(self):
        """Test MACD golden cross detection logic."""
        strategy = MomentumBreakoutStrategy()

        # Set previous values: MACD below signal
        strategy.prev_macd = -0.5
        strategy.prev_macd_signal = 0.3

        # Current: MACD above signal (golden cross)
        assert strategy._is_macd_golden_cross(0.5, 0.3) is True

        # No cross - MACD still above
        strategy.prev_macd = 0.6
        strategy.prev_macd_signal = 0.3
        assert strategy._is_macd_golden_cross(0.8, 0.3) is False

    def test_macd_death_cross_detection(self):
        """Test MACD death cross detection logic."""
        strategy = MomentumBreakoutStrategy()

        # Set previous values: MACD above signal
        strategy.prev_macd = 0.8
        strategy.prev_macd_signal = 0.3

        # Current: MACD below signal (death cross)
        assert strategy._is_macd_death_cross(0.2, 0.3) is True

        # No cross - MACD still below
        strategy.prev_macd = 0.1
        strategy.prev_macd_signal = 0.3
        assert strategy._is_macd_death_cross(0.0, 0.3) is False

    def test_get_config_schema(self):
        """Test configuration schema."""
        strategy = MomentumBreakoutStrategy()
        schema = strategy.get_config_schema()

        assert "adx_entry_threshold" in schema
        assert "adx_exit_threshold" in schema
        assert "volume_multiplier" in schema
        assert "trailing_stop_pct" in schema
        assert "position_size_pct" in schema

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test status output."""
        strategy = MomentumBreakoutStrategy()
        await strategy.initialize("2330", 1_000_000, {})

        status = strategy.get_status()

        assert "動量突破策略" in status
        assert "2330" in status
        assert "ADX" in status
        assert "MACD" in status
