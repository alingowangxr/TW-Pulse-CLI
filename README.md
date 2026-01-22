# TW-Pulse-CLI

<div align="center">

![TW-Pulse-CLI](https://img.shields.io/badge/TW--Pulse--CLI-58a6ff?style=for-the-badge&logo=python&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=for-the-badge&logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Beta-yellow?style=for-the-badge)

**AI-Powered Taiwan Stock Market Analysis CLI**

*台灣股市分析工具 (基於 AI 的終端介面)*

[Features](#features) • [Installation](#installation) • [Usage](USAGE.md) • [Roadmap](TODO.md)

[![GitHub](https://img.shields.io/badge/GitHub-alingowangxr%2FTW--Pulse--CLI-181717?style=flat-square&logo=github)](https://github.com/alingowangxr/TW-Pulse-CLI)

</div>

---

## About

**TW-Pulse-CLI** 是基於 [Pulse-CLI](https://github.com/alingowangxr/Pulse-CLI) 借鑑並重新改寫的台灣股市分析 CLI 工具。

原 Pulse-CLI 專注於印尼股市，本專案針對台灣市場進行優化，整合 FinMind、Yahoo Finance 等數據源，提供技術分析、基本面分析、法人動向、機器學習預測等功能。

---

## Features

| Feature | Description |
|---------|-------------|
| **Smart Agent** | AI 代理會在分析前獲取真實數據 |
| **Natural Language** | 支援繁體中文或英文提問 |
| **Technical Analysis** | RSI, MACD, 布林通道, SMA/EMA, ADX, CCI, Ichimoku 等 18+ 指標 |
| **Fundamental Analysis** | PE, PB, ROE/ROA, 股息率, 營收成長 |
| **Institutional Flow** | 外資、投信、自營商買賣超分析 |
| **Stock Screening** | 多條件篩選股票，支援 CSV 匯出，進度條顯示 |
| **Trading Plan** | 自動生成停利/停損/風險報酬計算 |
| **SAPTA Engine** | 機器學習預漲偵測 (6 模組 + XGBoost) + `/sapta-retrain` |
| **SAPTA Feature Analysis** | `/sapta-retrain --report` 特徵重要性 + `/sapta-retrain --thresholds` 閾值分析 |
| **Smart Money Screener** | 主力足跡選股 (Trend/Volume/Bias) |
| **Chart Generation** | 匯出價格圖表為 PNG 格式 (支援自訂主題) |
| **E2E Tests** | 461 tests with comprehensive coverage |

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
DEEPSEEK_API_KEY=your_key          # 預設 AI 模型
FINMIND_TOKEN=your_token           # 法人動向數據
```

### Launch

```bash
pulse
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

- **Language**: Python 3.11+
- **TUI**: Textual + Rich
- **AI**: LiteLLM (DeepSeek/Groq/Gemini/Claude/GPT)
- **Data**: FinMind, Yahoo Finance, Fugle
- **ML**: XGBoost, scikit-learn
- **Analysis**: pandas, numpy, ta

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
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

- [Pulse-CLI](https://github.com/alingowangxr/Pulse-CLI) - 原始專案啟發
- [Textual](https://github.com/Textualize/textual) - TUI 框架
- [yfinance](https://github.com/ranaroussi/yfinance) - Yahoo Finance API
- [FinMind](https://github.com/FinMind/FinMind) - 台灣金融數據
- [TA-Lib](https://github.com/bukosabino/ta) - 技術分析庫
- [Rich](https://github.com/Textualize/rich) - 終端格式化

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

<div align="center">

**Made with heart for Taiwan Stock Market**

[Report Bug](https://github.com/alingowangxr/TW-Pulse-CLI/issues) | [Request Feature](https://github.com/alingowangxr/TW-Pulse-CLI/issues)

</div>
