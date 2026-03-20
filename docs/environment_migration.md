# 環境一致性測試與遷移指南

## 📊 當前狀態

### ✅ venv 環境 (本地)
- **路徑**: `D:\azure_code\DatabricksGenieBOT\env`
- **Python**: 3.12.7
- **套件數**: 136 個
- **狀態**: ✓ 運行正常
- **關鍵套件**:
  - fastapi: 0.128.5
  - uvicorn: 0.40.0
  - httpx: 0.27+
  - pandas: 2.3.3
  - botbuilder-core: 4.17.0

### 🔄 uv 環境 (目標)
- **路徑**: `.venv` (待創建)
- **Python**: 3.12
- **套件數**: 根據 `pyproject.toml` 安裝
- **狀態**: 需要測試

## 🎯 建議：統一使用 uv

### 原因：
1. **開發生產一致性**: 上版用 uv，本地也應該用 uv
2. **依賴鎖定**: uv 有 `uv.lock` 確保版本一致
3. **效能更好**: 套件安裝速度快 10-100 倍
4. **更好的依賴解析**: 避免版本衝突

## 📋 遷移步驟

### Step 1: 備份現有 venv 環境
```bash
cd d:/azure_code/DatabricksGenieBOT
./env/Scripts/pip freeze > requirements_venv_backup.txt
```

### Step 2: 使用 uv 創建新環境
```bash
# 創建 .venv
uv venv

# 同步安裝所有依賴（從 pyproject.toml）
uv sync
```

### Step 3: 測試兩種環境
```bash
# 測試 venv
PYTHONPATH=. ./env/Scripts/python tests/test_environment.py

# 測試 uv
uv run python tests/test_environment.py
```

### Step 4: 比較套件差異
```bash
# 導出兩種環境的套件清單
./env/Scripts/pip freeze | sort > venv_packages.txt
uv pip freeze | sort > uv_packages.txt

# 比較差異 (PowerShell)
Compare-Object (Get-Content venv_packages.txt) (Get-Content uv_packages.txt)

# 比較差異 (bash)
diff venv_packages.txt uv_packages.txt
```

## 🧪 測試檢查清單

### ✅ 基礎測試
- [ ] Python 版本一致 (3.12.7)
- [ ] 所有關鍵套件可導入
- [ ] 套件版本符合 pyproject.toml
- [ ] 應用程式主模組可載入

### ✅ 功能測試
- [ ] FastAPI 服務可啟動
- [ ] Bot Framework 連接正常
- [ ] Databricks SDK 可用
- [ ] 圖表生成功能正常
- [ ] 健康檢查端點回應正常

### ✅ 整合測試
```bash
# 使用 venv 啟動服務
./env/Scripts/activate
uvicorn app.main:app --reload

# 使用 uv 啟動服務
uv run uvicorn app.main:app --reload

# 測試 API 端點
curl http://localhost:8000/
curl http://localhost:8000/health
curl http://localhost:8000/docs
```

## 🔧 測試命令

### 快速測試 (venv)
```bash
cd d:/azure_code/DatabricksGenieBOT
./env/Scripts/activate
python tests/test_environment.py
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 快速測試 (uv)
```bash
cd d:/azure_code/DatabricksGenieBOT
uv run python tests/test_environment.py
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 📝 版本控制建議

### 建議忽略的檔案 (.gitignore)
```
# Virtual Environments
env/
.venv/
venv/

# uv
uv.lock
.python-version

# 測試產生的檔案
*_packages.txt
requirements_venv_backup.txt
```

### 需要提交的檔案
```
✓ pyproject.toml       # uv 依賴定義
✓ uv.lock             # uv 鎖定檔案 (建議提交)
✓ README.md           # 文檔更新
✓ tests/test_environment.py  # 環境測試腳本
```

## 🚀 最佳實踐

### 開發流程
1. **本地開發**: 使用 `uv run` 執行命令
2. **安裝新套件**: `uv add <package>` (自動更新 pyproject.toml)
3. **同步依賴**: `uv sync` (安裝 pyproject.toml 中的所有依賴)
4. **啟動服務**: `uv run uvicorn app.main:app --reload`

### CI/CD 流程
```yaml
# Azure Pipeline 範例
steps:
  - script: |
      curl -LsSf https://astral.sh/uv/install.sh | sh
      uv sync
      uv run uvicorn app.main:app
```

## ⚠️ 注意事項

### 遷移時要注意：
1. **環境變數**: 確保 `.env` 檔案配置正確
2. **依賴版本**: 檢查是否有版本衝突
3. **測試覆蓋**: 執行完整測試確保功能正常
4. **文檔更新**: 更新 README.md 中的啟動命令

### 可能的問題：
1. **網路問題**: 如果 `uv sync` 失敗，檢查網路連線或使用鏡像源
2. **Python 版本**: 確保 Python 3.12+ 已安裝
3. **權限問題**: Windows 可能需要管理員權限

## 📊 效能比較

| 操作 | venv + pip | uv |
|------|------------|-----|
| 安裝所有依賴 | ~2-5 分鐘 | ~10-30 秒 |
| 依賴解析 | 較慢 | 極快 |
| 鎖定檔案 | 無 | uv.lock |
| 虛擬環境創建 | ~10 秒 | ~2 秒 |

## ✅ 遷移完成檢查

完成以下項目表示遷移成功：
- [ ] `.venv` 環境創建成功
- [ ] 所有依賴安裝完成
- [ ] 測試腳本通過
- [ ] 服務可正常啟動
- [ ] API 端點正常回應
- [ ] 文檔已更新
- [ ] 舊 `env/` 可安全刪除
