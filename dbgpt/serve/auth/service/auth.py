from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import redis
import json
import uuid

from dbgpt.serve.auth.api.schemas import UserRequest, RegisterRequest, AuthResponse
from dbgpt.serve.auth.core.config import get_auth_settings
from dbgpt.serve.auth.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    verify_token,
    oauth2_scheme
)
from dbgpt.serve.auth.models.user import User
from dbgpt.serve.auth.dao.user_dao import UserDao

auth_settings = get_auth_settings()

class RedisSessionManager:
    """Redis会话管理器"""
    def __init__(self, redis_url: str):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        self.prefix = "auth:session:"
        self.user_prefix = "auth:user:"
    
    def store_user_session(self, token: str, user_info: dict, expire_minutes: int):
        """存储用户会话信息"""
        session_key = f"{self.prefix}{token}"
        user_key = f"{self.user_prefix}{user_info['user_id']}"
        
        pipe = self.redis_client.pipeline()
        # 存储会话信息
        pipe.setex(
            session_key,
            timedelta(minutes=expire_minutes),
            json.dumps({
                "user_info": user_info,
                "created_at": datetime.utcnow().isoformat(),
                "last_activity": datetime.utcnow().isoformat()
            })
        )
        # 存储用户活跃token
        pipe.sadd(f"{user_key}:tokens", token)
        pipe.execute()
    
    def get_user_session(self, token: str) -> Optional[dict]:
        """获取用户会话信息"""
        session_key = f"{self.prefix}{token}"
        session_data = self.redis_client.get(session_key)
        if session_data:
            # 更新最后活动时间
            session_info = json.loads(session_data)
            session_info["last_activity"] = datetime.utcnow().isoformat()
            self.redis_client.setex(
                session_key,
                timedelta(minutes=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES),
                json.dumps(session_info)
            )
            return session_info["user_info"]
        return None
    
    def remove_session(self, token: str, user_id: str):
        """移除用户会话"""
        pipe = self.redis_client.pipeline()
        # 删除会话信息
        pipe.delete(f"{self.prefix}{token}")
        # 从用户活跃token中移除
        pipe.srem(f"{self.user_prefix}{user_id}:tokens", token)
        pipe.execute()

class AuthService:
    def __init__(self, redis_url: str):
        self.user_dao = UserDao()
        self.session_manager = RedisSessionManager(redis_url)


    def authenticate_user(self, username: str, password: str) -> User:
        """验证用户凭据"""
        user = self.user_dao.get_by_username(username)
        if not user or not verify_password(password, user.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password"
            )
        return user

    def register(self, register_data: RegisterRequest) -> AuthResponse:
        """用户注册"""
        # 检查是否允许注册
        if not auth_settings.ALLOW_REGISTRATION:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Registration is not allowed"
            )
        
        # 检查用户名是否已存在
        if self.user_dao.get_by_username(register_data.username):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        # 检查邮箱是否已存在
        if register_data.email and self.user_dao.get_by_email(register_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # 创建新用户
        user = User(
            user_id=str(uuid.uuid4()),  # 生成唯一用户ID
            user_name=register_data.username,
            password=get_password_hash(register_data.password),
            email=register_data.email,
            real_name=register_data.real_name,
            nick_name=register_data.nick_name or register_data.username,
            role=auth_settings.DEFAULT_ROLE,
            status="active"
        )
        
        try:
            user = self.user_dao.create_user(user)
            access_token = create_access_token(user.user_id)
            user_info = user.to_user_request().dict()
            
            # 存储会话信息到Redis
            self.session_manager.store_user_session(
                access_token,
                user_info,
                auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES
            )
            
            return AuthResponse(
                access_token=access_token,
                token_type="bearer",
                expires_in=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                user=UserRequest(**user_info)
            )
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Registration failed: {str(e)}"
            )


    def login(self, username: str, password: str) -> AuthResponse:
        """用户登录"""
        # 验证用户
        user = self.authenticate_user(username, password)
        
        # 创建token
        access_token = create_access_token(user.user_id)
        
        # 准备用户信息
        user_info = user.to_user_request().dict()
        
        # 存储会话信息到Redis
        self.session_manager.store_user_session(
            access_token,
            user_info,
            auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        
        return AuthResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserRequest(**user_info)
        )

    def logout(self, token: str):
        """用户登出"""
        try:
            # 验证token
            payload = verify_token(token)
            user_id = payload.get("sub")
            
            # 从Redis中移除会话
            self.session_manager.remove_session(token, user_id)
            return True
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Logout failed: {str(e)}"
            )

    def get_current_user(self, token: str = Depends(oauth2_scheme)) -> UserRequest:
        """获取当前用户"""
        try:
            
            # 从Redis获取用户会话信息
            user_info = self.session_manager.get_user_session(token)
            if not user_info:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Session expired or invalid"
                )
            
            return UserRequest(**user_info)
            
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"}
            )

# 依赖项
def get_auth_service() -> AuthService:
    """获取认证服务实例"""
    return AuthService(auth_settings.REDIS_URL)