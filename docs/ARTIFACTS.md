# Match Artifacts (spec)

This document defines **non-strategy match artifacts** that the host/tournament runner can write so results are auditable and reproducible.

Design goals:
- **Deterministic & comparable** across machines (prefer tick-count timing).
- **No strategy leakage** beyond what already occurs during a match.
- **Small by default**, with optional heavier artifacts (per-tick logs) behind flags.

## Artifact layout

Recommended per-run layout:

```
logs/
  matches/
    <match_id>/
      meta.json
      result.json
      events.jsonl        # optional
      obs_p1.jsonl        # optional
      obs_p2.jsonl        # optional
```

- `match_id` should be unique and filesystem-safe.
- For local ad-hoc runs, `match_id` can be a timestamp.

## `meta.json` (run metadata)

Minimal example:

```json
{
  "schema": "openclaw-battle.artifacts.meta.v0",
  "match_id": "2026-03-31T06-46-00Z--p1-script--p2-script",
  "created_at": "2026-03-31T06:46:00Z",
  "mode": "MATCH",
  "best_of": 3,
  "fixed_tick_match": true,
  "fps": 60,
  "controllers": {
    "p1": {"kind": "script", "name": "my-bot", "script_path": "bots/my_bot.py"},
    "p2": {"kind": "script", "name": "other-bot", "script_path": "bots/other_bot.py"}
  },
  "arena": {"screen_width": 1000, "screen_height": 600}
}
```

Notes:
- `schema` is required and versioned.
- `controllers.*.script_path` is optional (and may be omitted for privacy in tournament runs).

## `result.json` (high-level outcome)

Minimal example:

```json
{
  "schema": "openclaw-battle.artifacts.result.v0",
  "match_id": "...",
  "winner": 1,
  "score": {"p1": 2, "p2": 1},
  "rounds": [
    {"round": 1, "winner": 1, "ticks": 3420, "end_reason": "ko"},
    {"round": 2, "winner": 2, "ticks": 5400, "end_reason": "timeout"},
    {"round": 3, "winner": 1, "ticks": 4100, "end_reason": "ko"}
  ]
}
```

End reasons (suggested):
- `ko`
- `timeout`
- `disconnect` (remote controller)
- `forfeit`

## `events.jsonl` (optional)

JSON Lines stream of notable events (recommended instead of per-tick dumps):

```jsonl
{"t":120,"type":"hit","by":1,"dmg":10,"p1":{"x":210,"y":310,"health":90},"p2":{"x":700,"y":310,"health":100}}
{"t":121,"type":"hit","by":1,"dmg":10,"p1":{"x":220,"y":310,"health":90},"p2":{"x":690,"y":310,"health":90}}
{"t":5400,"type":"round_end","reason":"timeout","winner":2}
```

Rules:
- `t` is **tick** (int) within the round (or absolute match tick if you prefer; just document it).
- `by` is best-effort (may be null).
- `dmg` is best-effort (0 when unknown/ambiguous).
- `p1`/`p2` capture a minimal, non-strategy snapshot useful for replay/debug.

## Observations logs (optional)

If enabled, `obs_p1.jsonl` / `obs_p2.jsonl` can store the exact observation objects sent to controllers.

This is useful for:
- debugging controller failures
- replay analysis / visualization

It is not required for a tournament scoreboard.

---

If you add/extend artifacts, bump the schema string (e.g., `...v1`).
