"""
FastAPI 接口测试

测试 API 端点功能。
"""
import pytest
from fastapi.testclient import TestClient

from app.api.main import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


class TestRootEndpoint:
    """根路径测试"""
    
    def test_root(self, client):
        """测试根路径"""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Text2SQL Agent API"
        assert "version" in data
        assert "endpoints" in data


class TestHealthEndpoint:
    """健康检查测试"""
    
    def test_health(self, client):
        """测试健康检查"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["ok", "error"]
        assert "db_type" in data
        assert "latency_ms" in data
        assert "timestamp" in data


class TestSchemasEndpoint:
    """Schema 端点测试"""
    
    def test_schemas(self, client):
        """测试获取 Schema"""
        response = client.get("/schemas")
        
        assert response.status_code == 200
        data = response.json()
        assert "tables" in data
        assert isinstance(data["tables"], dict)


class TestSchemaModels:
    """Schema 模型与 OpenAPI 测试"""

    def test_openapi_examples_render(self, client):
        """测试 OpenAPI 中仍能看到请求示例"""
        response = client.get("/openapi.json")

        assert response.status_code == 200
        schema = response.json()
        ask_request = schema["components"]["schemas"]["AskRequest"]
        question_prop = ask_request["properties"]["question"]
        session_prop = ask_request["properties"]["session_id"]
        assert question_prop["example"] == "上个月销售额最高的前5个产品是什么？"
        assert session_prop["example"] == "user-001"


class TestAskEndpoint:
    """查询端点测试"""
    
    def test_ask_post(self, client):
        """测试 POST /ask"""
        response = client.post(
            "/ask",
            json={
                "question": "查询所有产品",
                "explain": True,
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "question" in data
        assert "generated_sql" in data
    
    def test_ask_get(self, client):
        """测试 GET /ask"""
        response = client.get("/ask?question=查询所有产品")
        
        assert response.status_code == 200
        data = response.json()
        assert "question" in data
        assert data["question"] == "查询所有产品"
    
    def test_ask_with_invalid_question(self, client):
        """测试无效问题"""
        response = client.post(
            "/ask",
            json={"question": ""}
        )
        
        # 应该返回 422 (验证错误) 或 200 (带错误信息)
        assert response.status_code in [200, 422]


class TestErrorResponse:
    """错误响应测试"""
    
    def test_404(self, client):
        """测试 404 响应"""
        response = client.get("/nonexistent")
        
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])