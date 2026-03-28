"""Random baseline bot.

Useful for smoke-testing the controller interface.
"""

import random

BOT_NAME = "random"


def choose_action(obs: dict) -> int:
    # action ids: 0 noop, 1 left, 2 right, 3 jump, 4 heavy, 5 light
    # Slightly bias toward movement so it doesn't look frozen.
    return random.choices([0, 1, 2, 3, 4, 5], weights=[1, 4, 4, 1, 2, 2])[0]
