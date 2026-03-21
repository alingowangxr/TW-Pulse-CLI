"""
CriteriaParser - Converts natural-language queries and text strings into
screener criteria dictionaries.

Extracted from StockScreener to keep parsing logic self-contained.
"""

import re
from typing import TYPE_CHECKING, Any

from pulse.utils.logger import get_logger

if TYPE_CHECKING:
    from pulse.core.screener import ScreenResult, StockScreener

log = get_logger(__name__)


class CriteriaParser:
    """Parses criteria strings and natural-language queries into criteria dicts."""

    def __init__(self, presets: dict):
        self._presets = presets

    def parse(self, criteria_str: str) -> dict[str, Any]:
        """
        Parse criteria string into dict.

        Examples:
            "rsi<30"                -> {"rsi_14": ("<", 30)}
            "rsi>70 and pe<15"      -> {"rsi_14": (">", 70), "pe_ratio": ("<", 15)}
            "macd_bullish"          -> {"macd_above_signal": True}
        """
        from pulse.core.screener import ScreenPreset

        criteria: dict[str, Any] = {}
        criteria_str = criteria_str.lower().strip()

        # Handle preset names
        if criteria_str in [p.value for p in ScreenPreset]:
            return self._presets[ScreenPreset(criteria_str)]["criteria"]

        # Special keywords
        if "bullish" in criteria_str or "naik" in criteria_str:
            criteria["macd_above_signal"] = True
            criteria["price_above_sma20"] = True

        if "bearish" in criteria_str or "turun" in criteria_str:
            criteria["macd_below_signal"] = True
            criteria["price_below_sma20"] = True

        if "oversold" in criteria_str:
            criteria["rsi_14"] = ("<", 30)

        if "overbought" in criteria_str:
            criteria["rsi_14"] = (">", 70)

        if "squeeze" in criteria_str:
            criteria["bb_squeeze"] = True

        if "breakout" in criteria_str:
            criteria["near_resistance"] = True
            criteria["volume_spike"] = True

        if "multibagger" in criteria_str or "growth" in criteria_str:
            criteria["high_growth"] = True
            criteria["macd_above_signal"] = True

        if "small cap" in criteria_str:
            criteria["market_cap_small"] = True

        if "volume" in criteria_str and "spike" in criteria_str:
            criteria["volume_spike"] = True

        # Parse numeric criteria: rsi<30, pe>15, etc.
        field_map = {
            "rsi": "rsi_14",
            "pe": "pe_ratio",
            "pb": "pb_ratio",
            "pbv": "pb_ratio",
            "roe": "roe",
            "macd": "macd",
            "volume": "volume",
            "price": "price",
            "change": "change_percent",
        }

        for indicator, operator, value in re.findall(
            r"(\w+)\s*([<>]=?)\s*(\d+\.?\d*)", criteria_str
        ):
            field_name = field_map.get(indicator, indicator)
            criteria[field_name] = (operator, float(value))

        return criteria

    async def smart_parse(
        self,
        query: str,
        screener: "StockScreener",
        limit: int = 10,
    ) -> tuple[list["ScreenResult"], str]:
        """
        Natural-language query → (results, explanation).

        Matches keywords to preset criteria, then runs screening.
        """
        query_lower = query.lower()

        if any(w in query_lower for w in ["multibagger", "multi bagger", "10x", "100x", "大漲", "潛力股"]):
            criteria: dict[str, Any] = {
                "market_cap_small_mid": True,
                "macd_above_signal": True,
                "volume_above_avg": True,
            }
            explanation = "尋找潛力股 (小型/中型股, 技術面多頭, 成交量活躍)。條件: 非大型股, MACD 多頭, 平均成交量以上。"

        elif any(w in query_lower for w in ["small cap", "小型股", "小型"]):
            criteria = {"market_cap_small": True, "macd_above_signal": True}
            explanation = "尋找小型股多頭趨勢"

        elif any(w in query_lower for w in ["growth", "成長", "高成長"]):
            criteria = {"high_growth": True, "macd_above_signal": True}
            explanation = "尋找高成長股票 (營收/獲利成長率 > 15-20%)"

        elif any(w in query_lower for w in ["breakout", "突破", "即將上漲"]):
            criteria = {"near_resistance": True, "volume_spike": True}
            explanation = "尋找即將突破股票 (接近壓力位, 成交量爆發)"

        elif any(w in query_lower for w in ["oversold", "超賣", "撿便宜"]):
            criteria = {"rsi_14": ("<", 30)}
            explanation = "尋找超賣股票 (RSI < 30)"

        elif any(w in query_lower for w in ["便宜", "低估", "被低估"]):
            criteria = {"pe_ratio": ("<", 15), "roe": (">", 10)}
            explanation = "尋找被低估股票 (PE < 15, ROE > 10%)"

        elif any(w in query_lower for w in ["下跌", "空頭", "賣出", "避開"]):
            criteria = {"rsi_14": (">", 70), "macd_below_signal": True}
            explanation = "尋找空頭訊號股票 (RSI > 70, MACD 空頭)"

        elif any(w in query_lower for w in ["上漲", "多頭", "看好", "潛力", "買進"]):
            criteria = {
                "rsi_14": ("between", (30, 65)),
                "macd_above_signal": True,
                "volume_above_avg": True,
            }
            explanation = "尋找多頭趨勢股票 (RSI 30-65, MACD 多頭, 成交量增加)"

        else:
            criteria = {"macd_above_signal": True, "volume_above_avg": True}
            explanation = "技術面篩選 (MACD 多頭, 成交量增加)"

        results = await screener._run_screen(
            criteria=criteria,
            sort_by="score",
            sort_asc=False,
            limit=limit,
        )
        return results, explanation
