"""
数据导入模块单元测试
"""
from __future__ import annotations

import pytest
import pandas as pd

from app.core.data_import.sanitizer import (
    sanitize_table_name,
    sanitize_column_names,
    validate_file_size,
    validate_dataframe,
    DataImportError,
    MAX_FILE_SIZE_BYTES,
)
from app.core.data_import.file_parser import (
    parse_uploaded_file,
    _parse_markdown,
    _parse_json,
    _parse_csv,
    _get_extension,
)


# ==================== sanitizer tests ====================

class TestSanitizeTableName:
    def test_normal_name(self):
        assert sanitize_table_name("my_table") == "my_table"

    def test_chinese_name(self):
        assert sanitize_table_name("销售数据") == "销售数据"

    def test_spaces_replaced(self):
        assert sanitize_table_name("my table") == "my_table"

    def test_special_chars_replaced(self):
        assert sanitize_table_name("my-table!@#") == "my_table"

    def test_starts_with_digit(self):
        result = sanitize_table_name("123abc")
        assert result.startswith("t_")

    def test_sql_keyword(self):
        result = sanitize_table_name("select")
        assert result != "select"
        assert result == "t_select"

    def test_empty_raises(self):
        with pytest.raises(DataImportError):
            sanitize_table_name("")

    def test_long_name_truncated(self):
        result = sanitize_table_name("a" * 100)
        assert len(result) <= 64


class TestSanitizeColumnNames:
    def test_normal_columns(self):
        result = sanitize_column_names(["name", "age", "city"])
        assert result == ["name", "age", "city"]

    def test_special_chars(self):
        result = sanitize_column_names(["col-1", "col 2", "col@3"])
        assert result == ["col_1", "col_2", "col_3"]

    def test_duplicates(self):
        result = sanitize_column_names(["name", "name", "name"])
        assert len(result) == 3
        assert len(set(result)) == 3

    def test_sql_keyword_column(self):
        result = sanitize_column_names(["select", "from"])
        assert "select" not in [r.lower() for r in result]

    def test_digit_prefix(self):
        result = sanitize_column_names(["1col"])
        assert result[0].startswith("c_")


class TestValidateFileSize:
    def test_valid_size(self):
        validate_file_size(1000)  # should not raise

    def test_too_large(self):
        with pytest.raises(DataImportError, match="文件大小超过限制"):
            validate_file_size(MAX_FILE_SIZE_BYTES + 1)


class TestValidateDataframe:
    def test_empty_df_raises(self):
        with pytest.raises(DataImportError, match="内容为空"):
            validate_dataframe(pd.DataFrame(), "test")

    def test_valid_df(self):
        df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
        validate_dataframe(df, "test")  # should not raise

    def test_injection_detected(self):
        df = pd.DataFrame({"a": ["normal", "'; drop table users --"]})
        with pytest.raises(DataImportError, match="注入"):
            validate_dataframe(df, "test")


# ==================== file_parser tests ====================

class TestGetExtension:
    def test_xlsx(self):
        assert _get_extension("data.xlsx") == ".xlsx"

    def test_csv(self):
        assert _get_extension("file.CSV") == ".csv"

    def test_no_extension_raises(self):
        with pytest.raises(DataImportError):
            _get_extension("noext")


class TestParseCSV:
    def test_basic_csv(self):
        csv_bytes = b"name,age\nAlice,30\nBob,25"
        df = _parse_csv(csv_bytes)
        assert len(df) == 2
        assert "name" in df.columns


class TestParseJSON:
    def test_records_format(self):
        json_bytes = b'[{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]'
        df = _parse_json(json_bytes)
        assert len(df) == 2

    def test_dict_format(self):
        json_bytes = b'{"name": ["Alice", "Bob"], "age": [30, 25]}'
        df = _parse_json(json_bytes)
        assert len(df) == 2


class TestParseMarkdown:
    def test_basic_table(self):
        md = b"| name | age |\n|------|-----|\n| Alice | 30 |\n| Bob | 25 |"
        df = _parse_markdown(md)
        assert len(df) == 2
        assert "name" in df.columns

    def test_no_table_raises(self):
        with pytest.raises(DataImportError):
            _parse_markdown(b"just some text without a table")


class TestParseUploadedFile:
    def test_unsupported_format(self):
        with pytest.raises(DataImportError, match="不支持"):
            parse_uploaded_file(b"data", "file.txt")

    def test_csv_integration(self):
        csv_bytes = b"col1,col2\n1,2\n3,4"
        df = parse_uploaded_file(csv_bytes, "test.csv", "test_table")
        assert len(df) == 2

    def test_oversized_file(self):
        with pytest.raises(DataImportError, match="文件大小"):
            parse_uploaded_file(b"x" * (MAX_FILE_SIZE_BYTES + 1), "big.csv")
