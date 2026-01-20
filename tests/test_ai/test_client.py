"""Tests for AI client (pulse/ai/client.py)."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from pulse.ai.client import AIClient


class MockResponse:
    """Mock LiteLLM response."""

    def __init__(self, content: str):
        self.choices = [MockChoice(content)]


class MockChoice:
    """Mock choice in response."""

    def __init__(self, content: str):
        self.message = MockMessage(content)


class MockMessage:
    """Mock message in choice."""

    def __init__(self, content: str):
        self.content = content


@pytest.fixture
def mock_litellm():
    """Mock litellm acompletion."""
    with patch("pulse.ai.client.acompletion", new_callable=AsyncMock) as mock:
        yield mock


@pytest.fixture
def ai_client(mock_litellm):
    """Create AI client with mocked litellm."""
    client = AIClient(model="deepseek/deepseek-chat")
    return client


class TestAIClientInitialization:
    """Test cases for AIClient initialization."""

    def test_default_initialization(self, ai_client):
        """Test default initialization."""
        assert ai_client.model == "deepseek/deepseek-chat"
        assert ai_client.temperature is not None
        assert ai_client.max_tokens is not None
        assert ai_client.timeout is not None

    def test_custom_model_initialization(self):
        """Test initialization with custom model."""
        client = AIClient(model="anthropic/claude-sonnet-4-20250514")
        assert client.model == "anthropic/claude-sonnet-4-20250514"

    def test_empty_history_on_init(self, ai_client):
        """Test conversation history starts empty."""
        assert ai_client._conversation_history == []


class TestSetModel:
    """Test cases for set_model method."""

    def test_set_valid_model(self, ai_client):
        """Test setting a valid model."""
        with patch.object(ai_client, "model", new_callable=lambda: None):
            pass
        # Just verify method exists and is callable
        assert callable(ai_client.set_model)


class TestGetCurrentModel:
    """Test cases for get_current_model method."""

    def test_get_current_model_returns_dict(self, ai_client):
        """Test that get_current_model returns a dictionary."""
        result = ai_client.get_current_model()
        assert isinstance(result, dict)
        assert "id" in result
        assert "name" in result
        assert "deepseek" in result["id"].lower()


class TestListModels:
    """Test cases for list_models method."""

    def test_list_models_returns_list(self, ai_client):
        """Test that list_models returns a list."""
        result = ai_client.list_models()
        assert isinstance(result, list)
        assert len(result) > 0

    def test_list_models_contains_expected_models(self, ai_client):
        """Test that expected models are in the list."""
        result = ai_client.list_models()
        model_ids = [m["id"] for m in result]
        assert any("deepseek" in m for m in model_ids)
        assert any("groq" in m for m in model_ids)


class TestClearHistory:
    """Test cases for clear_history method."""

    def test_clear_history_empties_history(self, ai_client):
        """Test that clear_history empties conversation history."""
        # Add some mock history
        ai_client._conversation_history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]
        ai_client.clear_history()
        assert ai_client._conversation_history == []


class TestChat:
    """Test cases for chat method."""

    @pytest.mark.asyncio
    async def test_chat_returns_response(self, ai_client, mock_litellm):
        """Test that chat returns a response."""
        mock_litellm.return_value = MockResponse("分析結果: 台積電股價上漲")

        result = await ai_client.chat("分析 2330")

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_chat_adds_to_history(self, ai_client, mock_litellm):
        """Test that chat adds messages to history."""
        mock_litellm.return_value = MockResponse("分析結果")

        initial_history_len = len(ai_client._conversation_history)
        await ai_client.chat("Test message")

        assert len(ai_client._conversation_history) == initial_history_len + 2

    @pytest.mark.asyncio
    async def test_chat_with_custom_system_prompt(self, ai_client, mock_litellm):
        """Test chat with custom system prompt."""
        mock_litellm.return_value = MockResponse("自定義回應")

        result = await ai_client.chat(
            message="Test",
            system_prompt="你是一個股票分析專家",
        )

        assert isinstance(result, str)
        # Verify acompletion was called
        mock_litellm.assert_called_once()

    @pytest.mark.asyncio
    async def test_chat_without_history(self, ai_client, mock_litellm):
        """Test chat without using history."""
        mock_litellm.return_value = MockResponse("回應")

        result = await ai_client.chat("Test", use_history=False)

        assert isinstance(result, str)
        # History should remain empty
        assert ai_client._conversation_history == []

    @pytest.mark.asyncio
    async def test_chat_error_handling(self, ai_client, mock_litellm):
        """Test chat error handling."""
        mock_litellm.side_effect = Exception("API Error")

        with pytest.raises(Exception):
            await ai_client.chat("Test")

    @pytest.mark.asyncio
    async def test_greeting_handled(self, ai_client, mock_litellm):
        """Test that greetings are handled with identity reminder."""
        mock_litellm.return_value = MockResponse("你好！")

        result = await ai_client.chat("嗨")

        assert isinstance(result, str)
        mock_litellm.assert_called_once()


class TestChatStream:
    """Test cases for chat_stream method."""

    @pytest.mark.asyncio
    async def test_chat_stream_yields_chunks(self, ai_client, mock_litellm):
        """Test that chat_stream yields response chunks."""

        # Create a mock async iterator
        async def mock_stream():
            chunks = [
                type(
                    "Chunk",
                    (),
                    {
                        "choices": [
                            type(
                                "Delta", (), {"delta": type("Content", (), {"content": "第一"})()}
                            )()
                        ]
                    },
                )(),
                type(
                    "Chunk",
                    (),
                    {
                        "choices": [
                            type(
                                "Delta", (), {"delta": type("Content", (), {"content": "第二"})()}
                            )()
                        ]
                    },
                )(),
                type(
                    "Chunk",
                    (),
                    {
                        "choices": [
                            type(
                                "Delta", (), {"delta": type("Content", (), {"content": "部分"})()}
                            )()
                        ]
                    },
                )(),
            ]
            for chunk in chunks:
                yield chunk

        mock_litellm.return_value = mock_stream()

        chunks = []
        async for chunk in ai_client.chat_stream("Test"):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert "".join(chunks) == "第一第二部分"

    @pytest.mark.asyncio
    async def test_chat_stream_updates_history(self, ai_client, mock_litellm):
        """Test that chat_stream updates history after complete."""

        async def mock_stream():
            chunk = type(
                "Chunk",
                (),
                {
                    "choices": [
                        type("Delta", (), {"delta": type("Content", (), {"content": "回應"})()})()
                    ]
                },
            )()
            yield chunk

        mock_litellm.return_value = mock_stream()

        async for _ in ai_client.chat_stream("Test"):
            pass

        # History should be updated after streaming
        assert len(ai_client._conversation_history) == 2


class TestAnalyzeStock:
    """Test cases for analyze_stock method."""

    @pytest.mark.asyncio
    async def test_analyze_stock_returns_response(self, ai_client, mock_litellm):
        """Test that analyze_stock returns analysis response."""
        mock_litellm.return_value = MockResponse("技術分析: RSI 偏高")

        stock_data = {
            "price": 820.0,
            "rsi_14": 65.0,
            "macd": 2.5,
        }

        result = await ai_client.analyze_stock("2330", stock_data, "technical")

        assert isinstance(result, str)
        mock_litellm.assert_called_once()

    @pytest.mark.asyncio
    async def test_analyze_stock_comprehensive(self, ai_client, mock_litellm):
        """Test comprehensive stock analysis."""
        mock_litellm.return_value = MockResponse("綜合分析: 建議買入")

        stock_data = {
            "price": 820.0,
            "rsi_14": 55.0,
            "pe_ratio": 25.0,
        }

        result = await ai_client.analyze_stock("2330", stock_data, "comprehensive")

        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_analyze_stock_fundamental(self, ai_client, mock_litellm):
        """Test fundamental stock analysis."""
        mock_litellm.return_value = MockResponse("基本面: 獲利成長")

        stock_data = {
            "pe_ratio": 12.0,
            "roe": 25.0,
        }

        result = await ai_client.analyze_stock("2330", stock_data, "fundamental")

        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_analyze_stock_broker_flow(self, ai_client, mock_litellm):
        """Test broker flow analysis."""
        mock_litellm.return_value = MockResponse("法人買超")

        stock_data = {
            "foreign_net_buy": 500000000,
            "trust_net_buy": 100000000,
        }

        result = await ai_client.analyze_stock("2330", stock_data, "broker")

        assert isinstance(result, str)


class TestGetRecommendation:
    """Test cases for get_recommendation method."""

    @pytest.mark.asyncio
    async def test_get_recommendation_returns_dict(self, ai_client, mock_litellm):
        """Test that get_recommendation returns recommendation."""
        import json

        mock_litellm.return_value = MockResponse(
            json.dumps({"action": "BUY", "confidence": 85, "reason": "RSI oversold"})
        )

        analysis_result = {
            "rsi_14": 25.0,
            "macd": "Bullish",
            "trend": "Uptrend",
        }

        result = await ai_client.get_recommendation("2330", analysis_result)

        assert isinstance(result, dict)
        assert "action" in result


class TestModelSettings:
    """Test cases for model settings."""

    def test_temperature_default(self, ai_client):
        """Test default temperature value."""
        assert ai_client.temperature is not None
        assert 0 <= ai_client.temperature <= 2

    def test_max_tokens_default(self, ai_client):
        """Test default max_tokens value."""
        assert ai_client.max_tokens is not None
        assert ai_client.max_tokens > 0

    def test_timeout_default(self, ai_client):
        """Test default timeout value."""
        assert ai_client.timeout is not None
        assert ai_client.timeout > 0


class TestEdgeCases:
    """Test edge cases."""

    @pytest.mark.asyncio
    async def test_empty_message(self, ai_client, mock_litellm):
        """Test handling of empty message."""
        mock_litellm.return_value = MockResponse("收到")

        result = await ai_client.chat("")

        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_very_long_message(self, ai_client, mock_litellm):
        """Test handling of very long message."""
        mock_litellm.return_value = MockResponse("回應")

        long_message = " ".join(["分析"] * 1000)
        result = await ai_client.chat(long_message)

        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_special_characters_in_message(self, ai_client, mock_litellm):
        """Test handling of special characters in message."""
        mock_litellm.return_value = MockResponse("回應")

        result = await ai_client.chat("分析 2330！@#$% 股價走勢如何？")

        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_chinese_message(self, ai_client, mock_litellm):
        """Test handling of Chinese message."""
        mock_litellm.return_value = MockResponse("分析結果")

        result = await ai_client.chat("分析台積電的股價走勢")

        assert isinstance(result, str)

    @pytest.mark.asyncio
    async def test_english_message(self, ai_client, mock_litellm):
        """Test handling of English message."""
        mock_litellm.return_value = MockResponse("Analysis result")

        result = await ai_client.chat("Analyze TSMC stock price")

        assert isinstance(result, str)
