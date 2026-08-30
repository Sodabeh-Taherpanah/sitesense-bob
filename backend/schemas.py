# schemas.py
# Pydantic models for request validation and response serialization.
# Separating schemas from ORM models means the API contract stays stable
# even if the database schema evolves.

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ── Inbound (simulator → API) ────────────────────────────────────────────────

class SensorReadingCreate(BaseModel):
    sensor_id: str
    zone_id: str
    water_level: float = Field(..., ge=0.0, description="Water level in meters")
    timestamp: datetime


# ── Outbound (API → frontend) ────────────────────────────────────────────────

class SensorReadingOut(BaseModel):
    id: int
    sensor_id: str
    zone_id: str
    water_level: float
    timestamp: datetime

    model_config = {"from_attributes": True}


class ZoneStatus(BaseModel):
    zone_id: str
    latest_water_level: float
    status: Literal["ok", "warning", "critical"]
    timestamp: datetime


class AlertOut(BaseModel):
    zone_id: str
    latest_water_level: float
    timestamp: datetime
