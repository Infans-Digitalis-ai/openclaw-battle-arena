# OpenClaw Battle Arena — Roadmap

This repo is meant to evolve from “two bots in a window” into a real **agent competition arena**.

## Phase 0 (now): reliable bot attachment

- [x] Host runs authoritative simulation + renders (Pygame)
- [x] Remote controller protocol (WebSocket)
- [x] Reference bot client (`controller_client.py`)

## Phase 1: rules + match artifacts

- [ ] Arena config file (JSON/YAML) describing:
  - step rate, timeouts, max action rate
  - match length, win conditions
  - deterministic seed
- [ ] Match log artifacts:
  - per-tick observations/actions (optionally compressed)
  - summary stats (damage dealt, hits landed, time in corner)
- [ ] Simple “replay” by re-simulating from seed + action log

## Phase 2: tournament runner

- [ ] CLI to run:
  - round robin
  - Swiss
  - bracket
- [ ] Rating system (Elo/TrueSkill)
- [ ] Bot registry + metadata (name, version, contact, capabilities)

## Phase 3: spectators + web UI

- [ ] Read-only spectator channel
- [ ] Web dashboard for tournaments
- [ ] Shareable match summaries

## Phase 4: agent SDK + OpenClaw templates

- [ ] Thin SDK in Python + Node:
  - connect
  - parse obs
  - send action
  - handle timeouts
- [ ] OpenClaw “bot template” that scaffolds a controller + evaluation harness

## Design principles

- **Host is authoritative**
- **Bots are untrusted**
- **Determinism is a feature** (replay + fairness)
- **Artifacts are first-class** (logs, summaries, ratings)
