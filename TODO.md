# TW-Pulse-CLI Roadmap - 未來改進計劃

> **版本**: v0.2.0
> **最後更新**: 2026-01-22

---

## 核心功能改進

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

### 數據穩定性

- [x] **API 配額監控** ✅ v0.1.10
  - FinMind API 配額監控 (request_count, quota_limit)
  - 優雅降級策略 (現有)
  - 配額狀態 API: `get_quota_status()`, `set_quota_limit()`

- [ ] **批量股票測試**
  - 驗證多股票數據一致性
  - 自動化數據品質檢測

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

## 功能擴展

### 技術指標擴充

- [x] **新增技術指標** ✅ v0.1.9
  - OBV (On-Balance Volume) - 已有
  - ADX (Average Directional Index) - ✅ 新增
  - CCI (Commodity Channel Index) - ✅ 新增
  - Ichimoku Cloud (一目均衡表) - ✅ 新增

### 圖表自訂選項

- [x] **圖表客製化** ✅ v0.1.10
  - 顏色主題切換 (dark/light/traditional)
  - 圖表樣式調整 (ChartConfig)
  - 時間範圍自訂 (figure_size, line_width)
  - 多指標疊加 (MA20/MA50/MA200 開關)

### 批量掃描優化

- [x] **並發批量下載** ✅ v0.1.9
  - 多股票同時獲取數據 (已有 asyncio.gather)
  - 智能限流機制 (已有 semaphore=10)

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

### v0.2.0 - 個人化功能

- [ ] **自選股管理**
  - 本地 JSON 存儲自選股
  - 快速訪問清單
- [ ] **投資組合追蹤**
  - 成本基礎計算
  - 盈虧追蹤
  - 績效統計
- [ ] **價格提醒**
  - 突破/跌破通知
  - 自訂閾值設定

### v0.3.0 - 回測與策略

- [ ] **回測框架**
  - 歷史模擬交易
  - 信號回測驗證
- [ ] **策略建構器**
  - 自訂進場/出場規則
  - 條件組合編輯器
- [ ] **績效報告**
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
  -  Greeks 計算
  - 履約價分析

---

## 文檔計劃

- [ ] **部署指南**
  - Docker 容器化
  - pip 安裝說明
- [ ] **使用範例擴充**
  - 高級用法教程
  - 實際案例分析

---

*最後更新: 2026-01-20 (v0.1.8)*
