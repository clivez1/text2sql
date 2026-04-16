"""
错误处理模块测试
"""
import pytest
from app.core.errors import (
    AppError,
    ErrorCode,
    ValidationError,
    InvalidQuestionError,
    SQLGenerationError,
    LLMError,
    DatabaseError,
)


class TestErrorCode:
    """错误码测试"""
    
    def test_error_codes_exist(self):
        """测试错误码存在"""
        assert ErrorCode.INVALID_QUESTION.value == 1001
        assert ErrorCode.LLM_ERROR.value == 1004
        assert ErrorCode.DATABASE_ERROR.value == 3005


class TestAppError:
    """基础错误测试"""
    
    def test_create_error(self):
        """测试创建错误"""
        error = AppError(
            code=ErrorCode.LLM_ERROR,
            message="LLM call failed",
        )
        
        assert error.code == ErrorCode.LLM_ERROR
        assert error.message == "LLM call failed"
    
    def test_error_str(self):
        """测试错误字符串表示"""
        error = AppError(
            code=ErrorCode.VALIDATION_ERROR,
            message="Invalid input",
        )
        
        error_str = str(error)
        
        assert "Invalid input" in error_str


class TestValidationError:
    """验证错误测试"""
    
    def test_validation_error(self):
        """测试验证错误"""
        error = ValidationError("Question is empty")
        
        assert "Question is empty" in str(error)
        assert error.code == ErrorCode.VALIDATION_ERROR


class TestInvalidQuestionError:
    """无效问题错误测试"""
    
    def test_invalid_question_error(self):
        """测试无效问题错误"""
        error = InvalidQuestionError("Question too long")
        
        assert "Question too long" in str(error)
        assert error.code == ErrorCode.INVALID_QUESTION


class TestLLMError:
    """LLM 错误测试"""
    
    def test_llm_error(self):
        """测试 LLM 错误"""
        error = LLMError("API key invalid")
        
        assert "API key invalid" in str(error)
        assert error.code == ErrorCode.LLM_ERROR


class TestDatabaseError:
    """数据库错误测试"""
    
    def test_database_error(self):
        """测试数据库错误"""
        error = DatabaseError("Connection failed")
        
        assert "Connection failed" in str(error)
        assert error.code == ErrorCode.DATABASE_ERROR


if __name__ == "__main__":
    pytest.main([__file__, "-v"])