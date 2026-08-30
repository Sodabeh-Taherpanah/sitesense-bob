# conftest.py
# Shared pytest fixtures:
#   - in-memory SQLite database (fresh per test)
#   - FastAPI TestClient wired to the in-memory DB
# Using fixtures here keeps each test file free of setup boilerplate.
