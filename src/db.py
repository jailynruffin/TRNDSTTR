from pathlib import Path
from sqlalchemy import create_engine

DB_URL = "sqlite:///db/trends.db"
Path("db").mkdir(parents=True, exist_ok=True)
engine = create_engine(DB_URL, future=True)
