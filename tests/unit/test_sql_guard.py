"""
SQL Guard 测试
"""
import pytest
from app.core.sql.guard import SQLValidator, SQLValidationResult, validate_readonly_sql


class TestSQLValidator:
    """SQL Validator 测试"""
    
    @pytest.fixture
    def validator(self):
        return SQLValidator()
    
    def test_validate_select(self, validator):
        """测试有效 SELECT"""
        result = validator.validate("SELECT * FROM orders")
        
        assert result.is_valid is True
    
    def test_validate_insert_blocked(self, validator):
        """测试 INSERT 被阻止"""
        result = validator.validate("INSERT INTO orders VALUES (1, 2)")
        
        assert result.is_valid is False
    
    def test_validate_update_blocked(self, validator):
        """测试 UPDATE 被阻止"""
        result = validator.validate("UPDATE orders SET status = 'closed'")
        
        assert result.is_valid is False
    
    def test_validate_delete_blocked(self, validator):
        """测试 DELETE 被阻止"""
        result = validator.validate("DELETE FROM orders")
        
        assert result.is_valid is False
    
    def test_validate_drop_blocked(self, validator):
        """测试 DROP 被阻止"""
        result = validator.validate("DROP TABLE orders")
        
        assert result.is_valid is False


class TestValidateReadonlySQL:
    """便捷函数测试"""
    
    def test_validate_readonly_sql_valid(self):
        """测试有效的只读 SQL"""
        sql = validate_readonly_sql("SELECT 1")
        
        assert sql is not None
    
    def test_validate_readonly_sql_invalid(self):
        """测试无效的只读 SQL"""
        with pytest.raises(Exception):
            validate_readonly_sql("DELETE FROM orders")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])