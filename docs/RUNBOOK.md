# 運維手冊 (Runbook)

> 本文件從 `pyproject.toml` 與 `.env.example` 自動生成
> 生成日期：2026-02-07

## 目錄

- [部署流程](#部署流程)
- [監控與告警](#監控與告警)
- [常見問題與解決方案](#常見問題與解決方案)
- [回滾程序](#回滾程序)
- [故障排除](#故障排除)
- [緊急聯絡](#緊急聯絡)

---

## 部署流程

### 部署前檢查清單

```bash
# 1. 確保所有測試通過
python -m pytest

# 2. 程式碼檢查
ruff check pulse/

# 3. 類型檢查
mypy pulse/

# 4. 確認版本號
# 檢查 pyproject.toml 中的 version 欄位
```

### 標準部署流程

#### 方法 1: 從原始碼安裝（開發/測試環境）

```bash
# 1. 複製最新程式碼
git clone https://github.com/alingowangxr/TW-Pulse-CLI.git
cd TW-Pulse-CLI

# 2. 建立虛擬環境
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# 或: .venv\Scripts\activate  # Windows

# 3. 安裝
pip install -e ".[dev]"

# 4. 配置環境變數
cp .env.example .env
# 編輯 .env 填入 API 金鑰

# 5. 驗證安裝
pulse --version
```

#### 方法 2: 生產部署

```bash
# 1. 更新程式碼
git pull origin main

# 2. 重新安裝
pip install -e .

# 3. 驗證
pulse
```

### 版本發布流程

1. **更新版本號** (`pyproject.toml`)
   ```toml
   [project]
   version = "0.1.0"  # 更新此處
   ```

2. **更新 CHANGELOG** (如有)

3. **建立 Git Tag**
   ```bash
   git tag -a v0.1.0 -m "Release version 0.1.0"
   git push origin v0.1.0
   ```

4. **推送到 main**
   ```bash
   git push origin main
   ```

---

## 監控與告警

### 應用程式監控

#### 日誌位置

```
data/logs/           # 應用程式日誌
data/cache/          # 快取數據
.pytest_cache/       # 測試快取
```

#### 關鍵指標

| 指標 | 檢查方式 | 正常範圍 |
|------|----------|----------|
| 應用啟動 | `pulse` 命令 | 無錯誤啟動 |
| API 連線 | 測試指令碼 | 200 OK |
| 快取命中率 | 日誌分析 | >80% |
| 記憶體使用 | 系統監控 | <500MB |

### 健康檢查命令

```bash
# 1. 測試 AI 連線
python scripts/check_api_keys.py

# 2. 測試數據源
python scripts/fetch_stock_list.py

# 3. 驗證模型過濾
python scripts/verify_model_filtering.py

# 4. 運行完整測試
python -m pytest --tb=short
```

### 資料源狀態監控

| 資料源 | 狀態檢查 | 降級策略 |
|--------|----------|----------|
| FinMind | FINMIND_TOKEN 有效 | 使用 yfinance |
| yfinance | 網路連線 | 使用 Fugle |
| Fugle | FUGLE_API_KEY 有效 | 僅用本地快取 |

---

## 常見問題與解決方案

### 安裝問題

#### Q1: 安裝時出現相依性衝突

**症狀：**
```
ERROR: Cannot install pulse-cli because these package versions have conflicting dependencies.
```

**解決方案：**
```bash
# 1. 清除 pip 快取
pip cache purge

# 2. 更新 pip
pip install --upgrade pip

# 3. 重新安裝
pip install -e ".[dev]" --force-reinstall
```

#### Q2: Playwright 安裝失敗

**症狀：**
```
browserType.launch: Executable doesn't exist
```

**解決方案：**
```bash
# 安裝 Playwright 瀏覽器
playwright install chromium
```

### 運行問題

#### Q3: 應用無法啟動（缺少 API 金鑰）

**症狀：**
```
ConfigurationError: Missing required API key
```

**解決方案：**
```bash
# 1. 確認 .env 檔案存在
ls -la .env

# 2. 設定至少一個 AI API 金鑰
export DEEPSEEK_API_KEY="sk-xxx"
# 或編輯 .env 檔案

# 3. 驗證
python scripts/check_api_keys.py
```

#### Q4: FinMind API 限流

**症狀：**
```
FinMind API rate limit exceeded
```

**解決方案：**
```bash
# 1. 檢查 FinMind Token 是否設定
echo $FINMIND_TOKEN

# 2. 確認 Token 有效（網站檢查配額）
# https://finmindtrade.com/analysis/#/account/login

# 3. 使用備用數據源（yfinance）
# 應用會自動降級
```

#### Q5: 快取損壞

**症狀：**
```
Cache corruption error
Diskcache error
```

**解決方案：**
```bash
# 1. 清除快取
rm -rf data/cache/*

# 2. 重新啟動應用
pulse
```

### 測試問題

#### Q6: 測試失敗（網路相關）

**症狀：**
```
pytest - 網路超時錯誤
```

**解決方案：**
```bash
# 使用離線模式運行測試
python -m pytest -m "not network"

# 或增加超時時間
python -m pytest --timeout=300
```

#### Q7: MyPy 類型錯誤

**症狀：**
```
error: Incompatible types
```

**解決方案：**
```bash
# 檢查並修復類型註解
mypy pulse/ --show-error-codes

# 如有第三方庫缺失類型，加入 stubs
pip install types-requests types-pyyaml
```

### 數據問題

#### Q8: 股票數據缺失

**症狀：**
```
No data available for ticker
```

**解決方案：**
```bash
# 1. 確認股票代號格式（4位數字）
# 正確：2330
# 錯誤：2330.TW

# 2. 清除該股票快取
rm -rf data/cache/*2330*

# 3. 檢查數據源狀態
python scripts/fetch_stock_list.py
```

---

## 回滾程序

### 緊急回滾（程式碼層級）

```bash
# 1. 查看提交歷史
git log --oneline -10

# 2. 回滾到上一個穩定版本
git revert HEAD

# 3. 或強制回滾到特定提交
git reset --hard <commit-hash>

# 4. 強制推送（謹慎使用）
git push origin main --force
```

### 資料回滾

```bash
# 1. 備份當前資料
cp -r data/cache data/cache.backup.$(date +%Y%m%d)

# 2. 從備份恢復
rm -rf data/cache
cp -r data/cache.backup.<date> data/cache

# 3. 驗證
pulse
```

### 環境回滾

```bash
# 1. 移除虛擬環境
deactivate
rm -rf .venv

# 2. 重新建立乾淨環境
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 3. 驗證
python -m pytest
```

---

## 故障排除

### 診斷流程

```
問題發生
    ↓
檢查日誌 (data/logs/)
    ↓
運行健康檢查命令
    ↓
是 API 問題？ → 檢查 API 金鑰
    ↓
是數據問題？ → 清除快取
    ↓
是環境問題？ → 重建虛擬環境
    ↓
聯絡支援
```

### 收集診斷資訊

```bash
# 1. 環境資訊
python --version
pip list | grep pulse

# 2. 配置檢查
cat .env | grep -v "KEY\|TOKEN\|SECRET"

# 3. 測試結果
python -m pytest --tb=short -q > test_results.txt

# 4. 日誌收集
ls -la data/logs/
tail -n 100 data/logs/*.log
```

### 已知限制

| 問題 | 說明 | 因應措施 |
|------|------|----------|
| Windows 終端機相容性 | 部分 Unicode 表情符號可能無法顯示 | 使用標準 ASCII 輸出 |
| FinMind 免費版限制 | 每小時 600 次請求 | 設定 FINMIND_TOKEN |
| yfinance 台股數據 | 可能有 15 分鐘延遲 | 使用 Fugle 即時報價 |
| 記憶體使用 | 大量股票篩選時可能超過 1GB | 分批處理 |

---

## 緊急聯絡

### 資源

| 資源 | 連結 |
|------|------|
| GitHub Issues | https://github.com/alingowangxr/TW-Pulse-CLI/issues |
| 文件 | https://github.com/alingowangxr/TW-Pulse-CLI/tree/main/docs |
| README | https://github.com/alingowangxr/TW-Pulse-CLI/blob/main/README.md |

### API 支援

| 服務 | 支援連結 |
|------|----------|
| DeepSeek | https://platform.deepseek.com/support |
| FinMind | https://finmindtrade.com/ |
| Fugle | https://developer.fugle.tw/support |

### 緊急修復檢查清單

- [ ] 確認問題範圍（本地/全局）
- [ ] 檢查 API 金鑰有效性
- [ ] 驗證網路連線
- [ ] 清除快取並重試
- [ ] 查看應用日誌
- [ ] 運行健康檢查腳本
- [ ] 如有必要，執行回滾程序

---

## 維護排程

### 每日

- [ ] 檢查應用日誌是否有錯誤
- [ ] 驗證 API 連線狀態

### 每週

- [ ] 運行完整測試套件
- [ ] 檢查依賴項更新
- [ ] 清理舊快取檔案

### 每月

- [ ] 輪換 API 金鑰（建議）
- [ ] 檢查磁碟空間
- [ ] 備份重要資料

---

*最後更新：2026-02-07*
