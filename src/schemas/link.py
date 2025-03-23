from pydantic import BaseModel
from datetime import datetime

class LinkBase(BaseModel):
    original_url: str

class LinkCreate(LinkBase):
    custom_alias: str | None = None  # Для кастомных ссылок
    expires_at: datetime | None = None  # Время жизни ссылки

class LinkUpdate(BaseModel):
    original_url: str | None = None
    expires_at: datetime | None = None

class Link(LinkBase):
    short_code: str
    created_at: datetime
    expires_at: datetime | None
    clicks: int
    last_used: datetime | None

    class Config:
        from_attributes = True