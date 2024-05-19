from dataclasses import asdict
import uuid

import fsrs
from sqlalchemy import desc, select, Engine
from sqlalchemy.orm import Session
import db_models
from data_types import chat_types
from data_types import chat_response_types

def create_chat(
        engine: Engine,
        user_id: uuid.UUID,
        chat_id: uuid.UUID,
        chat_message_id: uuid.UUID,
        flash_card_lesson: chat_response_types.FlashCardLesson,
        flash_card: chat_response_types.FlashCard,
    ):
    content = flash_card_types.FlashCardContent(
        input_text=flash_card_lesson.input_text,
        translated_text=flash_card_lesson.translated_text,
        japanese_example=flash_card.japanese_example,
        dictionary_form=flash_card.dictionary_form,
        teaching_notes=flash_card.teaching_notes,
        jlpt_level=flash_card.jlpt_level,
    )

    fsrs_card = fsrs.Card()

    flash_card = db_models.FlashCard(
        user_id=user_id,
        chat_id=chat_id,
        chat_message_id=chat_message_id,
        content=content,
        fsrs=fsrs_card.to_dict(),
        fsrs_due_at=fsrs_card.due,
        fsrs_state=fsrs_card.state.value,
    )
    with Session(engine) as session:
        session.add(flash_card)
        session.commit()

def get_flash_cards_new(engine: Engine, user_id: uuid.UUID):
    stmt = (
        select(db_models.FlashCard)
        .where(db_models.FlashCard.user_id == user_id)
        .where(db_models.FlashCard.fsrs_state == fsrs.state.New.value)
        .order_by(db_models.FlashCard.created_at)
    )
    with Session(engine) as session:
        return session.execute(stmt).fetchall()


def get_flash_cards_review(engine: Engine, user_id: uuid.UUID):
    stmt = (
        select(db_models.FlashCard)
        .where(db_models.FlashCard.user_id == user_id)
        .where(db_models.FlashCard.fsrs_state > fsrs.state.New.value)
        .order_by(db_models.FlashCard.created_at)
    )
    with Session(engine) as session:
        return session.execute(stmt).fetchall()

def get_flash_cards_all(engine: Engine, user_id: uuid.UUID):
    """ TODO: paginate """
    stmt = (
        select(db_models.FlashCard)
        .where(db_models.FlashCard.user_id == user_id)
        .order_by(db_models.FlashCard.created_at)
        .limit(100)
    )
    with Session(engine) as session:
        return session.execute(stmt).fetchall()
