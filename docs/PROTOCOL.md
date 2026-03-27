# OpenClaw Battle Arena — Remote Controller Protocol (v0)

Goal: let the **arena host** remain authoritative while bots/agents act as **remote controllers**.

- Transport: WebSocket
- Default URL: `ws://127.0.0.1:8765`
- Encoding: JSON
- Update cadence: host broadcasts observations at ~30Hz (decoupled from render FPS).

## Message types

### 1) Observation (server → client)

```json
{
  "type": "obs",
  "player": 1,
  "obs": {
    "self": { "x": 123.0, "y": 456.0, "health": 92, "attacking": false, "attack_cooldown": 0 },
    "opp":  { "x": 900.0, "y": 456.0, "health": 88, "attacking": true,  "attack_cooldown": 12 },
    "arena": { "w": 1000, "h": 600 },
    "t": 123456
  }
}
```

Notes:
- The schema is intentionally small and stable. Add fields carefully.
- Clients should ignore unknown fields (forward-compat).

### 2) Action (client → server)

```json
{
  "type": "action",
  "player": 1,
  "action": 4
}
```

Action ids (current):
- `0` noop
- `1` move left
- `2` move right
- `3` jump
- `4` heavy attack

Host behavior:
- host never blocks waiting for actions
- if no action arrives, host reuses the last received action for that player (default noop)

## Versioning

Protocol is currently **v0** and may change.

Compatibility guideline:
- additive changes to `obs` are OK
- action id changes must bump the protocol version and keep a compatibility shim if possible

## Security / safety model

Controllers are treated as untrusted:
- they can only propose actions
- the host can clamp/ignore/rate-limit actions
- future: per-controller auth tokens (optional) + spectator read-only channels
