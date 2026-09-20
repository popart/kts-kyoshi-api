"""A/B test: recursive tree schema vs flat (id/parent_id) list schema.

Hypothesis: models return a tree encoded as a flat list of nodes with
`id` / `parent_id` faster (and at least as accurately) than a recursive
nested schema.

Both schemas encode the same tree: 1 root + 3 children + 9 grandchildren.
Shape variation is reported, not treated as failure. The flat representation is
rebuilt into a real tree so we can check whether the model kept the ids
consistent (duplicates, orphans, cycles, multiple roots). Thinking is disabled,
matching the app's client.

Usage:
    QWEN_API_KEY=... PYTHONPATH=src uv run python experiments/qwen3.8-flash/flat_vs_recursive_tree.py --trials 10
"""

import argparse
from dataclasses import dataclass, field
import os
import statistics
import time

import httpx
from openai import OpenAI
from pydantic import BaseModel, Field

MODEL = os.getenv("LLM_MODEL", "qwen3.8-flash")
BASE_URL = os.getenv(
    "LLM_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"
)

SENTENCE = "大型で強い台風25号は、関東に接近する見込みだ。"

SYSTEM = "You decompose Japanese sentences into grammatical constituent trees."

TASK = (
    "Break the following Japanese sentence into a grammatical constituent tree "
    "of exactly depth 2: one root, exactly 3 children of the root, and exactly "
    "3 children for each of those (13 nodes total). Leaves are words or "
    "particles. Give each node a grammatical label, the Japanese text, and an "
    "English gloss.\n\n"
    f"Sentence: {SENTENCE}"
)

FLAT_HINT = (
    "\n\nEncode the tree as a flat list of nodes. The root has id 0 and "
    "parent_id null. Every other node has a unique id and stores the id of its "
    "parent."
)


class RecursiveNode(BaseModel):
    label: str = Field(description="Grammatical role, e.g. 'Sentence', 'Noun Phrase'")
    japanese: str = Field(description="The Japanese text covered by this node")
    translation: str = Field(description="English gloss of this node")
    children: list["RecursiveNode"] = Field(
        description="Sub-constituents; empty list for leaves"
    )


RecursiveNode.model_rebuild()


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


def from_recursive(node: RecursiveNode) -> TreeNode:
    return TreeNode(
        label=node.label,
        japanese=node.japanese,
        translation=node.translation,
        children=[from_recursive(c) for c in node.children],
    )


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


def signature(node: TreeNode) -> str:
    if not node.children:
        return "."
    return "(" + ",".join(signature(c) for c in node.children) + ")"


def render(node: TreeNode, indent: int = 0) -> list[str]:
    lines = [f"{'  ' * indent}{node.label} | {node.japanese} | {node.translation}"]
    for child in node.children:
        lines += render(child, indent + 1)
    return lines


def run_trial(client: OpenAI, schema, hint: str) -> dict:
    started = time.perf_counter()
    try:
        response = client.chat.completions.parse(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": TASK + hint},
            ],
            response_format=schema,
            temperature=0.1,
            extra_body={"enable_thinking": False},
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {str(exc)[:160]}",
            "latency_s": time.perf_counter() - started,
        }

    latency = time.perf_counter() - started
    usage = response.usage
    parsed = response.choices[0].message.parsed
    result = {
        "ok": parsed is not None,
        "latency_s": latency,
        "completion_tokens": usage.completion_tokens if usage else None,
    }

    if parsed is None:
        return result

    if isinstance(parsed, RecursiveNode):
        forest = [from_recursive(parsed)]
        issues = FlatIssues()
    else:
        forest, issues = from_flat(parsed)

    node_counts = [stats(t)[0] for t in forest]
    depths = [stats(t)[1] for t in forest]
    result.update(
        forest=forest,
        issues=issues,
        nodes=sum(node_counts),
        depth=max(depths, default=0),
        signature="/".join(signature(t) for t in forest),
    )
    return result


def summarize(name: str, trials: list[dict]) -> dict:
    ok = [t for t in trials if t.get("ok")]
    latencies = [t["latency_s"] for t in ok]
    tokens = [t["completion_tokens"] for t in ok if t["completion_tokens"]]
    issues = [t["issues"] for t in ok]
    return {
        "name": name,
        "n": len(trials),
        "valid": len(ok),
        "latency_mean": statistics.mean(latencies) if latencies else None,
        "latency_median": statistics.median(latencies) if latencies else None,
        "completion_tokens_mean": statistics.mean(tokens) if tokens else None,
        "node_counts": sorted(t["nodes"] for t in ok),
        "depths": sorted(t["depth"] for t in ok),
        "bad_ids": sum(1 for i in issues if i.any),
        "bad_id_details": [str(i) for i in issues if i.any],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=10)
    args = parser.parse_args()

    client = OpenAI(
        base_url=BASE_URL,
        api_key=os.environ["QWEN_API_KEY"],
        timeout=httpx.Timeout(300.0, connect=10.0),
    )

    # warm up the connection so the first timed call isn't paying setup cost
    client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": "Say 'ok'."}],
        max_tokens=5,
        extra_body={"enable_thinking": False},
    )

    results: dict[str, list[dict]] = {"recursive": [], "flat": []}
    for i in range(args.trials):
        order = ["recursive", "flat"] if i % 2 == 0 else ["flat", "recursive"]
        for name in order:
            schema, hint = (
                (RecursiveNode, "") if name == "recursive" else (FlatTree, FLAT_HINT)
            )
            trial = run_trial(client, schema, hint)
            results[name].append(trial)

            if not trial.get("ok"):
                print(f"trial {i + 1:>2} {name:>9}: FAIL ({trial.get('error')})")
                continue

            print(
                f"trial {i + 1:>2} {name:>9}: {trial['latency_s']:6.2f}s "
                f"tokens={trial['completion_tokens']} nodes={trial['nodes']} "
                f"depth={trial['depth']} [{trial['issues']}]"
            )
            print(f"            shape: {trial['signature']}")
            for tree in trial["forest"]:
                for line in render(tree):
                    print(f"              {line}")
        print()

    print("=== summary ===")
    summaries = [summarize(name, trials) for name, trials in results.items()]
    for s in summaries:
        mean = f"{s['latency_mean']:.2f}s" if s["latency_mean"] else "n/a"
        median = f"{s['latency_median']:.2f}s" if s["latency_median"] else "n/a"
        tokens = (
            f"{s['completion_tokens_mean']:.0f}"
            if s["completion_tokens_mean"]
            else "n/a"
        )
        print(
            f"{s['name']:>9}: valid {s['valid']}/{s['n']}, latency mean {mean} "
            f"median {median}, completion tokens {tokens}"
        )
        print(f"           node counts {s['node_counts']}")
        print(f"           depths      {s['depths']}")
        print(f"           bad ids     {s['bad_ids']}/{s['valid']} {s['bad_id_details']}")

    if all(s["latency_mean"] for s in summaries):
        rec, flat = summaries
        delta = (flat["latency_mean"] - rec["latency_mean"]) / rec["latency_mean"] * 100
        faster = "flat" if delta < 0 else "recursive"
        print(f"\n{faster} was faster by {abs(delta):.1f}% (mean latency)")


if __name__ == "__main__":
    main()