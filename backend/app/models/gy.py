from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func

from app.database import Base


class GyAuth(Base):
    """光鸭网盘认证信息（单用户，只存一行）"""

    __tablename__ = "gy_auth"

    id = Column(Integer, primary_key=True, autoincrement=True)
    phone = Column(String(32), default="")
    access_token = Column(Text, default="")
    refresh_token = Column(Text, default="")
    device_id = Column(String(64), default="")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=func.now())


class GyConfig(Base):
    """光鸭网盘配置项（key-value）"""

    __tablename__ = "gy_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(64), unique=True, nullable=False, index=True)
    value = Column(Text, default="")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())


class GyMagnet(Base):
    """磁力链接表"""

    __tablename__ = "gy_magnets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    bangou = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(512), default="")
    magnet = Column(Text, default="")
    downloaded = Column(Boolean, default=False, nullable=False, index=True)
    downloaded_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())
