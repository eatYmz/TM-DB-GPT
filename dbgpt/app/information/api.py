import logging
from fastapi import APIRouter, Depends
from dbgpt.app.openapi.api_view_model import Result
from dbgpt.serve.utils.auth import UserRequest, get_user_from_headers
from dbgpt.app.information.service import InformationService
from dbgpt.app.information.request.request import InformationRequest
from dbgpt.app.information.request.response import InformationItem
from typing import Optional
from .information_crawler import InformationsCrawler

router = APIRouter()
logger = logging.getLogger(__name__)
information_service = InformationService()
crawler = InformationsCrawler()

@router.post("/v1/information/list")
async def get_information_list(
    request: InformationRequest,
    user_info: UserRequest = Depends(get_user_from_headers),
):
    """获取新闻列表"""
    try:
        result = await information_service.get_information_list(request)
        return Result.succ(result)
    except Exception as ex:
        logger.error(f"Get information list error: {str(ex)}")
        return Result.failed(code="E000X", msg=f"Get information list error: {ex}")

@router.post("/v1/information/fetch")
async def fetch_information(
    source: str,
    keyword: Optional[str] = None,
    user_info: UserRequest = Depends(get_user_from_headers),
):
    """手动获取新闻"""
    try:
        result = await information_service.fetch_and_save_news(source, keyword)
        return Result.succ({"success": result})
    except Exception as ex:
        logger.error(f"Fetch information error: {str(ex)}")
        return Result.failed(code="E000X", msg=f"Fetch information error: {ex}")

@router.post("/v1/information/search")
async def search_information(
    request: InformationRequest,
    user_info: UserRequest = Depends(get_user_from_headers),
):
    """搜索资讯接口"""
    try:
        # 先尝试获取新数据
        await information_service.fetch_and_save_news(request.source, request.keyword)
        
        # 从数据库获取完整列表
        result = await information_service.get_information_list(request)
        
        response_data = {
            "data": [
                {
                    "title": item.title,
                    "url": item.url,
                    "source": item.source,
                    "publish_date": item.publish_date.isoformat(),
                    "summary": item.summary,
                    "digest": item.digest
                }
                for item in result.data
            ],
            "total": result.total
        }
        
        # 添加响应数据日志
        logger.info(f"Sending response data: {response_data}")
        
        return Result.succ(response_data)
    except Exception as e:
        logger.error(f"Search information failed: {str(e)}")
        logger.exception(e)
        return Result.failed(code="E000X", msg=f"搜索资讯失败: {str(e)}")