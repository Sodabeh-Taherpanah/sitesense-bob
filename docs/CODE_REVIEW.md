# SiteSense — Code Review Report

> Full review across security, performance, code quality, and best practices.
> Severity: **Critical** → **High** → **Medium** → **Low**
> Total findings: **38** across 4 severity levels.

---

## Summary

| Severity | Count | Action |
|---|---|---|
| 🔴 Critical | 5 | Fix before any deployment |
| 🟠 High | 7 | Fix before production |
| 🟡 Medium | 13 | Fix before wider use |
| 🔵 Low | 13 | Improve when convenient |

---

## 🔴 Critical

### C1 — CORS wildcard open to any origin
**`backend/main.py:24`**

```python
# current
allow_origins=["*"]
```

Any website can make authenticated cross-origin requests to the API. Enables CSRF-style data theft.

```python
# fix
allow_origins=os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
```

---

### C2 — Hardcoded `BACKEND_URL` in simulator
**`simulator/config.py:5`**

```python
BACKEND_URL = "http://localhost:8000/sensor-data"  # hardcoded
```

Simulator cannot be deployed to any environment without editing source.

```python
# fix
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000/sensor-data")
```

---

### C3 — Hardcoded `BASE_URL` in frontend
**`frontend/index.html:50`**

```js
const BASE_URL = "http://localhost:8000";  // hardcoded
```

Dashboard cannot reach a backend at any other host or port without editing the file.

```js
// fix — inject at serve time, or derive from window.location
const BASE_URL = window.SITESENSE_API_URL || "http://localhost:8000";
// then set via: <script>window.SITESENSE_API_URL = "https://api.example.com";</script>
```

---

### C4 — No version pinning in `requirements.txt`
**`requirements.txt`**

```
fastapi          # no version — next install could pull a breaking change
sqlalchemy
```

Breaks reproducibility; a CI deploy on a different day can install incompatible versions.

```
# fix — pin all deps
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy==2.0.36
pydantic==2.9.2
httpx==0.27.2
pytest==8.3.3
pytest-asyncio==0.24.0
```

Run `pip freeze > requirements.txt` after confirming the working set.

---

### C5 — No authentication on any endpoint
**`backend/main.py`** — all routes

All endpoints (`POST /sensor-data`, `GET /zones`, `GET /alerts`, `GET /zones/{id}/history`) are publicly accessible with no credentials required.

```python
# fix — add API key header for MVP
from fastapi.security.api_key import APIKeyHeader
from fastapi import Security, HTTPException

API_KEY = os.getenv("API_KEY", "")
api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(key: str = Security(api_key_header)):
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API key")

# then add to routes:
@router.post("/sensor-data", dependencies=[Depends(verify_api_key)])
```

---

## 🟠 High

### H1 — No input length limits on `sensor_id` / `zone_id`
**`backend/schemas.py:14-15`**

Unbounded strings can exhaust memory on large payloads.

```python
# fix
sensor_id: str = Field(..., max_length=64)
zone_id:   str = Field(..., max_length=64)
```

---

### H2 — Timestamp not validated against current time
**`backend/schemas.py:18`**

Simulator (or an attacker) can insert readings with arbitrary past/future timestamps, corrupting history charts.

```python
# fix — reject readings more than 10 minutes old or in the future
from datetime import datetime, timezone, timedelta
from pydantic import field_validator

@field_validator("timestamp")
@classmethod
def timestamp_must_be_recent(cls, v: datetime) -> datetime:
    now = datetime.now(timezone.utc)
    if abs((now - v).total_seconds()) > 600:
        raise ValueError("Timestamp must be within 10 minutes of now")
    return v
```

---

### H3 — No request body size limit
**`backend/main.py`**

Unbounded request body enables memory exhaustion DoS.

```python
# fix — set in uvicorn or add middleware
# uvicorn: uvicorn main:app --limit-max-requests 1000 --limit-concurrency 50
# or in app:
from starlette.middleware.trustedhost import TrustedHostMiddleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "127.0.0.1"])
```

For request size, set `--limit-request-body` in the uvicorn startup command:
```bash
uvicorn main:app --limit-request-body 10000  # 10 KB max
```

---

### H4 — CDN scripts loaded without Subresource Integrity (SRI)
**`frontend/index.html:27-30`**

If jsdelivr is compromised, malicious JS runs in users' browsers.

```html
<!-- fix — add integrity hashes -->
<script
  src="https://cdn.jsdelivr.net/npm/react@18.2.0/umd/react.development.js"
  integrity="sha384-..."
  crossorigin="anonymous">
</script>
```

Generate hashes with: `curl -s <url> | openssl dgst -sha384 -binary | openssl base64 -A`

---

### H5 — No rate limiting on `POST /sensor-data`
**`backend/routes/sensor_data.py`**

A misconfigured simulator or attacker can flood the database with millions of readings.

```python
# fix — add slowapi rate limiting
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.post("/sensor-data")
@limiter.limit("60/minute")
def create_sensor_reading(request: Request, ...):
```

---

### H6 — No error handling on database operations
**`backend/routes/sensor_data.py:28-31`**, **`zones.py`**, **`alerts.py`**

A DB failure returns an unhandled 500 with a full SQLAlchemy stack trace exposed to the client.

```python
# fix
from sqlalchemy.exc import SQLAlchemyError

try:
    db.add(reading)
    db.commit()
    db.refresh(reading)
except SQLAlchemyError as e:
    db.rollback()
    raise HTTPException(status_code=500, detail="Database error")
```

---

### H7 — `Babel.transform()` executes arbitrary code at runtime
**`frontend/index.html:280`**

```js
var code = Babel.transform(src, { presets: ['react'] }).code;
```

Transpiling at runtime is a XSS vector if the source block is ever injectable. Also slow — adds ~300ms parse time on every page load.

**Fix:** Pre-transpile JSX using Vite or esbuild in a proper build step. For MVP, keep but document the risk clearly.

---

## 🟡 Medium

### M1 — Missing `index` on `timestamp` column
**`backend/models.py:20`**

History queries sort by `timestamp DESC` — no index means full table scan as data grows.

```python
# fix
timestamp = Column(DateTime(timezone=True), nullable=False, index=True, default=...)
```

---

### M2 — No pagination on `GET /zones`
**`backend/routes/zones.py:19`**

Returns all zones in one response. At scale this becomes an unbounded query.

```python
# fix
@router.get("/zones", response_model=list[ZoneStatus])
def list_zones(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    ...
    return results[skip : skip + limit]
```

---

### M3 — `zone_id` path parameter has no length validation
**`backend/routes/zones.py:44`**

```python
def zone_history(zone_id: str, ...):  # no length check
```

```python
# fix
from fastapi import Path
def zone_history(zone_id: str = Path(..., max_length=64), ...):
```

---

### M4 — `water_level` has no upper bound
**`backend/schemas.py:16`**

```python
water_level: float = Field(..., ge=0.0)  # no upper limit
```

A value of `999999.9` passes validation and corrupts alert logic.

```python
# fix
water_level: float = Field(..., ge=0.0, le=20.0)  # realistic max for a construction site
```

---

### M5 — Thresholds duplicated in frontend
**`frontend/index.html`** footer + **`backend/config.py`**

The frontend hardcodes `Warning ≥ 2.0 m · Critical ≥ 2.5 m` in the footer. If thresholds change in the backend, the UI text becomes stale.

**Fix:** Expose thresholds via a `GET /config` endpoint and render them from the API response.

---

### M6 — `GET /health` doesn't verify database connectivity
**`backend/main.py:38-39`**

```python
@app.get("/health")
def health_check():
    return {"status": "ok"}  # always ok, even if DB is down
```

```python
# fix
@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "db": "ok"}
    except Exception:
        raise HTTPException(503, detail={"status": "degraded", "db": "unreachable"})
```

---

### M7 — No logging in backend routes
**`backend/routes/`**

Errors are only exposed via HTTP 500. No structured logs for monitoring or debugging.

```python
# fix — add to main.py
import logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# then in routes
logger.info("Received reading: sensor=%s zone=%s level=%.3f", payload.sensor_id, payload.zone_id, payload.water_level)
```

---

### M8 — Simulator has no retry/backoff on failure
**`simulator/simulator.py:35-37`**

```python
except httpx.RequestError as exc:
    logger.warning("Could not reach backend (%s) — will retry next cycle", exc)
```

On a brief network blip, all readings for that cycle are silently dropped.

```python
# fix — simple retry
for attempt in range(3):
    try:
        response = await client.post(...)
        break
    except httpx.RequestError:
        if attempt == 2:
            logger.warning("All retries failed for %s", sensor.sensor_id)
        await asyncio.sleep(1)
```

---

### M9 — Frontend error handling doesn't distinguish error types
**`frontend/index.html:181-192`**

All fetch failures show the same generic message regardless of whether it's a 404, 500, or network timeout.

```js
// fix
} catch(e) {
  if (e.message.includes('Failed to fetch')) {
    setError('Cannot reach backend — is it running on port 8000?');
  } else if (e.message.includes('500')) {
    setError('Backend error — check server logs.');
  } else {
    setError('Unexpected error: ' + e.message);
  }
}
```

---

### M10 — History re-fetched on every zone poll
**`frontend/index.html:209-211`**

```js
useEffect(function() {
  if (selectedZone) fetchHistory(selectedZone);
}, [selectedZone, zones, fetchHistory]);  // runs on every zones update (every 5s!)
```

Every 5-second poll triggers an extra `GET /zones/{id}/history` call.

```js
// fix — only refetch history when selectedZone changes, not on every zones update
useEffect(function() {
  if (selectedZone) fetchHistory(selectedZone);
}, [selectedZone]);  // remove zones dependency
```

---

### M11 — No `__init__.py` in `backend/`
**`backend/`**, **`backend/routes/`**

Tests must manually prepend `sys.path` to import backend modules. This is fragile and non-standard.

```python
# fix — create empty files
# backend/__init__.py
# backend/routes/__init__.py
# Then tests can use: from backend.alert_service import get_zone_status
```

---

### M12 — `create_all()` used instead of migrations
**`backend/main.py:20`**

`Base.metadata.create_all()` cannot apply schema changes to an existing database. Adding a column to a model after first run has no effect.

**Fix:** Introduce [Alembic](https://alembic.sqlalchemy.org/):
```bash
pip install alembic
alembic init alembic
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

---

### M13 — Thresholds not configurable via environment
**`backend/config.py:8-9`**

```python
WARNING_THRESHOLD  = 2.0
CRITICAL_THRESHOLD = 2.5
```

Changing thresholds requires a code edit and redeploy.

```python
# fix
WARNING_THRESHOLD  = float(os.getenv("WARNING_THRESHOLD",  "2.0"))
CRITICAL_THRESHOLD = float(os.getenv("CRITICAL_THRESHOLD", "2.5"))
```

---

## 🔵 Low

### L1 — `sensor.py` constants not documented as class-level tunable knobs
**`simulator/sensor.py:19-22`**

The constants exist but have no docstring explaining which ones to tune for different simulations.

---

### L2 — `except KeyboardInterrupt` catches too broadly
**`simulator/simulator.py:62`**

```python
try:
    asyncio.run(run_simulator())
except KeyboardInterrupt:  # fine
    logger.info("Simulator stopped.")
```

Actually this is fine — but the bare `except` inside `asyncio.run` in older Python can mask `SystemExit`. Already handled correctly; add a comment for clarity.

---

### L3 — `_db_fd` variable is confusing
**`tests/conftest.py:24`**

```python
_db_fd, _db_path = tempfile.mkstemp(suffix=".test.db")
os.close(_db_fd)  # immediately closed — purpose unclear
```

```python
# fix — add comment
_db_fd, _db_path = tempfile.mkstemp(suffix=".test.db")
os.close(_db_fd)  # mkstemp returns an open fd; close it — we only need the path
```

---

### L4 — Frontend fallback hides unknown status values
**`frontend/index.html:74`**

```js
const cfg = STATUS[zone.status] || STATUS.ok;  // silently falls back
```

If backend adds a new status, the card shows green instead of an obvious error.

```js
// fix
const cfg = STATUS[zone.status];
if (!cfg) { console.error('Unknown status:', zone.status); }
return cfg || STATUS.ok;
```

---

### L5 — No `pytest.ini` or `pyproject.toml`
**`tests/`**

Test configuration (test paths, markers, asyncio mode) is implicit. Add a `pytest.ini`:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

---

### L6 — No `.env.example` file
**project root**

There are multiple env vars (`DATABASE_URL`, `API_KEY`, `BACKEND_URL`, `ALLOWED_ORIGINS`) with no documented defaults.

```bash
# fix — create .env.example
DATABASE_URL=sqlite:///./construction.db
BACKEND_URL=http://localhost:8000/sensor-data
ALLOWED_ORIGINS=http://localhost:3000
WARNING_THRESHOLD=2.0
CRITICAL_THRESHOLD=2.5
API_KEY=changeme
```

---

### L7 — No `HISTORY_LIMIT` upper-bound test
**`tests/test_routes.py`**

The 100-row cap in `backend/config.py` has no test verifying it is enforced.

---

### L8 — `GET /zones` response includes `timestamp` but not `sensor_id`
**`backend/schemas.py:32-37`**

The `ZoneStatus` schema doesn't expose which sensor produced the latest reading, making debugging harder.

---

### L9 — `docs/PLAN.md` thresholds not kept in sync with `config.py`
**`docs/PLAN.md`**

Thresholds are documented as hardcoded values. If `config.py` is changed, the doc silently goes stale.

---

### L10 — Simulator sends all sensors in parallel but logs individually
**`simulator/simulator.py:43`**

`asyncio.gather()` fires all sensors at once, but logs appear serially. A single summary log per cycle would be cleaner.

---

### L11 — `conftest.py` `pytest_sessionfinish` hook may not run on crash
**`tests/conftest.py:60-65`**

If pytest crashes (not exits), the temp DB file leaks. Use `atexit` as a safety net:

```python
import atexit
atexit.register(lambda: os.unlink(_db_path) if os.path.exists(_db_path) else None)
```

---

### L12 — No `Content-Security-Policy` header on frontend
**`frontend/index.html`**

No CSP header means injected scripts (via XSS) run freely.

```html
<!-- fix — add meta CSP -->
<meta http-equiv="Content-Security-Policy"
  content="default-src 'self'; script-src 'self' cdn.jsdelivr.net 'unsafe-inline';">
```

---

### L13 — Backend has no structured startup banner
**`backend/main.py`**

On startup there's no log showing which DB, thresholds, or port are active. Helpful for ops.

```python
# fix — add to lifespan
logger.info("SiteSense API starting | DB=%s | WARNING=%.1f | CRITICAL=%.1f",
            DATABASE_URL, WARNING_THRESHOLD, CRITICAL_THRESHOLD)
```

---

## Recommended Fix Order

```
Priority 1 (before any deployment)
  C1  Fix CORS — restrict allowed origins
  C4  Pin requirements.txt versions
  C5  Add API key authentication
  H6  Add DB error handling (don't leak stack traces)
  H5  Add rate limiting to POST /sensor-data

Priority 2 (before production)
  C2  Move BACKEND_URL to env var (simulator)
  C3  Move BASE_URL to env var (frontend)
  H1  Add max_length to sensor_id / zone_id
  H4  Add SRI hashes to CDN scripts
  M10 Fix history re-fetch on every poll cycle

Priority 3 (code quality pass)
  M1  Add timestamp index to DB
  M5  Expose thresholds via API instead of hardcoding in frontend
  M6  Make /health check the DB
  M11 Add __init__.py files
  M12 Introduce Alembic migrations
  L6  Add .env.example
```
