# TW-Pulse-CLI

<div align="center">

![TW-Pulse-CLI](https://img.shields.io/badge/TW--Pulse--CLI-58a6ff?style=for-the-badge&logo=python&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Beta-yellow?style=for-the-badge)

**AI-Powered Taiwan Stock Market Analysis & Strategy Backtesting CLI**

*台灣股市分析與策略回測工具 (基於 AI 的終端介面)*

[Features](#features) • [Installation](#installation) • [Usage](USAGE.md) • [Roadmap](TODO.md)

[![GitHub](https://img.shields.io/badge/GitHub-alingowangxr%2FTW--Pulse--CLI-181717?style=flat-square&logo=github)](https://github.com/alingowangxr/TW-Pulse-CLI)

</div>

---

## About

**TW-Pulse-CLI** 是基於 [Pulse-CLI](https://github.com/alingowangxr/Pulse-CLI) 借鑑並重新改寫的台灣股市分析 CLI 工具。

原 Pulse-CLI 專注於印尼股市，本專案針對台灣市場進行優化，整合 FinMind、Yahoo Finance 等數據源，提供技術分析、基本面分析、法人動向、機器學習預測、**策略回測**等功能。

---

## Features

### 🎯 核心功能

| Feature | Description |
|---------|-------------|
| **Smart Agent** | AI 代理會在分析前獲取真實數據 |
| **Natural Language** | 支援繁體中文或英文提問 |
| **Strategy Backtesting** | 🆕 完整的策略回測系統，支援多策略框架與績效報告 |
| **Dynamic Capital Management** | 🆕 動態資金管理，智能倉位控制 |
| **Trading Reports** | 🆕 詳細的交易報告與績效分析 |

### 📊 技術分析

| Feature | Description |
|---------|-------------|
| **Technical Analysis** | RSI, MACD, 布林通道, SMA/EMA, ADX, CCI, Ichimoku, Keltner Channel 等 20+ 指標 |
| **Fundamental Analysis** | PE, PB, ROE/ROA, 股息率, 營收成長 |
| **Institutional Flow** | 外資、投信、自營商買賣超分析（支援 API Token） |
| **Stock Screening** | 多條件篩選股票，支援 CSV 匯出，進度條顯示 |

### 🤖 智能系統

| Feature | Description |
|---------|-------------|
| **SAPTA Engine** | 機器學習預漲偵測 (6 模組 + XGBoost) + `/sapta-retrain` |
| **SAPTA Feature Analysis** | `/sapta-retrain --report` 特徵重要性 + 閾值分析 |
| **Smart Money Screener** | 主力足跡選股 (Trend/Volume/Bias) |
| **Trading Plan** | 自動生成停利/停損/風險報酬計算 |

### 📈 策略系統

| Strategy | Description |
|----------|-------------|
| **Farmer Planting** | 🆕 進階農夫播種術 - 基準價加減碼策略，適合趨勢股票長期持有 |
| **Keltner Channel** | 短線突破策略 (BUY/HOLD/SELL/WATCH 信號) |
| **Custom Strategies** | 支援自定義策略開發與回測 |

### 🛠️ 其他工具

| Feature | Description |
|---------|-------------|
| **Chart Generation** | 匯出價格圖表為 PNG 格式 (支援自訂主題) |
| **E2E Tests** | 461 tests with comprehensive coverage + 21 strategy tests |

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
DEEPSEEK_API_KEY=your_key          # 預設 AI 模型（推薦）
ANTHROPIC_API_KEY=your_key         # Claude
OPENAI_API_KEY=your_key            # GPT
GEMINI_API_KEY=your_key            # Gemini

# 數據源
FINMIND_TOKEN=your_token           # 法人動向數據（推薦取得付費 Token）
FUGLE_API_KEY=your_key             # Fugle 即時數據（選配）
```

### Launch

```bash
pulse
```

---

## Command Examples

### 基本分析
```bash
/analyze 2330                      # 台積電綜合分析
/chart 2330                        # 生成 K 線圖
/inst 2330                         # 法人買賣超
/plan 2330                         # 交易計畫
```

### 策略回測
```bash
/strategy                          # 查看所有可用策略
/strategy farmerplanting           # 查看農夫播種術策略詳情
/strategy farmerplanting 2330      # 查看策略在 2330 的狀態
/strategy farmerplanting 2330 backtest  # 執行回測（5年歷史數據）
```

### 智能選股
```bash
/screen                            # 股票篩選
/smart-money                       # 主力足跡選股
/sapta TW50                        # SAPTA 預漲偵測（台灣50）
/sapta-retrain                     # 重新訓練 SAPTA 模型
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [USAGE.md](USAGE.md) | 完整安裝與使用說明 |
| [TODO.md](TODO.md) | 未來改進計劃與路線圖 |
| [docs/SAPTA_ALGORITHM.md](docs/SAPTA_ALGORITHM.md) | SAPTA 算法詳解 |
| [docs/training_guide.md](docs/training_guide.md) | ML 模型訓練文檔 |
| [docs/architecture.md](docs/architecture.md) | 系統架構與設計 |

---

## Tech Stack

### Core Technologies
- **Language**: Python 3.11+
- **TUI**: Textual + Rich
- **AI**: LiteLLM (DeepSeek/Groq/Gemini/Claude/GPT)

### Data & Analysis
- **Data Sources**: FinMind, Yahoo Finance, Fugle
- **ML/AI**: XGBoost, scikit-learn
- **Analysis**: pandas, numpy, ta (Technical Analysis Library)

### Strategy & Backtesting
- **Backtesting Engine**: Custom-built with position management
- **Capital Management**: Dynamic capital allocation
- **Reporting**: Markdown reports with detailed metrics

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| **0.3.0** | **2026-01-27** | **策略回測系統、動態資金管理、FinMind Token 自動讀取** |
| 0.2.1 | 2026-01-22 | Keltner Channel indicator & strategy, 21 new tests |
| 0.2.0 | 2026-01-22 | E2E tests (461 total), SAPTA retrain CLI, chart customization |
| 0.1.10 | 2026-01-22 | Rich progress bar, chart customization, FinMind quota monitoring |
| 0.1.9 | 2026-01-22 | New indicators: ADX, CCI, Ichimoku Cloud; Cache TTL optimization |
| 0.1.8 | 2026-01-20 | Smart Money Screener, JSON 股票清單 |
| 0.1.7 | 2026-01-20 | SAPTA 圖表、基本面數據補救 |
| 0.1.6 | 2026-01-20 | DeepSeek 模型、測試覆蓋率提升 |
| 0.1.5 | 2026-01-20 | 環境變數修復、超時處理 |
| 0.1.4 | 2026-01-16 | CSV 匯出、類型提示 |
| 0.1.3 | 2026-01-15 | SAPTA 輸出優化 |
| 0.1.2 | 2026-01-14 | Fugle 整合 |
| 0.1.1 | 2026-01-14 | 台灣市場遷移 |
| 0.1.0 | 2026-01-13 | Initial release |

---

## Acknowledgments

### 🙏 Special Thanks

- **[@stanford201807](https://github.com/stanford201807)** - 感謝提供策略回測系統、農夫播種術策略、動態資金管理等核心代碼，大幅提升了本專案的功能完整性

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
