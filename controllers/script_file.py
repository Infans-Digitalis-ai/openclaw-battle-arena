from __future__ import annotations

import importlib.util
import os
import time
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from types import ModuleType
from typing import Any, Callable

from .base import Observation

# Keep controllers import-light: do NOT import pygame-dependent modules here.
_VALID_ACTIONS = {0, 1, 2, 3, 4, 5, 6, 7}


@dataclass
class ScriptSpec:
    path: str


def _load_module_from_path(path: str) -> ModuleType:
    path = os.path.abspath(path)
    name = f"battle_bot_{abs(hash(path))}"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Could not load bot script: {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[attr-defined]
    return mod


class ScriptFileController:
    """Controller that calls a user-provided Python script.

    The script must define:
      - choose_action(obs) -> int

    Where obs is a JSON-serializable dict (see Observation.to_json()).

    Fairness guardrails:
      - one action per tick (host-authoritative loop)
      - per-tick time budget: if the script doesn't respond in time, return NOOP
        (and mark the controller timed-out for the remainder of the match)
      - clamp invalid actions to NOOP
      - rate limit / anti-backlog: never queue multiple in-flight calls; if a call
        is already running, return NOOP for this tick.

    Note: Python threads can't be force-killed safely. If a script times out and
    then blocks forever, we treat it as "dead" and keep returning NOOP.
    """

    def __init__(self, *, script_path: str, act_timeout_ms: int = 8):
        self._script_path = script_path
        self._mod = _load_module_from_path(script_path)
        fn = getattr(self._mod, "choose_action", None)
        if not callable(fn):
            raise ValueError(f"Bot script {script_path} must define choose_action(obs) -> int")
        self._choose: Callable[[dict[str, Any]], int] = fn  # type: ignore[assignment]
        self.name = getattr(self._mod, "BOT_NAME", os.path.basename(script_path))

        self._act_timeout_s = max(0.0, float(act_timeout_ms) / 1000.0)
        self._timed_out = False
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="script_bot")
        self._inflight: Future | None = None

        # Per-tick cache: if act() is accidentally called multiple times for the same
        # tick, return the same action (or NOOP) and do NOT re-run user code.
        self._last_tick: int | None = None
        self._last_action: int = 0

        self._warned_timeout = False
        self._warned_error = False

    def _clamp_action(self, a: int) -> int:
        return a if a in _VALID_ACTIONS else 0

    def act(self, obs: Observation) -> int:
        # If we already decided the controller is "dead" for this match, fail closed.
        if self._timed_out:
            return 0

        # Per-tick rate limit: never run user code twice for the same tick.
        if self._last_tick == obs.tick:
            return self._last_action

        # Anti-backlog: if a previous tick's call is still running, don't queue more.
        if self._inflight is not None and not self._inflight.done():
            self._last_tick = obs.tick
            self._last_action = 0
            return 0

        # Pass dict to keep the script interface stable and language-agnostic.
        payload = obs.to_json()

        # No budget => just call directly.
        if self._act_timeout_s <= 0:
            try:
                a = self._clamp_action(int(self._choose(payload)))
            except Exception:
                a = 0
            self._last_tick = obs.tick
            self._last_action = a
            return a

        self._inflight = self._executor.submit(self._choose, payload)
        try:
            a = self._inflight.result(timeout=self._act_timeout_s)
            a2 = self._clamp_action(int(a))
            self._last_tick = obs.tick
            self._last_action = a2
            return a2
        except FutureTimeoutError:
            # Best-effort cancel; if already running, this won't stop it.
            try:
                self._inflight.cancel()
            except Exception:
                pass

            self._timed_out = True
            self._last_tick = obs.tick
            self._last_action = 0

            if not self._warned_timeout:
                self._warned_timeout = True
                print(
                    f"[script] {self.name} timed out after {int(self._act_timeout_s*1000)}ms; "
                    "returning NOOP for the rest of the match"
                )
            return 0
        except Exception as e:
            # Fail closed: invalid scripts shouldn't crash the host.
            self._last_tick = obs.tick
            self._last_action = 0
            if not self._warned_error:
                self._warned_error = True
                print(f"[script] {self.name} error in choose_action: {e}; returning NOOP")
            return 0
