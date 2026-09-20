# qwen3.8-flash findings

Notes from switching the kyoshi backend from OpenAI tool-calling to
qwencloud + structured output.

## Setup

- Provider: `qwencloud` (Alibaba DashScope, **OpenAI-compatible** endpoint)
- Base URL: `https://dashscope-intl.aliyuncs.com/compatible-mode/v1`
- Model: `qwen3.8-flash`
- Key: `QWEN_API_KEY` (read from env by `OpenAIChatClient`)
- SDK: `openai` 1.109.1, `pydantic` 2.13.5

## Tool calling

`qwen3.8-flash` runs in **thinking mode** by default. That breaks the old
tool-calling code in two ways:

1. `tool_choice="required"` (what `Prompt.fetch` used to send) is rejected:

   ```
   400 InternalError.Algo.InvalidParameter:
   The tool_choice parameter does not support being set to required or object
   in thinking mode
   ```

   `tool_choice="auto"` works, and the model still called the single tool
   because the system prompt told it to.

2. Tool-calling worked, but the app isn't really choosing among tools (there is
   exactly one function), so tool calling was the wrong abstraction anyway.

## Structured output

Two modes on the compatible endpoint:

- `{"type": "json_object"}` — requires the word "json" somewhere in
  `messages`, otherwise 400. Does not enforce a structure.
- `{"type": "json_schema", "json_schema": {"name", "strict": True, "schema"}}`
  — enforces the schema. Works for the Qwen3.8-Flash series (per docs).

Using the SDK helper `client.chat.completions.parse(..., response_format=<PydanticModel>)`
generates the JSON schema from the pydantic model (nested models become
`$defs` + `$ref`) and parses the reply back into a typed object. DashScope
accepts the `$defs`/`$ref` schema.

### The gotcha: thinking mode

With thinking mode **on** (the default), `parse()` took >180 s and appeared to
hang. This is the "slightly different semantics" between endpoints:

- thinking on + strict json_schema = very slow / unreliable
- `extra_body={"enable_thinking": False}` + strict json_schema = ~8-15 s

The tutor prompt is pure text transformation, so reasoning isn't needed. We
disable it in `OpenAIChatClient`.

### Other rules

- **Do not set `max_tokens`** with structured output: the cap can truncate the
  JSON mid-output and produce invalid JSON. (The old client set it to 1500.)
- `temperature=0.1` is fine; `frequency_penalty` / `presence_penalty` were
  dropped to keep the request surface small.

## What changed

- `data_types/lesson_types.py` (new): pydantic `JapaneseLesson` / `FlashCard`
  schema (the structured-output contract).
- `data_types/chat_types.py`: `ChatMessage` is now a pydantic model with an
  optional `lesson: JapaneseLesson`. `to_llm_message()` serializes a lesson to
  JSON `content`; `dict_to_chat_message()` converts legacy `tool_calls` rows.
- `clients/chat/openai_chat_client.py`: uses `chat.completions.parse()` with
  `enable_thinking=False`; returns the parsed model or `None`; no tools, no
  `max_tokens`.
- `clients/chat/abstract_chat_client.py`: `complete_chat(messages, response_model)`.
- `prompts/prompt.py`: `Prompt` takes a `response_model`.
- `prompts/prompt_flash_cards.py`: few-shot assistant turns are now JSON
  `content` instead of tool calls.
- `data_types/chat_response_types.py`: builds the API lesson from
  `chat_message.lesson`.
- `app.py` / `chat_handler.py`: save the structured lesson; new chats record
  `llm_provider="QWEN"`.

## Verified live

`prompt.fetch()` on a Japanese weather-forecast line returned a valid
`JapaneseLesson` in ~15 s with 7 flash cards.

## A/B test: recursive tree vs flat (id/parent_id) list

Hypothesis: models handle a tree encoded as a **flat list of nodes with
`id`/`parent_id`** faster (and at least as accurately) than a **recursive
nested schema**.

Harness: `experiments/qwen3.8-flash/flat_vs_recursive_tree.py`. Same sentence, same tree
shape (1 root + 3 children + 9 grandchildren = 13 nodes), thinking off,
temperature 0.1.

### Results (10 trials/schema, 13-node balanced tree)

Both schemas returned valid, schema-conformant output in every trial.

- **Flat id integrity held**: 0/10 trials had bad ids (no duplicates, orphans,
  cycles, or extra roots). The rebuild function found `parent_id` references
  correct at this size.
- **Latency**:
  - flat: median **6.35s** (5.94-8.31s), mean 6.64s
  - recursive: median **10.09s** (6.46-20.58s), mean **47.02s** due to two
    multi-minute outliers (196.8s, 188.5s)
  - One outlier emitted only 479 tokens / 13 nodes, so the stall was
    server-side, not output length. A self-referential `$ref` schema looks like
    it can intermittently trigger pathological latency.
- **Output size**: recursive used more completion tokens (mean 728 vs 451) with
  a much wider spread (473-1234).
- **Shape drift**: flat mostly produced exactly the requested balanced tree
  `((.,.,.),(.,.,.),(.,.,.))` (13 nodes; a few 14/depth 4). Recursive drifted
  more: node counts 13-31, depth 3-4, often unbalanced.
- Both schemas inserted `Empty` filler leaves to satisfy "exactly 3 children".

**Smoke-test verdict**: consistent with the hypothesis. Flat isn't clearly
faster at the median (6.35s vs 10.09s) but it is far more stable / lower
variance, emits fewer tokens, stays closer to the requested shape, and the
id/parent_id encoding survived intact. Worth re-running with a harder sentence
(many nested clauses) and a deeper tree to really stress id integrity.

## New experiment: flat tree stress test

`experiments/qwen3.8-flash/flat_tree_stress.py` — flat-only, full parse tree,
no length cap. This is separate from the A/B harness above.

First run on a long nested-clause sentence (Shinjuku–Odawara 新特急車):

- valid, `ids ok`, **106 nodes**, **depth 14**, 4102 completion tokens, 51.6s
- no duplicate ids, orphans, cycles, or extra roots

The flat encoding survived a tree ~8x larger and ~4x deeper than the A/B tree
with every `parent_id` still pointing at a real node. One trial so far.