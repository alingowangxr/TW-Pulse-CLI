# Gemini 語言一致性修復

## 🐛 問題描述

使用 Gemini 模型執行股票分析（`/analyze` 指令）時，AI 回覆的語言不一致：
- 有時使用繁體中文
- 有時使用英文
- 有時混合使用

## 🔍 問題原因

在 `pulse/ai/prompts.py` 中，system prompt 給予 AI 選擇語言的自由度：

**問題代碼：**
```python
Language: Traditional Chinese / English  # 允許兩種語言
Use clear, professional language (English or Traditional Chinese)  # 沒有強制要求
```

這導致 Gemini 根據數據語言、上下文或隨機因素選擇回覆語言，造成不一致。

## ✅ 解決方案

### 1. 強化 System Prompt 語言指示

**修改位置：** `pulse/ai/prompts.py`

#### CHAT_SYSTEM_PROMPT
```python
# 修改前
Language: Traditional Chinese / English

# 修改後
Language: **MUST USE Traditional Chinese (繁體中文) for ALL responses**

# 新增規則
- **ALWAYS respond in Traditional Chinese (繁體中文)**
```

#### StockAnalysisPrompts.get_system_base()
```python
# 新增在開頭
IMPORTANT: **You MUST respond in Traditional Chinese (繁體中文) ONLY.
Do NOT use English for the main analysis.**

# 修改特徵描述
# 修改前
- Use clear, professional language (English or Traditional Chinese)

# 修改後
- Use clear, professional Traditional Chinese language
```

### 2. 在每個分析類型結尾加入語言提醒

為所有分析類型（comprehensive, technical, fundamental, broker flow, screening）添加：

```python
**CRITICAL: Your entire response MUST be in Traditional Chinese (繁體中文).
Do NOT use English.**
```

### 3. 修改 User Message 為中文

**format_analysis_request():**
```python
# 修改前
return f"""Analyze stock {ticker} based on the following data:
...
Provide comprehensive and actionable analysis.
"""

# 修改後
return f"""請用繁體中文分析股票 {ticker}，基於以下數據：
...
請提供全面且可執行的分析。

**重要：整個分析報告必須使用繁體中文撰寫。**
"""
```

同樣修改了：
- `format_comparison_request()` - 股票比較
- `format_sector_request()` - 產業分析

## 📋 修改的文件

1. **`pulse/ai/prompts.py`**
   - 更新 `CHAT_SYSTEM_PROMPT`
   - 更新 `StockAnalysisPrompts.get_system_base()`
   - 在所有分析 prompt 結尾添加語言指示
   - 將所有 format 方法改為中文

## 🧪 測試方法

### 方法 1: 使用測試腳本

```bash
cd C:\Users\mike\tw-pulse-cli
python scripts/test_gemini_language.py
```

這個腳本會：
- 執行 3 次分析測試
- 計算中文字元比例
- 檢查語言一致性

**期望輸出：**
```
測試 #1: ✓ 中文 (中文比例: 85.2%)
測試 #2: ✓ 中文 (中文比例: 87.4%)
測試 #3: ✓ 中文 (中文比例: 86.1%)

成功率: 3/3
[成功] 所有測試都使用繁體中文回覆！
```

### 方法 2: 在 Pulse CLI 中測試

```bash
pulse

# 切換到 Gemini 模型
/model
# 選擇 "Gemini 2.5 Flash (Google)"

# 執行多次分析
/analyze 2330
/analyze 2317
/analyze 2454
```

檢查所有回覆是否都使用繁體中文。

## 📊 修改前後對比

### 修改前
- ❌ 語言提示模糊：`English or Traditional Chinese`
- ❌ 沒有在 user message 中指定語言
- ❌ 沒有在 prompt 結尾強調語言
- ❌ 導致：回覆語言隨機變化

### 修改後
- ✅ 明確要求：`MUST USE Traditional Chinese`
- ✅ System prompt 多處強調繁體中文
- ✅ User message 使用中文並強調語言要求
- ✅ 每個分析類型結尾都有 `CRITICAL` 語言提醒
- ✅ 預期結果：所有回覆都使用繁體中文

## 🎯 為什麼這樣修改有效？

### 1. 多層次語言指示
```
System Prompt (全局)
    ↓
Analysis Type Prompt (分析類型)
    ↓
User Message (實際請求)
    ↓
Critical Reminder (結尾強調)
```

每一層都強調使用繁體中文，確保 AI 無法忽略。

### 2. 使用強烈的語氣詞

- `MUST` (必須)
- `CRITICAL` (關鍵)
- `ONLY` (唯一)
- `Do NOT` (不要)

這些詞彙讓 AI 明確知道這是強制要求，不是建議。

### 3. 中文 User Message

當 user message 本身就是中文時，AI 更傾向於用中文回覆（context priming）。

### 4. 針對 Gemini 的特性

Gemini 模型對語言指示較敏感，需要在多處明確重複才能確保一致性。

## 🔄 應用修改

### 不需要重新安裝

這只是 prompt 修改，不需要重新安裝套件。

### 需要重新啟動 Pulse CLI

```bash
# 如果 Pulse 正在運行，按 Ctrl+C 停止

# 重新啟動
pulse
```

### 清除 Python 緩存（可選）

```bash
cd C:\Users\mike\tw-pulse-cli
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

## 📝 其他注意事項

### 英文專有名詞仍然保留

修改後，AI 仍然會使用英文專有名詞和縮寫，例如：
- RSI (相對強弱指標)
- MACD (指數平滑異同移動平均線)
- P/E Ratio (本益比)

這是正常且合適的。重點是**分析內容和解釋必須使用繁體中文**。

### JSON 輸出

對於 `get_recommendation_prompt()` (JSON 格式輸出)，已特別指定：
```python
**CRITICAL: The "summary", "key_reasons", and "risks" fields
MUST be in Traditional Chinese (繁體中文).**
```

### 如果仍然出現英文

如果修改後仍然偶爾出現英文回覆，可能原因：
1. API 配額限制導致使用舊版本模型
2. Gemini 模型本身的不穩定性
3. 網路問題導致 prompt 截斷

**解決方法：**
- 等待片刻後重試
- 切換到其他模型（DeepSeek、Groq）
- 檢查 API 配額狀態

## 🎉 預期效果

修改後，使用 Gemini 進行股票分析時：
- ✅ 99%+ 的回覆使用繁體中文
- ✅ 語言一致性大幅提升
- ✅ 更符合台灣股市分析場景
- ✅ 使用者體驗更佳

---

**修改日期：** 2026-01-27
**影響範圍：** 所有使用 Gemini 模型的股票分析指令
**測試狀態：** 待用戶測試確認
