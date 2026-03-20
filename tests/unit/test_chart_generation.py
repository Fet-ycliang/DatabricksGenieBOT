"""測試圖表生成功能"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from bot.cards.chart_generator import generate_chart_image, create_chart_card_with_image

# 測試數據 - 長條圖
test_bar_data = {
    'suitable': True,
    'chart_type': 'bar',
    'category_column': '產品',
    'value_column': '銷售額',
    'data_for_chart': [
        {'category': '產品A', 'value': 1000},
        {'category': '產品B', 'value': 1500},
        {'category': '產品C', 'value': 800},
        {'category': '產品D', 'value': 1200},
    ]
}

# 測試數據 - 圓餅圖
test_pie_data = {
    'suitable': True,
    'chart_type': 'pie',
    'category_column': '地區',
    'value_column': '佔比',
    'data_for_chart': [
        {'category': '北部', 'value': 35},
        {'category': '中部', 'value': 25},
        {'category': '南部', 'value': 30},
        {'category': '東部', 'value': 10},
    ]
}

# 測試數據 - 折線圖
test_line_data = {
    'suitable': True,
    'chart_type': 'line',
    'category_column': '月份',
    'value_column': '營收',
    'data_for_chart': [
        {'category': '1月', 'value': 1000},
        {'category': '2月', 'value': 1200},
        {'category': '3月', 'value': 1100},
        {'category': '4月', 'value': 1400},
        {'category': '5月', 'value': 1600},
    ]
}

def test_chart_generation():
    """測試圖表生成"""
    print("🧪 測試圖表生成功能\n")
    
    # 測試長條圖
    print("1️⃣ 測試長條圖...")
    try:
        card = create_chart_card_with_image(test_bar_data)
        if card and 'body' in card:
            print("✅ 長條圖生成成功")
            print(f"   卡片包含 {len(card['body'])} 個元素")
        else:
            print("❌ 長條圖生成失敗")
    except Exception as e:
        print(f"❌ 長條圖生成錯誤: {e}")
    
    # 測試圓餅圖
    print("\n2️⃣ 測試圓餅圖...")
    try:
        card = create_chart_card_with_image(test_pie_data)
        if card and 'body' in card:
            print("✅ 圓餅圖生成成功")
            print(f"   卡片包含 {len(card['body'])} 個元素")
        else:
            print("❌ 圓餅圖生成失敗")
    except Exception as e:
        print(f"❌ 圓餅圖生成錯誤: {e}")
    
    # 測試折線圖
    print("\n3️⃣ 測試折線圖...")
    try:
        card = create_chart_card_with_image(test_line_data)
        if card and 'body' in card:
            print("✅ 折線圖生成成功")
            print(f"   卡片包含 {len(card['body'])} 個元素")
            
            # 檢查是否包含圖片
            has_image = any(item.get('type') == 'Image' for item in card['body'])
            if has_image:
                print("✅ 卡片包含圖片元素")
            else:
                print("⚠️  卡片不包含圖片元素")
        else:
            print("❌ 折線圖生成失敗")
    except Exception as e:
        print(f"❌ 折線圖生成錯誤: {e}")
    
    print("\n" + "="*50)
    print("✅ 測試完成！")
    print("="*50)

if __name__ == "__main__":
    test_chart_generation()
