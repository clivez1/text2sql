"""
文件解析模块

将上传的 Excel、JSON、Markdown、CSV 文件解析为 pandas DataFrame。
"""
from __future__ import annotations

import io
import re
from typing import Optional

import pandas as pd

from app.core.data_import.sanitizer import (
    DataImportError,
    validate_file_size,
    sanitize_column_names,
    validate_dataframe,
)


def parse_uploaded_file(
    file_bytes: bytes,
    filename: str,
    table_name: str = "",
) -> pd.DataFrame:
    """
    解析上传文件为 DataFrame。

    支持格式：
    - .xlsx / .xls (Excel)
    - .csv
    - .json
    - .md (Markdown 表格)

    Args:
        file_bytes: 文件内容字节
        filename: 原始文件名（用于检测格式）
        table_name: 目标表名（用于验证）

    Returns:
        清洗后的 DataFrame
    """
    validate_file_size(len(file_bytes))

    ext = _get_extension(filename)

    parsers = {
        ".xlsx": _parse_excel,
        ".xls": _parse_excel,
        ".csv": _parse_csv,
        ".json": _parse_json,
        ".md": _parse_markdown,
    }

    parser = parsers.get(ext)
    if parser is None:
        supported = ", ".join(parsers.keys())
        raise DataImportError(f"不支持的文件格式: {ext}（支持 {supported}）")

    try:
        df = parser(file_bytes)
    except DataImportError:
        raise
    except Exception as e:
        raise DataImportError(f"文件解析失败: {e}")

    # 清洗列名
    df.columns = sanitize_column_names(list(df.columns))

    # 验证数据
    validate_dataframe(df, table_name)

    return df


def _get_extension(filename: str) -> str:
    """提取小写扩展名"""
    if "." not in filename:
        raise DataImportError("文件名缺少扩展名，无法识别格式")
    return "." + filename.rsplit(".", 1)[-1].lower()


def _parse_excel(file_bytes: bytes) -> pd.DataFrame:
    """解析 Excel 文件"""
    buf = io.BytesIO(file_bytes)
    try:
        df = pd.read_excel(buf, engine="openpyxl")
    except Exception:
        # 尝试 xls 格式
        buf.seek(0)
        df = pd.read_excel(buf, engine=None)
    return df


def _parse_csv(file_bytes: bytes) -> pd.DataFrame:
    """解析 CSV 文件"""
    buf = io.BytesIO(file_bytes)
    # 自动检测编码
    try:
        df = pd.read_csv(buf, encoding="utf-8")
    except UnicodeDecodeError:
        buf.seek(0)
        df = pd.read_csv(buf, encoding="gbk")
    return df


def _parse_json(file_bytes: bytes) -> pd.DataFrame:
    """
    解析 JSON 文件。

    支持：
    - Array of objects: [{"col1": val1, ...}, ...]
    - Object with array values: {"col1": [...], "col2": [...]}
    """
    text = file_bytes.decode("utf-8")
    try:
        df = pd.read_json(io.StringIO(text))
    except ValueError:
        # 尝试 records 方向
        df = pd.read_json(io.StringIO(text), orient="records")
    return df


def _parse_markdown(file_bytes: bytes) -> pd.DataFrame:
    """
    解析 Markdown 表格。

    支持标准 GFM 格式:
    | col1 | col2 |
    |------|------|
    | val1 | val2 |
    """
    text = file_bytes.decode("utf-8")
    lines = [line.strip() for line in text.strip().split("\n") if line.strip()]

    # 找到表格部分
    table_lines = []
    for line in lines:
        if "|" in line:
            table_lines.append(line)

    if len(table_lines) < 2:
        raise DataImportError("未找到有效的 Markdown 表格（需要表头和至少一行数据）")

    # 解析表头
    header_line = table_lines[0]
    headers = [cell.strip() for cell in header_line.strip("|").split("|")]
    headers = [h for h in headers if h]

    # 跳过分隔行
    data_lines = []
    for line in table_lines[1:]:
        # 跳过分隔行 (---、:---:、---: 等)
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if all(re.match(r"^:?-+:?$", c) for c in cells if c):
            continue
        data_lines.append(cells)

    if not data_lines:
        raise DataImportError("Markdown 表格无数据行")

    # 构建 DataFrame
    rows = []
    for cells in data_lines:
        # 对齐列数
        row = [c.strip() for c in cells if c is not None]
        while len(row) < len(headers):
            row.append("")
        rows.append(row[: len(headers)])

    return pd.DataFrame(rows, columns=headers)
