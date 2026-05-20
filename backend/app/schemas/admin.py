from datetime import datetime
from typing import Annotated, Optional

from pydantic import BaseModel, EmailStr, Field


class UserOut(BaseModel):
    id: int
    email: str
    name: Optional[str]
    role: str
    created_at: datetime
    deleted_at: Optional[datetime]


class UserCreate(BaseModel):
    email: EmailStr
    name: Annotated[Optional[str], Field(max_length=100)] = None
    password: Annotated[str, Field(min_length=8)]
    role: Annotated[str, Field(pattern=r"^(admin|staff)$")]


class UserPatch(BaseModel):
    role: Annotated[Optional[str], Field(pattern=r"^(admin|staff)$")] = None
    name: Annotated[Optional[str], Field(max_length=100)] = None


class AuthVerifyRequest(BaseModel):
    email: EmailStr
    password: str


class AuthVerifyResponse(BaseModel):
    id: int
    email: str
    name: Optional[str]
    role: str


class StatsOverview(BaseModel):
    total_sessions: int
    total_messages: int
    avg_latency_ms: float
    p95_latency_ms: float
    total_cost_eur: float
    avg_messages_per_session: float
    cost_per_message: float


class WeekdayPoint(BaseModel):
    day: int
    count: int


class DailyPoint(BaseModel):
    date: str      # "YYYY-MM-DD"
    count: int


class HourlyPoint(BaseModel):
    hour: int      # 0-23
    count: int


class TopSourceRow(BaseModel):
    source: str
    hit_count: int


class HeatmapPoint(BaseModel):
    day: int   # 0=Sunday … 6=Saturday (PostgreSQL DOW)
    hour: int  # 0-23
    count: int


class ApiUsageRow(BaseModel):
    model: str
    prompt_tokens: int
    completion_tokens: int
    cost_eur: float
    avg_latency_ms: float


class PagedUsers(BaseModel):
    items: list[UserOut]
    total: int
    page: int
    page_size: int
