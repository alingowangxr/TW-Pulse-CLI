"""
End-to-end tests for CLI commands and data flow.

Tests cover:
- CLI command execution flows
- Data fetching and processing pipelines
- Integration between components
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import pandas as pd


class TestCLICommandE2E:
    """End-to-end tests for CLI command flows."""

    @pytest.fixture
    def mock_stock_data(self):
        """Create mock stock data for testing."""
        return {
            "ticker": "2330",
            "name": "台積電",
            "current_price": 1000.0,
            "previous_close": 980.0,
            "change": 20.0,
            "change_percent": 2.04,
            "volume": 50000000,
            "avg_volume": 45000000,
        }

    @pytest.fixture
    def mock_technical_indicators(self):
        """Create mock technical indicators."""
        return {
            "rsi_14": 65.5,
            "macd": 5.2,
            "macd_signal": 3.1,
            "macd_histogram": 2.1,
            "sma_20": 980.0,
            "sma_50": 960.0,
            "bb_upper": 1020.0,
            "bb_lower": 940.0,
            "atr_14": 15.0,
            "trend": "Bullish",
            "signal": "Buy",
        }

    @pytest.mark.asyncio
    async def test_analyze_command_flow(self, mock_stock_data, mock_technical_indicators):
        """Test complete analyze command flow."""
        from pulse.core.analysis.technical import TechnicalAnalyzer
        from pulse.core.data.stock_data_provider import StockDataProvider
        from pulse.core.models import StockData, TechnicalIndicators

        # Mock the dependencies
        with patch.object(StockDataProvider, "fetch_stock", new_callable=AsyncMock) as mock_fetch:
            # Create mock stock data
            mock_stock = StockData(
                ticker="2330",
                name="台積電",
                current_price=1000.0,
                previous_close=980.0,
                change=20.0,
                change_percent=2.04,
                volume=50000000,
                avg_volume=45000000,
            )
            mock_fetch.return_value = mock_stock

            # Execute the flow
            result = await StockDataProvider().fetch_stock("2330")

            # Verify result
            assert result is not None
            assert result.ticker == "2330"
            assert result.current_price == 1000.0

    @pytest.mark.asyncio
    async def test_screener_full_flow(self):
        """Test complete stock screening flow."""
        from pulse.core.screener import StockScreener, ScreenPreset

        # Create screener with small universe for testing
        screener = StockScreener(universe=["2330", "2303", "2454"])

        # Run screening with oversold preset
        results = await screener.screen_preset(
            ScreenPreset.OVERSOLD,
            limit=10,
        )

        # Verify results structure
        assert isinstance(results, list)
        # Results may be empty if no stocks match, but should not error

    @pytest.mark.asyncio
    async def test_screener_criteria_flow(self):
        """Test screening with custom criteria."""
        from pulse.core.screener import StockScreener

        screener = StockScreener(universe=["2330", "2303", "2454"])

        # Screen with RSI criteria
        results = await screener.screen_criteria(
            "rsi<30",
            limit=10,
        )

        assert isinstance(results, list)
        # Results may be empty if no stocks match, but should not error

    @pytest.mark.asyncio
    async def test_smart_screener_flow(self):
        """Test AI smart screening flow."""
        from pulse.core.screener import StockScreener

        screener = StockScreener(universe=["2330", "2303", "2454"])

        # Test bullish query
        results, explanation = await screener.smart_screen(
            "stocks that will rise",
            limit=5,
        )

        assert isinstance(results, list)
        assert isinstance(explanation, str)
        assert len(explanation) > 0


class TestDataFlowE2E:
    """End-to-end tests for data flow pipelines."""

    @pytest.fixture
    def sample_price_data(self):
        """Create sample OHLCV data."""
        dates = [(datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(30)]
        prices = [100 + i * 2 for i in range(30)]
        volumes = [1000000 + i * 10000 for i in range(30)]
        return dates, prices, volumes

    def test_chart_generation_flow(self, sample_price_data):
        """Test complete chart generation flow."""
        from pulse.core.chart_generator import ChartGenerator, ChartConfig, ChartTheme

        dates, prices, volumes = sample_price_data

        # Test with default config
        generator = ChartGenerator()
        result = generator.price_chart("2330", dates, prices, volumes, period="1mo")

        # Should return path or None (None if matplotlib not available)
        assert result is None or isinstance(result, str)

        # Test with custom config
        config = ChartConfig(theme=ChartTheme.LIGHT, show_ma200=True, figure_size=(14, 8))
        generator2 = ChartGenerator(config)
        result2 = generator2.price_chart(
            "2330", dates, prices, volumes, period="1mo", config=config
        )

        assert result2 is None or isinstance(result2, str)

    def test_technical_analysis_flow(self):
        """Test complete technical analysis flow."""
        from pulse.core.analysis.technical import TechnicalAnalyzer

        # Create sample DataFrame
        import pandas as pd
        import numpy as np

        dates = pd.date_range(end=datetime.now(), periods=100, freq="D")
        np.random.seed(42)
        base_price = 1000

        df = pd.DataFrame(
            {
                "date": dates,
                "open": base_price + np.cumsum(np.random.randn(100) * 5),
                "high": base_price + np.cumsum(np.random.randn(100) * 5) + 3,
                "low": base_price + np.cumsum(np.random.randn(100) * 5) - 3,
                "close": base_price + np.cumsum(np.random.randn(100) * 5),
                "volume": 1000000 + np.random.randn(100) * 100000,
            }
        )

        # Test indicator calculation
        analyzer = TechnicalAnalyzer()
        indicators = analyzer._calculate_indicators("2330", df)

        assert indicators is not None
        assert indicators.ticker == "2330"
        assert indicators.rsi_14 is not None
        assert indicators.macd is not None
        assert indicators.sma_20 is not None

    def test_screener_result_formatting(self):
        """Test screening results formatting."""
        from pulse.core.screener import StockScreener, ScreenResult

        # Create mock results
        results = [
            ScreenResult(
                ticker="2330",
                name="台積電",
                price=1000.0,
                change_percent=2.0,
                rsi_14=65.0,
                score=85.0,
            ),
            ScreenResult(
                ticker="2303",
                name="聯電",
                price=50.0,
                change_percent=-1.0,
                rsi_14=45.0,
                score=70.0,
            ),
        ]

        screener = StockScreener(universe=["2330", "2303"])

        # Test formatting
        formatted = screener.format_results(results, "Test Results", show_details=True)
        assert "2330" in formatted
        assert "台積電" in formatted
        assert "Test Results" in formatted

        # Test simple format
        simple = screener.format_results(results, show_details=False)
        assert "2330" in simple


class TestSAPTAEngineE2E:
    """End-to-end tests for SAPTA engine."""

    def test_sapta_engine_initialization(self):
        """Test SAPTA engine can be initialized."""
        from pulse.core.sapta.engine import SaptaEngine

        engine = SaptaEngine()
        assert engine is not None

    def test_sapta_modules_loaded(self):
        """Test all SAPTA modules are loaded."""
        from pulse.core.sapta.engine import SaptaEngine

        engine = SaptaEngine()

        # Check modules dictionary exists with expected keys
        assert hasattr(engine, "modules")
        modules = engine.modules
        assert "absorption" in modules
        assert "compression" in modules
        assert "bb_squeeze" in modules
        assert "elliott" in modules
        assert "time_projection" in modules
        assert "anti_distribution" in modules

    @pytest.mark.asyncio
    async def test_sapta_analysis_flow(self):
        """Test complete SAPTA analysis flow."""
        from pulse.core.sapta.engine import SaptaEngine
        from pulse.core.models import OHLCV
        from datetime import datetime
        import pandas as pd
        import numpy as np

        # Create sample data
        dates = pd.date_range(end=datetime.now(), periods=200, freq="D")
        np.random.seed(42)
        base_price = 1000

        df = pd.DataFrame(
            {
                "date": dates,
                "open": base_price + np.cumsum(np.random.randn(200) * 2),
                "high": base_price + np.cumsum(np.random.randn(200) * 2) + 5,
                "low": base_price + np.cumsum(np.random.randn(200) * 2) - 5,
                "close": base_price + np.cumsum(np.random.randn(200) * 2),
                "volume": 1000000 + np.random.randn(200) * 50000,
            }
        )

        engine = SaptaEngine()

        # Run analysis
        result = await engine.analyze("2330", df=df)

        # Verify result structure
        assert result is not None
        assert hasattr(result, "ticker")
        assert hasattr(result, "total_score")
        assert hasattr(result, "status")


class TestCacheE2E:
    """End-to-end tests for caching system."""

    def test_cache_initialization(self):
        """Test cache can be initialized."""
        from pulse.core.data.cache import DataCache
        from pathlib import Path

        cache = DataCache(cache_dir=Path("data/test_cache"))
        assert cache is not None
        cache.clear()
        cache.close()

    def test_cache_operations(self):
        """Test basic cache operations."""
        from pulse.core.data.cache import DataCache
        from pathlib import Path

        cache = DataCache(cache_dir=Path("data/test_cache"))

        # Test set/get
        result = cache.set("test_key", {"value": 123})
        assert result is True

        cached = cache.get("test_key")
        assert cached == {"value": 123}

        # Test delete
        deleted = cache.delete("test_key")
        assert deleted is True

        # Verify deleted
        assert cache.get("test_key") is None

        cache.clear()
        cache.close()

    def test_stock_cache_operations(self):
        """Test stock-specific cache operations."""
        from pulse.core.data.cache import DataCache
        from pathlib import Path

        cache = DataCache(cache_dir=Path("data/test_cache"))

        # Test stock cache
        stock_data = {"ticker": "2330", "price": 1000}
        result = cache.set_stock("2330", stock_data, ttl=3600)
        assert result is True

        cached = cache.get_stock("2330")
        assert cached == stock_data

        cache.clear()
        cache.close()

    def test_cache_stats(self):
        """Test cache statistics."""
        from pulse.core.data.cache import DataCache
        from pathlib import Path

        cache = DataCache(cache_dir=Path("data/test_cache"))

        # Add some data
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        stats = cache.stats()
        assert "size" in stats
        assert "volume" in stats
        assert "directory" in stats

        cache.clear()
        cache.close()


class TestConfigE2E:
    """End-to-end tests for configuration system."""

    def test_settings_loading(self):
        """Test settings can be loaded."""
        from pulse.core.config import settings

        assert settings is not None
        assert hasattr(settings, "ai")
        assert hasattr(settings, "data")
        assert hasattr(settings, "analysis")
        assert hasattr(settings, "ui")

    def test_data_settings(self):
        """Test data settings configuration."""
        from pulse.core.config import settings

        assert settings.data.cache_ttl > 0
        assert settings.data.cache_dir is not None

    def test_ai_settings(self):
        """Test AI settings configuration."""
        from pulse.core.config import settings

        assert settings.ai.default_model is not None
        assert settings.ai.temperature > 0
        assert settings.ai.timeout > 0

    def test_available_models(self):
        """Test available models list."""
        from pulse.core.config import settings

        models = settings.list_models()
        assert isinstance(models, list)
        assert len(models) > 0
        assert all("id" in m and "name" in m for m in models)


class TestModelsE2E:
    """End-to-end tests for data models."""

    def test_stock_data_creation(self):
        """Test StockData model creation."""
        from pulse.core.models import StockData, OHLCV
        from datetime import datetime

        ohlcv = OHLCV(
            date=datetime.now(), open=1000, high=1010, low=990, close=1005, volume=1000000
        )

        stock = StockData(
            ticker="2330",
            name="台積電",
            current_price=1005,
            previous_close=1000,
            change=5,
            change_percent=0.5,
            volume=1000000,
            history=[ohlcv],
        )

        assert stock.ticker == "2330"
        assert len(stock.history) == 1

    def test_technical_indicators_creation(self):
        """Test TechnicalIndicators model creation."""
        from pulse.core.models import TechnicalIndicators, TrendType, SignalType

        indicators = TechnicalIndicators(
            ticker="2330",
            rsi_14=65.0,
            macd=5.0,
            macd_signal=3.0,
            sma_20=980.0,
            trend=TrendType.BULLISH,
            signal=SignalType.BUY,
        )

        assert indicators.rsi_14 == 65.0
        assert indicators.trend == TrendType.BULLISH
        assert indicators.signal == SignalType.BUY

    def test_broker_summary_creation(self):
        """Test BrokerSummary model creation."""
        from pulse.core.models import BrokerSummary, BrokerTransaction, BandarDetector, AccDistType
        from datetime import datetime

        summary = BrokerSummary(
            ticker="2330",
            date=datetime.now(),
            top_buyers=[
                BrokerTransaction(
                    broker_code="FOREIGN",
                    broker_name="Foreign Investors",
                    buy_lot=1000,
                    buy_value=1000000,
                )
            ],
            foreign_net_buy=500000,
        )

        assert summary.ticker == "2330"
        assert summary.foreign_net_buy == 500000
        assert len(summary.top_buyers) == 1

    def test_trading_plan_creation(self):
        """Test TradingPlan model creation."""
        from pulse.core.models import (
            TradingPlan,
            TradeQuality,
            TradeValidity,
            TrendType,
            SignalType,
        )

        plan = TradingPlan(
            ticker="2330",
            entry_price=1000.0,
            tp1=1050.0,
            tp1_percent=5.0,
            stop_loss=980.0,
            stop_loss_percent=-2.0,
            risk_amount=20.0,
            reward_tp1=50.0,
            rr_ratio_tp1=2.5,
            trade_quality=TradeQuality.GOOD,
            confidence=75,
            validity=TradeValidity.SWING,
            trend=TrendType.BULLISH,
            signal=SignalType.BUY,
        )

        assert plan.ticker == "2330"
        assert plan.rr_ratio_tp1 == 2.5
        assert plan.confidence == 75


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
