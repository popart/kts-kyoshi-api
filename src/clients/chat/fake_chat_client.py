from typing import override

from clients.chat.abstract_chat_client import AbstractChatClient
from data_types import chat_types


SAMPLE_LESSON = {
    "student_input": "しょうがない、それでいこう",
    "tutor_response": "It can't be helped, let's go with that.",
    "example_sentence": "しょうがない、それでいこう",
    "example_sentence_translation": "It can't be helped, let's go with that.",
    "japanese_flash_cards": [
        {
            "japanese_example": "しょうがない",
            "dictionary_form": "仕方(しかた)がない",
            "teaching_notes": "Expression: 'It can't be helped' or 'nothing can be done about it.' Often used to express resignation or acceptance of a situation.",
            "jlpt_level": "N4",
        },
        {
            "japanese_example": "それで",
            "dictionary_form": "それで",
            "teaching_notes": "Conjunction: 'and with that,' 'therefore,' or 'because of that.' Used to connect sentences or clauses, indicating a cause or reason leading to a result.",
            "jlpt_level": "N5",
        },
        {
            "japanese_example": "いこう",
            "dictionary_form": "行(い)く",
            "teaching_notes": "Verb: volitional form of the verb '行(い)く' (to go), used to express a decision or suggestion about the future, equivalent to saying 'let's go' in English.",
            "jlpt_level": "N5",
        },
    ],
}


class FakeChatClient(AbstractChatClient):
    def __init__(self, response_type: str = "CHAT", lesson: dict = SAMPLE_LESSON):
        self.response_type = response_type
        self.lesson = lesson

    @override
    def complete_chat(
        self,
        input_messages: list[chat_types.ChatMessage],
        response_model,
    ):
        lesson = dict(self.lesson)
        if self.response_type == "CHAT":
            lesson["tutor_response"] = "Well, hello, stranger..."
        return response_model.model_validate(lesson)