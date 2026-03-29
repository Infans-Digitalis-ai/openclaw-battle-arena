"""Battle-Agents runtime settings.

Keep defaults matching current visual/audio behavior.

Controllers:
- "dqn" (original training)
- "heuristic" (lightweight baseline)
- "remote" (WebSocket; external agent supplies actions)

Modes:
- TRAIN: endless episodes (original behavior)
- MATCH: best-of-N rounds (for spectator/competitive play)
"""

# MODE can be: "TRAIN" or "MATCH"
MODE = "MATCH"

# Round format when MODE="MATCH"
MATCH_BEST_OF = 3  # best-of-3 rounds

# Controller selection
# Options: "remote" (ws), "heuristic", "dqn", "script"
# For Option A (local duels), use "script" for both players.
P1_CONTROLLER = "script"  # warrior
P2_CONTROLLER = "script"  # wizard

# Option A (script bots): provide a script path for each player.
# These two files are intended to be generated/edited by OpenClaw agents before a duel.
P1_SCRIPT_PATH = "bots/openclaw_p1.py"
P2_SCRIPT_PATH = "bots/openclaw_p2.py"

# Script controller fairness: per-tick deadline (ms). If a script fails to respond
# in time, the host treats it as NOOP for that tick (and then NOOP for the rest of
# the match to avoid runaway threads).
# At 60 FPS, a tick is ~16.6ms; keep this comfortably below that.
SCRIPT_ACT_TIMEOUT_MS = 8

# Security/privacy: remove generated OpenClaw script bots after each match.
# This keeps the bot handoff clean and ensures each new bot only sees its own script.
AUTO_DELETE_OPENCLAW_SCRIPTS = True

# WebSocket server (used when any controller is "remote")
WS_HOST = "127.0.0.1"
WS_PORT = 8765
