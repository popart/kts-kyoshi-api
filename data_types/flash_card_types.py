from dataclasses import dataclass
import uuid

import db_models

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
        flash_card_content=FlashCardContent(
            **card.content
        )
    )
