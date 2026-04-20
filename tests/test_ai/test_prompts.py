"""Tests for AI prompt templates."""

from pulse.ai.prompts import CHAT_SYSTEM_PROMPT, StockAnalysisPrompts


class TestChatSystemPrompt:
    """Test the general chat system prompt."""

    def test_forces_traditional_chinese(self):
        assert "所有回覆一律使用繁體中文" in CHAT_SYSTEM_PROMPT

    def test_scopes_to_taiwan_stock_analysis(self):
        assert "只回答與台灣股市、投資、交易相關的內容" in CHAT_SYSTEM_PROMPT


class TestStockAnalysisPrompts:
    """Test stock analysis prompt templates."""

    def test_system_base_contains_data_rules(self):
        prompt = StockAnalysisPrompts.get_system_base()

        assert "必須使用繁體中文回答" in prompt
        assert "資料不足" in prompt
        assert "不要自行補齊" in prompt
        assert "不要把猜測當作事實" in prompt

    def test_comprehensive_prompt_is_structured(self):
        prompt = StockAnalysisPrompts.get_comprehensive_prompt()

        assert "核心摘要" in prompt
        assert "資料完整度與可信度" in prompt
        assert "情境推演" in prompt
        assert "綜合操作建議" in prompt
        assert "資料不足" in prompt

    def test_technical_prompt_has_clear_sections(self):
        prompt = StockAnalysisPrompts.get_technical_prompt()

        assert "趨勢判讀" in prompt
        assert "動能判讀" in prompt
        assert "支撐與壓力" in prompt
        assert "風險報酬比" in prompt

    def test_fundamental_prompt_has_clear_sections(self):
        prompt = StockAnalysisPrompts.get_fundamental_prompt()

        assert "估值" in prompt
        assert "獲利能力" in prompt
        assert "財務健康" in prompt
        assert "內在價值" in prompt

    def test_broker_flow_prompt_has_clear_sections(self):
        prompt = StockAnalysisPrompts.get_broker_flow_prompt()

        assert "外資動向" in prompt
        assert "投信動向" in prompt
        assert "自營商動向" in prompt
        assert "風險提醒" in prompt

    def test_recommendation_prompt_requires_json(self):
        prompt = StockAnalysisPrompts.get_recommendation_prompt()

        assert "唯一一個有效 JSON" in prompt
        assert '"signal"' in prompt
        assert "summary、key_reasons、risks 必須是繁體中文" in prompt

    def test_screening_prompt_has_limits(self):
        prompt = StockAnalysisPrompts.get_screening_prompt()

        assert "股票篩選" in prompt
        assert "資料不足" in prompt
        assert "風險" in prompt

    def test_format_analysis_request_is_localized(self):
        prompt = StockAnalysisPrompts.format_analysis_request("2330", {"price": 100})

        assert "請分析股票 2330" in prompt
        assert "```json" in prompt
        assert "不要自行補數字" in prompt

    def test_format_comparison_request_is_localized(self):
        prompt = StockAnalysisPrompts.format_comparison_request(["2330", "2454"], {})

        assert "請比較以下股票：2330, 2454" in prompt
        assert "不要硬選" in prompt

    def test_format_sector_request_is_localized(self):
        prompt = StockAnalysisPrompts.format_sector_request("半導體", {})

        assert "請分析產業類別：半導體" in prompt
        assert "未來展望" in prompt
        assert "直接說明限制" in prompt
