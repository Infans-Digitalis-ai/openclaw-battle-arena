# Contributing to OpenClaw Battle Arena

Thanks for contributing.

## What we want

- New controllers (heuristics, RL, search, LLM-driven)
- Protocol improvements that preserve backwards compatibility
- Tournament tooling + match artifacts
- Better observations/rewards (with documentation)

## Ground rules

- Keep the **host authoritative**. Controllers should not reach into the simulation.
- Add fields to `obs` in an **additive** way. Don’t break existing bots casually.
- If you add a controller, document:
  - what observation fields it relies on
  - failure modes (stalling, corner loops, etc.)

## Dev setup

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python main.py
```

## Pull requests

- Prefer small PRs with clear scope
- Include screenshots or short notes if behavior changes
