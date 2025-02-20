import logging
from typing import List, Optional
from datetime import datetime

from dbgpt._private.config import Config
from dbgpt.app.information.info_db import InformationDao, InformationEntity
from dbgpt.app.information.request.response import InformationResponse, InformationListResponse
from dbgpt.app.information.request.request import InformationRequest
from dbgpt.app.information.information_crawler import InformationsCrawler

logger = logging.getLogger(__name__)
CFG = Config()

class InformationService:
    def __init__(self):
        self.crawler = InformationsCrawler()
        self.dao = InformationDao()

    async def fetch_and_save_news(self, source: str, keyword: str = None) -> bool:
        """获取并保存新闻"""
        logger.info(f"Fetching news for source: {source}, keyword: {keyword}")
        
        try:
            # 调用爬虫获取数据
            news_list = await self.crawler.fetch_news(source, keyword)
            logger.info(f"Fetched {len(news_list)} news items")
            
            if not news_list:
                logger.warning("No news items found")
                return False
            
            # 获取现有的URL列表，用于去重
            existing_urls = self.dao.get_existing_urls([news['url'] for news in news_list])
            logger.info(f"Found {len(existing_urls)} existing URLs")
            
            # 过滤掉已存在的新闻
            new_news_list = [
                news for news in news_list 
                if news['url'] not in existing_urls
            ]
            
            if not new_news_list:
                logger.info("No new news items to save")
                return True
                
            logger.info(f"Saving {len(new_news_list)} new news items")
            success = self.dao.create_information(new_news_list)
            
            if success:
                logger.info(f"Successfully saved {len(new_news_list)} news items")
            else:
                logger.warning("Failed to save news items")
            
            return success
            
        except Exception as e:
            logger.error(f"Error in fetch_and_save_news: {str(e)}")
            raise e

    async def get_information_list(self, request: InformationRequest) -> InformationListResponse:
        """获取资讯列表"""
        logger.info(f"Getting information list with params: {request}")
        
        # 从数据库获取数据
        items, total = self.dao.get_news_list(
            keyword=request.keyword,
            source=request.source,
            page=request.page,
            page_size=request.page_size
        )
        
        logger.info(f"Found {total} items in database")
        
        # 转换为响应格式
        data = []
        for item in items:
            data.append(InformationResponse(
                id=item.id,
                title=item.title,
                content=item.content,
                source=item.source,
                url=item.url,
                publish_date=item.publish_date,
                keywords=item.keywords,
                summary=item.summary,
                digest=item.summary,
                gmt_created=item.gmt_created,
                gmt_modified=item.gmt_modified
            ))

        response = InformationListResponse(
            data=data,
            total=total,
            page=request.page,
            page_size=request.page_size
        )
        
        logger.info(f"Returning response with {len(data)} items")
        return response