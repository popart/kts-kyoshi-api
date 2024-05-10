import json
from typing import override

from clients.chat import chat_types
from clients.chat.abstract_chat_client import AbstractChatClient

SAMPLE_FLASH_CARDS =  {
    "japanese_flash_cards": [
        {
            "japanese_example":"しょうがない",
            "dictionary_form":"仕方がない(しかたがない)",
            "teaching_notes":"Expression: 'It can't be helped' or 'nothing can be done about it.' Often used to express resignation or acceptance of a situation. A contraction where '仕方' means 'method' or 'way,' and 'がない' means 'there is none.'",
            "jlpt_level": "N4",
        },
        {
            "japanese_example":"それで",
            "dictionary_form":"それで",
            "teaching_notes":"Conjunction: 'and with that,' 'therefore,' or 'because of that.' Used to connect sentences or clauses, indicating a cause or reason leading to a result.",
            "jlpt_level": "N5",
        },
        {
            "japanese_example":"いこう",
            "dictionary_form":"行く(いく)",
            "teaching_notes":"Verb: volitional form of the verb '行く' (to go), used to express a decision or suggestion about the future, equivalent to saying 'let's go' in English.",
            "jlpt_level": "N5",
        }
    ],
    "translation": "It can't be helped, let's go with that."
}

class FakeChatClient(AbstractChatClient):
    def __init__(self, response_type: str = "CHAT", tool_args: dict = SAMPLE_FLASH_CARDS):
        self.response_type = response_type
        self.tool_args = tool_args

    @override
    def complete_chat(self,
                      input_messages: list[chat_types.ChatMessage],
                      tools=None,
                      tool_choice="auto") -> chat_types.ChatMessage:
        if self.response_type == "CHAT":
            return chat_types.ChatMessage(
                role="assistant",
                content="Well, hello, stranger...",
                tool_calls=[],
            )
        else:
            return chat_types.ChatMessage(
                role="assistant",
                content=None,
                tool_calls=[chat_types.ToolCall(
                    id="fake_call_001",
                    type="function",
                    function=chat_types.Function(
                        name="fake_function_name",
                        arguments=json.dumps(self.tool_args)
                    )
                )],
            )
