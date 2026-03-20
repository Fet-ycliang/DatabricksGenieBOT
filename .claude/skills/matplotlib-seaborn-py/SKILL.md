---
name: matplotlib-seaborn-py
description: Matplotlib and Seaborn for data visualization. Use when generating charts, plots, or statistical graphics in Python.
---

# Matplotlib & Seaborn for Python

Create static, animated, and interactive visualizations.

## Installation

```bash
pip install matplotlib seaborn
```

## Basic Setup

```python
import matplotlib.pyplot as plt
import seaborn as sns
import io

# Set style for better aesthetics
sns.set_theme(style="whitegrid")

# Fix for non-GUI environments (e.g., web apps)
plt.switch_backend('Agg')
```

## Creating a Chart Image (Base64)

Useful for returning images locally or via APIs without saving to disk.

```python
def create_chart_image(data):
    plt.figure(figsize=(10, 6))

    # Create plot
    sns.barplot(x="category", y="value", data=data)
    plt.title("My Chart")

    # Save to buffer
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    plt.close()

    # Convert to base64
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    return image_base64
```

## Common Chart Types

### Bar Chart (Categorical)

```python
sns.barplot(
    data=df,
    x="category",
    y="value",
    hue="group",
    errorbar=None  # Remove error bars for cleaner look
)
```

### Line Chart (Trends)

```python
sns.lineplot(
    data=df,
    x="date",
    y="value",
    marker="o"
)
```

### Scatter Plot (Relationships)

```python
sns.scatterplot(
    data=df,
    x="x_col",
    y="y_col",
    hue="category",
    size="size_col"
)
```

### Pie Chart (Matplotlib)

Seaborn doesn't support pie charts directly.

```python
plt.pie(
    x=df['value'],
    labels=df['category'],
    autopct='%.1f%%',
    startangle=90
)
```

## Chinese Character Support

Matplotlib often fails to render Chinese characters by default.

```python
import matplotlib.font_manager as fm

# Option 1: Use a system font (Windows)
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']

# Option 2: Use a specific font file
font_path = 'path/to/font.ttf'
font_prop = fm.FontProperties(fname=font_path)

plt.title("中文標題", fontproperties=font_prop)
```

## Best Practices

1.  **Use `plt.close()`**: Always close figures to free up memory, especially in web apps.
2.  **`bbox_inches='tight'`**: Use this when saving to prevent cutting off labels.
3.  **Non-Interactive Backend**: Set `plt.switch_backend('Agg')` to avoid errors in server environments.
4.  **Seaborn Themes**: Use `sns.set_theme()` for immediate visual improvement over default matplotlib.
