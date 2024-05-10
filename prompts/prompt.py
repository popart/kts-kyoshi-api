import json
import logging
import sys

from clients.chat.abstract_chat_client import AbstractChatClient
from clients.chat import chat_types


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Prompt:
    def __init__(self,
                 chat_client: AbstractChatClient,
                 role: str,
                 tools: list[dict]=None,
                 examples: list[chat_types.ChatMessage]=None):
        self.chat_client = chat_client
        self.base_messages = []
        self.base_messages.append(chat_types.ChatMessage(role="system", content=role))
        if examples:
            self.base_messages += examples
        self.tools=tools

    def fetch(self, messages: list[dict]) -> chat_types.ChatMessage:
        """
        Returns:
          {} a chat message dict, empty if we didn't get a good response
        """
        input_messages = self.base_messages.copy() + messages

        logger.info(f"completing chat: {input_messages}")

        chat_message: chat_types.ChatMessage = self.chat_client.complete_chat(
            input_messages=input_messages,
            tools=self.tools,
            tool_choice="auto",
        )

        return chat_message
