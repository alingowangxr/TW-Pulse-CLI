"""
CriteriaFilter - Evaluates a ScreenResult against a criteria dictionary
and calculates a ranking score.

Extracted from StockScreener to keep filtering logic self-contained and testable.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pulse.core.screener import ScreenResult


def matches_criteria(
    result: "ScreenResult",
    criteria: dict[str, Any],
) -> tuple[bool, list[str]]:
    """
    Check if a stock matches all criteria.

    Returns:
        (matches, list_of_matched_signal_strings)
    """
    signals: list[str] = []

    for key, condition in criteria.items():
        # ── Boolean / composite conditions ────────────────────────────────────

        if key == "macd_above_signal":
            if condition and result.macd is not None and result.macd_signal is not None:
                if result.macd > result.macd_signal:
                    signals.append("MACD Bullish")
                else:
                    return False, []
            continue

        if key == "macd_below_signal":
            if condition and result.macd is not None and result.macd_signal is not None:
                if result.macd < result.macd_signal:
                    signals.append("MACD Bearish")
                else:
                    return False, []
            continue

        if key == "price_above_sma20":
            if condition and result.sma_20 is not None:
                if result.price > result.sma_20:
                    signals.append("Price > SMA20")
                else:
                    return False, []
            continue

        if key == "price_below_sma20":
            if condition and result.sma_20 is not None:
                if result.price < result.sma_20:
                    signals.append("Price < SMA20")
                else:
                    return False, []
            continue

        if key == "volume_spike":
            if condition and result.volume_ratio > 1.5:
                signals.append(f"Volume Spike ({result.volume_ratio:.1f}x)")
            elif condition:
                return False, []
            continue

        if key == "volume_above_avg":
            if condition and result.volume_ratio > 1.0:
                signals.append("Volume > Avg")
            elif condition:
                return False, []
            continue

        if key == "near_resistance":
            if condition and result.resistance and result.price:
                pct_to_resistance = (result.resistance - result.price) / result.price * 100
                if 0 < pct_to_resistance < 3:
                    signals.append(f"Near Resistance ({pct_to_resistance:.1f}%)")
                else:
                    return False, []
            continue

        if key == "bb_squeeze":
            if condition and result.bb_upper and result.bb_lower and result.bb_middle:
                bb_width = (result.bb_upper - result.bb_lower) / result.bb_middle * 100
                if bb_width < 10:
                    signals.append(f"BB Squeeze ({bb_width:.1f}%)")
                else:
                    return False, []
            continue

        # ── Keltner Channel conditions ─────────────────────────────────────────

        if key == "kc_above_upper":
            if condition and result.kc_upper and result.price:
                if result.price >= result.kc_upper:
                    signals.append(f"KC Breakout ({result.price:.1f} >= {result.kc_upper:.1f})")
                else:
                    return False, []
            continue

        if key == "kc_above_middle":
            if condition and result.kc_middle and result.price:
                if result.price > result.kc_middle:
                    signals.append(f"KC Middle ({result.kc_middle:.1f})")
                else:
                    return False, []
            continue

        if key == "kc_below_upper":
            if condition and result.kc_upper and result.price:
                if result.price < result.kc_upper:
                    signals.append(f"KC Below Upper ({result.price:.1f} < {result.kc_upper:.1f})")
                else:
                    return False, []
            continue

        if key == "kc_above_lower":
            if condition and result.kc_lower and result.price:
                if result.price > result.kc_lower:
                    signals.append(f"KC Lower ({result.kc_lower:.1f})")
                else:
                    return False, []
            continue

        if key == "kc_ema_bullish":
            if condition:
                if result.ema_9 and result.ema_21 and result.ema_55:
                    if result.ema_9 > result.ema_21 > result.ema_55:
                        signals.append(
                            f"EMA Bullish ({result.ema_9:.1f} > {result.ema_21:.1f} > {result.ema_55:.1f})"
                        )
                    else:
                        return False, []
                else:
                    return False, []
            continue

        if key == "kc_position_above_upper":
            if condition and result.kc_position is not None and result.kc_upper and result.kc_lower:
                if result.kc_position >= 100:
                    signals.append(f"KC Position: {result.kc_position:.1f}%")
                else:
                    return False, []
            continue

        if key == "volume_min":
            if isinstance(condition, (int, float)):
                if result.avg_volume < condition:
                    return False, []
                signals.append(f"Vol: {result.avg_volume:,}")
            continue

        # ── Market cap categories ──────────────────────────────────────────────

        if key == "market_cap_small":
            if condition:
                if result.market_cap_category in ["micro", "small"]:
                    signals.append(f"Small Cap ({result.market_cap_category})")
                else:
                    return False, []
            continue

        if key == "market_cap_mid":
            if condition:
                if result.market_cap_category == "mid":
                    signals.append("Mid Cap")
                else:
                    return False, []
            continue

        if key == "market_cap_small_mid":
            if condition:
                if result.market_cap_category in ["micro", "small", "mid"]:
                    signals.append(f"Cap: {result.market_cap_category}")
                else:
                    return False, []
            continue

        if key == "high_growth":
            if condition:
                has_growth = False
                if result.earnings_growth and result.earnings_growth > 20:
                    signals.append(f"Earnings Growth: {result.earnings_growth:.0f}%")
                    has_growth = True
                if result.revenue_growth and result.revenue_growth > 15:
                    signals.append(f"Revenue Growth: {result.revenue_growth:.0f}%")
                    has_growth = True
                if not has_growth:
                    return False, []
            continue

        # ── Happy Lines (樂活五線譜) ────────────────────────────────────────────

        if key == "happy_lines":
            if condition == ("exists", True):
                if result.happy_lines is not None:
                    signals.append("Has Happy Lines")
                else:
                    return False, []
            continue

        if key == "happy_zone":
            if result.happy_lines is not None:
                zone = result.happy_lines.zone
                zone_map = {
                    "oversold": "超跌區",
                    "undervalued": "偏低區",
                    "balanced": "平衡區",
                    "overvalued": "偏高區",
                    "overbought": "過熱區",
                }
                multi_map = {
                    "cheap": ["超跌區", "偏低區"],
                    "expensive": ["偏高區", "過熱區"],
                }
                if condition in multi_map:
                    if zone.value in multi_map[condition]:
                        signals.append(f"Happy Zone: {zone.value}")
                    else:
                        return False, []
                elif zone_map.get(condition) == zone.value:
                    signals.append(f"Happy Zone: {zone.value}")
                else:
                    return False, []
            else:
                return False, []
            continue

        if key == "happy_position_ratio":
            if result.happy_lines is not None:
                ratio = result.happy_lines.position_ratio
                if isinstance(condition, tuple):
                    operator, threshold = condition
                    if operator == "<" and ratio >= threshold:
                        return False, []
                    elif operator == ">" and ratio <= threshold:
                        return False, []
                    elif operator == "<=" and ratio > threshold:
                        return False, []
                    elif operator == ">=" and ratio < threshold:
                        return False, []
                signals.append(f"Happy Position: {ratio:.1f}%")
            else:
                return False, []
            continue

        # ── Generic numeric comparisons ────────────────────────────────────────

        value = getattr(result, key, None)
        if value is None:
            continue

        if isinstance(condition, tuple):
            operator, threshold = condition
            if operator == "<" and value >= threshold:
                return False, []
            elif operator == ">" and value <= threshold:
                return False, []
            elif operator == "<=" and value > threshold:
                return False, []
            elif operator == ">=" and value < threshold:
                return False, []
            elif operator == "between":
                low, high = threshold
                if not (low <= value <= high):
                    return False, []
                signals.append(f"{key}: {value:.1f}")
            else:
                signals.append(f"{key}: {value:.1f}")

    return True, signals


def calculate_score(result: "ScreenResult") -> float:
    """Calculate overall ranking score (0-100) for a ScreenResult."""
    score = 50.0

    if result.rsi_14 is not None:
        if result.rsi_14 < 30:
            score += 25
        elif result.rsi_14 > 70:
            score -= 10
        elif 40 <= result.rsi_14 <= 60:
            score += 5

    if result.macd is not None and result.macd_signal is not None:
        is_oversold = result.rsi_14 is not None and result.rsi_14 < 30
        if result.macd > result.macd_signal:
            score += 15
            if result.macd_histogram and result.macd_histogram > 0:
                score += 5
        elif not is_oversold:
            score -= 10

    if result.volume_ratio > 1.5:
        score += 10
    elif result.volume_ratio < 0.5:
        score -= 5

    if result.sma_20 and result.sma_50:
        if result.price > result.sma_20 > result.sma_50:
            score += 20 if (result.rsi_14 is not None and result.rsi_14 < 30) else 15
        elif result.price < result.sma_20 < result.sma_50:
            score -= 10

    if result.pe_ratio:
        if 0 < result.pe_ratio < 15:
            score += 10
        elif result.pe_ratio > 30:
            score -= 5

    if result.roe and result.roe > 15:
        score += 10

    return max(0.0, min(100.0, score))
