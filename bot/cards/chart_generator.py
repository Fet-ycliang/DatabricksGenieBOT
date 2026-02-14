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
        
        # 根據圖表類型繪製
        if chart_type == 'pie':
            # 圓餅圖 - 使用較大的圖表和邊距
            fig, ax = plt.subplots(figsize=(14, 9), dpi=100)
            colors = sns.color_palette("Set2", len(categories))
            
            # 繪製圓餅圖，將標籤放在圖表外側
            wedges, texts, autotexts = ax.pie(
                values, 
                labels=None,  # 先不用 pie 內置標籤
                autopct='%1.1f%%', 
                colors=colors, 
                startangle=90,
                textprops={'fontsize': 13, 'fontweight': 'bold'},
                wedgeprops={'edgecolor': 'white', 'linewidth': 2},
                pctdistance=0.85
            )
            
            # 手動添加標籤到圖例
            ax.legend(categories, loc='center left', bbox_to_anchor=(1, 0, 0.5, 1), fontsize=12)
            ax.set_title(f'{category_col} vs {value_col}', fontsize=14, fontweight='bold', pad=20)
            
        elif chart_type == 'line':
            fig = plt.figure(figsize=(14, 8), dpi=100)
            # 折線圖 - 專業藍色
            plt.plot(categories, values, marker='o', linewidth=3, markersize=10, color='#1f77b4', markerfacecolor='#1f77b4', markeredgecolor='white', markeredgewidth=2)
            plt.fill_between(range(len(categories)), values, alpha=0.25, color='#1f77b4')
            # 在數據點上標上數值
            for i, (cat, val) in enumerate(zip(categories, values)):
                plt.text(i, val, f'{val:,.0f}', ha='center', va='bottom', fontsize=12, fontweight='bold', color='#1f77b4')
            plt.xlabel(category_col, fontsize=14, fontweight='bold', color='#333333')
            plt.ylabel(value_col, fontsize=14, fontweight='bold', color='#333333')
            plt.title(f'{category_col} vs {value_col}', fontsize=14, fontweight='bold', pad=20)
            plt.xticks(rotation=45, ha='right', fontsize=11, color='#555555')
            plt.yticks(fontsize=11, color='#555555')
            plt.grid(True, alpha=0.2, linestyle='--', color='#cccccc')
        
        else:  # bar（預設長條圖）
            fig = plt.figure(figsize=(14, 8), dpi=100)
            # 長條圖 - 專業漸層配色
            colors = sns.color_palette("husl", len(categories))
            ax = plt.gca()
            bars = ax.bar(range(len(categories)), values, color=colors, width=0.7, edgecolor='white', linewidth=1.5)
            
            # 在柱狀圖頂部標上數值
            for i, (cat, val) in enumerate(zip(categories, values)):
                ax.text(i, val, f'{val:,.0f}', ha='center', va='bottom', fontsize=12, fontweight='bold', color='#333333')
            
            ax.set_xticks(range(len(categories)))
            ax.set_xticklabels(categories, rotation=45, ha='right', fontsize=11, color='#555555')
            ax.set_yticks(fontsize=11, color='#555555')
            plt.xlabel(category_col, fontsize=14, fontweight='bold', color='#333333')
            plt.ylabel(value_col, fontsize=14, fontweight='bold', color='#333333')
            plt.title(f'{category_col} vs {value_col}', fontsize=14, fontweight='bold', pad=20)
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#cccccc')
            ax.spines['bottom'].set_color('#cccccc')
        
        # 調整布局以避免標籤被切掉
        plt.subplots_adjust(left=0.1, right=0.9, top=0.92, bottom=0.15)
        
        # 轉換為 PNG 並編碼為 base64
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight', pad_inches=0.5)
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
    """創建包含建議問題的 Adaptive Card 附件"""
    if not suggested_questions or len(suggested_questions) == 0:
        return None

    normalized_questions = []
    for item in suggested_questions:
        if isinstance(item, str):
            question = item.strip()
        elif isinstance(item, dict):
            question = (item.get("question") or item.get("text") or "").strip()
        else:
            question = str(item).strip()
        if question:
            normalized_questions.append(question)

    if not normalized_questions:
        return None

    actions = [
        {
            "type": "Action.Submit",
            "title": f"❓ {question[:35]}{'...' if len(question) > 35 else ''}",
            "data": {
                "action": "ask_suggested_question",
                "question": question
            }
        }
        for question in normalized_questions[:3]
    ]

    card_content = {
        "type": "AdaptiveCard",
        "version": "1.5",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "body": [
            {
                "type": "Container",
                "style": "emphasis",
                "items": [
                    {
                        "type": "ColumnSet",
                        "columns": [
                            {
                                "type": "Column",
                                "width": "auto",
                                "items": [{"type": "TextBlock", "text": "💡", "size": "Large"}],
                            },
                            {
                                "type": "Column",
                                "width": "stretch",
                                "items": [
                                    {
                                        "type": "TextBlock",
                                        "text": "建議問題",
                                        "weight": "Bolder",
                                        "size": "Medium",
                                        "color": "Accent",
                                    },
                                    {
                                        "type": "TextBlock",
                                        "text": "點擊下方按鈕繼續詢問",
                                        "isSubtle": True,
                                        "spacing": "None",
                                        "size": "Small",
                                    },
                                ],
                            },
                        ],
                    }
                ],
            }
        ],
        "actions": actions,
    }

    return {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": card_content,
    }
