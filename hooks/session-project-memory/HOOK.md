---
name: session-project-memory
description: "On new session start, point the agent to the active project memory file"
homepage: https://docs.openclaw.ai/automation/hooks
metadata:
  {
    "openclaw": {
      "emoji": "🧭",
      "events": ["session:start"],
      "requires": { "config": ["workspace.dir"] }
    }
  }
---

# Session Project Memory Hook

Reads `memory/.current-project` and injects a startup instruction for new sessions to load today's project memory file.

It also creates the daily file if missing.
