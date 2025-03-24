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