from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from database import Base

class Incident(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    error_message = Column(Text, nullable=False)
    sap_module = Column(String(50))
    root_cause = Column(Text)
    impact = Column(Text)
    resolution_steps = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    source = Column(String(20))  # "cache" or "ai"