"""
Pipeline 新功能单元测试：SQL 预览确认 + 自然语言摘要
"""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock

import pandas as pd

from app.core.orchestrator.pipeline import (
    generate_sql_preview,
    execute_confirmed_sql,
    summarize_result_natural_language,
    _template_summarize,
)


class TestGenerateSqlPreview:
    @patch("app.core.orchestrator.pipeline.generate_sql")
    @patch("app.core.orchestrator.pipeline.start_request", return_value="trace-1")
    def test_returns_preview_dict(self, mock_start, mock_gen):
        mock_gen.return_value = (
            "SELECT * FROM orders",
            "查询所有订单",
            "fallback",
            None,
        )
        result = generate_sql_preview("所有订单")
        assert result["sql"] == "SELECT * FROM orders"
        assert result["question"] == "所有订单"
        assert result["mode"] == "fallback"
        assert "trace_id" in result
        assert "generate_ms" in result


class TestExecuteConfirmedSql:
    @patch("app.core.orchestrator.pipeline.run_query")
    def test_executes_and_returns_result(self, mock_run):
        mock_run.return_value = pd.DataFrame({"id": [1, 2], "name": ["a", "b"]})
        preview = {
            "sql": "SELECT * FROM orders",
            "question": "所有订单",
            "explanation": "test",
            "mode": "fallback",
            "blocked_reason": None,
            "trace_id": "t1",
            "generate_ms": 10.0,
        }
        result = execute_confirmed_sql(preview)
        assert result.generated_sql == "SELECT * FROM orders"
        assert len(result.result_preview) == 2

    @patch("app.core.orchestrator.pipeline.run_query")
    def test_empty_result(self, mock_run):
        mock_run.return_value = pd.DataFrame()
        preview = {
            "sql": "SELECT 1",
            "question": "test",
            "explanation": "test",
            "mode": "fallback",
            "blocked_reason": None,
            "trace_id": "t2",
            "generate_ms": 5.0,
        }
        result = execute_confirmed_sql(preview)
        assert result.result_preview == []
        assert result.chart_config is None


class TestTemplateSummarize:
    def test_basic_summary(self):
        df = pd.DataFrame({"product": ["A", "B"], "sales": [100, 200]})
        summary = _template_summarize("销售数据", df)
        assert "2 条记录" in summary
        assert "sales" in summary

    def test_empty_df(self):
        result = summarize_result_natural_language("test", [], "SELECT 1")
        assert "为空" in result


class TestSummarizeResultNaturalLanguage:
    def test_with_data(self):
        records = [{"name": "A", "value": 10}]
        result = summarize_result_natural_language("test", records, "SELECT 1")
        assert len(result) > 0
