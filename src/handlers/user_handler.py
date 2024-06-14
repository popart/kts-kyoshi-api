from functools import lru_cache
import uuid

from sqlalchemy import exists, select, update, Engine
from sqlalchemy.orm import Session

import db_models


@lru_cache()
def get_user_id(engine: Engine, openid_sub: str) -> uuid.UUID | None:
    """Cached method to fetch the UUID for a User by openid_sub

    Should only be used for Users that already exist.
    Don't want to cache a None value and then create the User.
    """
    stmt = select(db_models.User.user_id).where(db_models.User.openid_sub == openid_sub)

    with Session(engine) as session:
        return session.execute(stmt).scalar()


def get_user_is_active(engine: Engine, user_id: uuid.UUID) -> bool:
    stmt = select(db_models.User.is_active).where(db_models.User.user_id == user_id)

    with Session(engine) as session:
        return session.execute(stmt).scalar()


def get_user_settings(engine: Engine, user_id: uuid.UUID) -> bool:
    stmt = select(db_models.User.settings).where(db_models.User.user_id == user_id)

    with Session(engine) as session:
        return session.execute(stmt).scalar()


def save_user_settings(engine: Engine, user_id: uuid.UUID, settings: dict) -> bool:
    print(settings)
    stmt = (
        update(db_models.User)
        .where(db_models.User.user_id == user_id)
        .values(settings=settings)
    )

    with Session(engine) as session:
        session.execute(stmt)
        session.commit()


def user_exists(engine: Engine, openid_sub: str) -> bool:
    stmt = exists().where(db_models.User.openid_sub == openid_sub)

    with Session(engine) as session:
        return session.query(stmt).scalar()


def create_user(engine: Engine, openid_sub: str, email: str) -> db_models.User:
    new_user = db_models.User(
        openid_sub=openid_sub,
        email=email,
    )

    with Session(engine) as session:
        session.add(new_user)
        session.commit()
        return new_user
