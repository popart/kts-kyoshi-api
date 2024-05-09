import json
import logging
import sys
import uuid

from openai import OpenAI


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

client = OpenAI()
MODEL = "gpt-4-1106-preview" # gpt-4 turbo
MAX_TOKENS = 1000

class Prompt:
    def __init__(self, role: str, tools: list[dict]=None, examples: list[dict]=None):
        self.base_messages = []
        self.base_messages.append({"role": "system", "content": role })
        if examples:
            self.base_messages += examples
        self.tools=tools

    def fetch(self, messages: list[dict]) -> list[dict]:
        input_messages = self.base_messages.copy() + messages

        logger.info(f"openai post: {input_messages}")

        response = client.chat.completions.create(
            model=MODEL,
            messages=input_messages,
            frequency_penalty=0.1,
            presence_penalty=0.1,
            temperature=0.1,
            user=str(uuid.uuid4()),
            tools=self.tools,
            tool_choice="auto",
            max_tokens=MAX_TOKENS,
        )
        choice = response.choices[0]

        output_messages = []

        if choice.finish_reason == "stop":
            output_messages.append({
                "role": "assistant",
                "content": choice.message.content,
            })
        elif choice.finish_reason == "tool_calls":
            output = choice.message.tool_calls[0].function.arguments
            try:
                # verify that output is valid json
                tool_response = json.loads(output)
                output_messages.append({
                    "role": "assistant",
                    "tool_calls": choice.message.tool_calls,
                })
                output_messages.append({
                    "role": "tool",
                    "tool_call_id": choice.message.tool_calls[0].id,
                    "content": "SUCCESS",
                })
            except json.decoder.JSONDecodeError:
                logger.error("Couldn't decode JSON: %s", output)
        else:
            logger.error("Response couldn't be read: %s", str(choice))

        return output_messages
