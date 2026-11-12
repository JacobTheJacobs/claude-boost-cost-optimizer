# Claude Boost: Claude Code cost optimizer

**Long Claude Code sessions cost 65% less, with the same quality. Free, local, and it adds zero tokens to your requests.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776ab?logo=python&logoColor=white)](tools/boost.py) [![Dependencies: none](https://img.shields.io/badge/dependencies-none-brightgreen)](#install) [![Runs locally](https://img.shields.io/badge/runs-100%25%20local-success)](#privacy) [![Claude Code](https://img.shields.io/badge/Claude%20Code-hooks%20%7C%20skills-d97757)](#whats-in-it) [![GitHub stars](https://img.shields.io/github/stars/JacobTheJacobs/claude-boost-cost-optimizer?style=flat&color=yellow)](https://github.com/JacobTheJacobs/claude-boost-cost-optimizer)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/hero-dark.svg">
  <img src="docs/hero-light.svg" alt="Claude Boost: cost of one 10-task Claude Code session on Opus 5.5. Plain $4.97, with Claude Boost $1.74, 65% less, 20/20 tasks passed in both.">
</picture>

## Result

| 10 tasks in one session, Opus 5.5 | Tasks passed | Cost per session |
|---|:-:|--:|
| Plain Claude Code | 20/20 | $4.97 |
| **With Claude Boost** | **20/20** | **$1.74 (-65%)** |

40 graded tasks, 2026-11-12. Details in [Eval](#eval).

## Why it works

Every request re-sends the whole session. By task 10 of a long session, each request re-reads ~175K tokens of old history, and that re-reading is most of the bill, not the code written. Starting fresh per task keeps each request near Claude Code's ~16K-token baseline.

So Boost watches the session size and tells you when a fresh start pays off. On short sessions it stays silent and costs nothing.

## Eval

Same 10 tasks, in order, on a test repo (a Python package, 12 modules, a 20,000-line log): a bug fix, a new function, then 8 lookups and counts over the code and the log. Each answer is checked by a script (`evals/check.py`). Claude Code 2.1.322, Opus 5.5, 2 sessions per setup.

- **Plain:** one continuous session, every task resumes the last.
- **Boost:** a fresh session per task (what `/clear` does) + the Haiku `reader` agent.

Average cost of each task:

| # | Task | Plain | Boost | Passed (plain / Boost) |
|--:|---|--:|--:|:-:|
| 1 | bug fix | $0.18 | $0.18 | 2/2 · 2/2 |
| 2 | add a function | $0.23 | $0.16 | 2/2 · 2/2 |
| 3 | find a code location | $0.31 | $0.17 | 2/2 · 2/2 |
| 4 | count log errors | $0.40 | $0.17 | 2/2 · 2/2 |
| 5 | count functions in 12 files | $0.52 | $0.22 | 2/2 · 2/2 |
| 6 | error breakdown as JSON | $0.56 | $0.15 | 2/2 · 2/2 |
| 7 | count warnings | $0.61 | $0.17 | 2/2 · 2/2 |
| 8 | count functions in a file | $0.67 | $0.16 | 2/2 · 2/2 |
| 9 | find a definition | $0.72 | $0.16 | 2/2 · 2/2 |
| 10 | count one error type | $0.77 | $0.19 | 2/2 · 2/2 |
| | **Total** | **$4.97** | **$1.74** | **20/20 · 20/20** |

Plain gets more expensive with every task because it re-reads everything before it; Boost stays flat. The same small task costs 4x more at step 10 of a long session than in a fresh one.

Reproduce (spends real tokens, about $13 at list price):

```bash
python3 evals/long.py --reps 2      # results in evals/long-results.jsonl
```

## Install

```bash
git clone https://github.com/JacobTheJacobs/claude-boost-cost-optimizer.git claude-boost
cd claude-boost && ./install.sh
```

Then add the hook it prints to `~/.claude/settings.json`:

```json
"hooks": {
  "UserPromptSubmit": [{ "hooks": [{ "type": "command", "command": "python3 /path/to/claude-boost/hooks/session_guard.py" }] }]
}
```

## What's in it

| Part | What it does | Tokens added per request |
|---|---|---|
| `hooks/session_guard.py` | Past 100K tokens of context (`BOOST_CLEAR_AT`), shows you: "new task? `/clear` first". Silent below that. | 0 |
| `tools/boost.py` | Shows where your money went: cache reads vs writes vs output, per model, project, session. | 0 |
| `skills/lean/` | Smallest-change checklist and short answers, loaded only when called. | 0 until called |
| `agents/reader.md` (`./install.sh --reader`) | Haiku 5.5 helper for bulky reads (many files, big logs). | ~550 |
| `hooks/cache_guard.py` (optional) | Warns before a mid-session CLAUDE.md or settings edit, which re-writes the whole cache. | 0 |
| `hooks/budget.py` (optional) | Daily dollar cap via `BOOST_DAY_USD`. Off unless set. | 0 |

## Habits that save the most

1. **`/clear` between unrelated tasks.** The measured 65%.
2. **`/compact` early** when you stay on one task. Long contexts are re-read on every request.
3. **Don't edit CLAUDE.md, settings, model or effort mid-session.** Each change re-writes the whole cached prompt; Anthropic measured 20-50x the cost of the same text sent as a message.
4. **Ask for short answers.** Output costs 5x input.
5. **Run `python3 tools/boost.py --days 7` weekly.** If cache reads dominate, your sessions are too long.

Sources: Anthropic's [cost guide](https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence) and [cookbook](https://platform.claude.com/cookbook/cost-optimization-cost-optimization).

## FAQ

**Why is my Claude Code bill high when I write little code?** Each request re-reads the whole context. A 300K-token session re-read 50 times is 15M tokens.

**Does it help short tasks?** No, and it doesn't cost them anything either. A short task has no long context to cut.

**Can I use Haiku for subagents?** Yes, with a named agent file (`model: haiku`) like `agents/reader.md`. `fork` subagents always use your main model.

## Privacy

Everything runs on your machine. No network calls, no telemetry. `boost.py` reads `~/.claude/projects`; the hooks read stdin and print one line.

## License

MIT.
