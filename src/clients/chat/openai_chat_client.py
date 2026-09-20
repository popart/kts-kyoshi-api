import logging
import os
from typing import TypeVar, override
import uuid

from openai import OpenAI
from pydantic import BaseModel

from clients.chat.abstract_chat_client import AbstractChatClient
from data_types import chat_types


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

ResponseT = TypeVar("ResponseT", bound=BaseModel)

# qwencloud (Alibaba DashScope, OpenAI-compatible API)
DEFAULT_BASE_URL = "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
DEFAULT_MODEL = "qwen3.8-flash"


class OpenAIChatClient(AbstractChatClient):
    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        api_key: str | None = None,
        enable_thinking: bool = False,
    ):
        self.model = model or os.getenv("LLM_MODEL", DEFAULT_MODEL)
        # qwen runs in thinking mode by default, which makes structured output
        # very slow. The tutor prompt doesn't need reasoning, so it's off.
        self.enable_thinking = enable_thinking
        self.client = OpenAI(
            base_url=base_url or os.getenv("LLM_BASE_URL", DEFAULT_BASE_URL),
            api_key=api_key or os.getenv("QWEN_API_KEY"),
        )

    @override
    def complete_chat(
        self,
        input_messages: list[chat_types.ChatMessage],
        response_model: type[ResponseT],
    ) -> ResponseT | None:
        messages = [m.to_llm_message() for m in input_messages]

        response = self.client.chat.completions.parse(
            model=self.model,
            messages=messages,
            # `response_format` is generated from the pydantic model and sent as
            # a strict JSON schema; the SDK parses the reply back into it.
            response_format=response_model,
            temperature=0.1,
            user=str(uuid.uuid4()),
            # NOTE: no max_tokens. Structured output can be truncated by a token
            # cap, which would produce invalid JSON.
            extra_body={"enable_thinking": self.enable_thinking},
        )
        self._log_tokens(response)

        choice = response.choices[0]
        if choice.finish_reason != "stop" or choice.message.parsed is None:
            logger.error(
                "No structured output (finish_reason=%s, refusal=%s)",
                choice.finish_reason,
                choice.message.refusal,
            )
            return None
        return choice.message.parsed

    @classmethod
    def _log_tokens(cls, response):
        usage = response.usage
        if usage is None:
            return
        logger.info(
            "Token usage: prompt=%d, completion=%d, total=%d",
            usage.prompt_tokens,
            usage.completion_tokens,
            usage.total_tokens,
        )