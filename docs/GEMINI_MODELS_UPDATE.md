# Gemini 模型更新說明 (2026)

## 📋 摘要

Gemini API 模型已全面更新，**Gemini 2.0 已停止服務**（2026-03-31）。現在支援 Gemini 2.5 和 Gemini 3 預覽版。

## ✅ 已完成的更新

### 1. 配置文件更新

**文件：** `pulse/core/config.py`

更新了可用模型列表：
```python
# Google Gemini (2.5 stable, 3.0 preview)
"gemini/gemini-2.5-flash": "Gemini 2.5 Flash (Google)",
"gemini/gemini-3-flash-preview": "Gemini 3 Flash Preview (Google)",
```

### 2. 環境變數範本

**文件：** `.env`

更新了模型選項註釋：
```bash
# Options:
#   - gemini/gemini-2.5-flash (Google Gemini 2.5 - Fast & Balanced)
#   - gemini/gemini-3-flash-preview (Google Gemini 3 - Preview Version)
```

### 3. 診斷和測試工具

- **`scripts/check_api_keys.py`** - 已更新模型列表
- **`scripts/test_gemini_api.py`** - 已更新測試模型
- **`docs/GEMINI_API_TROUBLESHOOTING.md`** - 已更新文檔

## 🎯 可用的 Gemini 模型

### Gemini 2.5 系列（穩定版）✅

| 模型 ID | 說明 | 狀態 | 測試結果 |
|---------|------|------|----------|
| `gemini/gemini-2.5-flash` | 快速、平衡的多模態理解 | 穩定 | ✅ 成功 |

**特點：**
- 1M token context window
- 多模態支援（文字、圖片、音訊、影片）
- 工具使用和 Google Search 整合
- 適應性思考能力

### Gemini 3 系列（預覽版）✅

| 模型 ID | 說明 | 狀態 | 測試結果 |
|---------|------|------|----------|
| `gemini/gemini-3-flash-preview` | 最新快速模型 | 預覽 | ✅ 成功 |

**特點：**
- 推理優先設計
- 複雜代理工作流程優化
- 最先進的推理能力
- 強大的編碼能力

### 已棄用的模型 ❌

| 模型 ID | 狀態 | 停止服務日期 |
|---------|------|--------------|
| `gemini/gemini-2.0-flash` | ❌ 已棄用 | 2026-03-31 |
| `gemini/gemini-2.0-flash-exp` | ❌ 已棄用 | 2026-03-31 |

## 🧪 測試結果

```bash
$ python scripts/test_gemini_api.py

Testing: gemini/gemini-2.5-flash
  [SUCCESS] Model is working correctly!

Testing: gemini/gemini-3-flash-preview
  [SUCCESS] Model is working correctly!
```

## 💰 定價資訊

### Gemini 2.5 Flash
- **輸入：** $0.075 / 百萬 tokens
- **輸出：** $0.30 / 百萬 tokens

### Gemini 3 Flash (預覽)
- **輸入：** $0.10 / 百萬 tokens
- **輸出：** $0.40 / 百萬 tokens

### 免費配額
- **每分鐘：** 15 次請求
- **每天：** 1,500 次請求
- **上下文緩存：** 每日 100 萬 tokens 免費

## 📖 使用方式

### 在 Pulse CLI 中使用

1. **啟動 Pulse CLI：**
   ```bash
   pulse
   ```

2. **切換到 Gemini 模型：**
   ```
   /model
   # 選擇: Gemini 2.5 Flash (Google)
   ```

3. **執行分析：**
   ```
   /analyze 2330
   ```

### 設定為默認模型

編輯 `.env` 文件：
```bash
PULSE_AI__DEFAULT_MODEL=gemini/gemini-2.5-flash
```

## 🔧 故障排除

### API 配額超限

**問題：** `You exceeded your current quota`

**解決方案：**
1. 等待配額重置（每分鐘或每日）
2. 申請新的 API key
3. 啟用計費以獲得更高配額
4. 使用替代模型（DeepSeek、Groq）

### 模型不存在（404）

**問題：** `Model not found`

**確認使用正確的模型 ID：**
- ✅ `gemini/gemini-2.5-flash`
- ✅ `gemini/gemini-3-flash-preview`
- ❌ `gemini/gemini-2.0-flash` (已棄用)
- ❌ `gemini/gemini-3-flash` (尚未推出)
- ❌ `gemini/gemini-3-pro` (尚未推出)

## 📚 相關資源

- [Gemini API 模型文檔](https://ai.google.dev/gemini-api/docs/models) - 官方模型列表
- [Google AI Studio](https://aistudio.google.com/apikey) - 管理 API keys
- [LiteLLM Gemini 提供商](https://docs.litellm.ai/docs/providers/gemini) - LiteLLM 整合文檔
- [Gemini API 價格](https://ai.google.dev/pricing) - 價格詳情
- [Gemini API 配額](https://ai.google.dev/gemini-api/docs/rate-limits) - 配額限制

## 🔄 遷移指南

如果你的代碼中使用了舊的 Gemini 2.0 模型：

### Before (已棄用)
```python
model = "gemini/gemini-2.0-flash"
```

### After (推薦)
```python
# 選項 1: 穩定版 Gemini 2.5
model = "gemini/gemini-2.5-flash"

# 選項 2: 最新預覽版 Gemini 3
model = "gemini/gemini-3-flash-preview"
```

## ✨ 推薦配置

### 一般使用（平衡效能與成本）
```bash
PULSE_AI__DEFAULT_MODEL=gemini/gemini-2.5-flash
```

### 嘗試最新功能
```bash
PULSE_AI__DEFAULT_MODEL=gemini/gemini-3-flash-preview
```

### 成本優化（免費且高效）
```bash
PULSE_AI__DEFAULT_MODEL=deepseek/deepseek-v4-flash
# 或
PULSE_AI__DEFAULT_MODEL=groq/llama-3.3-70b-versatile
```

## 🎉 更新完成

所有配置已更新為最新的 Gemini 模型。你的 Pulse CLI 現在支援：
- ✅ Gemini 2.5 Flash（穩定版）
- ✅ Gemini 3 Flash Preview（預覽版）

執行診斷確認：
```bash
python scripts/check_api_keys.py
python scripts/test_gemini_api.py
```
