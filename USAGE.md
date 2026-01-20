# TW-Pulse-CLI 使用說明

> 台灣股票市場分析 CLI 工具 (Taiwan Stock Market Analysis CLI)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub Stars](https://img.shields.io/github/stars/alingowangxr/TW-Pulse-CLI)](https://github.com/alingowangxr/TW-Pulse-CLI)

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

TW-Pulse-CLI 是一個專為台灣股票市場設計的 AI 驅動命令列分析工具，提供：

- **技術分析** - RSI、MACD、均線、布林通道、ATR 等指標
- **基本面分析** - PER、PBR、ROE、EPS、股利資料
- **法人動向** - 外資、投信、自營商買賣超
- **股票篩選** - 依技術指標篩選股票
- **SAPTA 預測** - 基於機器學習的預漲信號檢測
- **AI 智能分析** - 支援多家 LLM (Groq/Gemini/Claude/GPT)
- **交易計畫** - 自動生成停利/停損/風險報酬計算

---

## 安裝

### 環境需求

- Python 3.11 或更高版本
- Git

### 安裝步驟

```bash
# 1. 複製專案
git clone https://github.com/alingowangxr/TW-Pulse-CLI.git
cd TW-Pulse-CLI

# 2. 建立虛擬環境
python -m venv .venv

# Windows
.venv\Scripts\activate

# Linux/macOS
source .venv/bin/activate

# 3. 安裝依賴
pip install -e .
```

### 環境變數設定

複製 `.env.example` 為 `.env` 並填入 API 金鑰：

```bash
cp .env.example .env
```

編輯 `.env`（設定 AI API key）：

```env
# DeepSeek (預設 - 詳細分析，較慢)
DEEPSEEK_API_KEY=your_deepseek_key

# 或 Groq (免費 - 快速回應，精簡)
# GROQ_API_KEY=your_groq_key

# 或其他模型
# GEMINI_API_KEY=your_gemini_key
# ANTHROPIC_API_KEY=your_key
# OPENAI_API_KEY=your_key

# FinMind API (用於法人動向，可選)
FINMIND_TOKEN=your_finmind_token
```

> 💡 **提示**: 可同時填入多個 API Key，在 CLI 中自由切換模型

### 取得 API Key

| Provider | 取得方式 | 特性 |
|----------|----------|------|
| **DeepSeek** | https://platform.deepseek.com/api-keys | 詳細分析，較慢 (預設) |
| **Groq** | https://console.groq.com/keys | 快速回應，免費 (推薦) |
| **Google** | https://aistudio.google.com/apikey | 免費額度有限 |
| **Anthropic** | https://console.anthropic.com/ | 付費，高品質 |
| **OpenAI** | https://platform.openai.com/api-keys | 付費 |
| **FinMind** | https://finmindtrade.com/ | 法人動向數據 |

---

## 快速開始

### 啟動 CLI

```bash
# 設定 API Key (Windows PowerShell)
$env:DEEPSEEK_API_KEY="your_key"

# 或使用 Groq
# $env:GROQ_API_KEY="your_groq_key"

# 啟動程式
python -m pulse.cli.app
```

> **注意**: 確保 `.env` 檔案中已填入 API Key，程式會自動載入

### 進入後輸入命令

```
/help              - 顯示所有命令
/analyze 2330      - 台積電完整分析
/technical 2330    - 技術分析
/fundamental 2330  - 基本面分析
/institutional 2330 - 法人動向
/sapta 2330        - SAPTA 預漲分析
/screen oversold   - 篩選超賣股
/exit              - 退出程式
```

---

## 命令參考

### 分析命令

| 命令 | 別名 | 說明 | 用法 |
|------|------|------|------|
| `/analyze` | `/a`, `/stock` | 完整股票分析 | `/analyze 2330` |
| `/technical` | `/ta`, `/tech` | 技術指標分析 | `/technical 2330` |
| `/fundamental` | `/fa`, `/fund` | 基本面分析 | `/fundamental 2330` |
| `/institutional` | `/inst`, `/flow` | 法人動向分析 | `/institutional 2330` |
| `/chart` | `/c`, `/kline` | K線圖 (PNG) | `/chart 2330 6mo` |
| `/forecast` | `/fc`, `/predict` | 價格預測 | `/forecast 2330` |
| `/compare` | `/cmp`, `/vs` | 股票比較 | `/compare 2330 2454` |
| `/plan` | `/tp`, `/sl` | 交易計劃 | `/plan 2330` |
| `/sapta` | `/premarkup` | SAPTA 預漲偵測 | `/sapta 2330` |

### 篩選命令

| 命令 | 別名 | 說明 | 用法 |
|------|------|------|------|
| `/screen` | `/scan`, `/filter` | 股票篩選 | `/screen oversold` |

**篩選條件:**
- `oversold` - RSI < 30
- `overbought` - RSI > 70
- `bullish` - MACD 多頭 + 價格站上 SMA20
- `bearish` - MACD 空頭
- `breakout` - 突破壓力位
- `momentum` - 動能股

**Universe 選項:**
```bash
/screen oversold --universe=tw50     # 台灣50
/screen bullish --universe=midcap    # 中型股
/screen momentum --universe=all      # 全部
```

**匯出 CSV:**
```bash
/screen oversold --export             # 自動產生檔名
/screen rsi<30 --export=my_results.csv  # 自訂檔名
```

CSV 會儲存到 `data/reports/` 目錄，包含 18 個欄位：ticker, name, sector, price, change_percent, volume, rsi_14, macd, sma_20, sma_50, pe_ratio, pb_ratio, roe, dividend_yield, market_cap, score, signals。

### 系統命令

| 命令 | 別名 | 說明 |
|------|------|------|
| `/models` | `/model`, `/m` | 切換 AI 模型 |
| `/clear` | `/cls` | 清除對話歷史 |
| `/help` | `/h`, `/?` | 顯示說明 |
| `/exit` | `/quit`, `/q` | 退出程式 |

---

## 使用範例

### 技術分析

```bash
/technical 2330

# 輸出範例：
技術分析: 2330 (台積電)

  RSI(14): 58.3 (中性)
  MACD: 12.5 (多頭)
  SMA20: 820 | SMA50: 795 | SMA200: 750
  布林通道: 780 - 820 - 860
  支撐: 800 | 壓力: 850
  趨勢: 多頭 | 訊號: 買進
```

### 法人動向

```bash
/institutional 2330

# 輸出範例：
法人動向: 2330 (台積電)

  外資: +125 億 (買超)
  投信: +8 億 (買超)
  自營商: -3 億 (賣超)

  淨流量: +130 億
  訊號: 強力買進
```

### SAPTA 預漲分析

```bash
/sapta 2330

# 輸出範例：
SAPTA 分析: 2330
========================================
狀態: [PRE-MARKUP]
分數: 68.5/100
信心度: 高
ML 機率: 78%

模組明細:
  吸籌偵測: 22.5/25
  波動收縮: 18.0/20
  布林擠壓: 12.0/15
  波浪分析: 10.5/15
  時間投影: 5.5/15
  反出貨: 0.0/10
```

### 交易計畫

```bash
/plan 2330

# 輸出範例：
交易計畫: 2330
========================================
進場價: NT$ 820
停損: NT$ 800 (-2.44%)
停利1: NT$ 840 (+2.44%)
停利2: NT$ 860 (+4.88%)

風險報酬: 1:2.0
建議部位: 10 張
```

---

## 配置說明

### 配置文件

主配置文件：`config/pulse.yaml`

```yaml
# AI 設定 (LiteLLM)
ai:
  default_model: "deepseek/deepseek-chat"
  temperature: 0.7
  max_tokens: 4096
  timeout: 120

  available_models:
    # DeepSeek (Cost-effective, high performance)
    deepseek/deepseek-chat: "DeepSeek Chat (DeepSeek)"
    # Groq (免費)
    groq/llama-3.3-70b-versatile: "Llama 3.3 70B (Groq)"
    groq/llama-3.1-8b-instant: "Llama 3.1 8B (Groq)"
    # Google
    gemini/gemini-2.0-flash: "Gemini 2.0 Flash (Google)"
    # Anthropic
    anthropic/claude-sonnet-4-20250514: "Claude Sonnet 4 (Anthropic)"
    # OpenAI
    openai/gpt-4o: "GPT-4o (OpenAI)"
```

### 可用 AI 模型

| 模型 ID | 名稱 | Provider | 速度 | 風格 |
|---------|------|----------|------|------|
| `deepseek/deepseek-chat` | DeepSeek Chat | DeepSeek | 較慢 | 詳細 (預設) |
| `groq/llama-3.3-70b-versatile` | Llama 3.3 70B | Groq | **很快** | 精簡 (免費) |
| `groq/llama-3.1-8b-instant` | Llama 3.1 8B | Groq | 很快 | 精簡 (免費) |
| `gemini/gemini-2.0-flash` | Gemini 2.0 Flash | Google | 快 | 平衡 |
| `anthropic/claude-sonnet-4-20250514` | Claude Sonnet 4 | Anthropic | 中等 | 詳細 |
| `openai/gpt-4o` | GPT-4o | OpenAI | 中等 | 詳細 |

#### 模型選擇建議

| 使用場景 | 推薦模型 |
|----------|----------|
| 深度分析報告 ( `/analyze`) | **DeepSeek** |
| 快速查詢 ( `/technical`, `/sapta`) | **Groq** |
| 平衡速度與品質 | Gemini 2.0 Flash |

#### 切換模型

```bash
# 顯示模型選擇清單
/models

# 選擇模型
/models groq/llama-3.3-70b-versatile
/models deepseek/deepseek-chat
```

或在 `.env` 設定預設模型:
```env
PULSE_AI__DEFAULT_MODEL=deepseek/deepseek-chat
```

---

## 程式架構

```
TW-Pulse-CLI/
├── pulse/
│   ├── ai/                    # AI 整合 (LiteLLM)
│   │   ├── client.py          # AI 客戶端
│   │   └── prompts.py         # 提示詞模板
│   ├── cli/
│   │   ├── app.py             # Textual TUI 應用
│   │   └── commands/
│   │       ├── registry.py    # 命令註冊中心
│   │       ├── analysis.py    # 分析命令
│   │       ├── screening.py   # 篩選命令 (含 CSV 匯出)
│   │       └── advanced.py    # 進階命令
│   ├── core/
│   │   ├── config.py          # 設定管理
│   │   ├── smart_agent.py     # 智能 Agent
│   │   ├── screener.py        # 股票篩選器
│   │   ├── trading_plan.py    # 交易計畫生成
│   │   ├── forecasting.py     # 價格預測
│   │   ├── analysis/          # 分析模組
│   │   │   ├── technical.py
│   │   │   ├── fundamental.py
│   │   │   └── institutional_flow.py
│   │   ├── data/              # 數據層
│   │   │   ├── yfinance.py
│   │   │   ├── finmind_data.py
│   │   │   └── fugle.py       # Fugle 整合
│   │   └── sapta/             # SAPTA 引擎
│   │       ├── engine.py
│   │       ├── modules/       # 6 個分析模組
│   │       └── ml/            # 機器學習
│   └── utils/
│       ├── constants.py       # 股票清單
│       └── formatters.py      # 輸出格式化
├── config/
│   └── pulse.yaml             # 配置文件
├── data/
│   ├── tw_tickers.json        # 股票清單 (5,868 檔)
│   ├── cache/                 # 快取目錄
│   └── reports/               # 匯出報告 (CSV)
└── .env.example               # 環境變數範例
```

### 數據流程

```
用戶輸入 → CommandRegistry → Data Provider → Analysis Module → AI Agent → 輸出
              (命令解析)      (FinMind/Yahoo)    (技術/基本面)    (LLM分析)
```

---

## 常見問題

### Q1: 如何取得免費 AI API Key?

**推薦使用 Groq (免費額度最高):**
1. 訪問 https://console.groq.com/keys
2. 註冊帳號
3. 建立 API Key
4. 設定環境變數: `export GROQ_API_KEY="your_key"`

### Q2: 出現 Rate Limit 錯誤怎麼辦?

```bash
# 切換到其他 Provider
export GROQ_API_KEY="your_groq_key"
export PULSE_AI__DEFAULT_MODEL="groq/llama-3.3-70b-versatile"
```

### Q3: 如何切換 AI 模型?

```bash
# 方法1: 使用命令
/models

# 方法2: 設定環境變數
export PULSE_AI__DEFAULT_MODEL="deepseek/deepseek-chat"

# 方法3: 編輯 .env 檔案
PULSE_AI__DEFAULT_MODEL=deepseek/deepseek-chat
```

### Q4: 法人動向數據從哪裡來?

法人動向數據來自 [FinMind](https://finmindtrade.com/)。
- 免費註冊即可使用
- 設定 `FINMIND_TOKEN` 可提高 API 配額

### Q5: CLI 沒有回應怎麼辦?

1. 檢查網路連線
2. 確認 API Key 正確
3. 使用 `/clear` 清除對話歷史
4. 檢查日誌：`data/logs/pulse.log`

### Q6: 支援哪些數據源?

| 數據源 | 用途 | 備註 |
|--------|------|------|
| **FinMind** | 法人動向、融資融券 | 主要來源 |
| **Yahoo Finance** | 股價、技術指標 | 備援來源 |

---

## 測試

```bash
# 執行所有測試
pytest

# 執行特定測試
pytest tests/test_core/test_data/test_yfinance.py -v

# 顯示覆蓋率
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

**TW-Pulse-CLI 台灣股票市場分析工具**
