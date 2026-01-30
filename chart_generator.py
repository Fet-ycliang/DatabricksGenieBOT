"""Chart generation module for creating visual charts from data - using Plotly."""

import io
import base64
from asyncio.log import logger
from pathlib import Path
import tempfile

# 導入 Plotly（高品質圖表生成）
import plotly.graph_objects as go


def generate_chart_image(chart_info: dict) -> str:
    """用 Plotly 生成高品質圖表並返回 base64 編碼的 PNG
    
    使用 Plotly 生成美化的圖表，通過 kaleido 轉換為 PNG
    
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
        
        # 建立 Plotly 圖表
        fig = None
        
        if chart_type == 'pie':
            # 圓餅圖
            fig = go.Figure(data=[
                go.Pie(
                    labels=categories,
                    values=values,
                    marker=dict(line=dict(color='white', width=2)),
                    textposition='auto',
                    hoverinfo='label+value+percent'
                )
            ])
        
        elif chart_type == 'line':
            # 折線圖
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=categories,
                y=values,
                mode='lines+markers',
                name=value_col,
                line=dict(color='#2E86AB', width=3),
                marker=dict(size=10, color='#2E86AB'),
                fill='tozeroy',
                fillcolor='rgba(46, 134, 171, 0.2)',
                hovertemplate='<b>%{x}</b><br>' + value_col + ': %{y:,.0f}<extra></extra>'
            ))
        
        else:  # bar（預設長條圖）
            # 長條圖
            fig = go.Figure()
            fig.add_trace(go.Bar(
                x=categories,
                y=values,
                name=value_col,
                marker=dict(
                    color=values,
                    colorscale='Viridis',
                    line=dict(color='white', width=1)
                ),
                hovertemplate='<b>%{x}</b><br>' + value_col + ': %{y:,.0f}<extra></extra>'
            ))
        
        # 統一的布局設定
        fig.update_layout(
            title=dict(text=f'{category_col} vs {value_col}', font=dict(size=18, color='#333')),
            xaxis_title=category_col if chart_type != 'pie' else None,
            yaxis_title=value_col if chart_type != 'pie' else None,
            hovermode='closest',
            plot_bgcolor='rgba(240, 240, 240, 0.5)',
            paper_bgcolor='white',
            font=dict(family='Arial, sans-serif', size=12, color='#333'),
            width=1000,
            height=600,
            margin=dict(l=80, r=80, t=100, b=80),
            showlegend=chart_type != 'pie'
        )
        
        if chart_type != 'pie':
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', zeroline=False)
            fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor='lightgray', zeroline=False)
        
        # 轉換為 PNG 並編碼為 base64
        png_bytes = fig.to_image(format='png', width=1000, height=600)
        image_base64 = base64.b64encode(png_bytes).decode('utf-8')
        
        logger.info(f"[圖表生成] 成功生成 {chart_type} 圖表，大小: {len(png_bytes)} bytes")
        return image_base64
        
    except Exception as e:
        logger.error(f"生成 Plotly 圖表時發生錯誤: {e}", exc_info=True)
        raise


def create_chart_card_with_image(chart_info: dict) -> dict:
    """創建包含 Plotly 高品質圖表的 Adaptive Card"""
    if not chart_info.get('suitable'):
        return None
    
    chart_type = chart_info['chart_type']
    chart_data = chart_info['data_for_chart']
    category_col = chart_info['category_column']
    value_col = chart_info['value_column']
    
    chart_icons = {'bar': '���', 'pie': '���', 'line': '���'}
    chart_icon = chart_icons.get(chart_type, '���')
    
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
                                {"type": "TextBlock", "text": "��� 數據視覺化", "weight": "Bolder", "size": "Medium", "color": "Accent"},
                                {"type": "TextBlock", "text": f"{category_col} vs {value_col}", "isSubtle": True, "spacing": "None"}
                            ]
                        }
                    ]
                }]
            },
            {"type": "Image", "url": image_url, "size": "Stretch", "spacing": "Medium"},
            {"type": "TextBlock", "text": f"✨ 共 {len(chart_data)} 筆數據 | Plotly 生成", "wrap": True, "isSubtle": True, "size": "Small", "horizontalAlignment": "Center", "spacing": "Small"}
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
