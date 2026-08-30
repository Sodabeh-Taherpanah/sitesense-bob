# sensor.py
# Sensor class responsible for generating realistic water level readings.
# Uses a Brownian-motion walk: each step is a small random delta clamped within
# [MIN_LEVEL, MAX_LEVEL], so readings drift naturally rather than jumping randomly.

import random
from datetime import datetime, timezone


class Sensor:
    """
    Simulates a single water level sensor attached to a zone.

    The reading evolves as a random walk:
        new_value = current_value + random.uniform(-step, +step) + drift
    where `drift` is a tiny upward/downward trend to make the data more realistic.
    """

    MIN_LEVEL = 0.0   # meters
    MAX_LEVEL = 4.0   # meters
    STEP_SIZE = 0.08  # max change per reading (meters)
    DRIFT = 0.002     # slight upward drift per reading

    def __init__(self, sensor_id: str, zone_id: str, initial_level: float = 1.0):
        self.sensor_id = sensor_id
        self.zone_id = zone_id
        self._level = initial_level

    def read(self) -> dict:
        """Generate the next reading and return it as a plain dict."""
        delta = random.uniform(-self.STEP_SIZE, self.STEP_SIZE) + self.DRIFT
        self._level = max(self.MIN_LEVEL, min(self.MAX_LEVEL, self._level + delta))

        return {
            "sensor_id": self.sensor_id,
            "zone_id": self.zone_id,
            "water_level": round(self._level, 3),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
