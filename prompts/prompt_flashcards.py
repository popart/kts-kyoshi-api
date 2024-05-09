import json

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
                          "japanese_example": { "type": "string", "description": "the vocab or grammar point as written and conjugated in the input text, without changes. pronunciation appended in parenthesis when needed." },
                          "dictionary_form": {"type": "string", "description": "For vocab words, the vocab word in its dictionary, root form, in its most commonly seen writing variant. pronunciation appended in parenthesis when needed." },
                          "teaching_notes": {"type": "string", "description": "Explanation of grammar, including conjugation & colloqualisms. For shortened spoken forms, expands the form to its full originating phrase" },
                      }
                  },
                },
                "translation": {
                    "type": "string",
                    "description": "the simplest translation that still captures the nuance of the sentence"
                },
              },
              "required": ["japanese_vocab_words", "translation"]
            }
        }
    },
]
examples = []
examples.append({"role": "user", "content": "しょうがない、それでいこう" })
examples.append({
    "role": "assistant",
    "tool_calls": [{
        "id": "call_001",
        "type": "function",
        "function": {
            "name": "save_japanese_vocab_words",
            "arguments": json.dumps({
                "japanese_flash_cards": [
                    {
                        "japanese_example":"しょうがない",
                        "dictionary_form":"仕方がない(しかたがない)",
                        "teaching_notes":"Expression: 'It can't be helped' or 'nothing can be done about it.' Often used to express resignation or acceptance of a situation. A contraction where '仕方' means 'method' or 'way,' and 'がない' means 'there is none.'"
                    },
                    {
                        "japanese_example":"それで",
                        "dictionary_form":"それで",
                        "teaching_notes":"Conjunction: 'and with that,' 'therefore,' or 'because of that.' Used to connect sentences or clauses, indicating a cause or reason leading to a result."
                    },
                    {
                        "japanese_example":"いこう",
                        "dictionary_form":"行く(いく)",
                        "teaching_notes":"Verb: volitional form of the verb '行く' (to go), used to express a decision or suggestion about the future, equivalent to saying 'let's go' in English."
                    }
                ],
                "translation": "It can't be helped, let's go with that."
            })
        }
    }]
})
examples.append({
    "role": "tool",
    "tool_call_id": "call_001",
    "content": "SUCCESS",
})

flashcards_prompt = Prompt(role=role, tools=tools, examples=examples)
