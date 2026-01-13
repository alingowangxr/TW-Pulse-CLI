# Pulse-CLI 改寫進度與待辦事項

> **最後更新**: 2026-01-13 23:30
> **整體進度**: 100% 完成 🎉

---

## 已完成部分 ✅

### 1. 數據層重構
- [x] `finmind_data.py` - FinMind 數據獲取完整實現 (850+ 行)
  - 股價數據 (`fetch_stock`, `fetch_history`, `fetch_multiple`)
  - 基本面數據 (`fetch_fundamentals`)
  - 法人動向 (`fetch_institutional_investors`)
  - 融資融券 (`fetch_margin_trading`)
  - 外資持股 (`fetch_foreign_shareholding`)
  - **新增**: 財務報表 (`fetch_financial_statements`)
  - **新增**: 股利資料 (`fetch_dividend_info`)
  - **新增**: 公司基本資料 (`fetch_company_info`)
  - **新增**: TPEX 股票清單 (`fetch_tpex_stocks`)
- [x] `stock_data_provider.py` - 統一數據層 (FinMind 優先 + yfinance 回退)
- [x] `yfinance.py` - 更新為台灣市場 (.TW 後綴, TAIEX/TPEX 指數)

### 2. 核心模組台灣化
- [x] `pulse/__init__.py` - 更新項目描述為 Taiwan Stock Market
- [x] `pulse/utils/constants.py` - 完全重寫為台灣股票常量
  - **新增**: TWSE_SECTORS (上市產業分類)
  - **新增**: TPEX_SECTORS (櫃買產業分類，包含生技、電子、營建等)
  - **新增**: TW50_TICKERS (台灣50成分股)
  - **新增**: MIDCAP100_TICKERS (中型100成分股)
  - **新增**: TPEX_POPULAR (熱門上櫃股票)
  - **新增**: BROKER_CODES (台灣券商代碼)
  - **新增**: MARKET_INDICES (TAIEX/TPEX 指數)
  - **新增**: INSTITUTIONAL_INVESTORS (三大法人類型)
  - TRADING_HOURS (台灣交易時間)
  - PRICE_FRACTIONS (台灣價格檔位)
  - LOT_SIZE = 1000 (1張=1000股)
- [x] `pulse/utils/validators.py` - 台灣股票驗證 (4-6位數字)
- [x] `pulse/utils/formatters.py` - 台幣格式 (NT$, 億, 兆, 張)
- [x] `pulse/core/config.py` - 更新為 .TW 後綴和 tw_tickers.json
- [x] `pulse/ai/prompts.py` - 更新為台灣市場專用提示詞
- [x] `pyproject.toml` - 更新項目描述和關鍵詞

### 3. 分析模組
- [x] `institutional_flow.py` - 機構投資者流向分析 (173 行)
- [x] `technical.py` - 技術分析 (ta 庫 API 相容性修復)
- [x] `fundamental.py` - 基本面分析
- [x] `sector.py` - 產業分析 (支援 TWSE + TPEX)

### 4. CLI 命令台灣化
- [x] `pulse/cli/commands/registry.py` - 完成台灣化 (~50處)
  - 將 IHSG/LQ45/IDX30 改為 TAIEX/TW50
  - 將印尼股票範例改為台灣股票
  - 更新幫助文本為中英雙語
  - 更新 StockUniverse 映射 (TW50, MIDCAP, POPULAR, ALL)
  - 移除 `/auth` 和 `/bandar` 命令 (印尼 Stockbit 平台)
- [x] 可用命令:
  - `/analyze`, `/technical`, `/fundamental`, `/institutional`
  - `/chart`, `/forecast`, `/compare`, `/plan`
  - `/taiex`, `/sector`, `/screen`
  - `/sapta`, `/models`, `/clear`, `/help`

### 5. Smart Agent 台灣化
- [x] `pulse/core/smart_agent.py` - 完成台灣化 (~100處)
  - 移除印尼股票列表
  - 添加台灣股票列表 (2330, 2454, 2317, 2881, 2882 等)
  - 更新意向模式為繁體中文+英文
  - 更新所有提示詞為繁體中文
  - 更新貨幣從 Rp 改為 NT$

### 6. 其他核心文件
- [x] `pulse/ai/client.py` - AI Client 繁體中文支援
- [x] `pulse/core/agent.py` - 更新為台灣股票列表 + InstitutionalFlowAnalyzer
- [x] `pulse/core/trading_plan.py` - 確認 LOT_SIZE=1000 (已正確)
- [x] `pulse/core/analysis/sector.py` - 使用 TWSE_SECTORS + TPEX_SECTORS
- [x] `pulse/core/screener.py` - 更新 StockUniverse 枚舉 (TW50, MIDCAP, POPULAR, ALL)
- [x] `pulse/core/sapta/engine.py` - 簡化為 6 模組 (移除 broker_flow)

### 7. 依賴修復
- [x] `pyproject.toml` - 修復 ta 庫版本衝突 (ta>=0.5.25,<0.12.0)
- [x] 修復 ta 庫 API 相容性 (n vs window 參數名稱)

### 8. 代碼清理 (印尼 Stockbit 平台移除) ✅
- [x] 移除 `pulse/core/data/stockbit.py` (印尼券商數據平台)
- [x] 移除 `/auth` 命令 (Stockbit 認證)
- [x] 移除 `/bandar` 命令 (Bandarmology 分析)
- [x] 移除 `pulse/core/analysis/bandarmology/` (依賴 Stockbit)
- [x] 移除 `pulse/core/analysis/broker_flow.py` (兼容性層)
- [x] 移除 `pulse/core/sapta/modules/broker_flow.py`
- [x] 更新 `pulse/core/config.py` - 移除 StockbitSettings
- [x] 更新 `pulse/core/data/__init__.py` - 移除 StockbitClient 匯出

### 9. 驗證測試
- [x] `pip install -e ".[dev]"` - 依賴安裝成功
- [x] Python 語法檢查 - 所有修改文件編譯通過
- [x] TUI 啟動測試 - Textual 介面正常啟動
- [x] 單元測試 - test_yfinance.py 全部通過 (6/6 tests passed)
- [x] 命令測試:
  - `/help` ✅
  - `/technical 2330` ✅
  - `/fundamental 2330` ✅
  - `/institutional 2330` ✅
  - `/taiex` ✅
  - `/taiex TPEX` ✅
  - `/sector` ✅
  - `/screen oversold` ✅
  - `/sapta 2330` ✅
  - `/chart 2330` ✅
  - `/plan 2330` ✅
  - `/compare 2330 2454` ✅

### 10. 文檔更新
- [x] `README.md` - 完成台灣化更新
  - 移除所有印尼語內容
  - 更新示例為台灣股票
  - 更新自然語言示例為繁體中文
- [x] `CHANGELOG.md` - 更新版本歷史
- [x] `USAGE.md` - **新增** 完整使用說明手冊
  - 安裝指南
  - 命令參考
  - 使用範例
  - 配置說明
  - 程式架構
  - 常見問題
- [x] `TODO.md` - 更新進度至 100%

---

## 待完成部分 ⏳ (完成)

### 1. 功能性測試 ✅ 已完成
- [x] 調試斜杠命令解析問題 (`/technical 2330` 無法識別) - 已修復
- [x] 測試 `/fundamental 2330` 命令
- [x] 測試 `/institutional 2330` 命令
- [x] 測試 `/chart 2330 6mo` 命令
- [x] 測試 `/sapta 2330` 命令

### 2. 代碼清理 ✅ 已完成
- [x] 移除 `pulse/core/data/stockbit.py` (印尼平台)
- [x] 移除 `/auth` 和 `/bandar` 命令
- [x] 移除 `pulse/core/analysis/broker_flow.py` (兼容性層)
- [x] 移除 `pulse/core/analysis/bandarmology/` (依賴 Stockbit)
- [x] 移除 SAPTA broker_flow 模組
- [x] 更新 `pulse/core/config.py` - 移除 StockbitSettings
- [x] 更新 `pulse/core/agent.py` - 使用 InstitutionalFlowAnalyzer

### 11. 新增 FinMind 數據源 ✅
- [x] `fetch_financial_statements()` - 財報數據 (損益表、資產負債表、現金流量表)
- [x] `fetch_dividend_info()` - 股利歷史資料 (可回溯 5 年)
- [x] `fetch_company_info()` - 公司基本資料 (成立日期、資本額、網站等)
- [x] `fetch_tpex_stocks()` - TPEX/OTC 股票清單

### 12. TPEX/OTC 櫃買市場支援 ✅
- [x] 指數支援:
  - TAIEX (加權指數)
  - TPEX/OTC (櫃買指數)
- [x] 產業分類:
  - TWSE_SECTORS (上市產業)
  - TPEX_SECTORS (櫃買產業: 生技、電子、營建等)
- [x] 熱門股票清單: TPEX_POPULAR

---

## 待完成部分

### 未來規劃 (可選)
- [ ] 添加實時數據支持 (WebSocket 或輪詢)
- [ ] 添加自選股和投資組合追蹤功能
- [ ] 添加價格警報通知
- [ ] 添加更多 FinMind 數據源 (例如：庫藏股、增減資資料)
- [ ] 支持基本面選股條件

---

## 修改摘要

### 關鍵替換
```python
# 已完成替換:
"IHSG" → "TAIEX"
"LQ45" → "TW50"
"IDX30" → "TW50"
"idx80" → "midcap"
"BBCA" → "2330"
"BBRI" → "2881"
"Rp" → "NT$"
"^JKSE" → "^TWII"
```

### 新增文件
| 文件 | 說明 |
|------|------|
| `pulse/core/data/finmind_data.py` | FinMind API 數據獲取 (850+ 行) |
| `pulse/core/data/stock_data_provider.py` | 統一數據介面 |
| `pulse/core/analysis/institutional_flow.py` | 法人流向分析 |
| `data/tw_tickers.json` | 台灣股票清單 |
| `USAGE.md` | 完整使用說明手冊 |

### 修改文件狀態
| 文件 | 狀態 |
|------|------|
| `pulse/cli/commands/registry.py` | ✅ 已台灣化 |
| `pulse/core/smart_agent.py` | ✅ 已台灣化 |
| `pulse/core/agent.py` | ✅ 已台灣化 |
| `pulse/core/config.py` | ✅ 已更新 |
| `pulse/core/analysis/sector.py` | ✅ 已更新 |
| `pulse/core/analysis/technical.py` | ✅ 已修復 ta API |
| `pulse/core/screener.py` | ✅ 已更新 |
| `pulse/core/sapta/engine.py` | ✅ 已簡化 |
| `pulse/utils/constants.py` | ✅ 完全重寫 |
| `pyproject.toml` | ✅ 已修復依賴 |
| `tests/test_yfinance.py` | ✅ 已台灣化 |
| `README.md` | ✅ 已更新 |
| `CHANGELOG.md` | ✅ 已更新 |
| `USAGE.md` | ✅ **新增** |

### 移除文件 (印尼 Stockbit 平台)
| 文件 | 說明 |
|------|------|
| `pulse/core/data/stockbit.py` | Stockbit API 客戶端 |
| `pulse/core/analysis/bandarmology/` | Bandarmology 模組 |
| `pulse/core/analysis/broker_flow.py` | 兼容性層 |
| `pulse/core/sapta/modules/broker_flow.py` | SAPTA 模組 |

---

## 技術規格

| 項目 | 規格 |
|------|------|
| **股票代碼格式** | 4-6位數字 (2330, 2454, 2317) |
| **Yahoo Finance 後綴** | .TW |
| **貨幣** | NT$ (台幣) |
| **語言** | 繁體中文 + 英文 |
| **主要數據源** | FinMind |
| **備用數據源** | Yahoo Finance |
| **交易單位** | 1張=1000股 |
| **ta 庫版本** | 0.5.25 (FinMind 兼容性) |

---

## 命令快速參考

```bash
# 安裝依賴
pip install -e ".[dev]"

# 運行 CLI
python -m pulse.cli.app

# 運行測試
python -m pytest tests/test_core/test_data/test_yfinance.py -v

# 代碼檢查
ruff check pulse/
mypy pulse/
```

---

## 下一步行動

### 已完成 ✅

#### 1. 遷移完成
- [x] 印尼 → 台灣股票市場遷移 100% 完成
- [x] 所有印尼股票代碼替換為台灣股票代碼
- [x] 所有印尼指數替換為台灣指數
- [x] 所有印尼盾 (Rp) 替換為台幣 (NT$)

#### 2. 代碼清理
- [x] 移除 Stockbit 印尼平台相關代碼
- [x] 移除 /auth 和 /bandar 命令
- [x] 簡化 SAPTA 引擎 (6 模組)

#### 3. 新功能開發
- [x] 新增 FinMind 數據源:
  - 財報數據 (income statement, balance sheet, cash flow)
  - 股利資料 (5 年歷史)
  - 公司基本資料
  - TPEX 股票清單
- [x] TPEX/OTC 櫃買市場支援
- [x] ta 庫 API 相容性修復

#### 4. 功能測試
- [x] `/technical 2330` ✅
- [x] `/fundamental 2330` ✅
- [x] `/institutional 2330` ✅
- [x] `/taiex` ✅
- [x] `/taiex TPEX` ✅
- [x] `/sector` ✅
- [x] `/sector SEMICONDUCTOR` ✅
- [x] `/screen oversold` ✅
- [x] `/screen bullish` ✅
- [x] `/sapta 2330` ✅
- [x] `/chart 2330` ✅
- [x] `/plan 2330` ✅
- [x] `/compare 2330 2454` ✅

#### 5. 文檔
- [x] 更新 README.md
- [x] 更新 CHANGELOG.md
- [x] 新增 USAGE.md 完整使用說明手冊

---

**Pulse-CLI 台灣股票市場分析工具 100% 完成！** 🎉

### 快速開始

```bash
# 安裝
pip install -e ".[dev]"

# 運行 CLI
python -m pulse.cli.app

# 查看說明
/help
```
