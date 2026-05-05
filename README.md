# TW-Pulse-CLI

<div align="center">

![TW-Pulse-CLI](https://img.shields.io/badge/TW--Pulse--CLI-58a6ff?style=for-the-badge&logo=python&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Beta-yellow?style=for-the-badge)

**AI-Powered Taiwan Stock Market Analysis & Strategy Backtesting CLI**

*台灣股市分析與策略回測工具 (基於 AI 的終端介面)*

[Features](#features) • [SAPTA](#sapta-引擎) • [Installation](#quick-start) • [Usage](USAGE.md) • [Roadmap](TODO.md)

[![GitHub](https://img.shields.io/badge/GitHub-alingowangxr%2FTW-Pulse-CLI-181717?style=flat-square&logo=github)](https://github.com/alingowangxr/TW-Pulse-CLI)

</div>

---

## About

**TW-Pulse-CLI** 是基於 [Pulse-CLI](https://github.com/alingowangxr/Pulse-CLI) 借鑑並重新改寫的台灣股市分析 CLI 工具。

原 Pulse-CLI 專注於印尼股市，本專案針對台灣市場進行優化，整合 FinMind、Yahoo Finance、Fugle 與本地 SQLite 倉庫，提供技術分析、基本面分析、法人動向、機器學習預測、**策略回測**等功能。

---

## Features

### 🎯 核心功能

| Feature | Description |
|---------|-------------|
| **Smart Agent** | AI 代理會先抓取真實數據，再以固定結構產生繁體中文分析 |
| **Natural Language** | 支援繁體中文提問與回覆 |
| **Streaming Response** | 即時串流回應，AI 分析過程即時顯示，無需等待 |
| **Local Warehouse** | 可直接讀取本地台股 SQLite 倉庫，加速大量篩選與分析 |
| **Strategy Backtesting** | 完整的策略回測系統，支援多策略框架與績效報告 |
| **Dynamic Capital Management** | 動態資金管理，智能倉位控制 |
| **Trading Reports** | 詳細的交易報告與績效分析 |

### 📊 技術分析

| Feature | Description |
|---------|-------------|
| **Technical Analysis** | RSI, MACD, 布林通道, SMA/EMA, ADX, CCI, Ichimoku, Keltner Channel, **Happy Lines (樂活五線譜)** 等 20+ 指標 |
| **LOHAS Channel** | **樂活通道** - 20 日高低點平均線系統 (UB/MA20/LB)，精準判斷止跌站穩與強勢噴出 |
| **Fundamental Analysis** | PE, PB, ROE/ROA, 股息率, 營收成長 |
| **Institutional Flow** | 外資、投信、自營商買賣超分析（支援 API Token） |
| **Stock Screening** | 多條件篩選股票，支援 CSV 匯出，進度條顯示 |

### 🤖 智能系統

| Feature | Description |
|---------|-------------|
| **SAPTA Engine** | 機器學習預漲偵測 (6 模組 + XGBoost)，詳見 [SAPTA 引擎](#sapta-引擎) |
| **AutoTS Forecasting** | AI 價格預測引擎 (AutoTS)，支援快速/完整兩種模式 |
| **Smart Money Screener** | 主力足跡選股 (Trend/Volume/Bias) |
| **Warehouse Sync** | 可同步本地台股倉庫資料庫到本地分析環境，供分析模組直接使用 |
| **Trading Plan** | 自動生成停利/停損/風險報酬計算 |
| **Prompt Hardening** | 股票分析 prompt 已統一為繁體中文、固定輸出結構、資料不足明示 |

### 📈 策略系統

| Strategy | Description |
|----------|-------------|
| **Farmer Planting** | 進階農夫播種術 - 基準價加減碼策略，適合趨勢股票長期持有 |
| **Momentum Breakout** | 動量突破策略 - ADX 強趨勢 + MACD 黃金交叉 + 成交量確認 |
| **MA Crossover** | 均線交叉策略 - EMA9/EMA21 交叉 + MA50 趨勢過濾 |
| **BB Squeeze** | 布林壓縮策略 - 低波動壓縮後的向上突破 |
| **Keltner Channel** | 短線突破策略 (BUY/HOLD/SELL/WATCH 信號) |
| **Happy Lines +** | **樂活五線譜 + 樂活通道** - 長線位階結合短線動能，實作「站回 LB 買進、跌破 UB 賣出」專業規則 |
| **Custom Strategies** | 支援自定義策略開發與回測 |

### 🛠️ 其他工具

| Feature | Description |
|---------|-------------|
| **Chart Generation** | 匯出價格圖表為 PNG 格式 (支援自訂主題) |
| **E2E Tests** | 584 tests with comprehensive coverage |

---

## SAPTA 引擎

**SAPTA** = *Smart Money Analysis via Pre-markup Accumulation Tracking Algorithm*

混合式 **規則引擎 + XGBoost 機器學習**的評分系統，偵測股票在主升段啟動前的**吸籌/壓縮階段**，讓使用者在法人佈局完成、爆發前提前進場。

### 決策輸出

| 狀態 | 分數 | 意義 |
|------|------|------|
| 🔴 `PRE-MARKUP` | ≥ 80 | 即將啟動，優先進場 |
| 🟠 `READY` | ≥ 65 | 接近就緒，密切觀察 |
| 🟡 `WATCHLIST` | ≥ 50 | 跡象初現，加入名單 |
| ⚫ `IGNORE` | < 50 | 條件不足，略過 |

### 6 個分析模組

```
模組                   最高分   偵測目標
────────────────────── ──────  ──────────────────────────────────────
Supply Absorption       20     爆量後守住 + 高低點墊高 (吸籌型態)
Compression             15     ATR 斜率收縮 + 振幅縮小 (壓縮型態)
BB Squeeze              15     布林帶寬度壓至歷史低位 (極度擠壓)
Elliott Wave            20     費波納契回調 38.2–61.8% + ABC 修正
Time Projection         15     費波納契時間窗口 (21/34/55/89/144 日) + 月相
Anti-Distribution       15     過濾派發訊號 (高量弱收、假突破)
────────────────────── ──────
合計滿分               100
```

### 評分流程

```
6 模組並發執行
    → 加權彙總 → 0-100 分
    → 假突破懲罰 (-10 分)
    → XGBoost 校準信心水準
    → 輸出 PRE-MARKUP / READY / WATCHLIST / IGNORE
```

### ML 模型

- **演算法**：XGBoost binary classifier
- **訓練目標**：20 個交易日內漲幅 ≥ 10%
- **特徵向量**：70+ 維（各模組原始特徵 + 彙總特徵）
- **訓練模式**：Walk-Forward（36 月訓練 / 6 月測試）
- **自動校準**：門檻值由訓練資料學習，寫入 `SaptaConfig`

### SAPTA 指令

```bash
/sapta 2330                # 分析單支股票
/sapta TW50                # 掃描台灣 50 成分股
/sapta-retrain             # 重新訓練 XGBoost 模型
/sapta-retrain --report    # 輸出特徵重要性報告
```

> 完整演算法文件：[docs/SAPTA_ALGORITHM.md](docs/SAPTA_ALGORITHM.md)

---

## Quick Start

### Installation

```bash
git clone https://github.com/alingowangxr/TW-Pulse-CLI.git
cd TW-Pulse-CLI
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS
pip install -e .
```

### Configuration

複製環境變數範例並設定 API Key：

```bash
cp .env.example .env
```

編輯 `.env`：

```env
# AI 模型（擇一設定）
DEEPSEEK_API_KEY=your_key          # 預設 AI 模型（推薦，deepseek-v4-flash）
ANTHROPIC_API_KEY=your_key         # Claude
OPENAI_API_KEY=your_key            # GPT
GEMINI_API_KEY=your_key            # Gemini

# 數據源
FINMIND_TOKEN=your_token           # 法人動向數據（推薦取得付費 Token）
FUGLE_API_KEY=your_key             # Fugle 即時數據（選配）

# 本地台股倉庫（選配）
PULSE_DATA__LOCAL_WAREHOUSE_DB=path/to/tw_stock_warehouse.db
```

### Launch

```bash
pulse
```

### Local Warehouse

如果你希望使用本地股票資料，請先執行 `/warehouse` 或 `/warehouse sync` 來建立 `tw_stock_warehouse.db`。
這個檔案不會隨 repository 一起上傳，因為資料庫可能很大，且內容通常是本機環境專用。

```bash
/warehouse
/warehouse sync --mode=copy
/warehouse sync --mode=run
```

---

## Command Examples

### 基本分析
```bash
/analyze 2330                      # 台積電綜合分析（即時串流回應）
/a 2330                            # 同上，縮寫版本
/chart 2330                        # 生成 K 線圖
/inst 2330                         # 法人買賣超
/plan 2330                         # 交易計畫
/forecast 2330                     # 快速模式價格預測 (7天)
/forecast 2330 14 full             # 完整模式價格預測 (14天)
```

`/analyze` 與相關 AI 分析指令會：
- 先抓取真實市場數據，再交由 AI 解讀
- 統一以繁體中文輸出
- 固定輸出核心摘要、資料完整度、技術面、基本面/籌碼面、綜合建議與風險追蹤
- 若資料不足，會直接標示缺少欄位，不會硬猜數字

### SAPTA 預漲偵測
```bash
/sapta 2330                        # 分析台積電是否處於預漲階段
/sapta TW50                        # 掃描台灣 50，列出 PRE-MARKUP 股票
/sapta-retrain                     # 重新訓練 ML 模型（需要時間）
/sapta-retrain --report            # 輸出特徵重要性與門檻分析
```

### 策略回測
```bash
/strategy                          # 查看所有可用策略
/strategy farmerplanting           # 查看農夫播種術策略詳情
/strategy farmerplanting 2330 backtest  # 執行回測（5年歷史數據）

/strategy momentumbreakout 2330 backtest  # 動量突破策略回測
/strategy macrossover 2330 backtest       # 均線交叉策略回測
/strategy bbsqueeze 2330 backtest         # 布林壓縮策略回測
```

### 智能選股
```bash
/screen                            # 股票篩選
/smart-money                       # 主力足跡選股
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [USAGE.md](USAGE.md) | 完整安裝與使用說明 |
| [TODO.md](TODO.md) | 未來改進計劃與路線圖 |
| [docs/SAPTA_ALGORITHM.md](docs/SAPTA_ALGORITHM.md) | SAPTA 演算法完整技術文件 |
| [docs/training_guide.md](docs/training_guide.md) | ML 模型訓練指南 |
| [docs/architecture.md](docs/architecture.md) | 系統架構與設計 |
| [docs/CONTRIB.md](docs/CONTRIB.md) | 貢獻指南 - 開發工作流與環境設定 |
| [docs/RUNBOOK.md](docs/RUNBOOK.md) | 運維手冊 - 部署與故障排除 |

---

## Tech Stack

### Core Technologies
- **Language**: Python 3.11+
- **TUI**: Textual + Rich
- **AI**: LiteLLM (DeepSeek/Groq/Gemini/Claude/GPT)

### Data & Analysis
- **Data Sources**: FinMind, Yahoo Finance, Fugle, local SQLite warehouse
- **ML/AI**: XGBoost, scikit-learn, AutoTS (M6 competition winner)
- **Analysis**: pandas, numpy, ta (Technical Analysis Library)

### Strategy & Backtesting
- **Backtesting Engine**: Custom-built with position management
- **Capital Management**: Dynamic capital allocation
- **Reporting**: Markdown reports with detailed metrics

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| **0.5.0** | **2026-05-05** | **效能優化：快取單例模式、FinMind 向量化、yfinance 非同步化、技術指標快取、SMA 向量加速、TUI 滾動修復、投資人友善版 AI 提示詞** |
| **0.4.6** | **2026-05-04** | **樂活通道 (LOHAS Channel) 整合：實作 20 日高低點平均線、站回 LB 買進/跌破 UB 賣出策略規則、AI 分析同步支援** |
| **0.4.5** | **2026-04-20** | **AI 分析提示詞重寫、SmartAgent 輸出統一繁中、run/run_stream 整合測試補強** |
| **0.4.4** | **2026-03-21** | **效能與架構優化：SAPTA 模組並發執行、smart_agent/screener 拆分重構、統一 logger、修正 561 tests 全通過** |
| 0.4.3 | 2026-03-20 | Bug fixes: 修正串流超時失效、圖表進度 UI 閃現、SAPTA 閾值鍵名遷移、AI 系統提示語言錯誤 |
| 0.4.2 | 2026-03-19 | 即時串流回應：AI 分析過程即時顯示，改善使用者體驗 |
| 0.4.1 | 2026-02-08 | AutoTS 預測引擎：取代 Prophet，支援快速/完整兩種模式 + 16 new tests |
| 0.3.1 | 2026-02-03 | 三大交易策略：動量突破、均線交叉、布林壓縮 + 42 new tests |
| 0.3.0 | 2026-01-27 | 策略回測系統、動態資金管理、FinMind Token 自動讀取 |
| 0.2.1 | 2026-01-22 | Keltner Channel indicator & strategy, 21 new tests |
| 0.2.0 | 2026-01-22 | E2E tests (461 total), SAPTA retrain CLI, chart customization |
| 0.1.10 | 2026-01-22 | Rich progress bar, chart customization, FinMind quota monitoring |
| 0.1.9 | 2026-01-22 | New indicators: ADX, CCI, Ichimoku Cloud; Cache TTL optimization |
| 0.1.8 | 2026-01-20 | Smart Money Screener, JSON 股票清單 |
| 0.1.7 | 2026-01-20 | SAPTA 圖表、基本面數據補救 |
| 0.1.6 | 2026-01-16 | DeepSeek 模型、測試覆蓋率提升 |
| 0.1.5 | 2026-01-20 | 環境變數修復、超時處理 |
| 0.1.4 | 2026-01-16 | CSV 匯出、類型提示 |
| 0.1.3 | 2026-01-15 | SAPTA 輸出優化 |
| 0.1.2 | 2026-01-14 | Fugle 整合 |
| 0.1.1 | 2026-01-14 | 台灣市場遷移 |
| 0.1.0 | 2026-01-13 | Initial release |

---

## Acknowledgments

### 🙏 Special Thanks

- **[@stanford201807](https://github.com/stanford201807)** - 感感謝提供策略回測系統、農夫播種術策略、動態資金管理等核心代碼，大幅提升了本專案的功能完整性

### 📚 Open Source Projects

- [Pulse-CLI](https://github.com/alingowangxr/Pulse-CLI) - 原始專案啟發
- [Textual](https://github.com/Textualize/textual) - 強大的 Python TUI 框架
- [Rich](https://github.com/Textualize/rich) - 優雅的終端格式化工具
- [yfinance](https://github.com/ranaroussi/yfinance) - Yahoo Finance API 封裝
- [FinMind](https://github.com/FinMind/FinMind) - 台灣金融數據 API
- [TA-Lib](https://github.com/bukosabino/ta) - 技術分析指標庫
- [LiteLLM](https://github.com/BerriAI/litellm) - 統一的 LLM API 介面

---

## Contributing

歡迎提交 Issue 或 Pull Request！

如果你開發了新的策略或功能，歡迎貢獻回本專案。

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

<div align="center">

**Made with ❤️ for Taiwan Stock Market**

[Report Bug](https://github.com/alingowangxr/TW-Pulse-CLI/issues) | [Request Feature](https://github.com/alingowangxr/TW-Pulse-CLI/issues)

⭐ If you find this project useful, please consider giving it a star!

</div>