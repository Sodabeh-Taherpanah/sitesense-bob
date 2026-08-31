# test_routes.py
# Integration-style tests for all FastAPI routes using TestClient + in-memory DB.
# Fixtures are provided by conftest.py — no real DB or network needed.
#
# Coverage:
#   POST /sensor-data   — happy path, missing fields, negative water level
#   GET  /zones         — empty DB, single zone, multiple zones with correct status
#   GET  /zones/{id}/history — correct ordering, 404 for unknown zone
#   GET  /alerts        — no alerts, one alert, mixed zones

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from datetime import datetime, timezone

SAMPLE_READING = {
    "sensor_id": "sensor-A1",
    "zone_id": "zone-north",
    "water_level": 1.2,
    "timestamp": "2024-01-15T10:00:00Z",
}

CRITICAL_READING = {
    "sensor_id": "sensor-B1",
    "zone_id": "zone-south",
    "water_level": 2.9,
    "timestamp": "2024-01-15T10:01:00Z",
}

WARNING_READING = {
    "sensor_id": "sensor-C1",
    "zone_id": "zone-east",
    "water_level": 2.2,
    "timestamp": "2024-01-15T10:02:00Z",
}


# ── POST /sensor-data ─────────────────────────────────────────────────────────

class TestPostSensorData:
    def test_valid_reading_returns_201(self, client):
        response = client.post("/sensor-data", json=SAMPLE_READING)
        assert response.status_code == 201

    def test_response_contains_expected_fields(self, client):
        response = client.post("/sensor-data", json=SAMPLE_READING)
        data = response.json()
        assert "id" in data
        assert data["sensor_id"] == "sensor-A1"
        assert data["zone_id"] == "zone-north"
        assert data["water_level"] == 1.2

    def test_missing_required_field_returns_422(self, client):
        bad = {k: v for k, v in SAMPLE_READING.items() if k != "water_level"}
        response = client.post("/sensor-data", json=bad)
        assert response.status_code == 422

    def test_negative_water_level_returns_422(self, client):
        bad = {**SAMPLE_READING, "water_level": -1.0}
        response = client.post("/sensor-data", json=bad)
        assert response.status_code == 422

    def test_duplicate_sensor_readings_both_stored(self, client):
        client.post("/sensor-data", json=SAMPLE_READING)
        client.post("/sensor-data", json=SAMPLE_READING)
        response = client.get("/zones/zone-north/history")
        assert len(response.json()) == 2


# ── GET /zones ────────────────────────────────────────────────────────────────

class TestGetZones:
    def test_empty_db_returns_empty_list(self, client):
        response = client.get("/zones")
        assert response.status_code == 200
        assert response.json() == []

    def test_single_zone_returned(self, client):
        client.post("/sensor-data", json=SAMPLE_READING)
        response = client.get("/zones")
        assert response.status_code == 200
        zones = response.json()
        assert len(zones) == 1
        assert zones[0]["zone_id"] == "zone-north"

    def test_status_ok_for_low_reading(self, client):
        client.post("/sensor-data", json=SAMPLE_READING)  # 1.2m
        zones = client.get("/zones").json()
        assert zones[0]["status"] == "ok"

    def test_status_warning_for_mid_reading(self, client):
        client.post("/sensor-data", json=WARNING_READING)  # 2.2m
        zones = client.get("/zones").json()
        assert zones[0]["status"] == "warning"

    def test_status_critical_for_high_reading(self, client):
        client.post("/sensor-data", json=CRITICAL_READING)  # 2.9m
        zones = client.get("/zones").json()
        assert zones[0]["status"] == "critical"

    def test_latest_reading_wins(self, client):
        # First post ok, then post critical — zone should show critical
        client.post("/sensor-data", json=SAMPLE_READING)       # 1.2m ok
        client.post("/sensor-data", json={**SAMPLE_READING, "water_level": 2.9})  # 2.9m critical
        zones = client.get("/zones").json()
        north = next(z for z in zones if z["zone_id"] == "zone-north")
        assert north["status"] == "critical"
        assert north["latest_water_level"] == 2.9

    def test_multiple_zones_all_returned(self, client):
        client.post("/sensor-data", json=SAMPLE_READING)
        client.post("/sensor-data", json=CRITICAL_READING)
        client.post("/sensor-data", json=WARNING_READING)
        zones = client.get("/zones").json()
        assert len(zones) == 3


# ── GET /zones/{zone_id}/history ─────────────────────────────────────────────

class TestZoneHistory:
    def test_unknown_zone_returns_404(self, client):
        response = client.get("/zones/zone-unknown/history")
        assert response.status_code == 404

    def test_history_returns_readings_in_ascending_order(self, client):
        client.post("/sensor-data", json={**SAMPLE_READING, "timestamp": "2024-01-15T10:00:00Z", "water_level": 1.0})
        client.post("/sensor-data", json={**SAMPLE_READING, "timestamp": "2024-01-15T10:05:00Z", "water_level": 1.5})
        client.post("/sensor-data", json={**SAMPLE_READING, "timestamp": "2024-01-15T10:10:00Z", "water_level": 2.0})
        history = client.get("/zones/zone-north/history").json()
        levels = [r["water_level"] for r in history]
        assert levels == [1.0, 1.5, 2.0]

    def test_history_contains_correct_zone_only(self, client):
        client.post("/sensor-data", json=SAMPLE_READING)
        client.post("/sensor-data", json=CRITICAL_READING)
        history = client.get("/zones/zone-north/history").json()
        assert all(r["zone_id"] == "zone-north" for r in history)


# ── GET /alerts ───────────────────────────────────────────────────────────────

class TestGetAlerts:
    def test_no_alerts_when_db_empty(self, client):
        response = client.get("/alerts")
        assert response.status_code == 200
        assert response.json() == []

    def test_ok_zone_does_not_trigger_alert(self, client):
        client.post("/sensor-data", json=SAMPLE_READING)  # 1.2m
        assert client.get("/alerts").json() == []

    def test_warning_zone_does_not_trigger_alert(self, client):
        client.post("/sensor-data", json=WARNING_READING)  # 2.2m
        assert client.get("/alerts").json() == []

    def test_critical_zone_triggers_alert(self, client):
        client.post("/sensor-data", json=CRITICAL_READING)  # 2.9m
        alerts = client.get("/alerts").json()
        assert len(alerts) == 1
        assert alerts[0]["zone_id"] == "zone-south"

    def test_only_critical_zones_in_alerts(self, client):
        client.post("/sensor-data", json=SAMPLE_READING)    # ok
        client.post("/sensor-data", json=WARNING_READING)   # warning
        client.post("/sensor-data", json=CRITICAL_READING)  # critical
        alerts = client.get("/alerts").json()
        assert len(alerts) == 1
        assert alerts[0]["zone_id"] == "zone-south"

    def test_alert_resolves_when_level_drops(self, client):
        # Post critical, then a new ok reading for same zone
        client.post("/sensor-data", json=CRITICAL_READING)
        client.post("/sensor-data", json={**CRITICAL_READING, "water_level": 1.0, "timestamp": "2024-01-15T10:05:00Z"})
        alerts = client.get("/alerts").json()
        assert alerts == []
