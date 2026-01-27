# UI Mockups：模型過濾功能方案對比

## 現況（Before）

### 當前行為
```
┌──────────────────────────────────────────────┐
│              Select Model                     │
├──────────────────────────────────────────────┤
│  > DeepSeek Chat (DeepSeek)                  │
│    Claude Sonnet 4 (Anthropic)               │
│    Claude Haiku 4 (Anthropic)                │
│    GPT-4o (OpenAI)                           │
│    GPT-4o Mini (OpenAI)                      │
│    Gemini 2.5 Flash (Google)                 │
│    Gemini 2.5 Pro (Google)                   │
│    Gemini 3 Flash Preview (Google)           │
│    Llama 3.3 70B (Groq)                      │
│    Llama 3.1 8B (Groq)                       │
│                                               │
│    Enter: Select | Esc: Cancel                │
└──────────────────────────────────────────────┘

用戶情境：
- 只設置了 DEEPSEEK_API_KEY
- 看到 10 個選項（全部顯示）
- 選擇 Claude Sonnet 4
- ❌ 分析失敗："API key not valid"
- 困惑：「我明明設置了 key 啊？」
```

---

## 方案 A：簡單過濾（推薦）

### UI 呈現
```
┌──────────────────────────────────────────────┐
│              Select Model                     │
├──────────────────────────────────────────────┤
│  > DeepSeek Chat (DeepSeek)                  │
│                                               │
│                                               │
│                                               │
│  💡 Want more models?                        │
│     Configure API keys in .env file          │
│                                               │
│  Enter: Select | Esc: Cancel                  │
└──────────────────────────────────────────────┘

情境 1：只有一個 API Key
✅ 用戶只看到 1 個選項
✅ 明確知道哪個可用
✅ 看到提示：可以配置更多

情境 2：有 3 個 API Keys (DeepSeek, Gemini, Groq)
┌──────────────────────────────────────────────┐
│              Select Model                     │
├──────────────────────────────────────────────┤
│  > DeepSeek Chat (DeepSeek)                  │
│    Gemini 2.5 Flash (Google)                 │
│    Gemini 2.5 Pro (Google)                   │
│    Gemini 3 Flash Preview (Google)           │
│    Llama 3.3 70B (Groq)                      │
│    Llama 3.1 8B (Groq)                       │
│                                               │
│  💡 Want more models? Configure in .env      │
│  Enter: Select | Esc: Cancel                  │
└──────────────────────────────────────────────┘
✅ 顯示 6 個可用模型
✅ 所有選項都可以使用
✅ 底部仍有提示

情境 3：沒有任何 API Key
┌──────────────────────────────────────────────┐
│              Select Model                     │
├──────────────────────────────────────────────┤
│                                               │
│    ⚠️  No API keys configured                │
│                                               │
│    Please set at least one API key           │
│    in your .env file                          │
│                                               │
│    Run: python scripts/check_api_keys.py     │
│                                               │
│    Esc: Cancel                                │
└──────────────────────────────────────────────┘
✅ 清楚說明問題
✅ 提供解決方案
✅ 給出具體指令
```

### 優點 ✅
- 介面最簡潔
- 不會選擇到無效模型
- 適合新手

### 缺點 ❌
- 看不到其他可用模型
- 功能可見性較低

---

## 方案 B：分組顯示

### UI 呈現
```
┌──────────────────────────────────────────────┐
│              Select Model                     │
├──────────────────────────────────────────────┤
│  ✓ Available Models (3)                      │
│  > DeepSeek Chat (DeepSeek)                  │
│    Gemini 2.5 Flash (Google)                 │
│    Llama 3.3 70B (Groq)                      │
│                                               │
│  ⚠ Requires API Key (7)                      │
│    Claude Sonnet 4 (needs config)            │
│    Claude Haiku 4 (needs config)             │
│    GPT-4o (needs config)                     │
│    GPT-4o Mini (needs config)                │
│    Gemini 2.5 Pro (needs config)             │
│    Gemini 3 Flash Preview (needs config)     │
│    Llama 3.1 8B (needs config)               │
│                                               │
│  💡 Configure more in .env file              │
│  Enter: Select | Esc: Cancel                  │
└──────────────────────────────────────────────┘

互動行為：
- ✅ 「Available」區域的模型可以選擇
- ❌ 「Requires API Key」區域的選項禁用（灰色）
- 💡 滑鼠懸停時顯示配置提示
```

### 優點 ✅
- 功能可見性最高
- 用戶知道「還有什麼可用」
- 提供配置動機

### 缺點 ❌
- 列表較長（需滾動）
- UI 較複雜
- 禁用選項可能引起困惑

---

## 方案 C：智能提示

### UI 呈現（第一階段）
```
┌──────────────────────────────────────────────┐
│              Select Model                     │
├──────────────────────────────────────────────┤
│  > DeepSeek Chat (DeepSeek)         ✓       │
│    Claude Sonnet 4 (Anthropic)      ⚠       │
│    Claude Haiku 4 (Anthropic)       ⚠       │
│    GPT-4o (OpenAI)                  ⚠       │
│    GPT-4o Mini (OpenAI)             ⚠       │
│    Gemini 2.5 Flash (Google)        ✓       │
│    Gemini 2.5 Pro (Google)          ✓       │
│    Gemini 3 Flash Preview (Google)  ✓       │
│    Llama 3.3 70B (Groq)             ✓       │
│    Llama 3.1 8B (Groq)              ✓       │
│                                               │
│  ✓ Configured  ⚠ Needs API Key               │
│  Enter: Select | Esc: Cancel                  │
└──────────────────────────────────────────────┘

✓ = 已配置 API Key
⚠ = 需要配置
```

### UI 呈現（第二階段：選擇未配置的模型）
```
用戶選擇 "Claude Sonnet 4 (Anthropic) ⚠"
↓
彈出配置指南

┌──────────────────────────────────────────────┐
│  ⚠️  API Key Not Configured                  │
├──────────────────────────────────────────────┤
│                                               │
│  Model: Claude Sonnet 4 (Anthropic)          │
│                                               │
│  This model requires:                         │
│  • ANTHROPIC_API_KEY                         │
│                                               │
│  How to configure:                            │
│  1. Get API key at:                          │
│     https://console.anthropic.com/           │
│                                               │
│  2. Add to .env file:                        │
│     ANTHROPIC_API_KEY=sk-ant-xxx...          │
│                                               │
│  3. Restart Pulse CLI                        │
│                                               │
│  [📋 Copy .env Path]  [Cancel]               │
│                                               │
└──────────────────────────────────────────────┘

互動細節：
- 點擊「Copy .env Path」複製路徑到剪貼簿
- 關閉對話框後返回模型選擇
- 所有模型都可「選擇」，但未配置的會顯示指南
```

### 優點 ✅
- 最佳學習體驗
- 即時教育用戶
- 不隱藏任何功能
- 提供具體配置步驟

### 缺點 ❌
- 實現最複雜
- 需要維護配置數據
- 可能打斷工作流
- 對老手可能顯得囉嗦

---

## 視覺對比表

| 特性 | 現況 | 方案 A | 方案 B | 方案 C |
|------|------|--------|--------|--------|
| **列表長度** | 10 項 | 1-6 項 | 10 項（分組） | 10 項（標記） |
| **錯誤防護** | ❌ 無 | ✅ 完全 | ⚠️ 部分 | ⚠️ 提示 |
| **功能可見性** | ✅ 100% | ⚠️ 30% | ✅ 100% | ✅ 100% |
| **配置指引** | ❌ 無 | ⚠️ 簡單 | ⚠️ 簡單 | ✅ 詳細 |
| **UI 複雜度** | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **新手友好** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 互動流程對比

### 現況：選擇錯誤模型
```
1. 用戶打開 /model
2. 看到 10 個選項
3. 選擇 Claude Sonnet 4 ✓
4. 執行 /analyze 2330
5. ❌ 錯誤："API key not valid"
6. 困惑：為什麼不能用？
7. 查看文檔/尋求支持
```
**步驟數：** 7 步
**成功率：** ❌ 失敗

### 方案 A：只顯示可用
```
1. 用戶打開 /model
2. 只看到 1 個選項：DeepSeek
3. 選擇 DeepSeek ✓
4. 執行 /analyze 2330
5. ✅ 成功分析
```
**步驟數：** 5 步
**成功率：** ✅ 100%

### 方案 B：分組顯示
```
1. 用戶打開 /model
2. 看到可用區域（1 個）+ 需配置區域（9 個）
3. 嘗試選擇 Claude（禁用）
4. 意識到需要配置
5. 選擇 DeepSeek ✓
6. 執行 /analyze 2330
7. ✅ 成功分析
```
**步驟數：** 7 步（含探索）
**成功率：** ✅ 90%

### 方案 C：智能提示
```
1. 用戶打開 /model
2. 看到 10 個選項（帶狀態標記）
3. 選擇 Claude Sonnet 4 ⚠
4. 彈出配置指南
5. 閱讀指南，決定稍後配置
6. 選擇 DeepSeek ✓
7. 執行 /analyze 2330
8. ✅ 成功分析
```
**步驟數：** 8 步（含學習）
**成功率：** ✅ 85%
**附加價值：** 用戶學會如何配置新模型

---

## 推薦選擇

### 立即實施：方案 A ⭐⭐⭐⭐⭐

**原因：**
1. 最簡單（4-6 小時）
2. 最有效（100% 成功率）
3. 最適合當前用戶群

### 未來升級：方案 C ⭐⭐⭐⭐

**時機：**
- 產品成熟後
- 用戶群擴大時
- 有時間打磨細節時

### 不推薦：方案 B ⭐⭐

**原因：**
- 複雜度增加但價值有限
- 列表太長反而降低 UX
- 方案 A 或 C 都優於此方案

---

## 實施路線圖

```
Version 1.0 (Current)
└─> 顯示所有 10 個模型

Version 1.1 (建議)
└─> 實施方案 A：簡單過濾
    ├─ 只顯示已配置的模型
    ├─ 空列表時顯示提示
    └─ 底部添加配置建議

Version 1.2 (可選)
└─> 增強功能
    ├─ /models-all 指令
    ├─ /check-keys 指令
    └─ 更詳細的配置指南

Version 2.0 (未來)
└─> 升級到方案 C：智能提示
    ├─ 狀態指示器
    ├─ 配置嚮導對話框
    └─ 一鍵配置功能
```

---

**UI 設計日期：** 2026-01-27
**推薦方案：** 方案 A（漸進增強至方案 C）
