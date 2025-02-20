from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, Text
from dbgpt.storage.metadata import BaseDao, Model

class InformationEntity(Model):
    __tablename__ = "ai_news"
    
    # 修改 id 字段定义，添加自增属性
    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String(200))
    content = Column(Text)
    source = Column(String(100))  # 公众号
    url = Column(String(500))
    publish_date = Column(DateTime)
    keywords = Column(String(200))  # 关键词，用逗号分隔
    gmt_created = Column(DateTime)
    gmt_modified = Column(DateTime)
    summary = Column(String(500))  # 摘要

    def __repr__(self):
        return f"InformationEntity(id={self.id}, title='{self.title}', source='{self.source}')"

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "source": self.source,
            "url": self.url,
            "publish_date": self.publish_date,
            "keywords": self.keywords,
            "gmt_created": self.gmt_created,
            "gmt_modified": self.gmt_modified,
            "summary": self.summary
        }

class InformationDao(BaseDao):
    def get_existing_urls(self, urls: list) -> set:
        """获取已存在的URL列表"""
        session = self.get_raw_session()
        try:
            existing = session.query(InformationEntity.url)\
                            .filter(InformationEntity.url.in_(urls))\
                            .all()
            return {url[0] for url in existing}
        finally:
            session.close()

    def create_information(self, information_list):
        """创建新闻记录"""
        if not information_list:
            return True
            
        session = self.get_raw_session()
        try:
            information_entities = []
            for information in information_list:
                entity = InformationEntity(
                    title=information['title'],
                    content=information['content'],
                    source=information['source'],
                    url=information['url'],
                    publish_date=information['publish_date'],
                    keywords=information['keywords'],
                    gmt_created=datetime.now(),
                    gmt_modified=datetime.now(),
                    summary=information['summary']
                )
                information_entities.append(entity)
            
            session.add_all(information_entities)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_news_list(self, keyword=None, source=None, page=1, page_size=20):
        """获取新闻列表"""
        session = self.get_raw_session()
        try:
            query = session.query(InformationEntity)
            
            if keyword:
                query = query.filter(InformationEntity.keywords.like(f"%{keyword}%"))
            if source:
                query = query.filter(InformationEntity.source == source)
            
            total = query.count()
            
            information_list = query.order_by(InformationEntity.publish_date.desc())\
                            .offset((page - 1) * page_size)\
                            .limit(page_size)\
                            .all()
            
            return information_list, total
        finally:
            session.close()