from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from datetime import datetime
from dbgpt.storage.metadata import Model
from dbgpt.serve.auth.api.schemas import UserRequest


class User(Model):
    """用户模型"""
    __tablename__ = "users"
    

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(128), unique=True, nullable=False, comment="Unique user code")
    user_no = Column(String(128), nullable=True, comment="User no")
    user_name = Column(String(128), nullable=False, comment="User name")
    real_name = Column(String(128), nullable=True, comment="Real name")
    nick_name = Column(String(128), nullable=True, comment="Nick name")
    password = Column(String(256), nullable=False, comment="Encrypted password")
    email = Column(String(128), nullable=True, comment="User email")
    user_channel = Column(String(64), nullable=True, comment="User channel")
    avatar_url = Column(String(512), nullable=True, comment="User avatar url")
    role = Column(String(32), default="normal", comment="User role")
    status = Column(String(32), default="active", comment="User status: active/inactive/banned")
    sys_code = Column(String(128), nullable=True, comment="System code")
    
    # 审计字段
    gmt_created = Column(DateTime, default=datetime.utcnow, comment="Record creation time")
    gmt_modified = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, 
                         comment="Record update time")

    def __repr__(self):
        return f"<User {self.user_name}>"

    def to_user_request(self) -> UserRequest:
        """转换为 UserRequest"""
        return UserRequest(
            user_id=self.user_id,
            user_no=self.user_no,
            real_name=self.real_name,
            user_name=self.user_name,
            user_channel=self.user_channel,
            role=self.role,
            nick_name=self.nick_name,
            email=self.email,
            avatar_url=self.avatar_url
        )
