from abc import ABC, abstractmethod

from data_types import chat_types


class AbstractChatClient(ABC):
    @abstractmethod
    def complete_chat(
        self,
        input_messages: list[chat_types.ChatMessage],
        tools=None,
        tool_choice="auto",
    ) -> chat_types.ChatMessage:
        raise NotImplementedError
