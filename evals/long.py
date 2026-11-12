#!/usr/bin/env python3
"""Long-session eval: all tasks in tasks.json, one after another, on one copy of fixture/.

    python3 evals/long.py --reps 2

plain: one continuous session (each task resumes the last), so the context keeps growing.
boost: a fresh session per task (what /clear does) plus the reader agent.
Each task is checked right after it runs. Results: evals/long-results.jsonl."""
import argparse
import json
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

from run import CLAUDE, HERE, TOOLS, reader_json


def session(arm, rep, model):
    d = HERE / "runs" / f"long-{arm}-{rep}"
    shutil.rmtree(d, ignore_errors=True)
    shutil.copytree(HERE / "fixture", d)
    sid, out = None, []
    for step, task in enumerate(json.loads((HERE / "tasks.json").read_text())):
        cmd = [CLAUDE, "-p", task["prompt"], "--output-format", "json", "--allowedTools", TOOLS,
               "--max-budget-usd", "3", "--model", model]
        if arm == "plain" and sid:
            cmd += ["--resume", sid]
        if arm == "boost":
            cmd += ["--agents", reader_json(), "--no-session-persistence"]
        t0 = time.time()
        p = subprocess.run(cmd, cwd=d, capture_output=True, text=True, timeout=900)
        try:
            r = json.loads(p.stdout.splitlines()[0])
        except (ValueError, IndexError):
            r = {"is_error": True}
        sid = r.get("session_id") or sid
        ok = json.loads(subprocess.run([sys.executable, str(HERE / "check.py"), task["id"], str(d)],
                                       capture_output=True, text=True).stdout)["pass"]
        u = r.get("usage") or {}
        row = {"arm": arm, "rep": rep, "step": step, "task": task["id"], "pass": ok, "usd": r.get("total_cost_usd"),
               "prompt": u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("input_tokens", 0),
               "seconds": round(time.time() - t0, 1), "error": r.get("is_error"), "models": r.get("modelUsage")}
        print(json.dumps({k: row[k] for k in ("arm", "rep", "step", "task", "pass", "usd", "prompt")}), flush=True)
        out.append(row)
        (d / "ANSWER.txt").unlink(missing_ok=True)
        (d / "ANSWER.json").unlink(missing_ok=True)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--model", default="claude-opus-5-5")
    a = ap.parse_args()
    jobs = [(arm, r) for r in range(a.reps) for arm in ("plain", "boost")]
    with ThreadPoolExecutor(len(jobs)) as ex, (HERE / "long-results.jsonl").open("a") as f:
        for rows in ex.map(lambda j: session(*j, a.model), jobs):
            for row in rows:
                f.write(json.dumps(row) + "\n")


if __name__ == "__main__":
    main()
