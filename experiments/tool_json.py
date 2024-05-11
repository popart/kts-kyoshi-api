"""Try to pull out grammar, explanations, and pronuncations"""

import os
from openai import OpenAI
from openai.types.chat.chat_completion_message_tool_call import (
    Function,
    ChatCompletionMessageToolCall,
)

from pprint import pprint
import uuid
import json


client = OpenAI()
MODEL = "gpt-4-turbo"  # gpt-4 turbo


def tool_call_to_dict(tool_call):
    return {
        "id": tool_call.id,
        "type": tool_call.type,
        "function": {
            "name": tool_call.function.name,
            "arguments": tool_call.function.arguments,
        },
    }


def gen_tool_call_response(tool_call):
    return {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "content": "SUCCESS",
    }


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

# response = client.chat.completions.create(
#    model=MODEL,
#    messages=messages,
#    frequency_penalty=0.1,
#    presence_penalty=0.1,
#    temperature=0.1,
#    user=str(uuid.uuid4()),
#    tools=tools,
#    tool_choice="auto",
# )
# tool_calls = response.choices[0].message.tool_calls:

tool_calls = [
    ChatCompletionMessageToolCall(
        id="call_3lS7thGGCTGK6DvCt3ShWAsP",
        function=Function(
            arguments='{"japanese_flash_cards":[{"japanese_example":"しょうがない","dictionary_form":"仕方がない","teaching_notes":"A common expression meaning \'it can\'t be helped\' or \'nothing can be done about it.\' The phrase is often used to express resignation or acceptance of a situation."},{"japanese_example":"それでいこう","dictionary_form":"それで行こう","teaching_notes":"This phrase means \'Let\'s go with that,\' or \'Let\'s do it this way.\' It is used to agree on a suggestion or a course of action. The verb \'行く\' (いく) is in volitional form, indicating a suggestion or decision."}]}',
            name="create_japanese_flashcards",
        ),
        type="function",
    )
]

tc_dict = tool_call_to_dict(tool_calls[0])
pprint(tc_dict)

tool_call_message = {"role": "assistant", "tool_calls": [tc_dict]}
tool_result_message = {
    "role": "tool",
    "tool_call_id": tc_dict["id"],
    "content": "SUCCESS",
}
