"""OpenClaw Battle Arena bot template (Option A: script controller).

Implement `decide(obs)` and return an action id:
0 noop, 1 left, 2 right, 3 jump, 4 heavy, 5 light

Observation schema (best-effort; see controllers/base.py for the canonical version):
obs = {
  "tick": int,
  "self": {"x": float, "y": float, "health": int, "attack_cooldown": int, "attacking": bool, ...},
  "opp":  {"x": float, "y": float, "health": int, "attack_cooldown": int, "attacking": bool, ...},
}

Rules:
- Must be deterministic and fast (no sleeps, no network).
- Keep pure python (stdlib only).
"""

from __future__ import annotations

from typing import Any, Dict


def decide(obs: Dict[str, Any]) -> int:
    s = obs.get("self", {})
    o = obs.get("opp", {})

    sx = float(s.get("x", 0.0))
    ox = float(o.get("x", 0.0))
    dx = ox - sx
    dist = abs(dx)

    cooldown = int(s.get("attack_cooldown", 0) or 0)

    # Simple baseline: walk toward opponent; attack when close and off cooldown.
    if cooldown == 0 and dist < 140:
        return 4  # heavy attack

    return 1 if dx < 0 else 2
