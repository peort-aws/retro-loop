#!/usr/bin/env python3
"""
Kiro Spawn Hook: Learning Nudge
================================
Fires at session start. Checks for pending improvement suggestions
from the stop hook analyzer. If found, injects a nudge into the
agent's context so it can offer to apply the learnings.

Hook type: spawn
Output: INSTRUCTION directive to agent context window
"""

import json
from pathlib import Path


def main():
    pending_dir = Path(".kiro/retro/pending")
    if not pending_dir.is_dir():
        return

    total = 0
    high_count = 0
    for f in sorted(pending_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            for s in data.get("suggestions", []):
                total += 1
                if s.get("severity") == "high":
                    high_count += 1
        except (json.JSONDecodeError, KeyError):
            continue

    if total == 0:
        return

    # Inject nudge into agent context via stdout
    severity_note = f" ({high_count} high-severity)" if high_count else ""
    print(
        f"INSTRUCTION: There are {total} pending improvement suggestion(s){severity_note} "
        f"from previous sessions. Mention this once when there's a natural pause: "
        f"\"You have {total} pending retro suggestions — say 'retro' to review.\" "
        f"Then never mention them again this session."
    )


if __name__ == "__main__":
    main()
