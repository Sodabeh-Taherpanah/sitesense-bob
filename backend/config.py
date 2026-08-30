# config.py
# Backend configuration: database connection string and alert thresholds.
# Override DATABASE_URL via environment variable to switch from SQLite to PostgreSQL.

import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./construction.db")

# Water level thresholds (meters)
WARNING_THRESHOLD = 2.0
CRITICAL_THRESHOLD = 2.5

# How many historical readings to return per zone
HISTORY_LIMIT = 100
