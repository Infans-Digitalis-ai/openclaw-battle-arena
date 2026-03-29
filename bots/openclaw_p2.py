"""OpenClaw P2 bot (Wizard) — Entertaining competitive controller.

Style: kiter/counterpuncher.
- Maintain spacing, punish approach.
- Uses jumps to disengage and reset spacing.
- Includes corner-escape sequence to avoid pogoing in place at the wall.

Action ids: 0 noop, 1 left, 2 right, 3 jump, 4 heavy, 5 light, 6 jump-left, 7 jump-right
"""

from __future__ import annotations

from typing import Any, Dict

BOT_NAME = "p2_kite_corner_escape"

W = 80.0

_escape_until_tick = -1
_escape_phase = 0


def choose_action(obs: Dict[str, Any]) -> int:
    global _escape_until_tick, _escape_phase

    tick = int(obs.get("tick", 0) or 0)
    s = obs.get("self", {}) or {}
    o = obs.get("opp", {}) or {}
    arena = obs.get("arena", {}) or {}

    sx = float(s.get("x", 0.0) or 0.0)
    ox = float(o.get("x", 0.0) or 0.0)
    dx = (ox + W * 0.5) - (sx + W * 0.5)
    dist = abs(dx)

    cd = int(s.get("attack_cooldown", 0) or 0)
    self_attacking = bool(s.get("attacking", False))
    opp_attacking = bool(o.get("attacking", False))

    screen_w = float(arena.get("screen_width", 1000) or 1000)

    toward = 2 if dx > 0 else 1
    away = 1 if dx > 0 else 2

    if self_attacking:
        return 0

    margin = 40.0
    cornered = (sx <= margin) or (sx >= (screen_w - W - margin))

    if tick <= _escape_until_tick:
        if _escape_phase == 1:
            _escape_phase = 2
            return toward
        return toward
    else:
        _escape_until_tick = -1
        _escape_phase = 0

    if cornered and dist < 3.0 * W:
        _escape_until_tick = tick + 10
        _escape_phase = 1
        # Directed jump away from wall pressure is usually toward the opponent (side-switch attempt).
        return 7 if dx > 0 else 6

    if opp_attacking and dist < 2.4 * W:
        if tick % 10 == 0:
            return 6 if dx < 0 else 7
        return away

    preferred_min = 2.0 * W
    preferred_max = 3.2 * W

    if dist < preferred_min:
        if tick % 30 == 0:
            return 6 if dx < 0 else 7
        return away

    if dist > preferred_max:
        if tick % 55 == 0:
            return 6 if dx < 0 else 7
        return toward

    if cd == 0:
        return 5 if (tick % 4 != 0) else 4

    return 0 if (tick % 3 == 0) else away
