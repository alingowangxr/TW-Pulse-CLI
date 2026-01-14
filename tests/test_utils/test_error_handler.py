"""Tests for Error Handler - Exception classes and utilities."""

import pytest

from pulse.utils.error_handler import (
    PulseError,
    APIError,
    DataNotFoundError,
    RateLimitError,
    NetworkError,
    ValidationError,
    ConfigurationError,
    get_user_friendly_error,
    format_error_response,
)


class TestPulseExceptionClasses:
    """Test cases for exception classes."""

    def test_pulse_error_is_base(self):
        """Test PulseError is the base exception class."""
        error = PulseError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"
        assert error.user_message == "Test error"
        assert error.details == {}

    def test_pulse_error_with_details(self):
        """Test PulseError with details."""
        error = PulseError("Test error", details={"key": "value"})
        assert error.details == {"key": "value"}

    def test_api_error_inheritance(self):
        """Test APIError inherits from PulseError."""
        error = APIError("Request failed", api_name="TestAPI", status_code=500)
        assert isinstance(error, PulseError)
        assert isinstance(error, Exception)
        assert hasattr(error, "status_code")
        assert error.status_code == 500
        assert error.api_name == "TestAPI"

    def test_data_not_found_error(self):
        """Test DataNotFoundError inherits from PulseError."""
        error = DataNotFoundError("2330", "price data")
        assert isinstance(error, PulseError)
        assert "2330" in str(error)
        assert "price data" in str(error)
        assert error.ticker == "2330"

    def test_rate_limit_error(self):
        """Test RateLimitError inherits from APIError."""
        error = RateLimitError(api_name="FinMind", retry_after=60)
        assert isinstance(error, APIError)
        assert isinstance(error, PulseError)
        assert hasattr(error, "retry_after")
        assert error.retry_after == 60

    def test_network_error(self):
        """Test NetworkError inherits from APIError."""
        error = NetworkError(api_name="yfinance")
        assert isinstance(error, APIError)
        assert isinstance(error, PulseError)
        assert "yfinance" in str(error)

    def test_validation_error(self):
        """Test ValidationError inherits from PulseError."""
        error = ValidationError(field="ticker", value="INVALID", reason="Invalid format")
        assert isinstance(error, PulseError)
        assert hasattr(error, "field")
        assert error.field == "ticker"
        assert hasattr(error, "value")
        assert error.value == "INVALID"

    def test_configuration_error(self):
        """Test ConfigurationError inherits from PulseError."""
        error = ConfigurationError(setting="GROQ_API_KEY", reason="Missing API key")
        assert isinstance(error, PulseError)
        assert hasattr(error, "setting")
        assert error.setting == "GROQ_API_KEY"


class TestErrorFormatting:
    """Test cases for error formatting utilities."""

    def test_get_user_friendly_error_api(self):
        """Test API error formatting."""
        error = APIError("Request failed", api_name="TestAPI", status_code=404)
        result = get_user_friendly_error(error)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_user_friendly_error_not_found(self):
        """Test DataNotFoundError formatting."""
        error = DataNotFoundError("2330", "price")
        result = get_user_friendly_error(error)

        assert isinstance(result, str)
        assert "2330" in result or "找不到" in result

    def test_get_user_friendly_error_rate_limit(self):
        """Test RateLimitError formatting."""
        error = RateLimitError(api_name="FinMind", retry_after=30)
        result = get_user_friendly_error(error)

        assert isinstance(result, str)

    def test_get_user_friendly_error_network(self):
        """Test NetworkError formatting."""
        error = NetworkError(api_name="yfinance")
        result = get_user_friendly_error(error)

        assert isinstance(result, str)
        assert "連線" in result or "network" in result.lower()

    def test_get_user_friendly_error_validation(self):
        """Test ValidationError formatting."""
        error = ValidationError(field="price", value="abc", reason="Must be number")
        result = get_user_friendly_error(error)

        assert isinstance(result, str)

    def test_get_user_friendly_error_configuration(self):
        """Test ConfigurationError formatting."""
        error = ConfigurationError(setting="API_KEY", reason="Missing")
        result = get_user_friendly_error(error)

        assert isinstance(result, str)
        assert "設定" in result or "config" in result.lower()

    def test_get_user_friendly_error_generic(self):
        """Test generic error formatting."""
        error = PulseError("Unknown error")
        result = get_user_friendly_error(error)

        assert isinstance(result, str)
        assert len(result) > 0

    def test_format_error_response(self):
        """Test error response formatting."""
        error = APIError("Test error", api_name="API", status_code=500)
        response = format_error_response(error)

        assert isinstance(response, str)
        assert "錯誤" in response or "Error" in response


class TestExceptionHierarchy:
    """Test exception hierarchy is correct."""

    def test_exception_hierarchy(self):
        """Verify all exceptions form correct hierarchy."""
        exceptions = [
            PulseError,
            APIError,
            DataNotFoundError,
            RateLimitError,
            NetworkError,
            ValidationError,
            ConfigurationError,
        ]

        for exc in exceptions[1:]:  # Skip PulseError (base)
            assert issubclass(exc, PulseError)

    def test_exception_can_be_caught_by_base(self):
        """Test that specific exceptions can be caught by base."""
        errors = [
            APIError("test", api_name="API"),
            DataNotFoundError("2330", "data"),
            RateLimitError(api_name="API"),
            NetworkError(api_name="API"),
            ValidationError(field="f", value="v", reason="r"),
            ConfigurationError(setting="s", reason="r"),
        ]

        for error in errors:
            with pytest.raises(PulseError):
                raise error


class TestErrorContext:
    """Test error context information."""

    def test_api_error_context(self):
        """Test APIError has correct context."""
        error = APIError("Request failed", api_name="StockAPI", status_code=404)

        assert error.status_code == 404
        assert error.api_name == "StockAPI"

    def test_validation_error_context(self):
        """Test ValidationError has correct context."""
        error = ValidationError(field="ticker", value="INVALID!@#", reason="Invalid format")

        assert error.field == "ticker"
        assert error.value == "INVALID!@#"
        assert "Invalid format" in str(error)

    def test_configuration_error_context(self):
        """Test ConfigurationError has correct context."""
        error = ConfigurationError(setting="GROQ_API_KEY", reason="Required API key not found")

        assert error.setting == "GROQ_API_KEY"
        assert "Required API key" in str(error)
