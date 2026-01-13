# Pulse-CLI 使用說明

> 台灣股票市場分析 CLI 工具 (Taiwan Stock Market Analysis CLI)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 目錄

1. [簡介](#簡介)
2. [安裝](#安裝)
3. [快速開始](#快速開始)
4. [命令參考](#命令參考)
5. [使用範例](#使用範例)
6. [配置說明](#配置說明)
7. [程式架構](#程式架構)
8. [常見問題](#常見問題)

---

## 簡介

Pulse-CLI 是一個專為台灣股票市場設計的命令列分析工具，提供：

- 📊 **技術分析** - RSI、MACD、均線、布林通道、ATR 等指標
- 📈 **基本面分析** - PER、PBR、ROE、EPS、股利資料
- 🏦 **法人動向** - 外資、投信、自營商買賣超
- 📋 **產業分析** - 各類股表現與輪動
- 🔍 **股票篩選** - 依技術指標篩選股票
- 🤖 **SAPTA 預測** - PRE-MARKUP 信號檢測
- 💬 **AI 智能分析** - 結合 OpenAI/Gemini 大語言模型

---

## 安裝

### 環境需求

- Python 3.11 或更高版本
- Git

### 安裝步驟

```bash
# 1. 複製專案
git clone https://github.com/yourusername/Pulse-CLI.git
cd Pulse-CLI

# 2. 建立虛擬環境
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

# 3. 安裝依賴
pip install -e ".[dev]"

# 4. (可選) 安裝 Playwright 瀏覽器
playwright install chromium
```

### 環境變數設定

複製 `.env.example` 為 `.env` 並填入 API 金鑰：

```bash
cp .env.example .env
```

編輯 `.env`：

```env
# FinMind API (用於台灣股市數據，註冊免費)
FINMIND_API_TOKEN=your_finmind_token_here

# OpenAI API (用於 AI 分析，可選)
OPENAI_API_KEY=your_openai_key_here

# Gemini API (用於 AI 分析，可選)
GEMINI_API_KEY=your_gemini_key_here
```

> **注意**：FinMind 提供免費帳號，可至 [FinMind 官網](https://finmindtrade.com/) 註冊取得 API Token。

---

## 快速開始

### 啟動 CLI

```bash
python -m pulse.cli.app
```

### 進入後輸入命令

```
/help          - 顯示所有命令
/technical 2330 - 台積電技術分析
/fundamental 2330 - 台積電基本面
/institutional 2330 - 台積電法人動向
/taiex         - 查看大盤指數
/sector        - 查看產業分類
```

---

## 命令參考

### 分析命令

| 命令 | 別名 | 說明 | 用法 |
|------|------|------|------|
| `/analyze` | `/a`, `/stock` | 完整股票分析 | `/analyze 2330` |
| `/technical` | `/ta`, `/tech` | 技術指標分析 | `/technical 2330` |
| `/fundamental` | `/fa`, `/fund` | 基本面分析 | `/fundamental 2330` |
| `/institutional` | `/inst`, `/broker` | 法人動向分析 | `/institutional 2330` |
| `/chart` | `/c`, `/price` | 價格圖表 | `/chart 2330 6mo` |
| `/forecast` | `/fc`, `/predict` | 價格預測 | `/forecast 2330` |
| `/compare` | `/comp` | 股票比較 | `/compare 2330 2454` |
| `/plan` | `/tp`, `/sl`, `/tradingplan` | 交易計劃 | `/plan 2330 100000` |
| `/sapta` | `/premarkup`, `/markup` | SAPTA 預測 | `/sapta 2330` |

### 市場命令

| 命令 | 別名 | 說明 | 用法 |
|------|------|------|------|
| `/taiex` | `/index`, `/market`, `/twii` | 大盤指數 | `/taiex` 或 `/taiex TPEX` |
| `/sector` | `/sec` | 產業分析 | `/sector` 或 `/sector SEMICONDUCTOR` |
| `/screen` | `/screen`, `/filter` | 股票篩選 | `/screen oversold --universe=tw50` |

### 系統命令

| 命令 | 別名 | 說明 | 用法 |
|------|------|------|------|
| `/models` | `/model`, `/switch` | 切換 AI 模型 | `/models` |
| `/clear` | `/cls` | 清除對話歷史 | `/clear` |
| `/help` | `/h`, `/?` | 說明命令 | `/help` 或 `/help technical` |

---

## 使用範例

### 技術分析

```bash
# 基本技術分析
/technical 2330

# 輸出範例：
Technical Analysis: 2330

  RSI (14): 75.57 (Overbought)
  MACD: 65.98 (Bullish)
  SMA 20: 1,557
  SMA 50: 1,493
  BB Upper: 1,765
  BB Lower: 1,348
  Trend: Bullish
  Signal: Neutral
```

### 法人動向

```bash
/institutional 2330

# 輸出範例：
Institutional Flow: 2330 (台積電)

  Foreign: +12.5B (Buy)
  Trust: +0.8B (Buy)
  Dealer (Self): -0.3B (Sell)
  Dealer (Hedge): +0.1B (Buy)

  Net: +13.1B
  Status: Strong buying from foreign investors
```

### 產業分析

```bash
# 查看所有產業
/sector

# 輸出範例：
Available Sectors

  SEMICONDUCTOR (16 stocks)
  ELECTRONICS (16 stocks)
  FINANCE (16 stocks)
  BANKING (15 stocks)
  ...

# 特定產業分析
/sector SEMICONDUCTOR
```

### 股票篩選

```bash
# 篩選超賣股票
/screen oversold

# 篩選強勢股 (MACD 多頭 + 價格站上 SMA20)
/screen bullish

# 篩選條件組合
/screen "rsi<30 and volume>1000000"

# 限定範圍
/screen oversold --universe=tw50
/screen bullish --universe=midcap
```

### 大盤指數

```bash
# 台灣加權指數
/taiex

# 櫃買指數 (OTC/TPEX)
/taiex TPEX
```

### SAPTA 預測

```bash
# 單一股票 SAPTA 分析
/sapta 2330

# 掃描多檔股票
/sapta scan --universe=tw50
```

---

## 配置說明

### 配置文件

主配置文件：`config/pulse.yaml`

```yaml
# API 設定
ai:
  default_model: "gpt-4o"
  available_models:
    "gpt-4o": "GPT-4o [OpenAI]"
    "gpt-4o-mini": "GPT-4o Mini [OpenAI]"
    "gemini-1.5-pro": "Gemini 1.5 Pro [Google]"

# 數據設定
data:
  yfinance_suffix: ".TW"  # Yahoo Finance 後綴
  default_period: "3mo"   # 預設歷史期間
  tickers_file: "data/tw_tickers.json"

# 分析設定
analysis:
  rsi_period: 14
  rsi_oversold: 30.0
  rsi_overbought: 70.0
```

### 股票代碼格式

| 市場 | 格式 | 範例 |
|------|------|------|
| TWSE (上市) | 4-6 位數字 | `2330` (台積電) |
| TPEX (櫃買) | 4-6 位數字 | `3176` (華義) |
| Yahoo Finance | 加上 `.TW` | `2330.TW` |

### 產業分類

Pulse-CLI 使用台灣產業分類：

- **半導體** (SEMICONDUCTOR)
- **電子** (ELECTRONICS)
- **金融** (FINANCE)
- **銀行** (BANKING)
- **保險** (INSURANCE)
- **鋼鐵** (STEEL)
- **塑膠** (PLASTIC)
- **紡織** (TEXTILE)
- **食品** (FOOD)
- **航運** (SHIPPING)
- **生技** (BIOTECH)
- **電信** (TELECOM)
- **營建** (CONSTRUCTION)
- **觀光** (TOURISM)

---

## 程式架構

```
Pulse-CLI/
├── pulse/                      # 主要程式碼
│   ├── __init__.py            # 專案初始化
│   ├── cli/                   # 命令列介面
│   │   ├── app.py             # Textual 應用程式
│   │   └── commands/          # 命令實作
│   │       └── registry.py    # 命令註冊中心
│   ├── core/                  # 核心模組
│   │   ├── agent.py           # AI Agent
│   │   ├── smart_agent.py     # 智能 Agent
│   │   ├── config.py          # 設定管理
│   │   ├── models.py          # 資料模型
│   │   ├── screener.py        # 股票篩選器
│   │   └── screener.py        # SAPTA 引擎
│   ├── analysis/              # 分析模組
│   │   ├── technical.py       # 技術分析
│   │   ├── fundamental.py     # 基本面分析
│   │   ├── sector.py          # 產業分析
│   │   └── institutional_flow.py  # 法人動向
│   ├── data/                  # 數據層
│   │   ├── stock_data_provider.py  # 統一數據介面
│   │   ├── finmind_data.py    # FinMind API
│   │   └── yfinance.py        # Yahoo Finance
│   ├── ai/                    # AI 整合
│   │   ├── client.py          # AI API Client
│   │   └── prompts.py         # 提示詞模板
│   ├── sapta/                 # SAPTA 模組
│   │   ├── engine.py          # SAPTA 引擎
│   │   ├── models.py          # SAPTA 模型
│   │   └── modules/           # 分析模組
│   └── utils/                 # 工具函式
│       ├── constants.py       # 常數定義
│       ├── formatters.py      # 格式化工具
│       ├── logger.py          # 日誌系統
│       └── validators.py      # 驗證器
├── tests/                     # 測試檔案
├── config/                    # 設定檔
│   └── pulse.yaml
├── data/                      # 資料檔案
│   ├── tw_tickers.json        # 股票清單
│   └── cache/                 # 快取目錄
├── pyproject.toml            # 專案配置
├── README.md                 # 專案說明
└── CHANGELOG.md              # 更新日誌
```

### 數據流程

```
┌─────────────────┐
│   User Command  │ (CLI 輸入)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ CommandRegistry │ (命令解析)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Data Provider   │ (FinMind / Yahoo Finance)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Analysis Module │ (技術/基本面/法人分析)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   AI Agent      │ (可選：LLM 綜合分析)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Output        │ (顯示結果)
└─────────────────┘
```

### 主要類別

| 類別 | 職責 |
|------|------|
| `CommandRegistry` | 命令註冊與執行 |
| `StockDataProvider` | 統一數據獲取介面 |
| `FinMindFetcher` | FinMind API 數據獲取 |
| `YFinanceFetcher` | Yahoo Finance 數據獲取 |
| `TechnicalAnalyzer` | 技術指標計算 |
| `FundamentalAnalyzer` | 基本面分析 |
| `InstitutionalFlowAnalyzer` | 法人流向分析 |
| `SectorAnalyzer` | 產業分析 |
| `StockScreener` | 股票篩選 |
| `SaptaEngine` | SAPTA 預測引擎 |
| `SmartAgent` | 智能對話 Agent |

---

## 常見問題

### Q1: FinMind API Token 哪裡取得？

訪問 [FinMind 官網](https://finmindtrade.com/) 註冊帳號後，在「API 資訊」頁面取得 Token。

### Q2: 如何切換 AI 模型？

```bash
/models
# 會顯示模型選擇介面
```

或在 `.env` 中設定預設模型。

### Q3: 支援哪些數據源？

- **主要**: FinMind (台灣專業財經數據 API)
- **備用**: Yahoo Finance

### Q4: 如何更新股票清單？

股票清單自動從 FinMind 更新，或手動編輯 `data/tw_tickers.json`。

### Q5: CLI 沒有回應怎麼辦？

1. 檢查網路連線
2. 確認 API Token 正確
3. 嘗試使用 `/clear` 清除對話歷史
4. 檢查日誌：`tail -f data/logs/pulse.log`

### Q6: 技術分析指標的參數可以調整嗎？

可以在 `config/pulse.yaml` 中修改 `analysis` 區段的參數。

---

## 測試

```bash
# 執行所有測試
pytest

# 執行特定測試檔案
pytest tests/test_core/test_data/test_yfinance.py -v

# 執行特定測試
pytest tests/test_core/test_data/test_yfinance.py::test_fetch_stock_success -v

# 執行並顯示覆蓋率
pytest --cov=pulse --cov-report=term-missing
```

---

## 貢獻

歡迎提交 Issue 和 Pull Request！

1. Fork 本專案
2. 建立 Feature Branch (`git checkout -b feature/AmazingFeature`)
3. 提交變更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到 Branch (`git push origin feature/AmazingFeature`)
5. 建立 Pull Request

---

## 授權

本專案採用 MIT License 授權。

---

**感謝使用 Pulse-CLI！** 🚀
