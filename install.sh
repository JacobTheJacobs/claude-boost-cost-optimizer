#!/usr/bin/env bash
# Claude Boost installer: copies the reader agent and the lean skill into ~/.claude, and prints the hook settings to
# add yourself (it never edits your settings.json). Re-run to update. Nothing here runs on install.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p ~/.claude/agents ~/.claude/skills/lean
cp "$HERE/agents/reader.md" ~/.claude/agents/reader.md
cp "$HERE/skills/lean/SKILL.md" ~/.claude/skills/lean/SKILL.md
echo "installed: ~/.claude/agents/reader.md, ~/.claude/skills/lean/SKILL.md"
cat <<EOF

Optional hooks: merge into ~/.claude/settings.json under "hooks", and set BOOST_DAY_USD in "env" for the cap:

  "env": { "BOOST_DAY_USD": "10" },
  "hooks": {
    "UserPromptSubmit": [{ "hooks": [{ "type": "command", "command": "python3 $HERE/hooks/budget.py" }] }],
    "PreToolUse": [{ "matcher": "Edit|Write|MultiEdit",
                     "hooks": [{ "type": "command", "command": "python3 $HERE/hooks/cache_guard.py" }] }]
  }

Report: python3 $HERE/tools/boost.py --days 7
EOF
