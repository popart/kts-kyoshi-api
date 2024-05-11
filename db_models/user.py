"""User related DB models."""
import sqlalchemy as sa
from sqlalchemy.sql import func

from db_models import declarative_base

Base = declarative_base.Base

class User(Base):
    __tablename__ = "user"
    user_id = sa.Column(sa.String, primary_key=True)
    email = sa.Column(sa.String, unique=True, nullable=False)
    time_created = sa.Column(sa.DateTime(timezone=True), server_default=func.now())
    is_active = sa.Column(sa.Boolean, nullable=False, default=True)
