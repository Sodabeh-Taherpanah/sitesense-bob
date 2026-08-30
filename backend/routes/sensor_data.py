# sensor_data.py
# Route: POST /sensor-data
# Receives a reading from the simulator (or a real sensor), validates it,
# persists it to the database, and returns a 201 confirmation.

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from models import SensorReading
from schemas import SensorReadingCreate, SensorReadingOut

router = APIRouter()


@router.post(
    "/sensor-data",
    response_model=SensorReadingOut,
    status_code=status.HTTP_201_CREATED,
    summary="Receive a sensor reading",
)
def create_sensor_reading(payload: SensorReadingCreate, db: Session = Depends(get_db)):
    reading = SensorReading(
        sensor_id=payload.sensor_id,
        zone_id=payload.zone_id,
        water_level=payload.water_level,
        timestamp=payload.timestamp,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading
