"""Screening commands: screen, compare."""

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pulse.cli.app import PulseApp


async def screen_command(app: "PulseApp", args: str) -> str:
    """Screen stocks based on technical/fundamental criteria."""
    if not args:
        return """Stock Screening (股票篩選)

Usage: /screen <criteria> [--universe=tw50|midcap|popular]

Presets (預設篩選條件):
  /screen oversold    - RSI < 30 (超賣,準備反彈)
  /screen overbought  - RSI > 70 (超買,準備回落)
  /screen bullish     - MACD bullish + price > SMA20 (多頭)
  /screen bearish     - MACD bearish + price < SMA20 (空頭)
  /screen breakout    - Near resistance + volume spike (突破)
  /screen momentum    - RSI 50-70 + MACD bullish (動能)
  /screen undervalued - PE < 15 + ROE > 10% (低估)

Flexible (自訂條件):
  /screen rsi<30
  /screen rsi>70
  /screen pe<15

Universe (股票池):
  --universe=tw50    - 台灣50成分股 (快速)
  --universe=midcap  - 中型股100檔 (中速)
  --universe=popular - 熱門股150檔 (較慢)

Example (範例):
  /screen oversold --universe=tw50
"""

    from pulse.core.screener import ScreenPreset, StockScreener, StockUniverse

    # Parse universe option
    universe_type = None
    criteria_str = args

    if "--universe=" in args.lower():
        match = re.search(r"--universe=(\w+)", args.lower())
        if match:
            universe_map = {
                "tw50": StockUniverse.TW50,
                "lq45": StockUniverse.TW50,  # backward compat
                "midcap": StockUniverse.MIDCAP,
                "tw100": StockUniverse.MIDCAP,
                "popular": StockUniverse.POPULAR,
                "all": StockUniverse.ALL,
            }
            universe_type = universe_map.get(match.group(1))
            criteria_str = re.sub(r"\s*--universe=\w+", "", args).strip()

    # Create screener with proper universe
    screener = StockScreener()
    args_lower = criteria_str.strip().lower()

    # Check if it's a preset
    preset_names = [p.value for p in ScreenPreset]
    if args_lower in preset_names:
        results = await screener.screen_preset(ScreenPreset(args_lower))
        title = f"Screening: {args_lower.upper()} ({len(screener.universe)} stocks)"
    else:
        # Use flexible criteria
        results = await screener.screen_criteria(criteria_str)
        title = f"Screening: {criteria_str} ({len(screener.universe)} stocks)"

    if not results:
        return f"找不到符合條件的股票: {criteria_str}"

    # Convert ScreenResult to dict format for rich_output
    from pulse.utils.rich_output import create_screen_table

    result_dicts = []
    for r in results:
        signal = ""
        if r.rsi_status:
            signal = (
                "bullish"
                if "oversold" in r.rsi_status.lower()
                else "bearish"
                if "overbought" in r.rsi_status.lower()
                else ""
            )
        if not signal and r.macd_status:
            signal = (
                "bullish"
                if "bullish" in r.macd_status.lower()
                else "bearish"
                if "bearish" in r.macd_status.lower()
                else ""
            )

        result_dicts.append(
            {
                "ticker": r.ticker,
                "price": r.price,
                "change_percent": r.change_percent,
                "rsi": r.rsi_14,
                "signal": signal,
            }
        )

    return create_screen_table(result_dicts, title)


async def compare_command(app: "PulseApp", args: str) -> str:
    """Compare stocks command handler."""
    if not args:
        return "請指定股票代碼。用法: /compare 2330 2454 (台積電 vs 聯發科)"

    tickers = args.strip().upper().split()

    if len(tickers) < 2:
        return "請至少指定 2 檔股票進行比較"

    from pulse.core.data.yfinance import YFinanceFetcher

    fetcher = YFinanceFetcher()
    results = []

    for ticker in tickers[:4]:  # Max 4 tickers
        stock = await fetcher.fetch_stock(ticker)
        if stock:
            results.append(
                {
                    "ticker": stock.ticker,
                    "name": stock.name or ticker,
                    "price": stock.current_price,
                    "change": stock.change,
                    "change_pct": stock.change_percent,
                    "volume": stock.volume,
                }
            )

    if len(results) < 2:
        return "無法取得足夠的資料進行比較"

    from pulse.utils.rich_output import create_compare_table

    return create_compare_table(results)
