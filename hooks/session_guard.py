#!/usr/bin/env python3
"""Long-session guard (UserPromptSubmit hook): tells you when the session has grown long enough that starting fresh
for the next task saves money. Silent below the threshold, so short sessions pay nothing.

Each request re-reads the whole session. Measured (evals/long.py): 10 tasks in one session $4.97, a fresh session per
task $1.74, same 20/20 quality. This hook reads the last request's prompt size from the transcript and, past
BOOST_CLEAR_AT tokens (default 100000), shows a one-line note to you (systemMessage: not sent to the model, adds no
tokens). It repeats at most once per BOOST_CLEAR_EVERY tokens of further growth (default 50000). Never blocks."""
import json
import os
import sys
from pathlib import Path

AT = int(os.environ.get("BOOST_CLEAR_AT", 100_000))
EVERY = int(os.environ.get("BOOST_CLEAR_EVERY", 50_000))


def last_prompt_tokens(transcript: Path) -> int:
    """Prompt size of the newest API request in the transcript (input + cache read + cache write)."""
    size = transcript.stat().st_size
    with transcript.open("rb") as f:
        f.seek(max(0, size - 2_000_000))
        lines = f.read().decode("utf-8", "replace").splitlines()
    for line in reversed(lines):
        if '"usage"' not in line:
            continue
        try:
            u = json.loads(line)["message"]["usage"]
        except (ValueError, KeyError, TypeError):
            continue
        return u.get("input_tokens", 0) + u.get("cache_read_input_tokens", 0) + u.get("cache_creation_input_tokens", 0)
    return 0


def main():
    d = json.load(sys.stdin)
    t = Path(d.get("transcript_path") or "")
    if not t.is_file():
        return
    n = last_prompt_tokens(t)
    if n < AT:
        return
    mark = Path.home() / ".cache" / "claude-boost" / f"guard-{d.get('session_id', 'x')}"
    try:
        shown = int(mark.read_text())
    except (OSError, ValueError):
        shown = 0
    if shown and n < shown + EVERY:
        return
    mark.parent.mkdir(parents=True, exist_ok=True)
    mark.write_text(str(n))
    print(json.dumps({"systemMessage": f"Claude Boost: this session is ~{n // 1000}K tokens and every request re-reads it. "
                      "Starting a new task? /clear first (measured: 65% cheaper per 10 tasks, same quality). "
                      "Same task? Carry on, or /compact."}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
