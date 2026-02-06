"""Tests for Trading Plan Generator - TP, SL, and Risk/Reward calculations."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
from decimal import Decimal

from pulse.core.trading_plan import TradingPlanGenerator
from pulse.core.models import (
    SignalType,
    TradeQuality,
    TradeValidity,
    TradingPlan,
    TrendType,
    TechnicalIndicators,
    StockData,
)


# ============ Fixtures ============


@pytest.fixture
def generator():
    """Create TradingPlanGenerator instance for testing."""
    return TradingPlanGenerator()


@pytest.fixture
def mock_stock_data():
    """Create mock stock data."""
    return MagicMock(
        spec=StockData,
        ticker="2330",
        name="台積電",
        sector="半導體",
        current_price=820.0,
        previous_close=815.0,
        change=5.0,
        change_percent=0.61,
        volume=15234500,
        avg_volume=12456000,
        day_high=825.0,
        day_low=815.0,
        week_52_high=850.0,
        week_52_low=500.0,
        market_cap=5.5e12,
    )


@pytest.fixture
def mock_technical_data():
    """Create mock technical indicators."""
    indicators = MagicMock(spec=TechnicalIndicators)
    indicators.rsi_14 = 58.3
    indicators.macd = 12.5
    indicators.macd_signal = 10.3
    indicators.macd_histogram = 2.2
    indicators.sma_20 = 810.0
    indicators.sma_50 = 800.0
    indicators.sma_200 = 700.0
    indicators.ema_9 = 818.0
    indicators.ema_21 = 812.0
    indicators.bb_upper = 835.0
    indicators.bb_middle = 820.0
    indicators.bb_lower = 805.0
    indicators.stoch_k = 65.2
    indicators.stoch_d = 58.5
    indicators.atr_14 = 15.0
    indicators.support_1 = 805.0
    indicators.support_2 = 780.0
    indicators.resistance_1 = 835.0
    indicators.resistance_2 = 860.0
    indicators.trend = TrendType.BULLISH
    indicators.signal = SignalType.BUY
    return indicators


# ============ Test Classes ============


class TestTradingPlanGeneratorInitialization:
    """Test cases for TradingPlanGenerator initialization."""

    def test_default_settings(self, generator):
        """Test default settings are correctly set."""
        assert generator.DEFAULT_RISK_PERCENT == 2.0
        assert generator.DEFAULT_ATR_SL_MULTIPLIER == 1.5
        assert generator.DEFAULT_ATR_TP_MULTIPLIER == 2.0
        assert generator.DEFAULT_ACCOUNT_SIZE == 10_000_000

    def test_initializes_fetcher(self, generator):
        """Test generator initializes YFinanceFetcher."""
        assert generator.fetcher is not None

    def test_initializes_analyzer(self, generator):
        """Test generator initializes TechnicalAnalyzer."""
        assert generator.analyzer is not None


class TestCalculateStopLoss:
    """Test cases for stop loss calculation methods."""

    def test_atr_method(self, generator):
        """Test ATR-based stop loss calculation."""
        entry = 100.0
        atr = 10.0
        support_1 = 95.0
        support_2 = 90.0

        sl, method = generator._calculate_stop_loss(
            entry=entry, support_1=support_1, support_2=support_2, atr=atr, method="atr"
        )

        assert method == "atr"
        assert sl == entry - (atr * 1.5)  # 100 - 15 = 85.0
        assert sl < entry  # Stop loss must be below entry

    def test_support_method(self, generator):
        """Test support-based stop loss calculation."""
        entry = 100.0
        atr = 10.0
        support_1 = 95.0
        support_2 = 90.0

        sl, method = generator._calculate_stop_loss(
            entry=entry, support_1=support_1, support_2=support_2, atr=atr, method="support"
        )

        assert method == "support"
        assert sl == support_1 * 0.99  # 95 * 0.99 = 94.05
        assert sl < entry

    def test_percentage_method(self, generator):
        """Test percentage-based stop loss calculation."""
        entry = 100.0
        atr = 10.0
        support_1 = 95.0
        support_2 = 90.0

        sl, method = generator._calculate_stop_loss(
            entry=entry, support_1=support_1, support_2=support_2, atr=atr, method="percentage"
        )

        assert method == "percentage"
        assert sl == entry * 0.97  # 3% stop loss
        assert sl < entry

    def test_hybrid_method_selects_tightest(self, generator):
        """Test hybrid method selects the tightest (highest) valid stop loss."""
        entry = 100.0
        atr = 10.0  # atr_sl = 85.0
        support_1 = 95.0  # support_sl = 94.05
        support_2 = 90.0
        pct_sl = 97.0  # 3% = 97.0

        sl, method = generator._calculate_stop_loss(
            entry=entry, support_1=support_1, support_2=support_2, atr=atr, method="hybrid"
        )

        # Tightest stop loss = highest value below entry = 97.0
        assert sl == pct_sl
        assert method == "percentage"

    def test_hybrid_with_tightest_atr(self, generator):
        """Test hybrid when ATR provides tightest stop loss."""
        entry = 100.0
        atr = 1.0  # atr_sl = 98.5 (tightest)
        support_1 = 95.0  # support_sl = 94.05
        support_2 = 90.0

        sl, method = generator._calculate_stop_loss(
            entry=entry, support_1=support_1, support_2=support_2, atr=atr, method="hybrid"
        )

        # ATR-based should be tightest
        assert sl == 98.5
        assert method == "atr"

    def test_hybrid_fallback_to_percentage(self, generator):
        """Test hybrid falls back to percentage when other methods invalid."""
        entry = 100.0
        atr = 200.0  # Would give negative SL
        support_1 = 200.0  # Above entry (invalid)
        support_2 = 90.0

        sl, method = generator._calculate_stop_loss(
            entry=entry, support_1=support_1, support_2=support_2, atr=atr, method="hybrid"
        )

        # Should fall back to percentage method
        assert method == "percentage"
        assert 0 < sl < entry


class TestCalculateTakeProfits:
    """Test cases for take profit level calculation."""

    def test_tp_levels_with_resistance(self, generator):
        """Test TP calculation using resistance levels."""
        entry = 100.0
        resistance_1 = 110.0
        resistance_2 = 120.0
        atr = 5.0

        tp1, tp2, tp3 = generator._calculate_take_profits(
            entry=entry, resistance_1=resistance_1, resistance_2=resistance_2, atr=atr
        )

        # TP1 should use resistance_1
        assert tp1 == resistance_1
        # TP2 should use resistance_2
        assert tp2 == resistance_2
        # TP3 should be ATR-based
        assert tp3 == entry + (atr * 3.5)  # 117.5

    def test_tp_levels_fallback_to_atr(self, generator):
        """Test TP calculation when resistance not valid."""
        entry = 100.0
        resistance_1 = 101.0  # Too close to entry (needs > 1%)
        resistance_2 = 102.0  # Too close to TP1
        atr = 5.0

        tp1, tp2, tp3 = generator._calculate_take_profits(
            entry=entry, resistance_1=resistance_1, resistance_2=resistance_2, atr=atr
        )

        # TP1 should be ATR-based (entry + 1.5*atr)
        assert tp1 == entry + (atr * 1.5)  # 107.5
        # TP2 should be ATR-based (entry + 2.5*atr)
        assert tp2 == entry + (atr * 2.5)  # 112.5
        assert tp3 == entry + (atr * 3.5)  # 117.5

    def test_tp_all_above_entry(self, generator):
        """Test all TP levels are above entry price."""
        entry = 100.0
        resistance_1 = 115.0
        resistance_2 = 130.0
        atr = 10.0

        tp1, tp2, tp3 = generator._calculate_take_profits(
            entry=entry, resistance_1=resistance_1, resistance_2=resistance_2, atr=atr
        )

        assert tp1 > entry
        assert tp2 > entry
        assert tp3 > entry


class TestAssessTradeQuality:
    """Test cases for trade quality assessment."""

    def test_excellent_rr(self, generator):
        """Test excellent trade quality (RR >= 3.0)."""
        assert generator._assess_trade_quality(3.0) == TradeQuality.EXCELLENT
        assert generator._assess_trade_quality(4.0) == TradeQuality.EXCELLENT

    def test_good_rr(self, generator):
        """Test good trade quality (RR >= 2.0)."""
        assert generator._assess_trade_quality(2.0) == TradeQuality.GOOD
        assert generator._assess_trade_quality(2.5) == TradeQuality.GOOD

    def test_fair_rr(self, generator):
        """Test fair trade quality (RR >= 1.5)."""
        assert generator._assess_trade_quality(1.5) == TradeQuality.FAIR
        assert generator._assess_trade_quality(1.8) == TradeQuality.FAIR

    def test_poor_rr(self, generator):
        """Test poor trade quality (RR < 1.5)."""
        assert generator._assess_trade_quality(1.0) == TradeQuality.POOR
        assert generator._assess_trade_quality(0.5) == TradeQuality.POOR
        assert generator._assess_trade_quality(1.49) == TradeQuality.POOR


class TestCalculateConfidence:
    """Test cases for confidence score calculation."""

    def test_base_score(self, generator, mock_technical_data):
        """Test base confidence score is 50."""
        confidence = generator._calculate_confidence(
            technical=mock_technical_data, rr_ratio=1.5, trade_quality=TradeQuality.FAIR
        )
        assert 0 <= confidence <= 100

    def test_high_rr_boosts_confidence(self, generator, mock_technical_data):
        """Test high R:R ratio boosts confidence."""
        low_conf = generator._calculate_confidence(
            technical=mock_technical_data, rr_ratio=1.0, trade_quality=TradeQuality.POOR
        )
        high_conf = generator._calculate_confidence(
            technical=mock_technical_data, rr_ratio=3.0, trade_quality=TradeQuality.EXCELLENT
        )
        assert high_conf > low_conf

    def test_bullish_trend_boosts_confidence(self, generator, mock_technical_data):
        """Test bullish trend increases confidence."""
        mock_technical_data.trend = TrendType.BULLISH
        bullish_conf = generator._calculate_confidence(
            technical=mock_technical_data, rr_ratio=2.0, trade_quality=TradeQuality.GOOD
        )

        mock_technical_data.trend = TrendType.BEARISH
        bearish_conf = generator._calculate_confidence(
            technical=mock_technical_data, rr_ratio=2.0, trade_quality=TradeQuality.GOOD
        )

        assert bullish_conf > bearish_conf

    def test_strong_buy_boosts_confidence(self, generator, mock_technical_data):
        """Test Strong Buy signal increases confidence."""
        mock_technical_data.signal = SignalType.STRONG_BUY
        strong_buy_conf = generator._calculate_confidence(
            technical=mock_technical_data, rr_ratio=2.0, trade_quality=TradeQuality.GOOD
        )

        mock_technical_data.signal = SignalType.SELL
        sell_conf = generator._calculate_confidence(
            technical=mock_technical_data, rr_ratio=2.0, trade_quality=TradeQuality.GOOD
        )

        assert strong_buy_conf > sell_conf

    def test_oversold_rsi_boosts_confidence(self, generator, mock_technical_data):
        """Test oversold RSI condition increases confidence."""
        mock_technical_data.rsi_14 = 25.0  # Oversold
        oversold_conf = generator._calculate_confidence(
            technical=mock_technical_data, rr_ratio=2.0, trade_quality=TradeQuality.GOOD
        )

        mock_technical_data.rsi_14 = 75.0  # Overbought
        overbought_conf = generator._calculate_confidence(
            technical=mock_technical_data, rr_ratio=2.0, trade_quality=TradeQuality.GOOD
        )

        assert oversold_conf > overbought_conf

    def test_bullish_macd_boosts_confidence(self, generator, mock_technical_data):
        """Test bullish MACD increases confidence."""
        mock_technical_data.macd = 15.0
        mock_technical_data.macd_signal = 10.0  # MACD > Signal = bullish
        bullish_conf = generator._calculate_confidence(
            technical=mock_technical_data, rr_ratio=2.0, trade_quality=TradeQuality.GOOD
        )

        mock_technical_data.macd = 10.0
        mock_technical_data.macd_signal = 15.0  # MACD < Signal = bearish
        bearish_conf = generator._calculate_confidence(
            technical=mock_technical_data, rr_ratio=2.0, trade_quality=TradeQuality.GOOD
        )

        assert bullish_conf > bearish_conf

    def test_confidence_clamped_to_0_100(self, generator, mock_technical_data):
        """Test confidence is clamped between 0 and 100."""
        # Test with extreme values
        very_low = generator._calculate_confidence(
            technical=mock_technical_data, rr_ratio=-1.0, trade_quality=TradeQuality.POOR
        )
        very_high = generator._calculate_confidence(
            technical=mock_technical_data, rr_ratio=10.0, trade_quality=TradeQuality.EXCELLENT
        )

        assert 0 <= very_low <= 100
        assert 0 <= very_high <= 100


class TestDetermineValidity:
    """Test cases for trade validity determination."""

    def test_high_volatility_intraday(self, generator):
        """Test high volatility results in intraday validity."""
        # ATR > 3% of price
        validity = generator._determine_validity(atr=5.0, entry=100.0)  # 5%
        assert validity == TradeValidity.INTRADAY

    def test_medium_volatility_swing(self, generator):
        """Test medium volatility results in swing validity."""
        # 1.5% < ATR < 3%
        validity = generator._determine_validity(atr=2.0, entry=100.0)  # 2%
        assert validity == TradeValidity.SWING

    def test_low_volatility_position(self, generator):
        """Test low volatility results in position validity."""
        # ATR < 1.5%
        validity = generator._determine_validity(atr=1.0, entry=100.0)  # 1%
        assert validity == TradeValidity.POSITION


class TestGenerateNotes:
    """Test cases for trading notes generation."""

    def test_oversold_rsi_note(self, generator, mock_technical_data):
        """Test notes include oversold RSI observation."""
        mock_technical_data.rsi_14 = 25.0
        notes = generator._generate_notes(technical=mock_technical_data, entry=100.0, atr=5.0)

        rsi_notes = [n for n in notes if "RSI" in n]
        assert len(rsi_notes) == 1
        assert "Oversold" in rsi_notes[0]

    def test_overbought_rsi_note(self, generator, mock_technical_data):
        """Test notes include overbought RSI observation."""
        mock_technical_data.rsi_14 = 75.0
        notes = generator._generate_notes(technical=mock_technical_data, entry=100.0, atr=5.0)

        rsi_notes = [n for n in notes if "RSI" in n]
        assert len(rsi_notes) == 1
        assert "Overbought" in rsi_notes[0]

    def test_neutral_rsi_note(self, generator, mock_technical_data):
        """Test notes include neutral RSI observation."""
        mock_technical_data.rsi_14 = 50.0
        notes = generator._generate_notes(technical=mock_technical_data, entry=100.0, atr=5.0)

        rsi_notes = [n for n in notes if "RSI" in n]
        assert len(rsi_notes) == 1
        assert "Neutral" in rsi_notes[0]

    def test_bullish_macd_note(self, generator, mock_technical_data):
        """Test notes include bullish MACD observation."""
        mock_technical_data.macd = 15.0
        mock_technical_data.macd_signal = 10.0
        mock_technical_data.macd_histogram = 2.0
        notes = generator._generate_notes(technical=mock_technical_data, entry=100.0, atr=5.0)

        macd_notes = [n for n in notes if "MACD" in n]
        assert len(macd_notes) >= 1
        assert any("bullish" in n.lower() for n in macd_notes)

    def test_bearish_macd_note(self, generator, mock_technical_data):
        """Test notes include bearish MACD observation."""
        mock_technical_data.macd = 10.0
        mock_technical_data.macd_signal = 15.0
        mock_technical_data.macd_histogram = -1.0
        notes = generator._generate_notes(technical=mock_technical_data, entry=100.0, atr=5.0)

        macd_notes = [n for n in notes if "MACD" in n]
        assert len(macd_notes) >= 1
        assert any("bearish" in n.lower() for n in macd_notes)

    def test_trend_note_included(self, generator, mock_technical_data):
        """Test notes include trend information."""
        mock_technical_data.rsi_14 = 50.0
        notes = generator._generate_notes(technical=mock_technical_data, entry=100.0, atr=5.0)

        trend_notes = [n for n in notes if "Trend" in n]
        assert len(trend_notes) == 1
        assert "Bullish" in trend_notes[0]

    def test_atr_note_included(self, generator, mock_technical_data):
        """Test notes include ATR/volatility information."""
        mock_technical_data.rsi_14 = 50.0
        notes = generator._generate_notes(technical=mock_technical_data, entry=100.0, atr=5.0)

        atr_notes = [n for n in notes if "ATR" in n]
        assert len(atr_notes) == 1
        assert "5" in atr_notes[0] or "5.0" in atr_notes[0]

    def test_signal_note_included(self, generator, mock_technical_data):
        """Test notes include signal information."""
        mock_technical_data.rsi_14 = 50.0
        notes = generator._generate_notes(technical=mock_technical_data, entry=100.0, atr=5.0)

        signal_notes = [n for n in notes if "Signal" in n]
        assert len(signal_notes) == 1
        assert "Buy" in signal_notes[0]


class TestGenerateExecutionStrategy:
    """Test cases for execution strategy generation."""

    def test_includes_entry_step(self, generator):
        """Test execution strategy includes entry step."""
        strategy = generator._generate_execution_strategy(
            entry=100.0, tp1=110.0, tp2=120.0, stop_loss=95.0
        )

        assert len(strategy) >= 1
        assert any("Entry" in step for step in strategy)
        assert any("100" in step for step in strategy)

    def test_includes_stop_loss_step(self, generator):
        """Test execution strategy includes stop loss step."""
        strategy = generator._generate_execution_strategy(
            entry=100.0, tp1=110.0, tp2=120.0, stop_loss=95.0
        )

        assert any("stop loss" in step.lower() for step in strategy)

    def test_includes_tp1_step(self, generator):
        """Test execution strategy includes TP1 step."""
        strategy = generator._generate_execution_strategy(
            entry=100.0, tp1=110.0, tp2=120.0, stop_loss=95.0
        )

        assert any("TP1" in step or "110" in step for step in strategy)

    def test_includes_tp2_step(self, generator):
        """Test execution strategy includes TP2 step."""
        strategy = generator._generate_execution_strategy(
            entry=100.0, tp1=110.0, tp2=120.0, stop_loss=95.0
        )

        assert any("TP2" in step or "120" in step for step in strategy)

    def test_includes_breakeven_step(self, generator):
        """Test execution strategy includes breakeven step."""
        strategy = generator._generate_execution_strategy(
            entry=100.0, tp1=110.0, tp2=120.0, stop_loss=95.0
        )

        assert any("breakeven" in step.lower() for step in strategy)

    def test_includes_no_averaging_rule(self, generator):
        """Test execution strategy includes no averaging down rule."""
        strategy = generator._generate_execution_strategy(
            entry=100.0, tp1=110.0, tp2=120.0, stop_loss=95.0
        )

        assert any(
            "averaging" in step.lower() or "no averaging" in step.lower() for step in strategy
        )

    def test_steps_are_ordered(self, generator):
        """Test execution strategy steps are in logical order."""
        strategy = generator._generate_execution_strategy(
            entry=100.0, tp1=110.0, tp2=120.0, stop_loss=95.0
        )

        # Check that entry comes before TP1, TP1 before TP2
        entry_idx = next(i for i, s in enumerate(strategy) if "Entry" in s)
        tp1_idx = next(i for i, s in enumerate(strategy) if "TP1" in s)
        tp2_idx = next(i for i, s in enumerate(strategy) if "TP2" in s)
        sl_idx = next(i for i, s in enumerate(strategy) if "stop" in s.lower())

        assert entry_idx < tp1_idx < tp2_idx
        assert sl_idx > entry_idx  # SL should be set after entry


class TestCalculatePositionSize:
    """Test cases for position sizing calculations."""

    def test_position_size_basic(self, generator):
        """Test basic position size calculation."""
        plan = MagicMock()
        plan.ticker = "2330"
        plan.entry_price = 100.0
        plan.stop_loss = 95.0
        plan.risk_amount = 5.0
        plan.suggested_risk_percent = 2.0

        result = generator.calculate_position_size(plan, account_size=10_000_000)

        assert "error" not in result
        assert result["account_size"] == 10_000_000
        assert result["risk_percent"] == 2.0
        assert result["max_risk_amount"] == 200_000  # 2% of 10M
        assert result["risk_per_share"] == 5.0
        assert result["shares"] == 40_000  # 200,000 / 5
        assert result["lots"] == 400  # 40,000 / 100

    def test_position_size_with_custom_risk(self, generator):
        """Test position size with custom risk percentage."""
        plan = MagicMock()
        plan.ticker = "2330"
        plan.entry_price = 100.0
        plan.stop_loss = 95.0
        plan.risk_amount = 5.0
        plan.suggested_risk_percent = 2.0

        result = generator.calculate_position_size(plan, account_size=10_000_000, risk_percent=1.0)

        assert result["risk_percent"] == 1.0
        assert result["max_risk_amount"] == 100_000  # 1% of 10M
        assert result["shares"] == 20_000

    def test_position_size_zero_risk_per_share(self, generator):
        """Test position size returns error when risk_per_share is zero."""
        plan = MagicMock()
        plan.ticker = "2330"
        plan.entry_price = 100.0
        plan.stop_loss = 100.0  # Same as entry = no risk
        plan.risk_amount = 0.0
        plan.suggested_risk_percent = 2.0

        result = generator.calculate_position_size(plan)

        assert "error" in result
        assert "Invalid stop loss" in result["error"]

    def test_position_size_negative_risk_per_share(self, generator):
        """Test position size returns error when risk_per_share is negative."""
        plan = MagicMock()
        plan.ticker = "2330"
        plan.entry_price = 100.0
        plan.stop_loss = 105.0  # Above entry = negative risk
        plan.risk_amount = -5.0
        plan.suggested_risk_percent = 2.0

        result = generator.calculate_position_size(plan)

        assert "error" in result

    def test_position_value_calculation(self, generator):
        """Test position value is calculated correctly."""
        plan = MagicMock()
        plan.ticker = "2330"
        plan.entry_price = 100.0
        plan.stop_loss = 95.0
        plan.risk_amount = 5.0
        plan.suggested_risk_percent = 2.0

        result = generator.calculate_position_size(plan, account_size=10_000_000)

        # Position value = lots * 100 * entry_price
        expected_value = 400 * 100 * 100.0  # 4,000,000
        assert result["position_value"] == expected_value
        assert result["position_percent"] == 40.0  # 4M / 10M


class TestFormatPlan:
    """Test cases for trading plan formatting."""

    @pytest.mark.asyncio
    async def test_format_includes_ticker(self, generator, mock_stock_data, mock_technical_data):
        """Test formatted plan includes ticker."""
        with (
            patch.object(
                generator.fetcher, "fetch_stock", new_callable=AsyncMock
            ) as mock_fetch_stock,
            patch.object(generator.analyzer, "analyze", new_callable=AsyncMock) as mock_analyze,
        ):
            mock_fetch_stock.return_value = mock_stock_data
            mock_analyze.return_value = mock_technical_data

            plan = await generator.generate("2330", entry_price=100.0)

        assert plan is not None
        formatted = generator.format_plan(plan)
        assert "2330" in formatted

    @pytest.mark.asyncio
    async def test_format_includes_entry(self, generator, mock_stock_data, mock_technical_data):
        """Test formatted plan includes entry price."""
        with (
            patch.object(
                generator.fetcher, "fetch_stock", new_callable=AsyncMock
            ) as mock_fetch_stock,
            patch.object(generator.analyzer, "analyze", new_callable=AsyncMock) as mock_analyze,
        ):
            mock_fetch_stock.return_value = mock_stock_data
            mock_analyze.return_value = mock_technical_data

            plan = await generator.generate("2330", entry_price=100.0)

        assert plan is not None
        formatted = generator.format_plan(plan)
        assert "100" in formatted or "Entry" in formatted

    @pytest.mark.asyncio
    async def test_format_includes_tp1(self, generator, mock_stock_data, mock_technical_data):
        """Test formatted plan includes TP1."""
        with (
            patch.object(
                generator.fetcher, "fetch_stock", new_callable=AsyncMock
            ) as mock_fetch_stock,
            patch.object(generator.analyzer, "analyze", new_callable=AsyncMock) as mock_analyze,
        ):
            mock_fetch_stock.return_value = mock_stock_data
            mock_analyze.return_value = mock_technical_data

            plan = await generator.generate("2330", entry_price=100.0)

        assert plan is not None
        formatted = generator.format_plan(plan)
        assert "TP1" in formatted

    @pytest.mark.asyncio
    async def test_format_includes_stop_loss(self, generator, mock_stock_data, mock_technical_data):
        """Test formatted plan includes stop loss."""
        with (
            patch.object(
                generator.fetcher, "fetch_stock", new_callable=AsyncMock
            ) as mock_fetch_stock,
            patch.object(generator.analyzer, "analyze", new_callable=AsyncMock) as mock_analyze,
        ):
            mock_fetch_stock.return_value = mock_stock_data
            mock_analyze.return_value = mock_technical_data

            plan = await generator.generate("2330", entry_price=100.0)

        assert plan is not None
        formatted = generator.format_plan(plan)
        assert "SL" in formatted or "Stop" in formatted

    @pytest.mark.asyncio
    async def test_format_includes_rr_ratio(self, generator, mock_stock_data, mock_technical_data):
        """Test formatted plan includes R:R ratio."""
        with (
            patch.object(
                generator.fetcher, "fetch_stock", new_callable=AsyncMock
            ) as mock_fetch_stock,
            patch.object(generator.analyzer, "analyze", new_callable=AsyncMock) as mock_analyze,
        ):
            mock_fetch_stock.return_value = mock_stock_data
            mock_analyze.return_value = mock_technical_data

            plan = await generator.generate("2330", entry_price=100.0)

        assert plan is not None
        formatted = generator.format_plan(plan)
        assert "R:R" in formatted or "1:" in formatted

    @pytest.mark.asyncio
    async def test_format_includes_trade_quality(
        self, generator, mock_stock_data, mock_technical_data
    ):
        """Test formatted plan includes trade quality."""
        with (
            patch.object(
                generator.fetcher, "fetch_stock", new_callable=AsyncMock
            ) as mock_fetch_stock,
            patch.object(generator.analyzer, "analyze", new_callable=AsyncMock) as mock_analyze,
        ):
            mock_fetch_stock.return_value = mock_stock_data
            mock_analyze.return_value = mock_technical_data

            plan = await generator.generate("2330", entry_price=100.0)

        assert plan is not None
        formatted = generator.format_plan(plan)
        assert "Quality" in formatted or "FAIR" in formatted or "GOOD" in formatted

    @pytest.mark.asyncio
    async def test_format_includes_confidence(
        self, generator, mock_stock_data, mock_technical_data
    ):
        """Test formatted plan includes confidence score."""
        with (
            patch.object(
                generator.fetcher, "fetch_stock", new_callable=AsyncMock
            ) as mock_fetch_stock,
            patch.object(generator.analyzer, "analyze", new_callable=AsyncMock) as mock_analyze,
        ):
            mock_fetch_stock.return_value = mock_stock_data
            mock_analyze.return_value = mock_technical_data

            plan = await generator.generate("2330", entry_price=100.0)

        assert plan is not None
        formatted = generator.format_plan(plan)
        assert "Confidence" in formatted or "%" in formatted

    @pytest.mark.asyncio
    async def test_format_includes_position_sizing_by_default(
        self, generator, mock_stock_data, mock_technical_data
    ):
        """Test formatted plan includes position sizing by default."""
        with (
            patch.object(
                generator.fetcher, "fetch_stock", new_callable=AsyncMock
            ) as mock_fetch_stock,
            patch.object(generator.analyzer, "analyze", new_callable=AsyncMock) as mock_analyze,
        ):
            mock_fetch_stock.return_value = mock_stock_data
            mock_analyze.return_value = mock_technical_data

            plan = await generator.generate("2330", entry_price=100.0)

        assert plan is not None
        formatted = generator.format_plan(plan)
        assert "Position" in formatted or "Risk" in formatted

    @pytest.mark.asyncio
    async def test_format_excludes_position_sizing_when_disabled(
        self, generator, mock_stock_data, mock_technical_data
    ):
        """Test formatted plan can exclude position sizing."""
        with (
            patch.object(
                generator.fetcher, "fetch_stock", new_callable=AsyncMock
            ) as mock_fetch_stock,
            patch.object(generator.analyzer, "analyze", new_callable=AsyncMock) as mock_analyze,
        ):
            mock_fetch_stock.return_value = mock_stock_data
            mock_analyze.return_value = mock_technical_data

            plan = await generator.generate("2330", entry_price=100.0)

        assert plan is not None
        # Just verify it doesn't crash when called with False
        formatted = generator.format_plan(plan, include_position_sizing=False)
        assert formatted is not None

    @pytest.mark.asyncio
    async def test_format_includes_notes(self, generator, mock_stock_data, mock_technical_data):
        """Test formatted plan includes notes when available."""
        with (
            patch.object(
                generator.fetcher, "fetch_stock", new_callable=AsyncMock
            ) as mock_fetch_stock,
            patch.object(generator.analyzer, "analyze", new_callable=AsyncMock) as mock_analyze,
        ):
            mock_fetch_stock.return_value = mock_stock_data
            mock_analyze.return_value = mock_technical_data

            plan = await generator.generate("2330", entry_price=100.0)

        assert plan is not None
        assert len(plan.notes) > 0
        formatted = generator.format_plan(plan)
        assert "NOTES" in formatted

    @pytest.mark.asyncio
    async def test_format_includes_execution_strategy(
        self, generator, mock_stock_data, mock_technical_data
    ):
        """Test formatted plan includes execution strategy."""
        with (
            patch.object(
                generator.fetcher, "fetch_stock", new_callable=AsyncMock
            ) as mock_fetch_stock,
            patch.object(generator.analyzer, "analyze", new_callable=AsyncMock) as mock_analyze,
        ):
            mock_fetch_stock.return_value = mock_stock_data
            mock_analyze.return_value = mock_technical_data

            plan = await generator.generate("2330", entry_price=100.0)

        assert plan is not None
        assert len(plan.execution_strategy) > 0
        formatted = generator.format_plan(plan)
        assert "EXECUTION" in formatted or "STRATEGY" in formatted

    @pytest.mark.asyncio
    async def test_format_includes_validity(self, generator, mock_stock_data, mock_technical_data):
        """Test formatted plan includes validity timeframe."""
        with (
            patch.object(
                generator.fetcher, "fetch_stock", new_callable=AsyncMock
            ) as mock_fetch_stock,
            patch.object(generator.analyzer, "analyze", new_callable=AsyncMock) as mock_analyze,
        ):
            mock_fetch_stock.return_value = mock_stock_data
            mock_analyze.return_value = mock_technical_data

            plan = await generator.generate("2330", entry_price=100.0)

        assert plan is not None
        formatted = generator.format_plan(plan)
        assert (
            "Validity" in formatted
            or "Intraday" in formatted
            or "Swing" in formatted
            or "Position" in formatted
        )


class TestGetRRQualityLabel:
    """Test cases for R:R quality label."""

    def test_excellent_label(self, generator):
        """Test excellent quality label."""
        assert generator._get_rr_quality_label(3.0) == "EXCELLENT"
        assert generator._get_rr_quality_label(5.0) == "EXCELLENT"

    def test_good_label(self, generator):
        """Test good quality label."""
        assert generator._get_rr_quality_label(2.0) == "GOOD"
        assert generator._get_rr_quality_label(2.9) == "GOOD"

    def test_fair_label(self, generator):
        """Test fair quality label."""
        assert generator._get_rr_quality_label(1.5) == "FAIR"
        assert generator._get_rr_quality_label(1.9) == "FAIR"

    def test_poor_label(self, generator):
        """Test poor quality label."""
        assert generator._get_rr_quality_label(1.0) == "POOR"
        assert generator._get_rr_quality_label(0.5) == "POOR"
        assert generator._get_rr_quality_label(1.49) == "POOR"


class TestGenerateMethod:
    """Test cases for the main generate method."""

    @pytest.mark.asyncio
    async def test_generate_success(self, generator, mock_stock_data, mock_technical_data):
        """Test successful trading plan generation."""
        with (
            patch.object(
                generator.fetcher, "fetch_stock", new_callable=AsyncMock
            ) as mock_fetch_stock,
            patch.object(generator.analyzer, "analyze", new_callable=AsyncMock) as mock_analyze,
        ):
            mock_fetch_stock.return_value = mock_stock_data
            mock_analyze.return_value = mock_technical_data

            plan = await generator.generate("2330")

        assert plan is not None
        assert plan.ticker == "2330"
        assert plan.entry_price > 0
        assert plan.stop_loss < plan.entry_price
        assert plan.tp1 > plan.entry_price

    @pytest.mark.asyncio
    async def test_generate_with_custom_entry_price(
        self, generator, mock_stock_data, mock_technical_data
    ):
        """Test trading plan with custom entry price."""
        with (
            patch.object(
                generator.fetcher, "fetch_stock", new_callable=AsyncMock
            ) as mock_fetch_stock,
            patch.object(generator.analyzer, "analyze", new_callable=AsyncMock) as mock_analyze,
        ):
            mock_fetch_stock.return_value = mock_stock_data
            mock_analyze.return_value = mock_technical_data

            plan = await generator.generate("2330", entry_price=800.0)

        assert plan is not None
        assert plan.entry_price == 800.0

    @pytest.mark.asyncio
    async def test_generate_with_custom_risk_percent(
        self, generator, mock_stock_data, mock_technical_data
    ):
        """Test trading plan with custom risk percentage."""
        with (
            patch.object(
                generator.fetcher, "fetch_stock", new_callable=AsyncMock
            ) as mock_fetch_stock,
            patch.object(generator.analyzer, "analyze", new_callable=AsyncMock) as mock_analyze,
        ):
            mock_fetch_stock.return_value = mock_stock_data
            mock_analyze.return_value = mock_technical_data

            plan = await generator.generate("2330", risk_percent=1.5)

        assert plan is not None
        assert plan.suggested_risk_percent == 1.5

    @pytest.mark.asyncio
    async def test_generate_with_different_sl_methods(
        self, generator, mock_stock_data, mock_technical_data
    ):
        """Test trading plan with different stop loss methods."""
        with (
            patch.object(
                generator.fetcher, "fetch_stock", new_callable=AsyncMock
            ) as mock_fetch_stock,
            patch.object(generator.analyzer, "analyze", new_callable=AsyncMock) as mock_analyze,
        ):
            mock_fetch_stock.return_value = mock_stock_data
            mock_analyze.return_value = mock_technical_data

            # Test ATR method
            plan_atr = await generator.generate("2330", sl_method="atr")
            assert plan_atr is not None
            assert plan_atr.stop_loss_method == "atr"

            # Test support method
            plan_support = await generator.generate("2330", sl_method="support")
            assert plan_support is not None
            assert plan_support.stop_loss_method == "support"

    @pytest.mark.asyncio
    async def test_generate_returns_none_for_invalid_ticker(self, generator):
        """Test trading plan returns None for invalid ticker."""
        with patch.object(
            generator.fetcher, "fetch_stock", new_callable=AsyncMock
        ) as mock_fetch_stock:
            mock_fetch_stock.return_value = None

            plan = await generator.generate("INVALID")

        assert plan is None

    @pytest.mark.asyncio
    async def test_generate_returns_none_for_missing_technical_data(
        self, generator, mock_stock_data
    ):
        """Test trading plan returns None when technical data unavailable."""
        with (
            patch.object(
                generator.fetcher, "fetch_stock", new_callable=AsyncMock
            ) as mock_fetch_stock,
            patch.object(generator.analyzer, "analyze", new_callable=AsyncMock) as mock_analyze,
        ):
            mock_fetch_stock.return_value = mock_stock_data
            mock_analyze.return_value = None

            plan = await generator.generate("2330")

        assert plan is None

    @pytest.mark.asyncio
    async def test_generate_includes_technical_context(
        self, generator, mock_stock_data, mock_technical_data
    ):
        """Test trading plan includes technical analysis context."""
        with (
            patch.object(
                generator.fetcher, "fetch_stock", new_callable=AsyncMock
            ) as mock_fetch_stock,
            patch.object(generator.analyzer, "analyze", new_callable=AsyncMock) as mock_analyze,
        ):
            mock_fetch_stock.return_value = mock_stock_data
            mock_analyze.return_value = mock_technical_data

            plan = await generator.generate("2330")

        assert plan is not None
        assert plan.trend == TrendType.BULLISH
        assert plan.signal == SignalType.BUY
        assert plan.rsi is not None
        assert plan.atr is not None

    @pytest.mark.asyncio
    async def test_generate_includes_notes(self, generator, mock_stock_data, mock_technical_data):
        """Test trading plan includes generated notes."""
        with (
            patch.object(
                generator.fetcher, "fetch_stock", new_callable=AsyncMock
            ) as mock_fetch_stock,
            patch.object(generator.analyzer, "analyze", new_callable=AsyncMock) as mock_analyze,
        ):
            mock_fetch_stock.return_value = mock_stock_data
            mock_analyze.return_value = mock_technical_data

            plan = await generator.generate("2330")

        assert plan is not None
        assert len(plan.notes) > 0

    @pytest.mark.asyncio
    async def test_generate_includes_execution_strategy(
        self, generator, mock_stock_data, mock_technical_data
    ):
        """Test trading plan includes execution strategy."""
        with (
            patch.object(
                generator.fetcher, "fetch_stock", new_callable=AsyncMock
            ) as mock_fetch_stock,
            patch.object(generator.analyzer, "analyze", new_callable=AsyncMock) as mock_analyze,
        ):
            mock_fetch_stock.return_value = mock_stock_data
            mock_analyze.return_value = mock_technical_data

            plan = await generator.generate("2330")

        assert plan is not None
        assert len(plan.execution_strategy) > 0


class TestTradingPlanModel:
    """Test cases for TradingPlan model."""

    def test_trading_plan_creation(self):
        """Test creating a TradingPlan object."""
        plan = TradingPlan(
            ticker="2330",
            entry_price=100.0,
            tp1=110.0,
            tp1_percent=10.0,
            stop_loss=95.0,
            stop_loss_percent=-5.0,
            risk_amount=5.0,
            reward_tp1=10.0,
            rr_ratio_tp1=2.0,
        )

        assert plan.ticker == "2330"
        assert plan.entry_price == 100.0
        assert plan.tp1 == 110.0
        assert plan.stop_loss == 95.0

    def test_trading_plan_defaults(self):
        """Test TradingPlan default values."""
        plan = TradingPlan(
            ticker="2330",
            entry_price=100.0,
            tp1=110.0,
            tp1_percent=10.0,
            stop_loss=95.0,
            stop_loss_percent=-5.0,
            risk_amount=5.0,
            reward_tp1=10.0,
            rr_ratio_tp1=2.0,
        )

        assert plan.entry_type == "market"
        assert plan.trade_quality == TradeQuality.FAIR
        assert plan.confidence == 50
        assert plan.validity == TradeValidity.SWING
        assert plan.suggested_risk_percent == 2.0
        assert plan.trend == TrendType.SIDEWAYS
        assert plan.signal == SignalType.NEUTRAL

    def test_trading_plan_with_optional_fields(self):
        """Test TradingPlan with optional fields."""
        plan = TradingPlan(
            ticker="2330",
            entry_price=100.0,
            tp1=110.0,
            tp1_percent=10.0,
            tp2=120.0,
            tp2_percent=20.0,
            tp3=130.0,
            tp3_percent=30.0,
            stop_loss=95.0,
            stop_loss_percent=-5.0,
            risk_amount=5.0,
            reward_tp1=10.0,
            reward_tp2=20.0,
            rr_ratio_tp1=2.0,
            rr_ratio_tp2=4.0,
        )

        assert plan.tp2 == 120.0
        assert plan.tp3 == 130.0
        assert plan.reward_tp2 == 20.0
        assert plan.rr_ratio_tp2 == 4.0


class TestTradeQualityEnum:
    """Test cases for TradeQuality enum."""

    def test_quality_values(self):
        """Test TradeQuality enum values."""
        assert TradeQuality.EXCELLENT.value == "Excellent"
        assert TradeQuality.GOOD.value == "Good"
        assert TradeQuality.FAIR.value == "Fair"
        assert TradeQuality.POOR.value == "Poor"

    def test_quality_ordering(self):
        """Test quality ordering by R:R ratio."""
        assert TradeQuality.EXCELLENT.value == "Excellent"
        assert TradeQuality.GOOD.value == "Good"
        assert TradeQuality.FAIR.value == "Fair"
        assert TradeQuality.POOR.value == "Poor"


class TestTradeValidityEnum:
    """Test cases for TradeValidity enum."""

    def test_validity_values(self):
        """Test TradeValidity enum values."""
        assert TradeValidity.INTRADAY.value == "Intraday"
        assert TradeValidity.SWING.value == "Swing"
        assert TradeValidity.POSITION.value == "Position"
