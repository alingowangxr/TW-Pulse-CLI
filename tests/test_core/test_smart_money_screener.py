"""Tests for SmartMoneyScreener."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from pulse.core.models import OHLCV
from pulse.core.smart_money_screener import SmartMoneyScreener


@pytest.mark.asyncio
async def test_fetch_full_data_reuses_cached_history():
    screener = SmartMoneyScreener()
    screener.fetcher.fetch_stock = AsyncMock(
        return_value=SimpleNamespace(
            ticker="2330",
            name="台積電",
            sector="半導體",
            current_price=820.0,
            change_percent=0.61,
            volume=1000,
            history=[
                OHLCV(
                    date=datetime(2025, 1, 1),
                    open=810,
                    high=820,
                    low=805,
                    close=815,
                    volume=900,
                ),
                OHLCV(
                    date=datetime(2025, 1, 2),
                    open=815,
                    high=825,
                    low=814,
                    close=820,
                    volume=1000,
                ),
            ],
        )
    )
    screener.fetcher.fetch_history = AsyncMock()

    result = await screener._fetch_full_data("2330", fast_mode=True)

    assert result is not None
    screener.fetcher.fetch_stock.assert_awaited_once()
    screener.fetcher.fetch_history.assert_not_awaited()
