# P2 OpenClaw bot (generated/edited by an OpenClaw agent)
# Start from openclaw_template.py

from __future__ import annotations

from typing import Any, Dict


def decide(obs: Dict[str, Any]) -> int:
    # Defensive-ish baseline.
    s = obs.get("self", {})
    o = obs.get("opp", {})

    sx = float(s.get("x", 0.0))
    ox = float(o.get("x", 0.0))
    dx = ox - sx
    dist = abs(dx)

    cooldown = int(s.get("attack_cooldown", 0) or 0)
    opp_attacking = bool(o.get("attacking", False))

    if opp_attacking and dist < 170:
        # back up
        return 1 if dx > 0 else 2

    if cooldown == 0 and dist < 130:
        return 5  # light attack

    return 1 if dx < 0 else 2
