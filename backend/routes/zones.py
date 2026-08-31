# zones.py
# Routes:
#   GET /zones              — returns all zones with their latest reading + status
#   GET /zones/{zone_id}/history — returns last N readings for a specific zone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from alert_service import get_zone_status
from config import HISTORY_LIMIT
from database import get_db
from models import SensorReading
from schemas import SensorReadingOut, ZoneStatus

router = APIRouter()


@router.get("/zones", response_model=list[ZoneStatus], summary="Latest status for all zones")
def list_zones(db: Session = Depends(get_db)):
    """
    For each zone, return the most recent reading and its computed status.
    Uses a subquery to find max(id) per zone (latest row) efficiently.
    """
    # Subquery: latest reading id per zone
    latest_ids = (
        db.query(func.max(SensorReading.id))
        .group_by(SensorReading.zone_id)
        .scalar_subquery()
    )
    readings = db.query(SensorReading).filter(SensorReading.id.in_(latest_ids)).all()

    return [
        ZoneStatus(
            zone_id=r.zone_id,
            latest_water_level=r.water_level,
            status=get_zone_status(r.water_level),
            timestamp=r.timestamp,
        )
        for r in readings
    ]


@router.get(
    "/zones/{zone_id}/history",
    response_model=list[SensorReadingOut],
    summary="Historical readings for a zone",
)
def zone_history(zone_id: str, db: Session = Depends(get_db)):
    readings = (
        db.query(SensorReading)
        .filter(SensorReading.zone_id == zone_id)
        .order_by(SensorReading.timestamp.desc())
        .limit(HISTORY_LIMIT)
        .all()
    )
    if not readings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No data found for zone '{zone_id}'",
        )
    # Return in ascending order so charts render left-to-right
    return list(reversed(readings))
