---
name: python-dotenv
description: Manage environment variables with python-dotenv. Use when dealing with configuration, secrets, or .env files.
---

# python-dotenv

Read key-value pairs from a `.env` file and set them as environment variables.

## Installation

```bash
pip install python-dotenv
```

## Basic Usage

Load `.env` file located in the current directory or parents:

```python
from dotenv import load_dotenv
import os

# Load variables
load_dotenv()

# Access variable
api_key = os.getenv("API_KEY")

# With default value
debug_mode = os.getenv("DEBUG", "False")
```

## Explicit Path

Load from a specific file path:

```python
from dotenv import load_dotenv
from pathlib import Path

env_path = Path('.') / '.env.local'
load_dotenv(dotenv_path=env_path)
```

## Override

By default, `load_dotenv` does **not** override existing environment variables. Use `override=True` to force update.

```python
load_dotenv(override=True)
```

## .env File Format

```text
# Comments start with #
API_KEY=your-secret-key
DEBUG=True
PORT=8080

# Multiline values
PRIVATE_KEY="-----BEGIN RSA PRIVATE KEY-----
...
-----END RSA PRIVATE KEY-----"
```

## Best Practices

1.  **Don't commit `.env`**: Add `.env` to `.gitignore`.
2.  **Use `env.example`**: Commit a template file with placeholder values.
3.  **Load early**: Call `load_dotenv()` at the very beginning of your application entry point (e.g., `app.py`, `main.py`).
4.  **Use `os.environ` vs `os.getenv`**:
    - Use `os.environ["KEY"]` when the variable is **required** (crashes if missing).
    - Use `os.getenv("KEY")` when it is **optional**.
