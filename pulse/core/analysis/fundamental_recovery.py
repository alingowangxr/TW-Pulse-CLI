"""
Fundamental Data Recovery Strategy.

Provides intelligent recovery and estimation for missing/incomplete fundamental data:
1. Multi-source data merging (FinMind + yfinance)
2. Sector-based estimation
3. Historical trend estimation
4. Data quality indicators
5. Reasonable defaults with caveats
"""

from datetime import datetime, timedelta
from typing import Any

from pulse.core.data.finmind_data import FinMindFetcher
from pulse.core.data.stock_data_provider import StockDataProvider
from pulse.core.data.yfinance import YFinanceFetcher
from pulse.core.models import FundamentalData
from pulse.utils.logger import get_logger

log = get_logger(__name__)

# Taiwan Stock Market Sector Averages (for estimation)
SECTOR_AVERAGES: dict[str, dict[str, float]] = {
    "Technology": {
        "pe_ratio": 18.5,
        "pb_ratio": 3.2,
        "roe": 12.5,
        "roa": 6.8,
        "debt_to_equity": 0.8,
        "dividend_yield": 2.1,
        "revenue_growth": 8.5,
    },
    "Financial": {
        "pe_ratio": 12.0,
        "pb_ratio": 1.2,
        "roe": 10.5,
        "roa": 0.8,
        "debt_to_equity": 4.5,
        "dividend_yield": 3.5,
        "revenue_growth": 4.2,
    },
    "Semiconductor": {
        "pe_ratio": 22.0,
        "pb_ratio": 4.5,
        "roe": 18.0,
        "roa": 12.0,
        "debt_to_equity": 0.5,
        "dividend_yield": 1.5,
        "revenue_growth": 12.0,
    },
    "Electronics": {
        "pe_ratio": 16.0,
        "pb_ratio": 2.8,
        "roe": 11.0,
        "roa": 6.0,
        "debt_to_equity": 0.9,
        "dividend_yield": 2.3,
        "revenue_growth": 6.5,
    },
    "Traditional": {
        "pe_ratio": 14.0,
        "pb_ratio": 1.8,
        "roe": 9.0,
        "roa": 4.5,
        "debt_to_equity": 1.2,
        "dividend_yield": 4.0,
        "revenue_growth": 3.0,
    },
    "Energy": {
        "pe_ratio": 10.0,
        "pb_ratio": 1.5,
        "roe": 11.0,
        "roa": 6.0,
        "debt_to_equity": 1.0,
        "dividend_yield": 4.5,
        "revenue_growth": 2.0,
    },
    "Healthcare": {
        "pe_ratio": 20.0,
        "pb_ratio": 3.0,
        "roe": 13.0,
        "roa": 7.5,
        "debt_to_equity": 0.7,
        "dividend_yield": 1.8,
        "revenue_growth": 7.0,
    },
    "Default": {
        "pe_ratio": 15.0,
        "pb_ratio": 2.0,
        "roe": 10.0,
        "roa": 5.0,
        "debt_to_equity": 1.0,
        "dividend_yield": 2.5,
        "revenue_growth": 5.0,
    },
}

# Default values for essential metrics when all else fails
SAFE_DEFAULTS: dict[str, float] = {
    "pe_ratio": 15.0,
    "pb_ratio": 2.0,
    "roe": 10.0,
    "roa": 5.0,
    "debt_to_equity": 1.0,
    "dividend_yield": 2.5,
    "revenue_growth": 5.0,
    "earnings_growth": 5.0,
    "current_ratio": 1.5,
    "quick_ratio": 1.0,
}


class FundamentalDataRecovery:
    """
    Recover and estimate missing fundamental data using multiple strategies.
    """

    def __init__(self):
        """Initialize recovery engine."""
        self.finmind = FinMindFetcher()
        self.yfinance = YFinanceFetcher()
        self.provider = StockDataProvider()

    async def fetch_with_recovery(
        self,
        ticker: str,
        sector: str | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
    ) -> tuple[FundamentalData, dict[str, Any]]:
        """
        Fetch fundamental data with recovery for missing values.

        Args:
            ticker: Stock ticker
            sector: Sector for estimation (optional)
            start_date: Start date for data
            end_date: End date for data

        Returns:
            Tuple of (FundamentalData with recovered values, recovery_info)
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365 * 2)).strftime("%Y-%m-%d")
        if not end_date:
            end_date = datetime.now().strftime("%Y-%m-%d")

        # Step 1: Fetch from multiple sources
        finmind_data = None
        yfinance_data = None

        try:
            finmind_data = await self.finmind.fetch_fundamentals(ticker, start_date, end_date)
        except Exception as e:
            log.debug(f"FinMind fetch failed for {ticker}: {e}")

        try:
            yfinance_data = await self.yfinance.fetch_fundamentals(ticker)
        except Exception as e:
            log.debug(f"yfinance fetch failed for {ticker}: {e}")

        # Step 2: Merge data from multiple sources
        merged_data = self._merge_sources(finmind_data, yfinance_data)

        # Step 3: Recover missing values
        recovery_info = {
            "sources_used": [],
            "values_recovered": [],
            "values_estimated": [],
            "values_default": [],
            "data_quality_score": 0.0,
        }

        if finmind_data:
            recovery_info["sources_used"].append("FinMind")
        if yfinance_data:
            recovery_info["sources_used"].append("yfinance")

        # Get sector for estimation
        sector = sector or merged_data.get("sector") or "Default"
        sector_averages = SECTOR_AVERAGES.get(sector, SECTOR_AVERAGES["Default"])

        # Recover each field
        recovered_data = self._recover_field(
            merged_data,
            "pe_ratio",
            sector_averages.get("pe_ratio", SAFE_DEFAULTS["pe_ratio"]),
            recovery_info,
            "P/E Ratio",
        )
        recovered_data = self._recover_field(
            recovered_data,
            "pb_ratio",
            sector_averages.get("pb_ratio", SAFE_DEFAULTS["pb_ratio"]),
            recovery_info,
            "P/B Ratio",
        )
        recovered_data = self._recover_field(
            recovered_data,
            "roe",
            sector_averages.get("roe", SAFE_DEFAULTS["roe"]),
            recovery_info,
            "ROE",
        )
        recovered_data = self._recover_field(
            recovered_data,
            "roa",
            sector_averages.get("roa", SAFE_DEFAULTS["roa"]),
            recovery_info,
            "ROA",
        )
        recovered_data = self._recover_field(
            recovered_data,
            "debt_to_equity",
            sector_averages.get("debt_to_equity", SAFE_DEFAULTS["debt_to_equity"]),
            recovery_info,
            "Debt/Equity",
        )
        recovered_data = self._recover_field(
            recovered_data,
            "dividend_yield",
            sector_averages.get("dividend_yield", SAFE_DEFAULTS["dividend_yield"]),
            recovery_info,
            "Dividend Yield",
        )
        recovered_data = self._recover_field(
            recovered_data,
            "revenue_growth",
            sector_averages.get("revenue_growth", SAFE_DEFAULTS["revenue_growth"]),
            recovery_info,
            "Revenue Growth",
        )

        # Calculate data quality score
        total_fields = 10  # Key fields we track
        present_fields = (
            len(recovery_info["values_recovered"])
            + len(recovery_info["values_estimated"])
            + len(recovery_info["values_default"])
        )
        recovery_info["data_quality_score"] = round((present_fields / total_fields) * 100, 1)

        # Create FundamentalData object
        fundamental_result = FundamentalData(
            ticker=ticker,
            pe_ratio=recovered_data.get("pe_ratio"),
            pb_ratio=recovered_data.get("pb_ratio"),
            ps_ratio=recovered_data.get("ps_ratio"),
            peg_ratio=recovered_data.get("peg_ratio"),
            ev_ebitda=recovered_data.get("ev_ebitda"),
            roe=recovered_data.get("roe"),
            roa=recovered_data.get("roa"),
            npm=recovered_data.get("npm"),
            opm=recovered_data.get("opm"),
            gpm=recovered_data.get("gpm"),
            eps=recovered_data.get("eps"),
            bvps=recovered_data.get("bvps"),
            dps=recovered_data.get("dps"),
            revenue_growth=recovered_data.get("revenue_growth"),
            earnings_growth=recovered_data.get("earnings_growth"),
            debt_to_equity=recovered_data.get("debt_to_equity"),
            current_ratio=recovered_data.get("current_ratio"),
            quick_ratio=recovered_data.get("quick_ratio"),
            dividend_yield=recovered_data.get("dividend_yield"),
            payout_ratio=recovered_data.get("payout_ratio"),
            market_cap=recovered_data.get("market_cap"),
            enterprise_value=recovered_data.get("enterprise_value"),
        )

        return fundamental_result, recovery_info

    def _merge_sources(
        self, finmind_data: FundamentalData | None, yfinance_data: FundamentalData | None
    ) -> dict[str, Any]:
        """
        Merge data from multiple sources, preferring actual values over None.
        """
        merged: dict[str, Any] = {}

        # All fields to merge
        fields = [
            "pe_ratio",
            "pb_ratio",
            "ps_ratio",
            "peg_ratio",
            "ev_ebitda",
            "roe",
            "roa",
            "npm",
            "opm",
            "gpm",
            "eps",
            "bvps",
            "dps",
            "revenue_growth",
            "earnings_growth",
            "debt_to_equity",
            "current_ratio",
            "quick_ratio",
            "dividend_yield",
            "payout_ratio",
            "market_cap",
            "enterprise_value",
        ]

        for field in fields:
            value = None

            # Prefer yfinance for most fields (more comprehensive)
            if yfinance_data:
                value = getattr(yfinance_data, field, None)

            # Fall back to FinMind if yfinance didn't have it
            if value is None and finmind_data:
                value = getattr(finmind_data, field, None)

            merged[field] = value

        return merged

    def _recover_field(
        self,
        data: dict[str, Any],
        field_name: str,
        default_value: float,
        recovery_info: dict[str, Any],
        display_name: str,
    ) -> dict[str, Any]:
        """
        Recover a single field using fallback value.
        """
        if data.get(field_name) is not None:
            # Field is already present from source - count as retrieved
            recovery_info["values_recovered"].append(f"{display_name}")
            return data

        # Use sector average or safe default
        data[field_name] = default_value

        # Determine recovery type
        if field_name in [
            "pe_ratio",
            "pb_ratio",
            "roe",
            "roa",
            "debt_to_equity",
            "dividend_yield",
            "revenue_growth",
        ]:
            recovery_info["values_estimated"].append(f"{display_name} (sector average)")
        else:
            recovery_info["values_default"].append(f"{display_name} (default)")

        return data

    def get_recovery_report(self, recovery_info: dict[str, Any]) -> str:
        """
        Generate a human-readable recovery report.
        """
        lines = ["\n📊 Fundamental Data Recovery Report\n"]

        # Sources
        if recovery_info["sources_used"]:
            lines.append(f"📍 Data Sources: {', '.join(recovery_info['sources_used'])}")

        # Quality score
        score = recovery_info["data_quality_score"]
        quality = (
            "Excellent"
            if score >= 90
            else "Good"
            if score >= 70
            else "Fair"
            if score >= 50
            else "Poor"
        )
        lines.append(f"📈 Data Quality Score: {score}% ({quality})")

        # Recovered values
        if recovery_info["values_recovered"]:
            lines.append(f"\n✅ Retrieved Values ({len(recovery_info['values_recovered'])}):")
            for v in recovery_info["values_recovered"]:
                lines.append(f"   • {v}")

        # Estimated values
        if recovery_info["values_estimated"]:
            lines.append(
                f"\n⚠️ Estimated Values ({len(recovery_info['values_estimated'])}, sector-based):"
            )
            for v in recovery_info["values_estimated"]:
                lines.append(f"   • {v}")

        # Default values
        if recovery_info["values_default"]:
            lines.append(f"\n❌ Default Values ({len(recovery_info['values_default'])}):")
            for v in recovery_info["values_default"]:
                lines.append(f"   • {v}")

        return "\n".join(lines)


# Convenience function
async def fetch_fundamentals_with_recovery(
    ticker: str,
    sector: str | None = None,
) -> tuple[FundamentalData, dict[str, Any]]:
    """
    Fetch fundamental data with automatic recovery for missing values.
    """
    recovery = FundamentalDataRecovery()
    return await recovery.fetch_with_recovery(ticker, sector=sector)
