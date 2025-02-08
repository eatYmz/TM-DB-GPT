from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Annotated

from dbgpt.serve.auth.service.auth import AuthService, get_auth_service
from dbgpt.serve.auth.api.schemas import (
    LoginRequest,
    RegisterRequest,
    AuthResponse,
    UserRequest,
    CommonResponse
)
from dbgpt.serve.auth.core.security import oauth2_scheme
from dbgpt.serve.auth.core.config import get_auth_settings

router = APIRouter()
auth_settings = get_auth_settings()

# 认证相关API
@router.post("/login", response_model=AuthResponse)
async def login(
    request: LoginRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    """用户登录"""
    return await auth_service.login(request.username, request.password)

@router.post("/register", response_model=AuthResponse)
async def register(
    request: RegisterRequest,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    """用户注册"""
    if not auth_settings.ALLOW_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Registration is disabled"
        )
    return await auth_service.register(request)

@router.post("/logout", response_model=CommonResponse)
async def logout(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    token: str = Depends(oauth2_scheme)
):
    """用户登出"""
    await auth_service.logout(token)
    return CommonResponse(message="Logout successful")

# 用户管理API
@router.get("/me", response_model=UserRequest)
async def get_current_user_info(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    token: str = Depends(oauth2_scheme)
):
    """获取当前用户信息"""
    return await auth_service.get_current_user(token)


# # 会话管理API
# @router.get("/sessions", response_model=List[dict])
# async def get_user_sessions(
#     current_user: Annotated[UserRequest, Depends(get_active_user)],
#     auth_service: Annotated[AuthService, Depends(get_auth_service)]
# ):
#     """获取用户会话列表"""
#     return await auth_service.get_user_sessions(current_user.user_id)

# @router.delete("/sessions/{session_id}", response_model=CommonResponse)
# async def terminate_session(
#     session_id: str,
#     current_user: Annotated[UserRequest, Depends(get_active_user)],
#     auth_service: Annotated[AuthService, Depends(get_auth_service)]
# ):
#     """终止指定会话"""
#     await auth_service.terminate_session(current_user.user_id, session_id)
#     return CommonResponse(message="Session terminated successfully")

# # 管理员API
# @router.get("/users", response_model=List[UserRequest])
# async def get_all_users(
#     admin_user: Annotated[UserRequest, Depends(get_admin_user)],
#     auth_service: Annotated[AuthService, Depends(get_auth_service)]
# ):
#     """获取所有用户列表（仅管理员）"""
#     return await auth_service.get_all_users()