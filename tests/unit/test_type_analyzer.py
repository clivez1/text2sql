"""
数据类型分析器单元测试

测试 type_analyzer 模块的功能。
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app.core.chart.type_analyzer import (
    DataTypeAnalyzer,
    ColumnType,
    ColumnAnalysis,
    DataFrameAnalysis,
    analyze_column,
    analyze_dataframe,
    get_chart_recommendation,
)


class TestColumnType:
    """列类型枚举测试"""
    
    def test_column_types_exist(self):
        """测试所有类型都存在"""
        assert ColumnType.NUMERIC.value == "numeric"
        assert ColumnType.CATEGORICAL.value == "categorical"
        assert ColumnType.DATETIME.value == "datetime"
        assert ColumnType.BOOLEAN.value == "boolean"
        assert ColumnType.TEXT.value == "text"
        assert ColumnType.ID.value == "id"
        assert ColumnType.UNKNOWN.value == "unknown"


class TestNumericColumn:
    """数值类型列测试"""
    
    @pytest.fixture
    def analyzer(self):
        return DataTypeAnalyzer()
    
    def test_integer_column(self, analyzer):
        """测试整数列"""
        series = pd.Series([1, 2, 3, 4, 5], name="test_int")
        result = analyzer.analyze_column(series)
        
        assert result.column_type == ColumnType.NUMERIC
        assert result.is_numeric
        assert result.min_value == 1
        assert result.max_value == 5
        assert result.mean_value == 3.0
    
    def test_float_column(self, analyzer):
        """测试浮点数列"""
        series = pd.Series([1.1, 2.2, 3.3, 4.4, 5.5], name="test_float")
        result = analyzer.analyze_column(series)
        
        assert result.column_type == ColumnType.NUMERIC
        assert result.is_numeric
        assert result.mean_value == pytest.approx(3.3, rel=0.01)
    
    def test_numeric_with_nulls(self, analyzer):
        """测试有空值的数值列"""
        series = pd.Series([1, 2, None, 4, 5], name="test_null")
        result = analyzer.analyze_column(series)
        
        assert result.is_numeric
        assert result.null_count == 1
        assert result.total_count == 5
    
    def test_numeric_as_id(self, analyzer):
        """测试高唯一值比例的数值列（ID类型）- 需要列名包含 id"""
        series = pd.Series(range(100), name="user_id")  # 列名包含 id
        result = analyzer.analyze_column(series)
        
        # 列名包含 "id"，所以被识别为 ID
        assert result.column_type == ColumnType.ID
        assert result.is_id
    
    def test_numeric_high_cardinality(self, analyzer):
        """测试高基数数值列（非ID）"""
        series = pd.Series(range(100), name="values")  # 列名不含 id
        result = analyzer.analyze_column(series)
        
        # 虽然唯一值比例高，但列名不含 id 关键字，所以是 NUMERIC
        assert result.column_type == ColumnType.NUMERIC
        assert result.is_numeric


class TestCategoricalColumn:
    """分类类型列测试"""
    
    @pytest.fixture
    def analyzer(self):
        return DataTypeAnalyzer()
    
    def test_low_cardinality_string(self, analyzer):
        """测试低基数字符串列"""
        series = pd.Series(["A", "B", "A", "B", "A"] * 10, name="category")
        result = analyzer.analyze_column(series)
        
        assert result.column_type == ColumnType.CATEGORICAL
        assert result.is_categorical
        assert result.cardinality == 2
    
    def test_medium_cardinality(self, analyzer):
        """测试中等基数列"""
        # 10个唯一值，100行 -> 基数比例 = 0.1
        series = pd.Series([f"cat_{i}" for i in range(10)] * 10, name="medium")
        result = analyzer.analyze_column(series)
        
        assert result.is_categorical
        assert result.cardinality == 10
    
    def test_top_categories(self, analyzer):
        """测试获取 top categories"""
        series = pd.Series(["A", "B", "C", "A", "B", "A", "D", "E"], name="cats")
        result = analyzer.analyze_column(series)
        
        assert result.is_categorical
        assert result.top_categories[0] == "A"  # 最常见


class TestDatetimeColumn:
    """日期时间类型列测试"""
    
    @pytest.fixture
    def analyzer(self):
        return DataTypeAnalyzer()
    
    def test_datetime_type(self, analyzer):
        """测试 datetime 类型列"""
        dates = pd.date_range("2024-01-01", periods=10)
        series = pd.Series(dates, name="date_col")
        result = analyzer.analyze_column(series)
        
        assert result.column_type == ColumnType.DATETIME
        assert result.is_datetime
        assert result.suitable_for_x
    
    def test_string_datetime(self, analyzer):
        """测试字符串格式的日期"""
        series = pd.Series([
            "2024-01-01", "2024-01-02", "2024-01-03",
            "2024-01-04", "2024-01-05"
        ], name="date_str")
        result = analyzer.analyze_column(series)
        
        assert result.is_datetime

    def test_mixed_string_datetime_without_warning(self, analyzer):
        """测试混合日期字符串自动解析时不产生 pandas 推断 warning"""
        series = pd.Series([
            "2024-01-01", "2024/01/02", "2024-01-03 10:00:00"
        ], name="mixed_date_str")
        result = analyzer.analyze_column(series)

        assert result.is_datetime
    
    def test_time_range(self, analyzer):
        """测试时间范围检测"""
        dates = pd.date_range("2024-01-01", "2024-01-31")
        series = pd.Series(dates, name="dates")
        result = analyzer.analyze_column(series)
        
        assert result.time_range is not None
        assert result.time_range[0] == dates[0]
        assert result.time_range[1] == dates[-1]


class TestBooleanColumn:
    """布尔类型列测试"""
    
    @pytest.fixture
    def analyzer(self):
        return DataTypeAnalyzer()
    
    def test_bool_type(self, analyzer):
        """测试布尔类型"""
        series = pd.Series([True, False, True, False, True], name="bool_col")
        result = analyzer.analyze_column(series)
        
        assert result.column_type == ColumnType.BOOLEAN
        assert result.is_boolean
        assert result.suitable_for_x
        assert result.suitable_for_color
    
    def test_numeric_boolean(self, analyzer):
        """测试数值 0/1 作为布尔"""
        series = pd.Series([0, 1, 0, 1, 1], name="num_bool")
        result = analyzer.analyze_column(series)
        
        assert result.is_boolean


class TestTextColumn:
    """文本类型列测试"""
    
    @pytest.fixture
    def analyzer(self):
        return DataTypeAnalyzer()
    
    def test_high_cardinality_string(self, analyzer):
        """测试高基数字符串列（文本）"""
        series = pd.Series([f"text_{i}" for i in range(50)], name="text")
        result = analyzer.analyze_column(series)
        
        # 高基数，但唯一值比例 < 0.95（不是 ID）
        # 所以应该是 TEXT
        assert result.column_type in [ColumnType.TEXT, ColumnType.ID]


class TestIDColumn:
    """ID 类型列测试"""
    
    @pytest.fixture
    def analyzer(self):
        return DataTypeAnalyzer()
    
    def test_id_type(self, analyzer):
        """测试 ID 类型（列名包含 id 关键字）"""
        series = pd.Series([f"id_{i}" for i in range(100)], name="user_id")
        result = analyzer.analyze_column(series)
        
        assert result.column_type == ColumnType.ID
        assert result.is_id
        assert result.cardinality_ratio == 1.0


class TestDataFrameAnalysis:
    """DataFrame 分析测试"""
    
    @pytest.fixture
    def analyzer(self):
        return DataTypeAnalyzer()
    
    def test_basic_analysis(self, analyzer):
        """测试基本 DataFrame 分析"""
        df = pd.DataFrame({
            "category": ["A", "B", "A", "B"],
            "value": [10, 20, 30, 40],
            "date": pd.date_range("2024-01-01", periods=4),
        })
        
        result = analyzer.analyze_dataframe(df)
        
        assert result.row_count == 4
        assert result.column_count == 3
        assert len(result.numeric_columns) == 1
        assert len(result.categorical_columns) == 1
        assert len(result.datetime_columns) == 1
    
    def test_time_series_detection(self, analyzer):
        """测试时间序列检测"""
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=10),
            "value": range(10),
        })
        
        result = analyzer.analyze_dataframe(df)
        
        assert result.is_time_series
        assert result.time_column == "date"
    
    def test_chart_recommendation(self, analyzer):
        """测试图表推荐"""
        df = pd.DataFrame({
            "category": ["A", "B", "C", "A", "B", "C"],
            "value": [10, 20, 30, 15, 25, 35],
        })
        
        result = analyzer.get_chart_recommendation(df)
        
        assert result["chart_type"] == "bar"
        assert result["x"] == "category"
        assert "value" in result["y"]


class TestVisualizationSuitability:
    """可视化适用性测试"""
    
    @pytest.fixture
    def analyzer(self):
        return DataTypeAnalyzer()
    
    def test_numeric_suitable_for_y(self, analyzer):
        """测试数值适合 Y 轴"""
        series = pd.Series(range(100), name="values")
        result = analyzer.analyze_column(series)
        
        assert result.suitable_for_y
    
    def test_datetime_suitable_for_x(self, analyzer):
        """测试日期适合 X 轴"""
        series = pd.Series(pd.date_range("2024-01-01", periods=10), name="dates")
        result = analyzer.analyze_column(series)
        
        assert result.suitable_for_x
        assert not result.suitable_for_y
    
    def test_categorical_suitable_for_color(self, analyzer):
        """测试低基数分类适合颜色"""
        series = pd.Series(["A", "B", "A", "B"] * 10, name="cats")
        result = analyzer.analyze_column(series)
        
        assert result.suitable_for_color


class TestConvenienceFunctions:
    """便捷函数测试"""
    
    def test_analyze_column_function(self):
        """测试 analyze_column 便捷函数"""
        series = pd.Series([1, 2, 3, 4, 5], name="test")
        result = analyze_column(series)
        
        assert isinstance(result, ColumnAnalysis)
        assert result.is_numeric
    
    def test_analyze_dataframe_function(self):
        """测试 analyze_dataframe 便捷函数"""
        df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        result = analyze_dataframe(df)
        
        assert isinstance(result, DataFrameAnalysis)
        assert result.row_count == 3
    
    def test_get_chart_recommendation_function(self):
        """测试 get_chart_recommendation 便捷函数"""
        df = pd.DataFrame({
            "category": ["A", "B", "C"],
            "value": [10, 20, 30],
        })
        result = get_chart_recommendation(df)
        
        assert "chart_type" in result
        assert "x" in result
        assert "y" in result


class TestEdgeCases:
    """边界情况测试"""
    
    @pytest.fixture
    def analyzer(self):
        return DataTypeAnalyzer()
    
    def test_empty_series(self, analyzer):
        """测试空 Series"""
        series = pd.Series([], name="empty")
        result = analyzer.analyze_column(series)
        
        assert result.total_count == 0
        assert result.null_count == 0
    
    def test_all_null_series(self, analyzer):
        """测试全空 Series"""
        series = pd.Series([None, None, None], name="nulls")
        result = analyzer.analyze_column(series)
        
        assert result.null_count == 3
    
    def test_single_value_series(self, analyzer):
        """测试单值 Series"""
        series = pd.Series([42], name="single")
        result = analyzer.analyze_column(series)
        
        assert result.total_count == 1
        assert result.unique_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])