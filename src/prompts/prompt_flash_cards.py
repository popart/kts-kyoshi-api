import json

from data_types import chat_types
from clients.chat.abstract_chat_client import AbstractChatClient
from prompts.prompt import Prompt

role = """You are a Japanese tutor for English speaking students. The student will ask you a question about Japanese or give you some text in Japanese that they are trying to understand. You will generate a lesson from the student's input and save it by calling the create_japanese_lesson() function.

First, fix any spelling or grammar errors in the student's input (that can't be attributed to vernacular speech) and pass that as the `student_input` argument.

Then generate your tutor_response to the student. Your response could be a literal translation from Japanese to English, or it could be an explanation for a specific question from the student. Pass this response as the `tutor_response` argument. If the student input is not related to learning Japanese, then just pass an empty string.

Then create an example_sentence based on the vocab and grammar points from the tutor_response. If the student_input was a complete sentence, just use that as the example_sentence.

Finally generate a list of flash cards for the example_sentence. Each flash card teaches a vocabulary word or grammar point. The card are listed to match the order of words in the example_sentence.

<important>Any individual kanji that you output must be followed by its hiragana pronunciation in parenthesis. Do not output romaji.</important>
"""
tools = [
    {
        "type": "function",
        "function": {
            "name": "create_japanese_lesson",
            "description": "Saves a lesson and a list of japanese_flash_cards. Each japanese_flash_card in the list explains a vocab or grammar teaching point from the example_sentence.",
            "parameters": {
                "type": "object",
                "properties": {
                    "student_input": {
                        "type": "string",
                        "description": "The student's original query or request, corrected for any typos that cannot be attributed to vernacular speech.",
                    },
                    "tutor_response": {
                        "type": "string",
                        "description": "The tutor's response to the student. A literal translation or an answer to a pedagogical question. If the student_input was unrelated to language learning, then returns an empty string.",
                    },
                    "example_sentence": {
                        "type": "string",
                        "description": "A sentence in japanese that exemplifies the main teaching points from the tutor_response. If the student_input was already a Japanese sentence, then the `example_sentence` duplicates the `student_input`. The tutor can make up an example sentence or other fragment of japanese text to help teach the student something they asked about. Each individual kanji is followed by its pronunciation in parenthesis.",
                    },
                    "example_sentence_translation": {
                        "type": "string",
                        "description": "The `example_sentence` translated into English",
                    },
                    "japanese_flash_cards": {
                        "type": "array",
                        "description": "A comprehensive list of flash card objects based on the example_sentence. The example_sentence is completely broken down into teaching points, and each card focuses on a vocab or grammar point.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "japanese_example": {
                                    "type": "string",
                                    "description": "The vocab or grammar point as written and conjugated in the `example_sentence`, without changes. Each individual kanji is followed by its pronunciation in parenthesis.",
                                },
                                "dictionary_form": {
                                    "type": "string",
                                    "description": "For vocab words, the vocab word in its root, dictionary form (i.e. its 辞書形), in its most commonly seen writing variant. Each individual kanji is followed by its pronunciation in parenthesis.",
                                },
                                "teaching_notes": {
                                    "type": "string",
                                    "description": "Complete explanation of grammar in the japanese_example, including conjugation & colloqualisms. For shortened spoken forms, expands the form to its full originating phrase and explains how the elements are combined. For vocab words, provides a translation and explains it. For proper names, explains what the name means and the kanji for it.",
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
                    "example_sentence_translation",
                    "japanese_flash_cards",
                ],
            },
        },
    }
]

examples = []

# Example 1
examples.append(
    chat_types.ChatMessage(
        role="user", content="お前が近所からどう言われてるか、知らない訳じゃなだろ！"
    )
)
tutor_response_1 = """
### Literal Translation

"You know how you are being talked about from the neighborhood, right?"

### Literal Translation Breakdown

- **お前(まえ)が**: "You" (subject marker)
- **近(きん)所(じょ)から**: "from the neighborhood"
- **どう言(い)われてるか**: "how you are being talked about" (embedded question)
  - **どう**: "how"
  - **言(い)われてる**: Passive form of 言う (to say), meaning "being talked about"
  - **か**: Question marker for the embedded question
- **知(し)らない訳(わけ)じゃないだろ**: "it's not that you don't know, right?"
  - **知(し)らない**: "don't know"
  - **訳(わけ)じゃない**: "it's not that" (double negative implying the speaker actually knows)
  - **だろ**: Informal form of でしょう, used to seek confirmation, similar to "right?" or "isn't it?"
"""
examples.append(
    chat_types.ChatMessage(
        role="assistant",
        tool_calls=[
            chat_types.ToolCall(
                id="call_001",
                type="function",
                function=chat_types.Function(
                    name="create_japanese_lesson",
                    arguments=json.dumps(
                        {
                            "student_input": "お前(まえ)が近(きん)所(じょ)からどう言(い)われてるか、知(し)らない訳(わけ)じゃなだろ！",
                            "tutor_response": tutor_response_1,
                            "example_sentence": "お前(まえ)が近(きん)所(じょ)からどう言(い)われてるか、知(し)らない訳(わけ)じゃないだろ！",
                            "example_sentence_translation": "You know how you are being talked about from the neighborhood, right?",
                            "japanese_flash_cards": [
                                {
                                    "japanese_example": "お前(まえ)",
                                    "dictionary_form": "お前(まえ)",
                                    "jlpt_level": "N5",
                                    "teaching_notes": "Pronoun: A casual or rude way to say "
                                    '"you". Often used among friends '
                                    "or in confrontational "
                                    "situations.",
                                },
                                {
                                    "japanese_example": "近(きん)所(じょ)",
                                    "dictionary_form": "近(きん)所(じょ)",
                                    "jlpt_level": "N5",
                                    "teaching_notes": 'Noun: "neighborhood" or "vicinity".',
                                },
                                {
                                    "japanese_example": "言(い)われてる(い)",
                                    "dictionary_form": "言(い)われる",
                                    "jlpt_level": "N4",
                                    "teaching_notes": 'Verb: "to be said". Passive form of 言う (to say).',
                                },
                                {
                                    "japanese_example": "知(し)らない訳(わけ)じゃない",
                                    "dictionary_form": "知(し)る",
                                    "jlpt_level": "N3",
                                    "teaching_notes": "Expression: \"it's not that I "
                                    "don't know.\" A double negative "
                                    "form used to imply that the "
                                    "speaker actually knows "
                                    'something. "訳(わけ)"  means '
                                    '"reason" or "circumstance.',
                                },
                                {
                                    "japanese_example": "だろ",
                                    "dictionary_form": "だろう",
                                    "jlpt_level": "N4",
                                    "teaching_notes": "Auxiliary: A less formal version "
                                    'of "でしょう", used to express '
                                    "probability or expectation, "
                                    'similar to "right?" or "isn\'t '
                                    'it?" in English.',
                                },
                            ],
                        },
                        ensure_ascii=False,
                    ),
                ),
            )
        ],
    )
)

# Example 2
examples.append(
    chat_types.ChatMessage(role="user", content="What's an embedded question?")
)
examples.append(
    chat_types.ChatMessage(
        role="assistant",
        tool_calls=[
            chat_types.ToolCall(
                id="call_002",
                type="function",
                function=chat_types.Function(
                    name="create_japanese_lesson",
                    arguments=json.dumps(
                        {
                            "student_input": "What's an embedded question?",
                            "tutor_response": "An embedded question is a question that is included within "
                            "another sentence. In Japanese, embedded questions often "
                            "use the particle か to indicate the question within "
                            "the sentence. For example, in the sentence \"I don't know "
                            'where he is," the embedded question is "where he is.',
                            "example_sentence": "彼(かれ)がどこにいるか知(し)らない。",
                            "example_sentence_translation": "I don't know where he is.",
                            "japanese_flash_cards": [
                                {
                                    "japanese_example": "彼(かれ)",
                                    "dictionary_form": "彼(かれ)",
                                    "teaching_notes": 'Pronoun: "he" or "him".',
                                    "jlpt_level": "N5",
                                },
                                {
                                    "japanese_example": "どこ",
                                    "dictionary_form": "どこ",
                                    "teaching_notes": 'Interrogative: "where".',
                                    "jlpt_level": "N5",
                                },
                                {
                                    "japanese_example": "に",
                                    "dictionary_form": "に",
                                    "teaching_notes": "Particle: Indicates direction or "
                                    "location.",
                                    "jlpt_level": "N5",
                                },
                                {
                                    "japanese_example": "いる",
                                    "dictionary_form": "いる",
                                    "teaching_notes": 'Verb: "to be" or "to '
                                    'exist" (for animate objects).',
                                    "jlpt_level": "N5",
                                },
                                {
                                    "japanese_example": "か",
                                    "dictionary_form": "か",
                                    "teaching_notes": "Particle: Used to indicate a "
                                    "question within a sentence, "
                                    "marking the embedded question.",
                                    "jlpt_level": "N5",
                                },
                                {
                                    "japanese_example": "知(し)らない",
                                    "dictionary_form": "知(し)る",
                                    "teaching_notes": 'Verb: "to not know." Negative form of "to know".',
                                    "jlpt_level": "N5",
                                },
                            ],
                        },
                        ensure_ascii=False,
                    ),
                ),
            )
        ],
    )
)
# Example 3
examples.append(
    chat_types.ChatMessage(role="user", content="彼が遅れたのは、電車が遅れたからだ")
)
tutor_response_3 = """
### Literal Translation

"(The fact) that he was late is because the train was delayed."

### Literal Translation Breakdown

- **彼(かれ)が遅(おそ)れたのは**: "(The fact) that he was late" (nominalized and marked as the topic)
  - **彼(かれ)が**: "He" (subject marker)
  - **遅(おそ)れた**: "was late"
  - **の**: Nominalizer, turning the verb phrase "was late" into a noun phrase
  - **は**: Topic marker, indicating that the nominalized phrase is the topic of the sentence
- **電(でん)車(しゃ)が遅(おく)れたからだ**: "is because the train was delayed"
  - **電(でん)車(しゃ)が**: "train" (subject marker)
  - **遅(おく)れた**: "was delayed"
  - **から**: "because"
  - **だ**: Informal copula, meaning "is"
"""
examples.append(
    chat_types.ChatMessage(
        role="assistant",
        tool_calls=[
            chat_types.ToolCall(
                id="call_003",
                type="function",
                function=chat_types.Function(
                    name="create_japanese_lesson",
                    arguments=json.dumps(
                        {
                            "student_input": "彼(かれ)が遅(おそ)れたのは、電(でん)車(しゃ)が遅(おく)れたからだ。",
                            "tutor_response": tutor_response_3,
                            "example_sentence": "彼(かれ)が遅(おそ)れたのは、電(でん)車(しゃ)が遅(おく)れたからだ。",
                            "example_sentence_translation": "The reason he was late is because the train was delayed.",
                            "japanese_flash_cards": [
                                {
                                    "japanese_example": "彼(かれ)",
                                    "dictionary_form": "彼(かれ)",
                                    "jlpt_level": "N5",
                                    "teaching_notes": 'Pronoun: "he" or "him".',
                                },
                                {
                                    "japanese_example": "遅(おそ)れた",
                                    "dictionary_form": "遅(おそ)れる",
                                    "jlpt_level": "N5",
                                    "teaching_notes": 'Verb (ichidan): "was late", past tense of "to be late".',
                                },
                                {
                                    "japanese_example": "電(でん)車(しゃ)",
                                    "dictionary_form": "電(でん)車(しゃ)",
                                    "jlpt_level": "N5",
                                    "teaching_notes": 'Noun: "train".',
                                },
                                {
                                    "japanese_example": "遅(おく)れた",
                                    "dictionary_form": "遅(おく)れる",
                                    "jlpt_level": "N5",
                                    "teaching_notes": 'Verb (ichidan): "was delayed", past tense of "to be delayed"',
                                },
                                {
                                    "japanese_example": "…からだ",
                                    "dictionary_form": "から,だ",
                                    "jlpt_level": "N5",
                                    "teaching_notes": 'Expression: "because". Combines から (because) with だ (informal copula).',
                                },
                            ],
                        }
                    ),
                ),
            )
        ],
    )
)


def get_prompt_flash_cards(chat_client: AbstractChatClient):
    return Prompt(
        chat_client=chat_client, role=role, tools=tools, examples=examples[0:2]
    )
