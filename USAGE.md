# TW-Pulse-CLI 使用說明

> 台灣股票市場分析 CLI 工具 - 安裝與使用指南

---

## 目錄

1. [安裝](#安裝)
2. [設定](#設定)
3. [啟動](#啟動)
4. [命令](#命令)
5. [範例](#範例)
6. [常見問題](#常見問題)

---

## 安裝

### 環境需求

- Python 3.11+
- Git

### 安裝步驟

```bash
# 1. 複製專案
git clone https://github.com/alingowangxr/TW-Pulse-CLI.git
cd TW-Pulse-CLI

# 2. 建立虛擬環境
python -m venv .venv

# 3. 啟動虛擬環境
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # Linux/macOS

# 4. 安裝
pip install -e .
```

### 使用 uv (更快速)

```bash
pip install uv
uv pip install -e .
```

---

## 設定

### 環境變數

複製範例檔案：
```bash
cp .env.example .env
```

編輯 `.env` 填入 API Key：

```env
# AI API Key (選擇一個或多個)
DEEPSEEK_API_KEY=your_key          # 預設，詳細分析
# GROQ_API_KEY=your_key            # 免費，快速
# GEMINI_API_KEY=your_key
# ANTHROPIC_API_KEY=your_key
# OPENAI_API_KEY=your_key

# FinMind API (法人動向)
FINMIND_TOKEN=your_token

# 預設模型
PULSE_AI__DEFAULT_MODEL=deepseek/deepseek-chat
```

### 取得 API Key

| Provider | 網址 | 特性 |
|----------|------|------|
| DeepSeek | https://platform.deepseek.com/api-keys | 預設，詳細分析 |
| Groq | https://console.groq.com/keys | 免費額度，快速 |
| Google | https://aistudio.google.com/apikey | 免費額度有限 |
| Anthropic | https://console.anthropic.com/ | 付費，高品質 |
| OpenAI | https://platform.openai.com/api-keys | 付費 |
| FinMind | https://finmindtrade.com/ | 法人動向數據 |

---

## 啟動

```bash
# 進入虛擬環境後
pulse
```

或直接執行：
```bash
python -m pulse.cli.app
```

### 快捷鍵

| 快捷鍵 | 功能 |
|--------|------|
| `Enter` | 送出訊息 |
| `Ctrl+C` | 退出程式 |
| `Ctrl+L` | 清除對話 |
| `Escape` | 關閉命令面板 |
| `Tab` | 導航命令選擇 |
| `↑` `↓` | 上下選擇 |

---

## 命令

### 分析命令

| 命令 | 別名 | 說明 | 用法 |
|------|------|------|------|
| `/analyze` | `/a`, `/stock` | 完整分析 | `/analyze 2330` |
| `/technical` | `/ta`, `/tech` | 技術分析 | `/technical 2330` |
| `/fundamental` | `/fa`, `/fund` | 基本面分析 | `/fundamental 2330` |
| `/institutional` | `/inst`, `/flow` | 法人動向 | `/institutional 2330` |
| `/chart` | `/c` | 產生圖表 | `/chart 2330 3mo` |
| `/forecast` | `/fc` | 價格預測 | `/forecast 2330 14` |
| `/compare` | `/cmp`, `/vs` | 比較股票 | `/compare 2330 2454` |
| `/plan` | `/tp` | 交易計畫 | `/plan 2330` |
| `/sapta` | `/premarkup` | 預漲偵測 | `/sapta 2330` |
| `/index` | `/market` | 大盤指數 | `/index` |
| `/sector` | `/sec` | 產業分析 | `/sector` |

### 篩選命令

| 命令 | 別名 | 說明 | 用法 |
|------|------|------|------|
| `/screen` | `/s`, `/filter` | 股票篩選 | `/screen oversold` |
| `/smart-money` | `/tvb`, `/主力` | 主力足跡選股 | `/smart-money --tw50` |

### 系統命令

| 命令 | 別名 | 說明 |
|------|------|------|
| `/models` | `/model`, `/m` | 切換 AI 模型 |
| `/clear` | `/cls` | 清除對話 |
| `/help` | `/h`, `/?` | 說明 |
| `/exit` | `/quit`, `/q` | 退出 |

### 篩選條件

| 條件 | 說明 |
|------|------|
| `oversold` | RSI < 30 |
| `overbought` | RSI > 70 |
| `bullish` | MACD 多頭 + 站上 SMA20 |
| `bearish` | MACD 空頭 |
| `breakout` | 突破壓力位 + 量增 |
| `momentum` | RSI 50-70 + MACD 多頭 |
| `undervalued` | PE < 15 + ROE > 10% |
| `rsi<30` | 自訂條件 |
| `pe<15 and roe>10` | 複合條件 |

### Universe 選項

```bash
/screen oversold --universe=tw50     # 台灣50 (50檔)
/screen oversold --universe=listed   # 上市公司 (1,067檔)
/screen oversold --universe=otc      # 上櫃公司 (874檔)
/screen oversold --universe=all      # 全部 (1,941檔)
```

### 匯出 CSV

```bash
/screen oversold --export             # 自動產生檔名
/screen rsi<30 --export=my_data.csv   # 自訂檔名
```

匯出位置：`data/reports/screen_YYYYMMDD_HHMMSS.csv`

---

## Smart Money Screener

### `/smart-money` - 主力足跡選股

基於 **Trend/Volume/Bias** 三維度的主力吸籌選股。

### 評分邏輯 (100分制)

| 維度 | 權重 | 條件 | 分數 |
|------|------|------|------|
| 趨勢型態 | 40% | 極致壓縮 (BB寬度<15%+10天) | +25 |
| | | 帶量突破 | +15 |
| 量能K線 | 35% | OBV 先行創高 | +15 |
| | | 攻擊量 (>2x MV5) | +10 |
| | | K線霸氣 (實體>70%) | +10 |
| 乖離位階 | 25% | 黃金起漲 (乖離5-10%) | +15 |
| | | 站上年線 | +10 |

### 使用方式

```bash
/smart-money              # TW50 (50檔, ~10秒)
/smart-money --tw50       # 台灣50
/smart-money --listed     # 上市公司 (1,067檔, ~2分鐘)
/smart-money --otc        # 上櫃公司 (874檔, ~90秒)
/smart-money --all        # 全部市場 (1,941檔, ~4分鐘)
/smart-money --fast       # 快速模式 (跳過OBV)
/smart-money --min=60     # 高分篩選
/smart-money --limit=10   # 限制數量
```

### 輸出範例

```
主力足跡選股 (台灣50, min_score=40)
---
找到 3 檔符合條件的股票:

[★  ] 2317    48.0/100  鴻海
    NT$224 (-2.61%)  乖離MA20:-2.8%  量比:1.4x
    信號: 布林收縮 BB:7.5 | OBV整理 | 長紅100%

圖例: ★★★=80+強勢  ★★=60-79吸籌  ★=40-59觀察
```

別名：`/tvb`, `/主力`

---

## SAPTA 預漲偵測

### `/sapta` - 預漲信號檢測

**SAPTA** (System for Analyzing Pre-markup Technical Accumulation) - 基於機器學習的預漲偵測引擎。

### 狀態等级

| 狀態 | 分數 | 意義 |
|------|------|------|
| **PRE-MARKUP** | >= 47 | 準備突破 |
| **SIAP** | >= 35 | 接近就緒 |
| **WATCHLIST** | >= 24 | 早期吸籌 |
| **SKIP** | < 24 | 無信號 |

### 使用方式

```bash
/sapta 2330                 # 單一股票
/sapta 2330 --detailed      # 詳細分析
/sapta chart 2330           # 產生圖表
/sapta scan                 # 掃描 TW50
/sapta scan --listed        # 掃描上市公司
```

### 圖表輸出

```bash
/sapta chart 2330           # 基本圖表
/sapta chart 2330 --detailed # 詳細分析圖
```

圖表儲存：`charts/sapta_{TICKER}_{YYYYMMDD}.png`

---

## 範例

### 基本分析

```
> 分析 2330
> 台積電技術面如何？
> 比較 2330 和 2317
```

### 篩選股票

```
> 找出超賣的股票
> 找 RSI < 30 的股票
> 篩選突破股票
```

### 交易相關

```
> 幫 2330 建立交易計畫
> 檢查 2303 的潛在買點
```

### SAPTA

```
> 找預漲股票
> 找準備突破的股票
> 掃描全市場預漲股
```

---

## 常見問題

### Q1: 沒有 API Key 怎麼辦？

**推薦 Groq (免費且快速)：**
1. 訪問 https://console.groq.com/keys
2. 註冊並建立 API Key
3. 設定 `GROQ_API_KEY` 環境變數

### Q2: Rate Limit 怎麼辦？

```bash
# 切換到其他 Provider
export GROQ_API_KEY="your_groq_key"
export PULSE_AI__DEFAULT_MODEL="groq/llama-3.3-70b-versatile"
```

### Q3: 如何切換 AI 模型？

```bash
# 方法1: 使用命令
/models

# 方法2: 環境變數
export PULSE_AI__DEFAULT_MODEL="groq/llama-3.3-70b-versatile"

# 方法3: 編輯 .env
PULSE_AI__DEFAULT_MODEL=deepseek/deepseek-chat
```

### Q4: 法人動向沒有數據？

確認已設定 `FINMIND_TOKEN`：
- 訪問 https://finmindtrade.com/ 註冊
- 取得 Token 填入 `.env`

### Q5: CLI 沒有回應？

1. 檢查網路連線
2. 確認 API Key 正確
3. 使用 `/clear` 清除對話
4. 檢查日誌：`data/logs/pulse.log`

### Q6: 數據源

| 數據源 | 用途 |
|--------|------|
| **FinMind** | 法人動向、融資融券、基本面 |
| **Yahoo Finance** | 股價、技術指標 |
| **Fugle** | 即時報價、52週高低 |

---

**最後更新**: 2026-01-20
