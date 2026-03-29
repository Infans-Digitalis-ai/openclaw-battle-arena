from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Optional, Dict, Any


@dataclass(frozen=True)
class Observation:
    """Structured observation passed to controllers.

    Intentionally simple (no pixels): enough to reason about distance/health/state.
    """

    tick: int
    # self
    self_x: float
    self_y: float
    self_vy: float
    self_health: float
    self_alive: bool
    self_flip: bool
    self_jump: bool
    self_attacking: bool
    self_attack_cooldown: int

    # opponent
    opp_x: float
    opp_y: float
    opp_vy: float
    opp_health: float
    opp_alive: bool
    opp_flip: bool
    opp_jump: bool
    opp_attacking: bool
    opp_attack_cooldown: int

    # arena
    screen_width: int

    def to_json(self) -> Dict[str, Any]:
        return {
            "tick": self.tick,
            "self": {
                "x": self.self_x,
                "y": self.self_y,
                "vy": self.self_vy,
                "health": self.self_health,
                "alive": self.self_alive,
                "flip": self.self_flip,
                "jump": self.self_jump,
                "attacking": self.self_attacking,
                "attack_cooldown": self.self_attack_cooldown,
            },
            "opp": {
                "x": self.opp_x,
                "y": self.opp_y,
                "vy": self.opp_vy,
                "health": self.opp_health,
                "alive": self.opp_alive,
                "flip": self.opp_flip,
                "jump": self.opp_jump,
                "attacking": self.opp_attacking,
                "attack_cooldown": self.opp_attack_cooldown,
            },
            "arena": {"screen_width": self.screen_width},
        }


class Controller(Protocol):
    name: str

    def act(self, obs: Observation) -> int:
        """Return an action id.

        Action ids are defined by Fighter.ACTIONS (includes jump-left/jump-right).
        """


class NullController:
    name = "null"

    def act(self, obs: Observation) -> int:
        return 0  # noop
