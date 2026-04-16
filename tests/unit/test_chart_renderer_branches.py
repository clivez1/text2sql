import pandas as pd
import plotly.graph_objects as go

from app.ui.chart_renderer import PlotlyRenderer, render_simple_bar, render_simple_line
from app.core.chart.recommender import ChartRecommendation, ChartType


def test_bar_without_y_uses_counts():
    renderer = PlotlyRenderer(height=320, width=640)
    df = pd.DataFrame({"category": ["A", "A", "B"]})
    rec = ChartRecommendation(chart_type=ChartType.BAR, x_column="category")
    fig = renderer.render(df, rec)
    assert isinstance(fig, go.Figure)
    assert fig.layout.height == 320
    assert fig.layout.width == 640


def test_bar_multiple_y_columns_grouped():
    renderer = PlotlyRenderer()
    df = pd.DataFrame({"month": ["Jan", "Feb"], "sales": [10, 20], "cost": [3, 5]})
    rec = ChartRecommendation(
        chart_type=ChartType.BAR,
        x_column="month",
        y_columns=["sales", "cost"],
    )
    fig = renderer.render(df, rec)
    assert isinstance(fig, go.Figure)
    assert len(fig.data) == 2
    assert fig.layout.barmode == "group"


def test_bar_missing_x_returns_empty_figure():
    renderer = PlotlyRenderer()
    df = pd.DataFrame({"sales": [10, 20]})
    rec = ChartRecommendation(chart_type=ChartType.BAR, y_columns=["sales"])
    fig = renderer.render(df, rec)
    assert isinstance(fig, go.Figure)
    assert fig.layout.annotations[0].text == "缺少 X 轴列"


def test_line_missing_y_returns_empty_figure():
    renderer = PlotlyRenderer()
    df = pd.DataFrame({"date": [1, 2, 3]})
    rec = ChartRecommendation(chart_type=ChartType.LINE, x_column="date")
    fig = renderer.render(df, rec)
    assert isinstance(fig, go.Figure)
    assert fig.layout.annotations[0].text == "缺少 X/Y 轴列"


def test_scatter_missing_axis_returns_empty_figure():
    renderer = PlotlyRenderer()
    df = pd.DataFrame({"x": [1, 2, 3]})
    rec = ChartRecommendation(chart_type=ChartType.SCATTER, x_column="x")
    fig = renderer.render(df, rec)
    assert isinstance(fig, go.Figure)
    assert fig.layout.annotations[0].text == "缺少 X/Y 轴列"


def test_render_invalid_chart_type_returns_none():
    renderer = PlotlyRenderer()
    df = pd.DataFrame({"x": [1]})
    rec = ChartRecommendation(chart_type=None)
    assert renderer.render(df, rec) is None


def test_render_simple_helpers():
    df = pd.DataFrame({"x": ["A", "B"], "y": [1, 2]})
    bar = render_simple_bar(df, "x", "y")
    line = render_simple_line(df, "x", "y")
    assert isinstance(bar, go.Figure)
    assert isinstance(line, go.Figure)
