"""New experiment: stress the flat (id/parent_id) tree encoding.

Companion to `flat_vs_recursive_tree.py`. The A/B experiment measures speed /
stability on a small balanced tree. This experiment only asks whether the flat
encoding stays intact when the parse tree is large and deep:

- does the model still return schema-valid JSON?
- does it keep every `parent_id` pointing at a real node?
- are ids unique, is there exactly one root, is every node reachable?

Usage:
    QWEN_API_KEY=... PYTHONPATH=src uv run python experiments/qwen3.8-flash/flat_tree_stress.py
    QWEN_API_KEY=... PYTHONPATH=src uv run python experiments/qwen3.8-flash/flat_tree_stress.py \
        --sentence "..." --trials 3
"""

import argparse
from dataclasses import dataclass, field
import os
import time

import httpx
from openai import OpenAI
from pydantic import BaseModel, Field

MODEL = os.getenv("LLM_MODEL", "qwen3.8-flash")
BASE_URL = os.getenv(
    "LLM_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
)

SENTENCE = (
    "新宿と小田原を60分で結ぶことを目指した「画期的な軽量高性能新特急車」として計画され、"
    "開発に際して日本国有鉄道（国鉄）の鉄道技術研究所より技術協力が得られたことから、"
    "日本の鉄道車両において初の導入となる新技術がいくつか盛り込まれた車両であり、"
    "それらの中には国鉄の新幹線に発展的に引き継がれた技術も存在し、"
    "「新幹線のルーツ」や「超高速鉄道のパイオニア」ともいわれている。"
)

SYSTEM = "You decompose Japanese sentences into grammatical constituent trees."

TASK = (
    "Break the following Japanese sentence into a complete grammatical parse "
    "tree. Nest clauses and phrases as deeply as the grammar requires; every "
    "leaf is a single word or particle. Give each node a grammatical label, the "
    "Japanese text it covers, and an English gloss.\n\n"
    "Encode the tree as a flat list of nodes. The root has id 0 and parent_id "
    "null. Every other node has a unique id and stores the id of its parent.\n\n"
    f"Sentence: {SENTENCE}"
)


class FlatNode(BaseModel):
    id: int = Field(description="Unique id. The root has id 0.")
    parent_id: int | None = Field(description="id of the parent node; null for the root")
    label: str = Field(description="Grammatical role, e.g. 'Sentence', 'Noun Phrase'")
    japanese: str = Field(description="The Japanese text covered by this node")
    translation: str = Field(description="English gloss of this node")


class FlatTree(BaseModel):
    nodes: list[FlatNode] = Field(description="All nodes of the tree in a flat list")


@dataclass
class TreeNode:
    label: str
    japanese: str
    translation: str
    children: list["TreeNode"] = field(default_factory=list)


@dataclass
class FlatIssues:
    duplicate_ids: list[int] = field(default_factory=list)
    missing_parent: list[tuple[int, int]] = field(default_factory=list)
    multiple_roots: int = 0
    unreachable: list[int] = field(default_factory=list)
    cycles: list[int] = field(default_factory=list)

    @property
    def any(self) -> bool:
        return bool(
            self.duplicate_ids
            or self.missing_parent
            or self.multiple_roots > 1
            or self.unreachable
            or self.cycles
        )

    def __str__(self) -> str:
        if not self.any:
            return "ids ok"
        parts = []
        if self.duplicate_ids:
            parts.append(f"duplicate ids={self.duplicate_ids}")
        if self.missing_parent:
            parts.append(f"missing parents={self.missing_parent}")
        if self.multiple_roots > 1:
            parts.append(f"{self.multiple_roots} roots")
        if self.unreachable:
            parts.append(f"unreachable={self.unreachable}")
        if self.cycles:
            parts.append(f"cycles={self.cycles}")
        return ", ".join(parts)


def from_flat(tree: FlatTree) -> tuple[list[TreeNode], FlatIssues]:
    """Rebuild the nested tree from the flat id/parent_id list.

    Returns the forest (one tree per root) plus any id integrity problems.
    """
    issues = FlatIssues()

    by_id: dict[int, FlatNode] = {}
    for node in tree.nodes:
        if node.id in by_id:
            issues.duplicate_ids.append(node.id)
            continue
        by_id[node.id] = node

    children: dict[int, list[int]] = {i: [] for i in by_id}
    for node in by_id.values():
        if node.parent_id is None:
            continue
        if node.parent_id not in by_id:
            issues.missing_parent.append((node.id, node.parent_id))
            continue
        children[node.parent_id].append(node.id)

    root_ids = [i for i, n in by_id.items() if n.parent_id is None]
    issues.multiple_roots = len(root_ids)

    seen: set[int] = set()
    visiting: set[int] = set()

    def build(node_id: int) -> TreeNode:
        if node_id in visiting:
            issues.cycles.append(node_id)
            return TreeNode("", "", "")
        visiting.add(node_id)
        node = by_id[node_id]
        built = TreeNode(
            label=node.label,
            japanese=node.japanese,
            translation=node.translation,
            children=[build(c) for c in children[node_id]],
        )
        visiting.discard(node_id)
        seen.add(node_id)
        return built

    forest = [build(i) for i in root_ids]
    issues.unreachable = sorted(set(by_id) - seen)
    return forest, issues


def stats(node: TreeNode) -> tuple[int, int]:
    """Return (node_count, depth)."""
    if not node.children:
        return 1, 1
    counts, depths = zip(*(stats(c) for c in node.children))
    return 1 + sum(counts), 1 + max(depths)


def render(node: TreeNode, indent: int = 0) -> list[str]:
    lines = [f"{'  ' * indent}{node.label} | {node.japanese} | {node.translation}"]
    for child in node.children:
        lines += render(child, indent + 1)
    return lines


def run_trial(client: OpenAI, sentence: str) -> dict:
    task = TASK.replace(SENTENCE, sentence)
    started = time.perf_counter()
    try:
        response = client.chat.completions.parse(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": task},
            ],
            response_format=FlatTree,
            temperature=0.1,
            extra_body={"enable_thinking": False},
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {str(exc)[:200]}",
            "latency_s": time.perf_counter() - started,
        }

    latency = time.perf_counter() - started
    usage = response.usage
    parsed = response.choices[0].message.parsed
    if parsed is None:
        return {
            "ok": False,
            "error": f"parsed=None finish={response.choices[0].finish_reason}",
            "latency_s": latency,
            "completion_tokens": usage.completion_tokens if usage else None,
        }

    forest, issues = from_flat(parsed)
    node_counts = [stats(t)[0] for t in forest]
    depths = [stats(t)[1] for t in forest]
    return {
        "ok": True,
        "latency_s": latency,
        "completion_tokens": usage.completion_tokens if usage else None,
        "raw": parsed,
        "forest": forest,
        "issues": issues,
        "nodes": sum(node_counts),
        "depth": max(depths, default=0),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=1)
    parser.add_argument("--sentence", default=SENTENCE)
    parser.add_argument(
        "--show-tree", action="store_true", help="print the rebuilt parse tree"
    )
    parser.add_argument(
        "--save-json", default=None, help="write the raw flat JSON to this path"
    )
    args = parser.parse_args()

    client = OpenAI(
        base_url=BASE_URL,
        api_key=os.environ["QWEN_API_KEY"],
        timeout=httpx.Timeout(600.0, connect=10.0),
    )

    # warm up the connection so the first timed call isn't paying setup cost
    client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "Say 'ok'."}],
        max_tokens=5,
        extra_body={"enable_thinking": False},
    )

    print(f"sentence: {args.sentence}\n")

    for i in range(args.trials):
        trial = run_trial(client, args.sentence)
        if not trial["ok"]:
            print(
                f"trial {i + 1:>2}: FAIL after {trial['latency_s']:.2f}s "
                f"({trial['error']})"
            )
            continue

        print(
            f"trial {i + 1:>2}: {trial['latency_s']:6.2f}s "
            f"tokens={trial['completion_tokens']} nodes={trial['nodes']} "
            f"depth={trial['depth']} [{trial['issues']}]"
        )
        if args.save_json:
            with open(args.save_json, "w", encoding="utf-8") as fh:
                fh.write(trial["raw"].model_dump_json(indent=2))
            print(f"           saved raw JSON to {args.save_json}")
        if args.show_tree:
            for tree in trial["forest"]:
                for line in render(tree):
                    print(f"           {line}")


if __name__ == "__main__":
    main()