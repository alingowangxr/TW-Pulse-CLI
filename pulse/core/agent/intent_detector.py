"""
IntentDetector - Parses user messages to identify intent and extract tickers.

Extracted from SmartAgent to keep intent-parsing logic self-contained.
"""

import re

from pulse.utils.logger import get_logger

log = get_logger(__name__)


class IntentDetector:
    """Detects user intent and extracts Taiwan stock tickers from natural-language input."""

    _TICKER_WORD_RE = re.compile(r"\b(\d{4,6})\b")
    _VALID_TICKER_RE = re.compile(r"^\d{4,6}$")
    _CRITERIA_RE = re.compile(r"(rsi|pe|pb|roe|macd)\s*[<>]\s*\d+")

    # Taiwan stock tickers (common ones)
    KNOWN_TICKERS = {
        # Semiconductor (半導體)
        "2330",  # 台積電
        "2454",  # 聯發科
        "2303",  # 聯電
        "3711",  # 日月光投控
        "2379",  # 瑞昱
        "3034",  # 聯詠
        "6415",  # 矽力KY
        "2449",  # 京元電子
        "3529",  # 力旺
        "2408",  # 南亞科
        # Electronics (電子)
        "2317",  # 鴻海
        "2382",  # 廣達
        "2357",  # 華碩
        "3231",  # 緯創
        "2324",  # 仁寶
        "2356",  # 英業達
        "2301",  # 光寶科
        "2308",  # 台達電
        # Finance (金融)
        "2881",  # 富邦金
        "2882",  # 國泰金
        "2891",  # 中信金
        "2886",  # 兆豐金
        "2884",  # 玉山金
        "2892",  # 第一金
        "2880",  # 華南金
        "2883",  # 開發金
        "2887",  # 台新金
        "5880",  # 合庫金
        # Steel (鋼鐵)
        "2002",  # 中鋼
        "2006",  # 東和鋼鐵
        "2014",  # 中鴻
        "2027",  # 大成鋼
        # Plastic (塑化)
        "1301",  # 台塑
        "1303",  # 南亞
        "1326",  # 台化
        "6505",  # 台塑化
        # Food (食品)
        "1216",  # 統一
        "1227",  # 佳格
        "1229",  # 聯華
        "1231",  # 聯華食
        # Biotech (生技)
        "4736",  # 泰博
        "4743",  # 合一
        "4746",  # 台耀
        "6446",  # 藥華藥
        # Telecom (電信)
        "2412",  # 中華電
        "3045",  # 台灣大
        "4904",  # 遠傳
        # Others (其他)
        "2912",  # 統一超
        "2801",  # 彰銀
        "2603",  # 長榮
        "2609",  # 陽明
    }

    # Chinese stock name to ticker mapping (for user queries like "台塑股價")
    CHINESE_NAME_TO_TICKER = {
        # Plastic (塑化)
        "台塑": "1301",
        "南亞": "1303",
        "台化": "1326",
        "台塑化": "6505",
        # Semiconductor (半導體)
        "台積電": "2330",
        "聯發科": "2454",
        "聯電": "2303",
        "日月光": "3711",
        "瑞昱": "2379",
        "聯詠": "3034",
        "矽力": "6415",
        # Electronics (電子)
        "鴻海": "2317",
        "廣達": "2382",
        "華碩": "2357",
        "緯創": "3231",
        "仁寶": "2324",
        "英業達": "2356",
        "光寶科": "2301",
        "台達電": "2308",
        # Finance (金融)
        "富邦金": "2881",
        "國泰金": "2882",
        "中信金": "2891",
        "兆豐金": "2886",
        "玉山金": "2884",
        "第一金": "2892",
        "華南金": "2880",
        "開發金": "2883",
        "台新金": "2887",
        "合庫金": "5880",
        # Steel (鋼鐵)
        "中鋼": "2002",
        "東和鋼鐵": "2006",
        "中鴻": "2014",
        "大成鋼": "2027",
        # Food (食品)
        "統一": "1216",
        "佳格": "1227",
        "聯華": "1229",
        "聯華食": "1231",
        # Biotech (生技)
        "泰博": "4736",
        "合一": "4743",
        "台耀": "4746",
        "藥華藥": "6446",
        # Telecom (電信)
        "中華電": "2412",
        "台灣大": "3045",
        "遠傳": "4904",
        # Others (其他)
        "統一超": "2912",
        "彰銀": "2801",
        "長榮": "2603",
        "陽明": "2609",
    }

    # Words that look like tickers but aren't (Taiwan context)
    TICKER_BLACKLIST = {
        "1000",
        "2000",
        "3000",
        "5000",
        "10000",
        "STOP",
        "LOSS",
        "HOLD",
        "CHART",
        "DATA",
    }

    # Taiwan market indices
    KNOWN_INDICES = {
        "TAIEX": "^TWII",
        "TWII": "^TWII",
        "TPEX": "^TWOTCI",
        "OTC": "^TWOTCI",
        "TW50": "0050.TW",
    }

    # Intent patterns - Traditional Chinese & English
    INTENT_PATTERNS = {
        "analyze": [
            r"分析\s*(\d{4})",
            r"分析\s+(\w+)",
            r"看看\s*(\d{4})",
            r"查看\s*(\d{4})",
            r"檢查\s*(\d{4})",
            r"analyze\s+(\w+)",
            r"review\s+(\w+)",
        ],
        "price": [
            r"價格\s*(\d{4})",
            r"股價\s*(\d{4})",
            r"多少\s*(\d{4})",
            r"price\s+(\w+)",
        ],
        "chart": [
            r"圖表\s*(\d{4})",
            r"走勢\s*(\d{4})",
            r"chart\s+(\w+)",
            r"graph\s+(\w+)",
        ],
        "technical": [
            r"技術\s*(\d{4})",
            r"技術面\s*(\d{4})",
            r"technical\s+(\w+)",
            r"ta\s+(\w+)",
            r"rsi\s+(\w+)",
            r"macd\s+(\w+)",
        ],
        "fundamental": [
            r"基本面\s*(\d{4})",
            r"fundamental\s+(\w+)",
            r"valuation\s+(\w+)",
            r"pe\s+(\w+)",
            r"pbv\s+(\w+)",
        ],
        "forecast": [
            r"預測\s*(\d{4})",
            r"預估\s*(\d{4})",
            r"forecast\s+(\w+)",
            r"target\s+(\w+)",
        ],
        "compare": [
            r"比較\s*(\d{4})\s*(?:和|與|跟)\s*(\d{4})",
            r"(\d{4})\s+vs\.?\s+(\d{4})",
            r"(\w+)\s+vs\.?\s+(\w+)",
        ],
        "recommendation": [
            r"推薦\s*(\d{4})",
            r"建議\s*(\d{4})",
            r"可以買\s*(\d{4})",
            r"worth\s+(?:it)?\s+(\w+)",
        ],
        "screen": [
            r"找股票",
            r"篩選股票",
            r"尋找.*股票",
            r"哪些股票",
            r"什麼股票",
            r"screen\s+(.+)",
            r"filter\s+(.+)",
            r"rsi\s*[<>]\s*\d+",
            r"pe\s*[<>]\s*\d+",
            r"oversold",
            r"overbought",
            r"超賣",
            r"超買",
            r"bullish",
            r"bearish",
            r"多頭",
            r"空頭",
            r"breakout",
            r"突破",
            r"undervalued",
            r"低估",
            r"潛力股",
            r"推薦.*股票",
            r"small\s*cap",
            r"mid\s*cap",
        ],
        "trading_plan": [
            r"交易計畫\s*(\d{4})",
            r"trading\s*plan\s+(\w+)",
            r"plan\s+(\w+)",
            r"tp\s+sl\s+(\w+)",
            r"停利停損\s*(\d{4})",
            r"stop\s*loss\s+(\w+)",
            r"take\s*profit\s+(\w+)",
            r"停損\s*(\d{4})",
            r"停利\s*(\d{4})",
            r"rr\s+(\w+)",
            r"risk\s*reward\s+(\w+)",
            r"entry\s+(\w+)",
            r"進場\s*(\d{4})",
            r"出場\s*(\d{4})",
            r"目標價\s*(\d{4})",
        ],
        "sapta": [
            r"sapta\s+(\w+)",
            r"預漲\s*(\d{4})",
            r"準備突破\s*(\d{4})",
            r"pre[\s\-]?markup\s+(\w+)",
            r"(\d{4})\s*準備突破",
            r"(\d{4})\s*要突破",
            r"(\w+)\s+breakout",
        ],
    }

    # Pre-compiled patterns for detect_intent (avoids re.compile on every call)
    _COMPILED_INTENT_PATTERNS: dict[str, list] = {
        intent: [re.compile(p) for p in patterns]
        for intent, patterns in INTENT_PATTERNS.items()
    }

    def extract_tickers(self, message: str) -> list[str]:
        """Extract stock tickers from message (Taiwan 4-6 digit codes or Chinese names)."""
        tickers = []

        # Check for Chinese stock names first
        for name, ticker in self.CHINESE_NAME_TO_TICKER.items():
            if name in message:
                if ticker not in tickers:
                    tickers.append(ticker)
                log.debug(f"Found Chinese stock name: {name} -> {ticker}")

        # Check for known tickers (4-digit codes)
        for ticker in self.KNOWN_TICKERS:
            if ticker in message:
                if ticker not in tickers:
                    tickers.append(ticker)

        # Also check for 4-6 digit numbers that might be tickers
        for word in self._TICKER_WORD_RE.findall(message):
            if word not in tickers and self.is_valid_ticker(word):
                tickers.append(word)

        return tickers

    def is_valid_ticker(self, ticker: str) -> bool:
        """Validate ticker format (Taiwan 4-6 digit codes)."""
        if ticker in self.KNOWN_TICKERS:
            return True
        if ticker in self.TICKER_BLACKLIST:
            return False
        if self._VALID_TICKER_RE.match(ticker):
            return True
        return False

    def detect_intent(self, message: str) -> tuple[str, list[str]]:
        """
        Detect user intent and extract tickers.

        Returns:
            Tuple of (intent, tickers)
        """
        message_lower = message.lower().strip()

        # Check for index intent first (TAIEX, TW50, etc)
        # BUT NOT if there are screening keywords
        screen_context_keywords = ["screen", "篩選", "尋找", "找股票", "filter"]
        has_screen_context = any(kw in message_lower for kw in screen_context_keywords)

        if not has_screen_context:
            for index_name in self.KNOWN_INDICES:
                if index_name.lower() in message_lower:
                    return "index", [index_name]

        # Check for market keywords
        if any(kw in message_lower for kw in ["大盤", "市場", "指數", "market", "taiex"]):
            return "index", ["TAIEX"]

        # Check for trading plan intent (check BEFORE screen)
        trading_plan_keywords = [
            "trading plan",
            "交易計畫",
            "tp sl",
            "停利停損",
            "stop loss",
            "停損",
            "take profit",
            "停利",
            "risk reward",
            "進場",
            "出場",
            "目標價",
            "rr ratio",
        ]
        if any(kw in message_lower for kw in trading_plan_keywords):
            tickers = self.extract_tickers(message)
            if tickers:
                return "trading_plan", tickers

        # Check for SAPTA/pre-markup intent (check BEFORE screen)
        sapta_keywords = [
            "sapta",
            "預漲",
            "pre-markup",
            "premarkup",
            "pre markup",
            "準備突破",
            "要突破",
            "breakout",
        ]
        sapta_scan_keywords = [
            "找預漲股票",
            "尋找預漲",
            "預漲股票",
            "找準備突破",
            "準備突破的股票",
            "即將突破",
            "scan pre-markup",
            "scan premarkup",
            "pre-markup scan",
            "找突破股",
        ]
        if any(kw in message_lower for kw in sapta_scan_keywords):
            return "sapta_scan", []
        if any(kw in message_lower for kw in sapta_keywords):
            tickers = self.extract_tickers(message)
            if tickers:
                return "sapta", tickers
            if "scan" in message_lower or "cari" in message_lower or "carikan" in message_lower:
                return "sapta_scan", []

        # Check for screen intent (doesn't require tickers)
        screen_keywords = [
            "找股票",
            "篩選股票",
            "什麼股票",
            "哪些股票",
            "尋找股票",
            "oversold",
            "overbought",
            "超賣",
            "超買",
            "bullish",
            "bearish",
            "多頭",
            "空頭",
            "breakout",
            "突破",
            "undervalued",
            "低估",
            "便宜",
            "screen",
            "filter",
            "潛力股",
            "推薦股票",
            "small cap",
            "mid cap",
            "大漲",
        ]
        if any(kw in message_lower for kw in screen_keywords):
            return "screen", []

        # Check for rsi/pe/etc with operators (screening criteria)
        if self._CRITERIA_RE.search(message_lower):
            return "screen", []

        for intent, patterns in self._COMPILED_INTENT_PATTERNS.items():
            for pattern in patterns:
                match = pattern.search(message_lower)
                if match:
                    tickers = []
                    for group in match.groups():
                        ticker = group.upper()
                        if self.is_valid_ticker(ticker):
                            tickers.append(ticker)
                    if tickers:
                        return intent, tickers

        # Fallback: extract any tickers mentioned
        tickers = self.extract_tickers(message)
        if tickers:
            return "analyze", tickers

        return "general", []
