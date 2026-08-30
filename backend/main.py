# main.py
# FastAPI application factory.
# Mounts all routers, enables CORS, and creates DB tables on startup.

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routes.alerts import router as alerts_router
from routes.sensor_data import router as sensor_data_router
from routes.zones import router as zones_router

# Create all tables (no-op if they already exist)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SiteSense API",
    description="Construction site sensor logistics backend",
    version="1.0.0",
)

# Allow all origins for MVP (tighten for production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(sensor_data_router)
app.include_router(zones_router)
app.include_router(alerts_router)


@app.get("/health", tags=["meta"])
def health_check():
    return {"status": "ok"}
