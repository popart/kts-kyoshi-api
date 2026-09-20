"""Schema for a structured Japanese lesson (LLM structured output)."""

from typing import Literal

from pydantic import BaseModel, Field


class FlashCard(BaseModel):
    japanese_example: str = Field(
        description=(
            "The vocab or grammar point as written and conjugated in the "
            "example_sentence, without changes. Each individual kanji is "
            "followed by its hiragana pronunciation in parenthesis."
        )
    )
    dictionary_form: str = Field(
        description=(
            "For vocab words, the word in its root, dictionary form (辞書形), "
            "in its most commonly seen writing variant. Each individual kanji "
            "is followed by its hiragana pronunciation in parenthesis."
        )
    )
    teaching_notes: str = Field(
        description=(
            "Complete explanation of the grammar or vocabulary in "
            "japanese_example, including conjugation and colloquialisms. For "
            "shortened spoken forms, expand the form to its full originating "
            "phrase and explain how the elements combine. For vocab words, "
            "give a translation and explain it. For proper names, explain what "
            "the name means and the kanji for it. Do not use romaji."
        )
    )
    jlpt_level: Literal["N5", "N4", "N3", "N2", "N1"] = Field(
        description="Approximate JLPT level for this teaching point."
    )


class JapaneseLesson(BaseModel):
    student_input: str = Field(
        description=(
            "The student's original query or request, corrected for any typos "
            "that cannot be attributed to vernacular speech."
        )
    )
    tutor_response: str = Field(
        description=(
            "The tutor's response to the student: a literal translation or an "
            "answer to a pedagogical question. If the student_input was "
            "unrelated to language learning, return an empty string."
        )
    )
    example_sentence: str = Field(
        description=(
            "A sentence in Japanese that exemplifies the main teaching points "
            "from the tutor_response. If the student_input was already a "
            "Japanese sentence, reuse the corrected student_input. Each "
            "individual kanji is followed by its pronunciation in parenthesis."
        )
    )
    example_sentence_translation: str = Field(
        description="The example_sentence translated into English."
    )
    japanese_flash_cards: list[FlashCard] = Field(
        description=(
            "The example_sentence broken down into bite-size vocabulary and "
            "grammar teaching points, in the order they appear in the sentence."
        )
    )