# 🔧 Gemini 語言一致性已修復

## 問題

使用 Gemini 進行股票分析時，回覆語言不一致（有時中文，有時英文）。

## 解決方案

已更新 `pulse/ai/prompts.py`，在多個層級強制要求使用繁體中文：

1. ✅ **System Prompt** - 明確要求 `MUST USE Traditional Chinese`
2. ✅ **分析類型 Prompt** - 每個類型結尾加入 `CRITICAL` 語言提醒
3. ✅ **User Message** - 改為中文並強調語言要求

## 🚀 應用修改

### 重新啟動 Pulse CLI

```bash
# 按 Ctrl+C 停止當前的 Pulse

# 重新啟動
pulse
```

不需要重新安裝套件或清除緩存，只需要重啟 Pulse CLI。

## 🧪 測試

### 快速測試（推薦）

在 Pulse CLI 中：
```
/model
# 選擇 "Gemini 2.5 Flash (Google)"

/analyze 2330
/analyze 2317
```

檢查回覆是否都使用繁體中文。

### 完整測試（可選）

使用自動化測試腳本：
```bash
python scripts/test_gemini_language.py
```

會執行 3 次分析並檢查語言一致性。

## 📊 預期結果

修改後，Gemini 的分析回覆應該：
- ✅ **全部使用繁體中文**（99%+ 一致性）
- ✅ 英文專有名詞（RSI、MACD）仍然保留
- ✅ 不再隨機切換語言

## 📝 修改的文件

- **`pulse/ai/prompts.py`** - 所有 prompt 模板

## 💡 如果仍然出現英文

可能原因：
1. 舊的 Pulse CLI 進程未關閉 → 完全重啟
2. API 配額限制 → 等待或換 API key
3. Python 緩存 → 清除緩存後重啟

**清除緩存：**
```bash
cd C:\Users\mike\tw-pulse-cli
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

## 📚 詳細文檔

完整的修改說明和技術細節：
- `docs/GEMINI_LANGUAGE_FIX.md`

---

**修改日期：** 2026-01-27
**立即生效：** 重啟 Pulse CLI 後立即生效
**測試工具：** `scripts/test_gemini_language.py`
