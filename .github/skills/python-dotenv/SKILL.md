---
name: python-dotenv
description: 使用 python-dotenv 管理環境變數。在處理設定、秘密或 .env 檔案時使用。
---

# python-dotenv

從 `.env` 檔案讀取鍵值對並將其設定為環境變數。

## 安裝

```bash
pip install python-dotenv
```

## 基本用法

載入位於目前目錄或父目錄中的 `.env` 檔案：

```python
from dotenv import load_dotenv
import os

# 載入變數
load_dotenv()

# 存取變數
api_key = os.getenv("API_KEY")

# 帶有預設值
debug_mode = os.getenv("DEBUG", "False")
```

## 明確路徑

從特定檔案路徑載入：

```python
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env.local'
load_dotenv(dotenv_path=env_path)
```

## 覆寫 (Override)

預設情況下，`load_dotenv` **不會** 覆寫現有的環境變數。使用 `override=True` 強制更新。

```python
load_dotenv(override=True)
```

## .env 檔案格式

```text
# 註解以 # 開頭
API_KEY=your-secret-key
DEBUG=True
PORT=8080

# 多行值
PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----
...
-----END RSA PRIVATE KEY-----"
```

## 最佳實踐

1.  **不要提交 `.env`**：將 `.env` 新增至 `.gitignore`。
2.  **使用 `env.example`**：提交帶有預留位置值的範本檔案。
3.  **儘早載入**：在應用程式入口點 (例如 `app.py`, `main.py`) 的最開頭呼叫 `load_dotenv()`。
4.  **使用 `os.environ` vs `os.getenv`**：
    - 當變數是 **必要** 時使用 `os.environ["KEY"]` (若遺失會崩潰)。
    - 當變數是 **選填** 時使用 `os.getenv("KEY")`。
