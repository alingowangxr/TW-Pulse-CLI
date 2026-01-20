# TW-Pulse-CLI 台灣股票分析工具 - 內部任務追蹤

> **最後更新**: 2026-01-20
> **版本**: v0.1.7
> **README**: 請參閱 [README.md](README.md) 獲取專案概述和完整路線圖
> **整體進度**: 核心功能 100% 完成 | 測試 439 個通過 | 評分 9.5/10

---

## v0.1.7 更新摘要 (2026-01-20)

### 測試覆蓋率大幅提升
| 模組 | 新增測試數 | 狀態 |
|------|-----------|------|
| 股票篩選器 (screener.py) | 92 | ✅ 完成 |
| AI 客戶端 (ai/client.py) | 29 | ✅ 完成 |
| CLI 命令處理器 | 29 | ✅ 完成 |
| **小計** | **150** | |

### 新功能
1. **SAPTA 圖表輸出** `/sapta chart <TICKER>`
   - 價格走勢圖 + SAPTA 狀態/分數疊加
   - 6 個模組分數條形圖 (顏色區分優劣)
   - 信心等級與 ML 概率顯示
   - 艾略特波浪位置與費波那契回撤
   - 預期突破窗口與倒數天數

2. **基本面數據補救策略**
   - 多來源數據合併 (FinMind + yfinance)
   - 產業平均值估計 (Technology, Semiconductor, Financial 等)
   - 數據品質評分 (0-100%)
   - 恢復報告生成

### 現有功能增強
- oversold RSI 額外加分 (+25)
- 跳過 bearish MACD 處罰（當 RSI oversold 時）
- oversold + uptrend 組合額外加分 (+20)
- 新增智能篩選條件 (`multibagger`, `growth`, `small cap`)
- 修復 empty universe 處理邏輯

---

## 最近更新 (v0.1.5)

### 2026-01-20
- ✅ **新增 DeepSeek 模型支援** (`deepseek/deepseek-chat`)
  - 設為預設 AI 模型
  - 回應詳細，適合深度分析
- ✅ **修復環境變數載入問題**
  - 使用 python-dotenv 載入 `.env` 檔案
  - 確保 API Key 正確讀取
- ✅ **修復 Thinking Indicator 重複問題**
  - 新增重複檢查機制
  - 清理現有的 thinking widget 再添加新的
- ✅ **增加命令超時處理**
  - `/analyze` 命令 180 秒超時
  - 防止長時間等待無回應

---

## 快速鏈接

- [README.md](README.md) - 主文檔、專案概述、功能說明
- [CHANGELOG.md](CHANGELOG.md) - 版本變更記錄
- [USAGE.md](USAGE.md) - 使用範例
- [docs/SAPTA_ALGORITHM.md](docs/SAPTA_ALGORITHM.md) - SAPTA 算法詳解

---

## 代碼品質評估

| 指標 | 評分 |
|------|------|
| 功能完整性 | 9.5/10 |
| 代碼結構 | 9.5/10 |
| 文檔質量 | 9/10 |
| 測試覆蓋 | 9.2/10 (439 tests) |
| 錯誤處理 | 9/10 |
| 數據源備援 | 9/10 (3層) |
| 用戶體驗 | 9.5/10 |
| **總體評分** | **9.5/10** |

---

## 版本歷史

| 版本 | 日期 | 變更 |
|------|------|------|
| 0.1.7 | 2026-01-20 | SAPTA 圖表、基本面數據補救、150 個新測試 |
| 0.1.6 | 2026-01-20 | DeepSeek 模型、測試覆蓋率提升 (SmartAgent, TradingPlan, Technical) |
| 0.1.5 | 2026-01-20 | 環境變數修復、Thinking Indicator 修復、超時處理 |
| 0.1.4 | 2026-01-16 | CSV export、類型提示、 Ruff linting |
| 0.1.3 | 2026-01-15 | SAPTA 輸出優化、法人流向修復、模型重訓練 |
| 0.1.2 | 2026-01-14 | Fugle 整合、錯誤處理、註冊表重構 |
| 0.1.1 | 2026-01-14 | 台灣市場遷移 (FinMind, TWSE/TPEX) |
| 0.1.0 | 2026-01-13 | 初始發布 |

---

## 專案結構

```
tw-pulse-cli/
├── pulse/
│   ├── ai/               # LiteLLM 多 Provider AI 客戶端
│   ├── cli/              # Textual TUI 介面 + Commands
│   │   └── commands/     # 分析、圖表、篩選、進階命令
│   ├── core/
│   │   ├── analysis/     # 技術分析、基本面、法人動向、數據補救
│   │   ├── data/         # FinMind + Yahoo Finance + Fugle 數據層
│   │   ├── sapta/        # SAPTA 預測引擎 (6個模組 + ML)
│   │   │   ├── modules/  # 6 個分析模組
│   │   │   └── ml/       # XGBoost 訓練器
│   │   ├── screener/     # 股票篩選器
│   │   └── chart_generator.py  # 圖表生成 (含 SAPTA 圖表)
│   └── utils/            # 格式化、重試、錯誤處理
├── data/                 # 股票代碼、緩存、報告
├── docs/                 # 文檔 (算法、訓練、架構)
├── tests/                # 測試 suite (439 tests)
└── charts/               # 生成的圖表
```

---

## 測試套件統計

| 測試套件 | 測試數 |
|----------|--------|
| test_core/test_smart_agent.py | 99 |
| test_core/test_trading_plan.py | 77 |
| test_core/test_analysis/ | 46 |
| test_core/test_screener.py | 92 |
| test_ai/test_client.py | 29 |
| test_cli/test_commands.py | 29 |
| test_utils/ | 67 |
| **總計** | **439** |

---

## 已知限制

1. **FinMind API 配額**: 免費版有請求上限，法人動向功能可能受限
2. **AI 服務依賴**: 需設定 LLM API key (GROQ_API_KEY 等)
3. **Prophet 可選**: 價格預測功能依賴 Prophet，未安裝時使用簡易備用方案
4. **Fugle API Key 格式**: 新版 API Key 需直接使用 base64 編碼格式

---

*最後更新: 2026-01-20 (v0.1.6)*

**TW-Pulse-CLI 台灣股票市場分析工具**
