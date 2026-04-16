"""
图表推荐器 (Chart Recommender)

基于数据类型分析推荐最佳图表类型。

支持的图表类型：
- bar: 柱状图（分类 vs 数值）
- line: 折线图（时间序列）
- pie: 饼图（分类占比）
- scatter: 散点图（数值 vs 数值）
- table: 表格（无可视化）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any

import pandas as pd

from app.core.chart.type_analyzer import (
    DataTypeAnalyzer,
    DataFrameAnalysis,
    ColumnType,
)


class ChartType(Enum):
    """图表类型"""
    BAR = "bar"
    LINE = "line"
    PIE = "pie"
    SCATTER = "scatter"
    TABLE = "table"


@dataclass
class ChartRecommendation:
    """图表推荐结果"""
    chart_type: ChartType
    x_column: Optional[str] = None
    y_column: Optional[str] = None
    y_columns: List[str] = field(default_factory=list)
    color_column: Optional[str] = None
    
    # 推荐置信度 (0.0 - 1.0)
    confidence: float = 0.5
    
    # 备选图表
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    
    # 推荐理由
    reason: str = ""
    
    # 数据分析结果
    analysis: Optional[DataFrameAnalysis] = None
    
    # 图表配置
    config: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "chart_type": self.chart_type.value,
            "x_column": self.x_column,
            "y_column": self.y_column,
            "y_columns": self.y_columns,
            "color_column": self.color_column,
            "confidence": self.confidence,
            "alternatives": self.alternatives,
            "reason": self.reason,
            "config": self.config,
        }


class ChartRecommender:
    """
    图表推荐器
    
    基于数据类型分析推荐最佳图表类型。
    """
    
    # 饼图最大分类数
    PIE_MAX_CATEGORIES = 8
    
    # 柱状图最大分类数
    BAR_MAX_CATEGORIES = 20
    
    def __init__(self):
        self.type_analyzer = DataTypeAnalyzer()
    
    def recommend(
        self, 
        df: pd.DataFrame, 
        question: Optional[str] = None
    ) -> ChartRecommendation:
        """
        推荐最佳图表类型
        
        Args:
            df: pandas DataFrame
            question: 用户问题（可选，用于语义提示）
            
        Returns:
            ChartRecommendation: 推荐结果
        """
        # 分析数据类型
        analysis = self.type_analyzer.analyze_dataframe(df)
        
        # 基于规则推荐
        recommendation = self._apply_rules(df, analysis, question)
        
        # 存储分析结果
        recommendation.analysis = analysis
        
        return recommendation
    
    def _apply_rules(
        self, 
        df: pd.DataFrame, 
        analysis: DataFrameAnalysis,
        question: Optional[str] = None
    ) -> ChartRecommendation:
        """应用推荐规则"""
        
        # 获取可用列
        numeric_cols = analysis.numeric_columns
        categorical_cols = analysis.categorical_columns
        datetime_cols = analysis.datetime_columns
        boolean_cols = analysis.boolean_columns
        
        # 分类列包含布尔列
        all_categorical = categorical_cols + boolean_cols
        
        # 规则优先级：
        # 1. 时间序列 → 折线图
        # 2. 分类 + 数值 → 柱状图
        # 3. 单分类（低基数）→ 饼图
        # 4. 双数值 → 散点图
        # 5. 默认 → 表格
        
        # 规则 1: 时间序列 → 折线图
        if datetime_cols and numeric_cols:
            return self._recommend_line(
                datetime_cols[0], 
                numeric_cols[:3],
                analysis,
                confidence=0.9
            )
        
        # 规则 2: 分类 + 数值 → 柱状图
        if all_categorical and numeric_cols:
            cat_col = self._select_best_categorical(all_categorical, analysis)
            if cat_col:
                return self._recommend_bar(
                    cat_col,
                    numeric_cols[:3],
                    analysis,
                    confidence=0.85
                )
        
        # 规则 3: 单分类（低基数）→ 饼图
        if len(all_categorical) >= 1 and len(numeric_cols) == 0:
            cat_col = self._select_best_categorical(all_categorical, analysis)
            if cat_col and self._get_cardinality(cat_col, analysis) <= self.PIE_MAX_CATEGORIES:
                return self._recommend_pie(
                    cat_col,
                    analysis,
                    confidence=0.7
                )
        
        # 规则 4: 双数值 → 散点图
        if len(numeric_cols) >= 2:
            return self._recommend_scatter(
                numeric_cols[0],
                numeric_cols[1],
                analysis,
                confidence=0.8
            )
        
        # 规则 5: 单数值 → 柱状图（低基数时）
        if len(numeric_cols) == 1:
            col_analysis = self._get_column_analysis(numeric_cols[0], analysis)
            if col_analysis and col_analysis.cardinality <= self.BAR_MAX_CATEGORIES:
                return self._recommend_bar(
                    numeric_cols[0],
                    [],  # 没有 Y 轴，显示计数
                    analysis,
                    confidence=0.6
                )
        
        # 默认: 表格
        return self._recommend_table(analysis)
    
    def _recommend_line(
        self,
        x_col: str,
        y_cols: List[str],
        analysis: DataFrameAnalysis,
        confidence: float = 0.9
    ) -> ChartRecommendation:
        """推荐折线图"""
        reason = f"时间序列数据，'{x_col}' 作为时间轴"
        if y_cols:
            reason += f"，'{y_cols[0]}' 作为数值"
        
        alternatives = self._generate_alternatives(
            analysis, 
            exclude=ChartType.LINE
        )
        
        return ChartRecommendation(
            chart_type=ChartType.LINE,
            x_column=x_col,
            y_column=y_cols[0] if y_cols else None,
            y_columns=y_cols,
            confidence=confidence,
            alternatives=alternatives,
            reason=reason,
            config={
                "sort_x": True,
                "markers": True,
            }
        )
    
    def _recommend_bar(
        self,
        x_col: str,
        y_cols: List[str],
        analysis: DataFrameAnalysis,
        confidence: float = 0.85
    ) -> ChartRecommendation:
        """推荐柱状图"""
        cardinality = self._get_cardinality(x_col, analysis)
        
        if y_cols:
            reason = f"分类数据 '{x_col}' 与数值 '{y_cols[0]}' 对比"
        else:
            reason = f"分类数据 '{x_col}' 的频次统计"
        
        # 基数过高时降低置信度
        if cardinality > self.BAR_MAX_CATEGORIES:
            confidence *= 0.7
            reason += f"（注意：分类较多 ({cardinality} 个），可能显示拥挤）"
        
        alternatives = self._generate_alternatives(
            analysis,
            exclude=ChartType.BAR
        )
        
        return ChartRecommendation(
            chart_type=ChartType.BAR,
            x_column=x_col,
            y_column=y_cols[0] if y_cols else None,
            y_columns=y_cols,
            confidence=confidence,
            alternatives=alternatives,
            reason=reason,
            config={
                "orientation": "v",
                "show_values": cardinality <= 10,
            }
        )
    
    def _recommend_pie(
        self,
        col: str,
        analysis: DataFrameAnalysis,
        confidence: float = 0.7
    ) -> ChartRecommendation:
        """推荐饼图"""
        cardinality = self._get_cardinality(col, analysis)
        reason = f"分类 '{col}' 的占比分布（{cardinality} 个分类）"
        
        alternatives = self._generate_alternatives(
            analysis,
            exclude=ChartType.PIE
        )
        
        return ChartRecommendation(
            chart_type=ChartType.PIE,
            x_column=col,
            y_column=None,
            y_columns=[],
            confidence=confidence,
            alternatives=alternatives,
            reason=reason,
            config={
                "show_percentage": True,
                "show_legend": cardinality <= 6,
            }
        )
    
    def _recommend_scatter(
        self,
        x_col: str,
        y_col: str,
        analysis: DataFrameAnalysis,
        confidence: float = 0.8
    ) -> ChartRecommendation:
        """推荐散点图"""
        reason = f"数值 '{x_col}' 与 '{y_col}' 的相关性分析"
        
        # 检查是否有分类列可用于颜色
        color_col = None
        if analysis.categorical_columns:
            color_col = analysis.categorical_columns[0]
            reason += f"，按 '{color_col}' 分组"
        
        alternatives = self._generate_alternatives(
            analysis,
            exclude=ChartType.SCATTER
        )
        
        return ChartRecommendation(
            chart_type=ChartType.SCATTER,
            x_column=x_col,
            y_column=y_col,
            y_columns=[y_col],
            color_column=color_col,
            confidence=confidence,
            alternatives=alternatives,
            reason=reason,
            config={
                "show_trendline": True,
                "opacity": 0.6,
            }
        )
    
    def _recommend_table(
        self,
        analysis: DataFrameAnalysis
    ) -> ChartRecommendation:
        """推荐表格"""
        reason = "数据不适合可视化，建议以表格形式展示"
        
        # 如果有数值列，可以作为备选
        alternatives = []
        if analysis.numeric_columns:
            alternatives.append({
                "chart_type": "bar",
                "reason": "可以尝试柱状图",
                "x_column": analysis.numeric_columns[0],
            })
        
        return ChartRecommendation(
            chart_type=ChartType.TABLE,
            confidence=0.3,
            alternatives=alternatives,
            reason=reason,
            config={
                "pagination": True,
                "page_size": 20,
            }
        )
    
    def _select_best_categorical(
        self, 
        categorical_cols: List[str],
        analysis: DataFrameAnalysis
    ) -> Optional[str]:
        """选择最佳分类列（基数适中）"""
        best_col = None
        best_score = -1
        
        for col in categorical_cols:
            cardinality = self._get_cardinality(col, analysis)
            
            # 最佳基数：3-10
            if 3 <= cardinality <= 10:
                score = 10 - abs(cardinality - 5)
            elif cardinality < 3:
                score = cardinality
            else:
                score = max(0, 10 - (cardinality - 10))
            
            if score > best_score:
                best_score = score
                best_col = col
        
        return best_col
    
    def _get_cardinality(
        self, 
        col: str, 
        analysis: DataFrameAnalysis
    ) -> int:
        """获取列的基数"""
        for col_analysis in analysis.columns:
            if col_analysis.column_name == col:
                return col_analysis.cardinality
        return 0
    
    def _get_column_analysis(
        self, 
        col: str, 
        analysis: DataFrameAnalysis
    ) -> Optional[Any]:
        """获取列分析结果"""
        for col_analysis in analysis.columns:
            if col_analysis.column_name == col:
                return col_analysis
        return None
    
    def _generate_alternatives(
        self,
        analysis: DataFrameAnalysis,
        exclude: ChartType
    ) -> List[Dict[str, Any]]:
        """生成备选图表"""
        alternatives = []
        
        numeric_cols = analysis.numeric_columns
        categorical_cols = analysis.categorical_columns + analysis.boolean_columns
        datetime_cols = analysis.datetime_columns
        
        # 折线图备选
        if datetime_cols and numeric_cols and exclude != ChartType.LINE:
            alternatives.append({
                "chart_type": "line",
                "reason": "时间序列数据",
                "x_column": datetime_cols[0],
                "y_column": numeric_cols[0] if numeric_cols else None,
            })
        
        # 柱状图备选
        if categorical_cols and numeric_cols and exclude != ChartType.BAR:
            alternatives.append({
                "chart_type": "bar",
                "reason": "分类对比",
                "x_column": categorical_cols[0],
                "y_column": numeric_cols[0] if numeric_cols else None,
            })
        
        # 散点图备选
        if len(numeric_cols) >= 2 and exclude != ChartType.SCATTER:
            alternatives.append({
                "chart_type": "scatter",
                "reason": "数值相关性分析",
                "x_column": numeric_cols[0],
                "y_column": numeric_cols[1],
            })
        
        return alternatives[:3]  # 最多 3 个备选


# 便捷函数
def recommend_chart(
    df: pd.DataFrame, 
    question: Optional[str] = None
) -> ChartRecommendation:
    """
    推荐图表类型（便捷函数）
    
    Args:
        df: pandas DataFrame
        question: 用户问题（可选）
        
    Returns:
        ChartRecommendation: 推荐结果
    """
    recommender = ChartRecommender()
    return recommender.recommend(df, question)


def get_chart_type(df: pd.DataFrame) -> str:
    """
    获取推荐的图表类型字符串（向后兼容）
    
    Args:
        df: pandas DataFrame
        
    Returns:
        str: 图表类型名称
    """
    recommendation = recommend_chart(df)
    return recommendation.chart_type.value