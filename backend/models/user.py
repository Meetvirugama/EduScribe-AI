import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
from core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    google_id = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    picture = Column(String, nullable=True)
    # ISSUE-003: is_admin field for admin RBAC — defaults to False for all users
    is_admin = Column(Boolean, nullable=False, default=False)
    # ISSUE-004: timezone-aware datetime
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(tz=timezone.utc))
