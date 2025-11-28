from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True)
    customer = Column(String, index=True, nullable=False)
    title = Column(String, nullable=False)
    brief = Column(JSON, default={})
    agenda = Column(JSON, default=[])
    created_at = Column(DateTime, default=datetime.utcnow)
