# Pulse CLI 系統架構文檔

> **Pulse CLI** - AI-Powered 台灣股市分析工具 - 系統架構總覽

## 目錄

1. [系統總覽](#系統總覽)
2. [模組架構](#模組架構)
3. [數據流程](#數據流程)
4. [核心組件](#核心組件)
5. [命令系統](#命令系統)
6. [配置管理](#配置管理)
7. [擴展點](#擴展點)

---

## 系統總覽

### 系統架構圖

```
┌─────────────────────────────────────────────────────────────────────────┐
│                          Pulse CLI 架構                                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐               │
│  │   User      │     │   TUI       │     │  Commands   │               │
│  │  (終端使用者) │◄──►│  Interface  │◄──►│  Registry   │               │
│  │             │     │  (Textual)  │     │             │               │
│  └─────────────┘     └─────────────┘     └──────┬──────┘               │
│                                                  │                      │
│  ┌──────────────────────────────────────────────┼────────────────────┐  │
│  │                                              ▼                    │  │
│  │                              ┌─────────────────────────────┐      │  │
│  │                              │      Smart Agent            │      │  │
│  │                              │    (AI Orchestrator)        │      │  │
│  │                              └──────────────┬──────────────┘      │  │
│  │                                             │                     │  │
│  │      ┌──────────────────────────────────────┼──────────────────┐  │  │
│  │      │                                      │                  │  │  │
│  │      ▼                                      ▼                  │  │  │
│  │  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    │  │  │
│  │  │ Stock   │    │ Tech    │    │Fundamen │    │ Broker  │    │  │  │
│  │  │ Data    │    │Analysis │    │  tal    │    │  Flow   │    │  │  │
│  │  │  (數據)  │    │(技術分析) │    │(基本面) │    │(法人流向)│    │  │  │
│  │  └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘    │  │  │
│  │       │              │              │              │         │  │  │
│  │       └──────────────┼──────────────┼──────────────┘         │  │  │
│  │                      │              │                        │  │  │
│  │                      ▼              ▼                        │  │  │
│  │               ┌─────────────────────────────┐               │  │  │
│  │               │       SAPTA Engine          │               │  │  │
│  │               │   (Pre-markup Detection)    │               │  │  │
│  │               │                             │               │  │  │
│  │               │  ┌───┐ ┌───┐ ┌───┐ ┌───┐  │               │  │  │
│  │               │  │Abs│ │Com│ │BB │ │Elli│  │               │  │  │
│  │               │  └───┘ └───┘ └───┘ └───┘  │               │  │  │
│  │               │  ┌───┐ ┌───┐              │               │  │  │
│  │               │  │Time│ │Anti│              │               │  │  │
│  │               │  └───┘ └───┘              │               │  │  │
│  │               │        + ML Model         │               │  │  │
│  │               └────────────┬──────────────┘               │  │  │
│  │                              │                              │  │  │
│  │                              ▼                              │  │  │
│  │               ┌─────────────────────────────┐               │  │  │
│  │               │   Trading Plan Generator    │               │  │  │
│  │               │    (交易計劃生成器)          │               │  │  │
│  │               └─────────────────────────────┘               │  │  │
│  │                                                              │  │  │
│  │      ┌────────────────────────────────────────────────────┐  │  │  │
│  │      │                   AI/LLM Layer                      │  │  │  │
│  │      │   (LiteLLM - 多模型支援: Groq/Gemini/Claude/GPT)   │  │  │  │
│  │      └────────────────────────────────────────────────────┘  │  │  │
│  │                                                               │  │  │
│  │  ┌─────────────────────────────────────────────────────────┐ │  │  │
│  │  │                      Data Layer                          │ │  │  │
│  │  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │ │  │  │
│  │  │  │FinMind  │  │yfinance │  │  Cache  │  │ tickers │    │ │  │  │
│  │  │  │  (API)  │  │  (API)  │  │(磁碟)   │  │(清單)   │    │ │  │  │
│  │  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │ │  │  │
│  │  └─────────────────────────────────────────────────────────┘ │  │  │
│  │                                                               │  │  │
│  └───────────────────────────────────────────────────────────────┘  │  │
│                                                                  │  │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                      Utilities                               │  │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │  │
│  │  │ Logger   │ │Formatters│ │Validators│ │Constants │        │  │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 技術棧

| 層面 | 技術 | 用途 |
|-----|------|------|
| **UI 框架** | [Textual](https://textual.textualize.io/) | TUI 介面 |
| **AI 整合** | [LiteLLM](https://docs.litellm.io/) | 多模型統一接口 |
| **數據獲取** | [yfinance](https://github.com/ranaroussi/yfinance) | Yahoo Finance (secondary) |
| **數據獲取** | [FinMind](https://finmindtrade.com/) | 台灣股市 API (primary) |
| **數據獲取** | [Fugle](https://www.fugle.tw/) | 實時報價 API (tertiary fallback) |
| **技術分析** | [TA-Lib](https://github.com/bukosabino/ta) | 技術指標 |
| **數據處理** | [Pandas](https://pandas.pydata.org/) | 數據處理 |
| **機器學習** | [XGBoost](https://xgboost.readthedocs.io/) | ML 模型 |
| **配置管理** | [Pydantic](https://docs.pydantic.dev/) | 類型驗證 |
| **終端美化** | [Rich](https://rich.readthedocs.io/) | 格式化輸出 |

### 專案結構

```
pulse-cli/
├── pulse/
│   ├── __init__.py                    # 入口點
│   │
│   ├── cli/                           # CLI 介面層
│   │   ├── __init__.py
│   │   ├── app.py                     # Textual 應用主程式
│   │   └── commands/
│   │       ├── __init__.py            # 命令註冊
│   │       ├── registry.py            # 命令分發器
│   │       ├── analysis.py            # 分析命令
│   │       ├── charts.py              # 圖表命令
│   │       ├── screening.py           # 篩選命令
│   │       └── advanced.py            # 進階命令
│   │
│   ├── core/                          # 核心業務邏輯
│   │   ├── __init__.py
│   │   ├── config.py                  # 配置管理 (Pydantic)
│   │   ├── models.py                  # 數據模型
│   │   ├── smart_agent.py             # AI 代理 orchestrator
│   │   ├── screener.py                # 股票篩選器
│   │   ├── trading_plan.py            # 交易計劃生成器
│   │   ├── chart_generator.py         # 圖表生成器
│   │   ├── forecasting.py             # 價格預測
│   │   │
│   │   ├── data/                      # 數據層
│   │   │   ├── __init__.py
│   │   │   ├── yfinance.py            # Yahoo Finance 獲取
│   │   │   ├── finmind_data.py        # FinMind API
│   │   │   ├── fugle.py               # Fugle Market Data (tertiary fallback)
│   │   │   ├── stockbit.py            # Stockbit (Legacy)
│   │   │   └── cache.py               # 磁碟緩存
│   │   │
│   │   ├── analysis/                  # 分析模組
│   │   │   ├── __init__.py
│   │   │   ├── technical.py           # 技術指標
│   │   │   ├── fundamental.py         # 基本面分析
│   │   │   ├── broker_flow.py         # 法人流向
│   │   │   └── sector.py              # 產業分析
│   │   │
│   │   └── sapta/                     # SAPTA 引擎
│   │       ├── __init__.py
│   │       ├── engine.py              # 主引擎
│   │       ├── models.py              # SAPTA 數據模型
│   │       ├── modules/               # 6 個分析模組
│   │       │   ├── base.py
│   │       │   ├── absorption.py
│   │       │   ├── compression.py
│   │       │   ├── bb_squeeze.py
│   │       │   ├── elliott.py
│   │       │   ├── time_projection.py
│   │       │   └── anti_distribution.py
│   │       ├── ml/                    # 機器學習
│   │       │   ├── __init__.py
│   │       │   ├── trainer.py         # 訓練器
│   │       │   ├── features.py        # 特徵提取
│   │       │   ├── labeling.py        # 標籤生成
│   │       │   └── data_loader.py     # 數據加載
│   │       └── data/                  # 模型數據
│   │           ├── sapta_model.pkl
│   │           └── thresholds.json
│   │
│   ├── ai/                            # AI 整合層
│   │   ├── __init__.py
│   │   ├── client.py                  # LiteLLM 客戶端
│   │   └── prompts.py                 # 系統提示詞
│   │
│   └── utils/                         # 工具層
│       ├── __init__.py
│       ├── logger.py                  # 日誌
│       ├── formatters.py              # 格式化
│       ├── validators.py              # 驗證器
│       ├── constants.py               # 常量
│       ├── retry.py                   # 重試機制
│       └── error_handler.py           # 錯誤處理
│
├── config/
│   └── pulse.yaml                     # 配置文件
│
├── data/
│   ├── tw_tickers.json                # 台股代號清單
│   ├── twse_tickers.json              # 上市清單
│   ├── otc_tickers.json               # 上櫃清單
│   ├── cache/                         # 數據緩存
│   └── logs/                          # 日誌文件
│
├── docs/                              # 文檔
│   ├── SAPTA_ALGORITHM.md
│   ├── training_guide.md
│   └── architecture.md
│
├── tests/                             # 測試
│   └── ...
│
├── pyproject.toml                     # 項目配置
├── README.md                          # 主文檔
└── .env.example                       # 環境變量模板
```

---

## 模組架構

### CLI 命令模組

```
pulse/cli/commands/
├── registry.py       # 輕量級分發器 (287 lines)
│                    # 解析命令並調用對應處理函數
│
├── analysis.py       # 分析命令
│   ├── analyze_command()      # /analyze - 完整分析
│   ├── technical_command()    # /technical - 技術分析
│   └── fundamental_command()  # /fundamental - 基本面分析
│
├── charts.py         # 圖表命令
│   ├── chart_command()        # /chart - 生成價格圖表
│   ├── forecast_command()     # /forecast - 價格預測
│   └── taiex_command()        # /taiex - 大盤分析
│
├── screening.py      # 篩選命令
│   ├── screen_command()       # /screen - 股票篩選
│   └── compare_command()      # /compare - 比較股票
│
└── advanced.py       # 進階命令
    ├── broker_command()       # /institutional - 法人流向
    ├── sector_command()       # /sector - 產業分析
    ├── plan_command()         # /plan - 交易計劃
    └── sapta_command()        # /sapta - SAPTA 分析
```

### SAPTA 引擎模組

```
pulse/core/sapta/
├── engine.py                 # 主引擎 (604 lines)
│    ├── analyze()            # 單股分析
│    ├── scan()               # 批量掃描
│    └── _run_modules()       # 執行 6 個模組
│
├── models.py                 # 數據模型
│    ├── SaptaConfig          # 配置
│    ├── SaptaResult          # 分析結果
│    ├── SaptaStatus          # 狀態枚舉
│    ├── ModuleScore          # 模組分數
│    └── MLModelInfo          # 模型信息
│
├── modules/                  # 6 個分析模組
│    ├── base.py              # 基類 BaseModule
│    ├── absorption.py        # 供給吸收 (25%)
│    ├── compression.py       # 波動收縮 (20%)
│    ├── bb_squeeze.py        # 布林擠壓 (15%)
│    ├── elliott.py           # 波浪分析 (15%)
│    ├── time_projection.py   # 時間投影 (15%)
│    └── anti_distribution.py # 反派發 (10%)
│
└── ml/                       # 機器學習
     ├── trainer.py           # 訓練器 (Walk-forward)
     ├── features.py          # 特徵提取 (60+ 特徵)
     ├── labeling.py          # 標籤生成
     └── data_loader.py       # 數據加載
```

### 模組權重配置

```python
# SAPTA 模組權重 (總和 100%)
weights = {
    "absorption": 25,         # 供給吸收 - 最重要
    "compression": 20,        # 波動收縮 - 重要
    "bb_squeeze": 15,         # 布林擠壓 - 中等
    "elliott": 15,            # 波浪分析 - 中等
    "time_projection": 15,    # 時間投影 - 輔助
    "anti_distribution": 10,  # 反派發 - 過濾器
}

# 狀態門檻
status_thresholds = {
    "PRE-MARKUP": 80,     # 準備突破
    "SIAP": 65,           # 接近就緒
    "WATCHLIST": 50,      # 觀察名單
    "ABAIKAN": 0,         # 跳過
}
```

---

## 數據流程

### 分析請求流程

```
用戶輸入: "/analyze 2330"
    │
    ▼
┌───────────────────┐
│  Command Registry │
│  (registry.py)    │
└─────────┬─────────┘
          │
          ▼
┌───────────────────────────┐
│  analyze_command()        │
│  (analysis.py)            │
└─────────┬─────────────────┘
          │
          ▼
┌───────────────────────────────────┐
│  Smart Agent                      │
│  1. 解析意圖                      │
│  2. 獲取數據 (yfinance/FinMind)   │
│  3. 執行分析                      │
│  4. 組裝回應                      │
└─────────┬─────────────────────────┘
          │
          ▼
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐  ┌───────┐
│ 技術  │  │ 基本面 │
│ 分析  │  │ 分析   │
└───┬───┘  └───┬───┘
    │          │
    └────┬─────┘
         │
         ▼
┌───────────────────────────────────┐
│  SAPTA Engine                     │
│  - 運行 6 個模組                   │
│  - 計算加權分數                   │
│  - ML 模型校正                    │
│  - 確定狀態                       │
└─────────┬─────────────────────────┘
          │
          ▼
┌───────────────────────────────────┐
│  AI Summary (LiteLLM)             │
│  - 生成分析摘要                   │
│  - 提供投資建議                   │
└─────────┬─────────────────────────┘
          │
          ▼
┌───────────────────────────────────┐
│  Response Formatter               │
│  - 格式化輸出                     │
│  - Rich 終端渲染                  │
└─────────┬─────────────────────────┘
          │
          ▼
用戶看到: 彩色終端輸出
```

### SAPTA 詳細流程

```
輸入: OHLCV 數據 (1年日線)
    │
    ▼
┌──────────────────────────────────────┐
│  6 個分析模組並行執行                 │
│  ┌────────┐ ┌────────┐ ┌────────┐   │
│  │Absorpt.│ │Compres.│ │BB Sqz. │   │
│  └────┬───┘ └────┬───┘ └────┬───┘   │
│       │          │          │       │
│  ┌────┴───┐ ┌────┴───┐ ┌────┴───┐   │
│  │ Elliott│ │ Time   │ │ Anti-  │   │
│  │        │ │Project.│ │Distrib.│   │
│  └────────┘ └────────┘ └────────┘   │
└──────────────┬──────────────────────┘
               │
               ▼
    ┌─────────────────────────┐
    │  Module Scores (各模組分數) │
    └──────────┬──────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  加權彙總                           │
│  score = Σ(module_score × weight)   │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  特徵提取 (60+ 維度)                 │
│  features = extract_features(scores)│
└──────────────┬───────────────────────┘
               │
               ▼
        ┌──────┴──────┐
        │             │
        ▼             ▼
   ┌─────────┐  ┌─────────────┐
   │ 門檻判斷 │  │ ML 模型預測 │
   │ (規則)   │  │ (XGBoost)   │
   └────┬────┘  └──────┬──────┘
        │              │
        └──────┬───────┘
               │
               ▼
┌──────────────────────────────────────┐
│  確定狀態                            │
│  PRE-MARKUP / SIAP / WATCHLIST /... │
└──────────────┬───────────────────────┘
               │
               ▼
┌──────────────────────────────────────┐
│  輸出結果                            │
│  - 分數 (0-100)                      │
│  - 狀態                              │
│  - 置信度                            │
│  - 模組分解                          │
│  - 訊號列表                          │
└──────────────────────────────────────┘
```

---

## 核心組件

### Smart Agent (智能代理)

```python
# pulse/core/smart_agent.py
class SmartAgent:
    """AI 代理 orchestrator - 協調所有分析組件"""
    
    async def analyze(self, ticker: str) -> AnalysisResult:
        """
        1. 獲取股票數據
        2. 執行技術分析
        3. 執行基本面分析
        4. 執行 SAPTA 分析
        5. 生成 AI 摘要
        6. 返回完整結果
        """
```

### 配置管理

```python
# pulse/core/config.py
class Settings(BaseSettings):
    """Pydantic 配置 - 環境變量優先"""
    
    ai: AISettings           # AI 配置
    data: DataSettings       # 數據配置
    analysis: AnalysisSettings  # 分析配置
    ui: UISettings           # UI 配置
```

**配置優先級**:
1. 環境變量 (`PULSE_*`)
2. `.env` 文件
3. `config/pulse.yaml`
4. 預設值

### 數據提供者

```python
# pulse/core/data/

class YFinanceFetcher:
    """Yahoo Finance - 備用數據源 (secondary)"""
    def get_history_df(ticker, period) -> pd.DataFrame:
        """獲取 OHLCV 數據"""

class FinMindData:
    """FinMind API - 台股數據 (primary)"""
    def get_institutional_flow(ticker, days) -> dict:
        """獲取法人買賣超"""

class FugleFetcher:
    """Fugle Market Data - 第三備援數據源 (tertiary)"""
    def get_history_df(ticker, start_date, end_date) -> pd.DataFrame:
        """獲取 OHLCV 數據"""
    def get_quote(ticker) -> dict:
        """獲取實時報價"""

class StockDataProvider:
    """統一數據接口 - 智能選擇數據源"""
    async def get_stock_data(ticker) -> StockData:
        """自動選擇最佳數據源 (FinMind → yfinance → Fugle)"""
        # fallback chain:
        # 1. Try FinMind first (primary - has institutional data)
        # 2. Fallback to yfinance (secondary - unlimited, no auth)
        # 3. Fallback to Fugle (tertiary - real-time quotes)
```

### 數據源優先級

| 優先級 | 數據源 | 用途 | 認證 |
|-------|--------|------|------|
| 1 (Primary) | FinMind | 法人動向、融資融券、基本面 | 需 API Token |
| 2 (Secondary) | Yahoo Finance | OHLCV、技術指標 | 無需認證 |
| 3 (Tertiary) | Fugle Market Data | 實時報價、Tick 數據 | 需 API Key |

### 錯誤處理

```python
# pulse/utils/error_handler.py

class PulseError(Exception):
    """基礎異常類"""
    pass

class APIError(PulseError):
    """API 調用錯誤"""
    pass

class DataNotFoundError(PulseError):
    """數據未找到"""
    pass

class RateLimitError(PulseError):
    """API 頻率限制"""
    pass

class NetworkError(PulseError):
    """網絡錯誤"""
    pass
```

---

## 命令系統

### 命令註冊模式

```python
# pulse/cli/commands/registry.py

# 命令映射表
COMMAND_HANDLERS = {
    "analyze": analyze_command,
    "a": analyze_command,
    "stock": analyze_command,
    "technical": technical_command,
    "ta": technical_command,
    "tech": technical_command,
    "fundamental": fundamental_command,
    "fa": fundamental_command,
    "fund": fundamental_command,
    # ... 更多命令
}

# 自然語言映射
NL_INTENTS = {
    "分析": "analyze",
    "技術分析": "technical",
    "基本面": "fundamental",
    "找預漲股票": "sapta_scan_premarkup",
    # ... 更多意圖
}
```

### 命令處理流程

```
用戶輸入: "> 分析 2330"
    │
    ▼
┌───────────────────────────────────┐
│  輸入解析                         │
│  - 識別命令類型 (斜槓/自然語言)    │
│  - 提取參數                       │
└─────────┬─────────────────────────┘
          │
          ▼
┌───────────────────────────────────┐
│  意圖分類                         │
│  - 映射到內部命令                 │
│  - 驗證參數                       │
└─────────┬─────────────────────────┘
          │
          ▼
┌───────────────────────────────────┐
│  權限檢查                         │
│  - API key 檢查                   │
│  - 數據可用性檢查                 │
└─────────┬─────────────────────────┘
          │
          ▼
┌───────────────────────────────────┐
│  執行命令                         │
│  - 調用對應 handler               │
│  - 處理異常                       │
└─────────┬─────────────────────────┘
          │
          ▼
┌───────────────────────────────────┐
│  格式化輸出                       │
│  - 組裝回應字符串                 │
│  - 終端渲染                       │
└─────────┬─────────────────────────┘
          │
          ▼
更新 TUI 顯示
```

---

## 配置管理

### 環境變量

```bash
# AI API Keys
GROQ_API_KEY=your_groq_key           # Groq (推薦 - 免費)
GEMINI_API_KEY=your_gemini_key       # Google Gemini
ANTHROPIC_API_KEY=your_claude_key    # Anthropic Claude
OPENAI_API_KEY=your_openai_key       # OpenAI GPT

# 預設模型
PULSE_AI__DEFAULT_MODEL=groq/llama-3.3-70b-versatile

# Data API Keys
FINMIND_TOKEN=your_finmind_token     # FinMind (法人動向)
FUGLE_API_KEY=your_fugle_key         # Fugle (實時報價備援)

# Debug
PULSE_DEBUG=false
```

### 配置文件

```yaml
# config/pulse.yaml

# AI Settings
ai:
  default_model: "groq/llama-3.3-70b-versatile"
  temperature: 0.7
  max_tokens: 4096
  timeout: 120

# FinMind Settings (Primary)
finmind:
  api_token: ""  # From FINMIND_TOKEN env var
  api_url: "https://api.finmindtrade.com/api"

# Fugle Settings (Tertiary Fallback)
fugle:
  api_key: ""    # From FUGLE_API_KEY env var
  api_url: "https://api.fugle.tw/v1"

# Data Settings
data:
  cache_ttl: 3600      # 1 hour
  default_period: "3mo"
  yfinance_suffix: ".TW"
  fallback_enabled: true  # Enable yfinance → Fugle fallback chain

# Analysis Settings
analysis:
  rsi_period: 14
  rsi_oversold: 30
  rsi_overbought: 70
  macd_fast: 12
  macd_slow: 26
  macd_signal: 9

# UI Settings
ui:
  theme: "dark"
  chart_width: 60
  chart_height: 15
  max_results: 50
```

---

## 擴展點

### 新增數據源

Pulse-CLI 支持多層級數據源 fallback 機制。如需新增數據源，可參考 `pulse/core/data/fugle.py` 的實現：

```python
# 步驟 1: 在 data/ 目錄新增 fetcher (參考 fugle.py)
class NewDataSource:
    """新增數據源的實現範例"""
    
    async def fetch_stock(self, ticker: str, start_date: str, end_date: str) -> StockData | None:
        """獲取股票數據"""
        pass
    
    async def fetch_history(self, ticker: str, start_date: str, end_date: str) -> pd.DataFrame | None:
        """獲取歷史數據"""
        pass

# 步驟 2: 更新 StockDataProvider 的 fallback 鏈
class StockDataProvider:
    def __init__(self):
        self.finmind_fetcher = FinMindFetcher()
        self.yfinance_fetcher = YFinanceFetcher()
        self.fugle_fetcher = FugleFetcher()  # 新增
        self.new_fetcher = NewDataSource()   # 新增
    
    async def get_stock_data(self, ticker: str) -> StockData:
        # 嘗試 FinMind → yfinance → Fugle → NewDataSource
        data = await self.finmind_fetcher.fetch_stock(ticker)
        if data: return data
        
        data = await self.yfinance_fetcher.fetch_stock(ticker)
        if data: return data
        
        data = await self.fugle_fetcher.fetch_stock(ticker)
        if data: return data
        
        return await self.new_fetcher.fetch_stock(ticker)  # 最後嘗試
```

**新增數據源的最佳實踐：**
1. 實現 `fetch_stock()` 返回 `StockData` 模型
2. 實現 `fetch_history()` 返回 `pd.DataFrame` (OHLCV)
3. 添加適當的錯誤處理和重試機制
4. 在 `StockDataProvider` 中註冊到 fallback 鏈

### 新增分析模組

```python
# 步驟 1: 在 modules/ 目錄新增模組
class NewModule(BaseModule):
    name = "new_module"
    max_score = 20.0
    
    def analyze(self, df: pd.DataFrame) -> ModuleScore:
        # 實現分析邏輯
        pass

# 步驟 2: 在 engine.py 中註冊
class SaptaEngine:
    def __init__(self):
        self.modules = {
            # ... 現有模組
            "new_module": NewModule(),
        }
```

### 新增命令

```python
# 步驟 1: 在 commands/ 目錄新增處理函數
async def new_command(app: "PulseApp", args: str) -> str:
    """新命令處理函數"""
    # 實現邏輯
    return result

# 步驟 2: 在 registry.py 中註冊
COMMAND_HANDLERS = {
    # ... 現有命令
    "newcmd": new_command,
}
```

### 新增 AI 模型

```python
# 步驟 1: 更新 config.py 中的可用模型
class AISettings(BaseSettings):
    available_models: dict[str, str] = {
        # ... 現有模型
        "provider/new-model": "New Model (Provider)",
    }

# 步驟 2: 用戶設置環境變量
# PULSE_AI__DEFAULT_MODEL=provider/new-model
```

---

## 參考資料

- [SAPTA 算法詳解](SAPTA_ALGORITHM.md)
- [模型訓練指南](training_guide.md)
- [官方 README](../../README.md)
- [pyproject.toml](../../pyproject.toml)
