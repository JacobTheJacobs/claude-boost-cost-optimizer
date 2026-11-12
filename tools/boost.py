#!/usr/bin/env python3
"""Claude Boost usage report: where your Claude Code tokens and dollars went, from the local session logs.

    python3 tools/boost.py                 last 7 days, all projects
    python3 tools/boost.py --days 1        today and yesterday
    python3 tools/boost.py --project NAME  only projects whose folder name contains NAME
    python3 tools/boost.py --today-usd     print today's list-price dollars only (used by hooks/budget.py)

Reads ~/.claude/projects/*/*.jsonl and each session's subagents/*.jsonl. Each API message is counted once, at its last
logged usage. Dollars are list prices (below); a subscription is billed differently, so treat them as relative weight.
Standard library only."""
import argparse
import collections
import datetime as dt
import json
import sys
from pathlib import Path

ROOT = Path.home() / ".claude" / "projects"
# $ per 1M tokens: input, output, cache read, 5m cache write, 1h cache write. Anthropic pricing page, 2026-11-10.
RATES = {
    "fable-5-2": (8.00, 40.00, 0.20, 10.00, 16.00),
    "fable-5-1": (10.00, 50.00, 0.25, 12.50, 20.00),
    "opus-5-5": (4.00, 20.00, 0.20, 5.00, 8.00),
    "sonnet-5-5": (2.00, 10.00, 0.10, 2.50, 4.00),
    "haiku-5-5": (0.10, 0.50, 0.01, 0.125, 0.20),
    "haiku-5-5-long": (0.50, 2.50, 0.05, 0.625, 1.00),  # whole request, prompt over 100K tokens
    "opus": (5.00, 25.00, 0.50, 6.25, 10.00),  # older Opus 4.x / 5
    "sonnet": (3.00, 15.00, 0.30, 3.75, 6.00),  # older Sonnet 4.x
    "haiku": (1.00, 5.00, 0.10, 1.25, 2.00),  # Haiku 4.5
}


def rate(model: str, prompt: int):
    m = model.lower()
    for k in ("fable-5-2", "fable-5-1", "opus-5-5", "sonnet-5-5", "haiku-5-5"):
        if k in m:
            return RATES[k + "-long"] if k == "haiku-5-5" and prompt > 100_000 else RATES[k]
    for k in ("opus", "sonnet", "haiku"):
        if k in m:
            return RATES[k]
    return None


def messages(path: Path):
    """Last usage snapshot per API message id in one transcript."""
    last = {}
    try:
        lines = path.open(errors="replace")
    except OSError:
        return []
    with lines:
        for line in lines:
            if '"usage"' not in line:
                continue
            try:
                d = json.loads(line)
            except ValueError:
                continue
            m = d.get("message") or {}
            u = m.get("usage")
            if not isinstance(u, dict) or not m.get("model") or m["model"].startswith("<"):
                continue
            last[m.get("id") or d.get("uuid")] = (d.get("timestamp", ""), m["model"], u)
    return last.values()


def cost(model: str, u: dict) -> float:
    i, o, cr = u.get("input_tokens", 0), u.get("output_tokens", 0), u.get("cache_read_input_tokens", 0)
    cc = u.get("cache_creation") or {}
    w5 = cc.get("ephemeral_5m_input_tokens", 0)
    w1 = cc.get("ephemeral_1h_input_tokens", 0)
    if not cc:
        w5 = u.get("cache_creation_input_tokens", 0)
    r = rate(model, i + cr + w5 + w1)
    if not r:
        return 0.0
    return (i * r[0] + o * r[1] + cr * r[2] + w5 * r[3] + w1 * r[4]) / 1e6


def collect(days: int, project: str | None):
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=days)).isoformat()
    rows = []
    for proj in sorted(ROOT.glob("*")):
        if project and project not in proj.name:
            continue
        for t in proj.glob("*.jsonl"):
            sid = t.stem
            files = [(t, "main")] + [(s, "subagent") for s in (proj / sid / "subagents").glob("*.jsonl")]
            for f, who in files:
                if f.stat().st_mtime < (dt.datetime.now() - dt.timedelta(days=days + 1)).timestamp():
                    continue
                for ts, model, u in messages(f):
                    if ts >= since:
                        rows.append((proj.name, sid, who, ts, model, u))
    return rows


def today_usd(project: str | None) -> float:
    start = dt.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).astimezone(dt.timezone.utc).isoformat()
    return sum(cost(m, u) for _, _, _, ts, m, u in collect(1, project) if ts >= start)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--project")
    ap.add_argument("--today-usd", action="store_true")
    a = ap.parse_args()
    if a.today_usd:
        print(f"{today_usd(a.project):.2f}")
        return
    rows = collect(a.days, a.project)
    if not rows:
        sys.exit("no usage found")
    tok = collections.Counter()
    usd = collections.Counter()
    for proj, sid, who, ts, model, u in rows:
        c = cost(model, u)
        cc = u.get("cache_creation_input_tokens", 0)
        tok["input"] += u.get("input_tokens", 0)
        tok["cache read"] += u.get("cache_read_input_tokens", 0)
        tok["cache write"] += cc
        tok["output"] += u.get("output_tokens", 0)
        usd["total"] += c
        usd["who:" + who] += c
        usd["model:" + model] += c
        usd["proj:" + proj] += c
        usd["sess:" + proj + "/" + sid[:8]] += c
        r = rate(model, 0)
        if r:
            usd["class:cache read"] += u.get("cache_read_input_tokens", 0) * r[2] / 1e6
            usd["class:output"] += u.get("output_tokens", 0) * r[1] / 1e6
            usd["class:input"] += u.get("input_tokens", 0) * r[0] / 1e6
    usd["class:cache write"] = usd["total"] - usd["class:cache read"] - usd["class:output"] - usd["class:input"]
    t = usd["total"] or 1
    prompt = tok["input"] + tok["cache read"] + tok["cache write"]
    hit = tok["cache read"] / prompt if prompt else 0
    print(f"Claude Boost report, last {a.days} days: ${usd['total']:.2f} list price, {len(rows)} requests")
    print(f"cache read share of input: {hit:.0%}  (Anthropic: agent loops ~84%; look into it below 80%)")
    avg = prompt / len(rows)
    print(f"average prompt per request: {avg / 1000:.0f}K tokens (every request re-reads it)")

    def block(title, prefix, n=8):
        print(f"\n{title}")
        for k, v in sorted(((k, v) for k, v in usd.items() if k.startswith(prefix)), key=lambda x: -x[1])[:n]:
            print(f"  {k[len(prefix):]:<52} ${v:8.2f}  {v / t:5.0%}")

    block("by token class", "class:")
    block("main thread vs subagents", "who:")
    block("by model", "model:")
    block("by project", "proj:")
    block("top sessions", "sess:")
    tips = []
    if hit < 0.8:
        tips.append("cache read share under 80%: something rewrites the prompt start (CLAUDE.md/settings/effort edits, model switches, long pauses)")
    if usd["class:cache write"] / t > 0.3:
        tips.append("cache writes over 30% of spend: fewer mid-session model/effort switches; resume less after long breaks")
    if usd["class:cache read"] / t > 0.5 and avg > 80_000:
        tips.append(f"cache reads are {usd['class:cache read'] / t:.0%} of spend at ~{avg / 1000:.0f}K tokens a request: the context is too long; /clear or a new session per task, /compact earlier, hand bulky reads to `reader`")
    if usd["class:output"] / t > 0.3:
        tips.append("output over 30% of spend: ask for shorter answers (skills/lean)")
    if usd["who:subagent"] / t > 0.1:
        tips.append("subagents over 10%: route easy lookups to the Haiku `reader` agent, not `fork` (forks run on your main model)")
    if tips:
        print("\nlevers")
        for x in tips:
            print("  - " + x)


if __name__ == "__main__":
    main()
