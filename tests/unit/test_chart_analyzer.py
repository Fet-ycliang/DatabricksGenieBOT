"""測試 ChartAnalyzer 圖表分析功能"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from app.utils.chart_analyzer import ChartAnalyzer


def test_chart_analyzer_basic():
    """測試基本的圖表分析功能"""
    print("Testing ChartAnalyzer basic functionality...")

    # 測試數據：類別 + 數值
    columns = {
        'columns': [
            {'name': 'product', 'type_text': 'string'},
            {'name': 'sales', 'type_text': 'int'}
        ]
    }
    data = {
        'data_array': [
            ['Product A', 100],
            ['Product B', 200],
            ['Product C', 150]
        ]
    }

    result = ChartAnalyzer.analyze_suitability(columns, data)

    assert result['suitable'] == True, "Should be suitable for chart"
    # 3 categories, no negatives -> should be pie chart
    assert result['chart_type'] == 'pie', "Should recommend pie chart (3 categories, no negatives)"
    assert result['category_column'] == 'product'
    assert result['value_column'] == 'sales'
    assert len(result['data_for_chart']) == 3

    print("  PASS: Basic chart analysis")


def test_chart_analyzer_pie_chart():
    """測試圓餅圖識別"""
    print("Testing pie chart detection...")

    columns = {
        'columns': [
            {'name': 'region', 'type_text': 'string'},
            {'name': 'percentage', 'type_text': 'double'}
        ]
    }
    data = {
        'data_array': [
            ['North', 25.0],
            ['South', 30.0],
            ['East', 20.0],
            ['West', 25.0]
        ]
    }

    result = ChartAnalyzer.analyze_suitability(columns, data)

    assert result['suitable'] == True
    assert result['chart_type'] == 'pie', "Should recommend pie chart (4 categories, no negatives)"

    print("  PASS: Pie chart detection")


def test_chart_analyzer_line_chart():
    """測試折線圖識別（時間序列）"""
    print("Testing line chart detection for time series...")

    columns = {
        'columns': [
            {'name': 'date', 'type_text': 'string'},
            {'name': 'revenue', 'type_text': 'decimal'}
        ]
    }
    data = {
        'data_array': [
            ['2024-01', 1000],
            ['2024-02', 1200],
            ['2024-03', 1100]
        ]
    }

    result = ChartAnalyzer.analyze_suitability(columns, data)

    assert result['suitable'] == True
    assert result['chart_type'] == 'line', "Should recommend line chart for date column"

    print("  PASS: Line chart detection")


def test_chart_analyzer_insufficient_data():
    """測試數據不足的情況"""
    print("Testing insufficient data...")

    # 只有一筆數據
    columns = {
        'columns': [
            {'name': 'category', 'type_text': 'string'},
            {'name': 'value', 'type_text': 'int'}
        ]
    }
    data = {
        'data_array': [['A', 100]]
    }

    result = ChartAnalyzer.analyze_suitability(columns, data)

    assert result['suitable'] == False, "Should not be suitable (only 1 data point)"

    print("  PASS: Insufficient data handling")


def test_chart_analyzer_missing_columns():
    """測試缺少必要欄位的情況"""
    print("Testing missing columns...")

    # 只有一個欄位
    columns = {
        'columns': [
            {'name': 'category', 'type_text': 'string'}
        ]
    }
    data = {
        'data_array': [['A'], ['B']]
    }

    result = ChartAnalyzer.analyze_suitability(columns, data)

    assert result['suitable'] == False, "Should not be suitable (only 1 column)"

    print("  PASS: Missing columns handling")


def test_chart_analyzer_type_name_fallback():
    """測試使用 type_name 作為備用類型識別"""
    print("Testing type_name fallback...")

    columns = {
        'columns': [
            {'name': 'item', 'type_text': '', 'type_name': 'STRING'},
            {'name': 'count', 'type_text': '', 'type_name': 'BIGINT'}
        ]
    }
    data = {
        'data_array': [
            ['Item1', 50],
            ['Item2', 75]
        ]
    }

    result = ChartAnalyzer.analyze_suitability(columns, data)

    assert result['suitable'] == True, "Should work with type_name"
    assert result['category_column'] == 'item'
    assert result['value_column'] == 'count'

    print("  PASS: type_name fallback")


def test_chart_analyzer_with_nulls():
    """測試包含 NULL 值的數據"""
    print("Testing data with NULL values...")

    columns = {
        'columns': [
            {'name': 'name', 'type_text': 'string'},
            {'name': 'amount', 'type_text': 'int'}
        ]
    }
    data = {
        'data_array': [
            ['A', 100],
            ['B', None],  # NULL value
            ['C', 150],
            ['D', 200]
        ]
    }

    result = ChartAnalyzer.analyze_suitability(columns, data)

    assert result['suitable'] == True
    assert len(result['data_for_chart']) == 3, "Should skip NULL values"

    print("  PASS: NULL value handling")


def test_chart_analyzer_negative_values():
    """測試包含負值的數據（不應使用圓餅圖）"""
    print("Testing negative values...")

    columns = {
        'columns': [
            {'name': 'account', 'type_text': 'string'},
            {'name': 'balance', 'type_text': 'double'}
        ]
    }
    data = {
        'data_array': [
            ['Account1', 1000],
            ['Account2', -500],  # Negative value
            ['Account3', 750]
        ]
    }

    result = ChartAnalyzer.analyze_suitability(columns, data)

    assert result['suitable'] == True
    assert result['chart_type'] == 'bar', "Should use bar chart (has negatives)"

    print("  PASS: Negative value handling")


def run_all_tests():
    """執行所有測試"""
    print("="*60)
    print("ChartAnalyzer Unit Tests")
    print("="*60)
    print()

    tests = [
        test_chart_analyzer_basic,
        test_chart_analyzer_pie_chart,
        test_chart_analyzer_line_chart,
        test_chart_analyzer_insufficient_data,
        test_chart_analyzer_missing_columns,
        test_chart_analyzer_type_name_fallback,
        test_chart_analyzer_with_nulls,
        test_chart_analyzer_negative_values,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR: {e}")
            failed += 1

    print()
    print("="*60)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*60)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
