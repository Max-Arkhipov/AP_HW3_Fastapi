from datetime import datetime

from sqlalchemy import Column, String, TIMESTAMP, Boolean, DateTime, Integer, ForeignKey, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from src.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)

    links = relationship("Link", back_populates="user")


class Link(Base):
    __tablename__ = "links"

    id = Column(Integer, primary_key=True, index=True)  # Возвращаем id
    short_code = Column(String(10), unique=True, index=True, nullable=False)
    original_url = Column(String(2048), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    clicks = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True))
    user_id = Column(Integer, ForeignKey("users.id"))
    is_active = Column(Boolean, default=True)
    project = Column(String(50), nullable=True)

    user = relationship("User", back_populates="links")
