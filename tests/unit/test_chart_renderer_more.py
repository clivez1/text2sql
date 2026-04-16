"""
Chart Renderer 补充测试
"""
import pytest
import pandas as pd
import plotly.graph_objects as go

from app.ui.chart_renderer import PlotlyRenderer, render_chart


class TestPlotlyRendererMore:
    """Plotly 渲染器补充测试"""
    
    @pytest.fixture
    def renderer(self):
        return PlotlyRenderer()
    
    def test_render_bar_chart(self, renderer):
        """测试柱状图"""
        df = pd.DataFrame({
            "category": ["A", "B", "C"],
            "value": [10, 20, 30],
        })
        
        from app.core.chart.recommender import recommend_chart
        rec = recommend_chart(df)
        
        fig = renderer.render(df, rec)
        
        assert fig is not None
        assert isinstance(fig, go.Figure)
    
    def test_render_line_chart(self, renderer):
        """测试折线图"""
        df = pd.DataFrame({
            "date": pd.date_range("2024-01-01", periods=5),
            "value": [1, 2, 3, 4, 5],
        })
        
        from app.core.chart.recommender import recommend_chart
        rec = recommend_chart(df)
        
        fig = renderer.render(df, rec)
        
        assert fig is not None
    
    def test_render_scatter_chart(self, renderer):
        """测试散点图"""
        df = pd.DataFrame({
            "x": [1, 2, 3, 4, 5],
            "y": [2, 4, 5, 4, 5],
        })
        
        from app.core.chart.recommender import recommend_chart
        rec = recommend_chart(df)
        
        fig = renderer.render(df, rec)
        
        assert fig is not None
    
    def test_render_pie_chart(self, renderer):
        """测试饼图"""
        df = pd.DataFrame({
            "category": ["A", "B", "C", "A", "B", "A"],
        })
        
        from app.core.chart.recommender import recommend_chart
        rec = recommend_chart(df)
        
        fig = renderer.render(df, rec)
        
        assert fig is not None
    
    def test_render_with_none_recommendation(self, renderer):
        """测试空推荐 - 应该抛出异常或返回默认"""
        df = pd.DataFrame({"a": [1, 2, 3]})
        
        # None recommendation 应该抛出 AttributeError
        # 这是预期行为，测试应该捕获这个异常
        with pytest.raises(AttributeError):
            renderer.render(df, None)


class TestRenderChartFunction:
    """render_chart 函数测试"""
    
    def test_render_chart_with_dataframe(self):
        """测试 render_chart 函数"""
        df = pd.DataFrame({
            "x": ["A", "B", "C"],
            "y": [1, 2, 3],
        })
        
        from app.core.chart.recommender import recommend_chart
        rec = recommend_chart(df)
        
        fig = render_chart(df, rec)
        
        assert isinstance(fig, go.Figure)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])