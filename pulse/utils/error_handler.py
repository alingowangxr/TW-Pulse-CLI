"""Error handling utilities with user-friendly messages."""

from typing import Any

from pulse.utils.logger import get_logger

log = get_logger(__name__)


class PulseError(Exception):
    """Base exception for Pulse CLI errors."""

    def __init__(
        self, message: str, user_message: str | None = None, details: dict[str, Any] | None = None
    ):
        super().__init__(message)
        self.user_message = user_message or message
        self.details = details or {}

    def log(self) -> None:
        """Log the error with details."""
        log.error(f"{self.__class__.__name__}: {self.args[0]}", extra=self.details)


class APIError(PulseError):
    """Exception for API-related errors."""

    def __init__(
        self,
        message: str,
        api_name: str = "API",
        status_code: int | None = None,
        user_message: str | None = None,
    ):
        details = {"api_name": api_name, "status_code": status_code}
        super().__init__(f"{api_name} error: {message}", user_message, details)
        self.api_name = api_name
        self.status_code = status_code


class DataNotFoundError(PulseError):
    """Exception when data is not found."""

    def __init__(self, ticker: str, data_type: str = "stock data", user_message: str | None = None):
        message = f"No {data_type} found for ticker: {ticker}"
        if user_message is None:
            user_message = f"找不到 {ticker} 的 {data_type}。請確認股票代號是否正確。"
        super().__init__(message, user_message, {"ticker": ticker, "data_type": data_type})
        self.ticker = ticker


class RateLimitError(APIError):
    """Exception when API rate limit is exceeded."""

    def __init__(self, api_name: str = "API", retry_after: int | None = None):
        user_message = f"{api_name} 請求次數已達上限，請稍後再試。"
        super().__init__(
            f"Rate limit exceeded for {api_name}",
            api_name,
            status_code=429,
            user_message=user_message,
        )
        self.retry_after = retry_after


class NetworkError(APIError):
    """Exception for network-related errors."""

    def __init__(self, api_name: str = "Network", user_message: str | None = None):
        if user_message is None:
            user_message = f"無法連線到 {api_name}，請檢查網路連線後再試。"
        super().__init__(f"Network error accessing {api_name}", api_name, user_message=user_message)
        self.api_name = api_name


class ValidationError(PulseError):
    """Exception for validation errors."""

    def __init__(self, field: str, value: Any, reason: str, user_message: str | None = None):
        message = f"Validation error for {field}: {value} - {reason}"
        if user_message is None:
            user_message = f"輸入驗證失敗：{field}={value}，原因：{reason}"
        super().__init__(message, user_message, {"field": field, "value": value, "reason": reason})
        self.field = field
        self.value = value


class ConfigurationError(PulseError):
    """Exception for configuration errors."""

    def __init__(self, setting: str, reason: str, user_message: str | None = None):
        message = f"Configuration error for {setting}: {reason}"
        if user_message is None:
            user_message = f"設定錯誤：{setting} - {reason}。請檢查設定檔或環境變數。"
        super().__init__(message, user_message, {"setting": setting, "reason": reason})
        self.setting = setting


def get_user_friendly_error(error: Exception) -> str:
    """
    Convert an exception to a user-friendly error message.

    Args:
        error: The exception to convert

    Returns:
        User-friendly error message string
    """
    # Check if it's a PulseError with user_message
    if isinstance(error, PulseError):
        return error.user_message

    # Handle common error types
    error_type = type(error).__name__
    error_str = str(error).lower()

    # Timeout errors
    if "timeout" in error_str or isinstance(error, TimeoutError):
        return "請求超時，請稍後再試。如果問題持續發生，請檢查網路連線。"

    # Connection errors
    if "connection" in error_str or "network" in error_str:
        return "無法連線到伺服器，請檢查網路連線後再試。"

    # Authentication errors
    if "auth" in error_str or "api_key" in error_str or "unauthorized" in error_str:
        return "認證失敗，請確認 API Key 已正確設定。"

    # Rate limit errors
    if "rate limit" in error_str or "429" in error_str:
        return "請求次數已達上限，請稍後再試。"

    # Data not found
    if "not found" in error_str or "no data" in error_str:
        return "找不到相關資料，請確認股票代號是否正確。"

    # General fallback
    return f"發生錯誤：{error_str if str(error) else error_type}"


def format_error_response(error: Exception) -> str:
    """
    Format an error for display to the user.

    Args:
        error: The exception to format

    Returns:
        Formatted error message string
    """
    user_msg = get_user_friendly_error(error)
    return f"❌ 錯誤：{user_msg}"
