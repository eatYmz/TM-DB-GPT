import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException
import json
from datetime import datetime
import uuid

from dbgpt.serve.auth.service.auth import AuthService
from dbgpt.serve.auth.api.schemas import RegisterRequest, UserRequest
from dbgpt.serve.auth.models.user import User
from dbgpt.serve.auth.core.config import get_auth_settings
from dbgpt.serve.auth.core.security import get_password_hash

auth_settings = get_auth_settings()

# 测试数据
TEST_USER = {
    "username": "testuser",
    "password": "testpass123",
    "email": "test@example.com",
    "real_name": "Test User",
    "nick_name": "tester"
}

@pytest.fixture
def mock_user_dao():
    """Mock UserDao"""
    with patch('dbgpt.serve.auth.service.auth.UserDao') as mock:
        dao = Mock()
        dao.get_by_username.return_value = None
        dao.get_by_email.return_value = None
        
        def create_user(user):
            user.user_id = str(uuid.uuid4())
            return user
            
        dao.create_user.side_effect = create_user
        mock.return_value = dao
        yield dao

@pytest.fixture
def mock_redis():
    """Mock Redis客户端"""
    with patch('redis.from_url') as mock:
        redis_client = Mock()
        redis_client.get.return_value = None
        redis_client.setex.return_value = True
        redis_client.delete.return_value = True
        redis_client.pipeline.return_value.execute.return_value = None
        mock.return_value = redis_client
        yield redis_client

class TestAuthService:
    @pytest.fixture
    def auth_service(self, mock_redis, mock_user_dao):
        """创建 AuthService 实例"""
        return AuthService(redis_url="redis://localhost:6379/0")

    def test_register_success(self, auth_service):
        """测试成功注册"""
        register_data = RegisterRequest(**TEST_USER)
        response = auth_service.register(register_data)
        
        assert response.user.user_name == TEST_USER["username"]
        assert response.access_token is not None
        assert response.token_type == "bearer"

    def test_register_existing_username(self, auth_service, mock_user_dao):
        """测试注册用户名已存在"""
        mock_user_dao.get_by_username.return_value = User(
            user_name=TEST_USER["username"]
        )
        
        with pytest.raises(HTTPException) as exc:
            auth_service.register(RegisterRequest(**TEST_USER))
        assert exc.value.status_code == 400
        assert "Username already registered" in str(exc.value.detail)

    def test_login_success(self, auth_service, mock_user_dao):
        """测试成功登录"""
        # 创建一个真实的密码哈希
        hashed_password = get_password_hash(TEST_USER["password"])
        
        user = User(
            user_id="test123",
            user_name=TEST_USER["username"],
            password=hashed_password,  # 使用真实的密码哈希
            email=TEST_USER["email"]
        )
        mock_user_dao.get_by_username.return_value = user
        
        response = auth_service.login(TEST_USER["username"], TEST_USER["password"])
        
        assert response.access_token is not None
        assert response.user.user_name == TEST_USER["username"]

    def test_login_invalid_credentials(self, auth_service, mock_user_dao):
        """测试登录失败 - 无效凭据"""
        mock_user_dao.get_by_username.return_value = None
        
        with pytest.raises(HTTPException) as exc:
            auth_service.login("wrong_user", "wrong_pass")
        assert exc.value.status_code == 401
        assert "Incorrect username or password" in str(exc.value.detail)