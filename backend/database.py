# database.py
# SQLAlchemy engine and session factory.
# All other modules import `get_db` (a FastAPI dependency) to access a DB session.
# Swapping the database engine only requires changing DATABASE_URL in config.py.
