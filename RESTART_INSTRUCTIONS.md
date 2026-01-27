# 🔄 重新啟動 Pulse CLI 以載入新的 Gemini 模型

## ✅ 已完成的更新

以下文件已更新為最新的 Gemini 模型：
- ✅ `pulse/core/config.py` - Python 配置
- ✅ `config/pulse.yaml` - YAML 配置（這是問題所在！）
- ✅ `.env` - 環境變數範本
- ✅ Python 緩存已清除

## 🔍 驗證結果

運行驗證腳本確認配置正確：
```bash
$ python scripts/verify_models.py

Gemini models found:
----------------------------------------------------------------------
[OK]  gemini/gemini-2.5-flash       -> Gemini 2.5 Flash (Google)
[OK]  gemini/gemini-2.5-pro         -> Gemini 2.5 Pro (Google)
[OK]  gemini/gemini-3-flash-preview -> Gemini 3 Flash Preview (Google)

[SUCCESS] Configuration updated correctly!
```

## 🚀 重新啟動步驟

### 1. 停止當前的 Pulse CLI

如果 Pulse CLI 正在運行，請按 `Ctrl+C` 退出。

### 2. 重新啟動 Pulse CLI

```bash
cd C:\Users\mike\tw-pulse-cli
pulse
```

### 3. 驗證新的模型列表

在 Pulse CLI 中：
```
/model
```

或使用快捷鍵 `M`

**你應該看到：**
- ❌ ~~Gemini 2.0 Flash~~ (已移除)
- ✅ Gemini 2.5 Flash (Google)
- ✅ Gemini 2.5 Pro (Google)
- ✅ Gemini 3 Flash Preview (Google)

## 🎯 現在可用的 Gemini 模型

| 模型 | 說明 | 推薦用途 |
|------|------|----------|
| Gemini 2.5 Flash | 快速、平衡 | 日常股票分析 ⭐ |
| Gemini 2.5 Pro | 進階推理 | 複雜分析任務 |
| Gemini 3 Flash Preview | 最新預覽 | 測試新功能 |

## 🔧 如果仍然看到舊模型

### 方法 1: 完全重新安裝

```bash
# 卸載
pip uninstall pulse-cli -y

# 重新安裝
pip install -e .

# 啟動
pulse
```

### 方法 2: 手動清除所有緩存

```bash
# 清除 Python 緩存
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# 清除 pip 緩存
pip cache purge

# 重新啟動
pulse
```

### 方法 3: 驗證配置文件

確認 `config/pulse.yaml` 中沒有舊的 Gemini 2.0 模型：
```bash
cat config/pulse.yaml | grep -i gemini
```

應該只看到 2.5 和 3.0 的模型。

## 📋 問題檢查清單

- [ ] 已停止舊的 Pulse CLI 進程
- [ ] Python 緩存已清除
- [ ] 已確認 `config/pulse.yaml` 已更新
- [ ] 已重新啟動 Pulse CLI
- [ ] 使用 `/model` 或 `M` 指令檢查模型列表

## ✨ 測試新模型

重啟後，測試新的 Gemini 2.5：

```bash
# 在 Pulse CLI 中
/model
# 選擇 "Gemini 2.5 Flash (Google)"

/analyze 2330
# 應該使用 Gemini 2.5 進行分析
```

## 📞 仍有問題？

如果重啟後仍然看到舊模型，請提供：

1. 運行此命令的輸出：
   ```bash
   python scripts/verify_models.py
   ```

2. 檢查 YAML 配置：
   ```bash
   cat config/pulse.yaml | grep -A 15 "available_models"
   ```

3. Pulse CLI 的啟動日誌

---

**更新時間：** 2026-01-27
**問題原因：** `config/pulse.yaml` 中保留了舊的 Gemini 2.0 模型定義
**解決方案：** 已更新 YAML 配置並清除緩存
