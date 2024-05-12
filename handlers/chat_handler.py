from dataclasses import asdict
import uuid

from sqlalchemy import desc, select, Engine
from sqlalchemy.orm import Session
import db_models
from data_types import chat_types


def _get_god_user_id(engine: Engine) -> uuid.UUID:
    """dev method to fetch the god user id"""
    stmt = select(db_models.User.user_id).where(
        db_models.User.email == "god@tsunderegeniuslabs.com"
    )

    with Session(engine) as session:
        result = session.execute(stmt).scalar()
        assert isinstance(result, uuid.UUID), "Expected a UUID, got None or other type"
        return result


def create_chat(engine: Engine):
    god_user_id = _get_god_user_id(engine)
    chat = db_models.Chat(
        user_id=god_user_id,
        llm_provider="OPENAI",
    )
    with Session(engine) as session:
        session.add(chat)
        session.commit()


def get_chats(engine: Engine) -> list[db_models.Chat]:
    god_user_id = _get_god_user_id(engine)
    stmt = (
        select(db_models.Chat)
        .where(db_models.Chat.user_id == god_user_id)
        .order_by(desc(db_models.Chat.created_at))
    )
    with Session(engine) as session:
        return [
            chat_types.Chat(
                user_id=c.user_id,
                chat_id=c.chat_id,
                created_at=c.created_at,
            )
            for c in session.scalars(stmt)
        ]


def get_chat_messages(
    engine: Engine, chat_id: uuid.UUID
) -> list[chat_types.ChatMessage]:
    stmt = (
        select(db_models.ChatMessage.content)
        .where(db_models.ChatMessage.chat_id == chat_id)
        .order_by(desc(db_models.ChatMessage.created_at))
        .limit(10)
    )
    with Session(engine) as session:
        result = session.execute(stmt).fetchall()
        return [chat_types.dict_to_chat_message(row[0]) for row in result]


def save_chat_messages(
    engine: Engine, chat_id: uuid.UUID, chat_messages: list[chat_types.ChatMessage]
):
    god_user_id = _get_god_user_id(engine)
    messages = [
        db_models.ChatMessage(chat_id=chat_id, user_id=god_user_id, content=asdict(cm))
        for cm in chat_messages
    ]

    # insert serially to preserve created_at order
    for message in messages:
        with Session(engine) as session:
            session.add(message)
            session.commit()
