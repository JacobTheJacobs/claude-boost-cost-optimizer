---
name: lean
description: Lean coding - smallest working change, least code, short answers. Use when asked to keep it lean or cheap.
---

# Lean

Loaded only when called, so it costs nothing on turns that do not need it.

## Before writing code

1. Is there already code that does this? Grep first; reuse it.
2. Can the standard library or an installed dependency do it? Use that.
3. What is the smallest change that passes? Write that, nothing more.
4. No abstraction, option, config or helper nobody asked for.
5. Deleting beats adding. Fixing the caller beats a new wrapper.
6. Bug fix: find every caller before you edit; fix the cause, not the symptom.

Stop at the first step that solves it.

## Answers

- Lead with the result. One line when one line will do.
- No recap of what you did, no restated question, no options nobody asked for.
- Code, commands, paths and errors stay exact and complete.

## Keep the cache warm

- Do not edit CLAUDE.md, settings or the effort level mid-session; each edit re-writes the whole cached prompt.
- Hand bulky reading (logs, many files, docs) to the `reader` agent; its tokens never enter this context.
