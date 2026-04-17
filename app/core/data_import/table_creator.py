"""
数据表创建模块

将 DataFrame 安全地写入 SQLite 数据库，同时更新白名单配置。
"""
from __future__ import annotations

import logging
import re
from typing import Optional

import pandas as pd
from sqlalchemy import create_engine, text

from app.core.data_import.sanitizer import (
    DataImportError,
    sanitize_table_name,
    sanitize_column_names,
    validate_dataframe,
)
from app.config.settings import get_settings

logger = logging.getLogger(__name__)


def import_dataframe_to_db(
    df: pd.DataFrame,
    table_name: str,
    if_exists: str = "replace",
) -> dict:
    """
    将 DataFrame 导入到数据库。

    安全策略：
    1. 表名/列名经过清洗
    2. 使用 SQLAlchemy 参数化写入（防注入）
    3. 自动将新表加入白名单

    Args:
        df: 要导入的数据
        table_name: 目标表名（会被清洗）
        if_exists: 'replace' 覆盖 / 'append' 追加 / 'fail' 已存在则报错

    Returns:
        dict: {"table_name": str, "rows": int, "columns": list}
    """
    # 清洗表名
    safe_name = sanitize_table_name(table_name)

    # 清洗列名
    df = df.copy()
    df.columns = sanitize_column_names(list(df.columns))

    # 验证
    validate_dataframe(df, safe_name)

    # 获取数据库连接
    settings = get_settings()
    db_url = settings.db_url

    # 数据导入需要可写连接，不使用只读模式
    writable_url = _make_writable_url(db_url)

    engine = create_engine(writable_url)

    try:
        # 使用 pandas to_sql（内部使用参数化 INSERT，防注入）
        df.to_sql(
            name=safe_name,
            con=engine,
            if_exists=if_exists,
            index=False,
        )

        # 获取实际写入行数
        with engine.connect() as conn:
            count_result = conn.execute(
                text(f"SELECT COUNT(*) FROM [{safe_name}]")
            )
            row_count = count_result.scalar()

        logger.info(f"成功导入表 '{safe_name}'：{row_count} 行, {len(df.columns)} 列")

        # 更新白名单
        _update_allowed_tables(safe_name)

        return {
            "table_name": safe_name,
            "rows": row_count,
            "columns": list(df.columns),
        }
    except Exception as e:
        logger.error(f"导入表 '{safe_name}' 失败: {e}")
        raise DataImportError(f"数据导入失败: {e}")
    finally:
        engine.dispose()


def _make_writable_url(db_url: str) -> str:
    """将只读 URL 转为可写 URL"""
    # 移除 mode=ro 参数
    url = re.sub(r"\?mode=ro&uri=true", "", db_url)
    url = re.sub(r"\?mode=ro", "", url)
    # 还原 file: 前缀（如有）
    url = url.replace("sqlite:///file:", "sqlite:///")
    return url


def _update_allowed_tables(table_name: str) -> None:
    """将新表添加到 SQL 校验器的白名单"""
    try:
        from app.core.sql.guard import DEFAULT_ALLOWED_TABLES
        DEFAULT_ALLOWED_TABLES.add(table_name)
        logger.info(f"已将表 '{table_name}' 添加到查询白名单")
    except Exception as e:
        logger.warning(f"更新白名单失败: {e}")


def get_user_tables() -> list[dict]:
    """获取当前数据库中的所有用户表信息"""
    settings = get_settings()
    db_url = settings.db_url

    # 同样用可写连接读取也行，但用只读也可以
    writable_url = _make_writable_url(db_url)
    engine = create_engine(writable_url)

    try:
        with engine.connect() as conn:
            result = conn.execute(text(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
                "AND name NOT LIKE 'chroma_%' ORDER BY name"
            ))
            tables = []
            for row in result:
                name = row[0]
                count_res = conn.execute(text(f"SELECT COUNT(*) FROM [{name}]"))
                count = count_res.scalar()
                tables.append({"name": name, "rows": count})
            return tables
    except Exception as e:
        logger.error(f"获取表信息失败: {e}")
        return []
    finally:
        engine.dispose()
