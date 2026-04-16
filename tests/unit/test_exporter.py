import pandas as pd

from app.ui.exporter import ExportManager, export_to_excel, export_to_pdf


def test_export_excel_returns_bytes():
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    data = export_to_excel(df)
    assert isinstance(data, bytes)
    assert len(data) > 0


def test_export_manager_filenames():
    manager = ExportManager()
    assert manager.get_excel_filename().endswith(".xlsx")
    assert manager.get_pdf_filename().endswith(".pdf")


def test_export_excel_with_long_columns():
    df = pd.DataFrame({"very_long_column_name": ["abc", "def"]})
    manager = ExportManager()
    data = manager.export_excel(df)
    assert isinstance(data, bytes)
    assert len(data) > 0


def test_export_pdf_returns_bytes_with_context():
    df = pd.DataFrame({"name": ["Alice", "Bob"], "amount": [10, 20]})
    manager = ExportManager(title="Sales Report")
    data = manager.export_pdf(df, sql="SELECT * FROM orders", question="订单列表")
    assert isinstance(data, bytes)
    assert len(data) > 100


def test_export_pdf_truncates_large_dataframe():
    df = pd.DataFrame({"id": list(range(60)), "name": [f"user_{i}" for i in range(60)]})
    data = export_to_pdf(df)
    assert isinstance(data, bytes)
    assert len(data) > 100
