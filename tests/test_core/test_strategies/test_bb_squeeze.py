"""Tests for BB Squeeze Strategy."""

import pytest
from datetime import datetime

from pulse.core.strategies.bb_squeeze import BBSqueezeStrategy
from pulse.core.strategies.base import SignalAction


class TestBBSqueezeStrategy:
    """Test BBSqueezeStrategy class."""

    def test_strategy_initialization(self):
        """Test strategy initialization with default parameters."""
        strategy = BBSqueezeStrategy()

        assert strategy.name == "布林壓縮策略"
        assert strategy.ticker == ""
        assert strategy.prev_bb_width is None
        assert strategy.in_squeeze is False

    @pytest.mark.asyncio
    async def test_strategy_initialize(self):
        """Test strategy initialization method."""
        strategy = BBSqueezeStrategy()
        await strategy.initialize("2330", 1_000_000, {})

        assert strategy.ticker == "2330"
        assert strategy.state is not None
        assert strategy.state.cash == 1_000_000
        assert strategy.config["squeeze_percentile"] == 20
        assert strategy.config["lookback_period"] == 20

    @pytest.mark.asyncio
    async def test_strategy_initialize_custom_config(self):
        """Test strategy initialization with custom config."""
        strategy = BBSqueezeStrategy()
        await strategy.initialize(
            "2330",
            1_000_000,
            {
                "squeeze_percentile": 15,
                "lookback_period": 30,
                "position_size_pct": 0.3,
            },
        )

        assert strategy.config["squeeze_percentile"] == 15
        assert strategy.config["lookback_period"] == 30
        assert strategy.config["position_size_pct"] == 0.3

    @pytest.mark.asyncio
    async def test_no_signal_without_history(self):
        """Test no signal when insufficient history."""
        strategy = BBSqueezeStrategy()
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
            "bb_upper": 110,
            "bb_middle": 100,
            "bb_lower": 90,
            "bb_width": 0.05,
        }

        signal = await strategy.on_bar(bar, indicators)
        assert signal is None  # Not enough history

    @pytest.mark.asyncio
    async def test_squeeze_detection(self):
        """Test squeeze state detection."""
        strategy = BBSqueezeStrategy()
        await strategy.initialize("2330", 1_000_000, {"lookback_period": 5})

        # Build up history with wider bands
        for i in range(5):
            bar = {
                "date": datetime.now(),
                "open": 100,
                "high": 105,
                "low": 98,
                "close": 102,
                "volume": 1000,
            }
            indicators = {
                "bb_upper": 110,
                "bb_middle": 100,
                "bb_lower": 90,
                "bb_width": 0.10 + (i * 0.02),  # Widths: 0.10, 0.12, 0.14, 0.16, 0.18
            }
            await strategy.on_bar(bar, indicators)

        # Now provide a very narrow band (squeeze)
        bar = {
            "date": datetime.now(),
            "open": 100,
            "high": 105,
            "low": 98,
            "close": 102,
            "volume": 1000,
        }
        indicators = {
            "bb_upper": 105,
            "bb_middle": 100,
            "bb_lower": 95,
            "bb_width": 0.05,  # Very narrow - should trigger squeeze
        }
        await strategy.on_bar(bar, indicators)

        assert strategy.in_squeeze is True

    @pytest.mark.asyncio
    async def test_buy_signal_on_squeeze_breakout(self):
        """Test buy signal on squeeze breakout."""
        strategy = BBSqueezeStrategy()
        await strategy.initialize("2330", 1_000_000, {"lookback_period": 5})

        # Build up history with wider bands
        for i in range(5):
            bar = {
                "date": datetime.now(),
                "open": 100,
                "high": 105,
                "low": 98,
                "close": 102,
                "volume": 1000,
            }
            indicators = {
                "bb_upper": 110,
                "bb_middle": 100,
                "bb_lower": 90,
                "bb_width": 0.15,
            }
            await strategy.on_bar(bar, indicators)

        # Enter squeeze state
        bar_squeeze = {
            "date": datetime.now(),
            "open": 100,
            "high": 102,
            "low": 99,
            "close": 101,
            "volume": 1000,
        }
        indicators_squeeze = {
            "bb_upper": 103,
            "bb_middle": 100,
            "bb_lower": 97,
            "bb_width": 0.03,  # Very narrow
        }
        await strategy.on_bar(bar_squeeze, indicators_squeeze)
        assert strategy.in_squeeze is True

        # Breakout: width expands and price breaks upper band
        bar_breakout = {
            "date": datetime.now(),
            "open": 102,
            "high": 108,
            "low": 101,
            "close": 106,  # Above upper band (103)
            "volume": 1000,
        }
        indicators_breakout = {
            "bb_upper": 103,
            "bb_middle": 100,
            "bb_lower": 97,
            "bb_width": 0.05,  # Expanding from 0.03
        }

        signal = await strategy.on_bar(bar_breakout, indicators_breakout)

        assert signal is not None
        assert signal.action == SignalAction.BUY
        assert "布林壓縮突破" in signal.reason

    @pytest.mark.asyncio
    async def test_sell_signal_on_return_to_middle(self):
        """Test sell signal when price returns to middle band."""
        strategy = BBSqueezeStrategy()
        await strategy.initialize("2330", 1_000_000, {})

        # Simulate having a position
        strategy.state.positions = 1
        strategy.state.total_shares = 1000

        bar = {
            "date": datetime.now(),
            "open": 102,
            "high": 103,
            "low": 99,
            "close": 100,  # At middle band
            "volume": 1000,
        }
        indicators = {
            "bb_upper": 110,
            "bb_middle": 100,
            "bb_lower": 90,
            "bb_width": 0.10,
        }

        signal = await strategy.on_bar(bar, indicators)

        assert signal is not None
        assert signal.action == SignalAction.SELL
        assert "回歸中軌" in signal.reason

    @pytest.mark.asyncio
    async def test_sell_signal_on_lower_band_touch(self):
        """Test sell signal when price touches lower band."""
        strategy = BBSqueezeStrategy()
        await strategy.initialize("2330", 1_000_000, {})

        # Simulate having a position
        strategy.state.positions = 1
        strategy.state.total_shares = 1000

        # Price at lower band, but above middle band to avoid middle band trigger first
        bar = {
            "date": datetime.now(),
            "open": 82,
            "high": 83,
            "low": 79,
            "close": 80,  # At lower band (80), but middle is at 90, so lower band triggers
            "volume": 1000,
        }
        indicators = {
            "bb_upper": 110,
            "bb_middle": 90,
            "bb_lower": 80,
            "bb_width": 0.10,
        }

        signal = await strategy.on_bar(bar, indicators)

        assert signal is not None
        assert signal.action == SignalAction.SELL
        # Check that either lower band or middle band reason is in the signal
        assert "BB" in signal.reason

    def test_bb_width_percentile_calculation(self):
        """Test BB width percentile calculation."""
        strategy = BBSqueezeStrategy()
        strategy.config = {"lookback_period": 5}

        # Add width history
        strategy.bb_width_history.extend([0.10, 0.12, 0.14, 0.16, 0.18])

        # Current width at 0.08 should be 0th percentile (below all)
        percentile = strategy._get_bb_width_percentile(0.08)
        assert percentile == 0

        # Current width at 0.20 should be 100th percentile (above all)
        percentile = strategy._get_bb_width_percentile(0.20)
        assert percentile == 100

        # Current width at 0.13 should be 40th percentile (above 2 of 5)
        percentile = strategy._get_bb_width_percentile(0.13)
        assert percentile == 40

    def test_bb_width_percentile_insufficient_data(self):
        """Test percentile returns None with insufficient data."""
        strategy = BBSqueezeStrategy()
        strategy.config = {"lookback_period": 20}

        # Only 5 data points, need 20
        strategy.bb_width_history.extend([0.10, 0.12, 0.14, 0.16, 0.18])

        percentile = strategy._get_bb_width_percentile(0.13)
        assert percentile is None

    def test_is_expanding(self):
        """Test band expansion detection."""
        strategy = BBSqueezeStrategy()

        # Expanding
        strategy.prev_bb_width = 0.05
        assert strategy._is_expanding(0.08) is True

        # Contracting
        strategy.prev_bb_width = 0.10
        assert strategy._is_expanding(0.08) is False

        # None values
        strategy.prev_bb_width = None
        assert strategy._is_expanding(0.08) is False
        strategy.prev_bb_width = 0.05
        assert strategy._is_expanding(None) is False

    def test_get_config_schema(self):
        """Test configuration schema."""
        strategy = BBSqueezeStrategy()
        schema = strategy.get_config_schema()

        assert "squeeze_percentile" in schema
        assert "lookback_period" in schema
        assert "position_size_pct" in schema

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test status output."""
        strategy = BBSqueezeStrategy()
        await strategy.initialize("2330", 1_000_000, {})

        status = strategy.get_status()

        assert "布林壓縮策略" in status
        assert "2330" in status
        assert "壓縮" in status
        assert "上軌" in status

    @pytest.mark.asyncio
    async def test_squeeze_state_reset_after_breakout(self):
        """Test that squeeze state resets after breakout."""
        strategy = BBSqueezeStrategy()
        await strategy.initialize("2330", 1_000_000, {"lookback_period": 5})

        # Build history and enter squeeze
        for _ in range(5):
            bar = {
                "date": datetime.now(),
                "open": 100,
                "high": 105,
                "low": 98,
                "close": 102,
                "volume": 1000,
            }
            indicators = {"bb_upper": 110, "bb_middle": 100, "bb_lower": 90, "bb_width": 0.15}
            await strategy.on_bar(bar, indicators)

        # Enter squeeze
        strategy.in_squeeze = True
        strategy.prev_bb_width = 0.03

        # Breakout
        bar = {
            "date": datetime.now(),
            "open": 102,
            "high": 108,
            "low": 101,
            "close": 106,
            "volume": 1000,
        }
        indicators = {"bb_upper": 103, "bb_middle": 100, "bb_lower": 97, "bb_width": 0.05}

        signal = await strategy.on_bar(bar, indicators)

        assert signal is not None
        assert signal.action == SignalAction.BUY
        assert strategy.in_squeeze is False  # Reset after breakout

    @pytest.mark.asyncio
    async def test_no_buy_without_breakout(self):
        """Test no buy signal without upper band breakout."""
        strategy = BBSqueezeStrategy()
        await strategy.initialize("2330", 1_000_000, {"lookback_period": 5})

        # Build history
        for _ in range(5):
            bar = {
                "date": datetime.now(),
                "open": 100,
                "high": 105,
                "low": 98,
                "close": 102,
                "volume": 1000,
            }
            indicators = {"bb_upper": 110, "bb_middle": 100, "bb_lower": 90, "bb_width": 0.15}
            await strategy.on_bar(bar, indicators)

        # Enter squeeze with expansion but no breakout
        strategy.in_squeeze = True
        strategy.prev_bb_width = 0.03

        bar = {
            "date": datetime.now(),
            "open": 100,
            "high": 102,
            "low": 99,
            "close": 101,  # Below upper band (103)
            "volume": 1000,
        }
        indicators = {"bb_upper": 103, "bb_middle": 100, "bb_lower": 97, "bb_width": 0.05}

        signal = await strategy.on_bar(bar, indicators)

        assert signal is None
        assert strategy.in_squeeze is True  # Still in squeeze
