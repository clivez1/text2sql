"""
图表渲染模块测试
"""
import pytest
import pandas as pd
import plotly.graph_objects as go

from app.ui.chart_renderer import (
    PlotlyRenderer,
    render_chart,
)
from app.core.chart.recommender import ChartType


class TestPlotlyRenderer:
    """Plotly 渲染器测试"""
    
    @pytest.fixture
    def renderer(self):
        return PlotlyRenderer()
    
    @pytest.fixture
    def sample_df(self):
        return pd.DataFrame({
            "category": ["A", "B", "C"],
            "value": [10, 20, 30],
        })
    
    def test_render_bar(self, renderer, sample_df):
        """测试柱状图渲染"""
        from app.core.chart.recommender import recommend_chart
        
        rec = recommend_chart(sample_df)
        fig = renderer.render(sample_df, rec)
        
        assert fig is not None
        assert isinstance(fig, go.Figure)
    
    def test_render_pie(self, renderer, sample_df):
        """测试饼图渲染"""
        from app.core.chart.recommender import recommend_chart
        
        # 单列分类数据推荐饼图
        df = pd.DataFrame({"category": ["A", "B", "C", "A", "B", "A"]})
        rec = recommend_chart(df)
        fig = renderer.render(df, rec)
        
        assert fig is not None
    
    def test_render_table_returns_none(self, renderer, sample_df):
        """测试表格类型返回 None"""
        from app.core.chart.schemas import ChartRecommendation, ChartType
        
        rec = ChartRecommendation(
            chart_type=ChartType.TABLE,
            confidence=0.3,
        )
        
        fig = renderer.render(sample_df, rec)
        
        # TABLE 类型返回 None
        assert fig is None


class TestRenderChart:
    """便捷函数测试"""
    
    def test_render_chart_function(self):
        """测试 render_chart 函数"""
        df = pd.DataFrame({
            "cat": ["A", "B"],
            "val": [1, 2],
        })
        
        from app.core.chart.recommender import recommend_chart
        
        rec = recommend_chart(df)
        fig = render_chart(df, rec)
        
        assert isinstance(fig, go.Figure)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])