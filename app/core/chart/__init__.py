"""
图表模块

提供数据类型分析和图表推荐功能。
"""
from app.core.chart.recommender import (
    ChartRecommender,
    ChartType,
    ChartRecommendation,
    recommend_chart,
    get_chart_type,
)
from app.core.chart.type_analyzer import (
    DataTypeAnalyzer,
    ColumnType,
    ColumnAnalysis,
    DataFrameAnalysis,
    analyze_column,
    analyze_dataframe,
    get_chart_recommendation,
)

__all__ = [
    # recommender
    "ChartRecommender",
    "ChartType",
    "ChartRecommendation",
    "recommend_chart",
    "get_chart_type",
    # type_analyzer
    "DataTypeAnalyzer",
    "ColumnType",
    "ColumnAnalysis",
    "DataFrameAnalysis",
    "analyze_column",
    "analyze_dataframe",
    "get_chart_recommendation",
]