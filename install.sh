#!/usr/bin/env bash
# Claude Boost installer. Default: nothing that adds tokens to your requests (short tasks cost exactly the same).
#   ./install.sh            the lean skill (loads only when called) + prints the long-session guard hook to add
#   ./install.sh --reader   also the Haiku reader agent (adds ~550 tokens to every request; pays off on bulky lookups)
# It never edits your settings.json; it prints the block to merge. Nothing runs on install.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
mkdir -p ~/.claude/skills/lean
cp "$HERE/skills/lean/SKILL.md" ~/.claude/skills/lean/SKILL.md
echo "installed: ~/.claude/skills/lean/SKILL.md"
if [[ "${1:-}" == "--reader" ]]; then
  mkdir -p ~/.claude/agents
  cp "$HERE/agents/reader.md" ~/.claude/agents/reader.md
  echo "installed: ~/.claude/agents/reader.md"
fi
cat <<EOF

Add the long-session guard to ~/.claude/settings.json under "hooks" (silent until a session passes 100K tokens):

  "hooks": {
    "UserPromptSubmit": [{ "hooks": [{ "type": "command", "command": "python3 $HERE/hooks/session_guard.py" }] }]
  }

Optional extras, same place: hooks/cache_guard.py (PreToolUse, matcher "Edit|Write|MultiEdit") warns before an edit that
re-writes the prompt cache; hooks/budget.py (UserPromptSubmit, env BOOST_DAY_USD) is a daily dollar cap.

Report: python3 $HERE/tools/boost.py --days 7
EOF
