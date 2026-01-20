"""
Chart generator - creates PNG/JPG charts saved to disk.

Uses matplotlib for high-quality chart generation.
"""

from datetime import datetime
from pathlib import Path

from pulse.utils.logger import get_logger

log = get_logger(__name__)

# Chart output directory
CHARTS_DIR = Path(__file__).parent.parent.parent / "charts"


def ensure_charts_dir() -> Path:
    """Ensure charts directory exists."""
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    return CHARTS_DIR


def generate_filename(ticker: str, chart_type: str = "chart") -> str:
    """
    Generate filename for chart.

    Format: {type}_{ticker}_{date}.png
    Example: chart_BBCA_20260107.png, forecast_BBRI_20260107.png
    """
    date_str = datetime.now().strftime("%Y%m%d")
    return f"{chart_type}_{ticker}_{date_str}.png"


class ChartGenerator:
    """Generate high-quality charts as image files."""

    def __init__(self):
        self._check_matplotlib()

    def _check_matplotlib(self) -> bool:
        """Check if matplotlib is available."""
        try:
            import matplotlib

            matplotlib.use("Agg")  # Non-interactive backend
            import matplotlib.pyplot as plt

            self._plt = plt
            return True
        except ImportError:
            log.error("matplotlib not installed. Run: pip install matplotlib")
            self._plt = None
            return False

    def price_chart(
        self,
        ticker: str,
        dates: list[str],
        prices: list[float],
        volumes: list[float] | None = None,
        period: str = "3mo",
    ) -> str | None:
        """
        Generate price chart and save to file.

        Args:
            ticker: Stock ticker
            dates: List of date strings
            prices: List of closing prices
            volumes: Optional volume data
            period: Time period label

        Returns:
            Path to saved chart file, or None if failed
        """
        if not self._plt:
            return None

        plt = self._plt

        try:
            # Setup figure with dark theme
            plt.style.use("dark_background")

            if volumes:
                fig, (ax1, ax2) = plt.subplots(
                    2, 1, figsize=(12, 8), gridspec_kw={"height_ratios": [3, 1]}, sharex=True
                )
            else:
                fig, ax1 = plt.subplots(figsize=(12, 6))

            fig.patch.set_facecolor("#0d1117")
            ax1.set_facecolor("#0d1117")

            # Plot price line
            x = range(len(prices))
            ax1.plot(x, prices, color="#58a6ff", linewidth=2, label="Price")
            ax1.fill_between(x, prices, alpha=0.1, color="#58a6ff")

            # Add moving averages if enough data
            if len(prices) >= 20:
                ma20 = self._moving_average(prices, 20)
                ax1.plot(
                    x, ma20, color="#f0883e", linewidth=1, label="MA20", linestyle="--", alpha=0.7
                )

            if len(prices) >= 50:
                ma50 = self._moving_average(prices, 50)
                ax1.plot(
                    x, ma50, color="#a371f7", linewidth=1, label="MA50", linestyle="--", alpha=0.7
                )

            # Current price annotation
            current_price = prices[-1]
            prev_price = prices[-2] if len(prices) > 1 else current_price
            change = current_price - prev_price
            change_pct = (change / prev_price * 100) if prev_price else 0

            color = "#3fb950" if change >= 0 else "#f85149"
            ax1.axhline(y=current_price, color=color, linestyle="-", alpha=0.5)
            ax1.annotate(
                f"Rp {current_price:,.0f} ({change:+,.0f}, {change_pct:+.2f}%)",
                xy=(len(prices) - 1, current_price),
                xytext=(10, 0),
                textcoords="offset points",
                fontsize=10,
                color=color,
                bbox=dict(boxstyle="round", facecolor="#21262d", edgecolor=color),
            )

            # Styling
            ax1.set_title(f"{ticker} - {period}", fontsize=16, color="#c9d1d9", pad=20)
            ax1.set_ylabel("Price (Rp)", fontsize=12, color="#8b949e")
            ax1.legend(loc="upper left", facecolor="#21262d", edgecolor="#30363d")
            ax1.grid(True, alpha=0.2, color="#30363d")
            ax1.tick_params(colors="#8b949e")

            for spine in ax1.spines.values():
                spine.set_color("#30363d")

            # Volume subplot
            if volumes and "ax2" in dir():
                ax2.set_facecolor("#0d1117")
                colors = [
                    "#3fb950" if prices[i] >= prices[i - 1] else "#f85149"
                    for i in range(1, len(prices))
                ]
                colors.insert(0, "#3fb950")
                ax2.bar(x, volumes, color=colors, alpha=0.7)
                ax2.set_ylabel("Volume", fontsize=12, color="#8b949e")
                ax2.grid(True, alpha=0.2, color="#30363d")
                ax2.tick_params(colors="#8b949e")
                for spine in ax2.spines.values():
                    spine.set_color("#30363d")

            # X-axis labels (show every nth date)
            n = max(1, len(dates) // 6)
            tick_positions = list(range(0, len(dates), n))
            tick_labels = [dates[i] for i in tick_positions]
            ax1.set_xticks(tick_positions)
            ax1.set_xticklabels(tick_labels, rotation=45, ha="right")

            plt.tight_layout()

            # Save chart
            ensure_charts_dir()
            filename = generate_filename(ticker, "chart")
            filepath = CHARTS_DIR / filename

            plt.savefig(filepath, dpi=150, facecolor="#0d1117", edgecolor="none")
            plt.close(fig)

            log.info(f"Chart saved: {filepath}")
            return str(filepath)

        except Exception as e:
            log.error(f"Error generating chart: {e}")
            plt.close("all")
            return None

    def forecast_chart(
        self,
        ticker: str,
        dates: list[str],
        historical: list[float],
        forecast: list[float],
        lower_bound: list[float],
        upper_bound: list[float],
        forecast_days: int = 7,
    ) -> str | None:
        """
        Generate forecast chart and save to file.

        Args:
            ticker: Stock ticker
            dates: Historical dates
            historical: Historical prices
            forecast: Forecasted prices
            lower_bound: Lower confidence bound
            upper_bound: Upper confidence bound
            forecast_days: Number of forecast days

        Returns:
            Path to saved chart file, or None if failed
        """
        if not self._plt:
            return None

        plt = self._plt

        try:
            plt.style.use("dark_background")
            fig, ax = plt.subplots(figsize=(12, 6))
            fig.patch.set_facecolor("#0d1117")
            ax.set_facecolor("#0d1117")

            # Historical data (last 30 days)
            hist_data = historical[-30:]
            hist_x = list(range(len(hist_data)))

            ax.plot(hist_x, hist_data, color="#58a6ff", linewidth=2, label="Historical")

            # Forecast data
            forecast_x = list(range(len(hist_data) - 1, len(hist_data) + len(forecast) - 1))

            ax.plot(
                forecast_x,
                [hist_data[-1]] + forecast[:-1],
                color="#f0883e",
                linewidth=2,
                linestyle="--",
                label="Forecast",
            )

            # Confidence interval
            ax.fill_between(
                forecast_x,
                [hist_data[-1]] + lower_bound[:-1],
                [hist_data[-1]] + upper_bound[:-1],
                alpha=0.2,
                color="#f0883e",
                label="Confidence Interval",
            )

            # Target price annotation
            target = forecast[-1]
            current = hist_data[-1]
            change_pct = (target - current) / current * 100

            color = "#3fb950" if change_pct >= 0 else "#f85149"
            ax.annotate(
                f"Target: Rp {target:,.0f} ({change_pct:+.2f}%)",
                xy=(forecast_x[-1], target),
                xytext=(10, 0),
                textcoords="offset points",
                fontsize=10,
                color=color,
                bbox=dict(boxstyle="round", facecolor="#21262d", edgecolor=color),
            )

            # Vertical line separating historical from forecast
            ax.axvline(x=len(hist_data) - 1, color="#484f58", linestyle=":", alpha=0.7)

            # Styling
            ax.set_title(
                f"{ticker} - Forecast {forecast_days} Days", fontsize=16, color="#c9d1d9", pad=20
            )
            ax.set_ylabel("Price (Rp)", fontsize=12, color="#8b949e")
            ax.set_xlabel("Days", fontsize=12, color="#8b949e")
            ax.legend(loc="upper left", facecolor="#21262d", edgecolor="#30363d")
            ax.grid(True, alpha=0.2, color="#30363d")
            ax.tick_params(colors="#8b949e")

            for spine in ax.spines.values():
                spine.set_color("#30363d")

            plt.tight_layout()

            # Save chart
            ensure_charts_dir()
            filename = generate_filename(ticker, "forecast")
            filepath = CHARTS_DIR / filename

            plt.savefig(filepath, dpi=150, facecolor="#0d1117", edgecolor="none")
            plt.close(fig)

            log.info(f"Forecast chart saved: {filepath}")
            return str(filepath)

        except Exception as e:
            log.error(f"Error generating forecast chart: {e}")
            plt.close("all")
            return None

    def technical_chart(
        self,
        ticker: str,
        dates: list[str],
        prices: list[float],
        rsi: list[float] | None = None,
        macd: list[float] | None = None,
        macd_signal: list[float] | None = None,
        bb_upper: list[float] | None = None,
        bb_lower: list[float] | None = None,
    ) -> str | None:
        """
        Generate technical analysis chart with indicators.

        Returns:
            Path to saved chart file, or None if failed
        """
        if not self._plt:
            return None

        plt = self._plt

        try:
            plt.style.use("dark_background")

            # Create subplots based on available data
            n_plots = 1
            if rsi:
                n_plots += 1
            if macd:
                n_plots += 1

            fig, axes = plt.subplots(n_plots, 1, figsize=(12, 4 * n_plots), sharex=True)
            if n_plots == 1:
                axes = [axes]

            fig.patch.set_facecolor("#0d1117")

            x = range(len(prices))

            # Main price chart with Bollinger Bands
            ax_price = axes[0]
            ax_price.set_facecolor("#0d1117")
            ax_price.plot(x, prices, color="#58a6ff", linewidth=1.5, label="Price")

            if bb_upper and bb_lower:
                ax_price.plot(
                    x,
                    bb_upper,
                    color="#8b949e",
                    linewidth=1,
                    linestyle="--",
                    alpha=0.7,
                    label="BB Upper",
                )
                ax_price.plot(
                    x,
                    bb_lower,
                    color="#8b949e",
                    linewidth=1,
                    linestyle="--",
                    alpha=0.7,
                    label="BB Lower",
                )
                ax_price.fill_between(x, bb_lower, bb_upper, alpha=0.1, color="#8b949e")

            ax_price.set_title(
                f"{ticker} - Technical Analysis", fontsize=16, color="#c9d1d9", pad=20
            )
            ax_price.set_ylabel("Price", color="#8b949e")
            ax_price.legend(loc="upper left", facecolor="#21262d", edgecolor="#30363d")
            ax_price.grid(True, alpha=0.2, color="#30363d")

            plot_idx = 1

            # RSI subplot
            if rsi and plot_idx < len(axes):
                ax_rsi = axes[plot_idx]
                ax_rsi.set_facecolor("#0d1117")
                ax_rsi.plot(x, rsi, color="#a371f7", linewidth=1.5, label="RSI")
                ax_rsi.axhline(y=70, color="#f85149", linestyle="--", alpha=0.7)
                ax_rsi.axhline(y=30, color="#3fb950", linestyle="--", alpha=0.7)
                ax_rsi.fill_between(x, 30, 70, alpha=0.1, color="#8b949e")
                ax_rsi.set_ylim(0, 100)
                ax_rsi.set_ylabel("RSI", color="#8b949e")
                ax_rsi.legend(loc="upper left", facecolor="#21262d", edgecolor="#30363d")
                ax_rsi.grid(True, alpha=0.2, color="#30363d")
                plot_idx += 1

            # MACD subplot
            if macd and macd_signal and plot_idx < len(axes):
                ax_macd = axes[plot_idx]
                ax_macd.set_facecolor("#0d1117")
                ax_macd.plot(x, macd, color="#58a6ff", linewidth=1.5, label="MACD")
                ax_macd.plot(x, macd_signal, color="#f0883e", linewidth=1.5, label="Signal")

                # Histogram
                hist = [m - s for m, s in zip(macd, macd_signal)]
                colors = ["#3fb950" if h >= 0 else "#f85149" for h in hist]
                ax_macd.bar(x, hist, color=colors, alpha=0.5)

                ax_macd.axhline(y=0, color="#484f58", linestyle="-", alpha=0.5)
                ax_macd.set_ylabel("MACD", color="#8b949e")
                ax_macd.legend(loc="upper left", facecolor="#21262d", edgecolor="#30363d")
                ax_macd.grid(True, alpha=0.2, color="#30363d")

            # Style all axes
            for ax in axes:
                ax.tick_params(colors="#8b949e")
                for spine in ax.spines.values():
                    spine.set_color("#30363d")

            plt.tight_layout()

            # Save chart
            ensure_charts_dir()
            filename = generate_filename(ticker, "technical")
            filepath = CHARTS_DIR / filename

            plt.savefig(filepath, dpi=150, facecolor="#0d1117", edgecolor="none")
            plt.close(fig)

            log.info(f"Technical chart saved: {filepath}")
            return str(filepath)

        except Exception as e:
            log.error(f"Error generating technical chart: {e}")
            plt.close("all")
            return None

    def sapta_chart(
        self,
        ticker: str,
        dates: list[str],
        prices: list[float],
        volumes: list[float] | None = None,
        sapta_status: str = "WATCHLIST",
        sapta_score: float = 50.0,
        confidence: str = "MEDIUM",
        ml_probability: float | None = None,
        module_scores: dict[str, dict[str, Any]] | None = None,
        wave_phase: str | None = None,
        fib_retracement: float | None = None,
        projected_window: str | None = None,
        days_to_window: int | None = None,
        reasons: list[str] | None = None,
        notes: list[str] | None = None,
    ) -> str | None:
        """
        Generate SAPTA analysis chart with signals visualization.

        Args:
            ticker: Stock ticker
            dates: List of date strings
            prices: List of closing prices
            volumes: Optional volume data
            sapta_status: SAPTA status (PRE-MARKUP, SIAP, WATCHLIST, ABAIKAN)
            sapta_score: SAPTA score (0-100)
            confidence: Confidence level (HIGH, MEDIUM, LOW)
            ml_probability: ML model probability if available
            module_scores: Dict of module name -> score details
            wave_phase: Elliott wave phase if available
            fib_retracement: Fibonacci retracement level if available
            projected_window: Projected breakout window
            days_to_window: Days to projected window
            reasons: List of reasons for status
            notes: Additional notes

        Returns:
            Path to saved chart file, or None if failed
        """
        if not self._plt:
            return None

        plt = self._plt

        try:
            plt.style.use("dark_background")

            # Create figure with multiple subplots
            fig = plt.figure(figsize=(14, 12))
            fig.patch.set_facecolor("#0d1117")

            # Grid layout: price chart (top), module scores (bottom left), info (bottom right)
            gs = fig.add_gridspec(
                3, 2, height_ratios=[2, 1, 1], width_ratios=[1.5, 1], hspace=0.3, wspace=0.2
            )

            # === Price Chart (top, spanning both columns) ===
            ax_price = fig.add_subplot(gs[0, :])
            ax_price.set_facecolor("#0d1117")

            x = range(len(prices))
            ax_price.plot(x, prices, color="#58a6ff", linewidth=2, label="Price")
            ax_price.fill_between(x, prices, alpha=0.1, color="#58a6ff")

            # Add moving averages
            if len(prices) >= 20:
                ma20 = self._moving_average(prices, 20)
                ax_price.plot(
                    x, ma20, color="#f0883e", linewidth=1, label="MA20", linestyle="--", alpha=0.7
                )

            if len(prices) >= 50:
                ma50 = self._moving_average(prices, 50)
                ax_price.plot(
                    x, ma50, color="#a371f7", linewidth=1, label="MA50", linestyle="--", alpha=0.7
                )

            # Current price annotation
            current_price = prices[-1]
            prev_price = prices[-2] if len(prices) > 1 else current_price
            change = current_price - prev_price
            change_pct = (change / prev_price * 100) if prev_price else 0

            color = "#3fb950" if change >= 0 else "#f85149"
            ax_price.annotate(
                f"{current_price:,.0f} ({change_pct:+.2f}%)",
                xy=(len(prices) - 1, current_price),
                xytext=(10, 0),
                textcoords="offset points",
                fontsize=11,
                color=color,
                fontweight="bold",
                bbox=dict(boxstyle="round", facecolor="#21262d", edgecolor=color),
            )

            # SAPTA status overlay box
            status_colors = {
                "PRE-MARKUP": "#3fb950",  # Green
                "SIAP": "#f0883e",  # Orange
                "WATCHLIST": "#a371f7",  # Purple
                "ABAIKAN": "#8b949e",  # Gray
            }
            status_color = status_colors.get(sapta_status, "#8b949e")

            # Add status badge
            ax_price.annotate(
                f"SAPTA: {sapta_status}",
                xy=(0.98, 0.95),
                xycoords="axes fraction",
                fontsize=12,
                color=status_color,
                fontweight="bold",
                ha="right",
                va="top",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#21262d", edgecolor=status_color),
            )

            # Add score badge
            score_color = (
                "#3fb950" if sapta_score >= 65 else "#f0883e" if sapta_score >= 50 else "#f85149"
            )
            ax_price.annotate(
                f"Score: {sapta_score:.0f}",
                xy=(0.98, 0.88),
                xycoords="axes fraction",
                fontsize=11,
                color=score_color,
                fontweight="bold",
                ha="right",
                va="top",
                bbox=dict(boxstyle="round,pad=0.3", facecolor="#21262d", edgecolor=score_color),
            )

            # Volume subplot
            if volumes:
                ax_vol = fig.add_subplot(gs[1, 0], sharex=ax_price)
                ax_vol.set_facecolor("#0d1117")
                vol_colors = [
                    "#3fb950" if prices[i] >= prices[i - 1] else "#f85149"
                    for i in range(1, len(prices))
                ]
                vol_colors.insert(0, "#3fb950")
                ax_vol.bar(x, volumes, color=vol_colors, alpha=0.7)
                ax_vol.set_ylabel("Volume", fontsize=10, color="#8b949e")
                ax_vol.grid(True, alpha=0.2, color="#30363d")
                ax_vol.tick_params(colors="#8b949e")
                for spine in ax_vol.spines.values():
                    spine.set_color("#30363d")

            # === Module Scores Bar Chart ===
            ax_modules = fig.add_subplot(gs[1, 1])
            ax_modules.set_facecolor("#0d1117")

            if module_scores:
                module_names = []
                module_values = []
                module_max = []

                for name, data in module_scores.items():
                    module_names.append(name.replace("_", "\n").title())
                    module_values.append(data.get("score", 0))
                    module_max.append(data.get("max_score", 10))

                bars = ax_modules.barh(module_names, module_values, color="#58a6ff", alpha=0.8)

                # Color bars based on score
                for bar, val, max_val in zip(bars, module_values, module_max):
                    pct = val / max_val if max_val > 0 else 0
                    if pct >= 0.7:
                        bar.set_color("#3fb950")
                    elif pct >= 0.4:
                        bar.set_color("#f0883e")
                    else:
                        bar.set_color("#f85149")

                    # Add value label
                    ax_modules.annotate(
                        f"{val:.1f}/{max_val:.0f}",
                        xy=(val, bar.get_y() + bar.get_height() / 2),
                        xytext=(5, 0),
                        textcoords="offset points",
                        fontsize=9,
                        color="#c9d1d9",
                        va="center",
                    )

            ax_modules.set_xlabel("Score", fontsize=10, color="#8b949e")
            ax_modules.set_title("Module Scores", fontsize=12, color="#c9d1d9", pad=10)
            ax_modules.set_xlim(0, 25)
            ax_modules.grid(True, alpha=0.2, color="#30363d", axis="x")
            ax_modules.tick_params(colors="#8b949e")
            for spine in ax_modules.spines.values():
                spine.set_color("#30363d")

            # === Key Information Panel ===
            ax_info = fig.add_subplot(gs[2, :])
            ax_info.set_facecolor("#0d1117")
            ax_info.axis("off")

            # Build info text
            info_lines = []

            # Confidence & ML
            conf_color = {"HIGH": "#3fb950", "MEDIUM": "#f0883e", "LOW": "#f85149"}.get(
                confidence, "#8b949e"
            )
            info_lines.append(("Confidence:", conf_color, f"{confidence}"))
            if ml_probability:
                info_lines.append(("ML Probability:", "#58a6ff", f"{ml_probability * 100:.1f}%"))

            # Wave info
            if wave_phase:
                info_lines.append(("Wave:", "#a371f7", wave_phase.replace("wave", "Wave ").upper()))
            if fib_retracement:
                info_lines.append(("Fib Retracement:", "#a371f7", f"{fib_retracement:.1f}%"))

            # Projection
            if projected_window:
                info_lines.append(("Breakout Window:", "#f0883e", projected_window))
            if days_to_window is not None:
                info_lines.append(("Days to Window:", "#f0883e", f"{days_to_window} days"))

            # Draw info boxes
            n_items = len(info_lines)
            box_width = 0.9 / max(n_items, 1)

            for i, (label, label_color, value) in enumerate(info_lines):
                x_pos = 0.05 + i * box_width
                ax_info.text(
                    x_pos,
                    0.7,
                    label,
                    fontsize=10,
                    color=label_color,
                    transform=ax_info.transAxes,
                    fontweight="bold",
                )
                ax_info.text(
                    x_pos,
                    0.35,
                    value,
                    fontsize=12,
                    color="#c9d1d9",
                    transform=ax_info.transAxes,
                    fontweight="bold",
                )

            # === Reasons/Notes at bottom ===
            if reasons or notes:
                all_items = []
                if reasons:
                    all_items.extend([f"• {r}" for r in reasons[:3]])
                if notes:
                    all_items.extend([f"• {n}" for n in notes[:3]])

                if all_items:
                    info_text = " | ".join(all_items[:5])
                    ax_info.text(
                        0.5,
                        0.1,
                        info_text,
                        fontsize=9,
                        color="#8b949e",
                        transform=ax_info.transAxes,
                        ha="center",
                        va="bottom",
                    )

            # Style price chart
            ax_price.set_title(f"{ticker} - SAPTA Analysis", fontsize=16, color="#c9d1d9", pad=20)
            ax_price.set_ylabel("Price", fontsize=12, color="#8b949e")
            ax_price.legend(loc="upper left", facecolor="#21262d", edgecolor="#30363d")
            ax_price.grid(True, alpha=0.2, color="#30363d")
            ax_price.tick_params(colors="#8b949e")

            for spine in ax_price.spines.values():
                spine.set_color("#30363d")

            # X-axis labels
            n = max(1, len(dates) // 6)
            tick_positions = list(range(0, len(dates), n))
            tick_labels = [dates[i] for i in tick_positions]
            ax_price.set_xticks(tick_positions)
            ax_price.set_xticklabels(tick_labels, rotation=45, ha="right")

            plt.tight_layout()

            # Save chart
            ensure_charts_dir()
            filename = generate_filename(ticker, "sapta")
            filepath = CHARTS_DIR / filename

            plt.savefig(filepath, dpi=150, facecolor="#0d1117", edgecolor="none")
            plt.close(fig)

            log.info(f"SAPTA chart saved: {filepath}")
            return str(filepath)

        except Exception as e:
            log.error(f"Error generating SAPTA chart: {e}")
            plt.close("all")
            return None

    def _moving_average(self, data: list[float], window: int) -> list[float]:
        """Calculate simple moving average."""
        result = []
        for i in range(len(data)):
            if i < window - 1:
                result.append(None)
            else:
                result.append(sum(data[i - window + 1 : i + 1]) / window)
        return result


# Convenience functions
def create_price_chart(
    ticker: str,
    dates: list[str],
    prices: list[float],
    volumes: list[float] | None = None,
    period: str = "3mo",
) -> str | None:
    """Create and save a price chart."""
    gen = ChartGenerator()
    return gen.price_chart(ticker, dates, prices, volumes, period)


def create_forecast_chart(
    ticker: str,
    dates: list[str],
    historical: list[float],
    forecast: list[float],
    lower: list[float],
    upper: list[float],
    days: int = 7,
) -> str | None:
    """Create and save a forecast chart."""
    gen = ChartGenerator()
    return gen.forecast_chart(ticker, dates, historical, forecast, lower, upper, days)


def create_sapta_chart(
    ticker: str,
    dates: list[str],
    prices: list[float],
    volumes: list[float] | None = None,
    sapta_status: str = "WATCHLIST",
    sapta_score: float = 50.0,
    confidence: str = "MEDIUM",
    ml_probability: float | None = None,
    module_scores: dict[str, dict] | None = None,
    wave_phase: str | None = None,
    fib_retracement: float | None = None,
    projected_window: str | None = None,
    days_to_window: int | None = None,
    reasons: list[str] | None = None,
    notes: list[str] | None = None,
) -> str | None:
    """Create and save a SAPTA analysis chart."""
    gen = ChartGenerator()
    return gen.sapta_chart(
        ticker=ticker,
        dates=dates,
        prices=prices,
        volumes=volumes,
        sapta_status=sapta_status,
        sapta_score=sapta_score,
        confidence=confidence,
        ml_probability=ml_probability,
        module_scores=module_scores,
        wave_phase=wave_phase,
        fib_retracement=fib_retracement,
        projected_window=projected_window,
        days_to_window=days_to_window,
        reasons=reasons,
        notes=notes,
    )
