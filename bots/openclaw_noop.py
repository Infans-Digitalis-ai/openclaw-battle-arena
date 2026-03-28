"""No-op OpenClaw bot.

Used as the default when no OpenClaw agent has plugged in a script yet.
"""

from __future__ import annotations

from typing import Any, Dict

BOT_NAME = "noop"


def choose_action(obs: Dict[str, Any]) -> int:
    return 0
