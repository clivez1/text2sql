"""
Text2SQL Agent Streamlit 应用

Week 3 更新：
- 使用 Plotly 交互式图表
- 集成 ChartRecommender 智能推荐
- 支持 PDF/Excel 导出
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from app.core.orchestrator.pipeline import ask_question
from app.core.chart.recommender import ChartRecommender, ChartType
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
st.caption("自然语言 → SQL → 数据库 → 智能可视化 | Week 3 Enhanced")

# 初始化
if "result" not in st.session_state:
    st.session_state.result = None


def render_results():
    """渲染查询结果"""
    result = st.session_state.result
    if not result:
        return
    
    df = pd.DataFrame(result.result_preview)
    
    # 第一行：SQL 和元信息
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("📝 SQL")
        st.code(result.generated_sql, language="sql")
        
        # 元信息
        meta_cols = st.columns(3)
        meta_cols[0].metric("模式", result.mode)
        if result.blocked_reason:
            meta_cols[1].warning(f"⚠️ {result.blocked_reason}")
    
    with col2:
        st.subheader("💡 解释")
        st.write(result.sql_explanation)
    
    st.divider()
    
    # 第二行：数据表格
    st.subheader("📊 查询结果")
    
    if df.empty:
        st.info("查询结果为空")
        return
    
    # 数据统计
    stats_cols = st.columns(4)
    stats_cols[0].metric("行数", len(df))
    stats_cols[1].metric("列数", len(df.columns))
    
    # 数据表格
    st.dataframe(df, use_container_width=True, hide_index=True)
    
    # 第三行：智能图表
    st.divider()
    st.subheader("📈 智能图表")
    
    # 使用 ChartRecommender 推荐图表
    recommender = ChartRecommender()
    recommendation = recommender.recommend(df, result.question)
    
    # 显示推荐信息
    rec_cols = st.columns([3, 1])
    rec_cols[0].info(f"推荐图表: **{recommendation.chart_type.value.upper()}** | {recommendation.reason}")
    rec_cols[1].metric("置信度", f"{recommendation.confidence:.0%}")
    
    # 渲染 Plotly 图表
    if recommendation.chart_type != ChartType.TABLE:
        fig = render_chart(df, recommendation, height=400)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
            
            # 显示备选图表
            if recommendation.alternatives:
                with st.expander("🔄 备选图表"):
                    alt_cols = st.columns(len(recommendation.alternatives))
                    for i, alt in enumerate(recommendation.alternatives):
                        alt_cols[i].button(
                            f"{alt['chart_type'].upper()}",
                            key=f"alt_{i}",
                            help=alt.get('reason', ''),
                        )
    else:
        st.info("当前数据不适合可视化，建议查看表格")
    
    # 第四行：导出功能
    st.divider()
    st.subheader("📥 导出")
    
    export_cols = st.columns([1, 1, 4])
    
    with export_cols[0]:
        # Excel 导出
        export_manager = ExportManager(title="Text2SQL Report")
        excel_data = export_manager.export_excel(df)
        st.download_button(
            label="📥 导出 Excel",
            data=excel_data,
            file_name=export_manager.get_excel_filename(),
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
    
    with export_cols[1]:
        # PDF 导出
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


# 主界面
question = st.text_input(
    "请输入问题",
    value="上个月销售额最高的前5个产品是什么？",
    placeholder="例如：各城市的订单数量是多少？",
)

if st.button("🚀 执行查询", type="primary"):
    with st.spinner("正在生成 SQL 并查询..."):
        try:
            result = ask_question(question)
            st.session_state.result = result
        except Exception as e:
            st.error(f"查询失败: {e}")

# 渲染结果
render_results()

# 页脚
st.divider()
st.caption("Text2SQL Agent v3.0 | Local-first Text2SQL + Plotly + Streamlit")