"""Types for API interface"""

from dataclasses import dataclass
import enum
import uuid

from data_types import chat_types


class ChatMessageResponseType(enum.StrEnum):
    UNDEFINED = "undefined"
    MESSAGE = "message"
    FLASH_CARD_LESSON = "flash_card_lesson"


@dataclass
class FlashCard:
    japanese_example: str | None
    dictionary_form: str | None
    teaching_notes: str | None
    jlpt_level: str | None
    is_saved: bool = False


@dataclass
class FlashCardLesson:
    student_input: str | None
    tutor_response: str | None
    example_sentence: str | None
    example_sentence_translation: str | None
    flash_cards: list[FlashCard]


@dataclass
class ChatMessageResponse:
    chat_id: uuid.UUID
    chat_message_id: uuid.UUID
    role: str
    message_type: ChatMessageResponseType
    message: str | None
    flash_card_lesson: FlashCardLesson | None


def chat_message_to_chat_message_response(
    chat_id: uuid.UUID,
    chat_message_id: uuid.UUID,
    chat_message: chat_types.ChatMessage,
    saved_flash_card_indexes: list[int] = None,
) -> ChatMessageResponse:
    flash_card_lesson = None
    message_type = ChatMessageResponseType.UNDEFINED

    if chat_message.lesson:
        message_type = ChatMessageResponseType.FLASH_CARD_LESSON
        lesson = chat_message.lesson

        flash_cards = [
            FlashCard(
                japanese_example=card.japanese_example,
                dictionary_form=card.dictionary_form,
                teaching_notes=card.teaching_notes,
                jlpt_level=card.jlpt_level,
            )
            for card in lesson.japanese_flash_cards
        ]

        if saved_flash_card_indexes:
            for i in saved_flash_card_indexes:
                flash_cards[i].is_saved = True

        flash_card_lesson = FlashCardLesson(
            student_input=lesson.student_input,
            tutor_response=lesson.tutor_response,
            example_sentence=lesson.example_sentence,
            example_sentence_translation=lesson.example_sentence_translation,
            flash_cards=flash_cards,
        )
    elif chat_message.content:
        message_type = ChatMessageResponseType.MESSAGE

    return ChatMessageResponse(
        chat_id=chat_id,
        chat_message_id=chat_message_id,
        role=chat_message.role,
        message_type=message_type,
        message=chat_message.content,
        flash_card_lesson=flash_card_lesson,
    )