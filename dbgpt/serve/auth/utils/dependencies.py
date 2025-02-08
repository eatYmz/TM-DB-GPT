from fastapi import Depends, HTTPException, status
from typing import Optional, Annotated

from dbgpt.serve.auth.core.security import oauth2_scheme
from dbgpt.serve.auth.service.auth import AuthService, get_auth_service
from dbgpt.serve.auth.api.schemas import UserRequest
from dbgpt.serve.auth.core.config import get_auth_settings

auth_settings = get_auth_settings()

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> UserRequest:

    try:
        return await auth_service.get_current_user(token)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_active_user(
    current_user: Annotated[UserRequest, Depends(get_current_user)]
) -> UserRequest:
    """获取活跃用户
    
    Args:
        current_user: 当前用户信息
        
    Returns:
        UserRequest: 活跃用户信息
        
    Raises:
        HTTPException: 用户未激活时抛出
    """
    if current_user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user

async def get_admin_user(
    current_user: Annotated[UserRequest, Depends(get_active_user)]
) -> UserRequest:
    """获取管理员用户
    
    Args:
        current_user: 当前活跃用户信息
        
    Returns:
        UserRequest: 管理员用户信息
        
    Raises:
        HTTPException: 非管理员用户访问时抛出
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user

def check_permissions(*required_permissions: str):
    """检查用户权限装饰器
    
    Args:
        required_permissions: 所需权限列表
        
    Returns:
        Callable: 权限检查依赖项
    """
    async def permission_checker(
        current_user: Annotated[UserRequest, Depends(get_active_user)]
    ) -> UserRequest:
        user_permissions = current_user.permissions or []
        if not all(perm in user_permissions for perm in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    return permission_checker