"""布林壓縮交易策略。

進場條件:
- 帶寬收縮至 20% 百分位以下 (壓縮偵測)
- 帶寬開始擴張
- 收盤價突破上軌 (方向性突破)

出場條件:
- 價格回歸中軌
- 價格觸及下軌
"""

from collections import deque
from typing import Any

from pulse.core.strategies.base import BaseStrategy, SignalAction, StrategySignal, StrategyState
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class BBSqueezeStrategy(BaseStrategy):
    """布林壓縮策略實作。"""

    def __init__(self):
        super().__init__(
            name="布林壓縮策略",
            description="布林帶壓縮突破策略，在低波動後捕捉向上突破",
        )
        self.ticker = ""
        self.bb_width_history: deque = deque(maxlen=100)  # 帶寬歷史
        self.prev_bb_width = None  # 前一日帶寬
        self.in_squeeze = False  # 是否處於壓縮狀態

    async def initialize(
        self, ticker: str, initial_cash: float, config: dict[str, Any]
    ) -> None:
        """初始化策略。

        Args:
            ticker: 股票代碼
            initial_cash: 初始資金
            config: 配置參數
        """
        self.ticker = ticker
        self.config = {
            "squeeze_percentile": config.get("squeeze_percentile", 20),  # 壓縮判定百分位
            "lookback_period": config.get("lookback_period", 20),  # 帶寬歷史回顧期間
            "position_size_pct": config.get("position_size_pct", 0.2),  # 每次買入資金比例
        }

        self.state = StrategyState(cash=initial_cash, total_capital=initial_cash)
        self.bb_width_history = deque(maxlen=max(100, self.config["lookback_period"] * 2))
        self.prev_bb_width = None
        self.in_squeeze = False

        log.info(f"Initialized BBSqueezeStrategy for {ticker}")
        log.info(f"Config: {self.config}")

    def _get_bb_width_percentile(self, current_width: float) -> float | None:
        """計算當前帶寬在歷史中的百分位。

        Args:
            current_width: 當前帶寬

        Returns:
            百分位（0-100），None 表示數據不足
        """
        if len(self.bb_width_history) < self.config["lookback_period"]:
            return None

        # 取最近 lookback_period 筆資料
        recent_widths = list(self.bb_width_history)[-self.config["lookback_period"]:]

        # 計算百分位
        count_below = sum(1 for w in recent_widths if w < current_width)
        percentile = (count_below / len(recent_widths)) * 100

        return percentile

    def _is_expanding(self, bb_width: float | None) -> bool:
        """檢查帶寬是否開始擴張。

        Args:
            bb_width: 當前帶寬

        Returns:
            是否擴張中
        """
        if bb_width is None or self.prev_bb_width is None:
            return False

        return bb_width > self.prev_bb_width

    def _calculate_buy_quantity(self, price: float) -> int:
        """計算買進股數。

        Args:
            price: 當前價格

        Returns:
            買進股數
        """
        if not self.state:
            return 0

        # 使用可用資金的 position_size_pct 比例
        available_cash = self.state.cash
        position_value = available_cash * self.config["position_size_pct"]
        shares = int(position_value / price)

        return max(shares, 0)

    async def on_bar(
        self, bar: dict[str, Any], indicators: dict[str, Any]
    ) -> StrategySignal | None:
        """處理每根K線。

        Args:
            bar: K線數據 {date, open, high, low, close, volume}
            indicators: 技術指標 {bb_upper, bb_middle, bb_lower, bb_width, ...}

        Returns:
            交易訊號或 None
        """
        if not self.state:
            log.warning("Strategy not initialized")
            return None

        close_price = bar["close"]
        open_price = bar["open"]
        date = bar["date"]

        # 取得指標
        bb_upper = indicators.get("bb_upper")
        bb_middle = indicators.get("bb_middle")
        bb_lower = indicators.get("bb_lower")
        bb_width = indicators.get("bb_width")

        # 記錄帶寬歷史
        if bb_width is not None:
            self.bb_width_history.append(bb_width)

        signal = None

        # === 檢查賣出條件 ===
        if self.state.positions > 0:
            # 條件 1: 價格回歸中軌
            if bb_middle is not None and close_price <= bb_middle:
                signal = StrategySignal(
                    timestamp=date,
                    action=SignalAction.SELL,
                    quantity=self.state.total_shares,
                    price=open_price,
                    reason=f"價格回歸中軌（收盤 {close_price:,.0f} <= BB中軌 {bb_middle:,.0f}）",
                )
                self.in_squeeze = False
                self._update_prev_width(bb_width)
                return signal

            # 條件 2: 價格觸及下軌
            if bb_lower is not None and close_price <= bb_lower:
                signal = StrategySignal(
                    timestamp=date,
                    action=SignalAction.SELL,
                    quantity=self.state.total_shares,
                    price=open_price,
                    reason=f"價格觸及下軌（收盤 {close_price:,.0f} <= BB下軌 {bb_lower:,.0f}）",
                )
                self.in_squeeze = False
                self._update_prev_width(bb_width)
                return signal

        # === 檢查買入條件 ===
        if self.state.positions == 0 and bb_width is not None:
            # 計算當前帶寬百分位
            percentile = self._get_bb_width_percentile(bb_width)

            if percentile is not None:
                # 條件 1: 帶寬收縮至設定百分位以下（進入壓縮）
                if percentile <= self.config["squeeze_percentile"]:
                    self.in_squeeze = True
                    log.debug(f"進入壓縮狀態: 帶寬百分位 {percentile:.1f}%")

                # 條件 2 & 3: 壓縮中 + 帶寬開始擴張 + 突破上軌
                if self.in_squeeze:
                    is_expanding = self._is_expanding(bb_width)
                    breaks_upper = bb_upper is not None and close_price > bb_upper

                    if is_expanding and breaks_upper:
                        buy_shares = self._calculate_buy_quantity(open_price)
                        if buy_shares > 0:
                            signal = StrategySignal(
                                timestamp=date,
                                action=SignalAction.BUY,
                                quantity=buy_shares,
                                price=open_price,
                                reason=f"布林壓縮突破（帶寬擴張 + 突破上軌 {bb_upper:,.0f}）",
                            )
                            self.in_squeeze = False  # 已突破，重置壓縮狀態

        # 更新前一日帶寬
        self._update_prev_width(bb_width)

        return signal

    def _update_prev_width(self, bb_width: float | None) -> None:
        """更新前一日帶寬。"""
        self.prev_bb_width = bb_width

    def get_config_schema(self) -> dict[str, Any]:
        """取得配置結構。"""
        return {
            "squeeze_percentile": {
                "type": "int",
                "default": 20,
                "description": "壓縮判定百分位（低於此百分位視為壓縮）",
            },
            "lookback_period": {
                "type": "int",
                "default": 20,
                "description": "帶寬歷史回顧期間",
            },
            "position_size_pct": {
                "type": "float",
                "default": 0.2,
                "description": "每次買入資金比例（20%）",
            },
        }

    def get_status(self) -> str:
        """取得策略狀態。"""
        if not self.state:
            return "策略尚未初始化"

        squeeze_status = "壓縮中" if self.in_squeeze else "正常"
        data_points = len(self.bb_width_history)

        return f"""
=== 布林壓縮策略：{self.ticker} ===

【當前狀態】
持倉：{self.state.positions} 份（{self.state.total_shares:,} 股）
平均成本：NT$ {self.state.avg_cost:,.0f}
可用資金：NT$ {self.state.cash:,.0f}
壓縮狀態：{squeeze_status}
歷史數據點：{data_points}

【進場條件】
✓ 帶寬 < 歷史 {self.config['squeeze_percentile']}% 百分位（壓縮偵測）
✓ 帶寬開始擴張
✓ 收盤價突破布林上軌

【出場條件】
✓ 價格回歸中軌
✓ 價格觸及下軌
"""
