# TW-Pulse-CLI 深度分析文檔

> **分析時間**：2026-01-22 | **版本**：v0.2.0 | **代碼規模**：61 Python 文件，461 測試

---

## 基本信息

| 屬性 | 值 |
|------|-----|
| **項目名稱** | TW-Pulse-CLI |
| **類型** | AI 驅動的台灣股市分析 CLI 工具 |
| **語言** | Python 3.11+ |
| **代碼規模** | 61 個 Python 文件 |
| **測試覆蓋** | 461 個 E2E 測試 (~6200 行測試代碼) |
| **狀態** | Beta (v0.2.0) |

---

## 核心架構 (七維透鏡分析)

### 世界 I：意念世界 (設計哲學)

#### 🧠 詮釋視角 - 核心使命

**「讓散戶擁有機構級的分析能力」**

Pulse-CLI 的設計初衷是將複雜的技術分析、機器學習預測和法人動向追蹤整合到一個終端介面中，讓一般投資者也能使用專業級工具。

**核心隱喻**：將 SAPTA 引擎比喻為「股市雷達」——它不預測價格，而是偵測主力吸籌的痕跡，幫助投資者在突破前發現機會。

#### ⏳ 演化視角 - 歷史沿革

```
Pulse-CLI 演化脈絡
├── v0.1.0 (2026-01-13)     初始發布 - 印尼市場版本
├── v0.1.1 (2026-01-14)     台灣市場遷移
├── v0.1.4 (2026-01-16)     CSV 匯出、類型提示
├── v0.1.6 (2026-01-20)     DeepSeek 模型整合
├── v0.1.8 (2026-01-20)     Smart Money Screener
├── v0.1.9 (2026-01-22)     新增 ADX, CCI, Ichimoku 指標
└── v0.2.0 (2026-01-22)     461 E2E 測試、SAPTA retrain CLI
```

### 世界 II：物質世界 (技術本體)

#### 🔍 機械視角 - 底層原理

**三層數據獲取機制 (Fallback Chain)**：

```
┌─────────────────────────────────────────────────────────────┐
│                    StockDataProvider                         │
├─────────────────────────────────────────────────────────────┤
│  1. FinMind API (首選)                                      │
│     ├── 法人買賣超數據 ✅                                   │
│     ├── 融資融券資料 ✅                                     │
│     ├── 基本面數據 ✅                                       │
│     └── 需要 API Token                                      │
│          │                                                  │
│          ▼ Fallback                                         │
│  2. Yahoo Finance (備用)                                    │
│     ├── OHLCV 數據 ✅                                       │
│     ├── 無需認證                                            │
│     └── 無法人數據 ❌                                       │
│          │                                                  │
│          ▼ Fallback                                         │
│  3. Fugle Market Data (第三備援)                            │
│     ├── 實時報價 ✅                                         │
│     └── 需要 API Key                                        │
└─────────────────────────────────────────────────────────────┘
```

**SAPTA 引擎核心流程**：

```
輸入: OHLCV 數據 (1年日線)
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│              6 個分析模組並行執行                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Absorption│ │Compression│ │BB Squeeze│ │ Elliott  │       │
│  │  (25%)   │ │  (20%)   │ │  (15%)   │ │  (15%)   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐                                  │
│  │Time Proj.│ │Anti-Dist.│                                  │
│  │  (15%)   │ │  (10%)   │                                  │
│  └──────────┘ └──────────┘                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              加權彙總: Score = Σ(module_score × weight)      │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              特徵提取 (60+ 維度)                             │
│              ┌─────────────────────────────────┐            │
│              │ ML 模型預測 (XGBoost)           │            │
│              │ confidence = model.predict_proba │            │
│              └─────────────────────────────────┘            │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              狀態分類                                        │
│  ┌─────────┬──────────┬────────────────────┐               │
│  │ PRE-MARKUP │ ≥80 │ 準備突破 (積極買入)  │               │
│  │ SIAP      │ 65-79│ 接近就緒 (密切監控) │               │
│  │ WATCHLIST │ 50-64│ 觀察名單 (列入關注) │               │
│  │ ABAIKAN   │ <50 │ 跳過 (暫時觀望)      │               │
│  └─────────┴──────────┴────────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

#### 🕸️ 系統視角 - 架構位置

```
Pulse-CLI 系統架構圖
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Pulse CLI 架構                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────┐     ┌─────────────┐     ┌─────────────┐                   │
│  │   User      │     │   TUI       │     │  Commands   │                   │
│  │  (終端使用者) │◄──►│  Interface  │◄──►│  Registry   │                   │
│  │             │     │  (Textual)  │     │             │                   │
│  └─────────────┘     └─────────────┘     └──────┬──────┘                   │
│                                                  │                          │
│  ┌──────────────────────────────────────────────┼──────────────────────┐   │
│  │                                              ▼                      │   │
│  │                              ┌─────────────────────────────┐        │   │
│  │                              │      Smart Agent            │        │   │
│  │                              │    (AI Orchestrator)        │        │   │
│  │                              └──────────────┬──────────────┘        │   │
│  │                                             │                       │   │
│  │      ┌──────────────────────────────────────┼──────────────────┐    │   │
│  │      │                                      │                  │    │   │
│  │      ▼                                      ▼                  │    │   │
│  │  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    │    │   │
│  │  │ Stock   │    │ Tech    │    │Fundamen │    │ Broker  │    │    │   │
│  │  │ Data    │    │Analysis │    │  tal    │    │  Flow   │    │    │   │
│  │  │  (數據)  │    │(技術分析) │    │(基本面) │    │(法人流向)│    │    │   │
│  │  └────┬────┘    └────┬────┘    └────┬────┘    └────┬────┘    │    │   │
│  │       │              │              │              │         │    │   │
│  │       └──────────────┼──────────────┼──────────────┘         │    │   │
│  │                      │              │                        │    │   │
│  │                      ▼              ▼                        │    │   │
│  │               ┌─────────────────────────────┐               │    │   │
│  │               │       SAPTA Engine          │               │    │   │
│  │               │   (Pre-markup Detection)    │               │    │   │
│  │               │                             │               │    │   │
│  │               │  ┌───┐ ┌───┐ ┌───┐ ┌───┐  │               │    │   │
│  │               │  │Abs│ │Com│ │BB │ │Elli│  │               │    │   │
│  │               │  └───┘ └───┘ └───┘ └───┘  │               │    │   │
│  │               │  ┌───┐ ┌───┐              │               │    │   │
│  │               │  │Time│ │Anti│              │               │    │   │
│  │               │  └───┘ └───┘              │               │    │   │
│  │               │        + ML Model         │               │    │   │
│  │               └────────────┬──────────────┘               │    │   │
│  │                              │                              │    │   │
│  │                              ▼                              │    │   │
│  │               ┌─────────────────────────────┐               │    │   │
│  │               │   Trading Plan Generator    │               │    │   │
│  │               │    (交易計劃生成器)          │               │    │   │
│  │               └─────────────────────────────┘               │    │   │
│  │                                                              │    │   │
│  │      ┌────────────────────────────────────────────────────┐  │    │   │
│  │      │                   AI/LLM Layer                      │  │    │   │
│  │      │   (LiteLLM - 多模型支援: Groq/Gemini/Claude/GPT)   │  │    │   │
│  │      └────────────────────────────────────────────────────┘  │    │   │
│  │                                                               │    │   │
│  │  ┌─────────────────────────────────────────────────────────┐ │    │   │
│  │  │                      Data Layer                          │ │    │   │
│  │  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐    │ │    │   │
│  │  │  │FinMind  │  │yfinance │  │  Cache  │  │ tickers │    │ │    │   │
│  │  │  │  (API)  │  │  (API)  │  │(磁碟)   │  │(清單)   │    │ │    │   │
│  │  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘    │ │    │   │
│  │  └─────────────────────────────────────────────────────────┘ │    │   │
│  │                                                               │    │   │
│  └───────────────────────────────────────────────────────────────┘    │   │
│                                                                  │     │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │                      Utilities                               │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐        │   │
│  │  │ Logger   │ │Formatters│ │Validators│ │Constants │        │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘        │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 世界 III：關係世界 (人機交互)

#### 👥 行為視角 - 開發者體驗

**命令系統設計**：

Pulse-CLI 採用命令註冊模式，支持自然語言和斜槓命令：

```python
# 命令映射表示例
COMMAND_HANDLERS = {
    "analyze": analyze_command,
    "a": analyze_command,           # 別名
    "stock": analyze_command,       # 別名
    "technical": technical_command,
    "ta": technical_command,        # 別名
    # ...
}

# 自然語言映射
NL_INTENTS = {
    "分析": "analyze",
    "技術分析": "technical",
    "基本面": "fundamental",
    "找預漲股票": "sapta_scan_premarkup",
}
```

**TUI 交互模式**：

- `/` 開頭觸發命令面板 (Command Palette)
- 自然語言輸入由 Smart Agent 解析意圖
- 支援對話歷史和上下文記憶
- 模型熱切換 (Ctrl/Command + K)

#### ⚔️ 對抗視角 - 反模式與陷阱

**常見錯誤模式**：

| 類型 | 錯誤行為 | 防禦策略 |
|------|---------|---------|
| **派發陷阱** | 買入主力正在出貨的股票 | Anti-Distribution Module (-8 分) |
| **假突破** | 追隨無量突破 | 量能驗證 (-5 分 penalty) |
| **逆勢操作** | 在下跌趨勢中做多 | Elliott Wave 確認 Wave 3-5 |
| **過度交易** | 頻繁進出 | SAPTA 置信度過濾 |

### 世界 IV：行動世界 (實踐落地)

#### 🌏 實用視角 - 業務場景

**核心使用場景**：

1. **預漲股票掃描** (`/sapta scan tw50`)
   - 掃描台灣 50 指數成分股
   - 過濾 PRE-MARKUP 狀態股票
   - 按分數排序輸出

2. **個股深度分析** (`/analyze 2330`)
   - 獲取即時股價數據
   - 執行技術分析 (RSI, MACD, 布林通道等)
   - 執行基本面分析 (PE, PB, ROE)
   - SAPTA 預漲評分
   - AI 綜合建議

3. **法人動向追蹤** (`/institutional 2330`)
   - 外資買賣超
   - 投信動向
   - 自營商交易

4. **交易計劃生成** (`/plan 2330`)
   - 自動計算停利/停損位
   - 風險報酬比計算
   - 仓位建議

#### 📦 安裝與配置

```bash
# 1. 克隆並安裝
git clone https://github.com/alingowangxr/TW-Pulse-CLI.git
cd TW-Pulse-CLI
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS
pip install -e .

# 2. 配置環境變量
cp .env.example .env

# 編輯 .env
DEEPSEEK_API_KEY=your_key          # 預設 AI 模型
FINMIND_TOKEN=your_token           # 法人動向數據

# 3. 啟動
pulse
```

#### 🔧 技術棧總覽

| 層面 | 技術 | 用途 |
|-----|------|------|
| **UI 框架** | Textual | TUI 介面 |
| **AI 整合** | LiteLLM | 多模型統一接口 |
| **數據獲取** | FinMind / yfinance / Fugle | 台灣股市 API |
| **技術分析** | ta (TA-Lib wrapper) | 技術指標 |
| **數據處理** | Pandas / NumPy | 數據處理 |
| **機器學習** | XGBoost / scikit-learn | ML 模型 |
| **配置管理** | Pydantic | 類型驗證 |
| **終端美化** | Rich | 格式化輸出 |

---

## 模組詳解

### SAPTA 六大分析模組

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SAPTA 六大分析模組                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  1. Supply Absorption Module (供給吸收) - 權重 25%          │   │
│  │     - 量能吸收: 大量賣出但價格撐住 (+8)                       │   │
│  │     - 底部墊高: 連續 higher lows (+6)                        │   │
│  │     - 收盤強度: 收盤位於 K 線上半部 (+6)                      │   │
│  │     - 分配警示: 出現 distribution candles (-4)              │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  2. Compression Module (波動收縮) - 權重 20%                │   │
│  │     - 波動收窄: ATR < 50% 平均 (+10)                        │   │
│  │     - 區間收斂: High-Low 持續縮小 (+6)                      │   │
│  │     - 低波動確認: 維持低波動 N 天 (+4)                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  3. BB Squeeze Module (布林擠壓) - 權重 15%                 │   │
│  │     - 擠壓偵測: BB 寬度 < 20日低點 (+8)                      │   │
│  │     - 接近下軌: 價格接近布林下軌 (+4)                        │   │
│  │     - 支撐確認: 下軌/中軌提供支撐 (+3)                       │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  4. Elliott Wave Module (波浪分析) - 權重 15%               │   │
│  │     - Wave 3: 推進浪第三波 (+15)                            │   │
│  │     - Wave 5: 推進浪第五波 (+12)                            │   │
│  │     - Wave C: 調整浪 C 波 (+10)                             │   │
│  │     - 回撤確認: 符合 Fibonacci 回撤 (+5)                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  5. Time Projection Module (時間投影) - 權重 15%            │   │
│  │     - 時間窗口: 接近 Fib 時間目標 (+8)                       │   │
│  │     - 循環週期: 符合歷史週期 (+4)                            │   │
│  │     - 近日轉折: 3-5 日內可能轉折 (+3)                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  6. Anti-Distribution Module (反派發) - 權重 10%            │   │
│  │     - 派發確認: 高量+弱收盤 (-8)                             │   │
│  │     - 假突破: 突破後迅速拉回 (-5)                            │   │
│  │     - 量價背離: 上漲但量能萎縮 (-4)                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

### 數據模型層

```python
# 核心數據模型
from pulse.core.models import StockData, FundamentalData, TechnicalIndicators

# StockData: 即時股價數據
@dataclass
class StockData:
    ticker: str           # 股票代號 (e.g., "2330")
    name: str            # 公司名稱
    current_price: float # 當前價格
    previous_close: float# 昨日收盤
    change: float        # 漲跌
    change_percent: float# 漲跌幅
    volume: int          # 成交量
    avg_volume: int      # 平均成交量

# SaptaResult: SAPTA 分析結果
@dataclass
class SaptaResult:
    ticker: str
    final_score: float   # 最終分數 (0-100)
    status: SaptaStatus  # PRE-MARKUP / SIAP / WATCHLIST / ABAIKAN
    confidence: ConfidenceLevel  # HIGH / MEDIUM / LOW
    wave_phase: str | None       # 波浪位置
    modules: dict       # 各模組分數詳情
```

---

## 代碼結構統計

```
Pulse-CLI 代碼結構
├── pulse/                          # 主程式碼目錄
│   ├── ai/                         # AI 整合層
│   │   ├── client.py               # LiteLLM 客戶端 (287 行)
│   │   └── prompts.py              # 系統提示詞
│   │
│   ├── cli/                        # CLI 介面層
│   │   ├── app.py                  # Textual 應用主程式 (489 行)
│   │   └── commands/
│   │       ├── registry.py         # 命令分發器
│   │       ├── analysis.py         # 分析命令
│   │       ├── charts.py           # 圖表命令
│   │       ├── screening.py        # 篩選命令
│   │       └── advanced.py         # 進階命令
│   │
│   ├── core/                       # 核心業務邏輯
│   │   ├── agent.py                # Smart Agent (443 行)
│   │   ├── config.py               # 配置管理 (219 行)
│   │   ├── models.py               # 數據模型
│   │   ├── smart_agent.py          # AI 代理 orchestrator
│   │   ├── screener.py             # 股票篩選器
│   │   ├── trading_plan.py         # 交易計劃生成器
│   │   ├── chart_generator.py      # 圖表生成器
│   │   ├── forecasting.py          # 價格預測
│   │   ├── data/                   # 數據層
│   │   │   ├── stock_data_provider.py  # 統一數據接口 (371 行)
│   │   │   ├── finmind_data.py     # FinMind API
│   │   │   ├── fugle.py            # Fugle Market Data
│   │   │   └── yfinance.py         # Yahoo Finance
│   │   ├── analysis/               # 分析模組
│   │   │   ├── technical.py        # 技術指標
│   │   │   ├── fundamental.py      # 基本面分析
│   │   │   ├── institutional_flow.py # 法人流向
│   │   │   └── sector.py           # 產業分析
│   │   └── sapta/                  # SAPTA 引擎
│   │       ├── engine.py           # 主引擎 (604 行)
│   │       ├── models.py           # SAPTA 數據模型
│   │       ├── modules/            # 6 個分析模組
│   │       │   ├── base.py
│   │       │   ├── absorption.py
│   │       │   ├── compression.py
│   │       │   ├── bb_squeeze.py
│   │       │   ├── elliott.py
│   │       │   ├── time_projection.py
│   │       │   └── anti_distribution.py
│   │       └── ml/                 # 機器學習
│   │           ├── trainer.py
│   │           ├── features.py
│   │           ├── labeling.py
│   │           └── data_loader.py
│   │
│   └── utils/                      # 工具層
│       ├── logger.py               # 日誌
│       ├── formatters.py           # 格式化
│       ├── validators.py           # 驗證器
│       ├── constants.py            # 常量
│       ├── retry.py                # 重試機制
│       └── error_handler.py        # 錯誤處理
│
├── tests/                          # 測試目錄
│   ├── test_e2e.py                # E2E 測試 (16KB)
│   ├── test_core/
│   │   ├── test_analysis/
│   │   ├── test_data/
│   │   └── test_sapta/
│   └── test_utils/
│
├── config/
│   └── pulse.yaml                  # 配置文件
│
├── data/
│   ├── tw_tickers.json            # 台股代號清單
│   ├── cache/                     # 數據緩存
│   └── logs/                      # 日誌文件
│
├── docs/
│   ├── architecture.md            # 系統架構文檔 (792 行)
│   ├── SAPTA_ALGORITHM.md         # SAPTA 算法詳解 (476 行)
│   ├── training_guide.md          # ML 模型訓練文檔
│   └── GITHUB_UPLOAD_GUIDE.md     # GitHub 上傳指南
│
├── pyproject.toml                 # 項目配置
├── README.md                      # 主文檔
├── USAGE.md                       # 使用說明
├── CODEBASE.md                    # 項目上下文
└── TODO.md                        # 待辦事項
```

---

## 擴展點指南

### 新增數據源

```python
# 步驟 1: 參考 fugle.py 實現新的 Fetcher
class NewDataSource:
    async def fetch_stock(self, ticker: str, start_date: str, end_date: str) -> StockData | None:
        """獲取股票數據"""
        pass

# 步驟 2: 更新 StockDataProvider 的 fallback 鏈
class StockDataProvider:
    def __init__(self):
        self.new_fetcher = NewDataSource()  # 新增
    
    async def fetch_stock(self, ticker: str, period: str = "3mo") -> StockData | None:
        # 嘗試現有數據源...
        # 最後嘗試新的數據源
        data = await self.new_fetcher.fetch_stock(ticker)
        return data
```

### 新增 SAPTA 模組

```python
# 步驟 1: 在 modules/ 目錄新增模組
class NewModule(BaseModule):
    name = "new_module"
    max_score = 20.0
    
    def analyze(self, df: pd.DataFrame) -> ModuleScore:
        # 實現分析邏輯
        pass

# 步驲 2: 在 engine.py 中註冊
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
    return result

# 步驟 2: 在 registry.py 中註冊
COMMAND_HANDLERS = {
    # ... 現有命令
    "newcmd": new_command,
}
```

---

## 常見問題 (FAQ)

<details>
<summary><strong>Q1: Pulse-CLI 與其他股市分析工具的核心差異是什麼？</strong></summary>

**A:** Pulse-CLI 的核心差異在於：
1. **SAPTA 引擎**：專門偵測主力吸籌行為，而非單純預測價格
2. **多數據源整合**：FinMind (法人數據) + yfinance (備用) + Fugle (實時報價)
3. **AI 代理**：自然語言輸入 + Smart Agent 自動意圖識別
4. **開源可擴展**：完整的擴展點設計，社區可自由擴充
</details>

<details>
<summary><strong>Q2: SAPTA 評分的可靠性如何？</strong></summary>

**A:** SAPTA 評分結合了規則引擎和 ML 模型：
- **規則引擎**：6 個模組獨立評分，加權彙總
- **ML 校正**：XGBoost 模型學習歷史數據的模式
- **置信度機制**：多模組確認時提升置信度
- **Walk-forward 訓練**：每 6 個月重新訓練，保持模型時效性
</details>

<details>
<summary><strong>Q3: 如何切換 AI 模型？</strong></summary>

**A:** 有三種方式：
1. **環境變量**：設置 `PULSE_AI__DEFAULT_MODEL=groq/llama-3.3-70b-versatile`
2. **對話內指令**：輸入 `/model` 或按 `Ctrl/Cmd + K`
3. **配置修改**：編輯 `config/pulse.yaml` 的 `ai.default_model`
</details>

<details>
<summary><strong>Q4: 數據延遲和準確性如何？</strong></summary>

**A:**
- **FinMind**：延遲 15-30 分鐘 (需要 API Token)
- **yfinance**：延遲 1-5 分鐘 (免費，無需認證)
- **Fugle**：實時報價 (需要 API Key，作為第三備援)
- **緩存策略**：默認 30 分鐘過期，可通過 `cache_ttl` 配置
</details>

<details>
<summary><strong>Q5: 支援哪些技術指標？</strong></summary>

**A:** 支援 18+ 技術指標：
- **趨勢指標**：SMA, EMA, ADX, Ichimoku Cloud
- **動量指標**：RSI, MACD, CCI
- **波動指標**：Bollinger Bands, ATR
- **成交量指標**：Volume SMA, Volume Spike
</details>

<details>
<summary><strong>Q6: 如何貢獻代碼或回報問題？</strong></summary>

**A:**
1. **GitHub Issues**：https://github.com/alingowangxr/TW-Pulse-CLI/issues
2. **Pull Request**：Fork 後提交 PR
3. **文檔改進**：直接編輯 docs/ 目錄下的 Markdown 文件
4. **測試貢獻**：在 tests/ 目錄下新增測試
</details>

<details>
<summary><strong>Q7: 是否支援期權或期貨分析？</strong></summary>

**A:** 目前版本專注於股票分析，未來可能擴展：
- 可通過 `SmartAgent` 擴展新的分析工具
- SAPTA 引擎的模組化設計便於新增期貨專用模組
- 數據層已支持多數據源，可接入期貨 API
</details>

<details>
<summary><strong>Q8: 系統需求和效能如何？</strong></summary>

**A:**
- **Python**：3.11+
- **記憶體**：建議 4GB+ (ML 模型載入約 500MB)
- **網路**：需要穩定的網路連接以獲取市場數據
- **效能**：單股分析約 3-5 秒，批量掃描取決於股票數量
</details>

---

## 記憶檢查點

<details>
<summary><strong>測驗 1: Pulse-CLI 的數據獲取優先順序是什麼？</strong></summary>

**答案**：FinMind (首選) → yfinance (備用) → Fugle (第三備援)
</details>

<details>
<summary><strong>測驗 2: SAPTA 引擎包含哪 6 個分析模組？</strong></summary>

**答案**：
1. Supply Absorption (供給吸收) - 25%
2. Compression (波動收縮) - 20%
3. BB Squeeze (布林擠壓) - 15%
4. Elliott Wave (波浪分析) - 15%
5. Time Projection (時間投影) - 15%
6. Anti-Distribution (反派發) - 10%
</details>

<details>
<summary><strong>測驗 3: SAPTA 狀態分類的門檻是什麼？</strong></summary>

**答案**：
- PRE-MARKUP：≥ 80 分
- SIAP：65-79 分
- WATCHLIST：50-64 分
- ABAIKAN：< 50 分
</details>

<details>
<summary><strong>測驗 4: Pulse-CLI 使用了哪些 AI 模型提供商？</strong></summary>

**答案**：DeepSeek、Anthropic (Claude)、OpenAI (GPT)、Google (Gemini)、Groq (Llama)
</details>

<details>
<summary><strong>測驗 5: TUI 框架使用的是什麼？</strong></summary>

**答案**：Textual (由 Textualize 開發的 Python TUI 框架)
</details>

<details>
<summary><strong>測驗 6: ML 模型使用什麼算法？</strong></summary>

**答案**：XGBoost Classifier (主要) + sklearn GradientBoostingClassifier (備用)
</details>

<details>
<summary><strong>測驗 7: 命令面板如何觸發？</strong></summary>

**答案**：輸入 `/` 開頭的指令，會自動彈出命令面板 (Command Palette)
</details>

<details>
<summary><strong>測驗 8: 代碼庫中有多少個 Python 文件？</strong></summary>

**答案**：61 個 Python 文件
</details>

---

## 延伸閱讀

- **Pulse-CLI GitHub** - 官方倉庫
- **Textual 文檔** - TUI 框架
- **LiteLLM 文檔** - 多模型統一接口
- **FinMind API** - 台灣金融數據
- **TA-Lib** - 技術分析庫
- **XGBoost 文檔** - 機器學習庫
- **SAPTA 算法詳解** - 專案內算法文檔
- **系統架構文檔** - 專案內架構文檔

---

*文檔生成時間：2026-01-22*
*分析範圍：Pulse-CLI v0.2.0*
*代碼行數：~10,000 行 (含測試)*
*測試覆蓋：461 個 E2E 測試*
