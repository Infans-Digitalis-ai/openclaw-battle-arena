"""OpenClaw P1 bot (Warrior) — Entertaining competitive controller (v2).

Style: pressure fighter.
- Never idles in clinch/neutral; uses step-back or jump to break contact.
- Deterministic anti-pin jump if too-close persists.

Action ids: 0 noop, 1 left, 2 right, 3 jump, 4 heavy, 5 light, 6 jump-left, 7 jump-right
"""

from __future__ import annotations

from typing import Any, Dict

BOT_NAME = "p1_pressure_v2_no_idle"

W = 80.0

_too_close_streak = 0


def choose_action(obs: Dict[str, Any]) -> int:
    global _too_close_streak

    tick = int(obs.get("tick", 0) or 0)
    s = obs.get("self", {}) or {}
    o = obs.get("opp", {}) or {}

    sx = float(s.get("x", 0.0) or 0.0)
    ox = float(o.get("x", 0.0) or 0.0)
    dx = (ox + W * 0.5) - (sx + W * 0.5)
    dist = abs(dx)

    cd = int(s.get("attack_cooldown", 0) or 0)
    opp_attacking = bool(o.get("attacking", False))

    toward = 2 if dx > 0 else 1
    away = 1 if dx > 0 else 2

    if dist < 0.75 * W:
        _too_close_streak += 1
    else:
        _too_close_streak = 0

    if _too_close_streak >= 18:
        _too_close_streak = 0
        return 6 if dx < 0 else 7

    if opp_attacking and dist < 1.9 * W:
        return 3 if (tick % 10 == 0) else away

    if dist < 0.75 * W:
        # Use directed jump away sometimes to avoid getting pinned.
        return away if (tick % 4 != 0) else (6 if dx < 0 else 7)

    if cd == 0:
        if dist <= 2.0 * W:
            return 4 if (tick % 6 == 0) else 5
        if dist <= 3.0 * W:
            return 4

    if 2.8 * W < dist < 5.2 * W and (tick % 45 == 0):
        # Directed jump-in
        return 7 if dx > 0 else 6

    return toward
