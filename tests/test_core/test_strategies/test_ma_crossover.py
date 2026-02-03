"""Tests for MA Crossover Strategy."""

import pytest
from datetime import datetime

from pulse.core.strategies.ma_crossover import MACrossoverStrategy
from pulse.core.strategies.base import SignalAction


class TestMACrossoverStrategy:
    """Test MACrossoverStrategy class."""

    def test_strategy_initialization(self):
        """Test strategy initialization with default parameters."""
        strategy = MACrossoverStrategy()

        assert strategy.name == "均線交叉策略"
        assert strategy.ticker == ""
        assert strategy.prev_ema_fast is None
        assert strategy.prev_ema_slow is None

    @pytest.mark.asyncio
    async def test_strategy_initialize(self):
        """Test strategy initialization method."""
        strategy = MACrossoverStrategy()
        await strategy.initialize("2330", 1_000_000, {})

        assert strategy.ticker == "2330"
        assert strategy.state is not None
        assert strategy.state.cash == 1_000_000
        assert strategy.config["ema_fast"] == 9
        assert strategy.config["ema_slow"] == 21
        assert strategy.config["ma_filter"] == 50

    @pytest.mark.asyncio
    async def test_strategy_initialize_custom_config(self):
        """Test strategy initialization with custom config."""
        strategy = MACrossoverStrategy()
        await strategy.initialize(
            "2330",
            1_000_000,
            {
                "ema_fast": 5,
                "ema_slow": 10,
                "ma_filter": 20,
                "position_size_pct": 0.3,
            },
        )

        assert strategy.config["ema_fast"] == 5
        assert strategy.config["ema_slow"] == 10
        assert strategy.config["ma_filter"] == 20
        assert strategy.config["position_size_pct"] == 0.3

    @pytest.mark.asyncio
    async def test_no_signal_without_conditions(self):
        """Test no signal when conditions not met."""
        strategy = MACrossoverStrategy()
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
            "ema_9": 95,  # Below EMA 21
            "ema_21": 100,
            "ma_50": 105,  # Close is below MA50
        }

        signal = await strategy.on_bar(bar, indicators)
        assert signal is None

    @pytest.mark.asyncio
    async def test_buy_signal_on_golden_cross(self):
        """Test buy signal on EMA golden cross with MA filter."""
        strategy = MACrossoverStrategy()
        await strategy.initialize("2330", 1_000_000, {})

        # First bar to set previous EMA values (fast below slow)
        bar1 = {
            "date": datetime.now(),
            "open": 100,
            "high": 105,
            "low": 98,
            "close": 102,
            "volume": 1000,
        }
        indicators1 = {
            "ema_9": 95,  # Below EMA 21
            "ema_21": 100,
            "ma_50": 90,
        }
        await strategy.on_bar(bar1, indicators1)

        # Second bar with golden cross
        bar2 = {
            "date": datetime.now(),
            "open": 105,
            "high": 110,
            "low": 104,
            "close": 108,  # Above MA50
            "volume": 1000,
        }
        indicators2 = {
            "ema_9": 102,  # Now above EMA 21 (golden cross)
            "ema_21": 100,
            "ma_50": 95,  # Close > MA50
        }

        signal = await strategy.on_bar(bar2, indicators2)

        assert signal is not None
        assert signal.action == SignalAction.BUY
        assert "均線黃金交叉" in signal.reason

    @pytest.mark.asyncio
    async def test_no_buy_without_ma_filter(self):
        """Test no buy signal when close is below MA filter."""
        strategy = MACrossoverStrategy()
        await strategy.initialize("2330", 1_000_000, {})

        # First bar to set previous EMA values
        bar1 = {
            "date": datetime.now(),
            "open": 100,
            "high": 105,
            "low": 98,
            "close": 102,
            "volume": 1000,
        }
        indicators1 = {
            "ema_9": 95,
            "ema_21": 100,
            "ma_50": 110,
        }
        await strategy.on_bar(bar1, indicators1)

        # Second bar with golden cross but below MA50
        bar2 = {
            "date": datetime.now(),
            "open": 105,
            "high": 110,
            "low": 104,
            "close": 108,  # Below MA50 (110)
            "volume": 1000,
        }
        indicators2 = {
            "ema_9": 102,
            "ema_21": 100,
            "ma_50": 110,  # Close < MA50
        }

        signal = await strategy.on_bar(bar2, indicators2)

        assert signal is None

    @pytest.mark.asyncio
    async def test_sell_signal_on_death_cross(self):
        """Test sell signal on EMA death cross."""
        strategy = MACrossoverStrategy()
        await strategy.initialize("2330", 1_000_000, {})

        # Simulate having a position with previous EMA fast above slow
        strategy.state.positions = 1
        strategy.state.total_shares = 1000
        strategy.prev_ema_fast = 102
        strategy.prev_ema_slow = 100

        bar = {
            "date": datetime.now(),
            "open": 95,
            "high": 98,
            "low": 94,
            "close": 96,
            "volume": 1000,
        }
        indicators = {
            "ema_9": 98,  # Now below EMA 21 (death cross)
            "ema_21": 100,
            "ma_50": 90,
        }

        signal = await strategy.on_bar(bar, indicators)

        assert signal is not None
        assert signal.action == SignalAction.SELL
        assert "EMA 死亡交叉" in signal.reason

    @pytest.mark.asyncio
    async def test_sell_signal_below_ma_filter(self):
        """Test sell signal when price drops below MA filter."""
        strategy = MACrossoverStrategy()
        await strategy.initialize("2330", 1_000_000, {})

        # Simulate having a position
        strategy.state.positions = 1
        strategy.state.total_shares = 1000
        strategy.prev_ema_fast = 102
        strategy.prev_ema_slow = 100

        bar = {
            "date": datetime.now(),
            "open": 85,
            "high": 88,
            "low": 84,
            "close": 86,  # Below MA50
            "volume": 1000,
        }
        indicators = {
            "ema_9": 102,  # Still above (no death cross)
            "ema_21": 100,
            "ma_50": 90,  # Close < MA50
        }

        signal = await strategy.on_bar(bar, indicators)

        assert signal is not None
        assert signal.action == SignalAction.SELL
        assert "跌破趨勢線" in signal.reason

    def test_golden_cross_detection(self):
        """Test EMA golden cross detection logic."""
        strategy = MACrossoverStrategy()

        # Set previous values: fast below slow
        strategy.prev_ema_fast = 95
        strategy.prev_ema_slow = 100

        # Current: fast above slow (golden cross)
        assert strategy._is_golden_cross(102, 100) is True

        # No cross - fast still above
        strategy.prev_ema_fast = 102
        strategy.prev_ema_slow = 100
        assert strategy._is_golden_cross(105, 100) is False

    def test_death_cross_detection(self):
        """Test EMA death cross detection logic."""
        strategy = MACrossoverStrategy()

        # Set previous values: fast above slow
        strategy.prev_ema_fast = 105
        strategy.prev_ema_slow = 100

        # Current: fast below slow (death cross)
        assert strategy._is_death_cross(98, 100) is True

        # No cross - fast still below
        strategy.prev_ema_fast = 95
        strategy.prev_ema_slow = 100
        assert strategy._is_death_cross(93, 100) is False

    def test_cross_detection_with_none_values(self):
        """Test cross detection with None values."""
        strategy = MACrossoverStrategy()

        # None current values
        assert strategy._is_golden_cross(None, 100) is False
        assert strategy._is_golden_cross(100, None) is False
        assert strategy._is_death_cross(None, 100) is False
        assert strategy._is_death_cross(100, None) is False

        # None previous values
        strategy.prev_ema_fast = None
        strategy.prev_ema_slow = 100
        assert strategy._is_golden_cross(105, 100) is False

    def test_get_config_schema(self):
        """Test configuration schema."""
        strategy = MACrossoverStrategy()
        schema = strategy.get_config_schema()

        assert "ema_fast" in schema
        assert "ema_slow" in schema
        assert "ma_filter" in schema
        assert "position_size_pct" in schema

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test status output."""
        strategy = MACrossoverStrategy()
        await strategy.initialize("2330", 1_000_000, {})

        status = strategy.get_status()

        assert "均線交叉策略" in status
        assert "2330" in status
        assert "EMA" in status
        assert "MA" in status

    @pytest.mark.asyncio
    async def test_calculate_buy_quantity(self):
        """Test buy quantity calculation."""
        strategy = MACrossoverStrategy()
        await strategy.initialize("2330", 1_000_000, {"position_size_pct": 0.2})

        # 20% of 1,000,000 = 200,000
        # At price 100, should buy 2000 shares
        quantity = strategy._calculate_buy_quantity(100)
        assert quantity == 2000

    @pytest.mark.asyncio
    async def test_no_buy_with_zero_cash(self):
        """Test no buy signal when cash is zero."""
        strategy = MACrossoverStrategy()
        await strategy.initialize("2330", 1_000_000, {})
        strategy.state.cash = 0

        # Set up golden cross conditions
        strategy.prev_ema_fast = 95
        strategy.prev_ema_slow = 100

        bar = {
            "date": datetime.now(),
            "open": 100,
            "high": 105,
            "low": 98,
            "close": 102,
            "volume": 1000,
        }
        indicators = {
            "ema_9": 102,
            "ema_21": 100,
            "ma_50": 90,
        }

        signal = await strategy.on_bar(bar, indicators)
        assert signal is None  # No signal because can't afford shares
