"""Tests for pulse.core.forecasting module."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from pulse.core.forecasting import ForecastResult, PriceForecaster


# --- ForecastResult dataclass tests ---


class TestForecastResult:
    """Test ForecastResult dataclass."""

    def test_default_fields(self):
        result = ForecastResult(
            ticker="2330",
            forecast_days=7,
            predictions=[100.0, 101.0],
            lower_bound=[98.0, 99.0],
            upper_bound=[102.0, 103.0],
            trend="bullish",
            confidence=75.0,
            target_price=101.0,
            support=98.0,
            resistance=103.0,
        )
        assert result.model_name == ""
        assert result.mode == "fast"

    def test_custom_fields(self):
        result = ForecastResult(
            ticker="2330",
            forecast_days=14,
            predictions=[100.0],
            lower_bound=[95.0],
            upper_bound=[105.0],
            trend="bearish",
            confidence=60.0,
            target_price=100.0,
            support=95.0,
            resistance=105.0,
            model_name="ARIMA",
            mode="full",
        )
        assert result.model_name == "ARIMA"
        assert result.mode == "full"
        assert result.forecast_days == 14


# --- PriceForecaster tests ---


def _make_prices(n: int = 100, base: float = 500.0) -> tuple[list[float], list[str]]:
    """Generate synthetic price and date lists."""
    import pandas as pd

    np.random.seed(42)
    prices = [base]
    for _ in range(n - 1):
        prices.append(prices[-1] + np.random.randn() * 2)
    dates_index = pd.bdate_range(end="2025-06-01", periods=n)
    dates = [d.strftime("%Y-%m-%d") for d in dates_index]
    return prices, dates


class TestPriceForecasterSimple:
    """Test PriceForecaster with simple fallback (no AutoTS)."""

    @patch("pulse.core.forecasting.PriceForecaster._check_autots", return_value=False)
    async def test_forecast_simple_returns_result(self, _mock):
        forecaster = PriceForecaster()
        prices, dates = _make_prices(100)
        result = await forecaster.forecast("2330", prices, dates, days=7)

        assert result is not None
        assert result.ticker == "2330"
        assert result.forecast_days == 7
        assert len(result.predictions) == 7
        assert len(result.lower_bound) == 7
        assert len(result.upper_bound) == 7
        assert result.model_name == "MA Extrapolation"
        assert result.mode == "fast"
        assert result.confidence == 50.0

    @patch("pulse.core.forecasting.PriceForecaster._check_autots", return_value=False)
    async def test_forecast_not_enough_data(self, _mock):
        forecaster = PriceForecaster()
        prices = [100.0] * 20
        dates = [f"2025-01-{i + 1:02d}" for i in range(20)]
        result = await forecaster.forecast("2330", prices, dates, days=7)
        assert result is None

    @patch("pulse.core.forecasting.PriceForecaster._check_autots", return_value=False)
    async def test_forecast_trend_bullish(self, _mock):
        forecaster = PriceForecaster()
        # Create strongly upward trending data
        prices = [100.0 + i * 2.0 for i in range(50)]
        dates = [f"2025-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}" for i in range(50)]
        result = await forecaster.forecast("2330", prices, dates, days=5)
        assert result is not None
        assert result.trend == "bullish"

    @patch("pulse.core.forecasting.PriceForecaster._check_autots", return_value=False)
    async def test_forecast_trend_bearish(self, _mock):
        forecaster = PriceForecaster()
        # Create strongly downward trending data
        prices = [200.0 - i * 2.0 for i in range(50)]
        dates = [f"2025-{(i // 28) + 1:02d}-{(i % 28) + 1:02d}" for i in range(50)]
        result = await forecaster.forecast("2330", prices, dates, days=5)
        assert result is not None
        assert result.trend == "bearish"

    @patch("pulse.core.forecasting.PriceForecaster._check_autots", return_value=False)
    async def test_forecast_bounds_ordering(self, _mock):
        """Lower bound should be less than upper bound for each prediction."""
        forecaster = PriceForecaster()
        prices, dates = _make_prices(60)
        result = await forecaster.forecast("2330", prices, dates, days=7)
        assert result is not None
        for lb, ub in zip(result.lower_bound, result.upper_bound):
            assert lb < ub

    @patch("pulse.core.forecasting.PriceForecaster._check_autots", return_value=False)
    async def test_forecast_days_1(self, _mock):
        forecaster = PriceForecaster()
        prices, dates = _make_prices(50)
        result = await forecaster.forecast("2330", prices, dates, days=1)
        assert result is not None
        assert len(result.predictions) == 1

    @patch("pulse.core.forecasting.PriceForecaster._check_autots", return_value=False)
    async def test_forecast_days_30(self, _mock):
        forecaster = PriceForecaster()
        prices, dates = _make_prices(100)
        result = await forecaster.forecast("2330", prices, dates, days=30)
        assert result is not None
        assert len(result.predictions) == 30


class TestPriceForecasterAutoTS:
    """Test PriceForecaster with mocked AutoTS."""

    def _build_mock_autots(self, days: int):
        """Build a mock AutoTS module and return the mock class."""
        import pandas as pd

        future_dates = pd.bdate_range(start="2025-06-02", periods=days)

        forecast_df = pd.DataFrame(
            {"close": [510.0 + i for i in range(days)]},
            index=future_dates,
        )
        lower_df = pd.DataFrame(
            {"close": [505.0 + i for i in range(days)]},
            index=future_dates,
        )
        upper_df = pd.DataFrame(
            {"close": [515.0 + i for i in range(days)]},
            index=future_dates,
        )

        mock_prediction = MagicMock()
        mock_prediction.forecast = forecast_df
        mock_prediction.lower_forecast = lower_df
        mock_prediction.upper_forecast = upper_df

        mock_model_instance = MagicMock()
        mock_model_instance.fit.return_value = mock_model_instance
        mock_model_instance.predict.return_value = mock_prediction
        mock_model_instance.best_model_name = "GLS"

        mock_autots_class = MagicMock(return_value=mock_model_instance)
        return mock_autots_class, mock_model_instance

    @patch("pulse.core.forecasting.PriceForecaster._check_autots", return_value=True)
    async def test_autots_fast_mode(self, _mock_check):
        forecaster = PriceForecaster()
        prices, dates = _make_prices(100, base=500.0)
        days = 7

        mock_autots_class, mock_model_instance = self._build_mock_autots(days)

        with patch.dict("sys.modules", {"autots": MagicMock()}):
            with patch(
                "pulse.core.forecasting.asyncio.to_thread",
            ) as mock_to_thread:
                import pandas as pd

                future_dates = pd.bdate_range(start="2025-06-02", periods=days)
                forecast_df = pd.DataFrame(
                    {"close": [510.0 + i for i in range(days)]}, index=future_dates
                )
                lower_df = pd.DataFrame(
                    {"close": [505.0 + i for i in range(days)]}, index=future_dates
                )
                upper_df = pd.DataFrame(
                    {"close": [515.0 + i for i in range(days)]}, index=future_dates
                )
                mock_to_thread.return_value = (forecast_df, lower_df, upper_df, "GLS")

                result = await forecaster._forecast_autots(
                    "2330", prices, dates, days, mode="fast"
                )

        assert result is not None
        assert result.model_name == "GLS"
        assert result.mode == "fast"
        assert len(result.predictions) == days

    @patch("pulse.core.forecasting.PriceForecaster._check_autots", return_value=True)
    async def test_autots_full_mode(self, _mock_check):
        forecaster = PriceForecaster()
        prices, dates = _make_prices(100, base=500.0)
        days = 14

        with patch.dict("sys.modules", {"autots": MagicMock()}):
            with patch(
                "pulse.core.forecasting.asyncio.to_thread",
            ) as mock_to_thread:
                import pandas as pd

                future_dates = pd.bdate_range(start="2025-06-02", periods=days)
                forecast_df = pd.DataFrame(
                    {"close": [510.0 + i for i in range(days)]}, index=future_dates
                )
                lower_df = pd.DataFrame(
                    {"close": [505.0 + i for i in range(days)]}, index=future_dates
                )
                upper_df = pd.DataFrame(
                    {"close": [515.0 + i for i in range(days)]}, index=future_dates
                )
                mock_to_thread.return_value = (forecast_df, lower_df, upper_df, "ARIMA")

                result = await forecaster._forecast_autots(
                    "2330", prices, dates, days, mode="full"
                )

        assert result is not None
        assert result.model_name == "ARIMA"
        assert result.mode == "full"
        assert len(result.predictions) == days

    @patch("pulse.core.forecasting.PriceForecaster._check_autots", return_value=True)
    async def test_autots_failure_falls_back_to_simple(self, _mock_check):
        """When AutoTS raises an exception, should fall back to simple method."""
        forecaster = PriceForecaster()
        prices, dates = _make_prices(100, base=500.0)

        with patch.dict("sys.modules", {"autots": MagicMock()}):
            with patch(
                "pulse.core.forecasting.asyncio.to_thread",
                side_effect=RuntimeError("AutoTS crashed"),
            ):
                result = await forecaster._forecast_autots(
                    "2330", prices, dates, 7, mode="fast"
                )

        # Should fall back to simple
        assert result is not None
        assert result.model_name == "MA Extrapolation"


class TestFormatForecast:
    """Test format_forecast output."""

    def test_format_fast_mode(self):
        result = ForecastResult(
            ticker="2330",
            forecast_days=7,
            predictions=[600.0] * 7,
            lower_bound=[590.0] * 7,
            upper_bound=[610.0] * 7,
            trend="bullish",
            confidence=75.0,
            target_price=600.0,
            support=590.0,
            resistance=610.0,
            model_name="GLS",
            mode="fast",
        )
        forecaster = PriceForecaster.__new__(PriceForecaster)
        text = forecaster.format_forecast(result)

        assert "快速模式" in text
        assert "GLS" in text
        assert "2330" in text
        assert "7 天" in text

    def test_format_full_mode(self):
        result = ForecastResult(
            ticker="2454",
            forecast_days=14,
            predictions=[1000.0] * 14,
            lower_bound=[950.0] * 14,
            upper_bound=[1050.0] * 14,
            trend="sideways",
            confidence=65.0,
            target_price=1000.0,
            support=950.0,
            resistance=1050.0,
            model_name="ARIMA",
            mode="full",
        )
        forecaster = PriceForecaster.__new__(PriceForecaster)
        text = forecaster.format_forecast(result)

        assert "完整模式" in text
        assert "ARIMA" in text

    def test_format_no_model_name(self):
        result = ForecastResult(
            ticker="2330",
            forecast_days=7,
            predictions=[500.0] * 7,
            lower_bound=[490.0] * 7,
            upper_bound=[510.0] * 7,
            trend="sideways",
            confidence=50.0,
            target_price=500.0,
            support=490.0,
            resistance=510.0,
            model_name="",
            mode="fast",
        )
        forecaster = PriceForecaster.__new__(PriceForecaster)
        text = forecaster.format_forecast(result)

        assert "模型:" not in text


class TestCheckAutoTS:
    """Test _check_autots availability detection."""

    def test_autots_not_installed(self):
        """When autots is not importable, _autots_available should be False."""
        forecaster = PriceForecaster.__new__(PriceForecaster)
        with patch.dict("sys.modules", {"autots": None}):
            result = forecaster._check_autots()
        assert result is False
