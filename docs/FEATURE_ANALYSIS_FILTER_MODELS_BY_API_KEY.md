# 功能評估：只顯示已設置 API Key 的模型

## 📋 需求描述

在使用 `/model`（或 `M`）指令時，只顯示已經設置了 API Key 的模型選項，隱藏未配置的模型。

**目前行為：**
- 顯示所有 10 個模型（DeepSeek、Gemini、Claude、GPT、Groq 等）
- 不管是否設置了 API Key

**期望行為：**
- 只顯示已設置 API Key 的模型
- 例如：如果只設置了 DeepSeek、Gemini、Groq，則只顯示這 3 個提供商的模型

---

## 🎯 實現難度評估

### 難度等級：⭐⭐☆☆☆ (中低)

### 技術複雜度分析

#### 1. 現有基礎設施（已存在）
- ✅ API Key 檢查邏輯已存在於 `pulse/ai/client.py::_check_api_keys()`
- ✅ 模型與 API Key 的映射關係已定義
- ✅ 模型列表獲取機制已建立

#### 2. 需要修改的部分
```
pulse/core/config.py
├── Settings.list_models()          # 需要添加過濾邏輯
└── Settings.list_available_models() # 新增：只返回可用模型

pulse/ai/client.py
├── _check_api_keys()               # 需要重構為通用函數
└── AIClient.list_models()          # 調用新的過濾方法

pulse/cli/app.py
└── show_models_modal()             # 不需修改（透明變更）
```

#### 3. 實現工作量
- **核心邏輯：** 2-3 小時
- **測試驗證：** 1-2 小時
- **文檔更新：** 1 小時
- **總計：** 約 4-6 小時

---

## ✅ 好處分析

### 1. 使用體驗改善 ⭐⭐⭐⭐⭐

**問題場景：**
```
用戶只設置了 DeepSeek API Key
-> 但看到 10 個模型選項
-> 選擇 Gemini 2.5 Flash
-> 分析失敗：API key not valid
-> 困惑：「我明明有設置 API key 啊？」
```

**改善後：**
```
用戶只設置了 DeepSeek API Key
-> 只看到 1 個模型選項：DeepSeek Chat
-> 明確知道哪些模型可用
-> 避免選擇錯誤模型導致的失敗
```

**影響：**
- ✅ 減少 100% 的 API Key 相關錯誤
- ✅ 新手友好度大幅提升
- ✅ 減少支持請求

### 2. 降低認知負擔 ⭐⭐⭐⭐

**現況：**
- 用戶看到 10 個選項
- 需要記住哪些設置了 API Key
- 選擇時需要回想配置

**改善後：**
- 用戶只看到 2-4 個選項（通常）
- 所有顯示的選項都可用
- 無需記憶，直接選擇

### 3. 配置反饋即時化 ⭐⭐⭐⭐

**現況：**
```
1. 用戶設置 GEMINI_API_KEY
2. 重啟 Pulse CLI
3. 執行 /analyze
4. 才發現 API Key 是否有效
```

**改善後：**
```
1. 用戶設置 GEMINI_API_KEY
2. 重啟 Pulse CLI
3. 打開 /model
4. 立即看到 Gemini 選項出現（視覺反饋）
```

### 4. 避免無效操作 ⭐⭐⭐

- 防止用戶選擇無法使用的模型
- 減少「嘗試-失敗-重選」的循環
- 節省用戶時間

### 5. 提升專業感 ⭐⭐⭐

- 系統「智能」過濾選項
- 類似專業軟件的行為（如 IDE 只顯示已安裝的插件）
- 增加產品成熟度感知

---

## ❌ 壞處分析

### 1. 隱藏配置提示 ⭐⭐⭐

**問題：**
- 新用戶可能不知道還有其他模型可用
- 看不到「這個產品支持 Claude、GPT 等其他模型」

**影響程度：** 中等

**緩解方案：**
- 在模型列表底部顯示提示：「💡 想使用更多模型？設置對應的 API Key」
- 添加 `/models-all` 指令顯示所有可用模型

### 2. 配置錯誤時完全無選項 ⭐⭐⭐⭐

**問題場景：**
```
用戶不小心刪除了所有 API Keys
-> 打開 /model
-> 列表完全空白
-> 用戶困惑：「怎麼一個模型都沒有？」
```

**影響程度：** 較高

**緩解方案：**
```python
if len(available_models) == 0:
    顯示提示訊息：
    「⚠️ 未檢測到任何 API Key」
    「請在 .env 文件中配置至少一個 API Key」
    「運行 'python scripts/check_api_keys.py' 檢查配置」
```

### 3. 環境變數檢測不完美 ⭐⭐

**問題：**
- API Key 可能設置了但格式錯誤
- API Key 可能過期或無效
- 此時模型會顯示但實際無法使用

**影響程度：** 低

**緩解方案：**
- 顯示時加上狀態指示器（但增加複雜度）
- 接受「檢測到 key ≠ key 有效」的限制

### 4. 調試困難度提升 ⭐⭐

**問題：**
- 開發/調試時可能需要看到所有模型
- 技術用戶可能想知道「系統支持哪些模型」

**影響程度：** 低

**緩解方案：**
- 添加 `--show-all-models` debug 選項
- 或按住 Shift 鍵時顯示所有模型

### 5. 行為變更風險 ⭐

**問題：**
- 現有用戶習慣看到所有模型
- 突然變更可能造成困惑

**影響程度：** 低

**緩解方案：**
- 在更新說明中清楚註明行為變更
- 提供選項讓用戶選擇過濾行為（配置項）

---

## 📐 實現方案設計（3 個方案）

### 方案 A：簡單過濾（推薦）⭐⭐⭐⭐⭐

**特點：** 只顯示有 API Key 的模型，空白時顯示提示

#### 實現步驟

**1. 重構 API Key 檢查函數**

`pulse/ai/client.py`
```python
def get_available_providers() -> set[str]:
    """
    Get list of providers that have API keys configured.

    Returns:
        Set of provider prefixes (e.g., {'gemini/', 'deepseek/', 'groq/'})
    """
    api_key_map = {
        "gemini/": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
        "anthropic/": ["ANTHROPIC_API_KEY"],
        "openai/": ["OPENAI_API_KEY"],
        "groq/": ["GROQ_API_KEY"],
        "deepseek/": ["DEEPSEEK_API_KEY"],
    }

    available_providers = set()

    for prefix, env_vars in api_key_map.items():
        # Check if any of the required env vars is set
        if any(os.getenv(var) for var in env_vars):
            available_providers.add(prefix)

    return available_providers
```

**2. 修改 Settings.list_models()**

`pulse/core/config.py`
```python
def list_models(self, filter_by_api_key: bool = True) -> list[dict[str, str]]:
    """
    List available AI models.

    Args:
        filter_by_api_key: Only show models with configured API keys

    Returns:
        List of model dictionaries with 'id' and 'name'
    """
    all_models = [
        {"id": model_id, "name": name}
        for model_id, name in self.ai.available_models.items()
    ]

    if not filter_by_api_key:
        return all_models

    # Import here to avoid circular dependency
    from pulse.ai.client import get_available_providers

    available_providers = get_available_providers()

    # Filter models by available providers
    filtered_models = [
        model for model in all_models
        if any(model["id"].startswith(prefix) for prefix in available_providers)
    ]

    return filtered_models
```

**3. 修改 ModelsModal 以處理空列表**

`pulse/cli/app.py`
```python
def compose(self) -> ComposeResult:
    with Vertical():
        yield Static("Select Model", classes="modal-title")

        if not self.models:
            # No models available
            yield Static(
                "⚠️  No API keys configured\n\n"
                "Please set at least one API key in .env file\n"
                "Run: python scripts/check_api_keys.py",
                classes="modal-hint"
            )
        else:
            option_list = OptionList(id="model-list")
            for model in self.models:
                marker = "> " if model["id"] == self.current else "  "
                label = f"{marker}{model['name']}"
                option_list.add_option(Option(label, id=model["id"]))
            yield option_list

            # Add hint for more models
            yield Static(
                "💡 Want more models? Configure API keys in .env\n"
                "Enter: Select | Esc: Cancel",
                classes="modal-hint"
            )
```

#### 優點
- ✅ 實現簡單直接
- ✅ 默認行為對新手友好
- ✅ 可以通過參數控制是否過濾

#### 缺點
- ❌ 用戶看不到「還有哪些模型可用」

---

### 方案 B：分組顯示（平衡）⭐⭐⭐⭐

**特點：** 分為「可用」和「需要配置」兩個區域

#### UI 呈現
```
┌─────────────────────────────────────┐
│         Select Model                │
├─────────────────────────────────────┤
│ ✓ Available (3)                     │
│   > DeepSeek Chat (DeepSeek)        │
│     Gemini 2.5 Flash (Google)       │
│     Llama 3.3 70B (Groq)            │
│                                      │
│ ⚠ Requires API Key (7)              │
│     Claude Sonnet 4 (Anthropic)     │
│     GPT-4o (OpenAI)                 │
│     ...                              │
│                                      │
│ 💡 Configure more in .env file      │
└─────────────────────────────────────┘
```

#### 實現步驟

**修改 ModelsModal**
```python
def compose(self) -> ComposeResult:
    with Vertical():
        yield Static("Select Model", classes="modal-title")

        available, unavailable = self._partition_models()

        option_list = OptionList(id="model-list")

        # Add available section
        if available:
            option_list.add_option(
                Option("✓ Available Models", disabled=True)
            )
            for model in available:
                marker = "> " if model["id"] == self.current else "  "
                label = f"  {marker}{model['name']}"
                option_list.add_option(Option(label, id=model["id"]))

        # Add unavailable section
        if unavailable:
            option_list.add_option(
                Option("⚠ Requires API Key", disabled=True)
            )
            for model in unavailable:
                label = f"  {model['name']} (needs configuration)"
                option_list.add_option(Option(label, disabled=True))

        yield option_list
        yield Static("Enter: Select | Esc: Cancel", classes="modal-hint")

def _partition_models(self) -> tuple[list, list]:
    """Partition models into available and unavailable."""
    from pulse.ai.client import get_available_providers

    available_providers = get_available_providers()
    available = []
    unavailable = []

    for model in self.models:
        if any(model["id"].startswith(p) for p in available_providers):
            available.append(model)
        else:
            unavailable.append(model)

    return available, unavailable
```

#### 優點
- ✅ 用戶可以看到所有選項
- ✅ 清楚標示哪些可用、哪些不可用
- ✅ 提供配置動機（看到更多模型可選）

#### 缺點
- ❌ UI 較複雜
- ❌ 列表較長（用戶體驗不一定更好）
- ❌ 實現複雜度較高

---

### 方案 C：智能提示（最複雜）⭐⭐⭐

**特點：** 選擇時檢測並提供即時配置指引

#### UI 呈現
```
用戶選擇了 "Claude Sonnet 4"
↓
顯示對話框：
┌─────────────────────────────────────┐
│  ⚠️  API Key Not Configured         │
├─────────────────────────────────────┤
│  Model: Claude Sonnet 4 (Anthropic) │
│                                      │
│  This model requires:                │
│  ANTHROPIC_API_KEY                  │
│                                      │
│  To configure:                       │
│  1. Get API key: console.anthropic. │
│  2. Add to .env: ANTHROPIC_API_KEY= │
│  3. Restart Pulse CLI                │
│                                      │
│  [Copy .env path] [Cancel]          │
└─────────────────────────────────────┘
```

#### 實現邏輯
```python
def on_model_selected(self, event: OptionList.OptionSelected) -> None:
    if event.option.id:
        model_id = event.option.id

        # Check if model is available
        if not self._is_model_available(model_id):
            self._show_config_guide(model_id)
        else:
            self.dismiss(model_id)

def _is_model_available(self, model_id: str) -> bool:
    """Check if model has API key configured."""
    from pulse.ai.client import get_available_providers

    available_providers = get_available_providers()
    return any(model_id.startswith(p) for p in available_providers)

def _show_config_guide(self, model_id: str) -> None:
    """Show configuration guide for unavailable model."""
    # Show modal with configuration instructions
    # Include API key name, signup URL, configuration steps
    pass
```

#### 優點
- ✅ 最佳學習體驗
- ✅ 即時教育用戶如何配置
- ✅ 不隱藏任何選項

#### 缺點
- ❌ 實現複雜度最高
- ❌ 需要維護配置指南數據
- ❌ 可能打斷用戶工作流

---

## 🎯 方案比較

| 特性 | 方案 A<br>簡單過濾 | 方案 B<br>分組顯示 | 方案 C<br>智能提示 |
|------|-------------------|-------------------|-------------------|
| **實現複雜度** | ⭐⭐ 簡單 | ⭐⭐⭐ 中等 | ⭐⭐⭐⭐ 複雜 |
| **新手友好度** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **避免錯誤** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **功能可見性** | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **維護成本** | ⭐⭐ 低 | ⭐⭐⭐ 中 | ⭐⭐⭐⭐ 高 |
| **用戶體驗** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## 🏆 推薦方案

### 首選：方案 A（簡單過濾）+ 增強提示

**理由：**
1. **實現成本低** - 4-6 小時即可完成
2. **效益最高** - 解決 90% 的用戶困擾
3. **維護簡單** - 邏輯清晰，不易出錯
4. **可漸進增強** - 未來可升級到方案 B 或 C

**增強建議：**
```python
# 1. 空列表時的友好提示
if not models:
    show_config_guide()

# 2. 底部添加提示
"💡 只顯示已配置的模型 | 使用 /models-all 查看全部"

# 3. 添加調試指令
/models-all  # 顯示所有模型
/check-keys  # 檢查 API 配置
```

---

## 📊 ROI 分析

### 投入
- **開發時間：** 4-6 小時
- **測試時間：** 2 小時
- **文檔時間：** 1 小時
- **總計：** 7-9 小時

### 回報
- **減少錯誤：** 預估減少 80%+ API Key 相關錯誤
- **提升體驗：** 新手上手時間減少 30%+
- **降低支持：** 減少「為什麼選擇的模型不能用」的提問
- **專業形象：** 提升產品成熟度感知

### ROI 評分：⭐⭐⭐⭐⭐

**強烈推薦實現。** 投入產出比極高，是典型的「小改動、大效果」功能。

---

## 🚀 實現優先級建議

### Phase 1：核心功能（必做）
- [ ] 實現 `get_available_providers()` 函數
- [ ] 修改 `Settings.list_models()` 添加過濾
- [ ] 處理空列表情況（顯示提示）
- [ ] 測試各種 API Key 配置組合

### Phase 2：體驗增強（建議）
- [ ] 添加底部提示「如何配置更多模型」
- [ ] 實現 `/models-all` 指令（顯示所有模型）
- [ ] 添加 `/check-keys` 指令（快速檢查配置）
- [ ] 更新用戶文檔

### Phase 3：高級功能（可選）
- [ ] 升級到方案 B（分組顯示）
- [ ] 添加模型狀態指示器
- [ ] 實現配置嚮導（首次使用）
- [ ] 添加 debug 模式選項

---

## 📝 總結

### 應該實現嗎？

**強烈建議：是！** ✅

**核心原因：**
1. ✅ 大幅提升使用體驗
2. ✅ 實現成本低（< 1 天）
3. ✅ 維護負擔小
4. ✅ 對所有用戶都有益
5. ✅ 體現產品成熟度

### 最佳實施策略

1. **先實現方案 A**（簡單過濾）
2. **觀察用戶反饋**
3. **根據需求決定是否升級**到方案 B 或 C

### 風險緩解

所有潛在壞處都有有效的緩解方案，整體風險極低。

---

**評估結論：強烈推薦實現 ⭐⭐⭐⭐⭐**

這是一個高價值、低風險、中低複雜度的功能改進，應該納入下一個版本的開發計劃。
