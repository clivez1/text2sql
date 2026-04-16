"""
数据类型分析器 (Data Type Analyzer)

分析 DataFrame 列的数据类型，为图表推荐提供基础。

功能：
1. 识别数值类型（整数、浮点数）
2. 识别分类类型（低基数字符串）
3. 识别日期时间类型
4. 识别布尔类型
5. 检测时间序列数据
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, Set

import pandas as pd
import numpy as np


class ColumnType(Enum):
    """列数据类型"""
    NUMERIC = "numeric"           # 数值类型（整数/浮点数）
    CATEGORICAL = "categorical"   # 分类类型（低基数字符串）
    DATETIME = "datetime"         # 日期时间类型
    BOOLEAN = "boolean"           # 布尔类型
    TEXT = "text"                 # 文本类型（高基数字符串）
    ID = "id"                     # ID 类型（唯一标识符）
    UNKNOWN = "unknown"           # 未知类型


@dataclass
class ColumnAnalysis:
    """单列分析结果"""
    column_name: str
    column_type: ColumnType
    dtype: str                    # pandas dtype 字符串
    
    # 基本统计
    total_count: int = 0          # 总行数
    null_count: int = 0           # 空值数量
    unique_count: int = 0         # 唯一值数量
    
    # 类型特定信息
    is_numeric: bool = False
    is_datetime: bool = False
    is_boolean: bool = False
    is_categorical: bool = False
    is_text: bool = False
    is_id: bool = False
    
    # 数值统计
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None
    median_value: Optional[float] = None
    std_value: Optional[float] = None
    
    # 分类统计
    cardinality: int = 0          # 基数（唯一值数量）
    cardinality_ratio: float = 0.0  # 基数比例
    top_categories: List[Any] = field(default_factory=list)
    
    # 时间统计
    datetime_format: Optional[str] = None
    time_range: Optional[tuple] = None
    
    # 可视化建议
    suitable_for_x: bool = False  # 适合作为 X 轴
    suitable_for_y: bool = False  # 适合作为 Y 轴
    suitable_for_color: bool = False  # 适合作为颜色分组
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "column_name": self.column_name,
            "column_type": self.column_type.value,
            "dtype": self.dtype,
            "total_count": self.total_count,
            "null_count": self.null_count,
            "unique_count": self.unique_count,
            "null_ratio": self.null_count / self.total_count if self.total_count > 0 else 0,
            "is_numeric": self.is_numeric,
            "is_datetime": self.is_datetime,
            "is_boolean": self.is_boolean,
            "is_categorical": self.is_categorical,
            "is_text": self.is_text,
            "is_id": self.is_id,
            "cardinality": self.cardinality,
            "cardinality_ratio": self.cardinality_ratio,
            "min_value": self.min_value,
            "max_value": self.max_value,
            "mean_value": self.mean_value,
            "median_value": self.median_value,
            "std_value": self.std_value,
            "suitable_for_x": self.suitable_for_x,
            "suitable_for_y": self.suitable_for_y,
            "suitable_for_color": self.suitable_for_color,
        }


@dataclass
class DataFrameAnalysis:
    """DataFrame 分析结果"""
    row_count: int
    column_count: int
    columns: List[ColumnAnalysis]
    
    # 汇总信息
    numeric_columns: List[str] = field(default_factory=list)
    categorical_columns: List[str] = field(default_factory=list)
    datetime_columns: List[str] = field(default_factory=list)
    boolean_columns: List[str] = field(default_factory=list)
    text_columns: List[str] = field(default_factory=list)
    id_columns: List[str] = field(default_factory=list)
    
    # 时间序列检测
    is_time_series: bool = False
    time_column: Optional[str] = None
    
    # 可视化建议
    recommended_x: Optional[str] = None
    recommended_y: List[str] = field(default_factory=list)
    recommended_color: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "row_count": self.row_count,
            "column_count": self.column_count,
            "columns": [c.to_dict() for c in self.columns],
            "numeric_columns": self.numeric_columns,
            "categorical_columns": self.categorical_columns,
            "datetime_columns": self.datetime_columns,
            "boolean_columns": self.boolean_columns,
            "text_columns": self.text_columns,
            "id_columns": self.id_columns,
            "is_time_series": self.is_time_series,
            "time_column": self.time_column,
            "recommended_x": self.recommended_x,
            "recommended_y": self.recommended_y,
            "recommended_color": self.recommended_color,
        }


class DataTypeAnalyzer:
    """
    数据类型分析器
    
    分析 DataFrame 的列类型，识别适合可视化的列组合。
    """
    
    # 分类类型的最大基数比例阈值
    CATEGORICAL_THRESHOLD = 0.1  # 唯一值比例 <= 10% 视为分类
    
    # 分类类型的最大绝对基数
    MAX_CATEGORIES = 20
    
    # ID 类型的最小唯一值比例
    ID_THRESHOLD = 0.95  # 唯一值比例 >= 95% 视为 ID
    
    # 常见日期格式
    DATETIME_PATTERNS = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%Y-%m-%d %H:%M:%S",
        "%Y/%m/%d %H:%M:%S",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%SZ",
    ]
    
    def __init__(
        self,
        categorical_threshold: float = None,
        max_categories: int = None,
        id_threshold: float = None,
    ):
        """
        初始化分析器
        
        Args:
            categorical_threshold: 分类类型基数比例阈值
            max_categories: 分类类型最大基数
            id_threshold: ID 类型唯一值比例阈值
        """
        self.categorical_threshold = categorical_threshold or self.CATEGORICAL_THRESHOLD
        self.max_categories = max_categories or self.MAX_CATEGORIES
        self.id_threshold = id_threshold or self.ID_THRESHOLD
    
    def analyze_column(self, series: pd.Series) -> ColumnAnalysis:
        """
        分析单列数据
        
        Args:
            series: pandas Series
            
        Returns:
            ColumnAnalysis: 列分析结果
        """
        analysis = ColumnAnalysis(
            column_name=series.name or "unknown",
            column_type=ColumnType.UNKNOWN,
            dtype=str(series.dtype),
        )
        
        # 基本统计
        analysis.total_count = len(series)
        analysis.null_count = series.isna().sum()
        analysis.unique_count = series.nunique()
        analysis.cardinality = analysis.unique_count
        analysis.cardinality_ratio = (
            analysis.unique_count / analysis.total_count 
            if analysis.total_count > 0 else 0
        )
        
        # 检测类型
        self._detect_type(series, analysis)
        
        # 计算统计信息
        self._calculate_stats(series, analysis)
        
        # 确定可视化适用性
        self._determine_visualization_suitability(analysis)
        
        return analysis
    
    def _detect_type(self, series: pd.Series, analysis: ColumnAnalysis) -> None:
        """检测列数据类型"""
        dtype = series.dtype
        col_name_lower = str(series.name or "").lower()
        
        # 1. 检测数值类型
        if pd.api.types.is_numeric_dtype(dtype):
            # 检查是否可能是 ID（仅通过列名检测，避免误判高基数数值列）
            is_id_by_name = any(kw in col_name_lower for kw in ["id", "key", "uuid", "pk"])
            if is_id_by_name:
                analysis.column_type = ColumnType.ID
                analysis.is_id = True
            # 检查是否是布尔数值（0/1）
            elif set(series.dropna().unique()) <= {0, 1, 0.0, 1.0}:
                analysis.column_type = ColumnType.BOOLEAN
                analysis.is_boolean = True
            else:
                analysis.column_type = ColumnType.NUMERIC
                analysis.is_numeric = True
            return
        
        # 2. 检测布尔类型
        if pd.api.types.is_bool_dtype(dtype):
            analysis.column_type = ColumnType.BOOLEAN
            analysis.is_boolean = True
            return
        
        # 3. 检测日期时间类型
        if pd.api.types.is_datetime64_any_dtype(dtype):
            analysis.column_type = ColumnType.DATETIME
            analysis.is_datetime = True
            return
        
        # 4. 尝试解析为日期时间
        if dtype == object:
            sample = series.dropna().head(100)
            if len(sample) > 0 and self._try_parse_datetime(sample):
                analysis.column_type = ColumnType.DATETIME
                analysis.is_datetime = True
                return
        
        # 5. 检测字符串类型（分类/文本/ID）
        if dtype == object or pd.api.types.is_string_dtype(dtype):
            col_name_lower = str(series.name or "").lower()
            
            # 检查是否是 ID（列名暗示 或 高唯一值比例 + 足够样本）
            is_id_by_name = any(kw in col_name_lower for kw in ["id", "key", "uuid", "pk"])
            is_id_by_ratio = analysis.cardinality_ratio >= 0.99 and analysis.total_count > 10
            if is_id_by_name or is_id_by_ratio:
                analysis.column_type = ColumnType.ID
                analysis.is_id = True
            # 检查是否是分类（低基数）
            elif analysis.cardinality <= self.max_categories:
                analysis.column_type = ColumnType.CATEGORICAL
                analysis.is_categorical = True
            else:
                analysis.column_type = ColumnType.TEXT
                analysis.is_text = True
            return
        
        # 默认：未知类型
        analysis.column_type = ColumnType.UNKNOWN
    
    def _try_parse_datetime(self, sample: pd.Series) -> bool:
        """尝试解析为日期时间"""
        for pattern in self.DATETIME_PATTERNS:
            try:
                pd.to_datetime(sample, format=pattern, errors='raise')
                return True
            except (ValueError, TypeError):
                continue
        
        # 尝试自动解析（统一按字符串处理，避免对象数组推断时产生噪音 warning）
        try:
            normalized = sample.astype(str)
            pd.to_datetime(normalized, errors='raise', format='mixed')
            return True
        except (ValueError, TypeError):
            return False
    
    def _calculate_stats(self, series: pd.Series, analysis: ColumnAnalysis) -> None:
        """计算统计信息"""
        # 数值统计（包括 ID 类型的数值列）
        if pd.api.types.is_numeric_dtype(series.dtype):
            clean = series.dropna()
            if len(clean) > 0:
                analysis.min_value = float(clean.min())
                analysis.max_value = float(clean.max())
                analysis.mean_value = float(clean.mean())
                analysis.median_value = float(clean.median())
                analysis.std_value = float(clean.std())
        
        elif analysis.is_categorical or analysis.is_boolean:
            # 分类统计：获取 top categories
            value_counts = series.value_counts()
            analysis.top_categories = value_counts.head(5).index.tolist()
        
        elif analysis.is_datetime:
            # 时间统计
            clean = pd.to_datetime(series.dropna(), errors='coerce')
            if len(clean) > 0:
                analysis.time_range = (clean.min(), clean.max())
    
    def _determine_visualization_suitability(self, analysis: ColumnAnalysis) -> None:
        """确定可视化适用性"""
        if analysis.is_datetime:
            # 日期时间适合 X 轴（时间序列）
            analysis.suitable_for_x = True
            analysis.suitable_for_color = analysis.cardinality <= self.max_categories
        
        elif analysis.is_categorical or analysis.is_boolean:
            # 分类适合 X 轴或颜色分组
            analysis.suitable_for_x = analysis.cardinality <= self.max_categories
            analysis.suitable_for_color = analysis.cardinality <= 10
        
        elif analysis.is_numeric:
            # 数值适合 Y 轴
            analysis.suitable_for_y = True
            # 如果基数低，也可以作为 X 轴
            analysis.suitable_for_x = analysis.cardinality <= self.max_categories
            analysis.suitable_for_color = analysis.cardinality <= 10
        
        elif analysis.is_id:
            # ID 不适合可视化
            pass
        
        elif analysis.is_text:
            # 文本：低基数的可以作为颜色分组
            analysis.suitable_for_color = analysis.cardinality <= 10
    
    def analyze_dataframe(self, df: pd.DataFrame) -> DataFrameAnalysis:
        """
        分析整个 DataFrame
        
        Args:
            df: pandas DataFrame
            
        Returns:
            DataFrameAnalysis: DataFrame 分析结果
        """
        analyses = [self.analyze_column(df[col]) for col in df.columns]
        
        result = DataFrameAnalysis(
            row_count=len(df),
            column_count=len(df.columns),
            columns=analyses,
        )
        
        # 分类列
        for col in analyses:
            if col.is_numeric:
                result.numeric_columns.append(col.column_name)
            if col.is_categorical:
                result.categorical_columns.append(col.column_name)
            if col.is_datetime:
                result.datetime_columns.append(col.column_name)
            if col.is_boolean:
                result.boolean_columns.append(col.column_name)
            if col.is_text:
                result.text_columns.append(col.column_name)
            if col.is_id:
                result.id_columns.append(col.column_name)
        
        # 检测时间序列
        if len(result.datetime_columns) > 0:
            result.is_time_series = True
            result.time_column = result.datetime_columns[0]
        
        # 推荐可视化列
        result.recommended_x = self._recommend_x_axis(analyses)
        result.recommended_y = self._recommend_y_axis(analyses, result.recommended_x)
        result.recommended_color = self._recommend_color(analyses)
        
        return result
    
    def _recommend_x_axis(self, analyses: List[ColumnAnalysis]) -> Optional[str]:
        """推荐 X 轴列"""
        # 优先级：datetime > categorical > numeric (low cardinality)
        
        for col in analyses:
            if col.is_datetime and col.suitable_for_x:
                return col.column_name
        
        for col in analyses:
            if col.is_categorical and col.suitable_for_x:
                return col.column_name
        
        for col in analyses:
            if col.is_boolean and col.suitable_for_x:
                return col.column_name
        
        for col in analyses:
            if col.is_numeric and col.suitable_for_x:
                return col.column_name
        
        return None
    
    def _recommend_y_axis(
        self, 
        analyses: List[ColumnAnalysis], 
        x_column: Optional[str]
    ) -> List[str]:
        """推荐 Y 轴列"""
        y_columns = []
        
        for col in analyses:
            if col.is_numeric and col.suitable_for_y:
                if col.column_name != x_column:
                    y_columns.append(col.column_name)
        
        return y_columns[:3]  # 最多推荐 3 个
    
    def _recommend_color(self, analyses: List[ColumnAnalysis]) -> Optional[str]:
        """推荐颜色分组列"""
        for col in analyses:
            if col.suitable_for_color and (col.is_categorical or col.is_boolean):
                return col.column_name
        
        return None
    
    def get_chart_recommendation(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        获取图表推荐
        
        Args:
            df: pandas DataFrame
            
        Returns:
            dict: 包含图表类型和建议的字典
        """
        analysis = self.analyze_dataframe(df)
        
        recommendation = {
            "chart_type": "table",  # 默认
            "x": analysis.recommended_x,
            "y": analysis.recommended_y,
            "color": analysis.recommended_color,
            "analysis": analysis.to_dict(),
        }
        
        # 根据数据特征推荐图表类型
        x_type = self._get_column_type(analysis, analysis.recommended_x)
        y_count = len(analysis.recommended_y)
        
        if analysis.is_time_series and y_count > 0:
            recommendation["chart_type"] = "line"
        elif x_type in ["categorical", "boolean"] and y_count > 0:
            recommendation["chart_type"] = "bar"
        elif y_count >= 2:
            recommendation["chart_type"] = "scatter"
        elif y_count == 1 and x_type == "numeric":
            recommendation["chart_type"] = "scatter"
        
        return recommendation
    
    def _get_column_type(
        self, 
        analysis: DataFrameAnalysis, 
        column_name: Optional[str]
    ) -> Optional[str]:
        """获取列类型"""
        if not column_name:
            return None
        
        for col in analysis.columns:
            if col.column_name == column_name:
                return col.column_type.value
        
        return None


# 便捷函数
def analyze_column(series: pd.Series) -> ColumnAnalysis:
    """分析单列（便捷函数）"""
    analyzer = DataTypeAnalyzer()
    return analyzer.analyze_column(series)


def analyze_dataframe(df: pd.DataFrame) -> DataFrameAnalysis:
    """分析 DataFrame（便捷函数）"""
    analyzer = DataTypeAnalyzer()
    return analyzer.analyze_dataframe(df)


def get_chart_recommendation(df: pd.DataFrame) -> Dict[str, Any]:
    """获取图表推荐（便捷函数）"""
    analyzer = DataTypeAnalyzer()
    return analyzer.get_chart_recommendation(df)