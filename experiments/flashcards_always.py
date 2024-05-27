"""Try to pull out grammar, explanations, and pronuncations"""

from openai import OpenAI

import pprint
import uuid
import json


client = OpenAI()
MODEL = "gpt-4o"  # gpt-4 turbo

role = """You are Kyoshi, a Japanese tutor for English speaking students. The student will ask you a question about Japanese or give you a sentence in Japanese that they are trying to translate.

You will generate a short lesson from the student's input and save it by calling the create_japanese_lesson() function.

First fix any spelling or grammar errors in the student's input (that can't be attributed to vernacular speech) and pass that as the `student_input` argument.

Then generate your response to the student. Your response could be a translation from Japanese to English, or it could be an explanation for a specific question from the student. Pass this response as the `tutor_response` argument. If the student input is not related to learning Japanese, then just pass an empty string.

Finally generate a sequence of flash cards that would be helpful for the student to review later to go over your translation or explanation. Each flash card is a bite-sized unit to learn, such as a vocabulary word or grammar point. If the student gave you a Japanese sentence to translate, the cards should match the order of words in the sentence.

<important>Any kanji or 熟語 that you output must be followed by their hiragana pronunciation in parenthesis.</important>
"""

tools = [
    {
        "type": "function",
        "function": {
            "name": "create_japanese_lesson",
            "description": "Saves a lesson point and a list of japanese_flash_cards. Each item in the list explains a vocab or grammar teaching point from the student_point and tutor_response.",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_input": {
                        "type": "string",
                        "description": "The student's original query or request. Typos that cannot be attributed to vernacular speech are corrected.",
                    },
                    "tutor_response": {
                        "type": "string",
                        "description": "The tutor's response to the student. A translation or an answer to a pedagogical question. If the student_input was unrelated to language learning, then returns an empty string.",
                    },
                    "example_sentence": {
                        "type": "string",
                        "description": "A sentence in japanese that is used to generate the lesson of flash cards. If the student_input was already a Japanese sentence, then the `example_sentence` duplicates the `student_input`. Otherwise, the tutor makes up an example sentence to help teach the student something they asked about.",
                    },
                    "japanese_flash_cards": {
                        "type": "array",
                        "description": "A comprehensive list of flash card objects. The tutor_response is completely broken down into bite-size teaching points. Each card focuses on a japanese_text, and teaches the student how to understand it.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "japanese_example": {
                                    "type": "string",
                                    "description": "The vocab or grammar point as written and conjugated in the example_sentence, without changes. Each kanji or 熟語 is followed by its pronunciation in parenthesis.",
                                },
                                "dictionary_form": {
                                    "type": "string",
                                    "description": "For vocab words, the vocab word in its root, dictionary form (i.e. its 辞書形), in its most commonly seen writing variant. Each kanji or 熟語 is followed by its pronunciation in parenthesis.",
                                },
                                "teaching_notes": {
                                    "type": "string",
                                    "description": "Explanation of grammar, including conjugation & colloqualisms. For shortened spoken forms, expands the form to its full originating phrase",
                                },
                                "jlpt_level": {
                                    "type": "string",
                                    "description": "Approximate JLPT level for this teaching point.",
                                    "enum": ["N5", "N4", "N3", "N2", "N1"],
                                },
                            },
                        },
                    },
                },
                "required": [
                    "student_input",
                    "tutor_response",
                    "example_sentence",
                    "japanese_flash_cards",
                ],
            },
        },
    }
]

messages = []
messages.append(
    {
        "role": "system",
        "content": role,
    }
)
# example 1
messages.append(
    {
        "role": "user",
        "content": "お前が近所からどう言われてるか、知らない訳じゃなだろ！",
    }
)

tutor_response_1 = """
### Translation

"You know what the neighborhood says about you, right?"

### Detailed Breakdown

- **お前(まえ)が**: "You" (subject marker)
- **近所(きんじょ)から**: "from the neighborhood"
- **どう言(い)われてるか**: "how you are being talked about" (embedded question)
  - **どう**: "how"
  - **言(い)われてる**: Passive form of 言う (to say), meaning "being talked about"
  - **か**: Question marker for the embedded question
- **知(し)らない訳(わけ)じゃないだろ**: "it's not that I don't know, right?"
  - **知(し)らない**: "don't know"
  - **訳(わけ)じゃない**: "it's not that" (double negative implying the speaker actually knows)
  - **だろ**: Informal form of でしょう, used to seek confirmation, similar to "right?" or "isn't it?"
"""
messages.append(
    dict(
        role="assistant",
        tool_calls=[
            dict(
                id="call_001",
                type="function",
                function=dict(
                    name="create_japanese_lesson",
                    arguments=json.dumps(
                        {
                            "student_input": "お前(まえ)が近所(きんじょ)からどう言(い)われてるか、知(し)らない訳(わけ)じゃないだろ！",
                            "tutor_response": tutor_response_1,
                            "example_sentence": "お前(まえ)が近所(きんじょ)からどう言(い)われてるか、知(し)らない訳(わけ)じゃないだろ！",
                            "japanese_flash_cards": [
                                {
                                    "japanese_example": "お前(まえ)",
                                    "dictionary_form": "お前(まえ)",
                                    "jlpt_level": "N5",
                                    "teaching_notes": "Pronoun: A casual or rude way to say "
                                    "'you'. Often used among friends "
                                    "or in confrontational "
                                    "situations.",
                                },
                                {
                                    "japanese_example": "近所(きんじょ)",
                                    "dictionary_form": "近所(きんじょ)",
                                    "jlpt_level": "N5",
                                    "teaching_notes": "Noun: Means 'neighborhood' or 'vicinity'.",
                                },
                                {
                                    "japanese_example": "言(い)われてる(い)",
                                    "dictionary_form": "言(い)われる",
                                    "jlpt_level": "N4",
                                    "teaching_notes": "Verb: Passive form of 言う (to say). "
                                    "Means 'to be said'.",
                                },
                                {
                                    "japanese_example": "知(し)らない訳(わけ)じゃない",
                                    "dictionary_form": "知(し)る",
                                    "jlpt_level": "N3",
                                    "teaching_notes": "Expression: 'it's not that I "
                                    "don't know.' A double negative "
                                    "form used to imply that the "
                                    "speaker actually knows "
                                    "something. '訳' (わけ) means "
                                    "'reason' or 'circumstance.'",
                                },
                                {
                                    "japanese_example": "だろ",
                                    "dictionary_form": "だろう",
                                    "jlpt_level": "N4",
                                    "teaching_notes": "Auxiliary: A less formal version "
                                    "of 'でしょう,' used to express "
                                    "probability or expectation, "
                                    "similar to 'right?' or 'isn't "
                                    "it?' in English.",
                                },
                            ],
                        }
                    ),
                ),
            )
        ],
    )
)
# required tool call response
messages.append(
    {
        "role": "tool",
        "tool_call_id": "call_001",
        "content": "SUCCESS",
    }
)
messages.append(
    {
        "role": "user",
        "content": "What's an embedded question?",
    }
)
messages.append(
    dict(
        role="assistant",
        tool_calls=[
            dict(
                id="call_002",
                type="function",
                function=dict(
                    name="create_japanese_lesson",
                    arguments=json.dumps(
                        {
                            "student_input": "What's an embedded question?",
                            "tutor_response": "An embedded question is a question that is included within "
                            "another sentence. In Japanese, embedded questions often "
                            "use the particle か to indicate the question within "
                            "the sentence. For example, in the sentence 'I don't know "
                            "where he is,' the embedded question is 'where he is.'",
                            "example_sentence": "彼(かれ)がどこにいるか知(し)らない。",
                            "japanese_flash_cards": [
                                {
                                    "dictionary_form": "彼(かれ)",
                                    "japanese_example": "彼(かれ)",
                                    "jlpt_level": "N5",
                                    "teaching_notes": "Pronoun: Means 'he' or 'him.'",
                                },
                                {
                                    "dictionary_form": "どこ",
                                    "japanese_example": "どこ",
                                    "jlpt_level": "N5",
                                    "teaching_notes": "Interrogative: Means 'where.'",
                                },
                                {
                                    "dictionary_form": "に",
                                    "japanese_example": "に",
                                    "jlpt_level": "N5",
                                    "teaching_notes": "Particle: Indicates direction or "
                                    "location.",
                                },
                                {
                                    "dictionary_form": "いる",
                                    "japanese_example": "いる",
                                    "jlpt_level": "N5",
                                    "teaching_notes": "Verb: Means 'to be' or 'to "
                                    "exist' (for animate objects).",
                                },
                                {
                                    "dictionary_form": "か",
                                    "japanese_example": "か",
                                    "jlpt_level": "N5",
                                    "teaching_notes": "Particle: Used to indicate a "
                                    "question within a sentence, "
                                    "marking the embedded question.",
                                },
                                {
                                    "dictionary_form": "知(し)る",
                                    "japanese_example": "知(し)らない",
                                    "jlpt_level": "N5",
                                    "teaching_notes": "Verb: Means 'to know.' In its "
                                    "negative form, it means 'to not "
                                    "know.'",
                                },
                            ],
                        }
                    ),
                ),
            )
        ],
    )
)
messages.append(
    {
        "role": "tool",
        "tool_call_id": "call_002",
        "content": "SUCCESS",
    }
)
messages.append(
    {
        "role": "user",
        "content": "What's an embedded question?",
    }
)

response = client.chat.completions.create(
    model=MODEL,
    messages=messages,
    frequency_penalty=0.0,
    presence_penalty=0.0,
    temperature=0.0,
    user=str(uuid.uuid4()),
    tools=tools,
    tool_choice={"type": "function", "function": {"name": "create_japanese_lesson"}},
)
pprint.pprint(response)

if response.choices[0].message.tool_calls:
    output = response.choices[0].message.tool_calls[0].function.arguments
    pprint.pprint(json.loads(output))
