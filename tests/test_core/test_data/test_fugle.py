"""Tests for Fugle Market Data provider."""

import pytest
from unittest.mock import MagicMock
from datetime import datetime

import pandas as pd

from pulse.core.data.fugle import (
    FugleFetcher,
    FugleAPIError,
    RateLimitError,
    UnauthorizedError,
    NotFoundError,
    NetworkError,
    APIError,
)


class TestFugleFetcher:
    """Test cases for FugleFetcher class."""

    @pytest.fixture
    def fetcher(self):
        """Create a FugleFetcher instance with mock API key."""
        return FugleFetcher(api_key="test_api_key")

    def test_format_ticker(self, fetcher):
        """Test ticker formatting."""
        assert fetcher._format_ticker("2330") == "2330"
        assert fetcher._format_ticker("2330.TW") == "2330"
        assert fetcher._format_ticker("2330.TWO") == "2330"
        assert fetcher._format_ticker("  2330  ") == "2330"

    def test_get_headers(self, fetcher):
        """Test header generation."""
        headers = fetcher._get_headers()
        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"
        assert headers["X-API-KEY"] == "test_api_key"

    def test_get_headers_no_api_key(self):
        """Test header generation without API key."""
        fetcher = FugleFetcher(api_key="")
        headers = fetcher._get_headers()
        assert "X-API-KEY" not in headers

    def test_index_mapping(self, fetcher):
        """Test index mapping."""
        assert fetcher.INDEX_MAPPING["TAIEX"] == ("TAIEX", "Taiwan Weighted Index")
        assert fetcher.INDEX_MAPPING["TWII"] == ("TAIEX", "Taiwan Weighted Index")
        assert fetcher.INDEX_MAPPING["TPEX"] == ("TPEX", "Taiwan OTC Index")
        assert fetcher.INDEX_MAPPING["OTC"] == ("TPEX", "Taiwan OTC Index")

    def test_close_session(self, fetcher):
        """Test session closing."""
        # Create a mock client
        mock_client = MagicMock()
        mock_client.is_closed = False
        fetcher._client = mock_client

        fetcher.close()

        mock_client.close.assert_called_once()
        assert fetcher._client is None

    def test_close_already_closed(self, fetcher):
        """Test closing already closed session."""
        fetcher._client = None
        # Should not raise
        fetcher.close()

    def test_close_with_open_session(self, fetcher):
        """Test closing when session exists and is open."""
        # Create a mock client
        mock_client = MagicMock()
        mock_client.is_closed = False
        fetcher._client = mock_client

        fetcher.close()

        mock_client.close.assert_called_once()
        assert fetcher._client is None


class TestFugleStockData:
    """Test cases for StockData model with Fugle data."""

    def test_stock_data_creation(self):
        """Test StockData model creation."""
        from pulse.core.models import StockData, OHLCV

        stock_data = StockData(
            ticker="2330",
            name="台積電",
            sector="半導體",
            industry="半導體製造",
            current_price=1710.0,
            previous_close=1700.0,
            change=10.0,
            change_percent=0.59,
            volume=33253803,
            avg_volume=28000000,
            day_low=1700.0,
            day_high=1715.0,
            week_52_low=780.0,
            week_52_high=1720.0,
            market_cap=1000000000000,
            shares_outstanding=5000000000,
            history=[],
        )

        assert stock_data.ticker == "2330"
        assert stock_data.name == "台積電"
        assert stock_data.current_price == 1710.0

    def test_stock_data_price_change_calculation(self):
        """Test StockData price change calculation."""
        from pulse.core.models import StockData

        current_price = 1710.0
        previous_close = 1700.0
        change = current_price - previous_close
        change_percent = (change / previous_close * 100) if previous_close else 0.0

        assert change == 10.0
        assert change_percent == pytest.approx(0.588, rel=0.01)


class TestFugleExceptions:
    """Test cases for Fugle exception classes."""

    def test_fugle_api_error(self):
        """Test FugleAPIError exception."""
        with pytest.raises(FugleAPIError):
            raise FugleAPIError("Test error")

    def test_rate_limit_error(self):
        """Test RateLimitError exception."""
        with pytest.raises(FugleAPIError):
            raise RateLimitError("Rate limit exceeded")

    def test_unauthorized_error(self):
        """Test UnauthorizedError exception."""
        with pytest.raises(FugleAPIError):
            raise UnauthorizedError("Unauthorized")

    def test_not_found_error(self):
        """Test NotFoundError exception."""
        with pytest.raises(FugleAPIError):
            raise NotFoundError("Not found")

    def test_network_error(self):
        """Test NetworkError exception."""
        with pytest.raises(FugleAPIError):
            raise NetworkError("Network error")

    def test_api_error(self):
        """Test APIError exception."""
        with pytest.raises(FugleAPIError):
            raise APIError("API error")

    def test_exception_inheritance(self):
        """Test exception inheritance chain."""
        assert issubclass(RateLimitError, FugleAPIError)
        assert issubclass(UnauthorizedError, FugleAPIError)
        assert issubclass(NotFoundError, FugleAPIError)
        assert issubclass(NetworkError, FugleAPIError)
        assert issubclass(APIError, FugleAPIError)


class TestFugleConfiguration:
    """Test cases for Fugle configuration."""

    def test_api_base_url(self):
        """Test API base URL configuration."""
        from pulse.core.data.fugle import FUGLE_BASE_URL, FUGLE_API_VERSION

        assert FUGLE_BASE_URL == "https://api.fugle.tw"
        assert FUGLE_API_VERSION == "marketdata/v1.0"

    def test_full_api_url(self):
        """Test full API URL construction."""
        from pulse.core.data.fugle import FUGLE_BASE_URL, FUGLE_API_VERSION

        endpoint = "/stock/historical/stats/2330"
        expected_url = f"{FUGLE_BASE_URL}/{FUGLE_API_VERSION}{endpoint}"

        assert expected_url == "https://api.fugle.tw/marketdata/v1.0/stock/historical/stats/2330"


class TestFugleMockRequests:
    """Test cases for FugleFetcher with mocked requests."""

    @pytest.fixture
    def fetcher(self):
        """Create a FugleFetcher instance with mock API key."""
        return FugleFetcher(api_key="test_api_key")

    def test_fetch_stock_success(self, fetcher):
        """Test successful stock fetch."""
        mock_response = {
            "data": {
                "date": "2026-01-14",
                "symbol": "2330",
                "name": "台積電",
                "closePrice": 1710.0,
                "previousClose": 1700.0,
                "change": 10.0,
                "changePercent": 0.59,
                "week52High": 1720.0,
                "week52Low": 780.0,
                "tradeVolume": 33253803,
                "highPrice": 1715.0,
                "lowPrice": 1700.0,
            }
        }

        # Mock the client and request
        mock_client = MagicMock()
        mock_response_obj = MagicMock()
        mock_response_obj.status_code = 200
        mock_response_obj.json.return_value = mock_response
        mock_client.get.return_value = mock_response_obj
        mock_client.is_closed = False
        fetcher._client = mock_client

        result = fetcher.fetch_stock("2330")

        assert result is not None
        assert result.ticker == "2330"
        assert result.name == "台積電"
        assert result.current_price == 1710.0
        assert result.previous_close == 1700.0

    def test_fetch_stock_not_found(self, fetcher):
        """Test stock fetch with 404 response."""
        mock_client = MagicMock()
        mock_response_obj = MagicMock()
        mock_response_obj.status_code = 404
        mock_response_obj.text = "Not found"
        mock_client.get.return_value = mock_response_obj
        mock_client.is_closed = False
        fetcher._client = mock_client

        result = fetcher.fetch_stock("INVALID")

        assert result is None

    def test_fetch_index_taiex(self, fetcher):
        """Test TAIEX index fetch via proxy."""
        mock_response = {
            "data": {
                "date": "2026-01-14",
                "symbol": "0050",
                "closePrice": 170.5,
                "previousClose": 169.0,
                "change": 1.5,
                "changePercent": 0.89,
                "week52High": 180.0,
                "week52Low": 140.0,
                "tradeVolume": 5000000,
                "highPrice": 171.0,
                "lowPrice": 169.0,
            }
        }

        mock_client = MagicMock()
        mock_response_obj = MagicMock()
        mock_response_obj.status_code = 200
        mock_response_obj.json.return_value = mock_response
        mock_client.get.return_value = mock_response_obj
        mock_client.is_closed = False
        fetcher._client = mock_client

        result = fetcher.fetch_index("TAIEX")

        assert result is not None
        assert result.ticker == "TAIEX"
        assert result.name == "Taiwan Weighted Index (TAIEX)"
        assert result.current_price == 170.5

    def test_fetch_index_tpex(self, fetcher):
        """Test TPEX index fetch via proxy."""
        mock_response = {
            "data": {
                "date": "2026-01-14",
                "symbol": "0051",
                "closePrice": 99.3,
                "previousClose": 98.5,
                "change": 0.8,
                "changePercent": 0.81,
                "week52High": 105.0,
                "week52Low": 85.0,
                "tradeVolume": 1000000,
                "highPrice": 99.8,
                "lowPrice": 98.2,
            }
        }

        mock_client = MagicMock()
        mock_response_obj = MagicMock()
        mock_response_obj.status_code = 200
        mock_response_obj.json.return_value = mock_response
        mock_client.get.return_value = mock_response_obj
        mock_client.is_closed = False
        fetcher._client = mock_client

        result = fetcher.fetch_index("TPEX")

        assert result is not None
        assert result.ticker == "TPEX"
        assert result.name == "Taiwan OTC Index (TPEX)"
        assert result.current_price == 99.3
