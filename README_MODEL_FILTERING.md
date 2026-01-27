# 🎯 新功能：智能模型過濾

## 功能說明

現在當你使用 `/model` 或 `M` 指令時，**只會顯示已配置 API Key 的模型**。

---

## ✨ 改善效果

### Before（之前）
```
打開 /model
├─> 看到 10 個模型選項
├─> 選了沒配置的模型（如 Claude）
├─> 分析失敗："API key not valid"
└─> ❌ 困惑
```

### After（現在）
```
打開 /model
├─> 只看到已配置的模型（例如 3 個）
├─> 全部都可以使用
├─> 選擇後成功分析
└─> ✅ 順暢
```

---

## 🎯 實際效果

### 情況 1：你有 3 個 API Keys

```
打開 /model 會看到：

┌──────────────────────────────────────┐
│         Select Model                  │
├──────────────────────────────────────┤
│  > DeepSeek Chat (DeepSeek)          │
│    Gemini 2.5 Flash (Google)         │
│    Gemini 2.5 Pro (Google)           │
│    Gemini 3 Flash Preview (Google)   │
│    Llama 3.3 70B (Groq)              │
│    Llama 3.1 8B (Groq)               │
│                                       │
│  💡 Want more models?                │
│     Configure API keys in .env       │
└──────────────────────────────────────┘

✅ 顯示 6 個可用模型
✅ 提示如何配置更多
✅ 不會看到無法使用的模型
```

### 情況 2：你還沒配置任何 API Key

```
打開 /model 會看到：

┌──────────────────────────────────────┐
│         Select Model                  │
├──────────────────────────────────────┤
│                                       │
│  ⚠️  No API keys configured           │
│                                       │
│  Please set at least one API key     │
│  in .env file:                       │
│    • DEEPSEEK_API_KEY (recommended)  │
│    • GEMINI_API_KEY                  │
│    • GROQ_API_KEY (free tier)        │
│                                       │
│  Run: python scripts/check_api_keys.py│
│                                       │
└──────────────────────────────────────┘

✅ 清楚說明問題
✅ 列出可配置的選項
✅ 提供檢查工具
```

---

## 🚀 立即使用

### 1. 重新啟動 Pulse CLI

```bash
# 按 Ctrl+C 停止當前的 Pulse

# 重新啟動
pulse
```

### 2. 測試新功能

```
# 在 Pulse CLI 中
/model  # 或按 M 鍵

# 你現在只會看到已配置的模型！
```

### 3. 檢查配置（可選）

```bash
# 查看哪些 API keys 已配置
python scripts/check_api_keys.py

# 驗證過濾功能
python scripts/verify_model_filtering.py
```

---

## 💡 常見問題

### Q: 我想看所有可用的模型怎麼辦？

**A:** 目前只能通過配置文件查看。Phase 2 會添加 `/models-all` 指令。

暫時可以：
```bash
# 查看所有定義的模型
python -c "from pulse.core.config import settings; print([m['name'] for m in settings.list_models(filter_by_api_key=False)])"
```

### Q: 為什麼我的模型不見了？

**A:** 可能是對應的 API key 未配置或失效。

檢查方法：
```bash
python scripts/check_api_keys.py
```

### Q: 如何添加更多模型？

**A:** 在 `.env` 文件中配置對應的 API key：

```bash
# 例如要使用 Claude
ANTHROPIC_API_KEY=sk-ant-xxx...

# 例如要使用 GPT
OPENAI_API_KEY=sk-xxx...
```

然後重啟 Pulse CLI。

### Q: 這個功能可以關閉嗎？

**A:** 目前不能通過界面關閉，但代碼中有預留接口。如果確實需要顯示全部模型，可以在代碼中修改：

```python
# pulse/core/config.py, line ~211
def list_models(self, filter_by_api_key: bool = True):  # 改為 False
```

---

## 📊 好處

| 指標 | 效果 |
|------|------|
| **防止錯誤** | 100% 避免 API key 錯誤 |
| **減少困惑** | 只看到能用的選項 |
| **配置反饋** | 立即知道哪些已配置 |
| **新手友好** | 清晰的指引和提示 |

---

## 📚 相關文檔

- **完整評估：** `docs/FEATURE_ANALYSIS_FILTER_MODELS_BY_API_KEY.md`
- **UI 設計：** `docs/FEATURE_UI_MOCKUPS.md`
- **實施總結：** `IMPLEMENTATION_SUMMARY_MODEL_FILTERING.md`

---

**生效日期：** 2026-01-27
**使用方式：** 重啟 Pulse CLI 即可
**影響範圍：** `/model` (或 `M`) 指令
