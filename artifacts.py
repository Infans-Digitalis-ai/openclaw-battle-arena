"""Match artifact helpers.

Implements a minimal writer consistent with docs/ARTIFACTS.md.

Artifacts are intended to be:
- small by default
- non-strategy (no bot internal state)
- useful for audits + tournament runners

Schema strings:
- openclaw-battle.artifacts.meta.v0
- openclaw-battle.artifacts.result.v0
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_mkdir(p: str) -> None:
    os.makedirs(p, exist_ok=True)


def _write_json(path: str, payload: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _append_jsonl(path: str, obj: dict[str, Any]) -> None:
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, separators=(",", ":"), ensure_ascii=False) + "\n")


@dataclass
class RoundResult:
    round: int
    winner: int | None
    ticks: int
    end_reason: str


@dataclass
class MatchArtifacts:
    out_dir: str
    match_id: str
    meta: dict[str, Any]

    rounds: list[RoundResult] = field(default_factory=list)
    score_p1: int = 0
    score_p2: int = 0

    # optional event stream
    events_path: str | None = None

    def event(self, evt: dict[str, Any]) -> None:
        if not self.events_path:
            return
        _append_jsonl(self.events_path, evt)

    def add_round(self, rr: RoundResult) -> None:
        self.rounds.append(rr)
        if rr.winner == 1:
            self.score_p1 += 1
        elif rr.winner == 2:
            self.score_p2 += 1

    def finalize(self) -> None:
        winner: int | None
        if self.score_p1 > self.score_p2:
            winner = 1
        elif self.score_p2 > self.score_p1:
            winner = 2
        else:
            winner = None

        payload = {
            "schema": "openclaw-battle.artifacts.result.v0",
            "match_id": self.match_id,
            "winner": winner,
            "score": {"p1": self.score_p1, "p2": self.score_p2},
            "rounds": [
                {
                    "round": r.round,
                    "winner": r.winner,
                    "ticks": r.ticks,
                    "end_reason": r.end_reason,
                }
                for r in self.rounds
            ],
        }
        _write_json(os.path.join(self.out_dir, "result.json"), payload)


def begin_match(
    *,
    base_dir: str,
    mode: str,
    best_of: int,
    fixed_tick_match: bool,
    fps: int,
    controllers: dict[str, dict[str, Any]],
    arena: dict[str, Any],
    enable_events: bool = True,
) -> MatchArtifacts:
    """Create artifact directory and write meta.json.

    Returns a MatchArtifacts handle used to add rounds and write result.json.
    """

    created_at = _utc_now_iso()
    # filesystem-safe match id
    mid = created_at.replace(":", "-") + f"--{controllers.get('p1', {}).get('kind', 'p1')}-{controllers.get('p2', {}).get('kind', 'p2')}"

    out_dir = os.path.join(base_dir, mid)
    _safe_mkdir(out_dir)

    meta = {
        "schema": "openclaw-battle.artifacts.meta.v0",
        "match_id": mid,
        "created_at": created_at,
        "mode": mode,
        "best_of": best_of,
        "fixed_tick_match": bool(fixed_tick_match),
        "fps": int(fps),
        "controllers": controllers,
        "arena": arena,
    }
    _write_json(os.path.join(out_dir, "meta.json"), meta)

    ma = MatchArtifacts(out_dir=out_dir, match_id=mid, meta=meta)
    if enable_events:
        ma.events_path = os.path.join(out_dir, "events.jsonl")
        ma.event({"t": 0, "type": "match_start", "created_at": created_at})

    return ma
