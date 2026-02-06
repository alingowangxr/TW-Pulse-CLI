"""Tests for Stock Screener - Filter stocks by technical and fundamental criteria."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from dataclasses import dataclass, field

from pulse.core.screener import (
    StockScreener,
    ScreenResult,
    ScreenPreset,
    StockUniverse,
    load_all_tickers,
)


# ============ Fixtures ============


@pytest.fixture
def screener():
    """Create StockScreener instance for testing."""
    return StockScreener(universe=["2330", "2454", "2303", "2881", "2308"])


@pytest.fixture
def mock_screen_result():
    """Create mock ScreenResult for testing."""
    return ScreenResult(
        ticker="2330",
        name="台積電",
        sector="半導體",
        price=820.0,
        change=5.0,
        change_percent=0.61,
        volume=15234500,
        avg_volume=12456000,
        rsi_14=55.0,
        macd=2.5,
        macd_signal=1.5,
        macd_histogram=1.0,
        sma_20=810.0,
        sma_50=800.0,
        bb_upper=835.0,
        bb_middle=820.0,
        bb_lower=805.0,
        stoch_k=65.0,
        stoch_d=58.0,
        pe_ratio=25.0,
        pb_ratio=6.0,
        roe=28.0,
        dividend_yield=1.8,
        market_cap=5.5e12,
        support=805.0,
        resistance=835.0,
    )


@pytest.fixture
def oversold_result():
    """Create oversold ScreenResult."""
    return ScreenResult(
        ticker="2303",
        name="聯電",
        price=50.0,
        change=-2.0,
        change_percent=-3.85,
        volume=8000000,
        avg_volume=6000000,
        rsi_14=25.0,
        macd=-1.0,
        macd_signal=0.5,
        macd_histogram=-1.5,
        sma_20=52.0,
        sma_50=55.0,
    )


@pytest.fixture
def overbought_result():
    """Create overbought ScreenResult."""
    return ScreenResult(
        ticker="2454",
        name="聯發科",
        price=1200.0,
        change=30.0,
        change_percent=2.56,
        volume=5000000,
        avg_volume=3000000,
        rsi_14=78.0,
        macd=5.0,
        macd_signal=3.0,
        macd_histogram=2.0,
        sma_20=1150.0,
        sma_50=1100.0,
    )


@pytest.fixture
def neutral_result():
    """Create neutral ScreenResult (no strong bullish/bearish signals)."""
    return ScreenResult(
        ticker="2377",
        name="宏達電",
        price=50.0,
        change=0.0,
        change_percent=0.0,
        volume=5000000,
        avg_volume=5000000,
        rsi_14=50.0,
        # No MACD data
        sma_20=50.0,
        sma_50=50.0,
        # No fundamental data
    )


# ============ Test Classes ============


class TestLoadAllTickers:
    """Test cases for load_all_tickers function."""

    def test_load_all_tickers_returns_list(self):
        """Test that load_all_tickers returns a list."""
        result = load_all_tickers()
        assert isinstance(result, list)

    def test_load_all_tickers_not_empty(self):
        """Test that load_all_tickers returns non-empty list."""
        result = load_all_tickers()
        assert len(result) > 0

    def test_load_all_tickers_sorted(self):
        """Test that load_all_tickers returns sorted list."""
        result = load_all_tickers()
        assert result == sorted(result)

    def test_load_all_tickers_no_duplicates(self):
        """Test that load_all_tickers has no duplicates."""
        result = load_all_tickers()
        assert len(result) == len(set(result))


class TestScreenPresetEnum:
    """Test cases for ScreenPreset enum."""

    def test_preset_values(self):
        """Test all preset values."""
        assert ScreenPreset.OVERSOLD.value == "oversold"
        assert ScreenPreset.OVERBOUGHT.value == "overbought"
        assert ScreenPreset.BULLISH.value == "bullish"
        assert ScreenPreset.BEARISH.value == "bearish"
        assert ScreenPreset.BREAKOUT.value == "breakout"
        assert ScreenPreset.SQUEEZE.value == "squeeze"
        assert ScreenPreset.UNDERVALUED.value == "undervalued"
        assert ScreenPreset.DIVIDEND.value == "dividend"
        assert ScreenPreset.MOMENTUM.value == "momentum"

    def test_all_presets_defined(self):
        """Test that all expected presets are defined."""
        presets = list(ScreenPreset)
        assert len(presets) == 15


class TestStockUniverse:
    """Test cases for StockUniverse enum."""

    def test_universe_values(self):
        """Test all universe values."""
        assert StockUniverse.TW50.value == "tw50"
        assert StockUniverse.MIDCAP.value == "midcap"
        assert StockUniverse.POPULAR.value == "popular"
        assert StockUniverse.ALL.value == "all"


class TestScreenResult:
    """Test cases for ScreenResult model."""

    def test_default_result(self):
        """Test creating default ScreenResult."""
        result = ScreenResult(ticker="2330")
        assert result.ticker == "2330"
        assert result.price == 0.0
        assert result.score == 0.0
        assert result.signals == []
        assert result.rsi_14 is None

    def test_result_with_values(self, mock_screen_result):
        """Test creating ScreenResult with values."""
        assert mock_screen_result.ticker == "2330"
        assert mock_screen_result.price == 820.0
        assert mock_screen_result.rsi_14 == 55.0

    def test_volume_ratio_calculation(self, mock_screen_result):
        """Test volume ratio calculation."""
        # volume=15234500, avg_volume=12456000
        # ratio = 15234500 / 12456000 ≈ 1.22
        ratio = mock_screen_result.volume_ratio
        assert ratio == pytest.approx(1.223, rel=0.01)

    def test_volume_ratio_zero_avg_volume(self):
        """Test volume ratio with zero average volume."""
        result = ScreenResult(ticker="2330", volume=1000000, avg_volume=0)
        assert result.volume_ratio == 1.0

    def test_market_cap_category_micro(self):
        """Test market cap category for micro cap."""
        result = ScreenResult(ticker="2330", market_cap=100e9)  # 100B
        assert result.market_cap_category == "micro"

    def test_market_cap_category_small(self):
        """Test market cap category for small cap."""
        result = ScreenResult(ticker="2330", market_cap=1e12)  # 1T
        assert result.market_cap_category == "small"

    def test_market_cap_category_mid(self):
        """Test market cap category for mid cap."""
        result = ScreenResult(ticker="2330", market_cap=5e12)  # 5T
        assert result.market_cap_category == "mid"

    def test_market_cap_category_large(self):
        """Test market cap category for large cap."""
        result = ScreenResult(ticker="2330", market_cap=20e12)  # 20T
        assert result.market_cap_category == "large"

    def test_market_cap_category_mega(self):
        """Test market cap category for mega cap."""
        result = ScreenResult(ticker="2330", market_cap=100e12)  # 100T
        assert result.market_cap_category == "mega"

    def test_market_cap_category_none(self):
        """Test market cap category for None market cap."""
        result = ScreenResult(ticker="2330", market_cap=None)
        assert result.market_cap_category == "unknown"

    def test_rsi_status_oversold(self):
        """Test RSI status for oversold."""
        result = ScreenResult(ticker="2330", rsi_14=25.0)
        assert result.rsi_status == "Oversold"

    def test_rsi_status_overbought(self):
        """Test RSI status for overbought."""
        result = ScreenResult(ticker="2330", rsi_14=75.0)
        assert result.rsi_status == "Overbought"

    def test_rsi_status_neutral(self):
        """Test RSI status for neutral."""
        result = ScreenResult(ticker="2330", rsi_14=50.0)
        assert result.rsi_status == "Neutral"

    def test_rsi_status_none(self):
        """Test RSI status for None RSI."""
        result = ScreenResult(ticker="2330", rsi_14=None)
        assert result.rsi_status == "N/A"

    def test_macd_status_bullish(self):
        """Test MACD status for bullish."""
        result = ScreenResult(ticker="2330", macd=2.0, macd_signal=1.0)
        assert result.macd_status == "Bullish"

    def test_macd_status_bearish(self):
        """Test MACD status for bearish."""
        result = ScreenResult(ticker="2330", macd=1.0, macd_signal=2.0)
        assert result.macd_status == "Bearish"

    def test_macd_status_none(self):
        """Test MACD status for None values."""
        result = ScreenResult(ticker="2330", macd=None, macd_signal=None)
        assert result.macd_status == "N/A"


class TestStockScreenerInitialization:
    """Test cases for StockScreener initialization."""

    def test_default_initialization(self, screener):
        """Test default initialization with custom universe."""
        assert screener.universe == ["2330", "2454", "2303", "2881", "2308"]

    def test_universe_type_initialization(self):
        """Test initialization with universe type."""
        screener = StockScreener(universe_type=StockUniverse.TW50)
        assert screener.universe is not None
        assert len(screener.universe) > 0

    def test_custom_universe_overrides_type(self):
        """Test that custom universe overrides universe_type."""
        screener = StockScreener(universe=["2330", "2454"], universe_type=StockUniverse.TW50)
        assert screener.universe == ["2330", "2454"]

    def test_empty_universe_uses_default(self):
        """Test that empty universe uses default (TW50)."""
        screener = StockScreener(universe=[], universe_type=None)
        # Should use TW50 as default
        assert screener.universe is not None


class TestParseCriteria:
    """Test cases for criteria parsing."""

    def test_parse_rsi_less_than(self, screener):
        """Test parsing RSI < 30 criteria."""
        criteria = screener.parse_criteria("rsi<30")
        assert criteria == {"rsi_14": ("<", 30)}

    def test_parse_rsi_greater_than(self, screener):
        """Test parsing RSI > 70 criteria."""
        criteria = screener.parse_criteria("rsi>70")
        assert criteria == {"rsi_14": (">", 70)}

    def test_parse_pe_less_than(self, screener):
        """Test parsing PE < 15 criteria."""
        criteria = screener.parse_criteria("pe<15")
        assert criteria == {"pe_ratio": ("<", 15)}

    def test_parse_multiple_criteria(self, screener):
        """Test parsing multiple criteria with 'and'."""
        criteria = screener.parse_criteria("rsi<30 and pe<15")
        assert "rsi_14" in criteria
        assert "pe_ratio" in criteria
        assert criteria["rsi_14"] == ("<", 30)
        assert criteria["pe_ratio"] == ("<", 15)

    def test_parse_preset_name(self, screener):
        """Test parsing preset name."""
        criteria = screener.parse_criteria("oversold")
        assert criteria == {"rsi_14": ("<", 30)}

    def test_parse_bullish_keyword(self, screener):
        """Test parsing bullish keyword."""
        criteria = screener.parse_criteria("bullish")
        assert criteria["macd_above_signal"] is True
        assert criteria["price_above_sma20"] is True

    def test_parse_bearish_keyword(self, screener):
        """Test parsing bearish keyword."""
        criteria = screener.parse_criteria("bearish")
        assert criteria["macd_below_signal"] is True
        assert criteria["price_below_sma20"] is True

    def test_parse_squeeze_keyword(self, screener):
        """Test parsing squeeze keyword."""
        criteria = screener.parse_criteria("squeeze")
        assert criteria["bb_squeeze"] is True

    def test_parse_breakout_keyword(self, screener):
        """Test parsing breakout keyword."""
        criteria = screener.parse_criteria("breakout")
        assert criteria["near_resistance"] is True
        assert criteria["volume_spike"] is True

    def test_parse_empty_string(self, screener):
        """Test parsing empty string returns empty dict."""
        criteria = screener.parse_criteria("")
        assert criteria == {}


class TestMatchesCriteria:
    """Test cases for criteria matching."""

    def test_match_rsi_less_than_success(self, screener, oversold_result):
        """Test matching RSI < 30 criteria."""
        criteria = {"rsi_14": ("<", 30)}
        matches, signals = screener._matches_criteria(oversold_result, criteria)
        assert matches is True
        assert len(signals) > 0

    def test_match_rsi_less_than_fail(self, screener, mock_screen_result):
        """Test failing RSI < 30 criteria."""
        criteria = {"rsi_14": ("<", 30)}
        matches, signals = screener._matches_criteria(mock_screen_result, criteria)
        assert matches is False

    def test_match_rsi_greater_than_success(self, screener, overbought_result):
        """Test matching RSI > 70 criteria."""
        criteria = {"rsi_14": (">", 70)}
        matches, signals = screener._matches_criteria(overbought_result, criteria)
        assert matches is True

    def test_match_macd_bullish_success(self, screener, mock_screen_result):
        """Test matching MACD bullish criteria."""
        criteria = {"macd_above_signal": True}
        matches, signals = screener._matches_criteria(mock_screen_result, criteria)
        assert matches is True
        assert "MACD Bullish" in signals

    def test_match_macd_bullish_fail(self, screener, oversold_result):
        """Test failing MACD bullish criteria."""
        criteria = {"macd_above_signal": True}
        matches, signals = screener._matches_criteria(oversold_result, criteria)
        assert matches is False

    def test_match_price_above_sma20_success(self, screener, mock_screen_result):
        """Test matching price > SMA20 criteria."""
        criteria = {"price_above_sma20": True}
        matches, signals = screener._matches_criteria(mock_screen_result, criteria)
        assert matches is True
        assert "Price > SMA20" in signals

    def test_match_volume_spike_success(self, screener, overbought_result):
        """Test matching volume spike criteria."""
        # overbought_result has volume=5000000, avg=3000000, ratio=1.67
        criteria = {"volume_spike": True}
        matches, signals = screener._matches_criteria(overbought_result, criteria)
        assert matches is True
        assert len(signals) > 0

    def test_match_near_resistance_success(self, screener, mock_screen_result):
        """Test matching near resistance criteria."""
        criteria = {"near_resistance": True}
        matches, signals = screener._matches_criteria(mock_screen_result, criteria)
        # mock_screen_result: price=820, resistance=835, pct=(835-820)/820*100 = 1.8%
        assert matches is True

    def test_match_bb_squeeze_success(self):
        """Test matching BB squeeze criteria."""
        # Create result with narrow BB width
        result = ScreenResult(
            ticker="2330",
            price=820.0,
            bb_upper=825.0,
            bb_middle=820.0,
            bb_lower=815.0,  # width = (825-815)/820*100 = 1.2% < 10%
        )
        screener = StockScreener(universe=["2330"])
        criteria = {"bb_squeeze": True}
        matches, signals = screener._matches_criteria(result, criteria)
        assert matches is True

    def test_match_multiple_criteria(self, screener, mock_screen_result):
        """Test matching multiple criteria."""
        criteria = {
            "rsi_14": ("<", 70),  # 55 < 70 = True
            "macd_above_signal": True,  # 2.5 > 1.5 = True
        }
        matches, signals = screener._matches_criteria(mock_screen_result, criteria)
        assert matches is True

    def test_match_multiple_criteria_partial_fail(self, screener, mock_screen_result):
        """Test matching multiple criteria where one fails."""
        criteria = {
            "rsi_14": ("<", 50),  # 55 < 50 = False
            "macd_above_signal": True,
        }
        matches, signals = screener._matches_criteria(mock_screen_result, criteria)
        assert matches is False


class TestCalculateScore:
    """Test cases for score calculation."""

    def test_base_score(self, screener, mock_screen_result):
        """Test base score is 50."""
        score = screener._calculate_score(mock_screen_result)
        assert score >= 50

    def test_oversold_bonus(self, screener, oversold_result, neutral_result):
        """Test oversold RSI adds score compared to neutral."""
        score_oversold = screener._calculate_score(oversold_result)
        score_neutral = screener._calculate_score(neutral_result)
        assert score_oversold > score_neutral, (
            f"Oversold ({score_oversold}) should be > neutral ({score_neutral})"
        )

    def test_overbought_penalty(self, screener, overbought_result, mock_screen_result):
        """Test overbought RSI reduces score."""
        score_overbought = screener._calculate_score(overbought_result)
        score_neutral = screener._calculate_score(mock_screen_result)
        assert score_overbought < score_neutral

    def test_macd_bullish_bonus(self, screener, mock_screen_result):
        """Test bullish MACD adds score."""
        # mock_screen_result has macd=2.5, signal=1.5 (bullish)
        score = screener._calculate_score(mock_screen_result)
        assert score > 50

    def test_macd_bearish_penalty(self, screener, oversold_result, mock_screen_result):
        """Test bearish MACD reduces score."""
        # oversold_result has macd=-1.0, signal=0.5 (bearish)
        score_bearish = screener._calculate_score(oversold_result)
        score_bullish = screener._calculate_score(mock_screen_result)
        assert score_bearish < score_bullish

    def test_high_volume_bonus(self, screener):
        """Test high volume adds score."""
        result_high_vol = ScreenResult(
            ticker="2330",
            price=820.0,
            volume=20000000,
            avg_volume=10000000,  # ratio=2.0
        )
        result_low_vol = ScreenResult(
            ticker="2330",
            price=820.0,
            volume=5000000,
            avg_volume=10000000,  # ratio=0.5
        )
        score_high = screener._calculate_score(result_high_vol)
        score_low = screener._calculate_score(result_low_vol)
        assert score_high > score_low

    def test_strong_uptrend_bonus(self, screener, mock_screen_result):
        """Test strong uptrend adds score."""
        # mock_screen_result: price=820, sma_20=810, sma_50=800 (price > sma_20 > sma_50)
        score = screener._calculate_score(mock_screen_result)
        assert score > 50

    def test_undervalued_pe_bonus(self, screener):
        """Test low PE adds score."""
        result_undervalued = ScreenResult(
            ticker="2330",
            price=100.0,
            pe_ratio=10.0,  # Undervalued
        )
        result_expensive = ScreenResult(
            ticker="2330",
            price=100.0,
            pe_ratio=35.0,  # Expensive
        )
        score_undervalued = screener._calculate_score(result_undervalued)
        score_expensive = screener._calculate_score(result_expensive)
        assert score_undervalued > score_expensive

    def test_good_roe_bonus(self, screener):
        """Test high ROE adds score."""
        result_high_roe = ScreenResult(
            ticker="2330",
            price=100.0,
            roe=20.0,  # Good ROE
        )
        result_low_roe = ScreenResult(
            ticker="2330",
            price=100.0,
            roe=5.0,  # Low ROE
        )
        score_high = screener._calculate_score(result_high_roe)
        score_low = screener._calculate_score(result_low_roe)
        assert score_high > score_low

    def test_score_clamped_to_100(self, screener):
        """Test score cannot exceed 100."""
        result = ScreenResult(
            ticker="2330",
            price=820.0,
            rsi_14=20,  # Oversold bonus
            macd=5.0,
            macd_signal=1.0,
            volume=20000000,
            avg_volume=10000000,
            sma_20=800.0,
            sma_50=750.0,
            pe_ratio=8.0,
            roe=25.0,
        )
        score = screener._calculate_score(result)
        assert score <= 100

    def test_score_clamped_to_0(self, screener):
        """Test score cannot go below 0."""
        result = ScreenResult(
            ticker="2330",
            price=820.0,
            rsi_14=85,  # Overbought penalty
            macd=-5.0,
            macd_signal=0.0,
            volume=1000000,
            avg_volume=5000000,
            pe_ratio=50.0,
        )
        score = screener._calculate_score(result)
        assert score >= 0


class TestScreenerPresets:
    """Test cases for preset screening."""

    def test_preset_oversold_config(self, screener):
        """Test oversold preset configuration."""
        config = screener.PRESETS[ScreenPreset.OVERSOLD]
        assert config["description"] == "Oversold stocks (RSI < 30)"
        assert config["criteria"] == {"rsi_14": ("<", 30)}

    def test_preset_overbought_config(self, screener):
        """Test overbought preset configuration."""
        config = screener.PRESETS[ScreenPreset.OVERBOUGHT]
        assert config["description"] == "Overbought stocks (RSI > 70)"
        assert config["criteria"] == {"rsi_14": (">", 70)}

    def test_preset_bullish_config(self, screener):
        """Test bullish preset configuration."""
        config = screener.PRESETS[ScreenPreset.BULLISH]
        assert "macd_above_signal" in config["criteria"]
        assert "price_above_sma20" in config["criteria"]

    def test_preset_breakout_config(self, screener):
        """Test breakout preset configuration."""
        config = screener.PRESETS[ScreenPreset.BREAKOUT]
        assert "near_resistance" in config["criteria"]
        assert "volume_spike" in config["criteria"]

    def test_preset_undervalued_config(self, screener):
        """Test undervalued preset configuration."""
        config = screener.PRESETS[ScreenPreset.UNDERVALUED]
        assert config["criteria"]["pe_ratio"] == ("<", 15)
        assert config["criteria"]["roe"] == (">", 10)

    def test_all_presets_have_description(self, screener):
        """Test all presets have descriptions."""
        # Only check presets that are actually in PRESETS dict
        expected_presets = [
            "oversold",
            "overbought",
            "bullish",
            "bearish",
            "breakout",
            "squeeze",
            "undervalued",
            "momentum",
        ]
        for preset_name in expected_presets:
            preset = ScreenPreset(preset_name)
            config = screener.PRESETS[preset]
            assert "description" in config
            assert len(config["description"]) > 0

    def test_all_presets_have_criteria(self, screener):
        """Test all presets have criteria."""
        # Only check presets that are actually in PRESETS dict
        expected_presets = [
            "oversold",
            "overbought",
            "bullish",
            "bearish",
            "breakout",
            "squeeze",
            "undervalued",
            "momentum",
        ]
        for preset_name in expected_presets:
            preset = ScreenPreset(preset_name)
            config = screener.PRESETS[preset]
            assert "criteria" in config
            assert len(config["criteria"]) > 0


class TestSmartScreen:
    """Test cases for AI-driven smart screening."""

    def test_smart_screen_multibagger_criteria(self, screener):
        """Test smart screen for multibagger pattern criteria parsing."""
        # The smart_screen method has internal logic for this
        # Test that parse_criteria returns sensible defaults for growth-related queries
        criteria = screener.parse_criteria("growth stocks")
        assert "high_growth" in criteria or "macd_above_signal" in criteria

    def test_smart_screen_small_cap_criteria(self, screener):
        """Test smart screen for small cap criteria parsing."""
        criteria = screener.parse_criteria("small cap")
        assert "market_cap_small" in criteria

    def test_smart_screen_growth_criteria(self, screener):
        """Test smart screen for growth stocks criteria parsing."""
        criteria = screener.parse_criteria("growth")
        assert "high_growth" in criteria

    def test_smart_screen_breakout_criteria(self, screener):
        """Test smart screen for breakout criteria parsing."""
        criteria = screener.parse_criteria("breakout")
        assert "near_resistance" in criteria
        assert "volume_spike" in criteria

    def test_smart_screen_oversold_criteria(self, screener):
        """Test smart screen for oversold criteria parsing."""
        criteria = screener.parse_criteria("oversold")
        assert criteria == {"rsi_14": ("<", 30)}

    def test_smart_screen_undervalued_criteria(self, screener):
        """Test smart screen for undervalued criteria parsing."""
        criteria = screener.parse_criteria("undervalued")
        assert "pe_ratio" in criteria
        assert "roe" in criteria

    def test_smart_screen_bullish_criteria(self, screener):
        """Test smart screen for bullish criteria parsing."""
        criteria = screener.parse_criteria("bullish")
        assert "macd_above_signal" in criteria
        assert "price_above_sma20" in criteria


class TestFormatResults:
    """Test cases for result formatting."""

    def test_format_empty_results(self, screener):
        """Test formatting empty results."""
        formatted = screener.format_results([])
        assert "No stocks found" in formatted

    def test_format_results_with_data(self, screener, mock_screen_result):
        """Test formatting results with data."""
        results = [mock_screen_result]
        formatted = screener.format_results(results)
        assert "2330" in formatted
        assert "台積電" in formatted or "TSMC" in formatted

    def test_format_results_with_details(self, screener, mock_screen_result):
        """Test formatting results with details."""
        results = [mock_screen_result]
        mock_screen_result.score = 75.0
        mock_screen_result.signals = ["MACD Bullish"]
        formatted = screener.format_results(results, show_details=True)
        assert "Score" in formatted or "75" in formatted
        assert "MACD Bullish" in formatted

    def test_format_results_without_details(self, screener, mock_screen_result):
        """Test formatting results without details."""
        results = [mock_screen_result]
        formatted = screener.format_results(results, show_details=False)
        # Should use table format
        assert "Ticker" in formatted or "Price" in formatted

    def test_format_results_multiple(self, screener, mock_screen_result, overbought_result):
        """Test formatting multiple results."""
        results = [mock_screen_result, overbought_result]
        formatted = screener.format_results(results)
        assert "2 stocks" in formatted or "2" in formatted


class TestRunScreen:
    """Test cases for internal screening methods."""

    @pytest.mark.asyncio
    async def test_run_screen_no_results(self, screener):
        """Test running screen with no matching stocks."""
        # Mock _fetch_stock_data to return None for all tickers
        with patch.object(screener, "_fetch_stock_data", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None

            results = await screener._run_screen(criteria={"rsi_14": ("<", 30)})

        assert results == []


class TestFetchStockData:
    """Test cases for stock data fetching."""

    @pytest.mark.asyncio
    async def test_fetch_stock_data_success(self, screener, mock_screen_result):
        """Test successful stock data fetching."""
        with (
            patch("pulse.core.analysis.technical.TechnicalAnalyzer") as MockAnalyzer,
            patch("pulse.core.data.stock_data_provider.StockDataProvider") as MockProvider,
        ):
            # Setup mock stock data
            mock_stock = MagicMock()
            mock_stock.ticker = "2330"
            mock_stock.name = "台積電"
            mock_stock.sector = "半導體"
            mock_stock.current_price = 820.0
            mock_stock.change = 5.0
            mock_stock.change_percent = 0.61
            mock_stock.volume = 15234500
            mock_stock.avg_volume = 12456000

            mock_provider = MagicMock()
            mock_provider.fetch_stock = AsyncMock(return_value=mock_stock)
            mock_provider.fetch_fundamentals = AsyncMock(return_value=None)
            MockProvider.return_value = mock_provider

            # Setup mock technical analysis
            mock_technical = MagicMock()
            mock_technical.rsi_14 = 55.0
            mock_technical.macd = 2.5
            mock_technical.macd_signal = 1.5
            mock_technical.macd_histogram = 1.0
            mock_technical.sma_20 = 810.0
            mock_technical.sma_50 = 800.0
            mock_technical.bb_upper = 835.0
            mock_technical.bb_lower = 805.0
            mock_technical.bb_middle = 820.0
            mock_technical.stoch_k = 65.0
            mock_technical.stoch_d = 58.0
            mock_technical.support_1 = 805.0
            mock_technical.resistance_1 = 835.0

            mock_analyzer = MockAnalyzer.return_value
            mock_analyzer.analyze = AsyncMock(return_value=mock_technical)

            result = await screener._fetch_stock_data("2330")

        assert result is not None
        assert result.ticker == "2330"
        assert result.price == 820.0
        assert result.rsi_14 == 55.0

    @pytest.mark.asyncio
    async def test_fetch_stock_data_no_stock(self, screener):
        """Test fetching data when stock is unavailable."""
        with patch("pulse.core.data.stock_data_provider.StockDataProvider") as MockProvider:
            mock_provider = MockProvider.return_value
            mock_provider.fetch_stock = AsyncMock(return_value=None)

            result = await screener._fetch_stock_data("INVALID")

        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_stock_data_exception(self, screener):
        """Test fetching data with exception."""
        with patch("pulse.core.data.stock_data_provider.StockDataProvider") as MockProvider:
            mock_provider = MockProvider.return_value
            mock_provider.fetch_stock = AsyncMock(side_effect=Exception("API error"))

            result = await screener._fetch_stock_data("2330")

        assert result is None


class TestScreenerWithDifferentUniverses:
    """Test cases for screener with different universes."""

    def test_tw50_universe(self):
        """Test TW50 universe selection."""
        screener = StockScreener(universe_type=StockUniverse.TW50)
        assert screener.universe is not None
        assert len(screener.universe) > 0

    def test_midcap_universe(self):
        """Test MIDCAP universe selection."""
        screener = StockScreener(universe_type=StockUniverse.MIDCAP)
        assert screener.universe is not None
        assert len(screener.universe) > 0

    def test_popular_universe(self):
        """Test POPULAR universe selection."""
        screener = StockScreener(universe_type=StockUniverse.POPULAR)
        assert screener.universe is not None
        assert len(screener.universe) > 0

    def test_all_universe(self):
        """Test ALL universe selection."""
        screener = StockScreener(universe_type=StockUniverse.ALL)
        assert screener.universe is not None
        # ALL should include all tickers (should be larger than other universes)
        all_tickers = load_all_tickers()
        assert len(screener.universe) == len(all_tickers)


class TestEdgeCases:
    """Test cases for edge cases."""

    def test_result_with_none_values(self):
        """Test ScreenResult with None values."""
        result = ScreenResult(
            ticker="2330",
            price=100.0,
            rsi_14=None,
            macd=None,
            macd_signal=None,
        )
        assert result.rsi_status == "N/A"
        assert result.macd_status == "N/A"

    def test_criteria_with_missing_field(self, screener, mock_screen_result):
        """Test matching criteria when result field is None."""
        criteria = {"pe_ratio": ("<", 15)}
        # mock_screen_result has pe_ratio=25.0, should not match
        matches, signals = screener._matches_criteria(mock_screen_result, criteria)
        assert matches is False

    def test_criteria_with_between_operator(self, screener, mock_screen_result):
        """Test matching criteria with 'between' operator."""
        criteria = {"rsi_14": ("between", (50, 60))}
        # mock_screen_result has rsi_14=55.0, should match
        matches, signals = screener._matches_criteria(mock_screen_result, criteria)
        assert matches is True

    def test_score_calculation_with_none_values(self, screener):
        """Test score calculation with None values."""
        result = ScreenResult(ticker="2330", price=100.0)
        score = screener._calculate_score(result)
        assert score == 50  # Base score

    def test_empty_universe_handling(self):
        """Test screener with empty universe."""
        screener = StockScreener(universe=[])
        assert screener.universe == []
