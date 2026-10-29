from datetime import datetime

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    service: str
    version: str
    timestamp: datetime


class ReadinessResponse(BaseModel):
    status: str
    checks: dict[str, str]
    timestamp: datetime

