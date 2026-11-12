# Claude Boost: Claude Code cost optimizer

**Cut your Claude Code bill without cutting quality. A free, local kit that shows where your tokens and dollars go, then applies the fixes Anthropic measured: a warm prompt cache, shorter context, a cheap Haiku subagent for lookups, and a daily dollar cap.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE) [![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776ab?logo=python&logoColor=white)](tools/boost.py) [![Dependencies: none](https://img.shields.io/badge/dependencies-none-brightgreen)](#install) [![Runs locally](https://img.shields.io/badge/runs-100%25%20local-success)](#privacy) [![Claude Code](https://img.shields.io/badge/Claude%20Code-agents%20%7C%20skills%20%7C%20hooks-d97757)](#what-is-in-it) [![GitHub stars](https://img.shields.io/github/stars/JacobTheJacobs/claude-boost-cost-optimizer?style=flat&color=yellow)](https://github.com/JacobTheJacobs/claude-boost-cost-optimizer)

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/hero-dark.svg">
  <img src="docs/hero-light.svg" alt="Claude Boost: a real week of one developer's Claude Code spend by token class: cache reads 64%, cache writes 22%, output 14%. Most of the bill is the context being re-read on every request.">
</picture>

**Contents:** [Why](#why) · [What is in it](#what-is-in-it) · [Install](#install) · [Eval results](#does-it-work-eval-results) · [The levers](#the-levers-in-order-with-their-source) · [Prices](#prices-used-per-1m-tokens-anthropic-pricing-page-2026-11-10) · [Plugins compared](#third-party-plugins-we-looked-at) · [FAQ](#faq) · [Privacy](#privacy)

## Why

In agent loops the bill is mostly the context being re-read, not the code being written. Every request re-sends the whole conversation. On one developer's week (the image above, from `tools/boost.py`): $542 at list price, 64% of it cache reads at an average of 299K tokens a request.

- **Measure first.** `boost.py` splits your spend by token class, model, project, session and main thread vs subagents, and names the lever that applies.
- **Keep the cache valid.** "Fewer tokens" is not "lower cost": anything that rewrites the start of the prompt turns cheap cache reads into expensive cache writes.
- **Cheap work on a cheap model.** `fork` subagents always run on your main model; the `reader` agent runs on Haiku 5.5, about 1/40 of Opus 5.5 per token.
- **A hard stop.** A daily dollar cap per machine or per project.
- **Every number has a source.** Each lever below links to Anthropic's own measurement.

## What is in it

| Part | What it does |
|---|---|
| `tools/boost.py` | Report from your local session logs: list-price dollars by token class (cache read / cache write / output / input), main thread vs subagents, model, project, top sessions, the share of input read from cache, average prompt size, and which levers apply. |
| `agents/reader.md` | A Haiku, read-only helper for lookups (find, read, list). Its tokens never enter your main context, and its answer is capped at 15 rows. |
| `skills/lean/` | Simplest-change checklist before coding, short answers, cache hygiene. Loaded only when called, so it adds nothing to turns that don't use it. |
| `hooks/budget.py` | Daily dollar cap (`BOOST_DAY_USD`), optionally per project (`BOOST_PROJECT`): warns at 80%, blocks new prompts at 100%. |
| `hooks/cache_guard.py` | Warns before an edit to CLAUDE.md / AGENTS.md / settings mid-session, which re-writes the whole cached prompt. |

## Install

```bash
git clone https://github.com/JacobTheJacobs/claude-boost-cost-optimizer.git claude-boost
cd claude-boost && ./install.sh          # copies the agent and skill; prints the hook settings to add
python3 tools/boost.py --days 7          # see where your money goes
```

Then add one line to your CLAUDE.md:

```markdown
For easy read-only work (reading files, logs or docs, searching, listing), use the `reader` agent instead of `fork`.
```

`fork` subagents always run on your main model; a model override on them is ignored. Named agents like `reader` run on the model in their file.

## Does it work? Eval results

We ran the same tasks with plain Claude Code and with Claude Code + Boost (the `reader` agent and the lean instructions), each run on a fresh copy of a small test repo, graded pass/fail by a script. Claude Code 2.1.322, Opus 5.5, 3 runs per task per arm, 36 runs, 2026-11-12. Reproduce: `python3 evals/run.py --reps 3 && python3 evals/report.py`.

| Task | Plain: pass | Plain: $/run | Boost: pass | Boost: $/run | Change |
|---|:-:|--:|:-:|--:|--:|
| bugfix | 3/3 | $0.184 | 3/3 | $0.187 | +1% |
| feature | 3/3 | $0.181 | 3/3 | $0.183 | +1% |
| helpers | 3/3 | $0.231 | 3/3 | $0.216 | -6% |
| logbreakdown | 3/3 | $0.185 | 3/3 | $0.176 | -5% |
| logcount | 3/3 | $0.214 | 3/3 | $0.206 | -4% |
| lookup | 3/3 | $0.188 | 3/3 | $0.190 | +1% |
| **all** | **18/18** | **$0.197** | **18/18** | **$0.193** | **-2%** |

Boost runs spent $0.002 in total on Haiku 5.5 (the reader agent).

**What this shows, honestly:**

- **Quality held:** 18/18 passes in both arms.
- **On short, one-shot tasks Boost saves little: about 2%, within run-to-run noise.** Each run cost about $0.19, and most of that is the fixed start-up context Claude Code writes to cache on the first request, which neither arm changes.
- **The reader agent was barely used** ($0.002 of Haiku in total): on tasks this small, Opus answers with one grep instead of delegating. The bulk-reading tasks were the ones Boost made cheaper (4-6%).
- **What this eval does not cover:** long sessions. The biggest cost we found in real use (`tools/boost.py`, image above) is a long context re-read on every request; that is fixed by habits (`/clear` per task, `/compact` early, lookups in a subagent), not by anything a 3-turn task exercises. A long-session eval is the next step.

So: use `tools/boost.py` first and act on what it shows; don't expect the agent and skill alone to cut a short task's cost.

## The levers, in order, with their source

| # | Lever | Measured | Source |
|---|---|---|---|
| 1 | **Short context.** `/clear` or a new session per task; `/compact` early. Every request re-reads it. | Compacting Haiku 5.5 at 90K instead of 150K cut cost per request 70% | [Anthropic cost guide](https://platform.claude.com/docs/en/about-claude/models/optimizing-for-cost-and-intelligence) |
| 2 | **Keep the cache valid.** No CLAUDE.md, settings, model or effort changes mid-session; stable text first, changing text last. | A system-prompt edit cost 25-50x the same text as a message; an effort change 20-40x | cost guide |
| 3 | **Bulky reads in a Haiku subagent.** | 78% cheaper on the cookbook's agent loop | [Anthropic cookbook](https://platform.claude.com/cookbook/cost-optimization-cost-optimization) |
| 4 | **Short answers.** Output costs 5x input. | One-line answer $0.49 vs six-section memo $1.40, same accuracy; shaped output 63% cheaper | cost guide, cookbook |
| 5 | **Lower effort, retry failures high.** | $0.17 vs $0.29 per task at about the same pass rate | cost guide |
| 6 | **Model per task.** Haiku for checkable high-volume work; Sonnet medium often matches Opus. | Haiku 5.5 ~1/20 of Opus 5.5 per correct answer (85% vs 91%); Sonnet medium 10/10 at ~1/3 of Opus high | cost guide, cookbook |
| 7 | **Prune stale instructions.** "Verify twice" and the like, written for older models. | Removing it made Opus 5 cheaper and more accurate | cost guide |
| 8 | **Load tools only when used.** | 502 tools deferred: $0.56 vs $1.02 per run | cost guide |
| 9 | **Batch what can wait 24 h** (API work). | 50% off | cost guide |

What did not save money in Anthropic's tests: an Opus advisor on a cheaper driver (+2.1x cost for 1.7 points), and context editing on short runs (+73%). Measure before adopting.

## Prices used (per 1M tokens, Anthropic pricing page, 2026-11-10)

| Model | Input | Output | Cache read | 5m write | 1h write |
|---|---:|---:|---:|---:|---:|
| Fable 5.2 | $8.00 | $40.00 | $0.20 | $10.00 | $16.00 |
| Opus 5.5 | $4.00 | $20.00 | $0.20 | $5.00 | $8.00 |
| Sonnet 5.5 | $2.00 | $10.00 | $0.10 | $2.50 | $4.00 |
| Haiku 5.5 (prompt <= 100K) | $0.10 | $0.50 | $0.01 | $0.125 | $0.20 |
| Haiku 5.5 (prompt > 100K, whole request) | $0.50 | $2.50 | $0.05 | $0.625 | $1.00 |

On Bedrock, Google Cloud and Foundry the `haiku` alias still means Haiku 4.5 ($1/$5); pin `ANTHROPIC_DEFAULT_HAIKU_MODEL` there.

## Third-party plugins we looked at

- **Ponytail** (simplest-solution checklist): one user saw ~50% less generated code and fewer dev/review rounds. Its checklist idea is in `skills/lean`, loaded on demand instead of every turn.
- **Caveman** (terse output): big output cuts, but its instructions ride on every turn; in a code loop that can cost more than it saves, and one benchmark found it only ~3% better than simply asking for brevity.
- **Headroom** (context compression): rewriting history broke the cache prefix and raised cache-write costs.

## FAQ

**How do I reduce Claude Code costs?** Run `python3 tools/boost.py`. If cache reads dominate, shorten sessions (`/clear` per task, `/compact` early). If cache writes are high, stop switching model, effort or CLAUDE.md mid-session. If output is high, ask for shorter answers. Move lookups to the `reader` agent.

**Why is my Claude Code bill so high when I write little code?** Each request re-reads the whole context. A 300K-token session re-read 50 times is 15M cache-read tokens, even at 5% of the input price.

**Does prompt caching make long sessions free?** No. Cache reads cost 5% of input on Opus and Sonnet 5.5; at large contexts they become the biggest line. Caching makes them cheap, not free.

**Can I use Haiku for Claude Code subagents?** Yes: set `model: haiku` in a named agent file (like `agents/reader.md`). It does not work for `fork`, which inherits the main model.

**Can I set a daily spending limit for Claude Code?** Yes: `hooks/budget.py` with `BOOST_DAY_USD=10` warns at 80% and blocks new prompts at 100%.

**Is it the same as Caveman, Ponytail or Headroom?** No. See [Third-party plugins we looked at](#third-party-plugins-we-looked-at): Claude Boost measures first and avoids per-turn instructions and history rewrites that break the cache.

## Privacy

Everything runs on your machine. `boost.py` reads `~/.claude/projects` and prints a report; no network calls, no telemetry. The hooks read stdin and print one JSON line. Dollars are computed from the price table in the script.
