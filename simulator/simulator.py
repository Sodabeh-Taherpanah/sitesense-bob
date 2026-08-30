# simulator.py
# Entry point for the sensor simulator.
# Instantiates all sensors from config, then runs an async loop that fires every
# SEND_INTERVAL_SECONDS and POSTs each sensor's latest reading to the backend API.
# Replace BACKEND_URL in config.py to point at a real sensor gateway.

import asyncio
import logging

import httpx

from config import BACKEND_URL, INITIAL_WATER_LEVEL, SEND_INTERVAL_SECONDS, SENSORS
from sensor import Sensor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def send_reading(client: httpx.AsyncClient, sensor: Sensor) -> None:
    """Read from sensor and POST to the backend. Logs success or failure."""
    payload = sensor.read()
    try:
        response = await client.post(BACKEND_URL, json=payload, timeout=5.0)
        response.raise_for_status()
        logger.info(
            "Sent | sensor=%-12s zone=%-14s water_level=%.3f m",
            payload["sensor_id"],
            payload["zone_id"],
            payload["water_level"],
        )
    except httpx.HTTPStatusError as exc:
        logger.error("HTTP error %s for sensor %s", exc.response.status_code, sensor.sensor_id)
    except httpx.RequestError as exc:
        logger.warning("Could not reach backend (%s) — will retry next cycle", exc)


async def run_simulator() -> None:
    """Main loop: send all sensor readings every SEND_INTERVAL_SECONDS."""
    sensors = [
        Sensor(
            sensor_id=s["sensor_id"],
            zone_id=s["zone_id"],
            initial_level=INITIAL_WATER_LEVEL,
        )
        for s in SENSORS
    ]

    logger.info("Starting simulator with %d sensors → %s", len(sensors), BACKEND_URL)
    logger.info("Send interval: %ds  |  Ctrl+C to stop", SEND_INTERVAL_SECONDS)

    async with httpx.AsyncClient() as client:
        while True:
            tasks = [send_reading(client, sensor) for sensor in sensors]
            await asyncio.gather(*tasks)
            await asyncio.sleep(SEND_INTERVAL_SECONDS)


if __name__ == "__main__":
    try:
        asyncio.run(run_simulator())
    except KeyboardInterrupt:
        logger.info("Simulator stopped.")
