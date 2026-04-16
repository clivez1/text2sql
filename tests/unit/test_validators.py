"""
输入验证模块测试
"""
import pytest
from app.core.validators import (
    AskRequest,
    SchemaRequest,
    ExecuteSQLRequest,
    FileUpload,
    validate_question,
    validate_sql_safety,
)


class TestAskRequest:
    """查询请求测试"""
    
    def test_valid_question(self):
        """测试有效问题"""
        req = AskRequest(question="查询销售额最高的产品")
        
        assert req.question == "查询销售额最高的产品"
    
    def test_question_strip(self):
        """测试问题去除空白"""
        req = AskRequest(question="  测试问题  ")
        
        assert req.question == "测试问题"
    
    def test_empty_question(self):
        """测试空问题"""
        with pytest.raises(ValueError):
            AskRequest(question="")
    
    def test_question_with_sql_comment(self):
        """测试包含 SQL 注释的问题"""
        with pytest.raises(ValueError):
            AskRequest(question="查询--注释")
    
    def test_question_too_long(self):
        """测试过长问题"""
        long_question = "测试" * 300
        with pytest.raises(ValueError):
            AskRequest(question=long_question)
    
    def test_db_name_valid(self):
        """测试有效数据库名"""
        req = AskRequest(question="测试", db_name="my_database")
        
        assert req.db_name == "my_database"
    
    def test_db_name_invalid_characters(self):
        """测试无效数据库名"""
        with pytest.raises(ValueError):
            AskRequest(question="测试", db_name="my-database")


class TestSchemaRequest:
    """Schema 请求测试"""
    
    def test_schema_request(self):
        """测试 Schema 请求"""
        req = SchemaRequest(db_name="test_db")
        
        assert req.db_name == "test_db"


class TestExecuteSQLRequest:
    """SQL 执行请求测试"""
    
    def test_valid_select(self):
        """测试有效 SELECT"""
        req = ExecuteSQLRequest(sql="SELECT * FROM orders")
        
        assert req.sql == "SELECT * FROM orders"
    
    def test_non_select_rejected(self):
        """测试非 SELECT 被拒绝"""
        with pytest.raises(ValueError):
            ExecuteSQLRequest(sql="DELETE FROM orders")
    
    def test_dangerous_keyword_rejected(self):
        """测试危险关键字被拒绝"""
        with pytest.raises(ValueError):
            ExecuteSQLRequest(sql="SELECT * FROM orders; DROP TABLE orders")


class TestFileUpload:
    """文件上传测试"""
    
    def test_valid_filename(self):
        """测试有效文件名"""
        upload = FileUpload(
            filename="test.csv", 
            content_type="text/csv",
            size_bytes=1024
        )
        
        assert upload.filename == "test.csv"
    
    def test_invalid_extension(self):
        """测试无效扩展名"""
        with pytest.raises(ValueError):
            FileUpload(
                filename="test.exe", 
                content_type="application/octet-stream",
                size_bytes=1024
            )


class TestValidateQuestion:
    """便捷函数测试"""
    
    def test_validate_question_function(self):
        """测试 validate_question 函数"""
        result = validate_question("测试问题")
        
        assert result == "测试问题"


class TestValidateSQLSafety:
    """SQL 安全验证测试"""
    
    def test_safe_sql(self):
        """测试安全 SQL"""
        sql = validate_sql_safety("SELECT name FROM users WHERE id = 1")
        
        assert "SELECT" in sql
    
    def test_unsafe_sql_drop(self):
        """测试 DROP 被拒绝"""
        with pytest.raises(ValueError):
            validate_sql_safety("DROP TABLE users")
    
    def test_unsafe_sql_insert(self):
        """测试 INSERT 被拒绝"""
        with pytest.raises(ValueError):
            validate_sql_safety("INSERT INTO users VALUES (1, 'admin')")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])