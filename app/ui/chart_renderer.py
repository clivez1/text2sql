"""
Plotly 图表渲染器

将 ChartRecommendation 转换为交互式 Plotly 图表。
"""
from __future__ import annotations

from typing import Optional, Dict, Any, List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from app.core.chart.recommender import ChartType, ChartRecommendation


class PlotlyRenderer:
    """Plotly 图表渲染器"""
    
    # 默认颜色方案
    COLOR_SEQUENCE = px.colors.qualitative.Plotly
    
    # 图表默认配置
    DEFAULT_LAYOUT = {
        "margin": dict(l=20, r=20, t=40, b=20),
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": dict(size=12),
    }
    
    def __init__(self, height: int = 400, width: Optional[int] = None):
        self.height = height
        self.width = width
    
    def render(
        self, 
        df: pd.DataFrame, 
        recommendation: ChartRecommendation
    ) -> Optional[go.Figure]:
        """
        根据推荐结果渲染图表
        
        Args:
            df: 数据
            recommendation: 图表推荐
            
        Returns:
            plotly Figure 或 None
        """
        if recommendation.chart_type == ChartType.TABLE:
            return None
        
        renderers = {
            ChartType.BAR: self._render_bar,
            ChartType.LINE: self._render_line,
            ChartType.PIE: self._render_pie,
            ChartType.SCATTER: self._render_scatter,
        }
        
        renderer = renderers.get(recommendation.chart_type)
        if not renderer:
            return None
        
        try:
            fig = renderer(df, recommendation)
            fig.update_layout(**self._get_layout_config())
            return fig
        except Exception as e:
            print(f"Error rendering chart: {e}")
            return None
    
    def _render_bar(
        self, 
        df: pd.DataFrame, 
        rec: ChartRecommendation
    ) -> go.Figure:
        """渲染柱状图"""
        x_col = rec.x_column
        y_cols = rec.y_columns or []
        
        if not x_col:
            return self._empty_figure("缺少 X 轴列")
        
        if not y_cols:
            # 没有 Y 列，显示计数
            counts = df[x_col].value_counts().reset_index()
            counts.columns = [x_col, "count"]
            fig = px.bar(
                counts,
                x=x_col,
                y="count",
                title=f"{x_col} 频次分布",
                color_discrete_sequence=self.COLOR_SEQUENCE,
            )
        elif len(y_cols) == 1:
            # 单 Y 列
            fig = px.bar(
                df,
                x=x_col,
                y=y_cols[0],
                color=rec.color_column,
                title=f"{y_cols[0]} 按 {x_col}",
                color_discrete_sequence=self.COLOR_SEQUENCE,
            )
        else:
            # 多 Y 列
            fig = go.Figure()
            for y_col in y_cols:
                fig.add_trace(go.Bar(
                    name=y_col,
                    x=df[x_col],
                    y=df[y_col],
                ))
            fig.update_layout(
                title=f"数值对比 按 {x_col}",
                barmode="group",
            )
        
        return fig
    
    def _render_line(
        self, 
        df: pd.DataFrame, 
        rec: ChartRecommendation
    ) -> go.Figure:
        """渲染折线图"""
        x_col = rec.x_column
        y_cols = rec.y_columns or []
        
        if not x_col or not y_cols:
            return self._empty_figure("缺少 X/Y 轴列")
        
        # 确保 X 轴排序
        df = df.sort_values(x_col)
        
        fig = go.Figure()
        
        for y_col in y_cols:
            fig.add_trace(go.Scatter(
                name=y_col,
                x=df[x_col],
                y=df[y_col],
                mode="lines+markers",
                line=dict(width=2),
            ))
        
        fig.update_layout(
            title=f"趋势图",
            xaxis_title=x_col,
            yaxis_title=y_cols[0] if len(y_cols) == 1 else "值",
        )
        
        return fig
    
    def _render_pie(
        self, 
        df: pd.DataFrame, 
        rec: ChartRecommendation
    ) -> go.Figure:
        """渲染饼图"""
        x_col = rec.x_column
        
        if not x_col:
            return self._empty_figure("缺少分类列")
        
        # 统计频次
        counts = df[x_col].value_counts()
        
        fig = px.pie(
            values=counts.values,
            names=counts.index,
            title=f"{x_col} 占比分布",
            color_discrete_sequence=self.COLOR_SEQUENCE,
        )
        
        fig.update_traces(
            textposition="inside",
            textinfo="percent+label",
        )
        
        return fig
    
    def _render_scatter(
        self, 
        df: pd.DataFrame, 
        rec: ChartRecommendation
    ) -> go.Figure:
        """渲染散点图"""
        x_col = rec.x_column
        y_col = rec.y_column
        color_col = rec.color_column
        
        if not x_col or not y_col:
            return self._empty_figure("缺少 X/Y 轴列")
        
        fig = px.scatter(
            df,
            x=x_col,
            y=y_col,
            color=color_col,
            title=f"{y_col} vs {x_col}",
            color_discrete_sequence=self.COLOR_SEQUENCE,
            opacity=0.7,
        )
        
        # 添加趋势线
        try:
            fig.update_traces(marker=dict(size=8))
        except Exception:
            pass
        
        return fig
    
    def _get_layout_config(self) -> Dict[str, Any]:
        """获取布局配置"""
        config = self.DEFAULT_LAYOUT.copy()
        config["height"] = self.height
        if self.width:
            config["width"] = self.width
        return config
    
    def _empty_figure(self, message: str = "无数据") -> go.Figure:
        """创建空图表"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False,
            font=dict(size=16),
        )
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
        )
        return fig


# 便捷函数
def render_chart(
    df: pd.DataFrame, 
    recommendation: ChartRecommendation,
    height: int = 400,
) -> Optional[go.Figure]:
    """
    渲染图表（便捷函数）
    
    Args:
        df: 数据
        recommendation: 推荐结果
        height: 图表高度
        
    Returns:
        plotly Figure 或 None
    """
    renderer = PlotlyRenderer(height=height)
    return renderer.render(df, recommendation)


def render_simple_bar(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: Optional[str] = None,
) -> go.Figure:
    """渲染简单柱状图"""
    fig = px.bar(
        df,
        x=x_col,
        y=y_col,
        title=title or f"{y_col} 按 {x_col}",
        color_discrete_sequence=PlotlyRenderer.COLOR_SEQUENCE,
    )
    return fig


def render_simple_line(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: Optional[str] = None,
) -> go.Figure:
    """渲染简单折线图"""
    fig = px.line(
        df,
        x=x_col,
        y=y_col,
        title=title or f"{y_col} 趋势",
        markers=True,
    )
    return fig