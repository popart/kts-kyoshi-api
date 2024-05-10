from dataclasses import dataclass

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
    tool_call_id: str | None = None
    tool_calls: list[ToolCall] | None = None
    content: str | None = None
