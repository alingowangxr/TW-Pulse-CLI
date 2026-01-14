# SAPTA 算法詳細文檔

> **SAPTA** (System for Analyzing Pre-markup Technical Accumulation) - 預漲技術吸籌分析系統

## 目錄

1. [系統概述](#系統概述)
2. [六大分析模組](#六大分析模組)
3. [評分系統](#評分系統)
4. [狀態分類](#狀態分類)
5. [ML 增強](#ml-增強)
6. [輸出格式](#輸出格式)

---

## 系統概述

SAPTA 是一個結合技術分析與機器學習的預漲偵測系統，用於識別股票是否處於 **主力吸籌階段** (Pre-markup Accumulation Phase)，即價格突破前的整理階段。

### 核心假設

```
主力吸籌 → 波動收縮 → 布林通道擠壓 → 突破拉升
```

### 分析流程

```
輸入: OHLCV 數據 (1年日線)
    ↓
執行 6 個分析模組
    ↓
加權彙總分數
    ↓
ML 模型校正 (可選)
    ↓
確定狀態等級
    ↓
輸出: 評分 + 狀態 + 置信度 + 訊號列表
```

---

## 六大分析模組

### 1. Supply Absorption Module (供給吸收模組)

**權重**: 25% | **最大分數**: 20

**偵測原理**: 當出現大量賣壓時，價格未能跌破支撐，表示需求正在吸收供給。

**評分項目**:

| 檢查項目 | 分數 | 說明 |
|---------|------|------|
| 量能吸收 | +8 | 大量賣出但價格撐住 |
| 底部墊高 | +6 | 連續出現 higher lows |
| 收盤強度 | +6 | 收盤價位於K線上半部 |
| 分配警示 | -4 | 出現 distribution candles |

**關鍵指標**:

```python
volume_spike_ratio = current_volume / avg_volume_50
price_held_after_spike = subsequent_low >= spike_low * 0.99
close_strength = (close - low) / (high - low)
```

**訊號範例**:
- "Volume spike 2.5x absorbed, price held"
- "Higher lows forming (4 consecutive)"
- "Strong closes (75% avg)"

---

### 2. Compression Module (波動收縮模組)

**權重**: 20% | **最大分數**: 20

**偵測原理**: 波動逐漸收窄形成整理區間，準備突破。

**評分項目**:

| 檢查項目 | 分數 | 說明 |
|---------|------|------|
| 波動收窄 | +10 | ATR 或價格範圍顯著下降 |
| 區間收斂 | +6 | High-Low 區間持續縮小 |
| 低波動確認 | +4 | 維持低波動狀態 N 天 |

**關鍵指標**:

```python
atr_current = atr.tail(14).iloc[-1]
atr_average = atr.rolling(50).mean().iloc[-1]
atr_ratio = atr_current / atr_average

range_current = high - low
range_average = (high - low).rolling(20).mean().iloc[-1]
```

**狀態判定**:

| 條件 | 狀態 |
|-----|------|
| ATR < 50% 平均 | 收縮中 |
| 區間 < 20日平均 60% | 高度收縮 |
| 持續 10+ 天 | 成熟整理 |

---

### 3. BB Squeeze Module (布林通道擠壓模組)

**權重**: 15% | **最大分數**: 15

**偵測原理**: 布林通道上下軌收窄，表示波動即將擴大。

**評分項目**:

| 檢查項目 | 分數 | 說明 |
|---------|------|------|
| 擠壓偵測 | +8 | BB 寬度 < 20日低點 |
| 接近下軌 | +4 | 價格接近布林下軌 |
| 支撐確認 | +3 | 下軌/中軌提供支撐 |

**關鍵指標**:

```python
bb_width = (upper_band - lower_band) / middle_band
bb_squeeze = bb_width < bb_width.rolling(20).min()
```

**交易意涵**:

```
BB 擠壓 → 價格即將突破
突破方向: 向上/向下 取決於整體趨勢
```

---

### 4. Elliott Wave Module (艾略特波浪模組)

**權重**: 15% | **最大分數**: 15

**偵測原理**: 識別波浪位置，處於 Wave 3-5 是最佳買入時機。

**評分項目**:

| 檢查項目 | 分數 | 說明 |
|---------|------|------|
| Wave 3 | +15 | 推進浪第三波 |
| Wave 5 | +12 | 推進浪第五波 |
| Wave C | +10 | 調整浪C波 (末期) |
| 回撤確認 | +5 | 符合 Fibonacci 回撤 |

**波浪識別**:

```python
# 簡易波浪識別
if wave_3_conditions:
    wave_phase = "Wave 3 (Impulse)"
elif wave_5_conditions:
    wave_phase = "Wave 5 (Ending)"
elif corrective_pattern:
    wave_phase = "Wave C (Correction)"
```

**Fibonacci 關鍵位**:

| 回撤比例 | 意義 |
|---------|------|
| 38.2% | 淺層回撤，強勢上漲 |
| 50.0% | 中性回撤 |
| 61.8% | 深層回撤，可能形成雙底 |

---

### 5. Time Projection Module (時間投影模組)

**權重**: 15% | **最大分數**: 15

**偵測原理**: 基於 Fibonacci 時間窗口預測潛在突破時機。

**評分項目**:

| 檢查項目 | 分數 | 說明 |
|---------|------|------|
| 時間窗口 | +8 | 接近 Fib 時間目標 |
| 循環週期 | +4 | 符合歷史週期 |
| 近日轉折 | +3 | 3-5 日內可能轉折 |

**計算方法**:

```python
# 從低點開始的天數
days_since_low = (current_date - significant_low_date).days

# Fib 時間目標
fib_targets = [21, 34, 55, 89, 144]

# 檢查是否接近任一目標
nearest_fib = min([t for t in fib_targets if t >= days_since_low])
days_to_window = nearest_fib - days_since_low
```

**行星相位 (可選)**:
- 月相周期 (~29.5天)
- 年度季節性效應

---

### 6. Anti-Distribution Module (反派發模組)

**權重**: 10% | **最大分數**: 10

**偵測原理**: 過濾出貨模式，避免買入主力正在派發的股票。

**檢查項目**:

| 類型 | 分數 | 說明 |
|-----|------|------|
| 派發確認 | -8 | 高量+弱收盤 (Distribution) |
| 假突破 | -5 | 突破後迅速拉回 |
| 量價背離 | -4 | 上漲但量能萎縮 |

**訊號**:

```python
# Distribution candle
is_distribution = (
    volume > avg_volume * 1.5 and
    close < low + (high - low) * 0.3
)

# False breakout
is_false_breakout = (
    price_breaks_high and
    volume < breakout_volume * 0.5
)
```

---

## 評分系統

### 權重配置

```python
weights = {
    "absorption": 25,      # 最重要
    "compression": 20,     # 重要
    "bb_squeeze": 15,      # 中等
    "elliott": 15,         # 中等
    "time_projection": 15, # 輔助
    "anti_distribution": 10, # 過濾器
}
```

### 分數計算

```
Weighted_Score = Σ (module_score × module_weight) / Σ (max_score × module_weight) × 100
```

### 評分範例

```
Module Breakdown:
  [+] Absorption: 18.0/25
  [+] Compression: 16.0/20
  [+] BB Squeeze: 12.0/15
  [+] Elliott: 10.5/15
  [-] Time Projection: 5.5/15
  [+] Anti-Distribution: 0.0/10

Total: 62.0/100 → PRE-MARKUP
```

---

## 狀態分類

| 狀態 | 分數範圍 | 意義 | 操作建議 |
|-----|---------|------|---------|
| **PRE-MARKUP** | ≥ 80 | 準備突破 | 積極買入 |
| **SIAP** | 65-79 | 接近就緒 | 密切監控 |
| **WATCHLIST** | 50-64 | 觀察名單 | 列入關注 |
| **ABAIKAN** | < 50 | 跳過 | 暫時觀望 |

### 置信度調整

```python
# 多模組確認時提升置信度
if active_modules >= 5:
    confidence = "HIGH"
elif active_modules >= 4:
    confidence = "MEDIUM"
else:
    confidence = "LOW"
```

### ML 置信度

```python
ml_probability = model.predict_proba([features])[0][1]

if ml_probability >= 0.7:
    confidence = "HIGH"
elif ml_probability >= 0.5:
    confidence = "MEDIUM"
else:
    confidence = "LOW"
```

---

## ML 增強

### 特徵提取

從每個模組提取 10+ 特徵，總計 60+ 維度：

```python
features = {
    # Absorption
    "absorption_volume_spike_ratio": 2.5,
    "absorption_price_held_after_spike": True,
    "absorption_higher_lows_count": 4,
    "absorption_avg_close_strength": 0.75,
    # Compression
    "compression_atr_ratio": 0.45,
    "compression_days_low_volatility": 12,
    # ... 更多特徵
}
```

### 模型選擇

**主要**: XGBoost Classifier
**備用**: sklearn GradientBoostingClassifier

### 訓練方法

**Walk-forward Training**:

```
TRAIN: 36 個月 → TEST: 6 個月
         ↓
TRAIN: +6 個月 → TEST: 6 個月
         ↓
... 重複滾動 ...
```

### 門檻學習

從模型預測概率自動學習最佳門檻：

| 狀態 | 百分位 |
|-----|--------|
| PRE-MARKUP | Top 10% |
| SIAP | Top 25% |
| WATCHLIST | Top 50% |

---

## 輸出格式

### 單股分析結果

```json
{
    "ticker": "2330",
    "final_score": 72.5,
    "status": "SIAP",
    "confidence": "MEDIUM",
    "wave_phase": "Wave 3 (Impulse)",
    "fib_retracement": 0.618,
    "projected_breakout_window": "5-8 days",
    "days_to_window": 3,
    "notes": [
        "Volume spike 2.1x absorbed, price held",
        "Higher lows forming (4 consecutive)",
        "Strong closes (72% avg)",
        "BB squeeze active",
        "Near Fib time window"
    ],
    "modules": {
        "absorption": {"score": 18.0, "status": true},
        "compression": {"score": 16.0, "status": true},
        "bb_squeeze": {"score": 12.0, "status": true},
        "elliott": {"score": 10.5, "status": true},
        "time_projection": {"score": 6.0, "status": true},
        "anti_distribution": {"score": 8.0, "status": true}
    }
}
```

### 掃描結果表

```
SAPTA Scan: TW50 (15 found)
============================================================
Ticker    Status        Score    Confidence    Wave
------------------------------------------------------------
2330      PRE-MARKUP    82.5     HIGH          Wave 3
2454      PRE-MARKUP    78.2     HIGH          Wave 3
2303      SIAP          71.0     MEDIUM        Wave C
2881      SIAP          68.5     MEDIUM        Wave 4
...
------------------------------------------------------------
Total: 15 stocks
```

---

## 使用範例

### 命令列使用

```bash
# 單股分析
/sapta 2330

# 詳細分析 (含模組分解)
/sapta 2330 --detailed

# 掃描預漲股
/sapta scan tw50
/sapta scan popular
/sapta scan all
```

### API 使用

```python
from pulse.core.sapta import SaptaEngine, SaptaStatus

# 初始化引擎
engine = SaptaEngine()

# 單股分析
result = await engine.analyze("2330")

if result.status == SaptaStatus.PRE_MARKUP:
    print(f"買入訊號! Score: {result.final_score}")
    print(f"Wave: {result.wave_phase}")
    print(f"預測窗口: {result.days_to_window} 天")

# 批量掃描
results = await engine.scan(
    tickers=["2330", "2454", "2303", "2881"],
    min_status=SaptaStatus.SIAP
)

for r in results:
    print(f"{r.ticker}: {r.status.value} ({r.final_score:.1f})")
```

---

## 限制與注意事項

1. **數據需求**: 至少需要 100 天歷史數據
2. **適用市場**: 流動性較好的股票
3. **輔助工具**: 應結合基本面分析
4. **風險管理**: 設定止損，不 All-in
5. **模型更新**: 建議每季重新訓練模型

---

## 參考資料

- [官方 README](../../README.md)
- [模型訓練指南](training_guide.md)
- [系統架構文檔](architecture.md)
