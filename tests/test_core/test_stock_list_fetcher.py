"""Tests for StockListFetcher."""

import json
from pathlib import Path
from unittest.mock import patch

from pulse.core.data.stock_list_fetcher import StockListFetcher


def test_save_all_for_main_program_includes_tw50(monkeypatch):
    test_root = Path.cwd() / "_tmp_stock_list_test"
    test_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.chdir(test_root)

    fetcher = StockListFetcher()
    twse_rows = [{"ticker": "2330", "name": "台積電", "industry": "半導體"}]
    tpex_rows = [{"ticker": "6488", "name": "環球晶", "industry": "半導體"}]

    with patch.object(StockListFetcher, "get_twse_stocks", return_value=twse_rows), patch.object(
        StockListFetcher, "get_tpex_stocks", return_value=tpex_rows
    ):
        files = fetcher.save_all_for_main_program()

    assert "tw_codes_tw50" in files
    tw50_path = test_root / "data" / "tw_codes_tw50.json"
    assert tw50_path.exists()

    with open(tw50_path, encoding="utf-8") as f:
        tickers = json.load(f)

    assert "0050" in tickers
    assert "2330" in tickers
    assert len(tickers) >= 50
