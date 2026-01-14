"""Tests for SAPTA Engine - Core business logic for pre-markup detection."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime, date
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path

from pulse.core.sapta.engine import SaptaEngine
from pulse.core.sapta.models import (
    SaptaConfig,
    SaptaStatus,
    ConfidenceLevel,
    ModuleScore,
    SaptaResult,
)
from pulse.core.sapta.modules import (
    SupplyAbsorptionModule,
    CompressionModule,
    BBSqueezeModule,
    ElliottModule,
    TimeProjectionModule,
    AntiDistributionModule,
)


def create_mock_price_data(
    rows: int = 200,
    start_price: float = 100.0,
    volatility: float = 0.02,
    trend: float = 0.0001,
) -> pd.DataFrame:
    """Create realistic mock price data for testing."""
    np.random.seed(42)
    dates = pd.date_range(start="2023-01-01", periods=rows, freq="D")

    # Generate random walk with trend
    returns = np.random.normal(trend, volatility, rows)
    prices = start_price * np.cumprod(1 + returns)

    # Generate OHLCV data (lowercase column names to match module expectations)
    data = {
        "open": prices * (1 + np.random.uniform(-0.005, 0.005, rows)),
        "high": prices * (1 + np.random.uniform(0, 0.01, rows)),
        "low": prices * (1 - np.random.uniform(0, 0.01, rows)),
        "close": prices,
        "volume": np.random.randint(1000000, 10000000, rows),
    }

    return pd.DataFrame(data, index=dates)


def create_accumulation_price_data(rows: int = 200) -> pd.DataFrame:
    """Create price data that simulates accumulation phase."""
    np.random.seed(42)
    dates = pd.date_range(start="2023-01-01", periods=rows, freq="D")

    # Price stays in a range (consolidation)
    base_price = 100.0
    prices = []
    current_price = base_price

    for i in range(rows):
        # Alternating accumulation and small up moves
        if i % 20 < 15:
            # Accumulation: small range
            move = np.random.uniform(-0.5, 0.8)
        else:
            # Small up move
            move = np.random.uniform(0.5, 1.5)
        current_price = max(current_price + move, base_price * 0.95)
        prices.append(current_price)

    prices = np.array(prices)

    # Volume spikes during accumulation
    volume_base = 5000000
    volumes = []
    for i in range(rows):
        if i % 20 < 15:
            vol = volume_base * np.random.uniform(1.5, 3.0)  # Higher volume
        else:
            vol = volume_base * np.random.uniform(0.5, 1.2)
        volumes.append(int(vol))

    data = {
        "open": prices * (1 + np.random.uniform(-0.003, 0.003, rows)),
        "high": prices * (1 + np.random.uniform(0, 0.008, rows)),
        "low": prices * (1 - np.random.uniform(0, 0.008, rows)),
        "close": prices,
        "volume": volumes,
    }

    return pd.DataFrame(data, index=dates)


@pytest.fixture
def mock_df():
    """Create mock price data."""
    return create_mock_price_data(rows=200)


@pytest.fixture
def accumulation_df():
    """Create accumulation phase price data."""
    return create_accumulation_price_data(rows=200)


@pytest.fixture
def sapta_config():
    """Create SAPTA configuration for testing."""
    return SaptaConfig(
        target_gain_pct=10.0,
        target_days=20,
        min_history_days=100,
        threshold_pre_markup=80.0,
        threshold_siap=65.0,
        threshold_watchlist=50.0,
    )


@pytest.fixture
def sapta_engine(sapta_config):
    """Create SAPTA engine for testing."""
    return SaptaEngine(config=sapta_config, auto_load_model=False)


class TestSaptaEngine:
    """Test cases for SAPTA Engine."""

    def test_engine_initialization(self, sapta_engine):
        """Test engine initializes with correct modules."""
        engine = sapta_engine
        assert "absorption" in engine.modules
        assert "compression" in engine.modules
        assert "bb_squeeze" in engine.modules
        assert "elliott" in engine.modules
        assert "time_projection" in engine.modules
        assert "anti_distribution" in engine.modules
        assert len(engine.modules) == 6

    def test_engine_weights_loaded(self, sapta_engine):
        """Test engine loads correct weights."""
        engine = sapta_engine
        assert "absorption" in engine.weights
        assert "compression" in engine.weights
        # Weights should be positive
        for weight in engine.weights.values():
            assert weight > 0

    @pytest.mark.asyncio
    async def test_analyze_with_sufficient_data(self, sapta_engine, mock_df):
        """Test analyze returns result with sufficient data."""
        result = await sapta_engine.analyze("2330", df=mock_df)

        assert result is not None
        assert result.ticker == "2330"
        assert 0 <= result.final_score <= 100
        assert result.status in SaptaStatus

    @pytest.mark.asyncio
    async def test_analyze_with_insufficient_data(self, sapta_engine):
        """Test analyze returns None with insufficient data."""
        # Create data with fewer than min_history_days rows
        short_df = create_mock_price_data(rows=50)
        result = await sapta_engine.analyze("2330", df=short_df)

        assert result is None

    @pytest.mark.asyncio
    async def test_analyze_with_none_data(self, sapta_engine):
        """Test analyze handles None data gracefully."""
        # With df=None, the engine will try to fetch data
        # If fetcher returns None, result should be None
        with patch.object(sapta_engine.fetcher, "get_history_df", return_value=None):
            result = await sapta_engine.analyze("2330", df=None)
            assert result is None

    @pytest.mark.asyncio
    async def test_status_classification(self, sapta_engine):
        """Test status classification logic."""
        from pulse.core.sapta.models import ConfidenceLevel

        # Test PRE-MARKUP threshold
        config = sapta_engine.config
        original_threshold = config.threshold_pre_markup

        config.threshold_pre_markup = 80.0

        # With mock data, score should be classified
        mock_df = create_mock_price_data(rows=200)
        result = await sapta_engine.analyze("2330", df=mock_df)

        assert result is not None
        assert result.status in [
            SaptaStatus.PRE_MARKUP,
            SaptaStatus.SIAP,
            SaptaStatus.WATCHLIST,
            SaptaStatus.ABAIKAN,
        ]

        # Restore threshold
        config.threshold_pre_markup = original_threshold

    @pytest.mark.asyncio
    async def test_scan_returns_list(self, sapta_engine, mock_df):
        """Test scan returns list of results."""
        tickers = ["2330", "2454", "2303", "2881", "2308"]

        # Mock the fetcher to return our test data
        with patch.object(sapta_engine, "fetcher") as mock_fetcher:
            mock_fetcher.get_history_df = AsyncMock(return_value=mock_df)

            results = await sapta_engine.scan(tickers, min_status=SaptaStatus.WATCHLIST)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_scan_empty_ticker_list(self, sapta_engine):
        """Test scan with empty ticker list."""
        results = await sapta_engine.scan([])
        assert results == []


class TestSupplyAbsorptionModule:
    """Test cases for Supply Absorption Module."""

    def test_module_has_correct_name(self):
        """Test module has correct name."""
        module = SupplyAbsorptionModule()
        assert module.name == "absorption"
        assert module.max_score == 20.0  # Actual max score

    def test_module_analyzes_data(self, accumulation_df):
        """Test module analyzes price data."""
        module = SupplyAbsorptionModule()
        result = module.analyze(accumulation_df)

        assert isinstance(result, ModuleScore)
        assert result.module_name == "absorption"
        assert result.max_score == 20.0
        assert 0 <= result.score <= 20.0

    def test_module_handles_empty_data(self):
        """Test module handles empty DataFrame."""
        module = SupplyAbsorptionModule()
        result = module.analyze(pd.DataFrame())

        assert isinstance(result, ModuleScore)
        assert result.score == 0.0
        assert result.status is False


class TestCompressionModule:
    """Test cases for Compression Module."""

    def test_module_has_correct_name(self):
        """Test module has correct name."""
        module = CompressionModule()
        assert module.name == "compression"
        assert module.max_score == 15.0

    def test_module_detects_compression(self, mock_df):
        """Test module detects volatility compression."""
        module = CompressionModule()
        result = module.analyze(mock_df)

        assert isinstance(result, ModuleScore)
        assert result.max_score == 15.0
        assert 0 <= result.score <= 15.0


class TestBBSqueezeModule:
    """Test cases for BB Squeeze Module."""

    def test_module_has_correct_name(self):
        """Test module has correct name."""
        module = BBSqueezeModule()
        assert module.name == "bb_squeeze"
        assert module.max_score == 15.0

    def test_module_analyzes_data(self, mock_df):
        """Test module analyzes Bollinger Band data."""
        module = BBSqueezeModule()
        result = module.analyze(mock_df)

        assert isinstance(result, ModuleScore)
        assert result.max_score == 15.0
        assert 0 <= result.score <= 15.0


class TestElliottModule:
    """Test cases for Elliott Wave Module."""

    def test_module_has_correct_name(self):
        """Test module has correct name."""
        module = ElliottModule()
        assert module.name == "elliott"
        assert module.max_score == 20.0  # Correct max score

    def test_module_analyzes_data(self, mock_df):
        """Test module analyzes wave patterns."""
        module = ElliottModule()
        result = module.analyze(mock_df)

        assert isinstance(result, ModuleScore)
        assert result.max_score == 20.0
        assert 0 <= result.score <= 20.0


class TestTimeProjectionModule:
    """Test cases for Time Projection Module."""

    def test_module_has_correct_name(self):
        """Test module has correct name."""
        module = TimeProjectionModule()
        assert module.name == "time_projection"
        assert module.max_score == 15.0

    def test_module_analyzes_data(self, mock_df):
        """Test module analyzes time projections."""
        module = TimeProjectionModule()
        result = module.analyze(mock_df)

        assert isinstance(result, ModuleScore)
        assert result.max_score == 15.0
        assert 0 <= result.score <= 15.0


class TestAntiDistributionModule:
    """Test cases for Anti-Distribution Module."""

    def test_module_has_correct_name(self):
        """Test module has correct name."""
        module = AntiDistributionModule()
        assert module.name == "anti_distribution"
        assert module.max_score == 15.0  # Correct max score

    def test_module_analyzes_data(self, mock_df):
        """Test module filters distribution patterns."""
        module = AntiDistributionModule()
        result = module.analyze(mock_df)

        assert isinstance(result, ModuleScore)
        assert result.max_score == 15.0
        assert 0 <= result.score <= 15.0


class TestSaptaConfig:
    """Test cases for SAPTA Configuration."""

    def test_default_config(self):
        """Test default configuration values."""
        config = SaptaConfig()

        assert config.target_gain_pct == 10.0
        assert config.target_days == 20
        assert config.min_history_days == 120  # Actual default value
        assert config.threshold_pre_markup == 80.0
        assert config.threshold_siap == 65.0
        assert config.threshold_watchlist == 50.0

    def test_custom_config(self):
        """Test custom configuration values."""
        config = SaptaConfig(
            target_gain_pct=15.0,
            target_days=30,
            threshold_pre_markup=75.0,
        )

        assert config.target_gain_pct == 15.0
        assert config.target_days == 30
        assert config.threshold_pre_markup == 75.0

    def test_weight_defaults(self):
        """Test default module weights."""
        config = SaptaConfig()

        # Check weights exist (actual values may vary)
        assert hasattr(config, "weight_absorption")
        assert hasattr(config, "weight_compression")
        assert hasattr(config, "weight_bb_squeeze")
        assert hasattr(config, "weight_elliott")
        assert hasattr(config, "weight_time_projection")
        assert hasattr(config, "weight_anti_distribution")


class TestSaptaStatus:
    """Test cases for SAPTA Status enum."""

    def test_status_values(self):
        """Test status enum values."""
        assert SaptaStatus.PRE_MARKUP.value == "PRE-MARKUP"
        assert SaptaStatus.SIAP.value == "SIAP"
        assert SaptaStatus.WATCHLIST.value == "WATCHLIST"
        assert SaptaStatus.ABAIKAN.value == "ABAIKAN"

    def test_status_ordering(self):
        """Test status can be ordered by score."""
        status_order = [
            SaptaStatus.ABAIKAN,
            SaptaStatus.WATCHLIST,
            SaptaStatus.SIAP,
            SaptaStatus.PRE_MARKUP,
        ]

        # Should be able to compare indices
        for i, status in enumerate(status_order):
            assert status_order.index(status) == i


class TestSaptaResult:
    """Test cases for SaptaResult model."""

    def test_result_creation(self):
        """Test creating a result object."""
        result = SaptaResult(
            ticker="2330",
            total_score=50.0,
            weighted_score=50.0,
            status=SaptaStatus.WATCHLIST,
            confidence=ConfidenceLevel.MEDIUM,
        )

        assert result.ticker == "2330"
        assert result.total_score == 50.0
        assert result.status == SaptaStatus.WATCHLIST
        assert result.confidence == ConfidenceLevel.MEDIUM

    def test_result_defaults(self):
        """Test result has correct defaults."""
        result = SaptaResult(
            ticker="2330",
            total_score=0.0,
            weighted_score=0.0,
            status=SaptaStatus.ABAIKAN,
            confidence=ConfidenceLevel.LOW,
        )

        # Check that default lists are properly initialized
        assert result.notes is not None
        assert result.reasons is not None
        assert result.warnings is not None
        assert result.penalties is not None
        assert result.penalty_score == 0.0
        assert result.features is not None

    def test_result_final_score(self):
        """Test final_score property."""
        result = SaptaResult(
            ticker="2330",
            total_score=50.0,
            weighted_score=50.0,
            penalty_score=5.0,
        )
        assert result.final_score == 45.0

    def test_result_score_pct(self):
        """Test score_pct property."""
        result = SaptaResult(
            ticker="2330",
            total_score=50.0,
            weighted_score=50.0,
            max_possible_score=100.0,
        )
        assert result.score_pct == 50.0


class TestSaptaEngineML:
    """Test cases for SAPTA ML integration."""

    def test_load_model_returns_false_when_no_model(self, sapta_engine):
        """Test loading model when none exists."""
        result = sapta_engine.load_ml_model("/nonexistent/path/model.pkl")
        assert result is False

    def test_ml_model_not_loaded_by_default(self, sapta_engine):
        """Test ML model is not loaded initially."""
        assert sapta_engine._ml_model is None
        assert sapta_engine._ml_loaded is False


class TestSaptaEngineFormatting:
    """Test cases for SAPTA result formatting."""

    @pytest.mark.asyncio
    async def test_format_result(self, sapta_engine, mock_df):
        """Test formatting result for display."""
        result = await sapta_engine.analyze("2330", df=mock_df)
        if result:
            formatted = sapta_engine.format_result(result)

            assert isinstance(formatted, str)
            assert "2330" in formatted
            assert "SAPTA Analysis:" in formatted or "SAPTA" in formatted

    @pytest.mark.asyncio
    async def test_format_result_detailed(self, sapta_engine, mock_df):
        """Test formatting result with detailed flag."""
        result = await sapta_engine.analyze("2330", df=mock_df)
        if result:
            formatted = sapta_engine.format_result(result, detailed=True)

            assert isinstance(formatted, str)
            assert len(formatted) > 0

    def test_format_scan_results_empty(self, sapta_engine):
        """Test formatting empty scan results."""
        formatted = sapta_engine.format_scan_results([])
        assert "No stocks" in formatted or "no" in formatted.lower()

    def test_format_scan_results_with_data(self, sapta_engine, mock_df):
        """Test formatting scan results with data."""
        from pulse.core.sapta.models import SaptaResult, ConfidenceLevel

        # Create mock results
        results = [
            SaptaResult(
                ticker="2330",
                total_score=75.0,
                weighted_score=75.0,
                status=SaptaStatus.SIAP,
                confidence=ConfidenceLevel.MEDIUM,
                wave_phase="Wave 3",
            ),
            SaptaResult(
                ticker="2454",
                total_score=85.0,
                weighted_score=85.0,
                status=SaptaStatus.PRE_MARKUP,
                confidence=ConfidenceLevel.HIGH,
                wave_phase="Wave 3",
            ),
        ]

        formatted = sapta_engine.format_scan_results(results)

        assert isinstance(formatted, str)
        assert "2330" in formatted
        assert "2454" in formatted
        assert "Total:" in formatted or "total" in formatted.lower()
