"""策略模組初始化。

自動導入並註冊所有可用的策略。
"""

from pulse.core.strategies.base import BaseStrategy, SignalAction, StrategySignal, StrategyState
from pulse.core.strategies.registry import registry

# 導入策略實作並自動註冊
from pulse.core.strategies.farmer_planting import FarmerPlantingStrategy
from pulse.core.strategies.momentum_breakout import MomentumBreakoutStrategy
from pulse.core.strategies.ma_crossover import MACrossoverStrategy
from pulse.core.strategies.bb_squeeze import BBSqueezeStrategy

# Note: HappyLinesStrategy is a screening strategy (not backtesting),
# so it's not registered here. It's used via the screener or CLI commands.

registry.register(FarmerPlantingStrategy)
registry.register(MomentumBreakoutStrategy)
registry.register(MACrossoverStrategy)
registry.register(BBSqueezeStrategy)

__all__ = [
    "BaseStrategy",
    "StrategySignal",
    "StrategyState",
    "SignalAction",
    "registry",
    "MomentumBreakoutStrategy",
    "MACrossoverStrategy",
    "BBSqueezeStrategy",
    # HappyLinesStrategy is available for import directly from its module
]
