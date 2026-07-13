#!/usr/bin/env python3
"""
Kiro Stop Hook: Self-Learning Conversation Analyzer
====================================================
Fires after each conversation ends. Analyzes the transcript for:
- User corrections (agent said X, user said "no, actually Y")
- Retry loops (same approach attempted 3+ times)
- Missing capabilities the user worked around

Writes structured improvement suggestions to .kiro/retro/pending/.
A companion spawn hook nudges the user to review them next session.

Hook type: stop
Output: JSON suggestion files
"""

import json
import os
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def analyze_transcript(transcript_path: str) -> list[dict]:
    """
    Analyze a conversation transcript for improvement signals.

    Returns a list of structured suggestions, each with:
    - type: skill_improvement | steering_update | new_skill
    - severity: high | medium | low
    - title: Short description
    - evidence: Relevant transcript excerpt
    - suggestion: Proposed fix
    """
    transcript = Path(transcript_path).read_text(encoding="utf-8")
    turns = parse_turns(transcript)

    suggestions = []
    suggestions.extend(find_user_corrections(turns))
    suggestions.extend(find_retry_loops(turns))
    suggestions.extend(find_workarounds(turns))

    return suggestions


def parse_turns(transcript: str) -> list[dict]:
    """Parse transcript into structured turns with role and content."""
    turns = []
    current_role = None
    current_content = []

    for line in transcript.split("\n"):
        if line.startswith("## Human") or line.startswith("## User"):
            if current_role:
                turns.append({"role": current_role, "content": "\n".join(current_content)})
            current_role = "user"
            current_content = []
        elif line.startswith("## Assistant") or line.startswith("## Agent"):
            if current_role:
                turns.append({"role": current_role, "content": "\n".join(current_content)})
            current_role = "assistant"
            current_content = []
        else:
            current_content.append(line)

    if current_role:
        turns.append({"role": current_role, "content": "\n".join(current_content)})

    return turns


def find_user_corrections(turns: list[dict]) -> list[dict]:
    """Detect turns where the user corrected the agent's behavior."""
    suggestions = []
    correction_signals = [
        "no,", "wrong", "actually", "i meant", "that's not",
        "don't do that", "i said", "not what i asked",
    ]

    for i, turn in enumerate(turns):
        if turn["role"] != "user":
            continue
        content_lower = turn["content"].lower()

        if any(signal in content_lower for signal in correction_signals):
            prev_assistant = ""
            if i > 0 and turns[i - 1]["role"] == "assistant":
                prev_assistant = turns[i - 1]["content"][:200]

            suggestions.append({
                "type": "steering_update",
                "severity": "high",
                "title": f"User correction at turn {i}",
                "evidence": f"Agent: {prev_assistant}...\nUser: {turn['content'][:200]}",
                "suggestion": "Encode the correct behavior as a steering constraint to prevent recurrence.",
            })

    return suggestions


def find_retry_loops(turns: list[dict]) -> list[dict]:
    """Detect when the same tool/approach was tried 3+ times."""
    suggestions = []
    tool_calls = []

    for turn in turns:
        if turn["role"] != "assistant":
            continue
        for line in turn["content"].split("\n"):
            if "invoke name=" in line or "tool_call" in line:
                # Normalize to just the tool name
                tool_calls.append(line.strip()[:80])

    if len(tool_calls) >= 3:
        counts = Counter(tool_calls)
        for call, count in counts.items():
            if count >= 3:
                suggestions.append({
                    "type": "skill_improvement",
                    "severity": "medium",
                    "title": f"Retry loop: same tool called {count}x",
                    "evidence": f"Tool pattern repeated {count} times: {call[:60]}",
                    "suggestion": "Add a circuit breaker — switch approach after 2 failures instead of retrying.",
                })

    return suggestions


def find_workarounds(turns: list[dict]) -> list[dict]:
    """Detect when user did something manually the agent could automate."""
    suggestions = []
    workaround_signals = [
        "i'll do it manually", "let me handle", "i'll just",
        "never mind, i'll", "forget it", "i'll do this myself",
    ]

    for i, turn in enumerate(turns):
        if turn["role"] != "user":
            continue
        content_lower = turn["content"].lower()

        if any(signal in content_lower for signal in workaround_signals):
            suggestions.append({
                "type": "new_skill",
                "severity": "medium",
                "title": f"User workaround at turn {i}",
                "evidence": turn["content"][:200],
                "suggestion": "Consider building a skill or automation for this workflow.",
            })

    return suggestions


def main():
    """Entry point — called by Kiro after conversation ends."""
    transcript_path = os.environ.get("KIRO_TRANSCRIPT_PATH")
    if not transcript_path or not Path(transcript_path).exists():
        return

    # Skip very short conversations (< 3 turns)
    transcript = Path(transcript_path).read_text(encoding="utf-8")
    turn_count = transcript.count("## Human") + transcript.count("## User")
    if turn_count < 3:
        return

    suggestions = analyze_transcript(transcript_path)
    if not suggestions:
        return

    # Write suggestions to pending queue
    output_dir = Path(".kiro/retro/pending")
    output_dir.mkdir(parents=True, exist_ok=True)

    conversation_id = str(uuid.uuid4())
    output = {
        "conversation_id": conversation_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "suggestions": suggestions,
    }

    output_file = output_dir / f"{conversation_id}.json"
    output_file.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"[retro] Wrote {len(suggestions)} suggestion(s) to {output_file.name}")


if __name__ == "__main__":
    main()
