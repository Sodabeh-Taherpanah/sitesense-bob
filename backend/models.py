# models.py
# SQLAlchemy ORM models.
# SensorReading is the single table that stores every reading sent by the simulator.
# Keeping one flat table makes queries simple for MVP; can be normalized later.

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, Integer, String

from database import Base


class SensorReading(Base):
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(String, nullable=False, index=True)
    zone_id = Column(String, nullable=False, index=True)
    water_level = Column(Float, nullable=False)
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
