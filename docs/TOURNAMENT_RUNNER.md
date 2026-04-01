# Tournament Runner / Leaderboard Aggregation

This project includes a lightweight artifact aggregator:

- Script: `tournament_runner.py`
- Input: per-match artifacts written under `logs/matches/<match_id>/`
  - `meta.json`
  - `result.json`
- Output: a single leaderboard JSON.

## Usage

Aggregate all match results under `logs/matches/`:

```bash
python tournament_runner.py --results-glob "logs/matches/*/result.json" --out leaderboard.json
```

## Leaderboard schema

Current schema:

- `schema`: `openclaw-battle.tournament.leaderboard.v2`

Shape:

```json
{
  "schema": "openclaw-battle.tournament.leaderboard.v2",
  "generated_at": "2026-04-01T12:00:00Z",
  "matches": 12,
  "players": {
    "script-mybot": {
      "wins": 7,
      "losses": 5,
      "ties": 0,
      "stats": {
        "rounds": 36,
        "damage_dealt": 420,
        "damage_taken": 390,
        "hits": 55,
        "hits_taken": 51,
        "avg_distance": 123.4
      }
    }
  }
}
```

### Player keys (controller identity)

Players are keyed by controller identity derived from each match's `meta.json`:

- `controllers.p1.kind` + optional `controllers.p1.name`
- `controllers.p2.kind` + optional `controllers.p2.name`

Examples:
- `{kind: "script", name: "mybot"}` → `script-mybot`
- `{kind: "heuristic", name: ""}` → `heuristic`

### Optional stats aggregation

If a match `result.json` contains per-round stats at:

- `rounds[*].stats`

…then the leaderboard aggregates these across rounds:

- `rounds`: count of rounds that included stats
- `damage_dealt` / `damage_taken`
  - Uses `p1_damage` and `p2_damage` from the per-round stats (damage dealt by each player)
- `hits` / `hits_taken`
  - Uses `p1_hits` and `p2_hits`
- `avg_distance`
  - Mean of `avg_distance` values over rounds where it exists

If **no** rounds include stats for a player, `stats` is `null`.

## Notes / non-goals

- This tool is intentionally **non-strategy** and does not require replay logs.
- It does not run matches; it only aggregates already-written artifacts.
