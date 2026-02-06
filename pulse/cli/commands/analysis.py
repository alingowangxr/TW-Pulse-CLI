"""Analysis commands: analyze, technical, fundamental."""

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pulse.cli.app import PulseApp


async def analyze_command(app: "PulseApp", args: str) -> str:
    """Analyze command handler."""
    if not args:
        return "請指定股票代碼。用法: /analyze 2330 (台積電)"

    ticker = args.strip().upper()

    from pulse.core.analysis.fundamental import FundamentalAnalyzer
    from pulse.core.analysis.institutional_flow import InstitutionalFlowAnalyzer
    from pulse.core.analysis.technical import TechnicalAnalyzer
    from pulse.core.data.yfinance import YFinanceFetcher

    fetcher = YFinanceFetcher()
    stock = await fetcher.fetch_stock(ticker)

    if not stock:
        return f"無法取得 {ticker} 的資料"

    # Fetch all data in parallel
    tech_analyzer = TechnicalAnalyzer()
    fundamental_analyzer = FundamentalAnalyzer()
    broker_analyzer = InstitutionalFlowAnalyzer()

    try:
        technical, fundamental, broker = await asyncio.gather(
            tech_analyzer.analyze(ticker),
            fundamental_analyzer.analyze(ticker),
            broker_analyzer.analyze(ticker),
        )
    except Exception as e:
        return f"分析資料時發生錯誤: {e}"

    data = {
        "stock": {
            "ticker": stock.ticker,
            "name": stock.name,
            "price": stock.current_price,
            "change": stock.change,
            "change_percent": stock.change_percent,
            "volume": stock.volume,
            "market_cap": stock.market_cap,
        },
        "technical": technical.to_summary() if technical else None,
        "fundamental": fundamental.to_summary() if fundamental else None,
        "broker": broker if broker else None,
    }

    try:
        response = await app.ai_client.analyze_stock(ticker, data)
    except Exception as e:
        return f"AI 分析時發生錯誤: {e}\n\n請稍後再試或使用其他模型。"

    return response


async def technical_command(app: "PulseApp", args: str) -> str:
    """Technical analysis command handler."""
    if not args:
        return "請指定股票代碼。用法: /technical 2330 (台積電)"

    ticker = args.strip().upper()

    from pulse.core.analysis.technical import TechnicalAnalyzer
    from pulse.utils.rich_output import create_technical_table

    analyzer = TechnicalAnalyzer()
    indicators = await analyzer.analyze(ticker)

    if not indicators:
        return f"無法分析 {ticker}，請確認股票代碼是否正確"

    summary = analyzer.get_indicator_summary(indicators)
    return create_technical_table(ticker, summary)


async def fundamental_command(app: "PulseApp", args: str) -> str:
    """Fundamental analysis command handler."""
    if not args:
        return "請指定股票代碼。用法: /fundamental 2330 (台積電)"

    ticker = args.strip().upper()

    from pulse.core.analysis.fundamental import FundamentalAnalyzer
    from pulse.utils.rich_output import create_fundamental_table

    analyzer = FundamentalAnalyzer()
    data = await analyzer.analyze(ticker)

    if not data:
        return f"無法取得 {ticker} 的基本面資料"

    summary = analyzer.get_summary(data)
    score_data = analyzer.score_valuation(data)

    return create_fundamental_table(ticker, summary, score_data["score"])


async def happy_lines_command(app: "PulseApp", args: str) -> str:
    """Happy Lines (樂活五線譜) analysis command handler."""
    if not args:
        return "請指定股票代碼。用法: /happy-lines 2330 [period=60]"

    # Parse arguments
    parts = args.strip().split()
    ticker = parts[0].upper()

    # Parse optional period parameter
    period = 120  # Default period
    for part in parts[1:]:
        if part.startswith("period="):
            try:
                period = int(part.split("=")[1])
            except (ValueError, IndexError):
                pass

    from pulse.core.analysis.technical import TechnicalAnalyzer
    from pulse.core.data.stock_data_provider import StockDataProvider

    try:
        # Fetch historical data
        fetcher = StockDataProvider()
        df = await fetcher.fetch_history(ticker, period="1y")

        if df is None or df.empty:
            return f"無法取得 {ticker} 的歷史資料"

        # Calculate Happy Lines
        analyzer = TechnicalAnalyzer()
        happy_lines = analyzer.calculate_happy_lines(df, ticker, period=period)

        if not happy_lines:
            return f"無法計算 {ticker} 的樂活五線譜 (可能需要更多歷史資料)"

        # Build simple list output
        price = happy_lines.current_price
        position_ratio = happy_lines.position_ratio

        lines = [
            (happy_lines.line_5, "第5線", "過熱區"),
            (happy_lines.line_4, "第4線", "偏高區"),
            (happy_lines.line_3, "第3線", "平衡區"),
            (happy_lines.line_2, "第2線", "偏低區"),
            (happy_lines.line_1, "第1線", "超跌區"),
        ]

        output_lines = [f"【樂活五線譜分析 - {ticker}】", ""]

        # Five lines display
        for i, (line_price, line_name, zone_name) in enumerate(lines):
            if line_price is not None:
                # Determine if current price is at this line
                indicator = ""
                if i == 0:  # Line 5 (highest)
                    if price >= line_price:
                        indicator = " ← 你在這裡"
                elif i == len(lines) - 1:  # Line 1 (lowest)
                    if price <= line_price:
                        indicator = " ← 你在這裡"
                else:
                    upper_line = lines[i - 1][0]
                    if upper_line is not None:
                        if price < upper_line and price >= line_price:
                            indicator = " ← 你在這裡"

                output_lines.append(f"{line_name} ({zone_name}): {line_price:,.0f}{indicator}")

        # Summary section
        output_lines.extend(
            [
                "",
                "【分析摘要】",
                f"  當前價格: NT$ {price:,.0f}",
                f"  位階百分比: {position_ratio:.1f}%",
                f"  所在區域: {happy_lines.zone.value}",
                f"  計算週期: {period}日",
                "",
                "【交易訊號】",
                f"  趨勢: {happy_lines.trend.value}",
                f"  訊號: {happy_lines.signal.value}",
            ]
        )

        return "\n".join(output_lines)

    except Exception as e:
        return f"分析樂活五線譜時發生錯誤: {e}"
