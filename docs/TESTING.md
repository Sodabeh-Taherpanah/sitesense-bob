# SiteSense — Test Suite Summary

> Last run: 32 passed, 0 failed, 0 skipped — 0.50s
> Run with: `cd tests && python -m pytest . -v`

---

## Results at a Glance

| Metric | Value |
|---|---|
| Total tests | **32** |
| Passed | **32** |
| Failed | 0 |
| Skipped | 0 |
| Duration | 0.50 s |
| Python | 3.12 |
| Framework | pytest 9.1.1 |

---

## Test Files

### `test_alert_service.py` — 11 tests (pure unit)

Tests the two functions in `backend/alert_service.py` with no DB or HTTP involved.

| Class | Test | What it checks |
|---|---|---|
| `TestGetZoneStatus` | `test_below_warning_is_ok` | 0.0, 1.0, 1.99 m → `"ok"` |
| | `test_exactly_at_warning_threshold_is_warning` | 2.0 m exactly → `"warning"` |
| | `test_between_thresholds_is_warning` | 2.1, 2.49 m → `"warning"` |
| | `test_exactly_at_critical_threshold_is_critical` | 2.5 m exactly → `"critical"` |
| | `test_above_critical_is_critical` | 2.51, 4.0, 99.9 m → `"critical"` |
| | `test_zero_is_ok` | 0.0 m → `"ok"` |
| `TestIsAlert` | `test_ok_level_is_not_alert` | 1.0 m → `False` |
| | `test_warning_level_is_not_alert` | 2.2 m → `False` |
| | `test_just_below_critical_is_not_alert` | 2.499 m → `False` |
| | `test_exactly_at_critical_is_alert` | 2.5 m → `True` |
| | `test_above_critical_is_alert` | 2.9, 4.0 m → `True` |

---

### `test_routes.py` — 21 tests (integration)

Uses `FastAPI.TestClient` + a temp-file SQLite DB (fresh per test).
No real server or network required.

#### `TestPostSensorData` — 5 tests

| Test | What it checks |
|---|---|
| `test_valid_reading_returns_201` | Happy path returns HTTP 201 |
| `test_response_contains_expected_fields` | Response body has `id`, `sensor_id`, `zone_id`, `water_level` |
| `test_missing_required_field_returns_422` | Missing `water_level` → HTTP 422 |
| `test_negative_water_level_returns_422` | `water_level = -1.0` → HTTP 422 |
| `test_duplicate_sensor_readings_both_stored` | Two POSTs → two rows stored |

#### `TestGetZones` — 7 tests

| Test | What it checks |
|---|---|
| `test_empty_db_returns_empty_list` | Empty DB → `[]` |
| `test_single_zone_returned` | One reading → one zone in response |
| `test_status_ok_for_low_reading` | 1.2 m → `status: "ok"` |
| `test_status_warning_for_mid_reading` | 2.2 m → `status: "warning"` |
| `test_status_critical_for_high_reading` | 2.9 m → `status: "critical"` |
| `test_latest_reading_wins` | Old ok + new critical → zone shows `critical` |
| `test_multiple_zones_all_returned` | 3 zones posted → 3 zones returned |

#### `TestZoneHistory` — 3 tests

| Test | What it checks |
|---|---|
| `test_unknown_zone_returns_404` | Unknown `zone_id` → HTTP 404 |
| `test_history_returns_readings_in_ascending_order` | Readings returned oldest → newest |
| `test_history_contains_correct_zone_only` | History filtered to requested zone only |

#### `TestGetAlerts` — 6 tests

| Test | What it checks |
|---|---|
| `test_no_alerts_when_db_empty` | Empty DB → `[]` |
| `test_ok_zone_does_not_trigger_alert` | 1.2 m → no alert |
| `test_warning_zone_does_not_trigger_alert` | 2.2 m → no alert |
| `test_critical_zone_triggers_alert` | 2.9 m → alert with correct `zone_id` |
| `test_only_critical_zones_in_alerts` | ok + warning + critical → only critical in response |
| `test_alert_resolves_when_level_drops` | Critical then ok reading → alert clears |

---

## Coverage Map

### ✅ Covered

| Area | What's tested |
|---|---|
| **Alert thresholds** | All three bands; exact boundary values (2.0 and 2.5); values above/below |
| **`is_alert()` logic** | True/false at and around critical threshold |
| **POST /sensor-data** | Valid payload, missing fields, negative value, duplicate storage |
| **GET /zones** | Empty state, single zone, multi-zone, status per threshold band, latest-wins |
| **GET /zones/{id}/history** | 404 for unknown zone, ascending order, zone isolation |
| **GET /alerts** | Empty state, ok/warning don't alert, critical alerts, multi-zone filter, alert resolution |
| **HTTP status codes** | 201 (create), 200 (list), 404 (not found), 422 (validation error) |
| **DB isolation** | Each test gets a fresh schema via `drop_all/create_all` |

### ❌ Not Covered (and why)

| Area | Why not covered |
|---|---|
| **Simulator `Sensor.read()`** | Randomised output — better verified by inspection/manual run than deterministic assertion |
| **Simulator HTTP loop** | Integration concern (requires live server); network behaviour tested via backend tests |
| **`GET /health`** | Trivial endpoint returning a hardcoded dict |
| **Concurrent requests** | No concurrency bugs expected at MVP data volumes |
| **DB connection failure** | Infrastructure concern; out of scope for MVP |
| **`HISTORY_LIMIT` cap (100 rows)** | Would require inserting 101+ rows; low risk for MVP |
| **PostgreSQL dialect** | SQLAlchemy abstracts this; not tested separately |
| **Frontend behaviour** | No browser/E2E test framework in place |
| **Simulator config validation** | Config is hand-edited; no user input to validate |

---

## Test Infrastructure Notes

### Why a temp file instead of `:memory:` SQLite?

FastAPI's `TestClient` runs requests in a worker thread via `anyio`.
SQLite `:memory:` databases are **per-connection** — the worker thread
opens a new connection and sees a blank database even if tables were
created on the test thread.

Using `tempfile.mkstemp()` creates a named file that all connections
share, solving this cleanly without mocking or patching connection pools.

### Fixture design

```
conftest.py
├── TEST_ENGINE          — file-based SQLite, created once per session
├── fresh_tables         — autouse: drop + create all tables before each test
└── client(fresh_tables) — TestClient with get_db overridden to test engine
```

Each test gets a completely empty database, so tests are fully independent
and can run in any order.

---

## How to Run

```bash
# From project root
source venv/bin/activate
cd tests
python -m pytest . -v            # verbose, all tests
python -m pytest . -v -k alert   # only alert-related tests
python -m pytest test_alert_service.py -v   # unit tests only
python -m pytest test_routes.py -v          # integration tests only
```
