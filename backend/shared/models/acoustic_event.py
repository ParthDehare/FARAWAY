import uuid
from sqlalchemy import Column, String, Float, DateTime, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from shared.database.connection import Base

class AcousticEvent(Base):
    __tablename__ = "acoustic_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    segment_id = Column(UUID(as_uuid=True), ForeignKey("segments.id"), nullable=False)
    event_type = Column(String, nullable=False)
    severity = Column(String, nullable=False, default="info")
    confidence = Column(Float, nullable=False)
    raw_features = Column(JSON, nullable=True)
    recorded_at = Column(DateTime(timezone=True), server_default=func.now())
