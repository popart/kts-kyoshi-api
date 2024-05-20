from dataclasses import asdict
import uuid

from sqlalchemy import desc, func, select, Engine
from sqlalchemy.orm import Session
import db_models
from data_types import chat_types


def create_chat(engine: Engine, user_id: uuid.UUID):
    chat = db_models.Chat(
        user_id=user_id,
        llm_provider="OPENAI",
    )
    with Session(engine) as session:
        session.add(chat)
        session.commit()


def get_chats(engine: Engine, user_id: uuid.UUID) -> list[db_models.Chat]:
    stmt = (
        select(db_models.Chat)
        .where(db_models.Chat.user_id == user_id)
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
    engine: Engine, user_id: uuid.UUID, chat_id: uuid.UUID
) -> list[(uuid.UUID, chat_types.ChatMessage, list[int])]:
    # first aggregate the saved_flash_card_indexes
    # (used to show which flash_card items have already been created)
    stmt_sub = (
        select(db_models.ChatMessage.chat_message_id,
               func.array_agg(db_models.FlashCard.flash_card_index).label("saved_flash_card_indexes"))
        .outerjoin(
            db_models.FlashCard,
            (db_models.ChatMessage.chat_message_id == db_models.FlashCard.chat_message_id)
            & (db_models.FlashCard.is_active))
        .where(db_models.ChatMessage.user_id == user_id)
        .where(db_models.ChatMessage.chat_id == chat_id)
        .group_by(db_models.ChatMessage.chat_message_id)
        .order_by(desc(db_models.ChatMessage.created_at))
        .limit(100)
    ).alias("stmt_sub")

    # then add on the content
    # (done separately b/c json columns don't aggregate)
    stmt = (
        select(stmt_sub.c.chat_message_id, db_models.ChatMessage.content, stmt_sub.c.saved_flash_card_indexes)
        .select_from(stmt_sub.join(db_models.ChatMessage, stmt_sub.c.chat_message_id == db_models.ChatMessage.chat_message_id))
        .order_by(desc(db_models.ChatMessage.created_at))
    )
    with Session(engine) as session:
        result = session.execute(stmt).fetchall()
        return [(
            row[0],
            chat_types.dict_to_chat_message(row[1]),
            [x for x in row[2] if x is not None],
        ) for row in result]

def get_chat_message(
    engine: Engine, user_id: uuid.UUID, chat_id: uuid.UUID, chat_message_id: uuid.UUID
) -> chat_types.ChatMessage:
    stmt = (
        select(db_models.ChatMessage.content)
        .where(db_models.ChatMessage.user_id == user_id)
        .where(db_models.ChatMessage.chat_id == chat_id)
        .where(db_models.ChatMessage.chat_message_id == chat_message_id)
    )
    with Session(engine) as session:
        res = session.execute(stmt).scalar_one_or_none()
        return chat_types.dict_to_chat_message(res) if res else None

def save_chat_messages(
    engine: Engine,
    user_id: uuid.UUID,
    chat_id: uuid.UUID,
    chat_messages: list[chat_types.ChatMessage],
):
    messages = [
        db_models.ChatMessage(chat_id=chat_id, user_id=user_id, content=asdict(cm))
        for cm in chat_messages
    ]

    # insert serially to preserve created_at order
    for message in messages:
        with Session(engine) as session:
            session.add(message)
            session.commit()
