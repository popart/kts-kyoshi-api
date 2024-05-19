"""FlashCard DB model."""

import uuid

from sqlalchemy import Column, Integer, DateTime, DefaultClause, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from db_models import declarative_base

Base = declarative_base.Base


class FlashCard(Base):
    __tablename__ = "flash_card"
    flash_card_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    chat_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    chat_message_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    flash_card_index = Column(Integer, nullable=False)

    content = Column(JSON, nullable=False)
        
    # FSRS data, contains all info for fsrs.Card.to_dict()
    fsrs = Column(JSON, nullable=False)
    # FSRS due date, for querying cards that are due
    fsrs_due_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # FSRS state, for querying NEW cards etc
    fsrs_state = Column(Integer, nullable=False, server_default=DefaultClause('0'))

    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
