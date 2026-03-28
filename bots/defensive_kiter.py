"""Defensive bot: tries to maintain distance and poke.

- Backs up when opponent is close or attacking.
- Uses light/heavy depending on distance.
- Jumps occasionally to break corner pressure.
"""

BOT_NAME = "defensive-kiter"


def choose_action(obs: dict) -> int:
    tick = int(obs.get("tick", 0) or 0)
    s = obs.get("self", {})
    o = obs.get("opp", {})

    sx = float(s.get("x", 0.0))
    ox = float(o.get("x", 0.0))
    dx = ox - sx
    dist = abs(dx)

    cooldown = int(s.get("attack_cooldown", 0) or 0)
    opp_attacking = bool(o.get("attacking", False))
    in_jump = bool(s.get("jump", False))

    # If cornered (near edges), jump sometimes.
    if not in_jump and (sx < 60 or sx > 900) and tick % 30 == 0:
        return 3

    # If opponent is close or attacking, create space.
    if opp_attacking and dist < 200:
        return 1 if dx > 0 else 2  # move away

    if dist < 170:
        # If we can attack, use heavy once; otherwise retreat.
        if cooldown == 0:
            return 4
        return 1 if dx > 0 else 2

    # Mid range: poke with light when available.
    if dist < 260 and cooldown == 0:
        return 5

    # Otherwise, drift away slightly to keep spacing.
    return 1 if dx > 0 else 2
