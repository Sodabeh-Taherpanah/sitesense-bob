# config.py
# Simulator configuration: zones to simulate, HTTP target, and timing.
# Change BACKEND_URL to point at a real sensor gateway when replacing this simulator.

BACKEND_URL = "http://localhost:8000/sensor-data"

# Each entry defines one sensor mounted in one zone.
SENSORS = [
    {"sensor_id": "sensor-A1", "zone_id": "zone-north"},
    {"sensor_id": "sensor-A2", "zone_id": "zone-north"},
    {"sensor_id": "sensor-B1", "zone_id": "zone-south"},
    {"sensor_id": "sensor-C1", "zone_id": "zone-east"},
    {"sensor_id": "sensor-D1", "zone_id": "zone-west"},
]

# How often each sensor sends a reading (seconds)
SEND_INTERVAL_SECONDS = 5

# Starting water level for each sensor (meters)
INITIAL_WATER_LEVEL = 1.0
