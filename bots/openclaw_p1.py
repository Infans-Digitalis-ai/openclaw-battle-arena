# P1 OpenClaw bot (generated/edited by an OpenClaw agent)
# Start from openclaw_template.py

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

    # Slightly aggressive baseline.
    if cooldown == 0 and dist < 150:
        return 4

    return 1 if dx < 0 else 2
