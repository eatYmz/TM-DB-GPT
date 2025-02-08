from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from functools import lru_cache

class AuthSettings(BaseSettings):
    """认证相关配置"""
    # JWT设置
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")  # 生产环境必须修改
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 密码策略
    PASSWORD_MIN_LENGTH: int = 6
    PASSWORD_MAX_LENGTH: int = 32
    
    # 系统设置
    ALLOW_REGISTRATION: bool = True  # 是否允许注册
    DEFAULT_ROLE: str = "normal"     # 默认角色
    EXCLUDE_PATHS: List[str] = ["/auth/login", "/auth/register"]
    
    # Redis设置
    REDIS_HOST: str = os.getenv("AUTH_REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("AUTH_REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("AUTH_REDIS_DB", "0"))
    REDIS_PASSWORD: Optional[str] = os.getenv("AUTH_REDIS_PASSWORD")
    REDIS_USERNAME: Optional[str] = os.getenv("AUTH_REDIS_USERNAME")
    REDIS_SSL: bool = os.getenv("AUTH_REDIS_SSL", "false").lower() == "true"
    
    @property
    def REDIS_URL(self) -> str:
        """构建Redis URL"""
        auth = ""
        if self.REDIS_USERNAME and self.REDIS_PASSWORD:
            auth = f"{self.REDIS_USERNAME}:{self.REDIS_PASSWORD}@"
        elif self.REDIS_PASSWORD:
            auth = f":{self.REDIS_PASSWORD}@"
            
        scheme = "rediss" if self.REDIS_SSL else "redis"
        return f"{scheme}://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    class Config:
        case_sensitive = True
        env_prefix = "AUTH_"  # 环境变量前缀

@lru_cache()
def get_auth_settings() -> AuthSettings:
    """获取认证配置单例"""
    return AuthSettings()