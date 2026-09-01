# SiteSense — System Architecture & Data Flow

> Diagrams render natively on GitHub. All Mermaid blocks below are self-contained.

---

## 1. High-Level System Overview

```mermaid
graph TD
    subgraph SIM["🏗 Sensor Simulator (Python)"]
        S1[sensor-A1\nzone-north]
        S2[sensor-A2\nzone-north]
        S3[sensor-B1\nzone-south]
        S4[sensor-C1\nzone-east]
        S5[sensor-D1\nzone-west]
    end

    subgraph API["⚙️ Backend API (FastAPI)"]
        R1[POST /sensor-data]
        R2[GET /zones]
        R3[GET /zones/:id/history]
        R4[GET /alerts]
        AL[alert_service.py\nget_zone_status\nis_alert]
    end

    subgraph DB["🗄️ Database (SQLite / PostgreSQL)"]
        T[(sensor_readings\ntable)]
    end

    subgraph FE["🖥️ Dashboard (React)"]
        ZC[Zone Cards\ngreen / yellow / red]
        AL2[Alert Panel]
        CH[History Chart\nRecharts]
    end

    S1 & S2 & S3 & S4 & S5 -->|HTTP POST every 5s| R1
    R1 -->|persist| T
    R1 --> AL
    AL -->|status flag| T

    T -->|latest per zone| R2
    T -->|last 100 rows| R3
    T -->|critical zones| R4

    R2 -->|poll every 5s| ZC
    R4 -->|poll every 5s| AL2
    R3 -->|on card click| CH
```

---

## 2. Sensor Simulator — Internal Flow

```mermaid
flowchart LR
    CFG[config.py\nSENSORS list]
    CFG -->|instantiate| SN[Sensor\nobject]

    subgraph LOOP["asyncio loop — every SEND_INTERVAL_SECONDS"]
        SN -->|read| RD["read()\nBrownian-motion step\n± 0.08 m + 0.002 drift\nclamp 0–4 m"]
        RD -->|plain dict| POST["httpx.AsyncClient\nPOST /sensor-data"]
        POST -->|201 OK| LOG[INFO log]
        POST -->|error| WARN[WARNING log\nretry next cycle]
    end
```

---

## 3. Backend API — Request Lifecycle

```mermaid
sequenceDiagram
    participant SIM as Simulator
    participant API as FastAPI
    participant DB  as SQLite
    participant FE  as Dashboard

    SIM->>API: POST /sensor-data {sensor_id, zone_id, water_level, timestamp}
    API->>API: Pydantic validation (water_level ≥ 0)
    API->>DB: INSERT INTO sensor_readings
    API-->>SIM: 201 Created {id, ...}

    loop Every 5 seconds
        FE->>API: GET /zones
        API->>DB: SELECT MAX(id) GROUP BY zone_id
        API->>API: get_zone_status(water_level)
        API-->>FE: [{zone_id, latest_water_level, status, timestamp}]

        FE->>API: GET /alerts
        API->>DB: SELECT MAX(id) GROUP BY zone_id
        API->>API: is_alert(water_level)
        API-->>FE: [{zone_id, latest_water_level, timestamp}]
    end

    FE->>API: GET /zones/{zone_id}/history  (on card click)
    API->>DB: SELECT last 100 rows ORDER BY timestamp DESC
    API-->>FE: [{id, sensor_id, zone_id, water_level, timestamp}]
```

---

## 4. Alert Logic — Status Classification

```mermaid
flowchart TD
    W[water_level\nfloat meters]
    W --> C1{">= 2.5 m\nCRITICAL_THRESHOLD?"}
    C1 -->|Yes| CRIT["🔴 critical\nis_alert = True\nappears in GET /alerts"]
    C1 -->|No| C2{">= 2.0 m\nWARNING_THRESHOLD?"}
    C2 -->|Yes| WARN["🟡 warning\nis_alert = False"]
    C2 -->|No| OK["🟢 ok\nis_alert = False"]
```

---

## 5. Frontend Polling Cycle

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Fetching : setInterval fires (5s)
    Fetching --> Fetching : GET /zones + GET /alerts\nin parallel
    Fetching --> Rendering : responses received
    Rendering --> Idle : React re-renders ZoneCards + AlertList

    Idle --> LoadingHistory : user clicks a ZoneCard
    LoadingHistory --> Rendering : GET /zones/:id/history received
    Rendering --> Idle : ZoneChart updates

    Fetching --> Error : network failure
    Error --> Idle : warning banner shown\nnext poll retries
```

---

## 6. Database Schema

```mermaid
erDiagram
    SENSOR_READINGS {
        int     id           PK
        string  sensor_id
        string  zone_id
        float   water_level
        datetime timestamp
    }
```

> Single flat table for MVP simplicity.
> Query pattern: `SELECT MAX(id) … GROUP BY zone_id` to get the latest reading per zone without N+1.

---

## 7. Deployment Overview

```mermaid
graph LR
    subgraph Local["Local Machine"]
        SIM["simulator.py\npython simulator.py"]
        BE["uvicorn main:app\nport 8000"]
        FE["python -m http.server\nport 3000"]
        DB2[("construction.db\nSQLite file")]
    end

    SIM -->|POST :8000| BE
    BE <-->|read/write| DB2
    FE -->|GET :8000| BE
    BROWSER["Browser\nlocalhost:3000"] --> FE

    style DB2 fill:#f5f5f5,stroke:#ccc
```

> **To switch to PostgreSQL:** set `DATABASE_URL=postgresql://user:pw@host/db`
> before starting the backend — no code changes required.
