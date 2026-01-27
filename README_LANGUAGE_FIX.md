# ✅ Gemini 語言一致性問題已修復

## 問題

使用 Gemini 執行 `/analyze` 指令時，回覆語言不一致（有時中文、有時英文）。

## 修復內容

已更新 `pulse/ai/prompts.py`，強制 AI 使用繁體中文回覆：

✅ **System Prompt** - 添加 `MUST USE Traditional Chinese` 強制指示
✅ **分析 Prompts** - 每個類型結尾加入 `CRITICAL` 語言提醒
✅ **User Messages** - 全部改為繁體中文
✅ **驗證通過** - 7/7 檢查全部通過

## 🚀 立即應用

### 步驟 1: 重新啟動 Pulse CLI

```bash
# 如果 Pulse 正在運行，按 Ctrl+C 停止

# 重新啟動
pulse
```

### 步驟 2: 測試

```
# 在 Pulse CLI 中
/model
# 選擇 "Gemini 2.5 Flash (Google)"

/analyze 2330
/analyze 2317
```

## 預期結果

現在 Gemini 應該：
- ✅ 100% 使用繁體中文回覆
- ✅ 不再隨機切換語言
- ✅ 提供一致的分析體驗

## 驗證修改

```bash
# 確認所有修改已正確應用
python scripts/verify_prompt_changes.py

# 測試語言一致性（可選）
python scripts/test_gemini_language.py
```

## 📚 相關文檔

- **詳細說明：** `docs/GEMINI_LANGUAGE_FIX.md`
- **快速摘要：** `LANGUAGE_FIX_SUMMARY.md`

---

**修復日期：** 2026-01-27
**立即生效：** 重啟 Pulse CLI 後立即生效
**不需要：** 重新安裝套件或清除緩存
