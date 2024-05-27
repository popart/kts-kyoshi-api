"""Chat related DB models."""

import uuid

from sqlalchemy import Boolean, Column, String, DateTime, JSON, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from db_models import declarative_base

Base = declarative_base.Base


class Chat(Base):
    __tablename__ = "chat"
    chat_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    chat_name = Column(String, nullable=False, server_default=text("''"))
    llm_provider = Column(String, nullable=False)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    is_active = Column(Boolean, nullable=False, server_default=text("TRUE"))


class ChatMessage(Base):
    __tablename__ = "chat_message"
    chat_message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    chat_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    content = Column(JSON, nullable=False)  # should match the ChatMessage type
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
