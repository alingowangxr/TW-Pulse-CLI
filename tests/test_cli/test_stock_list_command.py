"""Tests for /stocks command."""

from unittest.mock import MagicMock, patch

import pytest

from pulse.cli.commands.stock_list import parse_stocks_args, stocks_command


def test_parse_stocks_args_supports_sync():
    parsed = parse_stocks_args("--sync")

    assert parsed["sync"] is True


@pytest.mark.asyncio
async def test_stocks_command_sync_refreshes_all_files():
    mock_fetcher = MagicMock()
    mock_fetcher.save_all_for_main_program.return_value = {
        "tw_codes_tw50": "data/tw_codes_tw50.json",
        "tw_tickers": "data/tw_tickers.json",
        "tw_codes_listed": "data/tw_codes_listed.json",
        "tw_codes_otc": "data/tw_codes_otc.json",
        "stock_list": "data/stock_list.json",
    }
    mock_fetcher.get_twse_stocks.return_value = [{"ticker": "2330"}]
    mock_fetcher.get_tpex_stocks.return_value = [{"ticker": "6488"}]

    mock_app = MagicMock()
    mock_app.config = MagicMock()
    mock_app.config.finmind_token = ""

    with patch("pulse.cli.commands.stock_list.StockListFetcher", return_value=mock_fetcher):
        result = await stocks_command(mock_app, "--sync")

    assert "股票清單同步完成" in result
    assert "TW50: data/tw_codes_tw50.json" in result
    assert "TWSE: data/tw_codes_listed.json" in result
    assert "TPEx: data/tw_codes_otc.json" in result
    mock_fetcher.save_all_for_main_program.assert_called_once()
