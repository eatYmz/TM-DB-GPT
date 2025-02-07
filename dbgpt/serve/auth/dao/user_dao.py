from dbgpt.storage.metadata import BaseDao, db
from dbgpt.serve.auth.models.user import User
from dbgpt.serve.auth.api.schemas import UserRequest
from typing import Optional

class UserDao(BaseDao[User, UserRequest, UserRequest]):
    def __init__(self):
        super().__init__(db_manager=db)  # 显式传入 db_manager
    
    def get_by_username(self, username: str) -> Optional[User]:
        """通过用户名获取用户"""
        with self.session() as session:
            return session.query(User).filter(User.user_name == username).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """通过邮箱获取用户"""
        with self.session() as session:
            return session.query(User).filter(User.email == email).first()
    
    def create_user(self, user: User) -> User:
        """创建用户"""
        with self.session() as session:
            try:
                session.add(user)
                session.flush()  # 确保生成 ID
                session.refresh(user)  # 刷新对象
                session.commit()
                return user
            except Exception as e:
                session.rollback()
                raise e
