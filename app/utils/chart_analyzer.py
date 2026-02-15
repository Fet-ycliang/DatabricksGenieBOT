"""
圖表分析工具模組

提供數據圖表適用性分析和圖表類型建議功能。
"""

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class ChartAnalyzer:
    """圖表分析器 - 分析數據是否適合繪製圖表並建議圖表類型"""

    @staticmethod
    def analyze_suitability(columns: dict, data: dict) -> dict:
        """分析數據是否適合繪製圖表並返回建議的圖表類型

        Args:
            columns: 欄位定義字典，包含 columns 列表
            data: 數據字典，包含 data_array 列表

        Returns:
            dict: {
                'suitable': bool,           # 是否適合繪圖
                'chart_type': str,          # 圖表類型: 'bar', 'pie', 'line'
                'category_column': str,     # 類別欄位名稱
                'value_column': str,        # 數值欄位名稱
                'data_for_chart': list      # 格式化的圖表數據
            }

        Examples:
            >>> columns = {'columns': [
            ...     {'name': 'category', 'type_text': 'string'},
            ...     {'name': 'value', 'type_text': 'int'}
            ... ]}
            >>> data = {'data_array': [['A', 10], ['B', 20]]}
            >>> result = ChartAnalyzer.analyze_suitability(columns, data)
            >>> result['suitable']
            True
        """
        try:
            # 基本驗證
            if not columns or not data:
                logger.debug("圖表分析: 缺少 columns 或 data")
                return {'suitable': False}

            # 獲取列信息
            col_list = columns.get('columns', [])
            if len(col_list) < 2:
                logger.debug(f"圖表分析: 列數不足 ({len(col_list)} < 2)")
                return {'suitable': False}

            # 獲取數據行
            data_array = data.get('data_array', [])
            if not data_array or len(data_array) < 2:
                logger.debug(f"圖表分析: 數據行不足 ({len(data_array) if data_array else 0} < 2)")
                return {'suitable': False}

            # 限制圖表數據點的數量（超過50條時只取前50條）
            original_count = len(data_array)
            if len(data_array) > 50:
                data_array = data_array[:50]
                logger.debug(f"圖表分析: 數據行過多，從 {original_count} 截取至 50")

            # 分析列類型並識別類別列和數值列
            category_col, category_idx, value_col, value_idx = (
                ChartAnalyzer._identify_columns(col_list)
            )

            if not category_col or not value_col or category_idx is None or value_idx is None:
                logger.warning(
                    f"圖表分析失敗: 無法找到合適的類別列或數值列 "
                    f"(category={category_col}, value={value_col})"
                )
                return {'suitable': False}

            logger.debug(
                f"圖表分析: 識別結果 - 類別列: {category_col} (索引 {category_idx}), "
                f"數值列: {value_col} (索引 {value_idx})"
            )

            # 準備圖表數據
            chart_data, has_negative = ChartAnalyzer._prepare_chart_data(
                data_array, category_idx, value_idx
            )

            if len(chart_data) < 2:
                logger.debug(f"圖表分析: 有效數據點不足 ({len(chart_data)} < 2)")
                return {'suitable': False}

            # 決定圖表類型
            chart_type = ChartAnalyzer._determine_chart_type(
                category_col, chart_data, has_negative
            )

            logger.info(
                f"圖表分析成功: 類型={chart_type}, 類別={category_col}, "
                f"數值={value_col}, 數據點={len(chart_data)}"
            )

            return {
                'suitable': True,
                'chart_type': chart_type,
                'category_column': category_col,
                'value_column': value_col,
                'data_for_chart': chart_data
            }

        except Exception as e:
            logger.error(f"分析圖表適用性時發生錯誤: {e}", exc_info=True)
            return {'suitable': False}

    @staticmethod
    def _identify_columns(col_list: List[dict]) -> tuple:
        """識別類別列和數值列

        Args:
            col_list: 列定義列表

        Returns:
            tuple: (category_col, category_idx, value_col, value_idx)
        """
        category_col = None
        value_col = None
        category_idx = None
        value_idx = None

        # 記錄列信息用於調試
        logger.debug(f"分析圖表 - 列信息: {[col.get('name', '') for col in col_list]}")
        logger.debug(f"列類型信息: {[col.get('type_text', '') for col in col_list]}")
        logger.debug(f"列 type_name 信息: {[col.get('type_name', '') for col in col_list]}")

        # 第一輪：尋找字串列和數值列
        for idx, col in enumerate(col_list):
            col_name = col.get('name', '')
            col_type = col.get('type_text', '').lower()
            col_type_name = col.get('type_name', '').lower()

            logger.debug(
                f"  列 {idx}: {col_name} | type_text='{col_type}' | type_name='{col_type_name}'"
            )

            # 尋找類別列（字串類型）
            if not category_col and ChartAnalyzer._is_string_column(col_type, col_type_name):
                category_col = col_name
                category_idx = idx
                logger.debug(f"    ✓ 識別為類別列")

            # 尋找數值列
            if not value_col and ChartAnalyzer._is_numeric_column(col_type, col_type_name):
                value_col = col_name
                value_idx = idx
                logger.debug(f"    ✓ 識別為數值列")

        # 備用策略：如果沒找到數值列，選擇第一個非類別列
        if value_col is None and category_col is not None:
            logger.debug("未找到數值列，使用備用策略...")
            for idx, col in enumerate(col_list):
                if col.get('name', '') != category_col:
                    value_col = col.get('name', '')
                    value_idx = idx
                    logger.debug(f"  備用策略: 選擇列 {idx} ({value_col}) 作為數值列")
                    break

        return category_col, category_idx, value_col, value_idx

    @staticmethod
    def _is_string_column(col_type: str, col_type_name: str) -> bool:
        """判斷是否為字串類型列"""
        string_types = ['string', 'varchar', 'char', 'text']
        return any(t in col_type or t in col_type_name for t in string_types)

    @staticmethod
    def _is_numeric_column(col_type: str, col_type_name: str) -> bool:
        """判斷是否為數值類型列"""
        numeric_types = [
            'int', 'long', 'double', 'float', 'decimal',
            'bigint', 'numeric', 'number', 'money'
        ]
        return any(t in col_type or t in col_type_name for t in numeric_types)

    @staticmethod
    def _prepare_chart_data(
        data_array: List[list],
        category_idx: int,
        value_idx: int
    ) -> tuple:
        """準備圖表數據並檢查是否有負值

        Args:
            data_array: 原始數據陣列
            category_idx: 類別欄位索引
            value_idx: 數值欄位索引

        Returns:
            tuple: (chart_data, has_negative)
        """
        chart_data = []
        has_negative = False

        for row in data_array:
            if len(row) <= max(category_idx, value_idx):
                continue

            category = str(row[category_idx]) if row[category_idx] is not None else 'N/A'
            value = row[value_idx]

            # 跳過 None 值
            if value is None:
                continue

            try:
                value = float(value)
                if value < 0:
                    has_negative = True
                chart_data.append({'category': category, 'value': value})
            except (ValueError, TypeError):
                logger.debug(f"跳過無效數值: {value}")
                continue

        return chart_data, has_negative

    @staticmethod
    def _determine_chart_type(
        category_col: str,
        chart_data: List[dict],
        has_negative: bool
    ) -> str:
        """決定最適合的圖表類型

        Args:
            category_col: 類別欄位名稱
            chart_data: 圖表數據列表
            has_negative: 是否包含負值

        Returns:
            str: 'bar', 'pie', 或 'line'
        """
        # 默認使用長條圖
        chart_type = 'bar'

        # 如果類別看起來像時間序列，優先使用折線圖
        time_keywords = [
            'date', 'time', 'month', 'year', 'day', 'week',
            '日期', '時間', '月份', '年', '日', '週'
        ]
        if any(keyword in category_col.lower() for keyword in time_keywords):
            chart_type = 'line'
            logger.debug(f"圖表類型: 折線圖 (時間序列欄位: {category_col})")

        # 如果沒有負值且類別數量適中（2-8個），使用圓餅圖
        elif not has_negative and 2 <= len(chart_data) <= 8:
            chart_type = 'pie'
            logger.debug(f"圖表類型: 圓餅圖 (無負值, {len(chart_data)} 個類別)")

        else:
            logger.debug(
                f"圖表類型: 長條圖 (has_negative={has_negative}, "
                f"categories={len(chart_data)})"
            )

        return chart_type
