import logging

from clients.chat.abstract_chat_client import AbstractChatClient
from data_types import chat_types


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Prompt:
    """Base class for setting up chat prompt.

    Inputs:
    - role: system commands. should specify that irrelevant responses will end in "..."
        to avoid saving them and their requests to db (see app.chat)
    - tools: openai style function call specifications
    - examples: list of example messages for few-shot priming.
        for tool calls, you don't need to specify the tool call response!
        ChatClient assumes that tool call results are always "SUCCESS"
    """

    def __init__(
        self,
        chat_client: AbstractChatClient,
        role: str,
        tools: list[dict] | None = None,
        examples: list[chat_types.ChatMessage] | None = None,
    ):
        self.chat_client = chat_client
        self.base_messages = []
        self.base_messages.append(chat_types.ChatMessage(role="system", content=role))
        if examples:
            self.base_messages += examples
        self.tools = tools

    def fetch(self, messages: list[chat_types.ChatMessage]) -> chat_types.ChatMessage:
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
