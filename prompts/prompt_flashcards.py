import json

from data_types import chat_types
from clients.chat.abstract_chat_client import AbstractChatClient
from prompts.prompt import Prompt


role = """You are a Japanese grammar explainer for English speaking students. You have two jobs:
1a) When User gives you a sentence in Japanese, convert it into a JSON list of flash cards. Each flash card will the `japanese_example`, i.e. the word as conjugated in the sentence, the `dictionary_form`, i.e. the word as you would find it in a japanese dictionary, and `teaching_notes`, i.e. explanations of grammar points and other pedantically useful knowledge. Call the create_japanese_flashcards() function and pass in the JSON list of flashcards as an argument. Make sure you close all parenthesis and brackets in your arguments.
1b) After creating the flash cards, add a translation for the overall meaning of the sentence.
2) If User asks you a question in English, answer their question if it relates to Japanese. If the question is irrelevant just reply with an ellipsis (...)"""

tools = [
    {
        "type": "function",
        "function": {
            "name": "create_japanese_flashcards",
            "description": "Saves a list of japanese_flash_cards. Each item in the list explains a vocab or grammar teaching point from the input sentence.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_text": {
                        "type": "string",
                        "description": "the original input, with typos corrected",
                    },
                    "japanese_flash_cards": {
                        "type": "array",
                        "description": "A list of flash card objects.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "japanese_example": {
                                    "type": "string",
                                    "description": "the vocab or grammar point as written and conjugated in the input text, without changes. pronunciation is appended in parenthesis.",
                                },
                                "dictionary_form": {
                                    "type": "string",
                                    "description": "For vocab words, the vocab word in its dictionary, root form, in its most commonly seen writing variant. pronunciation is appended in parenthesis.",
                                },
                                "teaching_notes": {
                                    "type": "string",
                                    "description": "Explanation of grammar, including conjugation & colloqualisms. For shortened spoken forms, expands the form to its full originating phrase",
                                },
                                "jlpt_level": {
                                    "type": "string",
                                    "description": "JLPT level",
                                    "enum": ["N5", "N4", "N3", "N2", "N1"],
                                },
                            },
                        },
                    },
                    "translated_text": {
                        "type": "string",
                        "description": "the simplest translation that still captures the nuance of the sentence",
                    },
                },
                "required": ["japanese_vocab_words", "translated_text"],
            },
        },
    },
]
examples = []

# Example 1:
examples.append(
    chat_types.ChatMessage(role="user", content="しょうがない、それでいこう")
)
examples.append(
    chat_types.ChatMessage(
        role="assistant",
        tool_calls=[
            chat_types.ToolCall(
                id="call_001",
                type="function",
                function=chat_types.Function(
                    name="save_japanese_vocab_words",
                    arguments=json.dumps(
                        {
                            "input_text": "しょうがない、それでいこう",
                            "japanese_flash_cards": [
                                {
                                    "japanese_example": "しょうがない",
                                    "dictionary_form": "仕方がない(しかたがない)",
                                    "teaching_notes": "Expression: 'It can't be helped' or 'nothing can be done about it.' Often used to express resignation or acceptance of a situation. A contraction where '仕方' means 'method' or 'way,' and 'がない' means 'there is none.'",
                                    "jlpt_level": "N4",
                                },
                                {
                                    "japanese_example": "それで",
                                    "dictionary_form": "それで",
                                    "teaching_notes": "Conjunction: 'and with that,' 'therefore,' or 'because of that.' Used to connect sentences or clauses, indicating a cause or reason leading to a result.",
                                    "jlpt_level": "N5",
                                },
                                {
                                    "japanese_example": "いこう",
                                    "dictionary_form": "行く(いく)",
                                    "teaching_notes": "Verb: volitional form of the verb '行く' (to go), used to express a decision or suggestion about the future, equivalent to saying 'let's go' in English.",
                                    "jlpt_level": "N5",
                                },
                            ],
                            "translated_text": "It can't be helped, let's go with that.",
                        },
                        ensure_ascii=False,
                    ),
                ),
            )
        ],
    )
)

# Example 2:
examples.append(
    chat_types.ChatMessage(
        role="user", content="お前が近所からどう言われてるか、知らない訳じゃなだろ！"
    )
)
examples.append(
    chat_types.ChatMessage(
        role="assistant",
        tool_calls=[
            chat_types.ToolCall(
                id="call_001",
                type="function",
                function=chat_types.Function(
                    name="save_japanese_vocab_words",
                    arguments=json.dumps(
                        {
                            "input_text": "お前が近所からどう言われてるか、知らない訳じゃないだろ！",
                            "japanese_flash_cards": [
                                {
                                    "dictionary_form": "お前(おまえ)",
                                    "japanese_example": "お前(おまえ)",
                                    "jlpt_level": "N5",
                                    "teaching_notes": "Pronoun: 'you.' Informal and can "
                                    "be considered rude or "
                                    "confrontational when used "
                                    "outside of close relationships "
                                    "or familiar contexts.",
                                },
                                {
                                    "dictionary_form": "近所(きんじょ)",
                                    "japanese_example": "近所(きんじょ)",
                                    "jlpt_level": "N5",
                                    "teaching_notes": "Noun: 'neighborhood' or "
                                    "'vicinity.' Refers to the "
                                    "immediate area around one's "
                                    "living place.",
                                },
                                {
                                    "dictionary_form": "どう言う(どういう)",
                                    "japanese_example": "どう言われてる(どういわれてる)",
                                    "jlpt_level": "N3",
                                    "teaching_notes": "Expression: 'how is it said.' "
                                    "This is a passive construction "
                                    "of '言う' (to say), indicating "
                                    "what is being said about someone "
                                    "or something in general terms.",
                                },
                                {
                                    "dictionary_form": "知る(しる)",
                                    "japanese_example": "知らない訳じゃない(しらないわけじゃない)",
                                    "jlpt_level": "N3",
                                    "teaching_notes": "Expression: 'it's not that I "
                                    "don't know.' A double negative "
                                    "form used to imply that the "
                                    "speaker actually knows "
                                    "something. '訳' (わけ) means "
                                    "'reason' or 'circumstance.'",
                                },
                                {
                                    "dictionary_form": "だろう",
                                    "japanese_example": "だろ",
                                    "jlpt_level": "N4",
                                    "teaching_notes": "Auxiliary: A less formal version "
                                    "of 'でしょう,' used to express "
                                    "probability or expectation, "
                                    "similar to 'right?' or 'isn't "
                                    "it?' in English.",
                                },
                            ],
                            "translated_text": "You know what the neighborhood says about you, right?",
                        },
                        ensure_ascii=False,
                    ),
                ),
            )
        ],
    )
)


def get_prompt_flashcards(chat_client: AbstractChatClient):
    return Prompt(chat_client=chat_client, role=role, tools=tools, examples=examples)
