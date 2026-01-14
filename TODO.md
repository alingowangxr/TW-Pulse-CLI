# Pulse-CLI 台灣股票分析工具

> **最後更新**: 2026-01-14
> **整體進度**: 核心功能 100% 完成

---

## 專案概述

**Pulse-CLI** 是一個 AI 驅動的台灣股票市場分析終端工具 (TUI)，提供技術分析、基本面分析、法人動向、SAPTA 預測引擎等功能。

### 技術架構
```
pulse/
├── ai/            # LiteLLM 多 Provider AI 客戶端
├── cli/           # Textual TUI 介面
├── core/
│   ├── analysis/  # 技術分析、基本面、法人動向
│   ├── data/      # FinMind + Yahoo Finance 數據層
│   ├── sapta/     # SAPTA 預測引擎 (6個模組 + ML)
│   └── screener/  # 股票篩選器
└── utils/         # 格式化輸出工具
```

### 數據來源
| 來源 | 用途 | 備註 |
|------|------|------|
| **FinMind** | 法人動向、融資融券 | 主要來源，有 API 配額限制 |
| **Yahoo Finance** | 股價、技術指標 | 備援來源，無限制 |

### AI 支援 (LiteLLM)
| Provider | 模型 | 備註 |
|----------|------|------|
| **Groq** | llama-3.3-70b-versatile | 預設，免費額度高 |
| **Google** | gemini-2.0-flash | 需 GEMINI_API_KEY |
| **Anthropic** | claude-sonnet-4 | 需 ANTHROPIC_API_KEY |
| **OpenAI** | gpt-4o | 需 OPENAI_API_KEY |

---

## 可用命令

| 命令 | 別名 | 說明 |
|------|------|------|
| `/help` | h, ? | 查看可用命令 |
| `/analyze` | a, stock | 完整股票分析 |
| `/technical` | tech, ta | 技術分析 (RSI, MACD, BB) |
| `/fundamental` | fund, fa | 基本面分析 (PE, ROE, 殖利率) |
| `/institutional` | inst, flow | 法人動向 (需 FinMind API) |
| `/sapta` | premarkup | SAPTA 綜合預測分析 |
| `/screen` | scan | 股票篩選 (超買/超賣/突破) |
| `/chart` | k, kline | K線圖 (輸出 PNG) |
| `/forecast` | pred | 價格預測 |
| `/compare` | cmp, vs | 多檔股票比較 |
| `/plan` | trade | 交易計劃生成 |
| `/clear` | cls | 清除聊天 |
| `/exit` | quit, q | 退出程式 |

---

## 2026-01-14 更新記錄

### AI 架構重構
- [x] 移除 CLIProxyAPI 依賴
- [x] 改用 LiteLLM 直連多家 LLM API
- [x] 預設模型改為 Groq (免費額度高)
- [x] 更新 .env.example 和 config/pulse.yaml

### 之前修復項目
- [x] 命令註冊修復 (11個命令)
- [x] SAPTA BollingerBands ta 庫參數修復
- [x] CLI 輸出繁體中文化
- [x] Windows emoji 相容性 (fallback 機制)
- [x] 循環導入警告修復

---

## 待改善項目

### 高優先級

#### 測試覆蓋率 (目前 < 5%)
- [ ] SmartAgent 單元測試
- [ ] SAPTA 引擎測試 (6 個模組)
- [ ] 交易計劃生成器測試
- [ ] 技術分析器測試
- [ ] 股票篩選器測試
- [ ] AI 客戶端測試
- [ ] 命令處理器整合測試

#### 錯誤處理強化
- [ ] CLI app.py 異常處理完善 (目前有空 except pass)
- [ ] API 超時重試機制
- [ ] FinMind 配額限制優雅降級
- [ ] 用戶友好錯誤訊息

### 中優先級

#### 代碼重構
- [ ] registry.py 拆分 (目前 842 行過長)
- [ ] 命令處理器按功能分離
- [ ] 統一異步/同步調用模式

#### 文檔完善
- [ ] SAPTA 算法詳細文檔
- [ ] 模型訓練指南
- [ ] 架構設計文檔
- [ ] API 文檔 (docstring 完善)

#### 性能優化
- [ ] 大規模篩選並發處理
- [ ] 數據緩存優化
- [ ] 進度條顯示

### 低優先級 (未來版本)

#### v0.2.0 功能
- [ ] 自選股追蹤 (Watchlist)
- [ ] 投資組合管理 (Portfolio)
- [ ] 價格警報通知 (Alerts)

#### v0.3.0 功能
- [ ] 回測框架 (Backtesting)
- [ ] 策略建構器 (Strategy Builder)

#### v0.4.0+ 功能
- [ ] 實時 WebSocket 支援
- [ ] 多市場支援 (美股、加密貨幣)

---

## 已知限制

1. **FinMind API 配額**: 免費版有請求上限，法人動向功能可能受限
2. **AI 服務依賴**: 需設定 LLM API key (GROQ_API_KEY 等)
3. **Prophet 可選**: 價格預測功能依賴 Prophet，未安裝時使用簡易備用方案

---

## 快速開始

```bash
# 安裝
pip install -e ".[dev]"

# 設定 API Key (選一個)
export GROQ_API_KEY="your-key"      # Groq (免費)
export GEMINI_API_KEY="your-key"    # Google
export ANTHROPIC_API_KEY="your-key" # Anthropic

# 運行
python -m pulse.cli.app

# 常用命令
/help              # 查看說明
/analyze 2330      # 台積電完整分析
/technical 2330    # 技術分析
/sapta 2330        # SAPTA 預漲分析
/screen oversold   # 篩選超賣股
/exit              # 退出
```

---

## 代碼品質評估

| 指標 | 評分 | 備註 |
|------|------|------|
| 功能完整性 | 8/10 | 核心功能完成 |
| 代碼結構 | 7.5/10 | 模塊化設計，部分過大 |
| 文檔質量 | 7/10 | 用戶文檔好，技術文檔不足 |
| 測試覆蓋 | 2/10 | **嚴重不足** |
| 錯誤處理 | 7/10 | 基本完整 |

**總體評分: 6.9/10**

---

**Pulse-CLI 台灣股票市場分析工具**
