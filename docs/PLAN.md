# SiteSense — Architecture Plan

> This document is the living architecture reference for the project.
> Update it whenever a structural, data-flow, or design decision changes.

---

## Table of Contents

1. [Overview](#overview)
2. [File Structure](#file-structure)
3. [Data Flow](#data-flow)
4. [Component Responsibilities](#component-responsibilities)
5. [Data Schema](#data-schema)
6. [Alert Logic](#alert-logic)
7. [Status Levels](#status-levels)
8. [Key Design Decisions](#key-design-decisions)
9. [Change Log](#change-log)

---

## Overview

A full-stack MVP that simulates wireless water-level sensors across
construction site zones, collects readings via a REST API, and displays
live status on a web dashboard to support logistics decision-making.

**Four layers:**

| Layer | Technology | Purpose |
|---|---|---|
| Sensor Simulator | Python + httpx | Generates realistic readings, POSTs to backend |
| Backend API | Python + FastAPI + SQLAlchemy | Validates, persists, serves data |
| Database | SQLite (dev) / PostgreSQL (prod) | Stores all sensor readings |
| Frontend Dashboard | React 18 + Recharts (CDN) | Live zone status, alerts, history charts |

---

## File Structure

```
construction-dashboard/
├── docs/
│   └── PLAN.md              ← this file
│
├── simulator/
│   ├── config.py            # Zones, sensor list, backend URL, send interval
│   ├── sensor.py            # Sensor class — Brownian-motion random walk
│   └── simulator.py         # Async loop: reads all sensors, POSTs to backend
│
├── backend/
│   ├── config.py            # DATABASE_URL env var, thresholds, history limit
│   ├── database.py          # SQLAlchemy engine, SessionLocal, get_db() dependency
│   ├── models.py            # SensorReading ORM table
│   ├── schemas.py           # Pydantic in/out schemas (decoupled from ORM)
│   ├── alert_service.py     # Pure functions: get_zone_status(), is_alert()
│   ├── main.py              # FastAPI app, CORS, lifespan, router mounting
│   └── routes/
│       ├── __init__.py
│       ├── sensor_data.py   # POST /sensor-data
│       ├── zones.py         # GET /zones, GET /zones/{zone_id}/history
│       └── alerts.py        # GET /alerts
│
├── tests/
│   ├── conftest.py          # Temp-file SQLite engine, TestClient fixture
│   ├── test_alert_service.py  # 11 pure unit tests — alert logic
│   └── test_routes.py       # 21 integration tests — all endpoints
│
├── frontend/
│   └── index.html           # Single file: React + Recharts + all app JSX inlined
│                            # (CDN loaded via jsdelivr, Babel transpiles at runtime)
│
├── .gitignore
├── requirements.txt
└── README.md
```

---

## Data Flow

```
Sensor Simulator
  └─► POST /sensor-data
        │
        ▼
  Backend: validate (Pydantic) → persist (SQLAlchemy) → 201 response
        │
        ▼
  SQLite: sensor_readings table
        │
        ├─► GET /zones          → MAX(id) per zone → status classification
        ├─► GET /zones/{id}/history → last 100 readings, ascending
        └─► GET /alerts         → zones where latest reading ≥ CRITICAL_THRESHOLD

Frontend (polls every 5s)
  ├─► GET /zones   → ZoneCard grid (green / yellow / red)
  ├─► GET /alerts  → AlertList panel
  └─► GET /zones/{id}/history  (on card click) → ZoneChart line chart
```

---

## Component Responsibilities

### `simulator/sensor.py` — `Sensor` class
- Holds current water level in `_level`
- Each `read()` call applies: `delta = random(±STEP_SIZE) + DRIFT`
- Clamps to `[MIN_LEVEL, MAX_LEVEL]`
- Returns plain `dict` — no HTTP, no DB dependency

### `simulator/simulator.py`
- Creates all `Sensor` instances from `config.SENSORS`
- Runs `asyncio.gather()` every `SEND_INTERVAL_SECONDS`
- HTTP errors → logged as WARNING, loop continues

### `backend/alert_service.py`
- `get_zone_status(water_level) → "ok" | "warning" | "critical"`
- `is_alert(water_level) → bool`
- **No DB, no HTTP** — pure functions, unit-testable in isolation

### `backend/routes/zones.py`
- Uses `scalar_subquery()` with `MAX(id) GROUP BY zone_id` to find
  latest reading per zone in one query (avoids N+1)
- History returned in **ascending** order (for chart left-to-right)

### `frontend/index.html`
- All JSX inlined in a single `<script id="app-source" type="text/plain">`
- CDN load order: `react` → `react-dom` → `prop-types` → `recharts`
- Babel loaded **last** dynamically; `onload` manually transpiles app source
- This pattern guarantees all globals exist before Babel executes

---

## Data Schema

### `sensor_readings` table

| Column | Type | Notes |
|---|---|---|
| `id` | INTEGER PK | Auto-increment |
| `sensor_id` | STRING | e.g. `"sensor-A1"` |
| `zone_id` | STRING | e.g. `"zone-north"` |
| `water_level` | FLOAT | Meters, ≥ 0 |
| `timestamp` | DATETIME(tz) | UTC, from simulator |

### POST /sensor-data body

```json
{
  "sensor_id":   "sensor-A1",
  "zone_id":     "zone-north",
  "water_level": 1.42,
  "timestamp":   "2024-01-15T10:30:00Z"
}
```

---

## Alert Logic

Defined in `backend/alert_service.py`, configurable via `backend/config.py`.

```
water_level < WARNING_THRESHOLD (2.0)   → "ok"
water_level >= WARNING_THRESHOLD        → "warning"
water_level >= CRITICAL_THRESHOLD (2.5) → "critical"  ← triggers alert
```

A zone "resolves" automatically when its next reading drops below the
critical threshold — no manual acknowledgement needed.

---

## Status Levels

| Water Level | Status | UI Colour | Alert? |
|---|---|---|---|
| < 2.0 m | `ok` | 🟢 Green | No |
| 2.0 – 2.5 m | `warning` | 🟡 Yellow | No |
| > 2.5 m | `critical` | 🔴 Red | Yes |

Thresholds are constants in `backend/config.py`:
```python
WARNING_THRESHOLD  = 2.0  # meters
CRITICAL_THRESHOLD = 2.5  # meters
```

---

## Key Design Decisions

| # | Decision | Choice | Rationale |
|---|---|---|---|
| 1 | Sensor realism | Brownian-motion walk | Realistic drift; configurable step/drift |
| 2 | Alert logic location | Pure functions in `alert_service.py` | No DB/HTTP dependency → easily unit-tested |
| 3 | Schema/ORM separation | `schemas.py` ≠ `models.py` | API contract stable even if DB schema changes |
| 4 | Database | SQLite default, PostgreSQL via `DATABASE_URL` env var | Zero setup for MVP; production-ready swap |
| 5 | Frontend build | No build step — CDN + Babel standalone | No Node.js/npm required for MVP |
| 6 | CDN strategy | jsdelivr with pinned versions + prop-types loaded before Recharts | Avoids redirects; Recharts requires `prop-types` global |
| 7 | Babel execution | Loaded last, dynamically; transpiles `type="text/plain"` source manually | Guarantees all globals exist before transpilation |
| 8 | Latest reading query | `MAX(id) scalar_subquery GROUP BY zone_id` | Single query, no N+1 |
| 9 | Simulator decoupling | Only knows `BACKEND_URL` in config | Real hardware = change one config value |
| 10 | Test isolation | Temp-file SQLite (not `:memory:`) | FastAPI worker threads share one file connection |

---

## Change Log

| Date | Change | Files affected |
|---|---|---|
| Phase 1 | Sensor simulator with Brownian-motion model | `simulator/` |
| Phase 2 | FastAPI backend, SQLAlchemy models, alert service | `backend/` |
| Phase 2 fix | `scalar_subquery()` to fix SAWarning | `routes/zones.py`, `routes/alerts.py` |
| Phase 3 | React dashboard, polling, zone cards, chart, alerts | `frontend/` |
| Phase 3 fixes | CDN load order, prop-types peer dep, Babel dynamic load | `frontend/index.html` |
| Docs | README + PLAN.md added | `README.md`, `docs/PLAN.md` |
