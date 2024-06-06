from datetime import datetime, timezone
from dataclasses import asdict
import uuid

import fsrs
from sqlalchemy import case, desc, func, select, Engine
from sqlalchemy.orm import Session
import db_models
from data_types import chat_response_types, flash_card_types


def create_or_update_flash_card(
    engine: Engine,
    user_id: uuid.UUID,
    chat_id: uuid.UUID,
    chat_message_id: uuid.UUID,
    flash_card_index: int,
    flash_card_lesson: chat_response_types.FlashCardLesson,
    flash_card: chat_response_types.FlashCard,
    is_active: bool,
):
    content = asdict(
        flash_card_types.FlashCardContent(
            example_sentence=flash_card_lesson.example_sentence,
            example_sentence_translation=flash_card_lesson.example_sentence_translation,
            japanese_example=flash_card.japanese_example,
            dictionary_form=flash_card.dictionary_form,
            teaching_notes=flash_card.teaching_notes,
            jlpt_level=flash_card.jlpt_level,
        )
    )
    try:
        jlpt_level = flash_card_types.JLPTLevel[flash_card.jlpt_level].value
    except KeyError:
        jlpt_level = flash_card_types.JLPTLevel.UNKNOWN.value

    fsrs_card = fsrs.Card()

    existing_instance_stmt = (
        select(db_models.FlashCard)
        .where(db_models.FlashCard.user_id == user_id)
        .where(db_models.FlashCard.chat_id == chat_id)
        .where(db_models.FlashCard.chat_message_id == chat_message_id)
        .where(db_models.FlashCard.flash_card_index == flash_card_index)
        .with_for_update(nowait=True)
    )
    with Session(engine) as session:
        instance = session.execute(existing_instance_stmt).scalar_one_or_none()
        if instance:
            instance.is_active = is_active
            # whenever card is bookmarked, it should show up in new pile
            # but don't reset fsrs stats or due date
            instance.fsrs_state = fsrs.State.New.value
        else:
            instance = db_models.FlashCard(
                user_id=user_id,
                chat_id=chat_id,
                chat_message_id=chat_message_id,
                flash_card_index=flash_card_index,
                content=content,
                jlpt_level=jlpt_level,
                fsrs=fsrs_card.to_dict(),
                fsrs_due_at=fsrs_card.due,
                fsrs_state=fsrs_card.state.value,
                is_active=is_active,
            )
        session.add(instance)
        session.commit()


def delete_flash_card(
    engine: Engine,
    user_id: uuid.UUID,
    flash_card_id: uuid.UUID,
):
    existing_instance_stmt = (
        select(db_models.FlashCard)
        .where(db_models.FlashCard.user_id == user_id)
        .where(db_models.FlashCard.flash_card_id == flash_card_id)
        .with_for_update(nowait=True)
    )
    with Session(engine) as session:
        instance = session.execute(existing_instance_stmt).scalar_one_or_none()

        if instance:
            instance.is_active = False
            instance.fsrs_state = fsrs.State.New.value

            session.add(instance)
            session.commit()


def review_flash_card(
    engine: Engine,
    user_id: uuid.UUID,
    flash_card_id: uuid.UUID,
    rating: str,
):

    with Session(engine) as session:
        stmt = (
            select(db_models.FlashCard)
            .where(db_models.FlashCard.flash_card_id == flash_card_id)
            .where(db_models.FlashCard.user_id == user_id)
        )
        flash_card = session.execute(stmt).scalar_one_or_none()
        assert flash_card is not None

        if rating == "ADD_TO_REVIEW" and flash_card.fsrs_state == fsrs.State.New.value:
            flash_card.fsrs_state = fsrs.State.Review.value
        else:
            f = fsrs.FSRS()
            fsrs_card = fsrs.Card.from_dict(flash_card.fsrs)
            scheduling_cards = f.repeat(fsrs_card, datetime.now(tz=timezone.utc))
            new_card = scheduling_cards[fsrs.Rating[rating]].card

            flash_card.fsrs_card = new_card
            flash_card.fsrs_due_at = new_card.due
            flash_card.fsrs_state = new_card.state

        session.commit()


def get_flash_cards_new(engine: Engine, user_id: uuid.UUID):
    # TODO: paginate
    stmt = (
        select(db_models.FlashCard)
        .where(db_models.FlashCard.user_id == user_id)
        .where(db_models.FlashCard.fsrs_state == fsrs.State.New.value)
        .where(db_models.FlashCard.is_active)
        .order_by(desc(db_models.FlashCard.jlpt_level))
        .order_by(db_models.FlashCard.created_at)
        .limit(100)
    )
    with Session(engine) as session:
        return [row[0] for row in session.execute(stmt).fetchall()]


def get_flash_cards_review(engine: Engine, user_id: uuid.UUID):
    stmt = (
        select(db_models.FlashCard)
        .where(db_models.FlashCard.user_id == user_id)
        .where(db_models.FlashCard.fsrs_state > fsrs.State.New.value)
        .where(db_models.FlashCard.fsrs_due_at < datetime.now(tz=timezone.utc))
        .where(db_models.FlashCard.is_active)
        .order_by(db_models.FlashCard.fsrs_due_at)
        .limit(10)
    )
    with Session(engine) as session:
        return [row[0] for row in session.execute(stmt).fetchall()]


def get_flash_cards_all(engine: Engine, user_id: uuid.UUID):
    """TODO: paginate"""
    stmt = (
        select(db_models.FlashCard)
        .where(db_models.FlashCard.user_id == user_id)
        .order_by(db_models.FlashCard.created_at)
        .limit(100)
    )
    with Session(engine) as session:
        return [row[0] for row in session.execute(stmt).fetchall()]


def get_flash_card_counts(engine: Engine, user_id: uuid.UUID):
    is_due = case(
        (db_models.FlashCard.fsrs_due_at < datetime.now(tz=timezone.utc), True),
        else_=False,
    ).label("is_due")
    stmt = (
        select(
            db_models.FlashCard.fsrs_state,
            is_due,
            func.count(),
        )
        .where(db_models.FlashCard.user_id == user_id)
        .where(db_models.FlashCard.is_active)
        .group_by(db_models.FlashCard.fsrs_state, is_due)
    )
    with Session(engine) as session:
        return session.execute(stmt).all()
