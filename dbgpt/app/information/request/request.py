from typing import Optional
from dbgpt._private.pydantic import BaseModel

class InformationRequest(BaseModel):
    """资讯搜索请求模型"""
    source: str
    keyword: Optional[str] = None
    page: int = 1
    page_size: int = 20