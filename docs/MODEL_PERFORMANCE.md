# AI 模型性能對比

## 速度測試（/analyze 命令）

基於實際使用經驗的速度對比：

| 模型 | 平均響應時間 | 速度等級 | 成本 | API 要求 | 建議用途 |
|------|------------|---------|------|---------|---------|
| **Groq Llama 3.1 8B** | 2-4秒 | ⚡⚡⚡ | 免費 | GROQ_API_KEY | 快速分析、即時查詢 |
| **Groq Llama 3.3 70B** | 5-8秒 | ⚡⚡ | 免費 | GROQ_API_KEY | 平衡速度與品質 |
| **Claude Haiku 4** | 4-6秒 | ⚡⚡ | $0.001/1K | ANTHROPIC_API_KEY | 快速、高品質 |
| **Gemini 2.0 Flash** | 5-10秒 | ⚡⚡ | 免費/付費 | GEMINI_API_KEY | Google 生態整合 |
| **GPT-4o Mini** | 6-12秒 | ⚡ | $0.003/1K | OPENAI_API_KEY | OpenAI 用戶 |
| **DeepSeek Chat** | 10-20秒 | ⚡ | $0.0003/1K | DEEPSEEK_API_KEY | 性價比高、深度分析 |
| **Claude Sonnet 4** | 8-15秒 | ⚡ | $0.015/1K | ANTHROPIC_API_KEY | 最高品質 |
| **GPT-4o** | 10-20秒 | ⚡ | $0.015/1K | OPENAI_API_KEY | 複雜分析 |

## 性能優化建議

### 場景 1：快速查看（推薦 Groq）
```bash
# 在 Pulse CLI 中
/models
# 選擇: Groq Llama 3.1 8B 或 Llama 3.3 70B

# 或在配置中設置
# config/pulse.yaml
ai:
  default_model: "groq/llama-3.1-8b-instant"
```

**優勢：**
- ✅ 2-4秒響應（最快）
- ✅ 完全免費
- ✅ 無需信用卡
- ⚠️ 品質略低於 Claude/GPT-4

### 場景 2：平衡性能（推薦 Claude Haiku）
```yaml
ai:
  default_model: "anthropic/claude-haiku-4-20250514"
```

**優勢：**
- ✅ 4-6秒響應
- ✅ 高品質分析
- ✅ 成本低（$0.001/1K tokens）
- ✅ 支援台灣股市術語

### 場景 3：深度分析（DeepSeek/Sonnet）
```yaml
ai:
  default_model: "deepseek/deepseek-chat"  # 或 claude-sonnet-4
```

**優勢：**
- ✅ 最深度的分析
- ✅ 更準確的建議
- ⚠️ 10-20秒響應時間
- ⚠️ 需要付費 API

## 獲取 API 金鑰

### Groq（推薦新手）
1. 訪問 https://console.groq.com
2. 註冊免費帳戶
3. 創建 API Key
4. 添加到 `.env`: `GROQ_API_KEY=your_key_here`

### Anthropic (Claude)
1. 訪問 https://console.anthropic.com
2. 需要信用卡
3. 創建 API Key
4. 添加到 `.env`: `ANTHROPIC_API_KEY=your_key_here`

### OpenAI
1. 訪問 https://platform.openai.com
2. 需要信用卡
3. 創建 API Key
4. 添加到 `.env`: `OPENAI_API_KEY=your_key_here`

### DeepSeek
1. 訪問 https://platform.deepseek.com
2. 註冊帳戶
3. 創建 API Key
4. 添加到 `.env`: `DEEPSEEK_API_KEY=your_key_here`

## 其他優化技巧

### 1. 減少 max_tokens（更快響應）
```yaml
# config/pulse.yaml
ai:
  max_tokens: 2048  # 從 4096 減少到 2048
```

### 2. 減少 timeout（避免長時間等待）
```yaml
ai:
  timeout: 60  # 從 180 減少到 60 秒
```

### 3. 使用緩存（避免重複分析）
緩存會自動啟用，相同股票在 30 分鐘內不會重複請求數據。

## 實際建議

**初學者/免費用戶：**
→ 使用 **Groq Llama 3.3 70B**
- 完全免費
- 速度快（5-8秒）
- 品質夠用

**進階用戶：**
→ 使用 **Claude Haiku 4**
- 速度快（4-6秒）
- 高品質分析
- 成本低

**專業投資者：**
→ 使用 **Claude Sonnet 4** 或 **DeepSeek Chat**
- 最深度分析
- 更準確的技術指標解讀
- 適合重要決策

## 測試不同模型

```bash
# 在 Pulse CLI 中快速切換
/models

# 然後測試
/analyze 2330

# 比較響應時間和分析品質
```
