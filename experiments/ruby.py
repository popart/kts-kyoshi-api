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
messages.append({"role": "system", "content": """You are a japanese html generator. If there's kanji, use ruby tags to add furigana to the Japanese text fragment. If not, return the text unmodified."""})

messages.append({"role": "user", "content": "仕方がない" })
messages.append({"role": "assistant", "content": """<ruby>仕方<rt>しかた</rt></ruby>がない""" })
messages.append({"role": "user", "content": "それで" })
messages.append({"role": "assistant", "content": """それで""" })
messages.append({"role": "assistant", "content": """何度""" })

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
