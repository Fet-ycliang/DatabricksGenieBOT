"""Adaptive Card 統一常數定義。

集中管理所有 Card 的版本號、顏色主題、Emoji 和共用樣式，
確保整個應用程式的 UI 一致性。
"""

# Adaptive Card Schema 和版本
ADAPTIVE_CARD_SCHEMA = "http://adaptivecards.io/schemas/adaptive-card.json"
ADAPTIVE_CARD_VERSION = "1.5"
ADAPTIVE_CARD_CONTENT_TYPE = "application/vnd.microsoft.card.adaptive"

# Emoji 常數
EMOJI_BOT = "\U0001F916"       # 🤖
EMOJI_CHART_BAR = "\U0001F4CA"  # 📊
EMOJI_CHART_PIE = "\U0001F967"  # 🥧
EMOJI_CHART_LINE = "\U0001F4C8" # 📈
EMOJI_SUCCESS = "\u2705"        # ✅
EMOJI_ERROR = "\u274C"          # ❌
EMOJI_WARNING = "\u26A0\uFE0F"  # ⚠️
EMOJI_BULB = "\U0001F4A1"      # 💡
EMOJI_USER = "\U0001F464"       # 👤
EMOJI_WAVE = "\U0001F44B"       # 👋
EMOJI_SPARKLE = "\u2728"        # ✨
EMOJI_THUMBS_UP = "\U0001F44D"  # 👍
EMOJI_THUMBS_DOWN = "\U0001F44E" # 👎
EMOJI_QUESTION = "\u2753"       # ❓
EMOJI_GEAR = "\u2699\uFE0F"     # ⚙️
EMOJI_ROCKET = "\U0001F680"     # 🚀
EMOJI_RETRY = "\U0001F504"      # 🔄

# 圖表 Emoji 對照
CHART_ICONS = {
    'bar': EMOJI_CHART_BAR,
    'pie': EMOJI_CHART_PIE,
    'line': EMOJI_CHART_LINE,
}

# 使用 Adaptive Cards 語義顏色（支援 Dark Mode）
# 這些是 Adaptive Cards 內建顏色名稱，會自動適應深色/淺色主題
SEMANTIC_COLORS = {
    'default': 'Default',
    'accent': 'Accent',
    'good': 'Good',
    'warning': 'Warning',
    'attention': 'Attention',
    'light': 'Light',
    'dark': 'Dark',
}

# 品牌色調（用於 Container style）
CONTAINER_STYLES = {
    'default': 'default',
    'emphasis': 'emphasis',
    'accent': 'accent',
    'good': 'good',
    'attention': 'attention',
    'warning': 'warning',
}
