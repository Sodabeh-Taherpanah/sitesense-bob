# alerts.py
# Route: GET /alerts
# Returns all zones whose latest reading exceeds the critical threshold.

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from alert_service import is_alert
from database import get_db
from models import SensorReading
from schemas import AlertOut

router = APIRouter()


@router.get("/alerts", response_model=list[AlertOut], summary="Zones currently in alert state")
def get_alerts(db: Session = Depends(get_db)):
    """Return all zones where the latest reading exceeds the critical threshold."""
    latest_ids = (
        db.query(func.max(SensorReading.id))
        .group_by(SensorReading.zone_id)
        .scalar_subquery()
    )
    readings = db.query(SensorReading).filter(SensorReading.id.in_(latest_ids)).all()

    return [
        AlertOut(
            zone_id=r.zone_id,
            latest_water_level=r.water_level,
            timestamp=r.timestamp,
        )
        for r in readings
        if is_alert(r.water_level)
    ]
