"""Institutional investor flow analysis."""

from typing import Any
from datetime import datetime, timedelta
import pandas as pd

from pulse.core.data.stock_data_provider import StockDataProvider
from pulse.core.models import SignalType
from pulse.utils.formatters import format_currency
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class InstitutionalFlowAnalyzer:
    """Analyze institutional investor flow for Taiwan stocks."""

    def __init__(self):
        """Initialize institutional flow analyzer."""
        self.data_provider = StockDataProvider()

    async def analyze(
        self,
        ticker: str,
        days: int = 20,  # Analyze over 20 trading days (approx 1 month)
    ) -> dict[str, Any] | None:
        """
        Analyze institutional investor flow for a stock from FinMind data.

        Args:
            ticker: Stock ticker
            days: Number of days to analyze

        Returns:
            Analysis result dictionary
        """
        end_date = datetime.now()
        # Fetch enough data to cover 'days' trading days, accounting for weekends/holidays
        start_date = end_date - timedelta(days=days * 7 // 5 + 5)
        start_date_str = start_date.strftime("%Y-%m-%d")
        end_date_str = end_date.strftime("%Y-%m-%d")

        # Fetch institutional investor data from FinMind via StockDataProvider
        institutional_data_df = await self.data_provider.fetch_institutional_investors(
            ticker, start_date=start_date_str, end_date=end_date_str
        )

        if institutional_data_df is None or institutional_data_df.empty:
            log.warning(
                f"No institutional investor data found for {ticker} from FinMind for period {start_date_str} to {end_date_str}."
            )
            return None

        # Process the institutional data (simplified for now)
        # FinMind data typically includes columns like 'date', 'stock_id', 'buy', 'sell', 'deal', 'Foreign_Investor_Buy', 'Foreign_Investor_Sell', etc.

        # Calculate net buying/selling for different institutional types
        # Ensure the columns exist before attempting to access them
        institutional_data_df["Foreign_Investor_Net"] = institutional_data_df.get(
            "Foreign_Investor_Buy", 0
        ) - institutional_data_df.get("Foreign_Investor_Sell", 0)
        institutional_data_df["Investment_Trust_Net"] = institutional_data_df.get(
            "Investment_Trust_Buy", 0
        ) - institutional_data_df.get("Investment_Trust_Sell", 0)
        institutional_data_df["Dealer_Net"] = institutional_data_df.get(
            "Dealer_Self_Buy", 0
        ) - institutional_data_df.get("Dealer_Self_Sell", 0)
        institutional_data_df["Dealer_Hedge_Net"] = institutional_data_df.get(
            "Dealer_Hedge_Buy", 0
        ) - institutional_data_df.get("Dealer_Hedge_Sell", 0)

        # Take the sum over the analysis period
        total_foreign_net = institutional_data_df["Foreign_Investor_Net"].sum()
        total_investment_trust_net = institutional_data_df["Investment_Trust_Net"].sum()
        total_dealer_net = (
            institutional_data_df["Dealer_Net"] + institutional_data_df["Dealer_Hedge_Net"]
        ).sum()

        # Determine overall institutional net flow
        overall_net_flow = total_foreign_net + total_investment_trust_net + total_dealer_net

        analysis = {
            "ticker": ticker,
            "analysis_period_start": start_date_str,
            "analysis_period_end": end_date_str,
            "overall_institutional_net_flow": overall_net_flow,
            "overall_institutional_net_flow_formatted": format_currency(
                overall_net_flow, currency="NT$"
            ),
            "foreign_investor_net": total_foreign_net,
            "foreign_investor_net_formatted": format_currency(total_foreign_net, currency="NT$"),
            "investment_trust_net": total_investment_trust_net,
            "investment_trust_net_formatted": format_currency(
                total_investment_trust_net, currency="NT$"
            ),
            "dealer_net": total_dealer_net,
            "dealer_net_formatted": format_currency(total_dealer_net, currency="NT$"),
            "insights": [],
            "signal": SignalType.NEUTRAL,
            "score": 50,
        }

        # Generate insights and determine signal/score
        if overall_net_flow > 0:
            analysis["signal"] = SignalType.BUY
            analysis["score"] = 70
            analysis["insights"].append(
                f"🟢 機構法人總計淨買超 {analysis['overall_institutional_net_flow_formatted']} (過去 {days} 個交易日)"
            )
        elif overall_net_flow < 0:
            analysis["signal"] = SignalType.SELL
            analysis["score"] = 30
            analysis["insights"].append(
                f"🔴 機構法人總計淨賣超 {analysis['overall_institutional_net_flow_formatted']} (過去 {days} 個交易日)"
            )
        else:
            analysis["insights"].append(f"⚪ 機構法人買賣超不明顯 (過去 {days} 個交易日)")

        if total_foreign_net > 0:
            analysis["insights"].append(
                f"🟢 外資淨買超 {analysis['foreign_investor_net_formatted']}"
            )
        elif total_foreign_net < 0:
            analysis["insights"].append(
                f"🔴 外資淨賣超 {analysis['foreign_investor_net_formatted']}"
            )

        if total_investment_trust_net > 0:
            analysis["insights"].append(
                f"🟢 投信淨買超 {analysis['investment_trust_net_formatted']}"
            )
        elif total_investment_trust_net < 0:
            analysis["insights"].append(
                f"🔴 投信淨賣超 {analysis['investment_trust_net_formatted']}"
            )

        if total_dealer_net > 0:
            analysis["insights"].append(f"🟢 自營商淨買超 {analysis['dealer_net_formatted']}")
        elif total_dealer_net < 0:
            analysis["insights"].append(f"🔴 自營商淨賣超 {analysis['dealer_net_formatted']}")

        return analysis

    def format_summary_table(self, analysis: dict[str, Any]) -> str:
        """Format analysis as ASCII table."""
        lines = []
        lines.append(
            f"═══ 機構法人動向: {analysis['ticker']} ({analysis['analysis_period_start']} 至 {analysis['analysis_period_end']}) ═══"
        )
        lines.append("")

        # Signal
        signal = analysis.get("signal", SignalType.NEUTRAL)
        score = analysis.get("score", 50)
        lines.append(f"總體訊號: {signal.value} (評分: {score}/100)")
        lines.append("")

        # Institutional Net Flow Summary
        lines.append("─── 機構法人淨買賣超 ───")
        lines.append(f"總計淨流量: {analysis.get('overall_institutional_net_flow_formatted', '-')}")
        lines.append(f"外資淨流量: {analysis.get('foreign_investor_net_formatted', '-')}")
        lines.append(f"投信淨流量: {analysis.get('investment_trust_net_formatted', '-')}")
        lines.append(f"自營商淨流量: {analysis.get('dealer_net_formatted', '-')}")
        lines.append("")

        # Insights
        insights = analysis.get("insights", [])
        if insights:
            lines.append("─── 洞察報告 ───")
            for insight in insights:
                lines.append(insight)

        return "\n".join(lines)
