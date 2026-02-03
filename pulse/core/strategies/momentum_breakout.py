"""動量突破交易策略。

進場條件 (全部滿足):
- ADX > 25 (強趨勢)
- MACD 黃金交叉 (MACD 上穿信號線)
- 成交量 > 20日均量 × 1.5

出場條件 (任一觸發):
- ADX < 20 (趨勢轉弱)
- MACD 死亡交叉
- 移動停利 15%
"""

from typing import Any

from pulse.core.strategies.base import BaseStrategy, SignalAction, StrategySignal, StrategyState
from pulse.utils.logger import get_logger

log = get_logger(__name__)


class MomentumBreakoutStrategy(BaseStrategy):
    """動量突破策略實作。"""

    def __init__(self):
        super().__init__(
            name="動量突破策略",
            description="ADX 強趨勢 + MACD 黃金交叉 + 成交量確認的動量突破策略",
        )
        self.ticker = ""
        self.prev_macd = None  # 前一日 MACD
        self.prev_macd_signal = None  # 前一日 MACD Signal
        self.entry_price = 0.0  # 進場價格
        self.peak_price = 0.0  # 波段最高點

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
            "adx_entry_threshold": config.get("adx_entry_threshold", 25),
            "adx_exit_threshold": config.get("adx_exit_threshold", 20),
            "volume_multiplier": config.get("volume_multiplier", 1.5),
            "trailing_stop_pct": config.get("trailing_stop_pct", 0.15),
            "position_size_pct": config.get("position_size_pct", 0.1),  # 每次買入資金比例
        }

        self.state = StrategyState(cash=initial_cash, total_capital=initial_cash)
        self.prev_macd = None
        self.prev_macd_signal = None
        self.entry_price = 0.0
        self.peak_price = 0.0

        log.info(f"Initialized MomentumBreakoutStrategy for {ticker}")
        log.info(f"Config: {self.config}")

    def _is_macd_golden_cross(
        self, macd: float | None, macd_signal: float | None
    ) -> bool:
        """檢查 MACD 是否為黃金交叉。

        黃金交叉: MACD 從下方穿越 Signal 線
        """
        if macd is None or macd_signal is None:
            return False
        if self.prev_macd is None or self.prev_macd_signal is None:
            return False

        # 前一日 MACD < Signal，今日 MACD >= Signal
        return self.prev_macd < self.prev_macd_signal and macd >= macd_signal

    def _is_macd_death_cross(
        self, macd: float | None, macd_signal: float | None
    ) -> bool:
        """檢查 MACD 是否為死亡交叉。

        死亡交叉: MACD 從上方穿越 Signal 線
        """
        if macd is None or macd_signal is None:
            return False
        if self.prev_macd is None or self.prev_macd_signal is None:
            return False

        # 前一日 MACD >= Signal，今日 MACD < Signal
        return self.prev_macd >= self.prev_macd_signal and macd < macd_signal

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
            indicators: 技術指標 {adx, macd, macd_signal, volume_sma_20, ...}

        Returns:
            交易訊號或 None
        """
        if not self.state:
            log.warning("Strategy not initialized")
            return None

        close_price = bar["close"]
        open_price = bar["open"]
        date = bar["date"]
        volume = bar.get("volume", 0)

        # 取得指標
        adx = indicators.get("adx")
        macd = indicators.get("macd")
        macd_signal = indicators.get("macd_signal")
        volume_sma_20 = indicators.get("volume_sma_20")

        # 更新波段最高點
        if self.state.positions > 0 and close_price > self.peak_price:
            self.peak_price = close_price

        signal = None

        # === 檢查賣出條件 ===
        if self.state.positions > 0:
            # 1. 移動停利：從波段最高點回落 trailing_stop_pct
            if self.peak_price > 0:
                stop_price = self.peak_price * (1 - self.config["trailing_stop_pct"])
                if close_price <= stop_price:
                    signal = StrategySignal(
                        timestamp=date,
                        action=SignalAction.SELL,
                        quantity=self.state.total_shares,
                        price=open_price,
                        reason=f"移動停利觸發（從高點 {self.peak_price:,.0f} 回落 {self.config['trailing_stop_pct']*100:.0f}%）",
                    )
                    self._reset_state()
                    self._update_prev_macd(macd, macd_signal)
                    return signal

            # 2. ADX 趨勢轉弱
            if adx is not None and adx < self.config["adx_exit_threshold"]:
                signal = StrategySignal(
                    timestamp=date,
                    action=SignalAction.SELL,
                    quantity=self.state.total_shares,
                    price=open_price,
                    reason=f"ADX 趨勢轉弱（ADX {adx:.1f} < {self.config['adx_exit_threshold']}）",
                )
                self._reset_state()
                self._update_prev_macd(macd, macd_signal)
                return signal

            # 3. MACD 死亡交叉
            if self._is_macd_death_cross(macd, macd_signal):
                signal = StrategySignal(
                    timestamp=date,
                    action=SignalAction.SELL,
                    quantity=self.state.total_shares,
                    price=open_price,
                    reason=f"MACD 死亡交叉（MACD {macd:.2f} 下穿 Signal {macd_signal:.2f}）",
                )
                self._reset_state()
                self._update_prev_macd(macd, macd_signal)
                return signal

        # === 檢查買入條件 ===
        if self.state.positions == 0:
            # 條件 1: ADX > 25 (強趨勢)
            adx_ok = adx is not None and adx > self.config["adx_entry_threshold"]

            # 條件 2: MACD 黃金交叉
            macd_cross_ok = self._is_macd_golden_cross(macd, macd_signal)

            # 條件 3: 成交量 > 20日均量 × 1.5
            volume_ok = (
                volume_sma_20 is not None
                and volume > volume_sma_20 * self.config["volume_multiplier"]
            )

            # 三個條件都滿足才進場
            if adx_ok and macd_cross_ok and volume_ok:
                buy_shares = self._calculate_buy_quantity(open_price)
                if buy_shares > 0:
                    self.entry_price = open_price
                    self.peak_price = open_price
                    signal = StrategySignal(
                        timestamp=date,
                        action=SignalAction.BUY,
                        quantity=buy_shares,
                        price=open_price,
                        reason=f"動量突破進場（ADX {adx:.1f}, MACD 黃金交叉, 成交量 {volume/volume_sma_20:.1f}x）",
                    )

        # 更新前一日 MACD 值
        self._update_prev_macd(macd, macd_signal)

        return signal

    def _update_prev_macd(
        self, macd: float | None, macd_signal: float | None
    ) -> None:
        """更新前一日 MACD 值。"""
        self.prev_macd = macd
        self.prev_macd_signal = macd_signal

    def _reset_state(self) -> None:
        """重置策略狀態（賣出後）。"""
        self.entry_price = 0.0
        self.peak_price = 0.0

    def get_config_schema(self) -> dict[str, Any]:
        """取得配置結構。"""
        return {
            "adx_entry_threshold": {
                "type": "float",
                "default": 25,
                "description": "ADX 進場門檻（強趨勢）",
            },
            "adx_exit_threshold": {
                "type": "float",
                "default": 20,
                "description": "ADX 出場門檻（趨勢轉弱）",
            },
            "volume_multiplier": {
                "type": "float",
                "default": 1.5,
                "description": "成交量倍數（相對 20 日均量）",
            },
            "trailing_stop_pct": {
                "type": "float",
                "default": 0.15,
                "description": "移動停利回撤比例（15%）",
            },
            "position_size_pct": {
                "type": "float",
                "default": 0.1,
                "description": "每次買入資金比例（10%）",
            },
        }

    def get_status(self) -> str:
        """取得策略狀態。"""
        if not self.state:
            return "策略尚未初始化"

        return f"""
=== 動量突破策略：{self.ticker} ===

【當前狀態】
持倉：{self.state.positions} 份（{self.state.total_shares:,} 股）
進場價：NT$ {self.entry_price:,.0f}
波段最高：NT$ {self.peak_price:,.0f}
可用資金：NT$ {self.state.cash:,.0f}

【進場條件】
✓ ADX > {self.config['adx_entry_threshold']}（強趨勢）
✓ MACD 黃金交叉
✓ 成交量 > 20日均量 × {self.config['volume_multiplier']}

【出場條件】
✓ ADX < {self.config['adx_exit_threshold']}（趨勢轉弱）
✓ MACD 死亡交叉
✓ 移動停利 {self.config['trailing_stop_pct']*100:.0f}%
"""
