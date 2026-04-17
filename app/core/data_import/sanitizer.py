"""
数据导入安全验证模块

防止 SQL 注入和非法数据：
- 表名/列名只允许字母、数字、下划线、中文
- 文件大小限制
- 数据类型验证
- 敏感内容过滤
"""
from __future__ import annotations

import re
from typing import List, Optional

# 最大上传文件大小 (10 MB)
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024

# 最大行数
MAX_ROW_COUNT = 50_000

# 最大列数
MAX_COLUMN_COUNT = 100

# 表名/列名合法字符：字母、数字、下划线、中文
_SAFE_NAME_RE = re.compile(r"^[\w\u4e00-\u9fff]+$")

# SQL 关键字黑名单（不允许作为表名/列名）
_SQL_KEYWORDS = {
    "select", "insert", "update", "delete", "drop", "alter", "create",
    "table", "index", "from", "where", "join", "union", "exec", "execute",
    "truncate", "grant", "revoke", "commit", "rollback", "pragma",
}


class DataImportError(Exception):
    """数据导入错误"""
    pass


def validate_file_size(file_size: int) -> None:
    """验证文件大小"""
    if file_size > MAX_FILE_SIZE_BYTES:
        max_mb = MAX_FILE_SIZE_BYTES / (1024 * 1024)
        raise DataImportError(f"文件大小超过限制（最大 {max_mb:.0f} MB）")


def sanitize_table_name(name: str) -> str:
    """
    清洗表名：
    1. 去除首尾空格
    2. 替换非法字符为下划线
    3. 验证不为 SQL 关键字
    4. 长度限制
    """
    if not name or not name.strip():
        raise DataImportError("表名不能为空")

    # 替换空格和特殊字符
    cleaned = re.sub(r"[^\w\u4e00-\u9fff]", "_", name.strip())
    # 移除连续下划线
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    # 确保不以数字开头
    if cleaned and cleaned[0].isdigit():
        cleaned = f"t_{cleaned}"

    if not cleaned:
        raise DataImportError(f"无效的表名: {name!r}")

    if len(cleaned) > 64:
        cleaned = cleaned[:64]

    if cleaned.lower() in _SQL_KEYWORDS:
        cleaned = f"t_{cleaned}"

    return cleaned


def sanitize_column_names(columns: List[str]) -> List[str]:
    """
    清洗列名列表：
    1. 去除非法字符
    2. 去重（加后缀）
    3. 验证不为 SQL 关键字
    """
    result = []
    seen = set()

    for col in columns:
        cleaned = re.sub(r"[^\w\u4e00-\u9fff]", "_", str(col).strip())
        cleaned = re.sub(r"_+", "_", cleaned).strip("_")

        if not cleaned:
            cleaned = "col"

        if cleaned[0].isdigit():
            cleaned = f"c_{cleaned}"

        if cleaned.lower() in _SQL_KEYWORDS:
            cleaned = f"c_{cleaned}"

        if len(cleaned) > 64:
            cleaned = cleaned[:64]

        # 去重
        original = cleaned
        counter = 1
        while cleaned.lower() in seen:
            cleaned = f"{original}_{counter}"
            counter += 1

        seen.add(cleaned.lower())
        result.append(cleaned)

    return result


def validate_dataframe(df, table_name: str) -> None:
    """验证 DataFrame 是否安全导入"""
    import pandas as pd

    if not isinstance(df, pd.DataFrame):
        raise DataImportError("解析结果不是有效的表格数据")

    if df.empty:
        raise DataImportError("文件内容为空，无数据可导入")

    if len(df) > MAX_ROW_COUNT:
        raise DataImportError(f"数据行数 ({len(df)}) 超过限制（最大 {MAX_ROW_COUNT} 行）")

    if len(df.columns) > MAX_COLUMN_COUNT:
        raise DataImportError(f"数据列数 ({len(df.columns)}) 超过限制（最大 {MAX_COLUMN_COUNT} 列）")

    # 检查是否有可能的注入字符串
    for col in df.select_dtypes(include=["object"]).columns:
        sample = df[col].dropna().head(100)
        for val in sample:
            val_str = str(val).lower()
            # 检测包含 SQL 注入模式的值
            if any(pattern in val_str for pattern in ["'; drop", "-- ", "/*", "*/", "xp_", "exec("]):
                raise DataImportError(
                    f"列 '{col}' 中检测到疑似 SQL 注入内容，请检查数据"
                )
