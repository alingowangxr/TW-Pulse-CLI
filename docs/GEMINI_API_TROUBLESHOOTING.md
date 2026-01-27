# Gemini API 故障排除指南

## 重要更新：Gemini 模型版本變更

**注意：** Gemini 2.0 已於 2026 年 3 月 31 日停止服務。

**目前可用的模型（通過測試）：**
- **Gemini 2.5 系列**（穩定版）：
  - `gemini/gemini-2.5-flash` ✅ - 快速、平衡的多模態理解

- **Gemini 3 系列**（預覽版）：
  - `gemini/gemini-3-flash-preview` ✅ - 最新預覽版，複雜多模態理解

**注意：** Gemini 3 目前仍在預覽階段，完整版本尚未正式推出。

## 問題診斷結果

根據診斷，你的 Gemini API 整合存在以下問題：

### 1. API 配額超限（主要問題）

**錯誤訊息：**
```
You exceeded your current quota, please check your plan and billing details
```

**原因：**
- 你的 Gemini API key 已經超過使用配額限制
- Google Gemini 免費版有嚴格的速率限制：
  - 每分鐘 15 次請求
  - 每天 1,500 次請求

### 2. 環境變數載入問題（已修復）

**問題：** 在某些情況下，環境變數沒有在正確的時機被載入。

**修復：** 已在以下文件中添加環境變數載入機制：
- `pulse/cli/app.py` - 應用啟動時載入環境變數
- `pulse/ai/client.py` - 添加 API key 檢查和友好的錯誤訊息

## 解決方案

### 選項 1：等待配額重置（最簡單）

Google Gemini API 的配額會自動重置：
- **每分鐘配額：** 每分鐘重置一次
- **每日配額：** 每天 UTC 時間 00:00 重置

**操作步驟：**
1. 等待幾分鐘
2. 重新嘗試分析指令

### 選項 2：申請新的 API Key

訪問 [Google AI Studio](https://aistudio.google.com/apikey) 申請新的 API key。

**步驟：**
1. 訪問 https://aistudio.google.com/apikey
2. 點擊 "Create API Key"
3. 複製新的 API key
4. 更新 `.env` 文件中的 `GEMINI_API_KEY`

### 選項 3：啟用計費以獲得更高配額

如果你需要更高的配額，可以啟用 Google Cloud 計費。

**步驟：**
1. 訪問 [Google Cloud Console](https://console.cloud.google.com/)
2. 創建或選擇一個項目
3. 啟用 "Generative Language API"
4. 設置計費帳號
5. 付費版本的配額限制：
   - 每分鐘 1,000 次請求
   - 每分鐘 400 萬 tokens

**價格：**
- Gemini 2.5 Flash:
  - 輸入: $0.075 / 百萬 tokens
  - 輸出: $0.30 / 百萬 tokens
- Gemini 3 Flash:
  - 輸入: $0.10 / 百萬 tokens
  - 輸出: $0.40 / 百萬 tokens

### 選項 4：使用其他 AI 模型（推薦）

Pulse CLI 支援多個 AI 提供商。你可以切換到其他已配置的模型：

**可用的模型：**

1. **DeepSeek** (已配置，免費且效能優異)
   ```bash
   # 在 Pulse CLI 中切換模型
   /model
   # 選擇: DeepSeek Chat (DeepSeek)
   ```

2. **Groq Llama** (已配置，免費且速度超快)
   ```bash
   /model
   # 選擇: Llama 3.3 70B (Groq)
   ```

## 使用診斷工具

我創建了一個診斷工具來檢查你的 API 配置：

```bash
python scripts/check_api_keys.py
```

這個工具會顯示：
- 所有已配置的 API keys
- 可用的模型
- 當前的默認模型
- 配置建議

## 測試 Gemini API

配額重置後，你可以使用以下命令測試 Gemini API：

```bash
cd "C:\Users\mike\tw-pulse-cli"
python scripts/test_gemini_api.py
```

## 改進的錯誤處理

現在當 API 請求失敗時，你會看到更友好的錯誤訊息：

**配額超限時：**
```
API 配額超限。請檢查您的 API 使用額度或稍後再試。
模型: Gemini 2.0 Flash (Google)
詳細錯誤: [原始錯誤訊息]
```

**API key 無效時：**
```
API 金鑰無效或未設定。
模型: Gemini 2.0 Flash (Google)
請確認 .env 文件中已正確設定對應的 API 金鑰。
詳細錯誤: [原始錯誤訊息]
```

## 推薦的使用方式

1. **日常分析：** 使用 DeepSeek 或 Groq（免費且高效）
   ```bash
   # 設定為默認模型
   # 編輯 .env 文件：
   PULSE_AI__DEFAULT_MODEL=deepseek/deepseek-chat
   # 或
   PULSE_AI__DEFAULT_MODEL=groq/llama-3.3-70b-versatile
   ```

2. **需要 Gemini 時：** 臨時切換模型
   ```bash
   /model  # 在 CLI 中切換到 Gemini
   ```

3. **監控配額：** 定期檢查 [Google AI Studio](https://aistudio.google.com/apikey) 的使用情況

## 相關連結

- [Google AI Studio](https://aistudio.google.com/apikey) - 管理 API keys
- [Google Cloud Console](https://console.cloud.google.com/) - 設置計費
- [Gemini API 價格](https://ai.google.dev/pricing) - 查看價格詳情
- [Gemini API 配額限制](https://ai.google.dev/gemini-api/docs/quota) - 查看配額詳情

## 問題報告

如果問題持續存在，請提供以下資訊：

1. 運行診斷工具的輸出：
   ```bash
   python scripts/check_api_keys.py
   ```

2. 錯誤訊息的完整內容

3. 使用的模型名稱（例如：gemini/gemini-2.0-flash）

4. 發生錯誤的時間和頻率
