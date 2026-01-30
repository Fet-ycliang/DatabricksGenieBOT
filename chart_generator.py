"""Chart generation module for creating visual charts from data."""

import io
import base64
from asyncio.log import logger
from pathlib import Path
import tempfile

# 導入 Matplotlib 和 Seaborn（支援中文）
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import numpy as np

# 設定中文字體
matplotlib.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei', 'DejaVu Sans']
matplotlib.rcParams['axes.unicode_minus'] = False


def generate_chart_image(chart_info: dict) -> str:
    """用 Matplotlib + Seaborn 生成圖表並返回 base64 編碼的 PNG
    
    使用 Matplotlib 和 Seaborn 生成美化的圖表，支援中文
    
    Args:
        chart_info: 包含圖表信息的字典，包括:
            - chart_type: 圖表類型 ('bar', 'pie', 'line')
            - data_for_chart: 圖表數據列表
            - category_column: 類別欄位名稱
            - value_column: 數值欄位名稱
    
    Returns:
        base64 編碼的 PNG 圖片字符串
    """
    try:
        chart_type = chart_info['chart_type']
        chart_data = chart_info['data_for_chart']
        category_col = chart_info['category_column']
        value_col = chart_info['value_column']
        
        # 提取數據
        categories = [item['category'] for item in chart_data]
        values = [item['value'] for item in chart_data]
        
        # 設定樣式
        sns.set_style("whitegrid")
        plt.figure(figsize=(12, 7), dpi=100)
        
        # 根據圖表類型繪製
        if chart_type == 'pie':
            # 圓餅圖
            colors = sns.color_palette("husl", len(categories))
            plt.pie(values, labels=categories, autopct='%1.1f%%', colors=colors, startangle=90)
            plt.title(f'{category_col} vs {value_col}', fontsize=16, fontweight='bold', pad=20)
        
        elif chart_type == 'line':
            # 折線圖
            plt.plot(categories, values, marker='o', linewidth=2.5, markersize=8, color='#2E86AB')
            plt.fill_between(range(len(categories)), values, alpha=0.3, color='#2E86AB')
            # 在數據點上標上數值
            for i, (cat, val) in enumerate(zip(categories, values)):
                plt.text(i, val, f'{val:,.0f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
            plt.xlabel(category_col, fontsize=12, fontweight='bold')
            plt.ylabel(value_col, fontsize=12, fontweight='bold')
            plt.title(f'{category_col} vs {value_col}', fontsize=16, fontweight='bold', pad=20)
            plt.xticks(rotation=45, ha='right')
            plt.grid(True, alpha=0.3)
        
        else:  # bar（預設長條圖）
            # 長條圖
            colors = sns.color_palette("viridis", len(categories))
            ax = sns.barplot(x=categories, y=values, palette=colors, width=0.7)
            # 在柱狀圖頂部標上數值
            for i, (cat, val) in enumerate(zip(categories, values)):
                ax.text(i, val, f'{val:,.0f}', ha='center', va='bottom', fontsize=10, fontweight='bold')
            plt.xlabel(category_col, fontsize=12, fontweight='bold')
            plt.ylabel(value_col, fontsize=12, fontweight='bold')
            plt.title(f'{category_col} vs {value_col}', fontsize=16, fontweight='bold', pad=20)
            plt.xticks(rotation=45, ha='right')
        
        # 調整布局
        plt.tight_layout()
        
        # 轉換為 PNG 並編碼為 base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
        buffer.seek(0)
        png_bytes = buffer.getvalue()
        plt.close()
        
        image_base64 = base64.b64encode(png_bytes).decode('utf-8')
        
        logger.info(f"[圖表生成] 成功生成 {chart_type} 圖表，大小: {len(png_bytes)} bytes")
        return image_base64
        
    except Exception as e:
        logger.error(f"生成圖表時發生錯誤: {e}", exc_info=True)
        raise


def create_chart_card_with_image(chart_info: dict) -> dict:
    """創建包含 Plotly 高品質圖表的 Adaptive Card"""
    if not chart_info.get('suitable'):
        return None
    
    chart_type = chart_info['chart_type']
    chart_data = chart_info['data_for_chart']
    category_col = chart_info['category_column']
    value_col = chart_info['value_column']
    
    chart_icons = {'bar': '\U0001F4CA', 'pie': '\U0001F967', 'line': '\U0001F4C8'}
    chart_icon = chart_icons.get(chart_type, '\U0001F4CA')
    
    try:
        image_base64 = generate_chart_image(chart_info)
        image_url = f"data:image/png;base64,{image_base64}"
    except Exception as e:
        logger.error(f"生成圖表圖片時發生錯誤: {e}")
        return {
            "type": "AdaptiveCard",
            "version": "1.5",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "body": [
                {"type": "TextBlock", "text": "⚠️ 圖表生成失敗", "weight": "Bolder", "color": "Warning"},
                {"type": "TextBlock", "text": f"錯誤訊息: {str(e)[:100]}", "wrap": True, "isSubtle": True}
            ]
        }
    
    return {
        "type": "AdaptiveCard",
        "version": "1.5",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "body": [
            {
                "type": "Container",
                "style": "emphasis",
                "items": [{
                    "type": "ColumnSet",
                    "columns": [
                        {"type": "Column", "width": "auto", "items": [{"type": "TextBlock", "text": chart_icon, "size": "Large"}]},
                        {
                            "type": "Column",
                            "width": "stretch",
                            "items": [
                                {"type": "TextBlock", "text": "數據視覺化", "weight": "Bolder", "size": "Medium", "color": "Accent"},
                                {"type": "TextBlock", "text": f"{category_col} vs {value_col}", "isSubtle": True, "spacing": "None"}
                            ]
                        }
                    ]
                }]
            },
            {"type": "Image", "url": image_url, "size": "Stretch", "spacing": "Medium"},
            {"type": "TextBlock", "text": f"✨ 共 {len(chart_data)} 筆數據", "wrap": True, "isSubtle": True, "size": "Small", "horizontalAlignment": "Center", "spacing": "Small"}
        ]
    }


def create_suggested_questions_card(suggested_questions: list) -> dict:
    """創建包含建議問題的 Adaptive Card"""
    if not suggested_questions or len(suggested_questions) == 0:
        return None
    
    actions = [
        {
            "type": "Action.Submit",
            "title": f"❓ {question[:35]}{'...' if len(question) > 35 else ''}",
            "data": {"action": "ask_suggested_question", "question": question}
        }
        for question in suggested_questions[:3]
    ]
    
    return {
        "type": "AdaptiveCard",
        "version": "1.5",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "body": [
            {
                "type": "Container",
                "style": "emphasis",
                "items": [{
                    "type": "ColumnSet",
                    "columns": [
                        {"type": "Column", "width": "auto", "items": [{"type": "TextBlock", "text": "���", "size": "Large"}]},
                        {
                            "type": "Column",
                            "width": "stretch",
                            "items": [
                                {"type": "TextBlock", "text": "建議問題", "weight": "Bolder", "size": "Medium", "color": "Accent"},
                                {"type": "TextBlock", "text": "點擊下方按鈕繼續詢問", "isSubtle": True, "spacing": "None", "size": "Small"}
                            ]
                        }
                    ]
                }]
            }
        ],
        "actions": actions
    }
