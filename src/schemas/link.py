from fastapi import Query
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class LinkBase(BaseModel):
    original_url: str
    short_code: str | None = None
    expires_at: Optional[datetime] = None
    project: Optional[str] = None

class LinkCreate(LinkBase):
    pass

class LinkUpdate(BaseModel):
    original_url: Optional[str] = None
    expires_at: Optional[datetime] = None

class Link(LinkBase):
    id: int
    created_at: Optional[datetime] = None
    clicks: int
    last_used: Optional[datetime] = None

    class Config:
        from_attributes = True

class LinkSchema(BaseModel):
    id: int
    original_url: str
    short_code: str
    created_at: Optional[datetime] = None
    user_id: Optional[int] = None
    expires_at: Optional[datetime] = None
    clicks: int
    last_used: Optional[datetime] = None
    project: Optional[str] = None
    is_active: bool

    class Config:
        from_attributes = True  # Для совместимости с ORM, например, SQLAlchemy
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }