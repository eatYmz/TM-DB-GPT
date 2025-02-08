from typing import Optional, Dict
from pydantic import BaseModel, EmailStr

class UserRequest(BaseModel):
    """用户信息模型"""
    user_id: Optional[str] = None
    user_no: Optional[str] = None
    real_name: Optional[str] = None
    user_name: Optional[str] = None  # same with user_id
    user_channel: Optional[str] = None
    role: Optional[str] = "normal"
    nick_name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None
    nick_name_like: Optional[str] = None

    model_config = {
        "from_attributes": True
    }

# 认证相关的请求/响应模型
class LoginRequest(BaseModel):
    """登录请求"""
    username: str  # 用户名或邮箱
    password: str

    model_config = {
        "min_anystr_length": 6,
        "max_anystr_length": 32
    }

class RegisterRequest(BaseModel):
    """注册请求"""
    username: str
    password: str
    email: Optional[EmailStr] = None
    user_channel: Optional[str] = None
    real_name: Optional[str] = None
    nick_name: Optional[str] = None

    model_config = {
        "min_anystr_length": 6,
        "max_anystr_length": 32
    }

class AuthResponse(BaseModel):
    """认证响应"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # 默认1小时
    user: UserRequest

class CommonResponse(BaseModel):
    """通用响应"""
    code: str = "200"
    message: str = "success"
    data: Optional[Dict] = None