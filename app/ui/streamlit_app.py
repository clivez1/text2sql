"""
Text2SQL Agent Streamlit 应用

功能特性：
- 文件上传：支持 Excel、CSV、JSON、Markdown 表格导入数据库
- SQL 预览：先展示 SQL，用户确认后再执行
- 自然语言回答：默认用自然语言回答，可手动切换图表类型
- 数据导出：支持 PDF/Excel 导出
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from app.core.orchestrator.pipeline import (
    generate_sql_preview,
    execute_confirmed_sql,
    summarize_result_natural_language,
)
from app.core.chart.recommender import ChartRecommender, ChartType, ChartRecommendation
from app.ui.chart_renderer import render_chart
from app.ui.exporter import ExportManager


# 页面配置
st.set_page_config(
    page_title="Text2SQL Agent",
    layout="wide",
    page_icon="🔍",
)

# 标题
st.title("🔍 Text2SQL Agent")
st.caption("自然语言 → SQL → 数据库 → 智能可视化 | v4.0")

# ==================== 初始化 session_state ====================
for key, default in {
    "sql_preview": None,       # SQL 预览结果
    "result": None,            # 执行结果
    "nl_summary": None,        # 自然语言摘要
    "selected_chart": None,    # 用户选择的图表类型
}.items():
    if key not in st.session_state:
        st.session_state[key] = default


# ==================== 辅助函数 ====================

def _import_file(uploaded_file, table_name_input, if_exists_option):
    """处理文件上传导入"""
    from app.core.data_import.file_parser import parse_uploaded_file
    from app.core.data_import.table_creator import import_dataframe_to_db
    from app.core.data_import.sanitizer import DataImportError, sanitize_table_name

    with st.spinner("正在解析并导入数据..."):
        try:
            # 确定表名
            if table_name_input.strip():
                tname = table_name_input.strip()
            else:
                tname = uploaded_file.name.rsplit(".", 1)[0]
            tname = sanitize_table_name(tname)

            # 解析文件
            file_bytes = uploaded_file.getvalue()
            df = parse_uploaded_file(file_bytes, uploaded_file.name, tname)

            # 预览
            st.write(f"**预览**（前 5 行，共 {len(df)} 行 × {len(df.columns)} 列）：")
            st.dataframe(df.head(), use_container_width=True, hide_index=True)

            # 导入
            result = import_dataframe_to_db(df, tname, if_exists=if_exists_option)
            st.success(
                f"✅ 成功导入表 `{result['table_name']}`：{result['rows']} 行, "
                f"{len(result['columns'])} 列"
            )
        except DataImportError as e:
            st.error(f"❌ 导入失败: {e}")
        except Exception as e:
            st.error(f"❌ 导入异常: {e}")


def _show_tables():
    """显示数据库表信息"""
    try:
        from app.core.data_import.table_creator import get_user_tables
        tables = get_user_tables()
        if tables:
            for t in tables:
                st.text(f"• {t['name']} ({t['rows']} 行)")
        else:
            st.info("暂无数据表")
    except Exception:
        st.info("暂无数据表")


def _render_selected_chart(df: pd.DataFrame, chart_type_str: str, question: str):
    """根据用户选择的图表类型渲染图表"""
    recommender = ChartRecommender()
    recommendation = recommender.recommend(df, question)

    # 覆盖推荐的图表类型为用户选择的类型
    chart_type = ChartType(chart_type_str)
    recommendation = ChartRecommendation(
        chart_type=chart_type,
        x_column=recommendation.x_column,
        y_column=recommendation.y_column,
        y_columns=recommendation.y_columns,
        color_column=recommendation.color_column,
        confidence=1.0,
    )

    fig = render_chart(df, recommendation, height=400)
    if fig:
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning(f"无法使用 {chart_type_str} 类型渲染当前数据")


# ==================== 侧边栏：数据管理 ====================
with st.sidebar:
    st.header("📂 数据管理")

    # 文件上传
    st.subheader("上传数据文件")
    uploaded_file = st.file_uploader(
        "支持 Excel (.xlsx)、CSV、JSON、Markdown (.md)",
        type=["xlsx", "xls", "csv", "json", "md"],
        help="上传后自动解析并导入数据库，上传的数据可立即用于查询",
    )

    table_name_input = st.text_input(
        "目标表名（留空则从文件名提取）",
        value="",
        placeholder="例如：my_data",
    )

    if_exists_option = st.radio(
        "如果表已存在",
        options=["replace", "append", "fail"],
        format_func=lambda x: {"replace": "覆盖", "append": "追加", "fail": "报错"}[x],
        index=0,
    )

    if uploaded_file is not None:
        if st.button("📥 导入数据", type="primary"):
            _import_file(uploaded_file, table_name_input, if_exists_option)

    # 当前数据表概览
    st.divider()
    st.subheader("📋 数据库表")
    if st.button("🔄 刷新"):
        st.rerun()
    _show_tables()


# ==================== 主界面：查询 ====================
question = st.text_input(
    "请输入问题",
    value="上个月销售额最高的前5个产品是什么？",
    placeholder="例如：各城市的订单数量是多少？",
)

# ---- 第一步：生成 SQL 预览 ----
if st.button("🔍 生成 SQL", type="primary"):
    with st.spinner("正在生成 SQL..."):
        try:
            preview = generate_sql_preview(question)
            st.session_state.sql_preview = preview
            st.session_state.result = None
            st.session_state.nl_summary = None
            st.session_state.selected_chart = None
        except Exception as e:
            st.error(f"SQL 生成失败: {e}")

# ---- 展示 SQL 预览并等待确认 ----
if st.session_state.sql_preview and st.session_state.result is None:
    preview = st.session_state.sql_preview

    st.subheader("📝 SQL 预览")
    st.code(preview["sql"], language="sql")

    col_info, col_action = st.columns([3, 1])
    with col_info:
        st.caption(f"模式: {preview['mode']} | {preview['explanation'][:120]}")
        if preview["blocked_reason"]:
            st.warning(f"⚠️ {preview['blocked_reason']}")
    with col_action:
        if st.button("✅ 确认执行", type="primary"):
            with st.spinner("正在执行查询..."):
                try:
                    result = execute_confirmed_sql(preview)
                    st.session_state.result = result
                    # 生成自然语言摘要
                    st.session_state.nl_summary = summarize_result_natural_language(
                        result.question, result.result_preview, result.generated_sql
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"查询失败: {e}")

# ---- 展示结果 ----
if st.session_state.result is not None:
    result = st.session_state.result
    df = pd.DataFrame(result.result_preview)

    # SQL 信息（折叠）
    with st.expander("📝 SQL 语句", expanded=False):
        st.code(result.generated_sql, language="sql")
        st.caption(f"模式: {result.mode}")

    st.divider()

    # 自然语言回答（默认展示）
    st.subheader("💬 回答")
    if st.session_state.nl_summary:
        st.markdown(st.session_state.nl_summary)
    else:
        st.info("未能生成自然语言摘要")

    st.divider()

    # 数据表格
    st.subheader("📊 查询结果")
    if df.empty:
        st.info("查询结果为空")
    else:
        stats_cols = st.columns(4)
        stats_cols[0].metric("行数", len(df))
        stats_cols[1].metric("列数", len(df.columns))
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ---- 图表：用户手动选择类型 ----
    if not df.empty:
        st.divider()
        st.subheader("📈 数据可视化")

        chart_types = {
            "bar": "📊 柱状图",
            "line": "📈 折线图",
            "pie": "🥧 饼图",
            "scatter": "🔵 散点图",
        }

        chart_cols = st.columns(len(chart_types))
        for i, (ctype, label) in enumerate(chart_types.items()):
            if chart_cols[i].button(label, key=f"chart_{ctype}", use_container_width=True):
                st.session_state.selected_chart = ctype

        if st.session_state.selected_chart:
            _render_selected_chart(df, st.session_state.selected_chart, result.question)

    # ---- 导出 ----
    if not df.empty:
        st.divider()
        st.subheader("📥 导出")
        export_cols = st.columns([1, 1, 4])

        export_manager = ExportManager(title="Text2SQL Report")
        with export_cols[0]:
            excel_data = export_manager.export_excel(df)
            st.download_button(
                label="📥 导出 Excel",
                data=excel_data,
                file_name=export_manager.get_excel_filename(),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        with export_cols[1]:
            try:
                pdf_data = export_manager.export_pdf(
                    df,
                    sql=result.generated_sql,
                    question=result.question,
                )
                st.download_button(
                    label="📄 导出 PDF",
                    data=pdf_data,
                    file_name=export_manager.get_pdf_filename(),
                    mime="application/pdf",
                )
            except Exception as e:
                st.warning(f"PDF 导出不可用: {e}")


# 页脚
st.divider()
st.caption("Text2SQL Agent v4.0 | 文件上传 + SQL预览 + 自然语言回答 + 手动图表")