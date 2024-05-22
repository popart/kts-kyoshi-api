from dataclasses import dataclass
from enum import Enum
import uuid

import db_models


class JLPTLevel(Enum):
    """Should sort descending. N1 is 0 so that default (UNKNOWN) is last."""

    UNKNOWN = -1
    N1 = 0
    N2 = 1
    N3 = 2
    N4 = 3
    N5 = 4


@dataclass
class FlashCardContent:
    input_text: str | None
    translated_text: str | None
    japanese_example: str | None
    dictionary_form: str | None
    teaching_notes: str | None
    jlpt_level: str | None


@dataclass
class FlashCardResponse:
    flash_card_id: uuid.UUID
    flash_card_content: FlashCardContent


def flash_card_to_flash_card_response(card: db_models.FlashCard) -> FlashCardResponse:
    return FlashCardResponse(
        flash_card_id=card.flash_card_id,
        flash_card_content=FlashCardContent(**card.content),
    )
