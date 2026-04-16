"""
图表推荐器单元测试

测试 recommender 模块的功能。
"""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from app.core.chart.recommender import (
    ChartRecommender,
    ChartType,
    ChartRecommendation,
    recommend_chart,
    get_chart_type,
)
from app.core.chart.type_analyzer import DataTypeAnalyzer


class TestChartType:
    """图表类型枚举测试"""
    
    def test_chart_types_exist(self):
        """测试所有图表类型都存在"""
        assert ChartType.BAR.value == "bar"
        assert ChartType.LINE.value == "line"
        assert ChartType.PIE.value == "pie"
        assert ChartType.SCATTER.value == "scatter"
        assert ChartType.TABLE.value == "table"


class TestChartRecommendation:
    """推荐结果测试"""
    
    def test_to_dict(self):
        """测试转换为字典"""
        rec = ChartRecommendation(
            chart_type=ChartType.BAR,
            x_column="category",
            y_column="value",
            confidence=0.9,
            reason="test",
        )
        
        d = rec.to_dict()
        
        assert d["chart_type"] == "bar"
        assert d["x_column"] == "category"
        assert d["y_column"] == "value"
        assert d["confidence"] == 0.9


class TestBarChartRecommendation:
    """柱状图推荐测试"""
    
    @pytest.fixture
    def recommender(self):
        return ChartRecommender()
    
    def test_categorical_and_numeric(self, recommender):
        """测试分类 + 数值 → 柱状图"""
        df = pd.DataFrame({
            "category": ["A", "B", "C", "A", "B", "C"],
            "value": [10, 20, 30, 15, 25, 35],
        })
        
        result = recommender.recommend(df)
        
        assert result.chart_type == ChartType.BAR
        assert result.x_column == "category"
        assert result.y_column == "value"
        assert result.confidence >= 0.8
    
    def test_boolean_and_numeric(self, recommender):
        """测试布尔 + 数值 → 柱状图"""
        df = pd.DataFrame({
            "is_active": [True, False, True, False],
            "score": [85, 60, 90, 55],
        })
        
        result = recommender.recommend(df)
        
        assert result.chart_type == ChartType.BAR
        assert result.x_column == "is_active"
    
    def test_low_cardinality_numeric(self, recommender):
        """测试低基数数值作为分类 - 实际上数值列会优先作为 Y 轴"""
        df = pd.DataFrame({
            "rating": [1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
            "count": [10, 20, 30, 40, 50, 15, 25, 35, 45, 55],
        })
        
        result = recommender.recommend(df)
        
        # 两个都是数值列，优先散点图
        assert result.chart_type in [ChartType.BAR, ChartType.SCATTER]


class TestLineChartRecommendation:
    """折线图推荐测试"""
    
    @pytest.fixture
    def recommender(self):
        return ChartRecommender()
    
    def test_datetime_and_numeric(self, recommender):
        """测试日期 + 数值 → 折线图"""
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=10),
            "sales": [100, 120, 115, 130, 125, 140, 135, 150, 145, 160],
        })
        
        result = recommender.recommend(df)
        
        assert result.chart_type == ChartType.LINE
        assert result.x_column == "date"
        assert result.y_column == "sales"
        assert result.confidence >= 0.85
    
    def test_multiple_numeric_with_date(self, recommender):
        """测试日期 + 多个数值"""
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=10),
            "sales": range(10),
            "costs": range(10, 20),
        })
        
        result = recommender.recommend(df)
        
        assert result.chart_type == ChartType.LINE
        assert len(result.y_columns) == 2


class TestPieChartRecommendation:
    """饼图推荐测试"""
    
    @pytest.fixture
    def recommender(self):
        return ChartRecommender()
    
    def test_single_categorical(self, recommender):
        """测试单分类 → 饼图"""
        df = pd.DataFrame({
            "status": ["A", "B", "C", "A", "B", "A"],
        })
        
        result = recommender.recommend(df)
        
        assert result.chart_type == ChartType.PIE
        assert result.x_column == "status"
    
    def test_too_many_categories(self, recommender):
        """测试分类过多时不推荐饼图"""
        df = pd.DataFrame({
            "category": [f"cat_{i}" for i in range(15)],
        })
        
        result = recommender.recommend(df)
        
        # 15 个分类超过 PIE_MAX_CATEGORIES (8)，应该推荐表格
        assert result.chart_type != ChartType.PIE or result.confidence < 0.7


class TestScatterChartRecommendation:
    """散点图推荐测试"""
    
    @pytest.fixture
    def recommender(self):
        return ChartRecommender()
    
    def test_two_numeric(self, recommender):
        """测试双数值 → 散点图"""
        df = pd.DataFrame({
            "x": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            "y": [2, 4, 5, 4, 5, 7, 8, 9, 10, 12],
        })
        
        result = recommender.recommend(df)
        
        assert result.chart_type == ChartType.SCATTER
        assert result.x_column == "x"
        assert result.y_column == "y"
    
    def test_scatter_with_color(self, recommender):
        """测试散点图带颜色分组 - 实际上分类+数值优先推荐柱状图"""
        df = pd.DataFrame({
            "x": range(20),
            "y": range(20, 40),
            "group": ["A", "B"] * 10,
        })
        
        result = recommender.recommend(df)
        
        # 有分类列 + 数值列时，优先推荐柱状图
        assert result.chart_type == ChartType.BAR
        # 散点图应该作为备选
        assert any(alt["chart_type"] == "scatter" for alt in result.alternatives)


class TestTableRecommendation:
    """表格推荐测试"""
    
    @pytest.fixture
    def recommender(self):
        return ChartRecommender()
    
    def test_no_suitable_columns(self, recommender):
        """测试无适合列 → 表格"""
        df = pd.DataFrame({
            "name": [f"name_{i}" for i in range(100)],
            "description": [f"desc_{i}" for i in range(100)],
        })
        
        result = recommender.recommend(df)
        
        assert result.chart_type == ChartType.TABLE
        assert result.confidence < 0.5
    
    def test_empty_dataframe(self, recommender):
        """测试空 DataFrame"""
        df = pd.DataFrame()
        
        result = recommender.recommend(df)
        
        assert result.chart_type == ChartType.TABLE


class TestAlternatives:
    """备选图表测试"""
    
    @pytest.fixture
    def recommender(self):
        return ChartRecommender()
    
    def test_has_alternatives(self, recommender):
        """测试生成备选图表"""
        df = pd.DataFrame({
            "category": ["A", "B", "C"] * 3,
            "value": range(9),
            "date": pd.date_range("2024-01-01", periods=9),
        })
        
        result = recommender.recommend(df)
        
        # 折线图优先（有日期列），应该有备选
        assert len(result.alternatives) > 0
    
    def test_alternatives_exclude_primary(self, recommender):
        """测试备选不包含主推荐"""
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=10),
            "value": range(10),
        })
        
        result = recommender.recommend(df)
        
        # 主推荐是折线图，备选不应该包含折线图
        for alt in result.alternatives:
            assert alt["chart_type"] != "line"


class TestConvenienceFunctions:
    """便捷函数测试"""
    
    def test_recommend_chart_function(self):
        """测试 recommend_chart 便捷函数"""
        df = pd.DataFrame({
            "category": ["A", "B", "C"],
            "value": [10, 20, 30],
        })
        
        result = recommend_chart(df)
        
        assert isinstance(result, ChartRecommendation)
        assert result.chart_type == ChartType.BAR
    
    def test_get_chart_type_function(self):
        """测试 get_chart_type 便捷函数"""
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=5),
            "value": range(5),
        })
        
        chart_type = get_chart_type(df)
        
        assert isinstance(chart_type, str)
        assert chart_type == "line"


class TestEdgeCases:
    """边界情况测试"""
    
    @pytest.fixture
    def recommender(self):
        return ChartRecommender()
    
    def test_single_row(self, recommender):
        """测试单行数据"""
        df = pd.DataFrame({
            "category": ["A"],
            "value": [100],
        })
        
        result = recommender.recommend(df)
        
        # 单行数据应该能正常处理
        assert result.chart_type in [ChartType.BAR, ChartType.TABLE]
    
    def test_single_column(self, recommender):
        """测试单列数据"""
        df = pd.DataFrame({
            "value": [1, 2, 3, 4, 5],
        })
        
        result = recommender.recommend(df)
        
        # 单数值列
        assert result.chart_type in [ChartType.BAR, ChartType.TABLE]
    
    def test_all_nulls(self, recommender):
        """测试全空数据 - 应该推荐表格或饼图"""
        df = pd.DataFrame({
            "value": [None, None, None],
        })
        
        result = recommender.recommend(df)
        
        # 全空数据，列为分类类型（0 基数），推荐饼图或表格
        assert result.chart_type in [ChartType.PIE, ChartType.TABLE]
    
    def test_with_question_hint(self, recommender):
        """测试带问题提示"""
        df = pd.DataFrame({
            "category": ["A", "B", "C"],
            "value": [10, 20, 30],
        })
        
        result = recommender.recommend(df, question="各分类的销售额对比")
        
        # 问题提示目前不影响推荐，但不应报错
        assert result.chart_type == ChartType.BAR


class TestConfidence:
    """置信度测试"""
    
    @pytest.fixture
    def recommender(self):
        return ChartRecommender()
    
    def test_high_confidence_time_series(self, recommender):
        """测试时间序列高置信度"""
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=30),
            "value": range(30),
        })
        
        result = recommender.recommend(df)
        
        assert result.confidence >= 0.85
    
    def test_lower_confidence_for_table(self, recommender):
        """测试表格推荐低置信度"""
        df = pd.DataFrame({
            "name": [f"name_{i}" for i in range(50)],
        })
        
        result = recommender.recommend(df)
        
        assert result.chart_type == ChartType.TABLE
        assert result.confidence < 0.5


if __name__ == "__main__":
    pytest.main([__file__, "-v"])