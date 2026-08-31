# SiteSense — Construction Site Sensor Logistics Dashboard

A full-stack MVP that simulates wireless water-level sensors installed across
construction site zones, collects readings via a REST API, and displays live
status on a web dashboard to support logistics decision-making.

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Quick Start](#quick-start)
4. [Running Each Component](#running-each-component)
5. [API Reference](#api-reference)
6. [Running the Tests](#running-the-tests)
7. [Key Design Decisions](#key-design-decisions)
8. [Replacing the Simulator with Real Hardware](#replacing-the-simulator-with-real-hardware)

---

## Architecture Overview

```
┌─────────────────────┐        HTTP POST /sensor-data        ┌──────────────────────┐
│   Sensor Simulator  │ ───────────────────────────────────► │   FastAPI Backend    │
│   (Python / httpx)  │                                       │   (Python / uvicorn) │
│                     │                                       │                      │
│  5 virtual sensors  │                                       │  • Validates input   │
│  Brownian-motion    │                                       │  • Persists to DB    │
│  water-level drift  │                                       │  • Computes status   │
└─────────────────────┘                                       └──────────┬───────────┘
                                                                         │ SQLite
                                                              ┌──────────▼───────────┐
                                                              │     Database         │
                                                              │  sensor_readings     │
                                                              └──────────┬───────────┘
                                                                         │
                                          GET /zones                     │
┌─────────────────────┐ ◄─────────────────────────────────── ┌──────────▼───────────┐
│   React Dashboard   │   GET /alerts                        │   REST Endpoints     │
│   (CDN / no build)  │   GET /zones/{id}/history            │   /zones             │
│                     │                                       │   /alerts            │
│  • Zone cards       │                                       │   /zones/{id}/history│
│  • Alert panel      │                                       └──────────────────────┘
│  • History charts   │
│  Polls every 5s     │
└─────────────────────┘
```

**Status thresholds:**

| Water Level | Status   | Colour |
|-------------|----------|--------|
| < 2.0 m     | ok       | 🟢 Green  |
| 2.0 – 2.5 m | warning  | 🟡 Yellow |
| > 2.5 m     | critical | 🔴 Red    |

---

## Project Structure

```
construction-dashboard/
├── simulator/
│   ├── config.py        # Zones, sensor list, backend URL, send interval
│   ├── sensor.py        # Sensor class — Brownian-motion random walk
│   └── simulator.py     # Async loop: reads all sensors, POSTs to backend
│
├── backend/
│   ├── config.py        # DATABASE_URL, thresholds, history limit
│   ├── database.py      # SQLAlchemy engine + get_db() FastAPI dependency
│   ├── models.py        # SensorReading ORM model
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── alert_service.py # Pure functions: get_zone_status(), is_alert()
│   ├── main.py          # FastAPI app factory, CORS, router mounting
│   └── routes/
│       ├── sensor_data.py  # POST /sensor-data
│       ├── zones.py        # GET /zones, GET /zones/{zone_id}/history
│       └── alerts.py       # GET /alerts
│
├── tests/
│   ├── conftest.py         # Pytest fixtures — temp-file SQLite, TestClient
│   ├── test_alert_service.py  # 11 unit tests — pure alert logic
│   └── test_routes.py      # 21 integration tests — all 4 endpoints
│
├── frontend/
│   ├── index.html          # App shell — CDN imports (React, Recharts, Babel)
│   ├── api.js              # fetch wrappers for all backend endpoints
│   ├── app.js              # Root React component, polling, state
│   └── components/
│       ├── ZoneCard.jsx    # Zone status card (coloured by status)
│       ├── ZoneChart.jsx   # Recharts line chart with threshold lines
│       └── AlertList.jsx   # Active alerts panel
│
├── requirements.txt
└── README.md
```

---

## Quick Start

### Prerequisites

- Python 3.10+
- A virtual environment (recommended)
- No Node.js required — the frontend uses CDN scripts

### 1. Install dependencies

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Start the backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

The API is now live at `http://localhost:8000`.  
Interactive docs: `http://localhost:8000/docs`

### 3. Start the simulator

Open a second terminal:

```bash
source venv/bin/activate
cd simulator
python simulator.py
```

You'll see log lines like:
```
2024-01-15 10:30:05 [INFO] Sent | sensor=sensor-A1   zone=zone-north   water_level=1.234 m
```

### 4. Open the dashboard

Open a third terminal:

```bash
cd frontend
python3 -m http.server 3000
```

Navigate to **http://localhost:3000** in your browser.

---

## Running Each Component

### Backend only (no simulator)

```bash
cd backend
uvicorn main:app --reload --port 8000

# Manually post a reading to verify
curl -X POST http://localhost:8000/sensor-data \
  -H "Content-Type: application/json" \
  -d '{"sensor_id":"s1","zone_id":"zone-north","water_level":2.9,"timestamp":"2024-01-15T10:00:00Z"}'

curl http://localhost:8000/zones
curl http://localhost:8000/alerts
```

### Simulator only (backend must be running first)

```bash
cd simulator
python simulator.py
# Ctrl+C to stop — backend errors are logged as warnings, not crashes
```

### Change thresholds

Edit [`backend/config.py`](backend/config.py):

```python
WARNING_THRESHOLD  = 2.0   # meters
CRITICAL_THRESHOLD = 2.5   # meters
```

### Switch to PostgreSQL

```bash
export DATABASE_URL="postgresql://user:password@localhost/sitesense"
uvicorn main:app --reload --port 8000
```

No code changes required — SQLAlchemy handles the dialect difference.

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/sensor-data` | Ingest one sensor reading |
| `GET`  | `/zones` | Latest reading + status for every zone |
| `GET`  | `/zones/{zone_id}/history` | Last 100 readings for a zone (ascending) |
| `GET`  | `/alerts` | All zones currently above the critical threshold |
| `GET`  | `/health` | Liveness check — returns `{"status":"ok"}` |

Full interactive documentation available at `http://localhost:8000/docs`.

### POST /sensor-data — request body

```json
{
  "sensor_id":   "sensor-A1",
  "zone_id":     "zone-north",
  "water_level": 1.42,
  "timestamp":   "2024-01-15T10:30:00Z"
}
```

Validation: `water_level` must be ≥ 0. Missing fields return HTTP 422.

---

## Running the Tests

```bash
source venv/bin/activate
cd tests
python -m pytest . -v
```

Expected: **32 passed** in < 1 second.

Tests use a temporary SQLite file (not `:memory:`) so that FastAPI's worker
threads see the same database as the test fixtures. The file is deleted
automatically after the test run.

### Coverage summary

| Test file | Count | What's covered |
|-----------|-------|----------------|
| `test_alert_service.py` | 11 | `get_zone_status()` at all boundaries, `is_alert()` true/false |
| `test_routes.py` | 21 | POST /sensor-data happy path + validation, GET /zones status logic, latest-reading-wins, GET /zones/{id}/history ordering + 404, GET /alerts isolation + alert resolution |

---

## Key Design Decisions

### 1. Brownian-motion sensor model
Each `Sensor` applies a random step of ±0.08 m plus a tiny upward drift of
+0.002 m per reading. This produces realistic-looking drift rather than pure
noise — water levels creep up over time as they would on a real site.

### 2. Alert logic isolated as pure functions
`alert_service.py` contains only `get_zone_status(water_level)` and
`is_alert(water_level)`. No database access, no HTTP — just float → string.
This makes the business logic trivially unit-testable and easy to change.

### 3. Schemas decoupled from ORM models
Pydantic `schemas.py` and SQLAlchemy `models.py` are kept separate.
The API contract (`SensorReadingCreate`, `ZoneStatus`, `AlertOut`) can evolve
independently from the database schema.

### 4. SQLite for MVP, PostgreSQL-ready
`DATABASE_URL` defaults to a local SQLite file but is read from the
environment variable, so switching to PostgreSQL requires only setting that
variable — no code changes.

### 5. Frontend with no build step
React, Recharts, and Babel are loaded from CDN. JSX is transpiled in the
browser. This means the frontend can be served with any static file server
and requires no Node.js, npm, or bundler for the MVP.

### 6. Simulator is fully replaceable
The simulator only knows `BACKEND_URL` in `config.py`. Real sensors need only
POST the same JSON schema to the same endpoint — nothing else in the system
changes.

### 7. Latest-reading-wins via MAX(id) subquery
`GET /zones` and `GET /alerts` use `scalar_subquery()` with `MAX(id) GROUP BY
zone_id` to find the most recent reading per zone in a single query, avoiding
N+1 patterns.

---

## Replacing the Simulator with Real Hardware

1. Configure the real sensor firmware to POST to `http://<server>:8000/sensor-data`
2. Match the JSON schema: `sensor_id`, `zone_id`, `water_level` (float, metres), `timestamp` (ISO 8601)
3. Stop running `simulator.py` — nothing else changes

To add more zones or sensors, edit [`simulator/config.py`](simulator/config.py) `SENSORS` list
(or configure the real hardware directly).

---

*Made with IBM Bob*
