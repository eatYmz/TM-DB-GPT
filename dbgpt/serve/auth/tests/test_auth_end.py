import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock

from dbgpt.serve.auth.middleware.auth import AuthMiddleware
from dbgpt.serve.auth.api.endpoint import router as auth_router
from dbgpt.serve.auth.api.schemas import UserRequest

# 测试数据
TEST_USER = UserRequest(
    user_id="test123",
    username="testuser",
    email="test@example.com",
    role="user",
    status="active"
)

@pytest.fixture
def mock_auth_service():
    service = Mock()
    # 模拟登录方法
    service.login = AsyncMock(return_value={
        "access_token": "fake_token",
        "token_type": "bearer"
    })
    return service

@pytest.fixture
def app(mock_auth_service):
    app = FastAPI()
    # 添加中间件
    app.add_middleware(
        AuthMiddleware,
        exclude_paths=["/auth/login", "/auth/register"],
        auth_service=mock_auth_service
    )
    # 添加路由
    app.include_router(auth_router, prefix="/auth")
    return app

@pytest.fixture
def client(app):
    return TestClient(app)

class TestAuthMiddleware:
    def test_exclude_paths(self, client, mock_auth_service):
        """测试排除路径"""
        # 设置预期的返回值
        mock_auth_service.login.return_value = {
            "access_token": "fake_token",
            "token_type": "bearer"
        }
        
        response = client.post("/auth/login", json={
            "username": "testuser",
            "password": "password123"
        })
        
        assert response.status_code == 200
        assert "access_token" in response.json()