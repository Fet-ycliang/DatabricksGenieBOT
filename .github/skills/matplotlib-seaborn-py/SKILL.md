---
name: matplotlib-seaborn-py
description: 用於資料視覺化的 Matplotlib 和 Seaborn。當在 Python 中產生圖表、圖形或統計圖時使用。
---

# Matplotlib & Seaborn for Python

建立靜態、動畫和互動式視覺化內容。

## 安裝

```bash
pip install matplotlib seaborn
```

## 基本設定

```python
import matplotlib.pyplot as plt
import seaborn as sns
import io

# 設定樣式以獲得更好的美感
sns.set_theme(style="whitegrid")

# 針對非 GUI 環境 (例如網頁應用程式) 的修正
plt.switch_backend('Agg')
```

## 建立圖表圖片 (Base64)

適用於本地回傳圖片或透過 API 回傳而不儲存到磁碟。

```python
import base64

def create_chart_image(data):
    plt.figure(figsize=(10, 6))

    # 建立圖表
    sns.barplot(x="category", y="value", data=data)
    plt.title("My Chart")

    # 儲存到緩衝區
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()

    # 轉換為 base64
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return image_base64
```

## 常見圖表類型

### 長條圖 (Categorical)

```python
sns.barplot(
    data=df,
    x="category",
    y="value",
    hue="group",
    errorbar=None  # 移除誤差線以獲得更乾淨的外觀
)
```

### 折線圖 (Trends)

```python
sns.lineplot(
    data=df,
    x="date",
    y="value",
    marker="o"
)
```

### 散佈圖 (Relationships)

```python
sns.scatterplot(
    data=df,
    x="x_col",
    y="y_col",
    hue="category",
    size="size_col"
)
```

### 圓餅圖 (Matplotlib)

Seaborn 不直接支援圓餅圖。

```python
plt.pie(
    x=df['value'],
    labels=df['category'],
    autopct='%.1f%%',
    startangle=90
)
```

## 中文字元支援

Matplotlib 預設通常無法渲染中文字元。

```python
import matplotlib.font_manager as fm

# 選項 1: 使用系統字型 (Windows)
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']

# 選項 2: 使用特定字型檔案
font_path = 'path/to/font.ttf'
font_prop = fm.FontProperties(fname=font_path)

plt.title("中文標題", fontproperties=font_prop)
```

## 最佳實踐

1.  **使用 `plt.close()`**：務必關閉圖形以釋放記憶體，特別是在網頁應用程式中。
2.  **`bbox_inches='tight'`**：儲存時使用此參數以防止標籤被切掉。
3.  **非互動式後端**：設定 `plt.switch_backend('Agg')` 以避免在伺服器環境中發生錯誤。
4.  **Seaborn 主題**：使用 `sns.set_theme()` 立即改善預設 matplotlib 的視覺效果。
