"""
Smart Money Screener - Trend/Volume/Bias 三維度主力足跡選股器

核心代號: Trend (趨勢), Volume (量能), Bias (乖離)
針對「無籌碼數據」環境優化，利用高階形態學來捕捉主力足跡。

評分邏輯 (總分100分):
1. 趨勢與型態 (Trend & Pattern) - 權重40%
   - 極致壓縮 (The Perfect Squeeze): 布林帶寬<15%且維持至少10天 → +25分
   - 帶量突破 (Breakout): 股價突破上軌，且呈現實體紅棒 → +15分

2. 量能與K線 (Volume & Candle) - 權重35%
   - OBV先行創高 (Smart Money): 股價盤整時，OBV指標率先突破前高 → +15分
   - 純粹攻擊量: 當日量 > 兩倍MV5，且量比階梯式放大 → +10分
   - K線霸氣: 實體長紅 > 70%，且收盤接近最高點 → +10分

3. 乖離與位階 (Bias & Position) - 權重25%
   - 黃金起漲點: 距 MA20 乖離5%-10%，剛脫離成本區 → +15分
   - 長線保護短線: 股價位於年線之上 → +10分

Performance Tips:
- 使用 --tw50 預設小池子加速掃描
- 使用 --fast 跳過OBV歷史比對
"""

from pathlib import Path
from typing import Literal

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, cast

import pandas as pd

from pulse.core.analysis.technical import TechnicalAnalyzer
from pulse.core.data.stock_data_provider import StockDataProvider
from pulse.utils.logger import get_logger

log = get_logger(__name__)


# Stock market type
StockMarket = Literal["tw50", "listed", "otc", "all"]


def load_tickers_from_json(filename: str) -> list[str]:
    """從 JSON 檔案載入股票代號"""
    # Files are in data/ directory (same level as pulse/)
    base_dir = Path(__file__).resolve().parents[2]  # Go up to project root
    filepath = base_dir / "data" / filename
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            import json

            data = json.load(f)
            if isinstance(data, list):
                # 移除 0050 ETF (如果是 TW50)
                return [t for t in data if t != "0050"]
            return []
    except Exception as e:
        log.warning(f"無法載入 {filepath}: {e}")
        return []


@dataclass
class SmartMoneyResult:
    """主力足跡選股結果"""

    ticker: str
    name: str | None = None
    sector: str | None = None

    # Price data
    price: float = 0.0
    change_percent: float = 0.0
    volume: int = 0

    # Technical indicators
    bb_upper: float | None = None
    bb_middle: float | None = None
    bb_lower: float | None = None
    bb_width: float | None = None

    # MA indicators
    sma_20: float | None = None
    sma_200: float | None = None

    # Volume metrics
    volume_sma_5: float | None = None  # MV5

    # OBV metrics
    obv: float | None = None
    obv_consolidation_high: float | None = None  # OBV盤整期間高點
    obv_broke_high: bool = False  # OBV是否突破高點

    # Candle metrics
    body_ratio: float | None = None  # 實體比率
    close_position: float | None = None  # 收盤位置 (0-1, 1=最高點)

    # Bias
    bias_ma20: float | None = None  # 乖離率 (%)

    # Scoring breakdown
    total_score: float = 0.0
    trend_score: float = 0.0
    volume_score: float = 0.0
    bias_score: float = 0.0

    # Signals
    signals: list[str] = field(default_factory=list)

    # Squeeze info
    squeeze_days: int = 0
    is_breakout: bool = False
    is_volume_ladder: bool = False

    @property
    def bb_width_percent(self) -> float:
        """布林帶寬度百分比"""
        if self.bb_middle and self.bb_middle > 0 and self.bb_upper and self.bb_lower:
            return ((self.bb_upper - self.bb_lower) / self.bb_middle) * 100
        return 100.0

    @property
    def volume_ratio(self) -> float:
        """量比"""
        if self.volume_sma_5 and self.volume_sma_5 > 0:
            return self.volume / self.volume_sma_5
        return 1.0

    @property
    def status(self) -> str:
        """評分等級"""
        if self.total_score >= 80:
            return "⭐⭐⭐ 強勢主力股"
        elif self.total_score >= 60:
            return "⭐⭐ 主力吸籌"
        elif self.total_score >= 40:
            return "⭐ 觀察名單"
        else:
            return "未達標準"


class SmartMoneyScreener:
    """
    主力足跡選股器 - Trend/Volume/Bias 三維度評分

    針對無籌碼數據環境優化，利用技術分析捕捉主力行為。
    """

    # 評分閾值
    BB_SQUEEZE_WIDTH = 15.0  # 布林帶寬度閾值 (%)
    BB_SQUEEZE_DAYS = 10  # 壓縮天數閾值
    BODY_RATIO_THRESHOLD = 0.7  # 實體比率閾值
    CLOSE_POSITION_THRESHOLD = 0.9  # 收盤接近最高點閾值
    VOLUME_LADDER_THRESHOLD = 2.0  # 攻擊量倍數閾值
    BIAS_LOWER = 5.0  # 乖離率下限 (%)
    BIAS_UPPER = 10.0  # 乖離率上限 (%)

    def __init__(self, universe: list[str] | None = None):
        """
        Initialize screener with stock universe.

        Args:
            universe: List of tickers to screen. If None, uses all available tickers.
        """
        self.universe = universe
        self.fetcher = StockDataProvider()
        self.analyzer = TechnicalAnalyzer()

    def load_market_tickers(self, market: StockMarket = "tw50") -> list[str]:
        """依市場類型載入股票代號"""
        if market == "tw50":
            return load_tickers_from_json("tw_codes_tw50.json")
        elif market == "listed":
            return load_tickers_from_json("tw_codes_listed.json")
        elif market == "otc":
            return load_tickers_from_json("tw_codes_otc.json")
        elif market == "all":
            listed = load_tickers_from_json("tw_codes_listed.json")
            otc = load_tickers_from_json("tw_codes_otc.json")
            return sorted(list(set(listed + otc)))
        return []

    def _load_all_tickers(self) -> list[str]:
        """載入所有股票代號 (預設 TW50)"""
        return self.load_market_tickers("tw50")

    async def _fetch_full_data(
        self, ticker: str, fast_mode: bool = False
    ) -> SmartMoneyResult | None:
        """
        獲取完整數據用於主力足跡分析

        Args:
            ticker: Stock ticker
            fast_mode: If True, skip OBV historical comparison for speed
        """
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            start_date_str = start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")

            # Fetch stock data
            stock = await self.fetcher.fetch_stock(
                ticker, period="1y", start_date=start_date_str, end_date=end_date_str
            )
            if not stock:
                return None

            # Get technical indicators
            technical = await self.analyzer.analyze(ticker)
            if not technical:
                return None

            # Get historical data for additional analysis
            df = await self.fetcher.fetch_history(
                ticker, period="1y", start_date=start_date_str, end_date=end_date_str
            )

            result = SmartMoneyResult(
                ticker=ticker,
                name=stock.name,
                sector=stock.sector,
                price=stock.current_price,
                change_percent=stock.change_percent,
                volume=stock.volume,
                bb_upper=technical.bb_upper,
                bb_middle=technical.bb_middle,
                bb_lower=technical.bb_lower,
                bb_width=technical.bb_width,
                sma_20=technical.sma_20,
                sma_200=technical.sma_200,
                obv=technical.obv,
            )

            # Additional analysis from historical data (skip OBV in fast mode)
            if df is not None and not df.empty:
                result = self._analyze_from_dataframe(result, df, fast_mode)

            return result

        except Exception as e:
            log.error(f"Error fetching data for {ticker}: {e}")
            return None

    def _analyze_from_dataframe(
        self, result: SmartMoneyResult, df: pd.DataFrame, fast_mode: bool = False
    ) -> SmartMoneyResult:
        """從DataFrame進行額外分析"""
        df = df.copy()

        # 1. 計算 MV5 (5日均量)
        if "volume" in df.columns:
            vol_ma5 = df["volume"].rolling(5).mean()
            if isinstance(vol_ma5, pd.Series) and len(vol_ma5) > 0:
                result.volume_sma_5 = float(vol_ma5.iloc[-1])

        # 2. 計算實體比率與收盤位置
        if all(col in df.columns for col in ["open", "high", "low", "close"]):
            latest = df.iloc[-1]

            high_low_range = latest["high"] - latest["low"]
            if high_low_range > 0:
                body = abs(latest["close"] - latest["open"])
                result.body_ratio = body / high_low_range

                # 收盤位置: (close - low) / (high - low)
                result.close_position = (latest["close"] - latest["low"]) / high_low_range

        # 3. 計算乖離率
        if result.sma_20 and result.price > 0:
            result.bias_ma20 = ((result.price - result.sma_20) / result.sma_20) * 100

        # 4. OBV 先行創高分析
        if result.obv is not None and "close" in df.columns:
            df = df.copy()
            df["obv"] = self._calculate_obv(df)

            # 找出近期盤整期間 (價格波動小於ATR的1.5倍)
            atr_threshold = None
            if "atr_14" in df.columns:
                atr_threshold = df["atr_14"].iloc[-1] * 1.5

            if atr_threshold is None:
                # 如果沒有ATR，使用價格標準差作為閾值
                atr_threshold = df["close"].std() * 2

            # 最近30天內找出盤整區間
            recent_df = df.tail(30)

            # 計算價格波動
            price_std = recent_df["close"].std()
            price_mean = recent_df["close"].mean()
            is_consolidation = price_std / price_mean < 0.03  # 波動率 < 3%

            if is_consolidation:
                # 盤整期間的 OBV 高點
                consolidation_obv = recent_df["obv"].max()
                result.obv_consolidation_high = float(consolidation_obv)

                # 檢查 OBV 是否突破盤整高點 (使用iloc確保是pandas Series)
                prev_obv_values = df["obv"].iloc[-30:-10] if len(df) >= 30 else df["obv"]
                if hasattr(prev_obv_values, "max"):
                    prev_obv_high = prev_obv_values.max()
                    result.obv_broke_high = result.obv > prev_obv_high

        # 5. 極致壓縮分析 (布林帶寬持續低於閾值)
        if result.bb_width is not None:
            squeeze_days = 0
            # Calculate BB width for each row and check squeeze duration
            for i in range(-1, -min(30, len(df)), -1):
                # Recalculate BB width for this row
                close_i = df["close"].iloc[i]
                n = 20
                if len(df) >= n + i + 1:
                    recent_close = df["close"].iloc[max(0, i - n + 1) : i + 1]
                    if len(recent_close) >= n:
                        bb_middle_i = recent_close.mean()
                        bb_std_i = recent_close.std()
                        bb_width_i = (
                            (bb_middle_i + 2 * bb_std_i - (bb_middle_i - 2 * bb_std_i))
                            / bb_middle_i
                            * 100
                        )
                        if bb_width_i < self.BB_SQUEEZE_WIDTH:
                            squeeze_days += 1
                        else:
                            break
            result.squeeze_days = squeeze_days

        # 6. 帶量突破分析
        if result.bb_upper and result.price:
            result.is_breakout = result.price > result.bb_upper

        # 7. 階梯式放量分析
        if result.volume_ratio > self.VOLUME_LADDER_THRESHOLD:
            # 檢查最近3天是否階梯式放大
            recent_volumes = df["volume"].tail(5).tolist()
            if len(recent_volumes) >= 3:
                # 連續2天放大
                result.is_volume_ladder = (
                    recent_volumes[-1] > recent_volumes[-2] > recent_volumes[-3]
                ) or (recent_volumes[-1] > recent_volumes[-2] * 1.2)

        return result

    def _calculate_obv(self, df: pd.DataFrame) -> pd.Series:
        """計算 OBV"""
        close = df["close"]
        volume = df["volume"]

        obv = pd.Series(index=df.index, dtype=float)
        obv.iloc[0] = volume.iloc[0]

        for i in range(1, len(df)):
            if close.iloc[i] > close.iloc[i - 1]:
                obv.iloc[i] = obv.iloc[i - 1] + volume.iloc[i]
            elif close.iloc[i] < close.iloc[i - 1]:
                obv.iloc[i] = obv.iloc[i - 1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i - 1]

        return obv

    def _calculate_smart_money_score(self, result: SmartMoneyResult) -> SmartMoneyResult:
        """
        計算主力足跡評分

        Returns:
            Updated SmartMoneyResult with scores
        """
        score = 0.0
        trend_score = 0.0
        volume_score = 0.0
        bias_score = 0.0
        signals = []

        # ==================== 趨勢與型態 (40分) ====================

        # 1. 極致壓縮 (The Perfect Squeeze) - 25分
        if (
            result.bb_width_percent < self.BB_SQUEEZE_WIDTH
            and result.squeeze_days >= self.BB_SQUEEZE_DAYS
        ):
            # 布林帶寬 < 15% 且維持至少10天
            squeeze_score = 25.0
            trend_score += squeeze_score
            score += squeeze_score
            signals.append(
                f"極致壓縮 (BB寬度{result.bb_width_percent:.1f}%, 持續{result.squeeze_days}天)"
            )

        elif result.bb_width_percent < self.BB_SQUEEZE_WIDTH:
            # 寬度達標但天數不足
            squeeze_score = 15.0
            trend_score += squeeze_score
            score += squeeze_score
            signals.append(f"布林收縮 (BB寬度{result.bb_width_percent:.1f}%)")

        elif result.bb_width_percent < 20:
            trend_score += 5.0
            score += 5.0

        # 2. 帶量突破 (Breakout) - 15分
        if result.is_breakout and result.body_ratio and result.body_ratio > 0.5:
            breakout_score = 15.0
            trend_score += breakout_score
            score += breakout_score
            signals.append(f"帶量突破 (價格>{result.bb_upper}, 實體{result.body_ratio * 100:.0f}%)")

        elif result.is_breakout:
            breakout_score = 8.0
            trend_score += breakout_score
            score += breakout_score
            signals.append("突破布林上軌")

        # ==================== 量能與K線 (35分) ====================

        # 3. OBV先行創高 (Smart Money) - 15分
        if result.obv_broke_high:
            obv_score = 15.0
            volume_score += obv_score
            score += obv_score
            signals.append("OBV領先創高 (主力吃貨)")

        elif result.obv_consolidation_high:
            obv_score = 5.0
            volume_score += obv_score
            score += obv_score
            signals.append("OBV整理待突破")

        # 4. 純粹攻擊量 - 10分
        if result.is_volume_ladder and result.volume_ratio > self.VOLUME_LADDER_THRESHOLD:
            volume_ladder_score = 10.0
            volume_score += volume_ladder_score
            score += volume_ladder_score
            signals.append(f"階梯式攻擊量 ({result.volume_ratio:.1f}xMV5)")

        elif result.volume_ratio > self.VOLUME_LADDER_THRESHOLD:
            volume_ladder_score = 5.0
            volume_score += volume_ladder_score
            score += volume_ladder_score
            signals.append(f"放量 ({result.volume_ratio:.1f}xMV5)")

        # 5. K線霸氣 - 10分
        if (
            result.body_ratio
            and result.body_ratio >= self.BODY_RATIO_THRESHOLD
            and result.close_position
            and result.close_position >= self.CLOSE_POSITION_THRESHOLD
        ):
            candle_score = 10.0
            volume_score += candle_score
            score += candle_score
            signals.append(
                f"霸氣長紅 (實體{result.body_ratio * 100:.0f}%, 收盤{result.close_position * 100:.0f}%高點)"
            )

        elif result.body_ratio and result.body_ratio >= 0.5:
            candle_score = 5.0
            volume_score += candle_score
            score += candle_score
            signals.append(f"紅棒 ({result.body_ratio * 100:.0f}%實體)")

        # ==================== 乖離與位階 (25分) ====================

        # 6. 黃金起漲點 - 15分
        if result.bias_ma20:
            if self.BIAS_LOWER <= result.bias_ma20 <= self.BIAS_UPPER:
                bias_score += 15.0
                score += 15.0
                signals.append(f"黃金起漲點 (乖離{result.bias_ma20:.1f}%)")

            elif result.bias_ma20 > 0 and result.bias_ma20 < self.BIAS_LOWER * 2:
                bias_score += 7.0
                score += 7.0
                signals.append(f"脫離成本區 (乖離{result.bias_ma20:.1f}%)")

            elif result.bias_ma20 < 0:
                bias_score += 3.0
                score += 3.0
                signals.append(f"回調中 (乖離{result.bias_ma20:.1f}%)")

        # 7. 長線保護短線 - 10分
        if result.sma_200 and result.price > result.sma_200:
            trend_score += 10.0
            score += 10.0
            signals.append("站上年線")

        # Update result
        result.total_score = min(score, 100.0)
        result.trend_score = trend_score
        result.volume_score = volume_score
        result.bias_score = bias_score
        result.signals = signals

        return result

    async def screen(
        self,
        min_score: float = 40.0,
        limit: int = 20,
        universe: list[str] | None = None,
        market: StockMarket = "tw50",
        fast_mode: bool = False,
    ) -> list[SmartMoneyResult]:
        """
        主力足跡選股掃描

        Args:
            min_score: Minimum score to include (0-100)
            limit: Maximum number of results
            universe: Custom stock list. If None, uses market parameter.
            market: Stock market type (tw50, listed, otc, all)
            fast_mode: Skip OBV historical comparison for speed
        """
        target_universe = universe
        if target_universe is None:
            target_universe = self.load_market_tickers(market)

        if not target_universe:
            log.warning("No tickers available for screening")
            return []

        total = len(target_universe)
        market_name = {"tw50": "TW50", "listed": "上市公司", "otc": "上櫃公司", "all": "全部"}[
            market
        ]
        log.info(f"Scanning {total} stocks ({market_name})...")

        # Fetch data for all stocks in parallel with semaphore
        semaphore = asyncio.Semaphore(10)

        async def fetch_and_score(ticker: str) -> SmartMoneyResult | None:
            async with semaphore:
                data = await self._fetch_full_data(ticker, fast_mode)
                if data:
                    return self._calculate_smart_money_score(data)
                return None

        # Create and execute all tasks
        tasks = [fetch_and_score(ticker) for ticker in target_universe]
        all_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Filter results
        results: list[SmartMoneyResult] = []
        for item in all_results:
            if isinstance(item, Exception) or item is None:
                continue
            # Type guard: check if it has total_score attribute
            if hasattr(item, "total_score") and hasattr(item, "ticker"):
                result = cast(SmartMoneyResult, item)
                if result.total_score >= min_score:
                    results.append(result)

        # Sort results by score
        results.sort(key=lambda x: x.total_score, reverse=True)

        log.info(f"Found {len(results)} stocks with smart money score >= {min_score}")

        return results[:limit]

    def format_results(
        self,
        results: list[SmartMoneyResult],
        title: str = "主力足跡選股",
    ) -> str:
        """格式化選股結果為簡潔逐行輸出"""
        if not results:
            return f"""
{title}
---
未找到符合條件的股票 (min_score=40)

評分維度:
  趨勢型態 (40分): 極致壓縮(+25)、帶量突破(+15)
  量能K線 (35分): OBV創高(+15)、攻擊量(+10)、長紅(+10)
  乖離位階 (25分): 黃金起漲點(+15)、站上年線(+10)"""

        lines = [f"{title}", f"---", f"找到 {len(results)} 檔符合條件的股票:", ""]

        for r in results:
            # 狀態標記
            if r.total_score >= 80:
                status = "[★★★]"
            elif r.total_score >= 60:
                status = "[★★ ]"
            else:
                status = "[★  ]"

            # 第一行: 代號、分數、狀態
            lines.append(f"{status} {r.ticker:<6} {r.total_score:>5.1f}/100  {r.name or ''}")

            # 第二行: 價格、乖離、量比
            bias_str = f"乖離MA20:{r.bias_ma20:+.1f}%" if r.bias_ma20 else ""
            vol_str = f"量比:{r.volume_ratio:.1f}x" if r.volume_ratio else ""
            lines.append(f"    NT${r.price:,.0f} ({r.change_percent:+.2f}%)  {bias_str}  {vol_str}")

            # 第三行: 觸發的信號
            if r.signals:
                # 簡化信號顯示
                signal_summary = []
                for s in r.signals:
                    # 移除冗餘描述，保留關鍵詞
                    s = s.replace(" (BB寬度", " BB:")
                    s = s.replace("%)", "")
                    s = s.replace(", 持續", "")
                    s = s.replace("天)", "")
                    s = s.replace("價格>", "突破:")
                    s = s.replace("實體", "實體:")
                    s = s.replace(", 收盤", "")
                    s = s.replace("%高點", "%")
                    s = s.replace(" (主力吃貨)", "")
                    s = s.replace(" (階梯", " 階梯")
                    s = s.replace(" (", " ")
                    s = s.replace(")", "")
                    signal_summary.append(s)
                lines.append(f"    信號: {' | '.join(signal_summary[:3])}")

            lines.append("")  # 空行分隔

        # 圖例
        lines.append("圖例: ★★★=80+強勢  ★★=60-79吸籌  ★=40-59觀察")

        return "\n".join(lines)

    def format_single_result(self, result: SmartMoneyResult) -> str:
        """格式化單一股票詳細結果"""
        lines = [
            "╔════════════════════════════════════════════════════════════════════════════════╗",
            f"║ 主力足跡分析: {result.ticker} - {result.name or 'N/A':<50} ║",
            "╠════════════════════════════════════════════════════════════════════════════════╣",
        ]

        # 基本資訊
        lines.append(
            f"║ 價格: NT${result.price:,.0f} ({result.change_percent:+.2f}%)  成交量: {result.volume:,}         ║"
        )
        lines.append(f"║ 狀態: {result.status:<60} ║")

        # 評分
        score_bar = "█" * int(result.total_score / 5) + "░" * (20 - int(result.total_score / 5))
        lines.append(
            f"║ 總評分: {result.total_score:>5.1f}/100 [{score_bar}]                                        ║"
        )

        # 三維度評分
        trend_bar = "█" * int(result.trend_score / 1.5) + "░" * (27 - int(result.trend_score / 1.5))
        volume_bar = "█" * int(result.volume_score / 1.2) + "░" * (
            29 - int(result.volume_score / 1.2)
        )
        bias_bar = "█" * int(result.bias_score / 1) + "░" * (25 - int(result.bias_score / 1))

        lines.append(
            f"║                                                                                ║"
        )
        lines.append(
            f"║ 趨勢型態 (40分): {result.trend_score:>5.1f} [{trend_bar}]                    ║"
        )
        lines.append(
            f"║ 量能K線 (35分): {result.volume_score:>5.1f} [{volume_bar}]                    ║"
        )
        lines.append(
            f"║ 乖離位階 (25分): {result.bias_score:>5.1f} [{bias_bar}]                      ║"
        )

        # 技術指標
        lines.append(
            f"║                                                                                ║"
        )
        lines.append(
            f"║ ─────────────────────────── 技術指標 ───────────────────────────            ║"
        )

        bb_info = f"BB寬度: {result.bb_width_percent:.1f}%" if result.bb_width else "N/A"
        lines.append(
            f"║ 布林通道: {bb_info:<20} 壓縮天數: {result.squeeze_days}天                   ║"
        )

        ma_info = f"MA20: {result.sma_20:,.0f}" if result.sma_20 else "N/A"
        ma200_info = f"MA200: {result.sma_200:,.0f}" if result.sma_200 else "N/A"
        lines.append(f"║ 均線: {ma_info:<15} {ma200_info:<15}                     ║")

        bias_info = f"乖離MA20: {result.bias_ma20:+.1f}%" if result.bias_ma20 else "N/A"
        lines.append(f"║ {bias_info:<30}                                    ║")

        # 量能
        lines.append(
            f"║                                                                                ║"
        )
        lines.append(
            f"║ ─────────────────────────── 量能分析 ───────────────────────────            ║"
        )

        vol_info = f"量比MV5: {result.volume_ratio:.1f}x" if result.volume_ratio else "N/A"
        lines.append(f"║ {vol_info:<25}                                        ║")

        obv_info = "OBV突破" if result.obv_broke_high else "OBV整理"
        lines.append(f"║ {obv_info:<25}                                        ║")

        # K線
        if result.body_ratio and result.close_position:
            lines.append(
                f"║                                                                                ║"
            )
            lines.append(
                f"║ ─────────────────────────── K線型態 ───────────────────────────            ║"
            )
            lines.append(
                f"║ 實體比率: {result.body_ratio * 100:.0f}%  收盤位置: {result.close_position * 100:.0f}%高點                          ║"
            )

        # 信號
        if result.signals:
            lines.append(
                f"║                                                                                ║"
            )
            lines.append(
                f"║ ─────────────────────────── 觸發信號 ───────────────────────────            ║"
            )
            for signal in result.signals:
                lines.append(f"║  ✓ {signal:<73} ║")

        lines.append(
            "╚════════════════════════════════════════════════════════════════════════════════╝"
        )

        return "\n".join(lines)
