"""Chart generation module for creating visual charts from data."""

import io
import base64
from asyncio.log import logger
from pathlib import Path
import tempfile

# 導入圖表生成庫 (Matplotlib + Seaborn)
import matplotlib
import matplotlib.pyplot as plt
import seaborn as sns

# 設定中文字體支持
matplotlib.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial']
matplotlib.rcParams['axes.unicode_minus'] = False


def generate_chart_image(chart_info: dict) -> str:
    """生成圖表圖片並返回 base64 編碼的字符串
    
    使用 Matplotlib + Seaborn 生成高品質圖表
    
    Args:
        chart_info: 包含圖表信息的字典，包括:
            - chart_type: 圖表類型 ('bar', 'pie', 'line')
            - data_for_chart: 圖表數據列表
            - category_column: 類別欄位名稱
            - value_column: 數值欄位名稱
    
    Returns:
        base64 編碼的 PNG 圖片字符串
    """
    chart_type = chart_info['chart_type']
    chart_data = chart_info['data_for_chart']
    category_col = chart_info['category_column']
    value_col = chart_info['value_column']
    
    # 提取數據
    categories = [item['category'] for item in chart_data]
    values = [item['value'] for item in chart_data]
    
    # 設定風格
    sns.set_style("whitegrid")
    sns.set_palette("husl")
    
    try:
        # 創建圖表
        fig, ax = plt.subplots(figsize=(10, 6), dpi=100)
        
        if chart_type == 'pie':
            # 圓餅圖
            colors = sns.color_palette("husl", len(categories))
            ax.pie(
                values,
                labels=categories,
                autopct='%1.1f%%',
                startangle=90,
                colors=colors,
                textprops={'fontsize': 11, 'color': '#333'}
            )
            ax.set_title(
                f'{category_col} vs {value_col}',
                fontsize=14,
                fontweight='bold',
                pad=20
            )
            
        elif chart_type == 'line':
            # 折線圖
            ax.plot(
                categories,
                values,
                marker='o',
                linewidth=2.5,
                markersize=8,
                color='#2E86AB',
                markerfacecolor='white',
                markeredgecolor='#2E86AB',
                markeredgewidth=2
            )
            
            # 添加數值標籤
            for i, (cat, val) in enumerate(zip(categories, values)):
                ax.text(i, val, f'{val:,.0f}', ha='center', va='bottom', fontsize=10)
            
            # 填充區域
            ax.fill_between(
                range(len(categories)),
                values,
                alpha=0.2,
                color='#2E86AB'
            )
            
            ax.set_xlabel(category_col, fontsize=12, fontweight='bold')
            ax.set_ylabel(value_col, fontsize=12, fontweight='bold')
            ax.set_title(
                f'{category_col} vs {value_col}',
                fontsize=14,
                fontweight='bold',
                pad=20
            )
            ax.grid(True, alpha=0.3)
            ax.set_xticklabels(categories, rotation=45, ha='right')
            
        else:  # bar
            # 長條圖
            colors = sns.color_palette("husl", len(categories))
            bars = ax.bar(categories, values, color=colors, edgecolor='black', linewidth=1)
            
            # 添加數值標籤
            for bar in bars:
                height = bar.get_height()
                ax.text(
                    bar.get_x() + bar.get_width()/2.,
                    height,
                    f'{height:,.0f}',
                    ha='center',
                    va='bottom',
                    fontsize=10
                )
            
            ax.set_xlabel(category_col, fontsize=12, fontweight='bold')
            ax.set_ylabel(value_col, fontsize=12, fontweight='bold')
            ax.set_title(
                f'{category_col} vs {value_col}',
                fontsize=14,
                fontweight='bold',
                pad=20
            )
            ax.grid(True, alpha=0.3, axis='y')
            ax.set_xticklabels(categories, rotation=45, ha='right')
        
        # 調整佈局
        plt.tight_layout()
        
        # 保存為 PNG 並轉換為 base64
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            tmp_path = tmp.name
        
        fig.savefig(tmp_path, format='png', dpi=100, bbox_inches='tight')
        plt.close(fig)
        
        # 讀取圖片並編碼為 base64
        with open(tmp_path, 'rb') as image_file:
            image_bytes = image_file.read()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # 清理臨時文件
        Path(tmp_path).unlink()
        
        return image_base64
        
    except Exception as e:
        logger.error(f"生成 Matplotlib 圖表時發生錯誤: {e}")
        plt.close('all')
        raise


def create_chart_card_with_image(chart_info: dict) -> dict:
    """創建包含實際圖表圖片的 Adaptive Card
    
    Args:
        chart_info: 圖表信息字典
    
    Returns:
        Adaptive Card JSON 結構
    """
    if not chart_info.get('suitable'):
        return None
    
    chart_type = chart_info['chart_type']
    chart_data = chart_info['data_for_chart']
    category_col = chart_info['category_column']
    value_col = chart_info['value_column']
    
    # 圖表類型對應的中文名稱和圖示
    chart_names = {
        'bar': ('長條圖', '📊'),
        'pie': ('圓餅圖', '🥧'),
        'line': ('折線圖', '📈')
    }
    chart_name, chart_icon = chart_names.get(chart_type, ('圖表', '📊'))
    
    # 生成圖表圖片
    try:
        image_base64 = generate_chart_image(chart_info)
        image_url = f"data:image/png;base64,{image_base64}"
    except Exception as e:
        logger.error(f"生成圖表圖片時發生錯誤: {e}")
        # 如果生成失敗，返回錯誤訊息卡片
        return {
            "type": "AdaptiveCard",
            "version": "1.5",
            "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
            "body": [
                {
                    "type": "TextBlock",
                    "text": "⚠️ 圖表生成失敗",
                    "weight": "Bolder",
                    "color": "Warning"
                },
                {
                    "type": "TextBlock",
                    "text": f"錯誤訊息: {str(e)}",
                    "wrap": True,
                    "isSubtle": True
                }
            ]
        }
    
    card = {
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
                                "items": [
                                    {
                                        "type": "TextBlock",
                                        "text": chart_icon,
                                        "size": "Large"
                                    }
                                ]
                            },
                            {
                                "type": "Column",
                                "width": "stretch",
                                "items": [
                                    {
                                        "type": "TextBlock",
                                        "text": f"數據視覺化 - {chart_name}",
                                        "weight": "Bolder",
                                        "size": "Medium",
                                        "color": "Accent"
                                    },
                                    {
                                        "type": "TextBlock",
                                        "text": f"{category_col} vs {value_col}",
                                        "isSubtle": True,
                                        "spacing": "None"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            },
            {
                "type": "Image",
                "url": image_url,
                "size": "Stretch",
                "spacing": "Medium"
            },
            {
                "type": "TextBlock",
                "text": f"📊 共 {len(chart_data)} 筆數據 | {chart_name}",
                "wrap": True,
                "isSubtle": True,
                "size": "Small",
                "horizontalAlignment": "Center",
                "spacing": "Small"
            }
        ]
    }
    
    return card


def create_suggested_questions_card(suggested_questions: list) -> dict:
    """創建包含建議問題的 Adaptive Card
    
    用户可以點擊按鈕來選擇建議問題進行查詢
    
    Args:
        suggested_questions: 建議問題列表
    
    Returns:
        Adaptive Card JSON 結構，包含可點擊的建議問題按鈕
    """
    if not suggested_questions or len(suggested_questions) == 0:
        return None
    
    # 構建按鈕（最多 3 個）
    actions = [
        {
            "type": "Action.Submit",
            "title": f"❓ {question[:35]}{'...' if len(question) > 35 else ''}",
            "data": {
                "action": "ask_suggested_question",
                "question": question
            }
        }
        for question in suggested_questions[:3]
    ]
    
    card = {
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
                                "items": [
                                    {
                                        "type": "TextBlock",
                                        "text": "💡",
                                        "size": "Large"
                                    }
                                ]
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
                                        "color": "Accent"
                                    },
                                    {
                                        "type": "TextBlock",
                                        "text": "點擊下方按鈕繼續詢問",
                                        "isSubtle": True,
                                        "spacing": "None",
                                        "size": "Small"
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ],
        "actions": actions
    }
    
    return card