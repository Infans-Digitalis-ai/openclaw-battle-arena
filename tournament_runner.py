"""tournament_runner.py

Tournament runner/aggregator stub for OpenClaw Battle Arena.

Goal: take many per-match `result.json` artifacts (and their sibling `meta.json`) and aggregate into a simple leaderboard.

This does NOT run matches itself (yet). It is intentionally lightweight so a tournament host can:
1) run matches via `main.py` (or another runner) that writes `logs/matches/<match_id>/result.json`
2) run this script to build a scoreboard.

Example:
  python tournament_runner.py --results-glob "logs/matches/*/result.json" --out leaderboard.json

Output schema (v2):
{
  "schema": "openclaw-battle.tournament.leaderboard.v2",
  "generated_at": "...Z",
  "matches": 12,
  "players": {
     "script-a": {
       "wins": 7, "losses": 5, "ties": 0,
       "stats": {"rounds": 36, "damage_dealt": 420, "damage_taken": 390, "hits": 55, "hits_taken": 51, "avg_distance": 123.4}
     },
     "script-b": {
       "wins": 5, "losses": 7, "ties": 0,
       "stats": {"rounds": 36, "damage_dealt": 390, "damage_taken": 420, "hits": 51, "hits_taken": 55, "avg_distance": 123.4}
     }
  }
}

Notes:
- This is non-strategy and only uses match outcomes + optional per-round summary stats from `result.json`.
- For multi-bot tournaments, we key players by controller identity derived from each match's meta.json.
"""

from __future__ import annotations

import argparse
import glob
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class StatsAgg:
    rounds: int = 0
    damage_dealt: int = 0
    damage_taken: int = 0
    hits: int = 0
    hits_taken: int = 0
    _dist_sum: float = 0.0
    _dist_n: int = 0

    def add_distance(self, v: float | None) -> None:
        if v is None:
            return
        self._dist_sum += float(v)
        self._dist_n += 1

    @property
    def avg_distance(self) -> float | None:
        if self._dist_n <= 0:
            return None
        return self._dist_sum / float(self._dist_n)


@dataclass
class PlayerAgg:
    wins: int = 0
    losses: int = 0
    ties: int = 0
    stats: StatsAgg = field(default_factory=StatsAgg)


def _load_json(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _controller_id(meta_controller: Dict[str, Any]) -> str:
    """Derive a stable-ish id from meta.json controller info."""
    kind = str(meta_controller.get("kind", "controller") or "controller").strip().lower()
    name = str(meta_controller.get("name", "") or "").strip().lower()
    if name and name != kind:
        return f"{kind}-{name}"
    return kind


def aggregate_results(result_paths: List[str]) -> Dict[str, Any]:
    # players keyed by controller identity (from meta.json)
    players: Dict[str, PlayerAgg] = {}

    for result_path in result_paths:
        res = _load_json(result_path)
        meta_path = result_path.replace("/result.json", "/meta.json")
        meta = _load_json(meta_path)

        p1_id = _controller_id((meta.get("controllers") or {}).get("p1") or {})
        p2_id = _controller_id((meta.get("controllers") or {}).get("p2") or {})

        players.setdefault(p1_id, PlayerAgg())
        players.setdefault(p2_id, PlayerAgg())

        # Match-level W/L/T
        winner = res.get("winner")
        if winner == 1:
            players[p1_id].wins += 1
            players[p2_id].losses += 1
        elif winner == 2:
            players[p2_id].wins += 1
            players[p1_id].losses += 1
        else:
            players[p1_id].ties += 1
            players[p2_id].ties += 1

        # Optional per-round stats aggregation
        for rnd in (res.get("rounds") or []):
            st = (rnd or {}).get("stats") or None
            if not st:
                continue

            players[p1_id].stats.rounds += 1
            players[p2_id].stats.rounds += 1

            # In result.json, p1_damage is damage dealt by p1, and p2_damage by p2.
            p1_dmg = st.get("p1_damage")
            p2_dmg = st.get("p2_damage")
            if p1_dmg is not None:
                players[p1_id].stats.damage_dealt += int(p1_dmg)
                players[p2_id].stats.damage_taken += int(p1_dmg)
            if p2_dmg is not None:
                players[p2_id].stats.damage_dealt += int(p2_dmg)
                players[p1_id].stats.damage_taken += int(p2_dmg)

            p1_hits = st.get("p1_hits")
            p2_hits = st.get("p2_hits")
            if p1_hits is not None:
                players[p1_id].stats.hits += int(p1_hits)
                players[p2_id].stats.hits_taken += int(p1_hits)
            if p2_hits is not None:
                players[p2_id].stats.hits += int(p2_hits)
                players[p1_id].stats.hits_taken += int(p2_hits)

            players[p1_id].stats.add_distance(st.get("avg_distance"))
            players[p2_id].stats.add_distance(st.get("avg_distance"))

    def _player_payload(pa: PlayerAgg) -> Dict[str, Any]:
        avg_dist = pa.stats.avg_distance
        return {
            "wins": pa.wins,
            "losses": pa.losses,
            "ties": pa.ties,
            "stats": {
                "rounds": pa.stats.rounds,
                "damage_dealt": pa.stats.damage_dealt,
                "damage_taken": pa.stats.damage_taken,
                "hits": pa.stats.hits,
                "hits_taken": pa.stats.hits_taken,
                "avg_distance": avg_dist,
            }
            if pa.stats.rounds > 0
            else None,
        }

    return {
        "schema": "openclaw-battle.tournament.leaderboard.v2",
        "generated_at": _utc_now_iso(),
        "matches": len(result_paths),
        "players": {k: _player_payload(v) for k, v in sorted(players.items())},
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Aggregate OpenClaw Battle Arena result.json artifacts into a leaderboard")
    ap.add_argument(
        "--results-glob",
        type=str,
        default="logs/matches/*/result.json",
        help="Glob to match result.json files (default: logs/matches/*/result.json)",
    )
    ap.add_argument("--out", type=str, default=None, help="Write leaderboard JSON to this path")
    args = ap.parse_args()

    paths = sorted(glob.glob(args.results_glob))
    board = aggregate_results(paths)

    print(json.dumps(board, indent=2))

    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(board, f, indent=2)


if __name__ == "__main__":
    main()
