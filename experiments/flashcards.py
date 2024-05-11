"""Try to pull out grammar, explanations, and pronuncations"""

import os
from openai import OpenAI

import pprint
import uuid
import json


client = OpenAI()
MODEL = "gpt-4-turbo"  # gpt-4 turbo

tools = [
    {
        "type": "function",
        "function": {
            "name": "create_japanese_flashcards",
            "description": "Input: a list of japanese_flash_cards. Each item in the list explains a vocab or grammar teaching point from the input sentence.",
            "parameters": {
                "type": "object",
                "properties": {
                    "japanese_flash_cards": {
                        "type": "array",
                        "description": "A list of flash card objects.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "japanese_example": {
                                    "type": "string",
                                    "description": "the vocab or grammar point as written and conjugated in the input text, without changes",
                                },
                                "dictionary_form": {
                                    "type": "string",
                                    "description": "For vocab words, the vocab word in its dictionary, root form, in its most commonly seen writing variant.",
                                },
                                "teaching_notes": {
                                    "type": "string",
                                    "description": "Explanation of grammar, including conjugation & colloqualisms. For shortened spoken forms, expands the form to its full originating phrase",
                                },
                            },
                        },
                    },
                },
                "required": ["japanese_vocab_words"],
            },
        },
    },
]


messages = []

messages.append(
    {
        "role": "system",
        "content": """
You are a Japanese grammar explainer for English speaking students. You have two jobs:
1) When User gives you a sentence in Japanese, convert it into a JSON list of flash cards. Each flash card will the `japanese_example`, i.e. the word as conjugated in the sentence, the `dictionary_form`, i.e. the word as you would find it in a japanese dictionary, and `teaching_notes`, i.e. explanations of grammar points and other pedantically useful knowledge. Call the create_japanese_flashcards() function and pass in the JSON list of flashcards as an argument. Make sure you close all parenthesis and brackets in your arguments.
2) If User asks you a question in English, answer their question if it relates to Japanese. If the question is irrelevant just reply with an ellipsis (...)""",
    }
)

messages.append({"role": "user", "content": "しょうがない、それでいこう"})
messages.append(
    {
        "role": "assistant",
        "tool_calls": [
            {
                "id": "call_001",
                "type": "function",
                "function": {
                    "name": "save_japanese_vocab_words",
                    "arguments": json.dumps(
                        [
                            {
                                "japanese_example": "しょうがない",
                                "dictionary_form": "仕方がない",
                                "teaching_notes": "This phrase means 'it can't be helped' or 'nothing can be done about it.' It's often used to express resignation or acceptance of a situation. The phrase is a contraction where '仕方' means 'method' or 'way,' and 'がない' means 'there is none.'",
                            },
                            {
                                "japanese_example": "それで",
                                "dictionary_form": "それで",
                                "teaching_notes": "This conjunction means 'and with that,' 'therefore,' or 'because of that.' It is used to connect sentences or clauses, indicating a cause or reason leading to a result.",
                            },
                            {
                                "japanese_example": "いこう",
                                "dictionary_form": "行く",
                                "teaching_notes": "This is the volitional form of the verb '行く' (to go), used to express a decision or suggestion about the future, equivalent to saying 'let's go' in English.",
                            },
                        ]
                    ),
                },
            }
        ],
    }
)
messages.append(
    {
        "role": "tool",
        "tool_call_id": "call_001",
        "content": "SUCCESS",
    }
)

# tool_choice test: this works, answers the question
# messages.append({"role": "user", "content": "What does 'volitional form' mean?" })
# messages.append({"role": "assistant", "content": """The "volitional form" of a Japanese verb is used to express a speaker's will, intention, or determination to do something. It can also be used to make informal suggestions or invitations, similar to saying "let's" in English. This form is created by modifying the verb stem according to specific conjugation rules depending on the verb group. For example, for '行く' (iku, to go), the volitional form is '行こう' (ikou, let's go).""" })

# tool_choice test: this works, goes back to function call
# messages.append({"role": "user", "content": "携帯、何度かけても連絡つかなくて" })
messages.append(
    {
        "role": "user",
        "content": "お前が近所からどう言われてるか、知らない訳じゃなだろ！",
    }
)

# irrelevance test: this works, responds "..."
# messages.append({"role": "user", "content": "What are you wearing, hot stuff?" })

response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    frequency_penalty=0.1,
    presence_penalty=0.1,
    temperature=0.1,
    user=str(uuid.uuid4()),
    tools=tools,
    tool_choice="auto",
)
pprint.pprint(response)

if response.choices[0].message.tool_calls:
    output = response.choices[0].message.tool_calls[0].function.arguments
    pprint.pprint(json.loads(output))
