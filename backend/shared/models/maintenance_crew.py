import uuid
from sqlalchemy import Column, String, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from shared.database.connection import Base

class MaintenanceCrew(Base):
    __tablename__ = "maintenance_crews"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    zone = Column(String, nullable=False)
    specialization = Column(String, nullable=True)
    status = Column(String, default="available")
    members = Column(Integer, default=4)
    current_location = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
