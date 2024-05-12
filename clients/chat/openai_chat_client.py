from dataclasses import asdict
import json
import logging
from typing import override
import uuid

from openai import OpenAI
from openai.types.chat.chat_completion_message_tool_call import (
    ChatCompletionMessageToolCall,
)
from openai.types.chat.chat_completion import Choice

from data_types import chat_types
from clients.chat.abstract_chat_client import AbstractChatClient


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class OpenAIChatClient(AbstractChatClient):
    # MODEL = "gpt-4-1106-preview"
    MODEL = "gpt-4-turbo"
    MAX_TOKENS = 1000

    def __init__(self):
        self.client = OpenAI()

    @override
    def complete_chat(
        self,
        input_messages: list[chat_types.ChatMessage],
        tools=None,
        tool_choice="auto",
    ) -> chat_types.ChatMessage:
        messages: list[dict] = []
        for m in input_messages:
            messages.append(asdict(m))
            if m.tool_calls:
                messages.extend(
                    [self._gen_tool_call_response(tc) for tc in m.tool_calls]
                )

        response = self.client.chat.completions.create(
            model=self.MODEL,
            messages=messages,
            frequency_penalty=0.1,
            presence_penalty=0.1,
            temperature=0.1,
            user=str(uuid.uuid4()),
            tools=tools,
            tool_choice=tool_choice,
            max_tokens=self.MAX_TOKENS,
        )
        choice = response.choices[0]

        if choice.finish_reason in ["stop", "tool_calls"]:
            return self._parse_choice(choice)
        else:
            logger.error("Finish reason no good: %s", choice)
            return chat_types.ChatMessage(role="assistant")

    @classmethod
    def _parse_choice(cls, choice: Choice) -> chat_types.ChatMessage:
        try:
            if choice.message.tool_calls:
                tool_calls = [
                    cls._parse_tool_call(tc) for tc in choice.message.tool_calls
                ]
            else:
                tool_calls = None
            return chat_types.ChatMessage(
                role=choice.message.role,
                content=choice.message.content,
                tool_calls=tool_calls,
            )
        except json.decoder.JSONDecodeError:
            logger.error("Couldn't decode JSON: %s", choice)
            return chat_types.ChatMessage(role="assistant")

    @classmethod
    def _parse_tool_call(cls, tool_call: ChatCompletionMessageToolCall):
        # verify that fn_args are valid json
        json.loads(tool_call.function.arguments)

        return chat_types.ToolCall(
            id=tool_call.id,
            type=tool_call.type,
            function=chat_types.Function(
                name=tool_call.function.name,
                arguments=tool_call.function.arguments,
            ),
        )

    @classmethod
    def _gen_tool_call_response(cls, tool_call: chat_types.ToolCall) -> dict:
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": "SUCCESS",
        }
