import uuid
from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.dialects.postgresql import UUID
from shared.database.connection import Base

class AgentDecision(Base):
    __tablename__ = "agent_decisions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_name = Column(String, nullable=False)
    incident_id = Column(UUID(as_uuid=True), nullable=True)
    input_data = Column(JSON, nullable=True)
    reasoning = Column(Text, nullable=False)
    action_taken = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    human_override = Column(String, default="false")
    override_reason = Column(Text, nullable=True)
    outcome = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
