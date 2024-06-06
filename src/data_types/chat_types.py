"""Types for OpenAI interface"""

from dataclasses import dataclass
import datetime
import uuid


@dataclass
class Function:
    name: str
    arguments: str  # json formatted string


@dataclass
class ToolCall:
    id: str
    type: str
    function: Function


@dataclass
class ChatMessage:
    role: str
    tool_calls: list[ToolCall] | None = None
    content: str | None = None


@dataclass
class Chat:
    user_id: uuid.UUID
    chat_id: uuid.UUID
    chat_name: str
    created_at: datetime.datetime


def dict_to_chat_message(data: dict) -> ChatMessage:
    return ChatMessage(
        role=data["role"],
        tool_calls=(
            [
                ToolCall(
                    id=tc["id"],
                    type=tc["type"],
                    function=Function(
                        name=tc["function"]["name"],
                        arguments=tc["function"]["arguments"],
                    ),
                )
                for tc in data["tool_calls"]
            ]
            if data.get("tool_calls")
            else None
        ),
        content=data.get("content"),
    )
