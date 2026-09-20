from abc import ABC, abstractmethod
from typing import TypeVar

from pydantic import BaseModel

from data_types import chat_types

ResponseT = TypeVar("ResponseT", bound=BaseModel)


class AbstractChatClient(ABC):
    @abstractmethod
    def complete_chat(
        self,
        input_messages: list[chat_types.ChatMessage],
        response_model: type[ResponseT],
    ) -> ResponseT | None:
        """Return the model's output parsed into `response_model`."""
        raise NotImplementedError