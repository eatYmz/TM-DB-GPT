from dbgpt.storage.metadata import BaseDao, db
from dbgpt.serve.auth.models.user import User
from dbgpt.serve.auth.api.schemas import UserRequest
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import Session

class UserDao(BaseDao[User, UserRequest, UserRequest]):
    def __init__(self):
        super().__init__(db_manager=db)  # 显式传入 db_manager
    
    def get_by_username(self, username: str, session: Session) -> Optional[User]:
        """通过用户名获取用户"""
        return session.query(User).filter(User.user_name == username).first()
    
    def get_by_email(self, email: str, session: Session) -> Optional[User]:
        """通过邮箱获取用户"""
        return session.query(User).filter(User.email == email).first()
    
    def create_user(self, user: User, session: Session) -> User:
        """创建新用户"""
        session.add(user)
        session.flush()
        return user
