from __future__ import annotations

from typing import Optional

from .base import Controller, NullController
from .heuristic import HeuristicController
from .ws_server import BattleAgentsWSServer
from .remote_ws import RemoteWSController
from .script_file import ScriptFileController


def make_controller(
    kind: str,
    *,
    player: int,
    screen_width: int,
    ws_server: Optional[BattleAgentsWSServer] = None,
    script_path: Optional[str] = None,
    script_timeout_ms: int = 8,
) -> Controller:
    kind = (kind or "").strip().lower()

    if kind in ("null", "noop", "none", ""):
        return NullController()

    if kind in ("heuristic", "rule", "rules"):
        return HeuristicController()

    if kind in ("remote", "ws", "remote-ws", "websocket"):
        if ws_server is None:
            raise ValueError("ws_server is required for remote controller")
        return RemoteWSController(server=ws_server, player=player)

    if kind in ("script", "file", "script-file"):
        if not script_path:
            raise ValueError("script_path is required for script controller")
        return ScriptFileController(script_path=script_path, act_timeout_ms=script_timeout_ms)

    if kind in ("dqn", "torch"):
        from .dqn import DQNController

        return DQNController(screen_width=screen_width)

    raise ValueError(f"Unknown controller kind: {kind}")
