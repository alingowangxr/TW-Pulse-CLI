"""
SmartAgent - True Agentic Flow for Stock Analysis.

Flow:
1. User message -> Parse intent & extract tickers  (IntentDetector)
2. Fetch REAL data from yfinance                   (ContextBuilder)
3. Run analysis tools (technical, fundamental, etc) (ContextBuilder)
4. Build context with real data                    (ContextBuilder)
5. AI analyzes with full context                   (SmartAgent)
6. Return insight to user

This is NOT a proxy to AI - this is an agent that gathers data first,
then uses AI to analyze and explain the data.
"""

import re
from dataclasses import dataclass, field
from typing import Any

from pulse.core.agent.context_builder import ContextBuilder
from pulse.core.agent.intent_detector import IntentDetector
from pulse.utils.logger import get_logger

log = get_logger(__name__)


@dataclass
class AgentContext:
    """Context built from real data for AI analysis."""

    ticker: str | None = None
    tickers: list[str] = field(default_factory=list)
    intent: str = "general"
    stock_data: dict[str, Any] | None = None
    technical_data: dict[str, Any] | None = None
    fundamental_data: dict[str, Any] | None = None
    historical_prices: list[float] | None = None
    comparison_data: list[dict[str, Any]] | None = None
    error: str | None = None


@dataclass
class AgentResponse:
    """Response from agent execution."""

    message: str
    context: AgentContext | None = None
    chart: str | None = None
    raw_data: dict[str, Any] | None = None


class SmartAgent:
    """
    Smart agent that fetches real data FIRST, then uses AI for analysis.

    This implements true agentic flow:
    User Question -> Data Gathering -> AI Analysis with Context -> Response
    """

    # Patterns that indicate a follow-up question about the last-analysed ticker
    FOLLOWUP_PATTERNS = [
        r"為什麼",
        r"怎麼",
        r"為啥",
        r"為何",
        r"所以",
        r"然後",
        r"可以嗎",
        r"好嗎",
        r"推薦",
        r"應該",
        r"漲",
        r"跌",
        r"可以買",
        r"可以賣",
        r"怎麼看",
        r"你覺得",
        r"後續",
        r"目標",
        r"支撐",
        r"壓力",
        r"看法",
        r"建議",
        r"操作",
    ]

    def __init__(self, progress_callback=None):
        self.ai_client = None  # Lazy load
        self._last_ticker: str | None = None
        self._last_context: AgentContext | None = None
        self._progress_callback = progress_callback
        self._intent_detector = IntentDetector()
        self._context_builder = ContextBuilder()

    # ── Constants delegated from IntentDetector (backward-compat) ────────────

    @property
    def KNOWN_TICKERS(self):
        return self._intent_detector.KNOWN_TICKERS

    @property
    def TICKER_BLACKLIST(self):
        return self._intent_detector.TICKER_BLACKLIST

    @property
    def KNOWN_INDICES(self):
        return self._intent_detector.KNOWN_INDICES

    @property
    def INTENT_PATTERNS(self):
        return self._intent_detector.INTENT_PATTERNS

    def _get_ai_client(self):
        """Get AI client lazily."""
        if self.ai_client is None:
            from pulse.ai.client import AIClient

            self.ai_client = AIClient()
        return self.ai_client

    # ── Delegation helpers ────────────────────────────────────────────────────

    def _detect_intent(self, message: str) -> tuple[str, list[str]]:
        return self._intent_detector.detect_intent(message)

    def _extract_tickers(self, message: str) -> list[str]:
        return self._intent_detector.extract_tickers(message)

    def _is_valid_ticker(self, ticker: str) -> bool:
        return self._intent_detector.is_valid_ticker(ticker)

    async def _fetch_stock_data(self, ticker: str) -> dict[str, Any] | None:
        return await self._context_builder.fetch_stock_data(ticker)

    async def _fetch_technical(self, ticker: str) -> dict[str, Any] | None:
        return await self._context_builder.fetch_technical(ticker)

    async def _fetch_fundamental(self, ticker: str) -> dict[str, Any] | None:
        return await self._context_builder.fetch_fundamental(ticker)

    async def _generate_chart(self, ticker: str, period: str = "3mo") -> str | None:
        return await self._context_builder.generate_chart(ticker, period)

    async def _generate_forecast(
        self, ticker: str, days: int = 7, mode: str = "fast"
    ) -> dict[str, Any] | None:
        return await self._context_builder.generate_forecast(ticker, days, mode)

    async def _gather_context(self, intent: str, tickers: list[str]) -> AgentContext:
        return await self._context_builder.gather_context(intent, tickers, self._progress_callback)

    # ── Prompt builder ────────────────────────────────────────────────────────

    def _build_analysis_prompt(self, user_message: str, context: AgentContext) -> str:
        """Build prompt for AI with real data context."""
        parts = [
            "你是專業的台灣股市分析師，請一律使用繁體中文回覆。",
            "你只能根據下面提供的真實數據、上下文與使用者問題進行分析。",
            "如果資料不足，請直接標示資料不足並說明缺少哪些欄位，不要自行補數字。",
            "事實與推論要分開寫，不要把猜測包裝成已知事實。",
            "輸出結構請固定包含：1. 核心摘要 2. 資料完整度與可信度 3. 技術面與位階 4. 基本面或籌碼面 5. 綜合判斷 6. 風險與追蹤指標。",
            "所有分析都要包含：本分析僅供參考，不構成投資建議。",
            "",
            "以下是從市場取得的真實數據：",
            "",
        ]

        if context.stock_data:
            s = context.stock_data
            change_sign = "+" if s.get("change", 0) >= 0 else ""
            parts.append(f"=== 股票數據: {s.get('ticker')} ===")
            parts.append(f"名稱: {s.get('name', 'N/A')}")
            parts.append(f"產業: {s.get('sector', 'N/A')}")
            parts.append(f"股價: NT$ {s.get('current_price', 0):,.2f}")
            parts.append(
                f"漲跌: {change_sign}{s.get('change', 0):,.2f} ({change_sign}{s.get('change_percent', 0):.2f}%)"
            )
            parts.append(f"成交量: {s.get('volume', 0):,.0f} (均量: {s.get('avg_volume', 0):,.0f})")
            parts.append(f"當日區間: {s.get('day_low', 0):,.2f} - {s.get('day_high', 0):,.2f}")
            parts.append(
                f"52週區間: {s.get('week_52_low', 0):,.2f} - {s.get('week_52_high', 0):,.2f}"
            )
            if s.get("market_cap"):
                mc = s["market_cap"]
                mc_str = f"{mc / 1e12:.1f}兆" if mc >= 1e12 else f"{mc / 1e9:.1f}億"
                parts.append(f"市值: NT$ {mc_str}")
            parts.append("")

        if context.technical_data:
            t = context.technical_data
            parts.append("=== 技術指標 ===")
            if t.get("rsi_14") is not None:
                rsi_status = "超賣" if t["rsi_14"] < 30 else "超買" if t["rsi_14"] > 70 else "中性"
                parts.append(f"RSI(14): {t['rsi_14']:.1f} - {rsi_status}")
            if t.get("macd") is not None:
                macd_status = "多頭" if t["macd"] > t.get("macd_signal", 0) else "空頭"
                parts.append(
                    f"MACD: {t['macd']:.2f} (訊號: {t.get('macd_signal', 0):.2f}) - {macd_status}"
                )
            if t.get("sma_20") is not None:
                parts.append(f"SMA20: {t['sma_20']:,.2f} | SMA50: {t.get('sma_50', 0):,.2f}")
            if t.get("bb_upper") is not None:
                parts.append(
                    f"布林通道: {t['bb_lower']:,.2f} - {t['bb_middle']:,.2f} - {t['bb_upper']:,.2f}"
                )
            if t.get("stoch_k") is not None:
                parts.append(f"隨機指標: K={t['stoch_k']:.1f}, D={t['stoch_d']:.1f}")
            if t.get("support_1") is not None:
                parts.append(f"支撐: {t['support_1']:,.2f} | 壓力: {t.get('resistance_1', 0):,.2f}")
            if t.get("trend"):
                parts.append(f"趨勢: {t['trend']} | 訊號: {t.get('signal', 'N/A')}")
            parts.append("")

        if context.fundamental_data:
            f = context.fundamental_data
            parts.append("=== 基本面數據 ===")
            if f.get("pe_ratio") is not None:
                parts.append(f"本益比: {f['pe_ratio']:.2f}")
            if f.get("pb_ratio") is not None:
                parts.append(f"股價淨值比: {f['pb_ratio']:.2f}")
            if f.get("roe") is not None:
                parts.append(f"股東權益報酬率: {f['roe']:.1f}%")
            if f.get("roa") is not None:
                parts.append(f"資產報酬率: {f['roa']:.1f}%")
            if f.get("npm") is not None:
                parts.append(f"淨利率: {f['npm']:.1f}%")
            if f.get("debt_to_equity") is not None:
                parts.append(f"負債權益比: {f['debt_to_equity']:.2f}")
            if f.get("dividend_yield") is not None:
                parts.append(f"股利殖利率: {f['dividend_yield']:.2f}%")
            if f.get("revenue_growth") is not None:
                parts.append(f"營收成長率: {f['revenue_growth']:.1f}%")
            if f.get("earnings_growth") is not None:
                parts.append(f"獲利成長率: {f['earnings_growth']:.1f}%")
            parts.append("")

        if context.comparison_data:
            parts.append("=== 股票比較 ===")
            parts.append(f"{'代碼':<8} {'股價':>12} {'漲跌':>10}")
            parts.append("-" * 32)
            for stock in context.comparison_data:
                change_str = f"{stock.get('change_percent', 0):+.2f}%"
                parts.append(
                    f"{stock['ticker']:<8} {stock.get('current_price', 0):>12,.2f} {change_str:>10}"
                )
            parts.append("")

        parts.append("=== 使用者問題 ===")
        parts.append(user_message)
        parts.append("")
        parts.append("=== 指示 ===")
        parts.append("根據上述真實數據，提供分析時請：")
        parts.append("1. 依照固定結構輸出，不要跳章節")
        parts.append("2. 使用數據中的實際數字")
        parts.append("3. 提供可執行的洞察")
        parts.append("4. 如被問及建議，請根據數據說明理由")
        parts.append("5. 提及相關的支撐/壓力位")
        parts.append("6. 若資料缺漏，明確標示資料不足")
        parts.append("")
        parts.append("不要捏造數據。僅使用上述提供的數據。")

        return "\n".join(parts)

    # ── Intent handlers ───────────────────────────────────────────────────────

    async def _handle_index(self, index_name: str, user_message: str) -> AgentResponse:
        """Handle market index queries (TAIEX, TW50, etc)."""
        try:
            from pulse.core.chart_generator import ChartGenerator
            from pulse.core.data.yfinance import YFinanceFetcher

            fetcher = YFinanceFetcher()
            index_data = await fetcher.fetch_index(index_name)

            if not index_data:
                return AgentResponse(message=f"無法取得 {index_name} 的資料。")

            df = fetcher.get_history_df(
                f"^{self._intent_detector.KNOWN_INDICES.get(index_name, 'JKSE').replace('^', '')}",
                "3mo",
            )
            chart_path = None

            if df is not None and not df.empty:
                generator = ChartGenerator()
                dates = df.index.strftime("%Y-%m-%d").tolist()
                prices = df["close"].tolist()
                chart_path = generator.price_chart(index_name, dates, prices, period="3mo")

            change_sign = "+" if index_data.change >= 0 else ""
            msg = f"""{index_data.name} ({index_name})

價格：{index_data.current_price:,.2f}
漲跌：{change_sign}{index_data.change:,.2f} ({change_sign}{index_data.change_percent:.2f}%)
區間：{index_data.day_low:,.2f} - {index_data.day_high:,.2f}
52 週區間：{index_data.week_52_low:,.2f} - {index_data.week_52_high:,.2f}"""

            if chart_path:
                msg += f"\n\n圖表已儲存：{chart_path}"

            if any(
                w in user_message.lower()
                for w in ["gimana", "bagaimana", "kondisi", "analisis", "apa"]
            ):
                ai = self._get_ai_client()
                ai_prompt = f"""指數資料 {index_name}：
- 指數：{index_data.current_price:,.2f}
- 漲跌幅：{index_data.change_percent:+.2f}%
- 52 週區間：{index_data.week_52_low:,.2f} - {index_data.week_52_high:,.2f}

使用者問題：「{user_message}」

請用 2 到 3 句話簡短分析 {index_name} 目前的狀態。"""

                ai_response = await ai.chat(
                    ai_prompt,
                    system_prompt="你是資深股市分析師。請以繁體中文簡潔回答，重點明確。",
                    use_history=False,
                )
                msg = f"{ai_response}\n\n---\n\n{msg}"

            return AgentResponse(message=msg, chart=chart_path)

        except Exception as e:
            log.error(f"Error handling index {index_name}: {e}")
            return AgentResponse(message=f"處理 {index_name} 時發生錯誤：{e}")

    async def _handle_screen(self, user_message: str) -> AgentResponse:
        """Handle stock screening request."""
        try:
            from pulse.core.screener import StockScreener, StockUniverse

            msg_lower = user_message.lower()

            if any(kw in msg_lower for kw in ["semua", "all", "955", "seluruh"]):
                screener = StockScreener(universe_type=StockUniverse.ALL)
                universe_note = f"（掃描 {len(screener.universe)} 檔股票）"
            elif any(kw in msg_lower for kw in ["idx80", "80"]):
                screener = StockScreener(universe_type=StockUniverse.IDX80)
                universe_note = "（IDX80）"
            elif any(kw in msg_lower for kw in ["lq45", "lq"]):
                screener = StockScreener(universe_type=StockUniverse.LQ45)
                universe_note = "（LQ45）"
            else:
                screener = StockScreener(universe_type=StockUniverse.POPULAR)
                universe_note = f"（掃描 {len(screener.universe)} 檔股票）"

            results, explanation = await screener.smart_screen(user_message, limit=15)

            if not results:
                return AgentResponse(
                    message=f"找不到符合條件的股票 {universe_note}。\n\n條件說明：{explanation}"
                )

            formatted = screener.format_results(
                results,
                title=f"股票篩選結果 {universe_note}",
                show_details=True,
            )

            msg = f"{explanation}\n\n{formatted}"

            ai = self._get_ai_client()
            top_picks = []
            for r in results[:5]:
                rsi_str = f"{r.rsi_14:.1f}" if r.rsi_14 is not None else "無"
                mc_str = ""
                if hasattr(r, "market_cap") and r.market_cap:
                    mc = r.market_cap
                    mc_str = f", 市值: {mc / 1e12:.1f} 兆" if mc >= 1e12 else f", 市值: {mc / 1e9:.0f} 億"
                top_picks.append(
                    f"- {r.ticker}：NT$ {r.price:,.0f} ({r.change_percent:+.2f}%), "
                    f"RSI：{rsi_str}, 分數：{r.score:.0f}{mc_str}"
                )

            ai_prompt = f"""使用者問題：「{user_message}」

篩選結果說明：{explanation}

前五檔候選股票：
{chr(10).join(top_picks)}

請用 2 到 3 句話簡短總結這次篩選結果。
並說明哪一檔最值得關注，以及原因。"""

            ai_summary = await ai.chat(
                ai_prompt,
                system_prompt="你是資深股市分析師。請以繁體中文簡短總結選股結果，並說明重點。",
                use_history=False,
            )
            msg = f"{ai_summary}\n\n---\n\n{formatted}"

            return AgentResponse(message=msg)

        except Exception as e:
            log.error(f"Screen error: {e}")
            return AgentResponse(message=f"選股篩選時發生錯誤：{e}")

    async def _handle_trading_plan(self, ticker: str, user_message: str) -> AgentResponse:
        """Generate trading plan with TP, SL, and Risk/Reward for a ticker."""
        try:
            from pulse.core.trading_plan import TradingPlanGenerator

            self._last_ticker = ticker

            generator = TradingPlanGenerator()
            plan = await generator.generate(ticker)

            if not plan:
                return AgentResponse(
                    message=f"無法為 {ticker} 產生交易計畫，請確認代號是否正確。"
                )

            formatted = generator.format_plan(plan)

            ai = self._get_ai_client()
            ai_prompt = f"""交易計畫 {ticker}：
進場價：NT$ {plan.entry_price:,.0f}
第一目標價：NT$ {plan.tp1:,.0f} ({plan.tp1_percent:+.2f}%)
停損：NT$ {plan.stop_loss:,.0f} ({plan.stop_loss_percent:.2f}%)
風報比：1:{plan.rr_ratio_tp1:.1f}
交易品質：{plan.trade_quality.value}
趨勢：{plan.trend.value}
訊號：{plan.signal.value}
RSI：{plan.rsi}
信心度：{plan.confidence}%

使用者問題：「{user_message}」

請用 2 到 3 句話簡短評論這份交易計畫。
說明是否適合執行，以及需要注意什麼。"""

            ai_comment = await ai.chat(
                ai_prompt,
                system_prompt=(
                    "你是專業交易員。請以繁體中文提供簡短、可執行的交易建議，聚焦風險與可行性。"
                ),
                use_history=False,
            )

            msg = f"{ai_comment}\n\n---\n\n{formatted}"

            return AgentResponse(
                message=msg,
                raw_data={"trading_plan": plan.model_dump()},
            )

        except Exception as e:
            log.error(f"Trading plan error for {ticker}: {e}")
            return AgentResponse(message=f"產生交易計畫時發生錯誤：{e}")

    async def _handle_sapta(self, ticker: str, user_message: str) -> AgentResponse:
        """Run SAPTA PRE-MARKUP analysis for a ticker."""
        try:
            from pulse.core.sapta import SaptaEngine

            self._last_ticker = ticker

            engine = SaptaEngine()
            result = await engine.analyze(ticker)

            if not result:
                return AgentResponse(
                    message=f"無法對 {ticker} 進行 SAPTA 分析。請確保代號正確。"
                )

            formatted = engine.format_result(result, detailed=True)

            ai = self._get_ai_client()
            notes_str = (
                "\n".join(f"- {n}" for n in result.notes[:5]) if result.notes else "無特定訊號"
            )
            ai_prompt = f"""SAPTA 分析 {ticker}：
狀態：{result.status.value}
分數：{result.final_score:.1f}/100
信心度：{result.confidence.value}
波浪階段：{result.wave_phase or "N/A"}

偵測到的訊號：
{notes_str}

使用者問題：「{user_message}」

請對這份 SAPTA 結果提供 2 到 3 句話的簡短解讀。
說明這檔股票是否值得留意，以及較合適的觀察時機。"""

            ai_comment = await ai.chat(
                ai_prompt,
                system_prompt=(
                    "你是一位專業技術分析師，擅長偵測噴發前兆。請以繁體中文簡短解讀並給出行動建議。"
                ),
                use_history=False,
            )

            msg = f"{ai_comment}\n\n---\n\n{formatted}"

            return AgentResponse(
                message=msg,
                raw_data={"sapta_result": result.to_dict()},
            )

        except Exception as e:
            log.error(f"SAPTA analysis error for {ticker}: {e}")
            return AgentResponse(message=f"SAPTA 分析錯誤: {e}")

    async def _handle_sapta_scan(self, user_message: str) -> AgentResponse:
        """Scan stocks for SAPTA PRE-MARKUP candidates."""
        try:
            from pulse.core.sapta import SaptaEngine, SaptaStatus
            from pulse.core.screener import StockScreener, StockUniverse

            engine = SaptaEngine()
            msg_lower = user_message.lower()

            if any(kw in msg_lower for kw in ["semua", "all", "955", "seluruh", "所有", "全部"]):
                try:
                    from pulse.core.sapta.ml.data_loader import SaptaDataLoader

                    loader = SaptaDataLoader()
                    tickers = loader.get_all_tickers()
                    universe_name = f"全部 ({len(tickers)} 檔)"
                    min_status = SaptaStatus.READY
                except Exception:
                    screener = StockScreener(universe_type=StockUniverse.POPULAR)
                    tickers = screener.universe
                    universe_name = "熱門股票"
                    min_status = SaptaStatus.WATCHLIST
            elif "idx80" in msg_lower:
                screener = StockScreener(universe_type=StockUniverse.IDX80)
                tickers = screener.universe
                universe_name = "IDX80"
                min_status = SaptaStatus.WATCHLIST
            elif "popular" in msg_lower:
                screener = StockScreener(universe_type=StockUniverse.POPULAR)
                tickers = screener.universe
                universe_name = "POPULAR"
                min_status = SaptaStatus.WATCHLIST
            else:
                screener = StockScreener(universe_type=StockUniverse.LQ45)
                tickers = screener.universe
                universe_name = "LQ45"
                min_status = SaptaStatus.WATCHLIST

            results = await engine.scan(tickers, min_status=min_status)

            if not results:
                return AgentResponse(
                    message=f"在 {universe_name} 中找不到符合 SAPTA 條件（WATCHLIST 以上）的股票。"
                )

            formatted = engine.format_scan_results(
                results, title=f"SAPTA 掃描：{universe_name}（{len(results)} 檔）"
            )

            ai = self._get_ai_client()
            top_picks = [
                f"- {r.ticker}：{r.status.value}，分數：{r.final_score:.0f}，"
                f"波段：{r.wave_phase or '無'}"
                for r in results[:5]
            ]
            ai_prompt = f"""SAPTA 掃描結果 {universe_name}：
{chr(10).join(top_picks)}

總計：{len(results)} 檔股票符合條件。

使用者問題：「{user_message}」

請用 2 到 3 句話簡短總結這次掃描結果。
並說明哪幾檔最值得關注。"""

            ai_summary = await ai.chat(
                ai_prompt,
                system_prompt="你是技術分析師。請以繁體中文簡短總結 SAPTA 掃描結果與關注重點。",
                use_history=False,
            )

            msg = f"{ai_summary}\n\n---\n\n{formatted}"

            return AgentResponse(message=msg)

        except Exception as e:
            log.error(f"SAPTA scan error: {e}")
            return AgentResponse(message=f"SAPTA 掃描時發生錯誤：{e}")

    # ── Core flow ─────────────────────────────────────────────────────────────

    def _resolve_followup(self, user_message: str, intent: str, tickers: list[str]) -> tuple[bool, list[str]]:
        """Check if the message is a follow-up on the last ticker; return (is_followup, resolved_tickers)."""
        if tickers or not self._last_ticker or intent != "general":
            return False, tickers

        msg_lower = user_message.lower()
        for pattern in self.FOLLOWUP_PATTERNS:
            if pattern in msg_lower:
                log.info(f"Follow-up detected, using last ticker: {self._last_ticker}")
                return True, [self._last_ticker]

        return False, tickers

    async def run(self, user_message: str) -> AgentResponse:
        """
        Main entry point - run the agentic flow.

        1. Parse intent & extract tickers
        2. Use last ticker if none found (for follow-up questions)
        3. Fetch real data
        4. Build context
        5. AI analyzes with context (with history for follow-ups)
        6. Return response
        """
        log.info(f"SmartAgent processing: {user_message}")

        intent, tickers = self._detect_intent(user_message)
        log.info(f"Detected intent: {intent}, tickers: {tickers}")

        is_followup, tickers = self._resolve_followup(user_message, intent, tickers)

        if intent == "general" and not tickers and not is_followup:
            ai = self._get_ai_client()
            response = await ai.chat(
                user_message,
                system_prompt=(
                    "你是 PULSE，台灣股市分析助理。"
                    "如果使用者詢問與台股無關的內容，請禮貌拒絕並引導回股票分析。"
                    "請用繁體中文簡潔回覆。"
                ),
                use_history=True,
            )
            return AgentResponse(message=response)

        if intent == "index" and tickers:
            return await self._handle_index(tickers[0], user_message)

        if intent == "chart" and tickers:
            ticker = tickers[0]
            self._last_ticker = ticker
            filepath = await self._generate_chart(ticker)
            stock = await self._fetch_stock_data(ticker)
            if filepath and stock:
                msg = f"""{ticker}: NT$ {stock["current_price"]:,.0f} ({stock["change"]:+,.0f}, {stock["change_percent"]:+.2f}%)

圖表已儲存：{filepath}"""
                return AgentResponse(message=msg, chart=filepath)
            return AgentResponse(message=f"無法為 {ticker} 生成圖表。")

        if intent == "forecast" and tickers:
            ticker = tickers[0]
            self._last_ticker = ticker
            msg_lower = user_message.lower()
            forecast_mode = "full" if any(kw in msg_lower for kw in ["完整預測", "詳細預測", "full"]) else "fast"
            forecast = await self._generate_forecast(ticker, mode=forecast_mode)
            if forecast:
                msg = forecast["summary"]
                if forecast.get("filepath"):
                    msg += f"\n\n圖表已儲存：{forecast['filepath']}"
                return AgentResponse(message=msg, chart=forecast.get("filepath"))
            return AgentResponse(message=f"無法為 {ticker} 生成預測。")

        if intent == "screen":
            return await self._handle_screen(user_message)

        if intent == "trading_plan" and tickers:
            return await self._handle_trading_plan(tickers[0], user_message)

        if intent == "sapta" and tickers:
            return await self._handle_sapta(tickers[0], user_message)

        if intent == "sapta_scan":
            return await self._handle_sapta_scan(user_message)

        context = await self._gather_context(intent, tickers)

        if context.error:
            return AgentResponse(message=context.error, context=context)

        if tickers:
            self._last_ticker = tickers[0]
            self._last_context = context

        analysis_prompt = self._build_analysis_prompt(user_message, context)

        if is_followup and self._last_context:
            analysis_prompt = f"[前一次分析: {self._last_ticker}]\n\n" + analysis_prompt

        if self._progress_callback:
            await self._progress_callback("正在分析數據，請稍候...")

        ai = self._get_ai_client()
        ai_response = await ai.chat(
            analysis_prompt,
            system_prompt=(
                "你是台灣股市資深分析師。"
                "請根據提供的真實數據進行分析。"
                "請用繁體中文回覆，簡潔有力。"
                "不要編造數據，只能使用提供的數據。"
            ),
            use_history=True,
        )

        chart_filepath = await self._generate_chart(tickers[0]) if tickers else None
        final_message = ai_response
        if chart_filepath:
            final_message += f"\n\n圖表已儲存：{chart_filepath}"

        return AgentResponse(
            message=final_message,
            context=context,
            chart=chart_filepath,
            raw_data={
                "intent": intent,
                "tickers": tickers,
                "stock_data": context.stock_data,
                "technical_data": context.technical_data,
                "fundamental_data": context.fundamental_data,
            },
        )

    async def run_stream(self, user_message: str):
        """
        Run the agentic flow with streaming response.

        Yields progress updates and response chunks for real-time display.
        """
        log.info(f"SmartAgent processing (stream): {user_message}")

        intent, tickers = self._detect_intent(user_message)
        log.info(f"Detected intent: {intent}, tickers: {tickers}")

        is_followup, tickers = self._resolve_followup(user_message, intent, tickers)

        if intent == "general" and not tickers and not is_followup:
            ai = self._get_ai_client()
            yield {"type": "progress", "message": "正在思考..."}
            async for chunk in ai.chat_stream(
                user_message,
                system_prompt=(
                    "你是 Pulse，台灣股市 AI 分析助理。"
                    "若使用者詢問股市以外的話題，請禮貌拒絕並引導回台股分析。"
                    "以繁體中文簡潔回覆。"
                ),
                use_history=True,
            ):
                yield {"type": "chunk", "content": chunk}
            return

        if intent == "index" and tickers:
            yield {"type": "progress", "message": f"正在取得 {tickers[0]} 指數數據..."}
            response = await self._handle_index(tickers[0], user_message)
            yield {"type": "response", "message": response.message}
            return

        if intent == "chart" and tickers:
            ticker = tickers[0]
            self._last_ticker = ticker
            yield {"type": "progress", "message": f"正在生成 {ticker} K線圖..."}
            filepath = await self._generate_chart(ticker)
            stock = await self._fetch_stock_data(ticker)
            if filepath and stock:
                msg = f"""{ticker}: NT$ {stock["current_price"]:,.2f} ({stock["change"]:+,.2f}, {stock["change_percent"]:+.2f}%)

圖表已儲存：{filepath}"""
                yield {"type": "response", "message": msg, "chart": filepath}
            else:
                yield {"type": "response", "message": f"無法為 {ticker} 生成圖表。"}
            return

        if intent == "forecast" and tickers:
            ticker = tickers[0]
            self._last_ticker = ticker
            msg_lower = user_message.lower()
            forecast_mode = "full" if any(kw in msg_lower for kw in ["完整預測", "詳細預測", "full"]) else "fast"
            yield {"type": "progress", "message": f"正在為 {ticker} 生成價格預測 ({forecast_mode} 模式)..."}
            forecast = await self._generate_forecast(ticker, mode=forecast_mode)
            if forecast:
                msg = forecast["summary"]
                if forecast.get("filepath"):
                    msg += f"\n\n圖表已儲存：{forecast['filepath']}"
                yield {"type": "response", "message": msg, "chart": forecast.get("filepath")}
            else:
                yield {"type": "response", "message": f"無法為 {ticker} 生成預測。"}
            return

        if intent == "screen":
            yield {"type": "progress", "message": "正在執行智能選股..."}
            response = await self._handle_screen(user_message)
            yield {"type": "response", "message": response.message}
            return

        if intent == "trading_plan" and tickers:
            yield {"type": "progress", "message": f"正在為 {tickers[0]} 生成交易計畫..."}
            response = await self._handle_trading_plan(tickers[0], user_message)
            yield {"type": "response", "message": response.message}
            return

        if intent == "sapta" and tickers:
            yield {"type": "progress", "message": f"正在為 {tickers[0]} 執行 SAPTA 分析..."}
            response = await self._handle_sapta(tickers[0], user_message)
            yield {"type": "response", "message": response.message}
            return

        if intent == "sapta_scan":
            yield {"type": "progress", "message": "正在執行 SAPTA 掃描..."}
            response = await self._handle_sapta_scan(user_message)
            yield {"type": "response", "message": response.message}
            return

        context = await self._gather_context(intent, tickers)

        if context.error:
            yield {"type": "error", "message": context.error}
            return

        if tickers:
            self._last_ticker = tickers[0]
            self._last_context = context

        analysis_prompt = self._build_analysis_prompt(user_message, context)

        if is_followup and self._last_context:
            analysis_prompt = f"[前一次分析: {self._last_ticker}]\n\n" + analysis_prompt

        yield {"type": "progress", "message": "正在分析數據，請稍候..."}

        ai = self._get_ai_client()
        full_response = ""
        async for chunk in ai.chat_stream(
            analysis_prompt,
            system_prompt=(
                "你是台灣股市資深分析師。"
                "請根據提供的真實數據進行分析。"
                "請用繁體中文回覆，簡潔有力。"
                "不要編造數據，只能使用提供的數據。"
            ),
            use_history=True,
        ):
            full_response += chunk
            yield {"type": "chunk", "content": chunk}

        chart_filepath = await self._generate_chart(tickers[0]) if tickers else None
        final_message = full_response
        if chart_filepath:
            final_message += f"\n\n圖表已儲存：{chart_filepath}"

        yield {
            "type": "complete",
            "message": final_message,
            "chart": chart_filepath,
            "context": context,
            "raw_data": {
                "intent": intent,
                "tickers": tickers,
                "stock_data": context.stock_data,
                "technical_data": context.technical_data,
                "fundamental_data": context.fundamental_data,
            },
        }
