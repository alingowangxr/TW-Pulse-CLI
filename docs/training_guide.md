# SAPTA 模型訓練指南

> **SAPTA** (System for Analyzing Pre-markup Technical Accumulation) - 機器學習模型訓練文檔

## 目錄

1. [訓練概述](#訓練概述)
2. [數據準備](#數據準備)
3. [標籤生成](#標籤生成)
4. [特徵提取](#特徵提取)
5. [訓練方法](#訓練方法)
6. [門檻學習](#門檻學習)
7. [模型評估](#模型評估)
8. [部署模型](#部署模型)
9. [常見問題](#常見問題)

---

## 訓練概述

### 訓練流程

```
歷史價格數據 (yfinance)
        ↓
    SAPTA 分析 (6 個模組)
        ↓
    特徵提取 (60+ 特徵)
        ↓
    標籤生成 (未來報酬率)
        ↓
    訓練模型 (XGBoost)
        ↓
    門檻學習 (自動調整)
        ↓
    部署 (sapta_model.pkl + thresholds.json)
```

### 訓練目標

| 目標 | 說明 |
|-----|------|
| **目標報酬率** | 10% (可調整) |
| **達成天數** | 20 個交易日 (可調整) |
| **模型類型** | XGBoost Classifier (GradientBoosting fallback) |
| **評估指標** | Accuracy, Precision, Recall, F1, AUC-ROC |

---

## 數據準備

### 數據來源

```python
# 股票清單: data/tickers.json (約 955 檔台股)
# 價格數據: yfinance (live API)

from pulse.core.sapta.ml.data_loader import SaptaDataLoader

loader = SaptaDataLoader()

# 獲取所有股票代號
tickers = loader.get_all_tickers()  # ~955 檔

# 加載歷史數據 (2年)
stock_data = loader.get_multiple_stocks(
    tickers=tickers,
    period="2y",
    min_rows=120  # 最少 120 天數據
)
```

### 數據需求

| 項目 | 需求 |
|-----|------|
| **最少歷史天數** | 120 天 |
| **建議訓練期間** | 2-3 年 |
| **最少樣本數** | 100 筆 |
| **數據頻率** | 日線 (D) |

### 數據品質檢查

```python
def validate_data(df: pd.DataFrame) -> bool:
    """驗證數據品質"""
    # 1. 檢查缺失值
    if df.isnull().sum().sum() > len(df) * 0.05:
        return False
    
    # 2. 檢查數據長度
    if len(df) < 120:
        return False
    
    # 3. 檢查價格連續性
    if (df['close'] == 0).any():
        return False
    
    # 4. 檢查成交量
    if (df['volume'] == 0).any():
        return False
    
    return True
```

---

## 標籤生成

### 標籤邏輯

```python
from pulse.core.sapta.ml.labeling import SaptaLabeler

labeler = SaptaLabeler(
    target_gain_pct=10.0,   # 目標報酬率 10%
    target_days=20,          # 20 個交易日內達成
)

# 標籤價格序列
labeled_df = labeler.label_price_series(df)
```

### 標籤結果

| 欄位 | 說明 |
|-----|------|
| `forward_return` | 持有 target_days 的報酬率 |
| `max_forward_return` | 期間內最大報酬率 |
| `hit_target` | 1 = 達成目標, 0 = 未達成 |
| `days_to_target` | 達成目標的天數 (未達成為 NaN) |

### LabeledSample 結構

```python
@dataclass
class LabeledSample:
    ticker: str           # 股票代號
    date: date           # 分析日期
    features: dict       # 特徵字典
    label: int           # 1 = 達成目標, 0 = 未達成
    forward_return: float  # 實際報酬率
    max_return: float      # 期間最大報酬率
    days_to_target: int | None  # 達成天數
```

### 樣本統計

```python
# 計算標籤統計
stats = labeler.calculate_statistics(samples)

# 輸出範例:
{
    "total_samples": 5000,
    "positive_samples": 1200,  # 達成目標
    "negative_samples": 3800,  # 未達成目標
    "hit_rate": 24.0%,         # 命中率
    "avg_forward_return": 5.2%,
    "avg_max_return": 8.5%,
    "avg_days_to_target": 8,
}
```

---

## 特徵提取

### 特徵列表

SAPTA 提取 **60+ 維度** 特徵，分為 6 個模組：

| 模組 | 特徵數 | 範例 |
|-----|-------|------|
| **Absorption** | 10+ | volume_spike_ratio, price_held, higher_lows |
| **Compression** | 10+ | atr_slope, range_contraction, days_low_vol |
| **BB Squeeze** | 10+ | bb_width_percentile, squeeze_duration |
| **Elliott Wave** | 10+ | fib_retracement, wave_phase, trend_context |
| **Time Projection** | 10+ | days_since_low, fib_window, lunar_phase |
| **Anti-Distribution** | 10+ | distribution_candles, false_breakout |
| **Aggregate** | 5+ | total_score, weighted_score, modules_active |

### 特徵提取示例

```python
from pulse.core.sapta.ml.features import SaptaFeatureExtractor

extractor = SaptaFeatureExtractor()

# 從 SAPTA 結果提取特徵
features = extractor.extract_from_result(result)

# 或從模組分數提取
features = extractor.extract_from_scores(module_scores)

# 轉換為向量
feature_vector = extractor.to_vector(features)

# 轉換為 DataFrame
feature_df = extractor.to_dataframe([features])
```

### 重要特徵 (Top 10)

```python
# 依 feature_importances_ 排序
IMPORTANT_FEATURES = [
    "absorption_score",
    "compression_atr_slope",
    "bb_squeeze_bb_width_percentile",
    "total_score",
    "weighted_score",
    "elliott_fib_retracement",
    "absorption_volume_spike_ratio",
    "compression_range_contraction",
    "modules_active",
    "anti_distribution_score",
]
```

---

## 訓練方法

### 方法 1: 簡單分割訓練

```python
from pulse.core.sapta.ml.trainer import SaptaTrainer

trainer = SaptaTrainer()

# 簡單訓練 (80/20 分割)
result = trainer.train(
    samples=labeled_samples,
    test_size=0.2,
)
```

**適用場景**: 快速實驗、數據量較少 (< 5000 樣本)

### 方法 2: Walk-Forward 訓練 (推薦)

```python
# Walk-forward 訓練 (滾動窗口)
result = trainer.walk_forward_train(
    samples=labeled_samples,
    train_months=36,   # 訓練 36 個月
    test_months=6,     # 測試 6 個月
)
```

**Walk-Forward 示意圖**:

```
Timeline:  [--------|--------|--------|--------|--------|--------|--------]
           0M      36M     42M     48M     54M     60M     66M     72M
           ├───────┤        Train Window 1
                    ├───────┤        Train Window 2
                             ├───────┤        Train Window 3
                                      ...
                                             └────────────────┘
                                               Final Model
```

**適用場景**: 生產環境、避免前視偏差 (look-ahead bias)

### 模型配置

```python
# XGBoost 配置
model = xgb.XGBClassifier(
    n_estimators=100,       # 樹的數量
    max_depth=6,            # 樹的最大深度
    learning_rate=0.1,      # 學習率
    objective='binary:logistic',
    eval_metric='auc',
    random_state=42,
)

# Fallback: sklearn GradientBoosting
model = GradientBoostingClassifier(
    n_estimators=100,
    max_depth=6,
    learning_rate=0.1,
    random_state=42,
)
```

---

## 門檻學習

### 自動門檻計算

```python
def _learn_thresholds(self, model, X, y) -> dict:
    """從模型預測概率學習最佳門檻"""
    probas = model.predict_proba(X)[:, 1]
    
    # 按概率排序
    sorted_indices = np.argsort(probas)[::-1]
    n = len(probas)
    
    # 門檻學習
    thresholds = {
        # PRE-MARKUP: Top 10% (高精確率)
        "pre_markup": probas[sorted_indices[int(n * 0.10)]] * 100,
        
        # SIAP: Top 25%
        "siap": probas[sorted_indices[int(n * 0.25)]] * 100,
        
        # WATCHLIST: Top 50%
        "watchlist": probas[sorted_indices[int(n * 0.50)]] * 100,
    }
    
    return thresholds
```

### 門檻對照表

| 狀態 | 百分位 | 說明 |
|-----|-------|------|
| **PRE-MARKUP** | Top 10% | 高命中率，高信心 |
| **SIAP** | Top 25% | 中等命中率，密切監控 |
| **WATCHLIST** | Top 50% | 較低命中率，觀察名單 |

### 預設門檻 (未訓練時)

| 狀態 | 分數範圍 | 意義 |
|-----|---------|------|
| **PRE-MARKUP** | ≥ 80 | 準備突破 |
| **SIAP** | 65-79 | 接近就緒 |
| **WATCHLIST** | 50-64 | 觀察名單 |
| **ABAIKAN** | < 50 | 跳過 |

---

## 模型評估

### 評估指標

```python
metrics = {
    "accuracy": 0.72,      # 正確率
    "precision": 0.68,     # 精確率
    "recall": 0.65,        # 召回率
    "f1": 0.66,            # F1 分數
    "auc_roc": 0.78,       # AUC-ROC
}
```

### 指標解讀

| 指標 | 理想值 | 說明 |
|-----|-------|------|
| **Accuracy** | > 0.70 | 整體正確率 |
| **Precision** | > 0.65 | 預測為 PRE-MARKUP 的正確率 |
| **Recall** | > 0.60 | 實際 PRE-MARKUP 被找出的比例 |
| **F1** | > 0.60 | Precision/Recall 的調和平均 |
| **AUC-ROC** | > 0.75 | 模型區分能力 |

### 特徵重要性

```python
# 從訓練結果獲取特徵重要性
feature_importance = {
    "absorption_score": 0.15,
    "compression_atr_slope": 0.12,
    "bb_squeeze_bb_width_percentile": 0.10,
    "total_score": 0.09,
    "elliott_fib_retracement": 0.08,
    # ... 更多特徵
}

# 可視化 (需額外安裝 matplotlib)
import matplotlib.pyplot as plt

plt.barh(list(feature_importance.keys())[:15], 
        list(feature_importance.values())[:15])
plt.xlabel('Importance')
plt.title('Top 15 Feature Importance')
plt.tight_layout()
plt.savefig('feature_importance.png')
```

---

## 部署模型

### 模型保存位置

```
pulse/core/sapta/data/
├── sapta_model.pkl      # 訓練好的模型
└── thresholds.json      # 學習的門檻
```

### 自動載入

```python
# SaptaEngine 會自動載入模型
engine = SaptaEngine(auto_load_model=True)

# 手動載入
engine.load_ml_model("pulse/core/sapta/data/sapta_model.pkl")
```

### 訓練並保存

```python
from pulse.core.sapta.ml.trainer import SaptaTrainer
from pulse.core.sapta.ml.data_loader import load_training_data
from pulse.core.sapta.ml.labeling import SaptaLabeler
from pulse.core.sapta.ml.features import SaptaFeatureExtractor
from pulse.core.sapta.engine import SaptaEngine
import asyncio

async def train_and_deploy():
    # 1. 加載數據
    stock_data = load_training_data(period="2y", min_rows=120)
    
    # 2. 生成特徵和標籤
    labeler = SaptaLabeler(target_gain_pct=10.0, target_days=20)
    extractor = SaptaFeatureExtractor()
    engine = SaptaEngine(auto_load_model=False)
    
    samples = []
    
    for ticker, df in stock_data.items():
        # 執行 SAPTA 分析
        result = await engine.analyze(ticker, df=df)
        
        if result:
            # 提取特徵
            features = extractor.extract_from_result(result)
            
            # 標籤樣本
            sample = labeler.label_samples(
                features_by_date={result.analyzed_at.date(): features},
                price_df=df,
                ticker=ticker,
            )
            samples.extend(sample)
    
    # 3. 訓練模型
    trainer = SaptaTrainer()
    result = trainer.walk_forward_train(samples)
    
    if result:
        print(f"模型已保存: {result.model_path}")
        print(f"門檻: {result.model_info.threshold_pre_markup}, "
              f"{result.model_info.threshold_siap}, "
              f"{result.model_info.threshold_watchlist}")
        print(f"指標: Accuracy={result.metrics['accuracy']:.2f}, "
              f"AUC={result.metrics['auc_roc']:.2f}")

# 執行訓練
asyncio.run(train_and_deploy())
```

### 命令列訓練

```bash
# 訓練模型 (需要實時數據)
python -m pulse.core.sapta.ml.train_model

# 或直接執行
python -c "
from pulse.core.sapta.ml.trainer import SaptaTrainer
trainer = SaptaTrainer()
result = trainer.train(sample_data, test_size=0.2)
print(f'Model: {result.model_path}')
print(f'Metrics: {result.metrics}')
"
```

---

## 常見問題

### Q1: 訓練樣本不足怎麼辦?

```python
# 增加訓練數據
# 方法 1: 擴展股票範圍
stock_data = loader.get_multiple_stocks(
    tickers=loader.get_all_tickers(),  # 全部 955 檔
    period="3y",                       # 擴展到 3 年
    min_rows=120,
)

# 方法 2: 降低最小樣本要求
MIN_SAMPLES = 100  # 系統預設
```

### Q2: XGBoost 安裝失敗?

```python
# 使用 sklearn Fallback
from sklearn.ensemble import GradientBoostingClassifier

# SaptaTrainer 會自動檢測並使用 sklearn
# 訓練日誌會顯示: "XGBoost not available, using sklearn GradientBoosting"
```

### Q3: 模型效果不好?

```python
# 1. 調整標籤參數
labeler = SaptaLabeler(
    target_gain_pct=15.0,   # 提高目標報酬率
    target_days=30,         # 延長達成天數
)

# 2. 增加訓練數據
stock_data = load_training_data(period="3y")

# 3. 調整模型參數
model = xgb.XGBClassifier(
    n_estimators=200,       # 增加樹的數量
    max_depth=8,            # 增加深度
    learning_rate=0.05,     # 降低學習率
)

# 4. 特徵工程
# 添加更多技術指標特徵
```

### Q4: 如何更新已部署的模型?

```python
# 定期重新訓練 (建議每季)

# 1. 收集新數據
new_data = load_training_data(period="2y")

# 2. 重新訓練
trainer = SaptaTrainer()
result = trainer.walk_forward_train(samples)

# 3. 驗證指標
if result.metrics['accuracy'] > 0.65:
    # 替換舊模型
    import shutil
    shutil.copy(result.model_path, "pulse/core/sapta/data/sapta_model.pkl")
    shutil.copy(result.thresholds_path, "pulse/core/sapta/data/thresholds.json")
    print("模型已更新!")
```

### Q5: 前視偏差 (Look-ahead Bias) 問題?

```python
# 使用 Walk-Forward 訓練避免
trainer = SaptaTrainer()
result = trainer.walk_forward_train(
    samples,
    train_months=36,   # 只用歷史數據訓練
    test_months=6,     # 用未見過的數據測試
)

# 切勿:
# - 使用未來數據訓練
# - 在同一時期數據上訓練和測試
```

### Q6: 如何處理類別不平衡?

```python
# 檢查不平衡比例
positive = sum(1 for s in samples if s.label == 1)
negative = len(samples) - positive
print(f"正樣本: {positive}, 負樣本: {negative}")

# 方案 1: 調整 sample_weight
sample_weights = [2.0 if s.label == 1 else 1.0 for s in samples]

# 方案 2: 使用 scale_pos_weight
model = xgb.XGBClassifier(
    scale_pos_weight=negative/positive,  # 平衡類別
)
```

---

## 參考資料

- [SAPTA 算法詳解](../SAPTA_ALGORITHM.md)
- [系統架構](architecture.md)
- [XGBoost 文檔](https://xgboost.readthedocs.io/)
- [scikit-learn 文檔](https://scikit-learn.org/)
