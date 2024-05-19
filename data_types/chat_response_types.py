"""Types for API interface"""
from dataclasses import dataclass
import enum
import json
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
    input_text: str | None
    translated_text: str | None
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

    if chat_message.content:
        message_type = ChatMessageResponseType.MESSAGE
    elif chat_message.tool_calls:
        message_type = ChatMessageResponseType.FLASH_CARD_LESSON
        fn_args = json.loads(chat_message.tool_calls[0].function.arguments)
        print(fn_args)

        flash_cards = [
            FlashCard(
                japanese_example=card.get("japanese_example"),
                dictionary_form=card.get("dictionary_form"),
                teaching_notes=card.get("teaching_notes"),
                jlpt_level=card.get("jlpt_level"),
            )
            for card in fn_args.get("japanese_flash_cards", [])
        ]

        if saved_flash_card_indexes:
            for i in saved_flash_card_indexes:
                flash_cards[i].is_saved = True

        flash_card_lesson = FlashCardLesson(
            input_text=fn_args.get("input_text", ""),
            translated_text=fn_args.get("translated_text", ""),
            flash_cards=flash_cards,
        )

    return ChatMessageResponse(
        chat_id=chat_id,
        chat_message_id=chat_message_id,
        role=chat_message.role,
        message_type=message_type,
        message=chat_message.content,
        flash_card_lesson=flash_card_lesson,
    )
