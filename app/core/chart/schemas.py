"""
图表 schema 兼容模块

为旧测试和旧调用路径提供兼容导出。
实际定义仍以 recommender.py 为准。
"""
from __future__ import annotations

from app.core.chart.recommender import ChartRecommendation, ChartType

__all__ = ["ChartRecommendation", "ChartType"]
