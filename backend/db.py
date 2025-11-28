from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.models import Base

DB_PATH = Path("data/stratgen.db").as_posix()
ENGINE = create_engine(f"sqlite:///{DB_PATH}", future=True)
SessionLocal = sessionmaker(bind=ENGINE, expire_on_commit=False)

def init_db():
    Path("data").mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(ENGINE)
