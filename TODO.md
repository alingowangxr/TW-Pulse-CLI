# TW-Pulse-CLI Roadmap - 未來改進計劃

> **版本**: v0.3.1
> **最後更新**: 2026-02-03

---

## 版本 v0.3.1 - 三大交易策略 (2026-02-03)

### ✅ 已完成

#### 技術指標擴充

- [x] **技術分析指標擴充** ✅ v0.3.1
  - `EMA_9`, `EMA_21` 用於均線交叉策略
  - `Volume_SMA_20` 用於成交量確認
  - `ADX` 向量化計算 (`_calculate_adx_series()`)
  - `BB_width` 布林帶寬用於壓縮偵測

#### 回測引擎擴充

- [x] **指標傳遞擴充** ✅ v0.3.1
  - 新增 `macd`, `macd_signal`, `adx` 指標
  - 新增 `ema_9`, `ema_21` 指標
  - 新增 `bb_upper`, `bb_middle`, `bb_lower`, `bb_width` 指標
  - 新增 `volume_sma_20` 指標

#### 三大交易策略

- [x] **動量突破策略 (Momentum Breakout)** ✅ v0.3.1
  - 進場: ADX > 25 + MACD 黃金交叉 + 成交量 > 1.5x 均量
  - 出場: ADX < 20 / MACD 死亡交叉 / 移動停利 15%
  - 完整單元測試 (12 tests)

- [x] **均線交叉策略 (MA Crossover)** ✅ v0.3.1
  - 進場: EMA9 上穿 EMA21 + 收盤 > MA50
  - 出場: EMA9 下穿 EMA21 / 收盤 < MA50
  - 完整單元測試 (15 tests)

- [x] **布林壓縮策略 (BB Squeeze)** ✅ v0.3.1
  - 進場: 帶寬 < 20% 百分位 + 擴張 + 突破上軌
  - 出場: 價格回歸中軌 / 觸及下軌
  - 完整單元測試 (15 tests)

#### 測試覆蓋

- [x] **策略單元測試** ✅ 63 tests passed (新增 42 tests)
  - `test_momentum_breakout.py` - 動量突破策略測試 (12 tests)
  - `test_ma_crossover.py` - 均線交叉策略測試 (15 tests)
  - `test_bb_squeeze.py` - 布林壓縮策略測試 (15 tests)

---

## 版本 v0.2.1 - 技術指標擴充 (2026-01-22)

### ✅ 已完成

#### Keltner Channel 指標

- [x] **肯特納通道指標** ✅ v0.2.1
  - `_calculate_keltner_channel()` 計算方法
  - `kc_middle`, `kc_upper`, `kc_lower` 模型欄位
  - 預設參數: EMA(20), ATR(10), 倍數(2.0)

#### Keltner Channel 策略

- [x] **Keltner Channel 突破策略** ✅ v0.2.1
  - 完整策略模組 (`pulse/core/strategies/keltner_channel_strategy.py`)
  - 四種信號類型: BUY, HOLD, SELL, WATCH
  - 策略條件:
    - 買進: 價格 >= 肯特納上軌 + EMA 多頭排列 + 成交量充足
    - 持有: 價格在中軌與上軌之間
    - 賣出: 價格跌破中軌
  - 最小成交量濾網: 3,000,000 股
  - EMA 多頭排列確認: EMA 9 > EMA 21 > EMA 55

- [x] **選股器整合** ✅ v0.2.1
  - `ScreenPreset.KELTNER_BREAKOUT` - 突破型篩選
  - `ScreenPreset.KELTNER_HOLD` - 持有型篩選
  - 新增篩選條件: `kc_above_upper`, `kc_above_middle`, `kc_ema_bullish`, `volume_min`

#### 測試覆蓋

- [x] **技術分析測試** ✅ 29 tests passed
  - `test_keltner_channel_calculation` - Keltner Channel 計算測試
- [x] **策略單元測試** ✅ 21 tests passed
  - `TestKeltnerStrategyResult` - 結果模型測試
  - `TestKeltnerChannelStrategy` - 策略邏輯測試
  - `TestScreenKeltnerBreakout` - 快速篩選測試

---

## 版本 v0.2.0 - 測試覆蓋與 SAPTA 增強

### 測試覆蓋 (目標: 80%+)

- [x] **端到端測試 (E2E)** ✅ v0.2.0
  - CLI 命令完整流程測試 (22 new tests)
  - TUI 交互測試 (existing)
  - 數據流完整測試 (22 new tests)
  - **總測試數: 461 tests (v0.1.8: 439 tests)**

### SAPTA 引擎增強

- [x] **模型重新訓練** ✅ v0.2.0
  - `/sapta-retrain` CLI command (新增)
  - `/sapta-retrain --status` 查看模型狀態
  - `/sapta-retrain --walk-forward` walk-forward 驗證
  - `/sapta-retrain --stocks=200` 自訂股票數量

- [x] **優化特徵工程** ✅ v0.2.0
  - **Feature Importance 分析** (`pulse/core/sapta/ml/feature_analysis.py`)
  - `/sapta-retrain --report` 顯示特徵重要性排名
  - `/sapta-retrain --thresholds` 閾值分析與建議
  - 調整閾值參數 (PRE-MARKUP >= 46.3, SIAP >= 23.8, WATCHLIST >= 10.2)

---

## 技術指標總覽 (v0.2.1)

### 波動性指標

| 指標 | 狀態 | 說明 |
|------|------|------|
| 布林通道 (Bollinger Bands) | ✅ | 標準差通道 |
| **肯特納通道 (Keltner Channel)** | ✅ **新增** | EMA + ATR 通道 |
| ATR | ✅ | 平均真實波幅 |

### 趨勢指標

| 指標 | 狀態 | 說明 |
|------|------|------|
| SMA (20, 50, 200) | ✅ | 簡單移動平均線 |
| EMA (9, 21, 55) | ✅ | 指數移動平均線 |
| Ichimoku Cloud | ✅ | 一目均衡表 |

### 動量指標

| 指標 | 狀態 | 說明 |
|------|------|------|
| RSI (14) | ✅ | 相對強弱指標 |
| MACD | ✅ | 指數平滑異同移動平均線 |
| Stochastic | ✅ | 隨機指標 |
| ADX | ✅ | 平均方向指數 |
| CCI | ✅ | 商品通道指數 |

### 成交量指標

| 指標 | 狀態 | 說明 |
|------|------|------|
| OBV | ✅ | 能量潮 |
| MFI | ✅ | 資金流量指數 |
| Volume SMA | ✅ | 成交量均線 |

---

## 策略總覽 (v0.3.1)

### 回測策略

| 策略 | 狀態 | 類型 | 說明 |
|------|------|------|------|
| Farmer Planting | ✅ | 波段 | 進階農夫播種術 - 基準價加減碼策略 |
| **Momentum Breakout** | ✅ **新增** | 趨勢 | ADX 強趨勢 + MACD 黃金交叉 + 成交量確認 |
| **MA Crossover** | ✅ **新增** | 趨勢 | EMA9/EMA21 交叉 + MA50 趨勢過濾 |
| **BB Squeeze** | ✅ **新增** | 突破 | 布林壓縮後向上突破 |

### 選股策略

| 策略 | 狀態 | 類型 | 說明 |
|------|------|------|------|
| Smart Money Screener | ✅ | 選股 | 主力足跡選股 (Trend/Volume/Bias) |
| SAPTA Engine | ✅ | 預測 | 機器學習預漲偵測 |
| Keltner Breakout | ✅ | 短線 | 肯特納通道突破策略 |
| Keltner Hold | ✅ | 短線 | 肯特納通道持有策略 |

### Keltner Channel 策略參數

```python
# 預設參數
min_avg_volume = 3_000_000  # 最小日均成交量
ema_periods = (9, 21, 55)   # EMA 週期
atr_multiplier = 2.0        # ATR 倍數
atr_period = 10             # ATR 週期
rebalance_frequency = "biweekly"  # 換股頻率
```

---

## 性能優化

- [x] **並發處理優化** ✅ v0.1.9
  - 大規模篩選使用 `asyncio.gather` 並發下載 (已有)
  - 減少單線程阻塞 (已有)
- [x] **緩存優化** ✅ v0.1.9
  - diskcache TTL 參數調優 (新增特定數據類型TTL)
  - 熱數據預加載策略 (新增 cache_warmup 和 preload_hot_data)
- [x] **進度條改進** ✅ v0.1.10
  - Rich 進度條顯示優化 (screener 批量篩選)
  - 實時狀態回饋 (批次更新)

---

## 數據穩定性

- [x] **API 配額監控** ✅ v0.1.10
  - FinMind API 配額監控 (request_count, quota_limit)
  - 優雅降級策略 (現有)
  - 配額狀態 API: `get_quota_status()`, `set_quota_limit()`

---

## 代碼品質

- [x] **清理未使用代碼** ✅ v0.2.0
  - 移除未引用的 imports (5 個: functools.partial, MLModelInfo, train_model.main, subprocess, typing.Any)
  - 刪除 dead code (2 個: generate_chart 變數, min_periods 變數)
  - 優化依賴項 (ruff 檢查通過)
- [x] **API 文檔完善** ✅ v0.2.0
  - 所有公共函數添加完整 docstrings
  - 類型標註補充 (ChartConfig, ChartTheme, feature_analysis)

---

## 未來版本規劃

### v0.3.0 - 回測與策略 ✅ 已完成

- [x] **回測框架** ✅ v0.3.0
  - 歷史模擬交易
  - 信號回測驗證
- [x] **策略建構器** ✅ v0.3.1
  - 自訂進場/出场規則
  - 4 種內建策略 (農夫播種術、動量突破、均線交叉、布林壓縮)
- [x] **績效報告** ✅ v0.3.0
  - 勝率統計
  - 最大回撤計算
  - 夏普比率

### v0.4.0+ - 擴展功能

- [ ] **即時行情支援**
  - WebSocket 實時報價
  - 價格異動即時通知
- [ ] **多市場支援**
  - 美股市場
  - 港股市場
- [ ] **加密貨幣支援**
  - BTC/ETH 等主流幣種
  - 交易所 API 整合
- [ ] **選擇權分析**
  - Greeks 計算
  - 履約價分析

---

## 文檔計劃

- [ ] **部署指南**
  - Docker 容器化
  - pip 安裝說明
- [x] **策略文檔擴充** ✅ v0.2.1
  - Keltner Channel 策略說明
  - 策略參數與使用範例

---

*最後更新: 2026-02-03 (v0.3.1 - 三大交易策略)*
