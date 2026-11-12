#!/usr/bin/env python3
"""Warn before an edit that re-writes the whole prompt cache (PreToolUse hook, matcher Edit|Write|MultiEdit).

CLAUDE.md files and Claude Code settings sit at the start of every request. Editing one mid-session changes that
prefix, so the next request writes the full context to cache again instead of reading it (Anthropic measured a
system-prompt edit at 25-50x the cost of the same text sent as a message). It only warns; the edit goes ahead."""
import json
import sys
from pathlib import Path

WATCH = ("CLAUDE.md", "CLAUDE.local.md", "AGENTS.md", "settings.json", "settings.local.json")


def main():
    d = json.load(sys.stdin)
    f = (d.get("tool_input") or {}).get("file_path") or ""
    if Path(f).name in WATCH:
        print(json.dumps({"systemMessage": f"Claude Boost: editing {Path(f).name} changes the cached prompt start; the next request re-writes the whole context to cache. If it can wait, make it between sessions."}))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
