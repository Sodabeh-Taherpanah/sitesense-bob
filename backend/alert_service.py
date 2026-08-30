# alert_service.py
# Pure functions for alert/status logic.
# No DB access, no HTTP — just thresholds and water level values.
# Isolated here so it can be unit-tested without any infrastructure.

from typing import Literal

from config import CRITICAL_THRESHOLD, WARNING_THRESHOLD


def get_zone_status(water_level: float) -> Literal["ok", "warning", "critical"]:
    """
    Classify a water level reading into one of three status bands.

    ok       → water_level < WARNING_THRESHOLD
    warning  → WARNING_THRESHOLD <= water_level < CRITICAL_THRESHOLD
    critical → water_level >= CRITICAL_THRESHOLD
    """
    if water_level >= CRITICAL_THRESHOLD:
        return "critical"
    if water_level >= WARNING_THRESHOLD:
        return "warning"
    return "ok"


def is_alert(water_level: float) -> bool:
    """Return True if the water level requires an alert (critical status)."""
    return get_zone_status(water_level) == "critical"
