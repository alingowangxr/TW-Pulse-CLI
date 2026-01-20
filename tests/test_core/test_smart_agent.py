"""Tests for SmartAgent - True Agentic Flow for Stock Analysis."""

import pytest
import pandas as pd
import numpy as np
from datetime import datetime
from unittest.mock import MagicMock, AsyncMock, patch
from pathlib import Path

from pulse.core.smart_agent import SmartAgent, AgentContext, AgentResponse


# ============ Fixtures ============


@pytest.fixture
def agent():
    """Create SmartAgent instance for testing."""
    return SmartAgent()


@pytest.fixture
def mock_stock_data():
    """Create mock stock data."""
    return {
        "ticker": "2330",
        "name": "台積電",
        "sector": "半導體",
        "current_price": 820.0,
        "previous_close": 815.0,
        "change": 5.0,
        "change_percent": 0.61,
        "volume": 15234500,
        "avg_volume": 12456000,
        "day_low": 815.0,
        "day_high": 825.0,
        "week_52_high": 850.0,
        "week_52_low": 500.0,
        "market_cap": 5.5e12,
    }


@pytest.fixture
def mock_technical_data():
    """Create mock technical analysis data."""
    return {
        "rsi_14": 58.3,
        "macd": 12.5,
        "macd_signal": 10.3,
        "macd_histogram": 2.2,
        "sma_20": 810.0,
        "sma_50": 800.0,
        "sma_200": 700.0,
        "ema_9": 818.0,
        "ema_21": 812.0,
        "bb_upper": 835.0,
        "bb_middle": 820.0,
        "bb_lower": 805.0,
        "stoch_k": 65.2,
        "stoch_d": 58.5,
        "atr_14": 15.0,
        "support_1": 805.0,
        "resistance_1": 835.0,
        "trend": "Bullish",
        "signal": "Buy",
    }


@pytest.fixture
def mock_fundamental_data():
    """Create mock fundamental data."""
    return {
        "pe_ratio": 25.5,
        "pb_ratio": 6.2,
        "ps_ratio": 12.3,
        "roe": 28.5,
        "roa": 18.2,
        "npm": 38.5,
        "debt_to_equity": 0.35,
        "current_ratio": 2.1,
        "dividend_yield": 1.8,
        "eps": 32.15,
        "bvps": 132.5,
        "revenue_growth": 25.5,
        "earnings_growth": 28.3,
        "market_cap": 5.5e12,
    }


# ============ Test Classes ============


class TestAgentContext:
    """Test cases for AgentContext dataclass."""

    def test_default_context(self):
        """Test creating default context."""
        ctx = AgentContext()
        assert ctx.ticker is None
        assert ctx.tickers == []
        assert ctx.intent == "general"
        assert ctx.stock_data is None
        assert ctx.technical_data is None
        assert ctx.fundamental_data is None
        assert ctx.error is None

    def test_context_with_values(self):
        """Test creating context with values."""
        stock_data = {"price": 820}
        ctx = AgentContext(
            ticker="2330",
            tickers=["2330", "2454"],
            intent="analyze",
            stock_data=stock_data,
        )
        assert ctx.ticker == "2330"
        assert len(ctx.tickers) == 2
        assert ctx.intent == "analyze"
        assert ctx.stock_data["price"] == 820


class TestAgentResponse:
    """Test cases for AgentResponse dataclass."""

    def test_default_response(self):
        """Test creating default response."""
        resp = AgentResponse(message="Hello")
        assert resp.message == "Hello"
        assert resp.context is None
        assert resp.chart is None
        assert resp.raw_data is None

    def test_response_with_all_fields(self):
        """Test creating response with all fields."""
        ctx = AgentContext(ticker="2330")
        resp = AgentResponse(
            message="Analysis complete",
            context=ctx,
            chart="chart.png",
            raw_data={"data": "value"},
        )
        assert resp.message == "Analysis complete"
        assert resp.context.ticker == "2330"
        assert resp.chart == "chart.png"
        assert resp.raw_data["data"] == "value"


class TestSmartAgentInitialization:
    """Test cases for SmartAgent initialization."""

    def test_agent_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.ai_client is None
        assert agent._last_ticker is None
        assert agent._last_context is None

    def test_known_tickers_contains_popular_stocks(self, agent):
        """Test known tickers contains major Taiwan stocks."""
        assert "2330" in agent.KNOWN_TICKERS  # 台積電
        assert "2454" in agent.KNOWN_TICKERS  # 聯發科
        assert "2317" in agent.KNOWN_TICKERS  # 鴻海
        assert "2881" in agent.KNOWN_TICKERS  # 富邦金
        assert "2882" in agent.KNOWN_TICKERS  # 國泰金

    def test_ticker_blacklist(self, agent):
        """Test ticker blacklist contains non-ticker numbers."""
        assert "1000" in agent.TICKER_BLACKLIST
        assert "STOP" in agent.TICKER_BLACKLIST
        assert "LOSS" in agent.TICKER_BLACKLIST

    def test_known_indices(self, agent):
        """Test known indices mapping."""
        assert "TAIEX" in agent.KNOWN_INDICES
        assert "TWII" in agent.KNOWN_INDICES
        assert agent.KNOWN_INDICES["TAIEX"] == "^TWII"

    def test_intent_patterns_exist(self, agent):
        """Test intent patterns are defined."""
        assert "analyze" in agent.INTENT_PATTERNS
        assert "technical" in agent.INTENT_PATTERNS
        assert "fundamental" in agent.INTENT_PATTERNS
        assert "screen" in agent.INTENT_PATTERNS
        assert "sapta" in agent.INTENT_PATTERNS


class TestExtractTickers:
    """Test cases for ticker extraction."""

    def test_extract_single_ticker(self, agent):
        """Test extracting single ticker from message."""
        message = "分析 2330 的股價"
        result = agent._extract_tickers(message)
        assert "2330" in result

    def test_extract_multiple_tickers(self, agent):
        """Test extracting multiple tickers."""
        message = "比較 2330 和 2454 以及 2317"
        result = agent._extract_tickers(message)
        assert "2330" in result
        assert "2454" in result
        assert "2317" in result

    def test_extract_ticker_with_spaces(self, agent):
        """Test extracting ticker with spaces around it."""
        message = "分析  2330  的情況"
        result = agent._extract_tickers(message)
        assert "2330" in result

    def test_known_ticker_detection(self, agent):
        """Test known tickers are detected when explicitly mentioned."""
        message = "2330 今天表現如何"  # Ticker is in the message
        result = agent._extract_tickers(message)
        assert "2330" in result

    def test_no_tickers_in_message(self, agent):
        """Test message without tickers."""
        message = "今天大盤怎麼樣"
        result = agent._extract_tickers(message)
        assert result == []

    def test_blacklisted_words_not_extracted(self, agent):
        """Test blacklisted words are not extracted as tickers."""
        message = "請設定 stop loss 在 1000"
        result = agent._extract_tickers(message)
        assert "1000" not in result

    def test_returns_unique_tickers(self, agent):
        """Test duplicate tickers are removed."""
        message = "2330 和 2330 哪個好"
        result = agent._extract_tickers(message)
        assert len(result) == 1
        assert "2330" in result

    def test_extract_6_digit_ticker(self, agent):
        """Test extracting 6-digit OTC ticker."""
        message = "分析 641509 的股價"
        result = agent._extract_tickers(message)
        # 6-digit numbers should be valid tickers
        assert "641509" in result


class TestIsValidTicker:
    """Test cases for ticker validation."""

    def test_known_ticker_valid(self, agent):
        """Test known tickers are valid."""
        assert agent._is_valid_ticker("2330") is True

    def test_blacklisted_ticker_invalid(self, agent):
        """Test blacklisted tickers are invalid."""
        assert agent._is_valid_ticker("STOP") is False
        assert agent._is_valid_ticker("1000") is False

    def test_4_digit_number_valid(self, agent):
        """Test 4-digit numbers are valid tickers."""
        assert agent._is_valid_ticker("1234") is True
        assert agent._is_valid_ticker("9999") is True

    def test_5_digit_number_valid(self, agent):
        """Test 5-digit numbers are valid tickers."""
        assert agent._is_valid_ticker("12345") is True

    def test_6_digit_number_valid(self, agent):
        """Test 6-digit numbers are valid tickers."""
        assert agent._is_valid_ticker("123456") is True

    def test_3_digit_number_invalid(self, agent):
        """Test 3-digit numbers are invalid tickers."""
        assert agent._is_valid_ticker("123") is False

    def test_alpha_ticker_invalid(self, agent):
        """Test alphabetic strings are invalid tickers."""
        assert agent._is_valid_ticker("ABC") is False
        assert agent._is_valid_ticker("TEST") is False

    def test_mixed_ticker_invalid(self, agent):
        """Test mixed alphanumeric strings are invalid."""
        assert agent._is_valid_ticker("2330A") is False


class TestDetectIntent:
    """Test cases for intent detection."""

    # ============ Analyze Intent ============

    def test_detect_analyze_tw(self, agent):
        """Test detecting analyze intent in Chinese."""
        intent, tickers = agent._detect_intent("分析 2330")
        assert intent == "analyze"
        assert "2330" in tickers

    def test_detect_analyze_en(self, agent):
        """Test detecting analyze intent in English."""
        intent, tickers = agent._detect_intent("analyze 2330")
        assert intent == "analyze"
        assert "2330" in tickers

    def test_detect_review(self, agent):
        """Test detecting review intent."""
        intent, tickers = agent._detect_intent("review 2454")
        assert intent == "analyze"
        assert "2454" in tickers

    # ============ Technical Intent ============

    def test_detect_technical_tw(self, agent):
        """Test detecting technical intent in Chinese."""
        intent, tickers = agent._detect_intent("技術面 2330")
        assert intent == "technical"
        assert "2330" in tickers

    def test_detect_technical_en(self, agent):
        """Test detecting technical intent in English."""
        intent, tickers = agent._detect_intent("technical 2330")
        assert intent == "technical"
        assert "2330" in tickers

    def test_detect_rsi(self, agent):
        """Test detecting RSI intent."""
        intent, tickers = agent._detect_intent("rsi 2330")
        assert intent == "technical"
        assert "2330" in tickers

    def test_detect_macd(self, agent):
        """Test detecting MACD intent."""
        intent, tickers = agent._detect_intent("macd 2330")
        assert intent == "technical"
        assert "2330" in tickers

    # ============ Fundamental Intent ============

    def test_detect_fundamental_tw(self, agent):
        """Test detecting fundamental intent in Chinese."""
        intent, tickers = agent._detect_intent("基本面 2330")
        assert intent == "fundamental"
        assert "2330" in tickers

    def test_detect_fundamental_en(self, agent):
        """Test detecting fundamental intent in English."""
        intent, tickers = agent._detect_intent("fundamental 2330")
        assert intent == "fundamental"
        assert "2330" in tickers

    def test_detect_pe(self, agent):
        """Test detecting PE intent."""
        intent, tickers = agent._detect_intent("pe 2330")
        assert intent == "fundamental"
        assert "2330" in tickers

    # ============ Screen Intent ============

    def test_detect_screen_oversold(self, agent):
        """Test detecting screen oversold intent."""
        intent, tickers = agent._detect_intent("找超賣的股票")
        assert intent == "screen"
        assert tickers == []

    def test_detect_screen_bullish(self, agent):
        """Test detecting screen bullish intent."""
        intent, tickers = agent._detect_intent("找多頭股票")
        assert intent == "screen"

    def test_detect_screen_en(self, agent):
        """Test detecting screen in English."""
        intent, tickers = agent._detect_intent("screen oversold")
        assert intent == "screen"

    def test_detect_screen_rsi_criteria(self, agent):
        """Test detecting screen with RSI criteria."""
        intent, tickers = agent._detect_intent("rsi<30 的股票")
        assert intent == "screen"

    def test_detect_screen_pe_criteria(self, agent):
        """Test detecting screen with PE criteria."""
        intent, tickers = agent._detect_intent("pe<15")
        assert intent == "screen"

    # ============ Compare Intent ============

    def test_detect_compare_tw(self, agent):
        """Test detecting compare intent in Chinese."""
        intent, tickers = agent._detect_intent("比較 2330 和 2454")
        assert intent == "compare"
        assert "2330" in tickers
        assert "2454" in tickers

    def test_detect_compare_en(self, agent):
        """Test detecting compare intent in English."""
        intent, tickers = agent._detect_intent("2330 vs 2454")
        assert intent == "compare"
        assert "2330" in tickers
        assert "2454" in tickers

    # ============ SAPTA Intent ============

    def test_detect_sapta(self, agent):
        """Test detecting SAPTA intent."""
        intent, tickers = agent._detect_intent("sapta 2330")
        assert intent == "sapta"
        assert "2330" in tickers

    def test_detect_sapta_premarkup(self, agent):
        """Test detecting pre-markup intent."""
        intent, tickers = agent._detect_intent("預漲 2330")
        assert intent == "sapta"
        assert "2330" in tickers

    def test_detect_sapta_scan(self, agent):
        """Test detecting SAPTA scan intent."""
        intent, tickers = agent._detect_intent("找預漲股票")
        assert intent == "sapta_scan"
        assert tickers == []

    def test_detect_sapta_breakout(self, agent):
        """Test detecting breakout intent."""
        intent, tickers = agent._detect_intent("準備突破 2330")
        assert intent == "sapta"
        assert "2330" in tickers

    # ============ Trading Plan Intent ============

    def test_detect_trading_plan_tw(self, agent):
        """Test detecting trading plan intent in Chinese."""
        intent, tickers = agent._detect_intent("交易計畫 2330")
        assert intent == "trading_plan"
        assert "2330" in tickers

    def test_detect_trading_plan_en(self, agent):
        """Test detecting trading plan intent in English."""
        intent, tickers = agent._detect_intent("trading plan 2330")
        assert intent == "trading_plan"
        assert "2330" in tickers

    def test_detect_stop_loss(self, agent):
        """Test detecting stop loss intent."""
        intent, tickers = agent._detect_intent("停損 2330")
        assert intent == "trading_plan"
        assert "2330" in tickers

    def test_detect_risk_reward(self, agent):
        """Test detecting risk/reward intent."""
        intent, tickers = agent._detect_intent("rr 2330")
        assert intent == "trading_plan"
        assert "2330" in tickers

    # ============ Index Intent ============

    def test_detect_index_taiex(self, agent):
        """Test detecting TAIEX index intent."""
        intent, tickers = agent._detect_intent("大盤怎麼樣")
        assert intent == "index"
        assert "TAIEX" in tickers

    def test_detect_index_twii(self, agent):
        """Test detecting TWII index intent."""
        intent, tickers = agent._detect_intent("TWII 現在幾點")
        assert intent == "index"
        assert "TWII" in tickers

    def test_detect_index_market(self, agent):
        """Test detecting market intent."""
        intent, tickers = agent._detect_intent("今天市場狀況如何")
        assert intent == "index"

    # ============ Chart Intent ============

    def test_detect_chart_tw(self, agent):
        """Test detecting chart intent in Chinese."""
        intent, tickers = agent._detect_intent("圖表 2330")
        assert intent == "chart"
        assert "2330" in tickers

    def test_detect_chart_en(self, agent):
        """Test detecting chart intent in English."""
        intent, tickers = agent._detect_intent("chart 2330")
        assert intent == "chart"
        assert "2330" in tickers

    def test_detect_graph(self, agent):
        """Test detecting graph intent."""
        intent, tickers = agent._detect_intent("graph 2330")
        assert intent == "chart"
        assert "2330" in tickers

    # ============ Forecast Intent ============

    def test_detect_forecast_tw(self, agent):
        """Test detecting forecast intent in Chinese."""
        intent, tickers = agent._detect_intent("預測 2330")
        assert intent == "forecast"
        assert "2330" in tickers

    def test_detect_forecast_en(self, agent):
        """Test detecting forecast intent in English."""
        intent, tickers = agent._detect_intent("forecast 2330")
        assert intent == "forecast"
        assert "2330" in tickers

    def test_detect_target(self, agent):
        """Test detecting target intent."""
        intent, tickers = agent._detect_intent("target 2330")
        assert intent == "forecast"
        assert "2330" in tickers

    # ============ General Intent ============

    def test_detect_general_with_tickers(self, agent):
        """Test general intent with unknown pattern but with tickers."""
        intent, tickers = agent._detect_intent("幫我查 2330")
        assert intent == "analyze"
        assert "2330" in tickers

    def test_detect_general_without_tickers(self, agent):
        """Test general intent without tickers falls back to general."""
        intent, tickers = agent._detect_intent("你好")
        assert intent == "general"
        assert tickers == []


class TestBuildAnalysisPrompt:
    """Test cases for prompt building."""

    def test_prompt_with_stock_data(self, agent, mock_stock_data):
        """Test building prompt with stock data."""
        ctx = AgentContext(ticker="2330", intent="analyze", stock_data=mock_stock_data)
        prompt = agent._build_analysis_prompt("分析這檔股票", ctx)

        assert "2330" in prompt
        assert "台積電" in prompt or "ticker" in prompt.lower()
        assert "820" in prompt or "820" in prompt
        assert "你是專業的台灣股市分析師" in prompt

    def test_prompt_with_technical_data(self, agent, mock_stock_data, mock_technical_data):
        """Test building prompt with technical data."""
        ctx = AgentContext(
            ticker="2330",
            intent="analyze",
            stock_data=mock_stock_data,
            technical_data=mock_technical_data,
        )
        prompt = agent._build_analysis_prompt("技術面如何", ctx)

        assert "技術指標" in prompt
        assert "RSI" in prompt
        assert "MACD" in prompt

    def test_prompt_with_fundamental_data(self, agent, mock_stock_data, mock_fundamental_data):
        """Test building prompt with fundamental data."""
        ctx = AgentContext(
            ticker="2330",
            intent="analyze",
            stock_data=mock_stock_data,
            fundamental_data=mock_fundamental_data,
        )
        prompt = agent._build_analysis_prompt("基本面如何", ctx)

        assert "基本面數據" in prompt
        assert "本益比" in prompt
        assert "25.5" in prompt

    def test_prompt_with_comparison_data(self, agent, mock_stock_data):
        """Test building prompt with comparison data."""
        ctx = AgentContext(
            ticker="2330",
            intent="compare",
            stock_data=mock_stock_data,
            comparison_data=[
                {"ticker": "2330", "current_price": 820, "change_percent": 0.61},
                {"ticker": "2454", "current_price": 750, "change_percent": 1.2},
            ],
        )
        prompt = agent._build_analysis_prompt("比較這兩檔", ctx)

        assert "股票比較" in prompt
        assert "2330" in prompt
        assert "2454" in prompt

    def test_prompt_includes_user_question(self, agent):
        """Test that user question is included in prompt."""
        ctx = AgentContext(ticker="2330", intent="analyze")
        prompt = agent._build_analysis_prompt("這檔股票可以買嗎？", ctx)

        assert "這檔股票可以買嗎" in prompt

    def test_prompt_empty_context(self, agent):
        """Test building prompt with empty context."""
        ctx = AgentContext(intent="general")
        prompt = agent._build_analysis_prompt("你好", ctx)

        assert "你是專業的台灣股市分析師" in prompt
        assert "以下是從市場取得的真實數據" in prompt

    def test_prompt_contains_all_data_types(
        self, agent, mock_stock_data, mock_technical_data, mock_fundamental_data
    ):
        """Test prompt contains all data types when available."""
        ctx = AgentContext(
            ticker="2330",
            intent="analyze",
            stock_data=mock_stock_data,
            technical_data=mock_technical_data,
            fundamental_data=mock_fundamental_data,
        )
        prompt = agent._build_analysis_prompt("完整分析", ctx)

        # All sections should be present
        assert "股票數據" in prompt
        assert "技術指標" in prompt
        assert "基本面數據" in prompt

    def test_prompt_market_cap_formatting(self, agent, mock_stock_data):
        """Test market cap is formatted correctly (trillion/billion)."""
        # Test with large market cap (trillion)
        mock_stock_data["market_cap"] = 5.5e12
        ctx = AgentContext(ticker="2330", intent="analyze", stock_data=mock_stock_data)
        prompt = agent._build_analysis_prompt("分析", ctx)

        assert "兆" in prompt or "5.5" in prompt

        # Test with medium market cap (billion)
        mock_stock_data["market_cap"] = 5.5e9
        ctx = AgentContext(ticker="2330", intent="analyze", stock_data=mock_stock_data)
        prompt = agent._build_analysis_prompt("分析", ctx)

        assert "億" in prompt or "5.5" in prompt


class TestFetchStockData:
    """Test cases for stock data fetching."""

    @pytest.mark.asyncio
    async def test_fetch_stock_data_success(self, agent):
        """Test successful stock data fetching."""
        mock_stock = MagicMock()
        mock_stock.ticker = "2330"
        mock_stock.name = "台積電"
        mock_stock.sector = "半導體"
        mock_stock.current_price = 820.0
        mock_stock.previous_close = 815.0
        mock_stock.change = 5.0
        mock_stock.change_percent = 0.61
        mock_stock.volume = 15234500
        mock_stock.avg_volume = 12456000
        mock_stock.day_high = 825.0
        mock_stock.day_low = 815.0
        mock_stock.week_52_high = 850.0
        mock_stock.week_52_low = 500.0
        mock_stock.market_cap = 5.5e12

        with patch("pulse.core.data.yfinance.YFinanceFetcher") as MockFetcher:
            mock_fetcher = MagicMock()
            mock_fetcher.fetch_stock = AsyncMock(return_value=mock_stock)
            MockFetcher.return_value = mock_fetcher

            result = await agent._fetch_stock_data("2330")

        assert result is not None
        assert result["ticker"] == "2330"
        assert result["current_price"] == 820.0
        assert result["name"] == "台積電"

    @pytest.mark.asyncio
    async def test_fetch_stock_data_failure(self, agent):
        """Test failed stock data fetching."""
        with patch("pulse.core.data.yfinance.YFinanceFetcher") as MockFetcher:
            mock_fetcher = MockFetcher.return_value
            mock_fetcher.fetch_stock = AsyncMock(return_value=None)

            result = await agent._fetch_stock_data("INVALID")

        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_stock_data_exception(self, agent):
        """Test stock data fetching with exception."""
        with patch("pulse.core.data.yfinance.YFinanceFetcher") as MockFetcher:
            mock_fetcher = MockFetcher.return_value
            mock_fetcher.fetch_stock = AsyncMock(side_effect=Exception("API error"))

            result = await agent._fetch_stock_data("2330")

        assert result is None


class TestFetchTechnical:
    """Test cases for technical data fetching."""

    @pytest.mark.asyncio
    async def test_fetch_technical_success(self, agent):
        """Test successful technical data fetching."""
        mock_indicators = MagicMock()
        mock_indicators.rsi_14 = 58.3
        mock_indicators.macd = 12.5
        mock_indicators.macd_signal = 10.3
        mock_indicators.macd_histogram = 2.2
        mock_indicators.sma_20 = 810.0
        mock_indicators.sma_50 = 800.0
        mock_indicators.sma_200 = 700.0
        mock_indicators.ema_9 = 818.0
        mock_indicators.ema_21 = 812.0
        mock_indicators.bb_upper = 835.0
        mock_indicators.bb_middle = 820.0
        mock_indicators.bb_lower = 805.0
        mock_indicators.stoch_k = 65.2
        mock_indicators.stoch_d = 58.5
        mock_indicators.atr_14 = 15.0
        mock_indicators.support_1 = 805.0
        mock_indicators.resistance_1 = 835.0
        mock_indicators.trend = MagicMock(value="Bullish")
        mock_indicators.signal = MagicMock(value="Buy")

        with patch("pulse.core.analysis.technical.TechnicalAnalyzer") as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_analyzer.analyze = AsyncMock(return_value=mock_indicators)

            result = await agent._fetch_technical("2330")

        assert result is not None
        assert result["rsi_14"] == 58.3
        assert result["macd"] == 12.5

    @pytest.mark.asyncio
    async def test_fetch_technical_failure(self, agent):
        """Test failed technical data fetching."""
        with patch("pulse.core.analysis.technical.TechnicalAnalyzer") as MockAnalyzer:
            mock_analyzer = MockAnalyzer.return_value
            mock_analyzer.analyze = AsyncMock(return_value=None)

            result = await agent._fetch_technical("INVALID")

        assert result is None


class TestFetchFundamental:
    """Test cases for fundamental data fetching."""

    @pytest.mark.asyncio
    async def test_fetch_fundamental_success(self, agent):
        """Test successful fundamental data fetching."""
        mock_fund = MagicMock()
        mock_fund.pe_ratio = 25.5
        mock_fund.pb_ratio = 6.2
        mock_fund.ps_ratio = 12.3
        mock_fund.roe = 28.5
        mock_fund.roa = 18.2
        mock_fund.npm = 38.5
        mock_fund.debt_to_equity = 0.35
        mock_fund.current_ratio = 2.1
        mock_fund.dividend_yield = 1.8
        mock_fund.eps = 32.15
        mock_fund.bvps = 132.5
        mock_fund.revenue_growth = 25.5
        mock_fund.earnings_growth = 28.3
        mock_fund.market_cap = 5.5e12

        with patch("pulse.core.data.yfinance.YFinanceFetcher") as MockFetcher:
            mock_fetcher = MockFetcher.return_value
            mock_fetcher.fetch_fundamentals = AsyncMock(return_value=mock_fund)

            result = await agent._fetch_fundamental("2330")

        assert result is not None
        assert result["pe_ratio"] == 25.5
        assert result["roe"] == 28.5

    @pytest.mark.asyncio
    async def test_fetch_fundamental_failure(self, agent):
        """Test failed fundamental data fetching."""
        with patch("pulse.core.data.yfinance.YFinanceFetcher") as MockFetcher:
            mock_fetcher = MockFetcher.return_value
            mock_fetcher.fetch_fundamentals = AsyncMock(return_value=None)

            result = await agent._fetch_fundamental("INVALID")

        assert result is None


class TestGatherContext:
    """Test cases for context gathering."""

    @pytest.mark.asyncio
    async def test_gather_context_no_tickers(self, agent):
        """Test gathering context with no tickers."""
        ctx = await agent._gather_context("screen", [])
        assert ctx.ticker is None
        assert ctx.intent == "screen"

    @pytest.mark.asyncio
    async def test_gather_context_analyze_intent(
        self, agent, mock_stock_data, mock_technical_data, mock_fundamental_data
    ):
        """Test gathering context for analyze intent."""
        with (
            patch.object(agent, "_fetch_stock_data", new_callable=AsyncMock) as mock_stock,
            patch.object(agent, "_fetch_technical", new_callable=AsyncMock) as mock_tech,
            patch.object(agent, "_fetch_fundamental", new_callable=AsyncMock) as mock_fund,
        ):
            mock_stock.return_value = mock_stock_data
            mock_tech.return_value = mock_technical_data
            mock_fund.return_value = mock_fundamental_data

            ctx = await agent._gather_context("analyze", ["2330"])

        assert ctx.ticker == "2330"
        assert ctx.stock_data is not None
        assert ctx.technical_data is not None
        assert ctx.fundamental_data is not None

    @pytest.mark.asyncio
    async def test_gather_context_technical_only(self, agent, mock_stock_data, mock_technical_data):
        """Test gathering context for technical intent."""
        with (
            patch.object(agent, "_fetch_stock_data", new_callable=AsyncMock) as mock_stock,
            patch.object(agent, "_fetch_technical", new_callable=AsyncMock) as mock_tech,
        ):
            mock_stock.return_value = mock_stock_data
            mock_tech.return_value = mock_technical_data

            ctx = await agent._gather_context("technical", ["2330"])

        assert ctx.stock_data is not None
        assert ctx.technical_data is not None
        assert ctx.fundamental_data is None  # Not needed for technical

    @pytest.mark.asyncio
    async def test_gather_context_fundamental_only(
        self, agent, mock_stock_data, mock_fundamental_data
    ):
        """Test gathering context for fundamental intent."""
        with (
            patch.object(agent, "_fetch_stock_data", new_callable=AsyncMock) as mock_stock,
            patch.object(agent, "_fetch_fundamental", new_callable=AsyncMock) as mock_fund,
        ):
            mock_stock.return_value = mock_stock_data
            mock_fund.return_value = mock_fundamental_data

            ctx = await agent._gather_context("fundamental", ["2330"])

        assert ctx.stock_data is not None
        assert ctx.technical_data is None  # Not needed for fundamental
        assert ctx.fundamental_data is not None

    @pytest.mark.asyncio
    async def test_gather_context_compare_multiple(self, agent, mock_stock_data):
        """Test gathering context for compare intent with multiple tickers."""
        with patch.object(agent, "_fetch_stock_data", new_callable=AsyncMock) as mock_stock:
            mock_stock.return_value = mock_stock_data

            ctx = await agent._gather_context("compare", ["2330", "2454", "2303"])

        assert ctx.ticker == "2330"
        assert ctx.comparison_data is not None
        assert len(ctx.comparison_data) == 3

    @pytest.mark.asyncio
    async def test_gather_context_error_handling(self, agent):
        """Test error handling when fetching stock data fails."""
        with patch.object(agent, "_fetch_stock_data", new_callable=AsyncMock) as mock_stock:
            mock_stock.return_value = None

            ctx = await agent._gather_context("analyze", ["INVALID"])

        assert ctx.error is not None


class TestRunMethod:
    """Test cases for the main run method."""

    @pytest.mark.asyncio
    async def test_run_analyze_intent(
        self, agent, mock_stock_data, mock_technical_data, mock_fundamental_data
    ):
        """Test running analyze intent."""
        with (
            patch.object(agent, "_gather_context", new_callable=AsyncMock) as mock_gather,
            patch.object(agent, "_get_ai_client") as mock_get_client,
        ):
            # Setup mock context
            mock_ctx = AgentContext(
                ticker="2330",
                intent="analyze",
                stock_data=mock_stock_data,
                technical_data=mock_technical_data,
                fundamental_data=mock_fundamental_data,
            )
            mock_gather.return_value = mock_ctx

            # Setup mock AI client
            mock_client = MagicMock()
            mock_client.chat = AsyncMock(return_value="分析結果")
            mock_get_client.return_value = mock_client

            with patch.object(agent, "_generate_chart", new_callable=AsyncMock) as mock_chart:
                mock_chart.return_value = None

                response = await agent.run("分析 2330")

        assert isinstance(response, AgentResponse)
        assert response.message == "分析結果"
        assert response.context is not None
        assert response.context.ticker == "2330"

    @pytest.mark.asyncio
    async def test_run_screen_intent(self, agent):
        """Test running screen intent."""
        with patch.object(agent, "_handle_screen", new_callable=AsyncMock) as mock_screen:
            mock_screen.return_value = AgentResponse(message="篩選結果")

            response = await agent.run("找超賣股票")

        assert response.message == "篩選結果"

    @pytest.mark.asyncio
    async def test_run_sapta_intent(self, agent):
        """Test running SAPTA intent."""
        with patch.object(agent, "_handle_sapta", new_callable=AsyncMock) as mock_sapta:
            mock_sapta.return_value = AgentResponse(message="SAPTA 分析結果")

            response = await agent.run("sapta 2330")

        assert response.message == "SAPTA 分析結果"

    @pytest.mark.asyncio
    async def test_run_sapta_scan_intent(self, agent):
        """Test running SAPTA scan intent."""
        with patch.object(agent, "_handle_sapta_scan", new_callable=AsyncMock) as mock_scan:
            mock_scan.return_value = AgentResponse(message="掃描完成")

            response = await agent.run("找預漲股票")

        assert response.message == "掃描完成"

    @pytest.mark.asyncio
    async def test_run_trading_plan_intent(self, agent):
        """Test running trading plan intent."""
        with patch.object(agent, "_handle_trading_plan", new_callable=AsyncMock) as mock_plan:
            mock_plan.return_value = AgentResponse(message="交易計畫")

            response = await agent.run("交易計畫 2330")

        assert response.message == "交易計畫"

    @pytest.mark.asyncio
    async def test_run_general_intent_without_tickers(self, agent):
        """Test running general intent without tickers."""
        with patch.object(agent, "_get_ai_client") as mock_get_client:
            mock_client = MagicMock()
            mock_client.chat = AsyncMock(return_value="你好，我是 Pulse")
            mock_get_client.return_value = mock_client

            response = await agent.run("你好")

        assert response.message == "你好，我是 Pulse"

    @pytest.mark.asyncio
    async def test_run_remembers_last_ticker(self, agent, mock_stock_data):
        """Test that agent remembers last ticker for follow-ups."""
        with (
            patch.object(agent, "_gather_context", new_callable=AsyncMock) as mock_gather,
            patch.object(agent, "_get_ai_client") as mock_get_client,
        ):
            mock_ctx = AgentContext(ticker="2330", intent="analyze", stock_data=mock_stock_data)
            mock_gather.return_value = mock_ctx

            mock_client = MagicMock()
            mock_client.chat = AsyncMock(return_value="分析結果")
            mock_get_client.return_value = mock_client

            with patch.object(agent, "_generate_chart", new_callable=AsyncMock) as mock_chart:
                mock_chart.return_value = None

                await agent.run("分析 2330")

        # Last ticker should be remembered
        assert agent._last_ticker == "2330"

    @pytest.mark.asyncio
    async def test_run_remembers_ticker_for_followup(self, agent, mock_stock_data):
        """Test that agent remembers ticker for potential follow-ups."""
        with (
            patch.object(agent, "_gather_context", new_callable=AsyncMock) as mock_gather,
            patch.object(agent, "_get_ai_client") as mock_get_client,
        ):
            mock_ctx = AgentContext(ticker="2330", intent="analyze", stock_data=mock_stock_data)
            mock_gather.return_value = mock_ctx

            mock_client = MagicMock()
            mock_client.chat = AsyncMock(return_value="分析結果")
            mock_get_client.return_value = mock_client

            with patch.object(agent, "_generate_chart", new_callable=AsyncMock) as mock_chart:
                mock_chart.return_value = None

                response = await agent.run("分析 2330")

        # Last ticker should be remembered
        assert agent._last_ticker == "2330"
        # Context should be preserved for follow-ups
        assert agent._last_context is not None

    @pytest.mark.asyncio
    async def test_run_context_in_response(self, agent, mock_stock_data):
        """Test that response includes context."""
        with (
            patch.object(agent, "_gather_context", new_callable=AsyncMock) as mock_gather,
            patch.object(agent, "_get_ai_client") as mock_get_client,
        ):
            mock_ctx = AgentContext(ticker="2330", intent="analyze", stock_data=mock_stock_data)
            mock_gather.return_value = mock_ctx

            mock_client = MagicMock()
            mock_client.chat = AsyncMock(return_value="分析結果")
            mock_get_client.return_value = mock_client

            with patch.object(agent, "_generate_chart", new_callable=AsyncMock) as mock_chart:
                mock_chart.return_value = None

                response = await agent.run("分析 2330")

        # Response should include context
        assert response.context is not None
        assert response.context.ticker == "2330"


class TestHandleChart:
    """Test cases for chart generation."""

    @pytest.mark.asyncio
    async def test_handle_chart_success(self, agent, mock_stock_data):
        """Test successful chart generation."""
        with (
            patch.object(agent, "_generate_chart", new_callable=AsyncMock) as mock_chart,
            patch.object(agent, "_fetch_stock_data", new_callable=AsyncMock) as mock_fetch,
        ):
            mock_chart.return_value = "charts/2330_chart.png"
            mock_fetch.return_value = mock_stock_data

            response = await agent.run("chart 2330")

        assert response.chart == "charts/2330_chart.png"
        assert "2330" in response.message

    @pytest.mark.asyncio
    async def test_handle_chart_failure(self, agent, mock_stock_data):
        """Test failed chart generation."""
        with (
            patch.object(agent, "_generate_chart", new_callable=AsyncMock) as mock_chart,
            patch.object(agent, "_fetch_stock_data", new_callable=AsyncMock) as mock_fetch,
            patch.object(agent, "_get_ai_client") as mock_get_client,
        ):
            mock_chart.return_value = None
            mock_fetch.return_value = mock_stock_data  # Return stock data to avoid error path

            # Mock AI client to avoid actual API calls
            mock_client = MagicMock()
            mock_client.chat = AsyncMock(return_value="分析結果")
            mock_get_client.return_value = mock_client

            # With chart intent, _generate_chart returning None should still result in chart=None
            response = await agent.run("chart 2330")

        assert response.chart is None

    @pytest.mark.asyncio
    async def test_handle_chart_intent_returns_error_for_missing_ticker(self, agent):
        """Test chart intent with invalid ticker."""
        with patch.object(agent, "_get_ai_client") as mock_get_client:
            # Mock AI client for general intent fallback
            mock_client = MagicMock()
            mock_client.chat = AsyncMock(return_value="無法生成圖表")
            mock_get_client.return_value = mock_client

            response = await agent.run("chart INVALID")

        # Should fall back to general AI response
        assert response.message is not None


class TestHandleForecast:
    """Test cases for forecast generation."""

    @pytest.mark.asyncio
    async def test_handle_forecast_success(self, agent):
        """Test successful forecast generation."""
        with (
            patch.object(agent, "_generate_forecast", new_callable=AsyncMock) as mock_forecast,
            patch.object(agent, "_get_ai_client") as mock_get_client,
        ):
            mock_forecast.return_value = {
                "summary": "預測結果",
                "filepath": "charts/2330_forecast.png",
            }

            # Mock AI client to avoid actual API calls
            mock_client = MagicMock()
            mock_client.chat = AsyncMock(return_value="AI分析")
            mock_get_client.return_value = mock_client

            response = await agent.run("forecast 2330 14")

        assert response.chart == "charts/2330_forecast.png"
        # The message contains AI response + chart info
        assert response.message is not None
        assert "Chart saved" in response.message or "AI分析" in response.message

    @pytest.mark.asyncio
    async def test_handle_forecast_failure(self, agent, mock_stock_data):
        """Test failed forecast generation falls back to analysis."""
        with (
            patch.object(agent, "_generate_forecast", new_callable=AsyncMock) as mock_forecast,
            patch.object(agent, "_get_ai_client") as mock_get_client,
            patch.object(agent, "_gather_context", new_callable=AsyncMock) as mock_gather,
        ):
            mock_forecast.return_value = None

            # Setup mock context for analysis fallback
            mock_ctx = AgentContext(ticker="2330", intent="forecast", stock_data=mock_stock_data)
            mock_gather.return_value = mock_ctx

            # Mock AI client
            mock_client = MagicMock()
            mock_client.chat = AsyncMock(return_value="分析結果")
            mock_get_client.return_value = mock_client

            response = await agent.run("forecast INVALID 14")

        # Should fall back to analysis
        assert response.message == "分析結果"

        assert response.chart is None


class TestAiClientLazyLoading:
    """Test cases for AI client lazy loading."""

    def test_client_not_loaded_initially(self, agent):
        """Test AI client is not loaded during initialization."""
        assert agent.ai_client is None

    def test_client_loaded_on_first_use(self, agent):
        """Test AI client is loaded on first use."""
        with patch("pulse.ai.client.AIClient") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client

            client = agent._get_ai_client()

        assert MockClient.called
        assert client is not None

    def test_client_reused_on_subsequent_calls(self, agent):
        """Test AI client is reused on subsequent calls."""
        with patch("pulse.ai.client.AIClient") as MockClient:
            mock_client = MagicMock()
            MockClient.return_value = mock_client

            client1 = agent._get_ai_client()
            client2 = agent._get_ai_client()

        # Should only create one instance
        assert MockClient.call_count == 1
        assert client1 is client2
