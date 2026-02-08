"""Price forecasting using AutoTS and statistical models."""

import asyncio
from dataclasses import dataclass

import numpy as np
import pandas as pd

from pulse.utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class ForecastResult:
    """Forecast result container."""

    ticker: str
    forecast_days: int
    predictions: list[float]
    lower_bound: list[float]
    upper_bound: list[float]
    trend: str  # "bullish", "bearish", "sideways"
    confidence: float
    target_price: float
    support: float
    resistance: float
    model_name: str = ""
    mode: str = "fast"


class PriceForecaster:
    """Price forecasting using multiple models."""

    def __init__(self):
        self._autots_available = self._check_autots()

    def _check_autots(self) -> bool:
        """Check if AutoTS is available."""
        try:
            import autots  # noqa: F401

            return True
        except ImportError:
            log.warning("AutoTS not available, using fallback methods")
            return False

    async def forecast(
        self,
        ticker: str,
        prices: list[float],
        dates: list[str],
        days: int = 7,
        mode: str = "fast",
    ) -> ForecastResult | None:
        """
        Forecast future prices.

        Args:
            ticker: Stock ticker
            prices: Historical closing prices
            dates: Historical dates
            days: Days to forecast
            mode: "fast" (few seconds) or "full" (1-2 minutes, more models)

        Returns:
            ForecastResult or None
        """
        if len(prices) < 30:
            log.warning(f"Not enough data for forecasting: {len(prices)} points")
            return None

        if self._autots_available:
            return await self._forecast_autots(ticker, prices, dates, days, mode)
        return await self._forecast_simple(ticker, prices, dates, days)

    async def _forecast_autots(
        self,
        ticker: str,
        prices: list[float],
        dates: list[str],
        days: int,
        mode: str = "fast",
    ) -> ForecastResult | None:
        """Forecast using AutoTS with fast or full mode."""
        try:
            from autots import AutoTS

            # Prepare data for AutoTS
            df = pd.DataFrame(
                {"date": pd.to_datetime(dates), "close": prices}
            )
            df = df.set_index("date")
            df.index.name = "date"

            # Configure AutoTS based on mode
            # "superfast" list: ~8 lightweight models (GLS, ETS, Naive variants, etc.)
            if mode == "full":
                model_list = "superfast"
                max_generations = 3
                num_validations = 2
            else:
                model_list = "superfast"
                max_generations = 1
                num_validations = 1

            def _fit_and_predict():
                model = AutoTS(
                    forecast_length=days,
                    frequency="infer",
                    prediction_interval=0.9,
                    model_list=model_list,
                    max_generations=max_generations,
                    num_validations=num_validations,
                    verbose=0,
                    no_negatives=True,
                )
                model = model.fit(df)

                prediction = model.predict()
                forecast_df = prediction.forecast
                lower_df = prediction.lower_forecast
                upper_df = prediction.upper_forecast

                best_model = model.best_model_name

                return forecast_df, lower_df, upper_df, best_model

            # Run AutoTS in a thread to avoid blocking the event loop
            forecast_df, lower_df, upper_df, best_model = await asyncio.to_thread(
                _fit_and_predict
            )

            # Extract predictions from DataFrames
            predictions = forecast_df["close"].tolist()
            lower_bound = lower_df["close"].tolist()
            upper_bound = upper_df["close"].tolist()

            # Determine trend
            current_price = prices[-1]
            target_price = predictions[-1]
            change_pct = (target_price - current_price) / current_price * 100

            if change_pct > 3:
                trend = "bullish"
            elif change_pct < -3:
                trend = "bearish"
            else:
                trend = "sideways"

            # Calculate confidence based on prediction interval width
            avg_interval = np.mean(
                [upper - lower for upper, lower in zip(upper_bound, lower_bound)]
            )
            confidence = max(0, min(100, 100 - (avg_interval / current_price * 100)))

            # Support and resistance from bounds
            support = min(lower_bound)
            resistance = max(upper_bound)

            return ForecastResult(
                ticker=ticker,
                forecast_days=days,
                predictions=predictions,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
                trend=trend,
                confidence=round(confidence, 1),
                target_price=round(target_price, 2),
                support=round(support, 2),
                resistance=round(resistance, 2),
                model_name=best_model,
                mode=mode,
            )

        except Exception as e:
            log.error(f"AutoTS forecast failed: {e}")
            return await self._forecast_simple(ticker, prices, dates, days)

    async def _forecast_simple(
        self,
        ticker: str,
        prices: list[float],
        dates: list[str],
        days: int,
    ) -> ForecastResult | None:
        """Simple moving average based forecast."""
        try:
            # Simple trend extrapolation
            recent_trend = (prices[-1] - prices[-5]) / 5

            predictions = []
            for i in range(1, days + 1):
                # Dampen the trend over time
                dampening = 0.9**i
                pred = prices[-1] + (recent_trend * i * dampening)
                predictions.append(pred)

            # Calculate volatility for bounds
            volatility = np.std(prices[-20:])
            lower_bound = [p - volatility * 1.5 for p in predictions]
            upper_bound = [p + volatility * 1.5 for p in predictions]

            # Determine trend
            current_price = prices[-1]
            target_price = predictions[-1]
            change_pct = (target_price - current_price) / current_price * 100

            if change_pct > 2:
                trend = "bullish"
            elif change_pct < -2:
                trend = "bearish"
            else:
                trend = "sideways"

            # Lower confidence for simple method
            confidence = 50.0

            return ForecastResult(
                ticker=ticker,
                forecast_days=days,
                predictions=predictions,
                lower_bound=lower_bound,
                upper_bound=upper_bound,
                trend=trend,
                confidence=confidence,
                target_price=round(target_price, 2),
                support=round(min(lower_bound), 2),
                resistance=round(max(upper_bound), 2),
                model_name="MA Extrapolation",
                mode="fast",
            )

        except Exception as e:
            log.error(f"Simple forecast failed: {e}")
            return None

    def format_forecast(self, result: ForecastResult) -> str:
        """Format forecast result as text."""
        trend_symbol = {"bullish": "UP", "bearish": "DOWN", "sideways": "SIDEWAYS"}

        mode_label = "完整模式" if result.mode == "full" else "快速模式"

        lines = [
            f"預測: {result.ticker} ({result.forecast_days} 天)",
            "",
            f"模式: {mode_label}",
        ]

        if result.model_name:
            lines.append(f"模型: {result.model_name}")

        lines.extend([
            "",
            f"趨勢: {trend_symbol.get(result.trend, result.trend)}",
            f"目標價: {result.target_price:,.0f}",
            f"支撐位: {result.support:,.0f}",
            f"壓力位: {result.resistance:,.0f}",
            f"信心度: {result.confidence:.0f}%",
        ])

        return "\n".join(lines)
