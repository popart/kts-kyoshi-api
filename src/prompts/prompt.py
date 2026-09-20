import logging
from typing import TypeVar

from pydantic import BaseModel

from clients.chat.abstract_chat_client import AbstractChatClient
from data_types import chat_types


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ResponseT = TypeVar("ResponseT", bound=BaseModel)


class Prompt:
    """Base class for setting up a chat prompt.

    Inputs:
    - role: system commands. should specify that irrelevant responses will end in "..."
        to avoid saving them and their requests to db (see app.chat)
    - response_model: pydantic model the model must return (structured output)
    - examples: list of example messages for few-shot priming. Assistant
        examples carry their structured output as JSON in `content`.
    """

    def __init__(
        self,
        chat_client: AbstractChatClient,
        role: str,
        response_model: type[ResponseT],
        examples: list[chat_types.ChatMessage] | None = None,
    ):
        self.chat_client = chat_client
        self.response_model = response_model
        self.base_messages = []
        self.base_messages.append(chat_types.ChatMessage(role="system", content=role))
        if examples:
            self.base_messages += examples

    def fetch(self, messages: list[chat_types.ChatMessage]) -> ResponseT | None:
        """
        Returns:
          the model's output parsed into `response_model`, or None if the model
          didn't return a valid response.
        """
        input_messages = self.base_messages.copy() + messages

        return self.chat_client.complete_chat(
            input_messages=input_messages,
            response_model=self.response_model,
        )