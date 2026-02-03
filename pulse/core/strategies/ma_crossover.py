"""均線交叉交易策略。

進場條件:
- EMA9 上穿 EMA21 (黃金交叉)
- 收盤價 > MA50 (趨勢過濾)

出場條件:
- EMA9 下穿 EMA21 (死亡交叉)
- 收盤價 < MA50
"""

from typing import Any

from pulse.core.strategies.base import BaseStrategy, SignalAction, StrategySignal, StrategyState
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class MACrossoverStrategy(BaseStrategy):
    """均線交叉策略實作。"""

    def __init__(self):
        super().__init__(
            name="均線交叉策略",
            description="EMA9/EMA21 交叉 + MA50 趨勢過濾的均線交叉策略",
        )
        self.ticker = ""
        self.prev_ema_fast = None  # 前一日 EMA fast
        self.prev_ema_slow = None  # 前一日 EMA slow

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
            "ema_fast": config.get("ema_fast", 9),
            "ema_slow": config.get("ema_slow", 21),
            "ma_filter": config.get("ma_filter", 50),
            "position_size_pct": config.get("position_size_pct", 0.2),  # 每次買入資金比例
        }

        self.state = StrategyState(cash=initial_cash, total_capital=initial_cash)
        self.prev_ema_fast = None
        self.prev_ema_slow = None

        log.info(f"Initialized MACrossoverStrategy for {ticker}")
        log.info(f"Config: {self.config}")

    def _is_golden_cross(
        self, ema_fast: float | None, ema_slow: float | None
    ) -> bool:
        """檢查是否為黃金交叉。

        黃金交叉: EMA fast 從下方穿越 EMA slow
        """
        if ema_fast is None or ema_slow is None:
            return False
        if self.prev_ema_fast is None or self.prev_ema_slow is None:
            return False

        # 前一日 EMA fast < EMA slow，今日 EMA fast >= EMA slow
        return self.prev_ema_fast < self.prev_ema_slow and ema_fast >= ema_slow

    def _is_death_cross(
        self, ema_fast: float | None, ema_slow: float | None
    ) -> bool:
        """檢查是否為死亡交叉。

        死亡交叉: EMA fast 從上方穿越 EMA slow
        """
        if ema_fast is None or ema_slow is None:
            return False
        if self.prev_ema_fast is None or self.prev_ema_slow is None:
            return False

        # 前一日 EMA fast >= EMA slow，今日 EMA fast < EMA slow
        return self.prev_ema_fast >= self.prev_ema_slow and ema_fast < ema_slow

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
            indicators: 技術指標 {ema_9, ema_21, ma_50, ...}

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
        ema_fast = indicators.get("ema_9")  # EMA 9
        ema_slow = indicators.get("ema_21")  # EMA 21
        ma_filter = indicators.get("ma_50")  # MA 50

        signal = None

        # === 檢查賣出條件 ===
        if self.state.positions > 0:
            # 條件 1: EMA 死亡交叉
            if self._is_death_cross(ema_fast, ema_slow):
                signal = StrategySignal(
                    timestamp=date,
                    action=SignalAction.SELL,
                    quantity=self.state.total_shares,
                    price=open_price,
                    reason=f"EMA 死亡交叉（EMA{self.config['ema_fast']} {ema_fast:.2f} 下穿 EMA{self.config['ema_slow']} {ema_slow:.2f}）",
                )
                self._update_prev_ema(ema_fast, ema_slow)
                return signal

            # 條件 2: 收盤價 < MA50
            if ma_filter is not None and close_price < ma_filter:
                signal = StrategySignal(
                    timestamp=date,
                    action=SignalAction.SELL,
                    quantity=self.state.total_shares,
                    price=open_price,
                    reason=f"跌破趨勢線（收盤 {close_price:,.0f} < MA{self.config['ma_filter']} {ma_filter:,.0f}）",
                )
                self._update_prev_ema(ema_fast, ema_slow)
                return signal

        # === 檢查買入條件 ===
        if self.state.positions == 0:
            # 條件 1: EMA 黃金交叉
            golden_cross = self._is_golden_cross(ema_fast, ema_slow)

            # 條件 2: 收盤價 > MA50（趨勢過濾）
            above_ma_filter = ma_filter is not None and close_price > ma_filter

            # 兩個條件都滿足才進場
            if golden_cross and above_ma_filter:
                buy_shares = self._calculate_buy_quantity(open_price)
                if buy_shares > 0:
                    signal = StrategySignal(
                        timestamp=date,
                        action=SignalAction.BUY,
                        quantity=buy_shares,
                        price=open_price,
                        reason=f"均線黃金交叉（EMA{self.config['ema_fast']} 上穿 EMA{self.config['ema_slow']}, > MA{self.config['ma_filter']}）",
                    )

        # 更新前一日 EMA 值
        self._update_prev_ema(ema_fast, ema_slow)

        return signal

    def _update_prev_ema(
        self, ema_fast: float | None, ema_slow: float | None
    ) -> None:
        """更新前一日 EMA 值。"""
        self.prev_ema_fast = ema_fast
        self.prev_ema_slow = ema_slow

    def get_config_schema(self) -> dict[str, Any]:
        """取得配置結構。"""
        return {
            "ema_fast": {
                "type": "int",
                "default": 9,
                "description": "快速 EMA 週期",
            },
            "ema_slow": {
                "type": "int",
                "default": 21,
                "description": "慢速 EMA 週期",
            },
            "ma_filter": {
                "type": "int",
                "default": 50,
                "description": "趨勢過濾均線週期",
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

        return f"""
=== 均線交叉策略：{self.ticker} ===

【當前狀態】
持倉：{self.state.positions} 份（{self.state.total_shares:,} 股）
平均成本：NT$ {self.state.avg_cost:,.0f}
可用資金：NT$ {self.state.cash:,.0f}

【進場條件】
✓ EMA{self.config['ema_fast']} 上穿 EMA{self.config['ema_slow']}（黃金交叉）
✓ 收盤價 > MA{self.config['ma_filter']}（趨勢過濾）

【出場條件】
✓ EMA{self.config['ema_fast']} 下穿 EMA{self.config['ema_slow']}（死亡交叉）
✓ 收盤價 < MA{self.config['ma_filter']}（跌破趨勢）
"""
