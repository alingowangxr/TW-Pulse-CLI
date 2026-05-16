# TW-Pulse-CLI 使用說明

> 台灣股票市場分析 CLI 工具 - 安裝與使用指南

---

## 目錄

1. [安裝](#安裝)
2. [設定](#設定)
3. [啟動](#啟動)
4. [命令](#命令)
5. [範例](#範例)
6. [常見問題](#常見問題)

---

## 安裝

### 環境需求

- Python 3.11+
- Git

### 安裝步驟

```bash
# 1. 複製專案
git clone https://github.com/alingowangxr/TW-Pulse-CLI.git
cd TW-Pulse-CLI

# 2. 建立虛擬環境
python -m venv .venv

# 3. 啟動虛擬環境
.venv\Scripts\activate     # Windows
source .venv/bin/activate  # Linux/macOS

# 4. 安裝
pip install -e .
```

### 使用 uv (更快速)

```bash
pip install uv
uv pip install -e .
```

---

## 設定

### 環境變數

複製範例檔案：
```bash
cp .env.example .env
```

編輯 `.env` 填入 API Key：

```env
# AI API Key (選擇一個或多個)
DEEPSEEK_API_KEY=your_key          # 預設，詳細分析（deepseek-v4-flash）
# GROQ_API_KEY=your_key            # 免費，快速
# GEMINI_API_KEY=your_key
# ANTHROPIC_API_KEY=your_key
# OPENAI_API_KEY=your_key

# FinMind API (法人動向)
FINMIND_TOKEN=your_token

# 預設模型
PULSE_AI__DEFAULT_MODEL=deepseek/deepseek-v4-flash
```

### 取得 API Key

| Provider | 網址 | 特性 |
|----------|------|------|
| DeepSeek | https://platform.deepseek.com/api-keys | 預設，詳細分析（deepseek-v4-flash） |
| Groq | https://console.groq.com/keys | 免費額度，快速 |
| Google | https://aistudio.google.com/apikey | 免費額度有限 |
| Anthropic | https://console.anthropic.com/ | 付費，高品質 |
| OpenAI | https://platform.openai.com/api-keys | 付費 |
| FinMind | https://finmindtrade.com/ | 法人動向數據 |

---

## 啟動

```bash
# 進入虛擬環境後
pulse
```

或直接執行：
```bash
python -m pulse.cli.app
```

### 快捷鍵

| 快捷鍵 | 功能 |
|--------|------|
| `Enter` | 送出訊息 |
| `Ctrl+C` | 退出程式 |
| `Ctrl+L` | 清除對話 |
| `Escape` | 關閉命令面板 |
| `Tab` | 導航命令選擇 |
| `↑` `↓` | 上下選擇 |

---

## 命令

### 分析命令

| 命令 | 別名 | 說明 | 用法 |
|------|------|------|------|
| `/analyze` | `/a`, `/stock` | 完整分析 | `/analyze 2330` |
| `/technical` | `/ta`, `/tech` | 技術分析 | `/technical 2330` |
| `/fundamental` | `/fa`, `/fund` | 基本面分析 | `/fundamental 2330` |
| `/institutional` | `/inst`, `/flow` | 法人動向 | `/institutional 2330` |
| `/chart` | `/c` | 產生圖表 | `/chart 2330 3mo` |
| `/forecast` | `/pred`, `/predict` | 價格預測 | `/forecast 2330 14 [fast\|full]` |
| `/compare` | `/cmp`, `/vs` | 比較股票 | `/compare 2330 2454` |
| `/plan` | `/tp` | 交易計畫 | `/plan 2330` |
| `/sapta` | `/premarkup` | 預漲偵測 | `/sapta 2330` |
| `/index` | `/market` | 大盤指數 | `/index` |
| `/sector` | `/sec` | 產業分析 | `/sector` |
| `/keltner` | `/kc` | 肯特納通道策略 | `/keltner 2330` |
| `/happy-lines` | `/happy`, `/五線譜`, `/hl` | 樂活五線譜分析 | `/happy-lines 2330` |

### 篩選命令

| 命令 | 別名 | 說明 | 用法 |
|------|------|------|------|
| `/screen` | `/s`, `/filter` | 股票篩選 | `/screen oversold` |
| `/smart-money` | `/tvb`, `/主力` | 主力足跡選股 | `/smart-money --tw50` |
| `/stocks` | - | 更新股票清單檔案 | `/stocks --sync` |
| `/warehouse` | `/db`, `/datahub` | 本地台股倉庫狀態/同步 | `/warehouse sync --mode=copy` |

#### `/stocks`

`/stocks` 用來更新股票清單檔案，適合排程執行。

```bash
/stocks --sync
```

會更新：
- `data/tw_codes_tw50.json`
- `data/tw_codes_listed.json`
- `data/tw_codes_otc.json`
- `data/tw_tickers.json`
- `data/stock_list.json`

可搭配 Windows Task Scheduler 或 cron 定時跑 `python scripts/fetch_stock_list.py --sync`。

#### `/warehouse`

如果你要使用本地股票資料，請先執行 `/warehouse` 或 `/warehouse sync` 來建立 `data/local_warehouse/tw_stock_warehouse.db`。
這個檔案不會隨著 GitHub repository 一起提供，因為它是本機環境專用的資料庫檔。

#### 基本面數據批量更新

為了加速 AI 推論並解決即時 API 缺資料的問題，建議同步個股基本面數據到本地 SQLite 資料庫：

```bash
python scripts/update_fundamentals.py
```

此腳本會遍歷所有已知的股票代碼，透過 `yfinance` 抓取最新的估值指標與財務數據（如 PE, PB, ROE, ROA 等）並存入 `stock_fundamentals` 表格。建議每週執行一次。

### 系統命令

| 命令 | 別名 | 說明 |
|------|------|------|
| `/models` | `/model`, `/m` | 切換 AI 模型 |
| `/clear` | `/cls` | 清除對話 |
| `/help` | `/h`, `/?` | 說明 |
| `/exit` | `/quit`, `/q` | 退出 |

### 篩選條件

| 條件 | 說明 |
|------|------|
| `oversold` | RSI < 30 |
| `overbought` | RSI > 70 |
| `bullish` | MACD 多頭 + 站上 SMA20 |
| `bearish` | MACD 空頭 |
| `breakout` | 突破壓力位 + 量增 |
| `momentum` | RSI 50-70 + MACD 多頭 |
| `undervalued` | PE < 15 + ROE > 10% |
| `keltner_breakout` | 肯特納通道突破 |
| `keltner_hold` | 肯特納通道持有 |
| `happy_oversold` | 樂活五線譜超跌區 (第1線) |
| `happy_overbought` | 樂活五線譜過熱區 (第5線) |
| `happy_cheap` | 樂活五線譜偏低區以下 (第1-2線) |
| `happy_expensive` | 樂活五線譜偏高區以上 (第4-5線) |
| `rsi<30` | 自訂條件 |
| `pe<15 and roe>10` | 複合條件 |

### Universe 選項

```bash
/screen oversold --universe=tw50     # 台灣50 (50檔)
/screen oversold --universe=listed   # 上市公司 (1,067檔)
/screen oversold --universe=otc      # 上櫃公司 (874檔)
/screen oversold --universe=all      # 全部 (1,941檔)
```

### 匯出 CSV

```bash
/screen oversold --export             # 自動產生檔名
/screen rsi<30 --export=my_data.csv   # 自訂檔名
```

匯出位置：`data/reports/screen_YYYYMMDD_HHMMSS.csv`

---

## 策略回測系統

### 可用策略

| 策略 Key | 名稱 | 說明 |
|----------|------|------|
| `farmerplanting` | 進階農夫播種術 | 基準價加減碼策略，適合趨勢股票長期持有 |
| `momentumbreakout` | 動量突破策略 | ADX 強趨勢 + MACD 黃金交叉 + 成交量確認 |
| `macrossover` | 均線交叉策略 | EMA9/EMA21 交叉 + MA50 趨勢過濾 |
| `bbsqueeze` | 布林壓縮策略 | 低波動壓縮後的向上突破 |

### 策略回測指令

```bash
# 查看所有可用策略
/strategy

# 執行回測（5年歷史數據）
/strategy farmerplanting 2330 backtest
/strategy momentumbreakout 2330 backtest
/strategy macrossover 2330 backtest
/strategy bbsqueeze 2330 backtest
```

---

### 動量突破策略 (Momentum Breakout)

**進場條件** (全部滿足):
- ADX > 25 (強趨勢)
- MACD 黃金交叉 (MACD 上穿信號線)
- 成交量 > 20日均量 × 1.5

**出場條件** (任一觸發):
- ADX < 20 (趨勢轉弱)
- MACD 死亡交叉
- 移動停利 15%

**參數**:
| 參數 | 預設值 | 說明 |
|------|--------|------|
| `adx_entry_threshold` | 25 | ADX 進場門檻 |
| `adx_exit_threshold` | 20 | ADX 出場門檻 |
| `volume_multiplier` | 1.5 | 成交量倍數 |
| `trailing_stop_pct` | 0.15 | 移動停利 15% |

**風險緩解**: 成交量確認 + ADX 過濾假突破

---

### 均線交叉策略 (MA Crossover)

**進場條件**:
- EMA9 上穿 EMA21 (黃金交叉)
- 收盤價 > MA50 (趨勢過濾)

**出場條件**:
- EMA9 下穿 EMA21 (死亡交叉)
- 收盤價 < MA50

**參數**:
| 參數 | 預設值 | 說明 |
|------|--------|------|
| `ema_fast` | 9 | 快速 EMA 週期 |
| `ema_slow` | 21 | 慢速 EMA 週期 |
| `ma_filter` | 50 | 趨勢過濾均線週期 |

**風險緩解**: MA50 趨勢過濾減少盤整期頻繁交易

---

### 布林壓縮策略 (BB Squeeze)

**進場條件**:
- 帶寬收縮至 20% 百分位以下 (壓縮偵測)
- 帶寬開始擴張
- 收盤價突破上軌 (方向性突破)

**出場條件**:
- 價格回歸中軌
- 價格觸及下軌

**參數**:
| 參數 | 預設值 | 說明 |
|------|--------|------|
| `squeeze_percentile` | 20 | 壓縮判定百分位 |
| `lookback_period` | 20 | 帶寬歷史回顧期間 |

**風險緩解**: 只做向上突破，避免壓縮後無方向

---

## Smart Money Screener

### `/smart-money` - 主力足跡選股

基於 **Trend/Volume/Bias** 三維度的主力吸籌選股。

### 評分邏輯 (100分制)

| 維度 | 權重 | 條件 | 分數 |
|------|------|------|------|
| 趨勢型態 | 40% | 極致壓縮 (BB寬度<15%+10天) | +25 |
| | | 帶量突破 | +15 |
| 量能K線 | 35% | OBV 先行創高 | +15 |
| | | 攻擊量 (>2x MV5) | +10 |
| | | K線霸氣 (實體>70%) | +10 |
| 乖離位階 | 25% | 黃金起漲 (乖離5-10%) | +15 |
| | | 站上年線 | +10 |

### 使用方式

```bash
/smart-money              # TW50 (50檔, ~10秒)
/smart-money --tw50       # 台灣50
/smart-money --listed     # 上市公司
/smart-money --otc        # 上櫃公司
/smart-money --all        # 全部市場
/smart-money --fast       # 快速模式 (跳過 OBV 歷史比對)
/smart-money --min=60     # 高分篩選
/smart-money --limit=10    # 限制數量
```

### 使用說明

- 預設 universe 為 `TW50`，適合日常快速查看
- `--listed` 使用上市公司清單
- `--otc` 使用上櫃公司清單
- `--all` 使用上市 + 上櫃合併清單
- `--fast` 會略過 OBV 的較重歷史比對，適合大 universe
- `--min` 可提高篩選門檻，減少輸出數量
- `--limit` 控制最多輸出幾檔
- 如果本機有可用的 warehouse SQLite，`smart-money` 會優先讀本地資料
- `/stocks --sync` 或 `python scripts/fetch_stock_list.py --sync` 會更新 `TW50 / listed / otc / all` 的股票清單檔案
- `/warehouse` 用來查看狀態或同步本地倉庫，`copy` 複製現成 DB，`run` 先執行本地內建 downloader 再同步
預設會自動尋找 `data/local_warehouse/tw_stock_warehouse.db`，也可用 `PULSE_DATA__LOCAL_WAREHOUSE_DB` 指定自訂路徑。
如果這個檔案尚未建立，請先執行 `/warehouse` 或 `/warehouse sync`。

### 輸出範例

```
主力足跡選股 (台灣50, min_score=40)
---
找到 3 檔符合條件的股票:

[★  ] 2317    48.0/100  鴻海
    NT$224 (-2.61%)  乖離MA20:-2.8%  量比:1.4x
    信號: 布林收縮 BB:7.5 | OBV整理 | 長紅100%

圖例: ★★★=80+強勢  ★★=60-79吸籌  ★=40-59觀察
```

別名：`/tvb`, `/主力`

---

## Keltner Channel Strategy

### `/keltner` - 肯特納通道策略

**肯特納通道 (Keltner Channel)** 是一種波動性通道指標，由 Chester Keltner 在 1960 年代開發。
它使用 EMA 作為中軌，ATR 的倍數作為上下軌，與布林通道相比對價格變動的反應更平滑。

### 策略信號

| 信號 | 顏色 | 說明 |
|------|------|------|
| **BUY** | 🟢 綠色 | 價格突破上軌 + EMA 多頭排列 |
| **HOLD** | 🟡 黃色 | 價格在通道內 (中軌與上軌之間) |
| **SELL** | 🔴 紅色 | 價格跌破中軌 |
| **WATCH** | ⚪ 白色 | 接近上軌或成交量不足 |

### 策略參數

```python
# 預設參數
min_avg_volume = 3_000_000   # 最小日均成交量 (股)
ema_periods = (9, 21, 55)    # EMA 週期用於趨勢確認
atr_multiplier = 2.0         # ATR 倍數
atr_period = 10              # ATR 週期
rebalance_frequency = "biweekly"  # 換股頻率
```

### 策略邏輯

#### 買進條件 (BUY)
- 收盤價 **>=** 肯特納上軌 (kc_upper)
- EMA 多頭排列 (EMA 9 > EMA 21 > EMA 55)
- 日均成交量 **>=** 3,000,000 股

#### 持有條件 (HOLD)
- 收盤價在 **肯特納中軌** 與 **肯特納上軌** 之間
- 或收盤價維持在肯特納上軌之上

#### 賣出條件 (SELL)
- 收盤價 **跌破** 肯特納中軌 (保守止損)
- 或收盤價跌破肯特納上軌 (積極止損)

### 使用方式

```bash
# 分析單一股票
/keltner 2330

# 篩選買進信號
/keltner --buy

# 篩選持有信號 (用於倉位檢視)
/keltner --hold

# 篩選賣出信號 (用於倉位檢視)
/keltner --sell

# 自訂最小成交量
/keltner --min-volume=5000000

# 自訂股票清單
/keltner 2330 2303 2379
```

### Python API

```python
from pulse.core.strategies.keltner_channel_strategy import (
    KeltnerChannelStrategy,
    screen_keltner_breakout,
)

# 方式 1: 完整策略物件
strategy = KeltnerChannelStrategy()

# 買進信號篩選
buy_signals = await strategy.screen_buy_signals(limit=20)

# 持有信號篩選
hold_signals = await strategy.screen_hold_signals(limit=20)

# 賣出信號篩選
sell_signals = await strategy.screen_sell_signals(limit=20)

# 完整篩選 (含觀察名單)
all_signals = await strategy.screen(include_watchlist=True)

# 顯示結果
for r in buy_signals:
    print(f"{r.ticker}: {r.signal.value} @ ${r.price}")
    print(f"  KC Upper: {r.kc_upper:.2f}, KC Middle: {r.kc_middle:.2f}")
    print(f"  EMA: {r.ema_9:.2f} > {r.ema_21:.2f} > {r.ema_55:.2f}")
    print(f"  成交量: {r.avg_volume:,}")

# 方式 2: 快速篩選
quick_results = await screen_keltner_breakout(universe=["2330", "2303"], limit=10)
```

### 輸出範例

```
肯特納通道策略 (BUY 信號)
---
找到 5 檔符合條件的股票:

[BUY] 2330  台積電
    價格: NT$1,025 (+2.5%)
    KC Upper: 1,020.0 | KC Middle: 980.0 | KC Lower: 940.0
    EMA: 1,000 > 990 > 970 (多頭排列)
    成交量: 5,234,567 (1.3x 平均)
    距離上軌: +0.5%

[BUY] 2303  聯電
    價格: NT$52.5 (+1.8%)
    KC Upper: 51.8 | KC Middle: 49.2 | KC Lower: 46.6
    EMA: 52.1 > 50.5 > 48.9 (多頭排列)
    成交量: 3,456,789 (1.1x 平均)
    距離上軌: +1.4%

---
篩選條件:
  - 價格 >= 肯特納上軌
  - EMA 多頭排列 (EMA 9 > EMA 21 > EMA 55)
  - 日均成交量 >= 3,000,000 股
```

### 肯特納通道 vs 布林通道

| 特性 | 肯特納通道 | 布林通道 |
|------|------------|----------|
| 中軌 | EMA (20) | SMA (20) |
| 帶寬 | ATR × 倍數 | 標準差 × 倍數 |
| 反應 | 更平滑 | 更敏感 |
| 適用 | 趨勢確認 | 波動性測量 |

### 策略優勢與劣勢

#### 優勢
- 順勢交易，追蹤趨勢
- 明確的進場/出场規則
- 濾除噪音，減少假突破
- 適合波段行情

#### 劣勢
- 盤整市場可能產生假信號
- 參數需要優化
- 趨勢反轉時可能造成較大虧損
- 不適合當日沖銷

### 風險控制建議

1. **成交量濾網**: 排除日均成交量 < 3,000,000 股的股票
2. **EMA 確認**: 只在 EMA 多頭排列時買進
3. **換股頻率**: 兩週檢視一次 (Bi-weekly)
4. **止損紀律**: 跌破中軌立即止損
5. **分散投資**: 不要把所有資金投入單一股票

別名：`/kc`

---

## Happy Lines (樂活五線譜)

### `/happy-lines` - 樂活五線譜分析

**樂活五線譜**是一種基於統計分佈的股價位階判斷工具，透過移動平均線和標準差計算五條關鍵價位線，將股價分為五個區域，協助投資人判斷進出場時機。

### 五線譜計算邏輯

| 線位 | 名稱 | 計算公式 | 投資建議 |
|------|------|----------|----------|
| **第5線** | 過熱線 | 中軌 + (標準差 × 2.0) | 考慮減碼/停利 |
| **第4線** | 偏高線 | 中軌 + (標準差 × 1.0) | 分批獲利 |
| **第3線** | 平衡線 | N日移動平均 (預設120日) | 觀望等待 |
| **第2線** | 偏低線 | 中軌 - (標準差 × 1.0) | 分批布局 |
| **第1線** | 超跌線 | 中軌 - (標準差 × 2.0) | 考慮進場/加碼 |

### 策略參數

```python
# 預設參數
period = 120                    # 計算週期 (日)
min_avg_volume = 1_000_000      # 最小日均成交量 (股)
```

### 週期選擇建議

| 週期 | 適用風格 | 說明 |
|------|----------|------|
| 20日 | 短線 | 適合當沖或隔日沖 |
| 60日 | 中線 | 適合波段操作 |
| **120日** | **長線** | **適合長期投資 (預設)** |
| 240日 | 年線 | 適合價值投資 |

### 策略邏輯

#### 買進條件
- 股價處於 **第1線** 或 **第2線** 區域 (超跌/偏低)
- 趨勢為多頭或盤整 (非空頭)
- 日均成交量 >= 1,000,000 股

#### 賣出條件
- 股價突破 **第5線** (過熱區)
- 或股價跌破 **第3線** 且趨勢轉空

#### 持有條件
- 股價在 **第2-4線** 之間
- 或已進場且趨勢仍偏多

### 使用方式

```bash
# 分析單一股票 (預設120日週期)
/happy-lines 2330

# 使用不同週期
/happy-lines 2330 period=60     # 60日週期
/happy-lines 2330 period=240    # 240日週期

# 別名使用
/happy 2330
/五線譜 2330
/hl 2330
```

### 篩選功能

```bash
# 篩選超跌股票 (第1線附近)
/screen happy_oversold

# 篩選過熱股票 (第5線附近)
/screen happy_overbought

# 篩選便宜股票 (第1-2線區間)
/screen happy_cheap

# 篩選昂貴股票 (第4-5線區間)
/screen happy_expensive

# 指定股票池
/screen happy_cheap --universe=tw50
```

### Python API

```python
from pulse.core.strategies.happy_lines import (
    HappyLinesStrategy,
    HappyLinesSignal,
    screen_happy_lines,
)

# 方式 1: 完整策略物件
strategy = HappyLinesStrategy(period=120)

# 買進信號篩選
buy_signals = await strategy.screen_buy_signals(limit=20)

# 賣出信號篩選
sell_signals = await strategy.screen_sell_signals(limit=20)

# 超跌股票篩選
oversold = await strategy.screen_oversold(limit=20)

# 過熱股票篩選
overbought = await strategy.screen_overbought(limit=20)

# 顯示結果
for r in buy_signals:
    print(f"{r.ticker}: {r.signal.value} @ ${r.price}")
    print(f"  位階: {r.zone.value} ({r.position_ratio:.1f}%)")
    print(f"  五線: L1={r.line_1:.0f} L2={r.line_2:.0f} L3={r.line_3:.0f} L4={r.line_4:.0f} L5={r.line_5:.0f}")

# 方式 2: 快速篩選
quick_results = await screen_happy_lines(
    universe=["2330", "2454"],
    limit=10,
    period=120,
    buy_signals_only=True
)
```

### 輸出範例

```
【樂活五線譜分析 - 2330】

第5線 (過熱區): 1,250
第4線 (偏高區): 1,150
第3線 (平衡區): 1,050 ← 你在這裡
第2線 (偏低區): 950
第1線 (超跌區): 850

【分析摘要】
  當前價格: NT$ 1,085
  位階百分比: 58.0%
  所在區域: 平衡區
  計算週期: 120日

【交易訊號】
  趨勢: Sideways
  訊號: NEUTRAL
```

### 與其他策略的比較

| 特性 | 樂活五線譜 | 布林通道 | 肯特納通道 |
|------|------------|----------|------------|
| 中軌 | 移動平均 | SMA | EMA |
| 帶寬計算 | 標準差 | 標準差 | ATR |
| 區域劃分 | 五個明確區域 | 連續分佈 | 三條線 |
| 適用場景 | 位階判斷 | 波動性測量 | 趨勢確認 |
| 主要用途 | 進出場時機 | 超買超賣 | 順勢交易 |

### 策略優勢與劣勢

#### 優勢
- **統計基礎**: 基於標準差，客觀判斷位階
- **簡單易懂**: 五個區域明確，易於理解
- **適合波段**: 對中長期趨勢判斷準確
- **可搭配使用**: 可與農夫播種術等策略結合，作為加減碼參考

#### 劣勢
- **週期敏感**: 不同週期結論可能差異較大
- **盤整失真**: 長期盤整後突破可能產生假信號
- **單一維度**: 僅考慮價格，未考慮成交量等其他因素

### 使用建議

1. **選擇合適週期**: 根據投資風格選擇 60日(波段) 或 120日(長期)
2. **搭配趨勢確認**: 結合 EMA 或 MACD 確認趨勢方向
3. **分批操作**: 在第1-2線分批買入，第4-5線分批賣出
4. **設定停損**: 跌破第1線且趨勢轉空時考慮停損
5. **結合基本面**: 低估區+好基本面 = 更好的投資機會

別名：`/happy`, `/五線譜`, `/hl`

---

## 價格預測 (AutoTS)

### `/forecast` - AI 價格預測

基於 **AutoTS** (M6 預測競賽冠軍) 的多模型自動選擇預測引擎，支援快速與完整兩種模式。

### 預測模式

| 模式 | 說明 | 預估時間 |
|------|------|----------|
| **fast** (預設) | `superfast` 模型清單，1 代演化，1 次驗證 | ~18 秒 |
| **full** | `superfast` 模型清單，3 代演化，2 次驗證 | ~30 秒 |

### 使用方式

```bash
# 快速模式 (預設 7 天)
/forecast 2330

# 指定天數
/forecast 2330 14

# 完整模式
/forecast 2330 full
/forecast 2330 14 full

# 順序不拘
/forecast 2330 full 14
```

### 模型選擇

AutoTS 會自動從以下模型中選擇最佳預測模型：

| 模型 | 說明 |
|------|------|
| GLS | 廣義最小平方法 |
| ETS | 指數平滑法 |
| LastValueNaive | 最後值延伸 |
| AverageValueNaive | 平均值延伸 |
| SeasonalNaive | 季節性延伸 |
| SeasonalityMotif | 季節性模式匹配 |
| SectionalMotif | 區段模式匹配 |
| BasicLinearModel | 基本線性模型 |

### 輸出範例

```
=== 價格預測: 2330 (7天) ===

模式: 快速模式
模型: GLS

現價: NT$ 1,025.00
目標價: NT$ 1,042.00
預期漲跌: +1.66%

趨勢: + 上漲
支撐位: NT$ 1,010.00
壓力位: NT$ 1,055.00
信心度: [########--] 78%

圖表已儲存: charts/forecast_2330_20260208.png
```

### Fallback 機制

若 AutoTS 未安裝或執行失敗，系統會自動退回 **MA Extrapolation**（移動平均外推法），信心度固定為 50%。

### 自然語言支援

在 Smart Agent 模式下，可使用自然語言觸發預測：

```
> 預測 2330
> 完整預測 2330     → 自動使用 full 模式
> 詳細預測台積電    → 自動使用 full 模式
```

別名：`/pred`, `/predict`

---

## SAPTA 預漲偵測

### `/sapta` - 預漲信號檢測

**SAPTA** (System for Analyzing Pre-markup Technical Accumulation) - 基於機器學習的預漲偵測引擎。

### 狀態等级

| 狀態 | 分數 | 意義 |
|------|------|------|
| **PRE-MARKUP** | >= 47 | 準備突破 |
| **SIAP** | >= 35 | 接近就緒 |
| **WATCHLIST** | >= 24 | 早期吸籌 |
| **SKIP** | < 24 | 無信號 |

### 使用方式

```bash
/sapta 2330                 # 單一股票
/sapta 2330 --detailed      # 詳細分析
/sapta chart 2330           # 產生圖表
/sapta scan                 # 掃描 TW50
/sapta scan --listed        # 掃描上市公司
```

### 圖表輸出

```bash
/sapta chart 2330           # 基本圖表
/sapta chart 2330 --detailed # 詳細分析圖
```

圖表儲存：`charts/sapta_{TICKER}_{YYYYMMDD}.png`

---

## 範例

### 基本分析

```
> 分析 2330
> 台積電技術面如何？
> 比較 2330 和 2317
```

### 篩選股票

```
> 找出超賣的股票
> 找 RSI < 30 的股票
> 篩選突破股票
```

### 交易相關

```
> 幫 2330 建立交易計畫
> 檢查 2303 的潛在買點
```

### SAPTA

```
> 找預漲股票
> 找準備突破的股票
> 掃描全市場預漲股
```

---

## 常見問題

### Q1: 沒有 API Key 怎麼辦？

**推薦 Groq (免費且快速)：**
1. 訪問 https://console.groq.com/keys
2. 註冊並建立 API Key
3. 設定 `GROQ_API_KEY` 環境變數

### Q2: Rate Limit 怎麼辦？

```bash
# 切換到其他 Provider
export GROQ_API_KEY="your_groq_key"
export PULSE_AI__DEFAULT_MODEL="groq/llama-3.3-70b-versatile"
```

### Q3: 如何切換 AI 模型？

```bash
# 方法1: 使用命令
/models

# 方法2: 環境變數
export PULSE_AI__DEFAULT_MODEL="groq/llama-3.3-70b-versatile"

# 方法3: 編輯 .env
PULSE_AI__DEFAULT_MODEL=deepseek/deepseek-v4-flash
```

### Q4: 法人動向沒有數據？

確認已設定 `FINMIND_TOKEN`：
- 訪問 https://finmindtrade.com/ 註冊
- 取得 Token 填入 `.env`

### Q5: CLI 沒有回應？

1. 檢查網路連線
2. 確認 API Key 正確
3. 使用 `/clear` 清除對話
4. 檢查日誌：`data/logs/pulse.log`

### Q6: 數據源

| 數據源 | 用途 |
|--------|------|
| **FinMind** | 法人動向、融資融券、基本面 |
| **Yahoo Finance** | 股價、技術指標 |
| **Fugle** | 即時報價、52週高低 |

---

**最後更新**: 2026-02-08 (v0.4.1 - AutoTS 預測引擎，支援快速/完整模式)
