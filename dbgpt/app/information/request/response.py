from typing import List, Optional
from dbgpt._private.pydantic import BaseModel, Field
from datetime import datetime


class InformationItem(BaseModel):
    """单条资讯信息"""
    title: str
    content: str
    source: str
    url: str
    publish_date: datetime
    keywords: str
    summary: Optional[str]
    digest: Optional[str]

class InformationResponse(BaseModel):
    """单条资讯信息响应"""
    id: Optional[int] = None
    title: str
    content: str
    source: str
    url: str
    publish_date: datetime
    keywords: str
    summary: Optional[str] = None
    digest: Optional[str] = None
    gmt_created: Optional[datetime] = None
    gmt_modified: Optional[datetime] = None

class InformationListResponse(BaseModel):
    """资讯列表响应"""
    data: List[InformationResponse] = Field([], description="资讯列表")
    total: int = Field(0, description="总数")
    page: int = Field(1, description="当前页码")
    page_size: int = Field(20, description="每页数量")