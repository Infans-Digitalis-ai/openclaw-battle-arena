"""Minimal Battle-Agents remote controller client (protocol v0).

Connects to the game's WebSocket server and sends action messages.

Usage:
  . .venv/bin/activate
  python controller_client.py --player 1 --url ws://127.0.0.1:8765 --bot infans

Bots:
- infans: simple distance-based bot
- noop: does nothing

Protocol:
- server -> client: {"type":"obs","player":1|2, "obs":{...}}
- client -> server: {"type":"action","player":1|2, "action":<int>}

Action ids (current):
0 noop, 1 left, 2 right, 3 jump, 4 heavy
"""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any, Dict

import websockets


def choose_action_infans(obs: Dict[str, Any]) -> int:
    s = obs.get("self", {})
    o = obs.get("opp", {})
    sx = float(s.get("x", 0.0))
    ox = float(o.get("x", 0.0))
    dx = ox - sx
    dist = abs(dx)

    cooldown = int(s.get("attack_cooldown", 0) or 0)
    opp_attacking = bool(o.get("attacking", False))

    # Very simple: if opponent is attacking and close, back up.
    if opp_attacking and dist < 160:
        return 1 if dx > 0 else 2  # move away

    if cooldown > 0:
        return 1 if dx < 0 else 2  # move toward

    if dist < 140:
        return 4  # heavy

    return 1 if dx < 0 else 2


def choose_action_noop(obs: Dict[str, Any]) -> int:
    return 0


async def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="ws://127.0.0.1:8765")
    ap.add_argument("--player", type=int, choices=[1, 2], required=True)
    ap.add_argument("--bot", choices=["infans", "noop"], default="infans")
    args = ap.parse_args()

    chooser = choose_action_infans if args.bot == "infans" else choose_action_noop

    async with websockets.connect(args.url, ping_interval=20, ping_timeout=20) as ws:
        print(f"Connected to {args.url} as player {args.player} bot={args.bot}")
        async for msg in ws:
            try:
                data = json.loads(msg)
            except Exception:
                continue

            if data.get("type") != "obs":
                continue
            if int(data.get("player", 0) or 0) != args.player:
                continue

            obs = data.get("obs") or {}
            action = int(chooser(obs))
            out = {"type": "action", "player": args.player, "action": action}
            await ws.send(json.dumps(out))


if __name__ == "__main__":
    asyncio.run(main())
