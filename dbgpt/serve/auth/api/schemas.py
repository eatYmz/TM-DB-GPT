from typing import Optional
from pydantic import BaseModel, EmailStr, constr

class UserRequest(BaseModel):
    """与现有 UserRequest 保持一致"""
    user_id: Optional[str] = None
    user_no: Optional[str] = None
    real_name: Optional[str] = None
    user_name: Optional[str] = None  # same with user_id
    user_channel: Optional[str] = None
    role: Optional[str] = "normal"
    nick_name: Optional[str] = None
    email: Optional[str] = None
    avatar_url: Optional[str] = None

    model_config = {
        "from_attributes": True  # 支持从 ORM 模型创建
    }

# 认证相关的请求/响应模型
class LoginRequest(BaseModel):
    """登录请求"""
    username: str  # 可以是 user_name 或 email
    password: constr(min_length=6, max_length=32)

class RegisterRequest(BaseModel):
    """注册请求"""
    username: str
    password: constr(min_length=6, max_length=32)
    email: Optional[EmailStr] = None
    real_name: Optional[str] = None
    nick_name: Optional[str] = None

class AuthResponse(BaseModel):
    """认证响应（登录/注册）"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserRequest

class CommonResponse(BaseModel):
    """通用响应"""
    code: str = "200"
    message: str = "success"
    data: Optional[dict] = None