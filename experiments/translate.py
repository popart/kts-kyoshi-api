"""Add furigana to text"""

import os
from openai import OpenAI

import pprint
import uuid
import json

client = OpenAI()
MODEL = "gpt-4-turbo"
#MODEL = "gpt-3.5-turbo" # doesn't work

tools = None
tool_choice = None
messages = []
messages.append({"role": "system", "content": """You are a japanese translation function. Return the simplest translation that captures the nuance of the sentence."""})

messages.append({"role": "user", "content": "お前が近所からどう言われてるか、知らない訳じゃなだろ！" })

response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    frequency_penalty=0.1,
    presence_penalty=0.1,
    temperature=0.1,
    user=str(uuid.uuid4()),
    tools=tools,
    tool_choice=tool_choice,
)
pprint.pprint(response)
