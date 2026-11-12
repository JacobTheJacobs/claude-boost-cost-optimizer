#!/usr/bin/env python3
"""Claude Boost eval: the same tasks, plain Claude Code vs Claude Code + Boost, on a fresh copy of fixture/ each run.

    python3 evals/run.py --reps 2 [--model opus]

Per run: claude -p in headless mode, JSON output (total_cost_usd, turns, time), then check.py for pass/fail.
Plain arm: your setup with nothing added. Boost arm: + the reader agent (Haiku) and the lean/reader instructions.
Results go to evals/results.jsonl; evals/report.py turns them into the README table."""
import argparse
import glob
import os
import json
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
CLAUDE = os.environ.get("CLAUDE_BIN") or sorted(glob.glob(os.path.expanduser("~/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude")))[-1]
EXT = os.environ.get("BOOST_EXT", str(HERE / "ext"))
PLUGINS = {"ponytail": f"{EXT}/pt", "caveman": f"{EXT}/cv", "context-mode": f"{EXT}/cmnpm/package"}
TOOLS = "Read,Edit,Write,Grep,Glob,Bash(python3 *),Bash(grep *),Bash(wc *),Bash(ls *),Agent,Task,mcp__plugin_context-mode_context-mode"


def reader_json():
    t = (ROOT / "agents" / "reader.md").read_text().split("---")
    head, body = t[1], "---".join(t[2:]).strip()
    meta = dict(line.split(": ", 1) for line in head.strip().splitlines() if ": " in line)
    return json.dumps({"reader": {"description": meta["description"], "prompt": body, "model": meta["model"],
                                  "tools": [x.strip() for x in meta["tools"].split(",")]}})


def one(arm, task, rep, model):
    d = HERE / "runs" / f"{arm}-{task['id']}-{rep}"
    shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(HERE / "fixture", d)
    cmd = [CLAUDE, "-p", task["prompt"], "--output-format", "json", "--no-session-persistence",
           "--allowedTools", TOOLS, "--max-budget-usd", "3"]
    if model:
        cmd += ["--model", model]
    if arm == "boost":
        cmd += ["--agents", reader_json()]
    elif arm == "pohuy":
        cmd += ["--append-system-prompt-file", str(HERE / "pohuy_style.md")]
    elif arm in PLUGINS:
        cmd += ["--plugin-dir", PLUGINS[arm]]
    t0 = time.time()
    p = subprocess.run(cmd, cwd=d, capture_output=True, text=True, timeout=900)
    try:
        r = json.loads(p.stdout.splitlines()[0])
    except ValueError:
        r = {"is_error": True, "result": (p.stdout + p.stderr)[-300:]}
    ok = json.loads(subprocess.run([sys.executable, str(HERE / "check.py"), task["id"], str(d)],
                                   capture_output=True, text=True).stdout)["pass"]
    row = {"arm": arm, "task": task["id"], "rep": rep, "pass": ok, "usd": r.get("total_cost_usd"),
           "turns": r.get("num_turns"), "seconds": round(time.time() - t0, 1), "error": r.get("is_error"),
           "usage": r.get("usage"), "models": r.get("modelUsage")}
    print(json.dumps({k: row[k] for k in ("arm", "task", "rep", "pass", "usd", "turns", "seconds")}), flush=True)
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--model", default="claude-opus-5-5")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--arms", default="plain,boost")
    ap.add_argument("--tasks")
    a = ap.parse_args()
    tasks = json.loads((HERE / "tasks.json").read_text())
    if a.tasks:
        tasks = [t for t in tasks if t["id"] in a.tasks.split(",")]
    jobs = [(arm, t, r) for r in range(a.reps) for t in tasks for arm in a.arms.split(",")]
    out = HERE / "results.jsonl"
    with ThreadPoolExecutor(a.jobs) as ex, out.open("a") as f:
        for row in ex.map(lambda j: one(*j, a.model), jobs):
            f.write(json.dumps(row) + "\n")
            f.flush()


if __name__ == "__main__":
    main()
