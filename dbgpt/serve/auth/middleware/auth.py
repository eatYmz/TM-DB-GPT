from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from fastapi import HTTPException, status
from typing import List, Optional
import time

from dbgpt.serve.auth.service.auth import AuthService, get_auth_service
from dbgpt.serve.auth.core.config import get_auth_settings
from dbgpt.serve.auth.core.security import verify_security_token

auth_settings = get_auth_settings()

class AuthMiddleware(BaseHTTPMiddleware):
    def __init__(
        self, 
        app,
        exclude_paths: Optional[List[str]] = None,
        protected_paths: Optional[List[str]] = None,  # 新增：受保护的路径
        auth_service = None
    ):
        super().__init__(app)
        self.exclude_paths = exclude_paths or []
        self.protected_paths = protected_paths or ["/auth"]  # 默认只保护 /auth 路径
        self.auth_service = auth_service or get_auth_service()
    
    async def dispatch(self, request: Request, call_next):
        # 检查是否是需要保护的路径
        if not any(request.url.path.startswith(path) for path in self.protected_paths):
            return await call_next(request)
            
        # 检查是否是排除路径
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)

        # 获取并验证 token
        token = request.headers.get("Authorization")
        # 处理 Bearer 前缀
        if token.startswith('Bearer '):
            token = token.split(' ')[1]
                
        if not token:
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing authentication token"}
            )

        try:
            # 验证 token 并获取会话
            user_info = self.auth_service.session_manager.get_user_session(token)
            
            if not user_info:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Session expired or invalid -middleware"}
                )
            
            # 刷新会话过期时间
            self.auth_service.session_manager.refresh_session(token)
            
            request.state.user = user_info
            return await call_next(request)
        except Exception as e:
            return JSONResponse(
                status_code=401,
                content={"detail": str(e)}
            )
    
    def _is_exclude_path(self, path: str) -> bool:
        """检查路径是否在排除列表中
        
        Args:
            path: 请求路径
            
        Returns:
            bool: 是否排除认证
        """
        return any(
            path.startswith(excluded) 
            for excluded in self.exclude_paths
        )
    
    def _extract_token(self, request: Request) -> Optional[str]:
        """从请求头中提取token
        
        Args:
            request: FastAPI请求对象
            
        Returns:
            Optional[str]: Bearer token或None
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return None
        return auth_header.split(" ")[1]