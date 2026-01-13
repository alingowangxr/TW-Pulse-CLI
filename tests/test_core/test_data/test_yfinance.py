import pytest
import pandas as pd
from datetime import datetime
from unittest.mock import MagicMock, patch

from pulse.core.data.yfinance import YFinanceFetcher
from pulse.core.models import StockData, FundamentalData, OHLCV


@pytest.fixture
def fetcher():
    return YFinanceFetcher(suffix=".TW")


@pytest.fixture
def mock_yf_ticker():
    with patch("yfinance.Ticker") as mock:
        yield mock


@pytest.fixture
def mock_stock_data(mock_yf_ticker):
    # Mock history data
    dates = pd.date_range(start="2023-01-01", periods=5, freq="D")
    history_data = {
        "Open": [1000, 1010, 1005, 1020, 1015],
        "High": [1020, 1025, 1015, 1030, 1025],
        "Low": [990, 1000, 995, 1010, 1005],
        "Close": [1010, 1005, 1020, 1015, 1025],
        "Volume": [10000, 12000, 11000, 13000, 15000],
    }
    hist_df = pd.DataFrame(history_data, index=dates)

    # Mock info data
    info_data = {
        "longName": "Taiwan Semiconductor Manufacturing Company",
        "shortName": "2330",
        "sector": "Technology",
        "industry": "Semiconductors",
        "averageVolume": 12000000,
        "marketCap": 15000000000000,
        "sharesOutstanding": 25900000000,
        "trailingPE": 25.5,
        "priceToBook": 5.2,
        "dividendYield": 0.018,
    }

    mock_ticker_instance = mock_yf_ticker.return_value
    mock_ticker_instance.history.return_value = hist_df
    mock_ticker_instance.info = info_data

    return mock_ticker_instance


class TestYFinanceFetcher:
    def test_init(self):
        fetcher = YFinanceFetcher()
        assert fetcher.suffix == ".TW"

        fetcher_custom = YFinanceFetcher(suffix=".TWO")
        assert fetcher_custom.suffix == ".TWO"

    def test_format_ticker(self, fetcher):
        assert fetcher._format_ticker("2330") == "2330.TW"
        assert fetcher._format_ticker("2454") == "2454.TW"
        assert fetcher._format_ticker("2330.TW") == "2330.TW"

        # Test index
        assert fetcher._format_ticker("TAIEX") == "^TWII"
        assert fetcher._format_ticker("^TWII") == "^TWII"

    def test_clean_ticker(self, fetcher):
        assert fetcher._clean_ticker("2330.TW") == "2330"
        assert fetcher._clean_ticker("2330") == "2330"

    @pytest.mark.asyncio
    async def test_fetch_stock_success(self, fetcher, mock_stock_data):
        ticker = "2330"
        data = await fetcher.fetch_stock(ticker)

        assert data is not None
        assert isinstance(data, StockData)
        assert data.ticker == "2330"
        assert data.name == "Taiwan Semiconductor Manufacturing Company"
        assert data.current_price == 1025.0
        assert data.previous_close == 1015.0
        assert data.change == 10.0
        assert data.change_percent == pytest.approx(0.985, abs=0.001)
        assert len(data.history) == 5

    @pytest.mark.asyncio
    async def test_fetch_stock_no_data(self, fetcher, mock_yf_ticker):
        mock_ticker_instance = mock_yf_ticker.return_value
        mock_ticker_instance.history.return_value = pd.DataFrame()

        data = await fetcher.fetch_stock("UNKNOWN")
        assert data is None

    @pytest.mark.asyncio
    async def test_fetch_index_success(self, fetcher, mock_stock_data):
        index = "TAIEX"

        # Mock index info
        mock_stock_data.info = {"shortName": "TSEC weighted index", "averageVolume": 5000000000}

        data = await fetcher.fetch_index(index)

        assert data is not None
        assert isinstance(data, StockData)
        assert data.ticker == "TAIEX"
        assert data.name == "Taiwan Weighted Index"
        assert data.sector == "Index"
        assert data.current_price == 1025.0
