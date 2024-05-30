"""User related DB models."""

import uuid

from sqlalchemy import Boolean, Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from db_models import declarative_base

Base = declarative_base.Base


class User(Base):
    __tablename__ = "user"
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    openid_sub = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
