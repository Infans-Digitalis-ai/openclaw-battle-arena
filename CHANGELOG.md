# Changelog

## Unreleased

### Added
- Match artifacts writer (`meta.json`, `result.json`, optional `events.jsonl`) under `logs/matches/<match_id>/`.
- `result.json` per-round summary stats (when available) under `rounds[*].stats`:
  - `p1_damage`, `p2_damage`, `p1_hits`, `p2_hits`, `avg_distance`
- `tournament_runner.py` leaderboard aggregation:
  - Players keyed by controller identity derived from `meta.json` (`kind-name`).
  - Leaderboard schema v2: includes optional aggregated per-round stats.
- Docs: `docs/ARTIFACTS.md` (artifact spec) and `docs/TOURNAMENT_RUNNER.md` (leaderboard schema).

### Changed
- `events.jsonl` hit event type is canonicalized to `type: "hit"` and includes best-effort `dmg`.

### Tests
- Added unit tests for artifact writer and tournament runner.
- Added a minimal artifacts→leaderboard pipeline unittest.
