"""Baseline bot: simple approach + mixed attacks.

A slightly smarter baseline than pure random.
"""

BOT_NAME = "baseline-tracker"


def choose_action(obs: dict) -> int:
    s = obs.get("self", {})
    o = obs.get("opp", {})
    sx = float(s.get("x", 0.0))
    ox = float(o.get("x", 0.0))
    dx = ox - sx
    dist = abs(dx)

    cooldown = int(s.get("attack_cooldown", 0) or 0)

    if dist < 140 and cooldown == 0:
        return 4  # heavy

    if dist < 240 and cooldown == 0:
        return 5  # light

    # Otherwise move toward.
    return 1 if dx < 0 else 2
