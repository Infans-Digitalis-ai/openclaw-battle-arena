"""trial_runner.py

Local headless-ish match runner for Battle Arena.

Runs N matches using any local controller types (heuristic/script/dqn/null) and outputs
summary stats + optional per-match JSON/CSV.

Notes:
- Uses SDL dummy drivers to avoid opening a window or requiring audio hardware.
- Still loads sprite sheets because Fighter animation/state expects them, but no rendering is performed.

Example:
  python trial_runner.py --matches 50 --best-of 5 \
    --p1 script --p1-script bots/baseline.py \
    --p2 script --p2-script bots/random.py \
    --out results.json
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import statistics
import time
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

# Must be set before importing pygame.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from fighter import Fighter  # noqa: E402
from controllers.factory import make_controller  # noqa: E402


FPS = 60
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
ROUND_TIME_LIMIT_S = 90

# fighter setup data (kept in sync with main.py)
WARRIOR_DATA = [162, 4, [72, 56]]
WIZARD_DATA = [250, 3, [112, 107]]
WARRIOR_STEPS = [10, 8, 1, 7, 7, 3, 7]
WIZARD_STEPS = [8, 8, 1, 8, 8, 3, 7]


class DummySound:
    def play(self, *args, **kwargs):
        return None


@dataclass
class MatchResult:
    match_index: int
    best_of: int
    p1_wins: int
    p2_wins: int
    winner: int  # 1 or 2
    total_rounds: int
    total_ticks: int
    avg_round_seconds: float


def _load_sprite_sheets() -> tuple[pygame.Surface, pygame.Surface]:
    warrior = pygame.image.load("assets/images/warrior/Sprites/warrior.png").convert_alpha()
    wizard = pygame.image.load("assets/images/wizard/Sprites/wizard.png").convert_alpha()
    return warrior, wizard


def _make_fighters(warrior_sheet: pygame.Surface, wizard_sheet: pygame.Surface) -> tuple[Fighter, Fighter]:
    f1 = Fighter(
        player=1,
        x=200,
        y=310,
        flip=False,
        data=WARRIOR_DATA,
        sprite_sheet=warrior_sheet,
        animation_steps=WARRIOR_STEPS,
        attack_sound=DummySound(),
        screen_width=SCREEN_WIDTH,
    )
    f2 = Fighter(
        player=2,
        x=700,
        y=310,
        flip=True,
        data=WIZARD_DATA,
        sprite_sheet=wizard_sheet,
        animation_steps=WIZARD_STEPS,
        attack_sound=DummySound(),
        screen_width=SCREEN_WIDTH,
    )
    return f1, f2


def run_single_match(
    *,
    match_index: int,
    best_of: int,
    controller_1,
    controller_2,
    warrior_sheet: pygame.Surface,
    wizard_sheet: pygame.Surface,
    round_time_limit_s: int = ROUND_TIME_LIMIT_S,
) -> MatchResult:
    win_target = (best_of // 2) + 1

    fighter_1, fighter_2 = _make_fighters(warrior_sheet, wizard_sheet)

    p1_wins = 0
    p2_wins = 0
    total_rounds = 0
    total_ticks = 0
    round_durations_s: List[float] = []

    tick = 0

    while p1_wins < win_target and p2_wins < win_target:
        total_rounds += 1
        fighter_1.reset()
        fighter_2.reset()

        round_ticks = 0
        round_start = time.time()

        # Run until someone dies or time limit is hit.
        while True:
            tick += 1
            round_ticks += 1

            # build observations
            obs1 = fighter_1.make_observation(fighter_2, tick=tick)
            obs2 = fighter_2.make_observation(fighter_1, tick=tick)

            # controllers choose actions
            a1 = int(controller_1.act(obs1))
            a2 = int(controller_2.act(obs2))

            # step physics
            _r1, _d1 = fighter_1.step_from_action(fighter_2, action_id=a1, round_over=False)
            _r2, _d2 = fighter_2.step_from_action(fighter_1, action_id=a2, round_over=False)

            fighter_1.update()
            fighter_2.update()

            # round end conditions
            if not fighter_1.alive:
                p2_wins += 1
                break
            if not fighter_2.alive:
                p1_wins += 1
                break

            if (round_ticks / FPS) >= round_time_limit_s:
                # Time-out: decide by remaining health (tie-breaker: random)
                if fighter_1.health > fighter_2.health:
                    p1_wins += 1
                elif fighter_2.health > fighter_1.health:
                    p2_wins += 1
                else:
                    if random.random() < 0.5:
                        p1_wins += 1
                    else:
                        p2_wins += 1
                break

        total_ticks += round_ticks
        round_durations_s.append(time.time() - round_start)

    winner = 1 if p1_wins > p2_wins else 2
    avg_round_seconds = float(statistics.mean(round_durations_s)) if round_durations_s else 0.0

    return MatchResult(
        match_index=match_index,
        best_of=best_of,
        p1_wins=p1_wins,
        p2_wins=p2_wins,
        winner=winner,
        total_rounds=total_rounds,
        total_ticks=total_ticks,
        avg_round_seconds=avg_round_seconds,
    )


def main():
    ap = argparse.ArgumentParser(description="Run local headless-ish Battle Arena trials")
    ap.add_argument("--matches", type=int, default=20)
    ap.add_argument("--best-of", type=int, default=5)

    ap.add_argument("--p1", dest="p1_kind", default="heuristic")
    ap.add_argument("--p2", dest="p2_kind", default="heuristic")
    ap.add_argument("--p1-script", dest="p1_script", default=None)
    ap.add_argument("--p2-script", dest="p2_script", default=None)

    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--round-time", type=int, default=ROUND_TIME_LIMIT_S)

    ap.add_argument("--out", type=str, default=None, help="Write per-match results to .json or .csv")

    args = ap.parse_args()

    if args.matches < 1:
        raise SystemExit("--matches must be >= 1")
    if args.best_of < 1:
        raise SystemExit("--best-of must be >= 1")

    if args.seed is not None:
        random.seed(args.seed)

    pygame.init()

    # A tiny hidden surface (dummy video driver) to satisfy some pygame internals.
    pygame.display.set_mode((1, 1))

    warrior_sheet, wizard_sheet = _load_sprite_sheets()

    controller_1 = make_controller(
        args.p1_kind,
        player=1,
        screen_width=SCREEN_WIDTH,
        script_path=args.p1_script,
        script_timeout_ms=int(getattr(settings, "SCRIPT_ACT_TIMEOUT_MS", 8) or 8),
    )
    controller_2 = make_controller(
        args.p2_kind,
        player=2,
        screen_width=SCREEN_WIDTH,
        script_path=args.p2_script,
        script_timeout_ms=int(getattr(settings, "SCRIPT_ACT_TIMEOUT_MS", 8) or 8),
    )

    results: List[MatchResult] = []
    for i in range(args.matches):
        results.append(
            run_single_match(
                match_index=i,
                best_of=args.best_of,
                controller_1=controller_1,
                controller_2=controller_2,
                warrior_sheet=warrior_sheet,
                wizard_sheet=wizard_sheet,
                round_time_limit_s=args.round_time,
            )
        )

    p1_match_wins = sum(1 for r in results if r.winner == 1)
    p2_match_wins = sum(1 for r in results if r.winner == 2)
    avg_round_s = statistics.mean([r.avg_round_seconds for r in results]) if results else 0.0

    summary: Dict[str, Any] = {
        "matches": args.matches,
        "best_of": args.best_of,
        "p1": {"kind": args.p1_kind, "script": args.p1_script},
        "p2": {"kind": args.p2_kind, "script": args.p2_script},
        "match_wins": {"p1": p1_match_wins, "p2": p2_match_wins},
        "winrate": {"p1": p1_match_wins / args.matches, "p2": p2_match_wins / args.matches},
        "avg_round_seconds": avg_round_s,
    }

    print(json.dumps(summary, indent=2))

    if args.out:
        if args.out.lower().endswith(".json"):
            payload = {"summary": summary, "matches": [asdict(r) for r in results]}
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
        elif args.out.lower().endswith(".csv"):
            with open(args.out, "w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(asdict(results[0]).keys()))
                w.writeheader()
                for r in results:
                    w.writerow(asdict(r))
        else:
            raise SystemExit("--out must end with .json or .csv")

    pygame.quit()


if __name__ == "__main__":
    main()
