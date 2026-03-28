# OpenClaw dueling (Option A: script bots)

This arena supports **local duels** where each player is controlled by a Python script.

## The two bot files

- `bots/openclaw_p1.py` (Player 1)
- `bots/openclaw_p2.py` (Player 2)

Each file must expose:

```py
def decide(obs) -> int:
    ...
```

Action ids:
- 0 noop
- 1 left
- 2 right
- 3 jump
- 4 heavy
- 5 light

## Visual duel (desktop icon)

Double-click **OpenClaw Battle Arena**.

Current default config is in `settings.py`:

- `P1_CONTROLLER = "script"`
- `P2_CONTROLLER = "script"`
- `P1_SCRIPT_PATH = "bots/openclaw_p1.py"`
- `P2_SCRIPT_PATH = "bots/openclaw_p2.py"`

So the game will always run the **current** versions of those two bot scripts.

## Headless benchmarking (winrate + avg round time)

```bash
./scripts/run-battle-trials.sh 50 5 results.json
```

This runs `trial_runner.py` and writes a summary to stdout plus per-match details to `results.json`.

## Improvement loop (LLM-style)

1) Run trials → capture `results.json`.
2) Ask an agent to update its bot script based on the results.
3) Repeat.

Keep improvements small and measurable (e.g., change one tactic, rerun 50 matches).
