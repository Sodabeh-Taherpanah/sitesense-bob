# test_routes.py
# Integration-style tests for the FastAPI routes using TestClient.
# Uses the in-memory DB fixture from conftest.py so no real database is needed.
# Covers: POST /sensor-data, GET /zones, GET /zones/{id}/history, GET /alerts.
