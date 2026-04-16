"""
数据导出模块

支持 PDF 和 Excel 格式导出。
"""
from __future__ import annotations

import io
from datetime import datetime
from typing import Optional, List, Any

import pandas as pd

# 延迟导入以避免启动时加载
# from fpdf import FPDF
# import openpyxl


class ExportManager:
    """导出管理器"""
    
    def __init__(self, title: str = "Text2SQL Report"):
        self.title = title
        self.created_at = datetime.now()
    
    def export_excel(
        self,
        df: pd.DataFrame,
        sheet_name: str = "数据",
        include_chart: bool = False,
    ) -> bytes:
        """
        导出为 Excel 文件
        
        Args:
            df: 数据
            sheet_name: 工作表名称
            include_chart: 是否包含图表
            
        Returns:
            Excel 文件字节
        """
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
            # 自动调整列宽
            worksheet = writer.sheets[sheet_name]
            for idx, col in enumerate(df.columns):
                max_length = max(
                    df[col].astype(str).str.len().max(),
                    len(str(col))
                ) + 2
                # openpyxl 列宽是字符宽度的约 1.2 倍
                worksheet.column_dimensions[
                    chr(65 + idx) if idx < 26 else f"{chr(65 + idx // 26 - 1)}{chr(65 + idx % 26)}"
                ].width = min(max_length * 1.2, 50)
        
        return output.getvalue()
    
    def export_pdf(
        self,
        df: pd.DataFrame,
        sql: Optional[str] = None,
        question: Optional[str] = None,
    ) -> bytes:
        """
        导出为 PDF 文件
        
        Args:
            df: 数据
            sql: SQL 语句
            question: 用户问题
            
        Returns:
            PDF 文件字节
        """
        from fpdf import FPDF
        
        pdf = FPDF(orientation='L', unit='mm', format='A4')
        pdf.add_page()
        pdf.add_font('DejaVu', '', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', uni=True)
        
        # 标题
        pdf.set_font('DejaVu', '', 16)
        pdf.cell(0, 10, self.title, ln=True, align='C')
        
        # 时间
        pdf.set_font('DejaVu', '', 10)
        pdf.cell(0, 8, f"生成时间: {self.created_at.strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='R')
        
        # 问题
        if question:
            pdf.set_font('DejaVu', '', 12)
            pdf.cell(0, 10, f"问题: {question}", ln=True)
        
        # SQL
        if sql:
            pdf.set_font('DejaVu', '', 10)
            pdf.multi_cell(0, 6, f"SQL: {sql}")
            pdf.ln(5)
        
        # 数据表格
        pdf.set_font('DejaVu', '', 9)
        
        # 计算列宽
        page_width = 270  # A4 横向有效宽度
        num_cols = len(df.columns)
        col_width = min(60, page_width / num_cols)
        
        # 表头
        pdf.set_fill_color(200, 220, 255)
        for col in df.columns:
            pdf.cell(col_width, 8, str(col)[:20], border=1, fill=True, align='C')
        pdf.ln()
        
        # 数据行（最多 50 行）
        pdf.set_fill_color(255, 255, 255)
        max_rows = min(len(df), 50)
        for idx, row in df.head(max_rows).iterrows():
            for val in row:
                text = str(val)[:25] if pd.notna(val) else ""
                pdf.cell(col_width, 7, text, border=1, align='L')
            pdf.ln()
        
        # 总行数
        if len(df) > max_rows:
            pdf.ln(5)
            pdf.set_font('DejaVu', '', 10)
            pdf.cell(0, 8, f"... 共 {len(df)} 行数据，已截断显示前 {max_rows} 行", ln=True)
        
        return pdf.output(dest='S').encode('latin-1')
    
    def get_excel_filename(self, prefix: str = "text2sql") -> str:
        """生成 Excel 文件名"""
        timestamp = self.created_at.strftime('%Y%m%d_%H%M%S')
        return f"{prefix}_{timestamp}.xlsx"
    
    def get_pdf_filename(self, prefix: str = "text2sql") -> str:
        """生成 PDF 文件名"""
        timestamp = self.created_at.strftime('%Y%m%d_%H%M%S')
        return f"{prefix}_{timestamp}.pdf"


# 便捷函数
def export_to_excel(df: pd.DataFrame, sheet_name: str = "数据") -> bytes:
    """导出为 Excel"""
    manager = ExportManager()
    return manager.export_excel(df, sheet_name)


def export_to_pdf(
    df: pd.DataFrame,
    sql: Optional[str] = None,
    question: Optional[str] = None,
) -> bytes:
    """导出为 PDF"""
    manager = ExportManager()
    return manager.export_pdf(df, sql, question)