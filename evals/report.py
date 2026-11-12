#!/usr/bin/env python3
"""evals/results*.jsonl -> markdown: per setup, pass rate and mean $ per run vs plain; then per task."""
import collections
import json
from pathlib import Path

HERE = Path(__file__).parent
rows = [json.loads(x) for f in sorted(HERE.glob("results*.jsonl")) for x in f.read_text().splitlines() if x.strip()]
ORDER = ["plain", "boost", "ponytail", "caveman", "pohuy", "context-mode"]
arms = [a for a in ORDER if any(r["arm"] == a for r in rows)]
tasks = sorted({r["task"] for r in rows})
cell = collections.defaultdict(list)
for r in rows:
    cell[(r["arm"], r["task"])].append(r)


def mean(rs, k):
    return sum((r.get(k) or 0) for r in rs) / len(rs) if rs else 0


def first_write(rs):
    return mean([{"x": (r.get("usage") or {}).get("cache_creation_input_tokens", 0)} for r in rs], "x")


base = [r for r in rows if r["arm"] == "plain"]
print("| Setup | Pass | $ per run | vs plain | Output tokens per run | Prompt written to cache per run |")
print("|---|:-:|--:|--:|--:|--:|")
for a in arms:
    rs = [r for r in rows if r["arm"] == a]
    out = mean([{"x": (r.get("usage") or {}).get("output_tokens", 0)} for r in rs], "x")
    d = (mean(rs, "usd") - mean(base, "usd")) / mean(base, "usd")
    print(f"| {a} | {sum(r['pass'] for r in rs)}/{len(rs)} | ${mean(rs, 'usd'):.3f} | {d:+.0%} | {out:,.0f} | {first_write(rs):,.0f} |")
print("\n| Task | " + " | ".join(arms) + " |")
print("|---|" + "--:|" * len(arms))
for t in tasks:
    cells = []
    for a in arms:
        rs = cell[(a, t)]
        cells.append(f"${mean(rs, 'usd'):.3f} ({sum(r['pass'] for r in rs)}/{len(rs)})" if rs else "-")
    print(f"| {t} | " + " | ".join(cells) + " |")
