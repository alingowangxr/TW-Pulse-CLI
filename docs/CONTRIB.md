# 貢獻指南 (Contribution Guide)

> 本文件從 `pyproject.toml` 與 `.env.example` 自動生成
> 生成日期：2026-02-07

## 目錄

- [開發環境設置](#開發環境設置)
- [可用腳本與命令](#可用腳本與命令)
- [環境變數配置](#環境變數配置)
- [測試流程](#測試流程)
- [程式碼規範](#程式碼規範)
- [開發工作流](#開發工作流)
- [專案結構](#專案結構)

---

## 開發環境設置

### 系統需求

- **Python**: >= 3.11
- **作業系統**: Windows/Linux/macOS
- **套件管理**: pip (建議使用虛擬環境)

### 安裝步驟

```bash
# 1. 複製專案
git clone https://github.com/alingowangxr/TW-Pulse-CLI.git
cd TW-Pulse-CLI

# 2. 建立虛擬環境
python -m venv .venv

# 3. 啟動虛擬環境
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# 4. 安裝專案（開發模式）
pip install -e ".[dev]"

# 5. 複製環境變數範例
cp .env.example .env

# 6. 編輯 .env 填入你的 API 金鑰
```

### 開發依賴

安裝開發模式時會自動安裝以下工具：

| 工具 | 用途 | 版本 |
|------|------|------|
| pytest | 單元測試 | >=7.0.0 |
| pytest-asyncio | 異步測試 | >=0.21.0 |
| pytest-cov | 測試覆蓋率 | >=4.0.0 |
| ruff | 程式碼檢查與格式化 | >=0.1.0 |
| mypy | 靜態類型檢查 | >=1.0.0 |

---

## 可用腳本與命令

### 應用程式入口

| 命令 | 說明 | 來源 |
|------|------|------|
| `pulse` | 啟動 TUI 應用程式 | `pulse.cli.app:main` |

### 常用開發命令

```bash
# 運行應用
pulse
# 或
python -m pulse.cli.app

# 運行所有測試
python -m pytest

# 運行特定測試檔案
python -m pytest tests/test_core/test_strategies/test_bb_squeeze.py

# 運行測試並生成覆蓋率報告
python -m pytest --cov=pulse

# 程式碼檢查
ruff check pulse/

# 程式碼格式化
ruff format pulse/

# 靜態類型檢查
mypy pulse/
```

---

## 環境變數配置

### AI 模型配置 (LiteLLM)

設定以下 API 金鑰之一即可使用 AI 功能：

| 變數名稱 | 說明 | 取得位置 |
|----------|------|----------|
| `DEEPSEEK_API_KEY` | DeepSeek API（預設，性價比高） | https://platform.deepseek.com/api-keys |
| `GEMINI_API_KEY` | Google Gemini | https://aistudio.google.com/apikey |
| `ANTHROPIC_API_KEY` | Anthropic Claude | https://console.anthropic.com/ |
| `OPENAI_API_KEY` | OpenAI GPT-4o | https://platform.openai.com/api-keys |
| `GROQ_API_KEY` | Groq Llama（有免費額度） | https://console.groq.com/keys |

**AI 行為配置：**

| 變數名稱 | 預設值 | 說明 |
|----------|--------|------|
| `PULSE_AI__DEFAULT_MODEL` | `deepseek/deepseek-chat` | 預設 AI 模型 |
| `PULSE_AI__TEMPERATURE` | `0.7` | 溫度參數 (0.0-2.0) |
| `PULSE_AI__MAX_TOKENS` | `4096` | 最大回應字數 |
| `PULSE_AI__TIMEOUT` | `120` | 請求超時（秒） |

**可用模型列表：**
- `deepseek/deepseek-chat` - 預設，成本效益高
- `gemini/gemini-2.0-flash`
- `gemini/gemini-2.5-flash-preview-05-20`
- `anthropic/claude-sonnet-4-20250514`
- `openai/gpt-4o`
- `groq/llama-3.3-70b-versatile` - 免費！

### 數據源配置

| 變數名稱 | 說明 | 取得位置 |
|----------|------|----------|
| `FINMIND_TOKEN` | FinMind API Token（法人動向數據） | https://finmindtrade.com/analysis/#/account/login |
| `FUGLE_API_KEY` | Fugle 即時報價（選配） | https://developer.fugle.tw/ |

### 應用程式設定

| 變數名稱 | 預設值 | 說明 |
|----------|--------|------|
| `PULSE_DEBUG` | `false` | 啟用除錯模式 |
| `PULSE_DATA__CACHE_TTL` | `3600` | 快取存活時間（秒） |
| `PULSE_DATA__DEFAULT_PERIOD` | `3mo` | 預設歷史數據期間 |

### 環境變數範例

```bash
# AI 配置（擇一設定）
DEEPSEEK_API_KEY=sk-xxx
GEMINI_API_KEY=your-gemini-api-key

# 數據源
FINMIND_TOKEN=your-token

# 應用設定
PULSE_DEBUG=false
PULSE_DATA__CACHE_TTL=3600
```

---

## 測試流程

### 測試結構

測試檔案遵循原始碼結構：

```
tests/
├── test_core/
│   ├── test_strategies/
│   │   ├── test_bb_squeeze.py
│   │   └── ...
│   └── ...
├── test_ai/
└── test_utils/
```

### 執行測試

```bash
# 全部測試
python -m pytest

# 特定目錄
python -m pytest tests/test_core/

# 特定檔案
python -m pytest tests/test_core/test_strategies/test_bb_squeeze.py

# 包含覆蓋率
python -m pytest --cov=pulse --cov-report=html

#  verbose 模式（顯示詳細資訊）
python -m pytest -v
```

### 測試規範

- 使用 `pytest` 框架
- 異步測試自動處理（`asyncio_mode = "auto"`）
- 測試函式命名：`test_` 前綴
- 測試類別命名：`Test` 前綴

---

## 程式碼規範

### 格式化與檢查

專案使用 **Ruff** 進行程式碼檢查與格式化：

```bash
# 檢查程式碼問題
ruff check pulse/

# 自動修復可修復的問題
ruff check pulse/ --fix

# 格式化程式碼
ruff format pulse/
```

### 配置規則

- **目標 Python 版本**: 3.11
- **行長限制**: 100 字元
- **忽略的規則**: E501（行長超過限制，因為我們用 100 而非 88）
- **啟用的規則**: E, F, I, N, W, UP

### 類型檢查

```bash
mypy pulse/
```

配置：
- **Python 版本**: 3.11
- **嚴格模式**: 啟用
- **忽略缺失導入**: 是

### 命名規範

- **程式碼**: 英文命名
- **UI 文字**: 繁體中文
- **註解**: 繁體中文
- **股票代號**: 4 位數字（如 2330 代表台積電）

---

## 開發工作流

### 1. 開始新功能

```bash
# 確保在 main 分支且已更新
git checkout main
git pull origin main

# 建立功能分支
git checkout -b feat/your-feature-name
```

### 2. 開發與測試

```bash
# 開發過程中持續運行測試
python -m pytest -x -v  # -x: 失敗即停止，-v: verbose

# 提交前檢查
ruff check pulse/
ruff format pulse/
mypy pulse/
python -m pytest
```

### 3. 提交規範

使用約定式提交（Conventional Commits）：

```
feat: 新增功能
fix: 修復問題
docs: 文件更新
style: 程式碼格式（不影響功能）
refactor: 重構
perf: 效能優化
test: 測試相關
chore: 建構/工具相關
```

範例：
```bash
git commit -m "feat: 新增布林壓縮策略回測功能"
git commit -m "fix: 修復 FinMind API 超時問題"
git commit -m "docs: 更新 API 文件"
```

### 4. 提交前檢查清單

- [ ] 所有測試通過
- [ ] Ruff 檢查無錯誤
- [ ] MyPy 類型檢查通過
- [ ] 程式碼已格式化
- [ ] 文件已更新（如需要）

---

## 專案結構

```
TW-Pulse-CLI/
├── pulse/                    # 主要原始碼
│   ├── cli/                 # TUI 層
│   │   ├── app.py          # 應用程式入口
│   │   └── commands/       # 指令處理
│   ├── core/               # 業務邏輯
│   │   ├── data/          # 數據層
│   │   ├── strategies/    # 策略系統
│   │   ├── sapta/         # SAPTA 引擎
│   │   └── models.py      # 資料模型
│   ├── ai/                 # AI 整合
│   ├── utils/              # 工具函式
│   └── reports/            # 報告生成
├── tests/                  # 測試檔案
├── docs/                   # 文件
├── data/                   # 資料快取
├── scripts/                # 輔助腳本
├── pyproject.toml          # 專案配置
├── .env.example           # 環境變數範例
└── README.md              # 專案說明
```

### 關鍵檔案

| 檔案 | 說明 |
|------|------|
| `pulse/cli/app.py` | TUI 應用程式主檔 |
| `pulse/core/config.py` | 配置管理 |
| `pulse/core/models.py` | Pydantic 資料模型 |
| `pulse/ai/client.py` | AI 客戶端 |
| `pyproject.toml` | 專案元數據與工具配置 |

---

## 取得協助

- **GitHub Issues**: https://github.com/alingowangxr/TW-Pulse-CLI/issues
- **文件**: 參見 `docs/` 目錄
- **架構說明**: 參見 `docs/architecture.md`

---

*最後更新：2026-02-07*
