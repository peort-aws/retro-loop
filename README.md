# 🔄 retro-loop

**A Kiro hook that makes your agent permanently smarter after every conversation.**

Built for the [Kiro 1st Birthday Challenge](https://kiro.dev/birthday/2026/challenge/) — Day 1: Build a Hook.

## What It Does

A two-hook system that creates a **self-learning loop**:

1. **`stop` hook** — After each conversation, analyzes the transcript for user corrections, retry loops, and workarounds. Writes structured improvement suggestions to a pending queue.

2. **`spawn` hook** — At session start, checks the queue and nudges you to review. Apply the suggestions to make fixes permanent.

**The result:** Every mistake becomes a one-time mistake. Your agent accumulates behavioral rules from real usage — far more nuanced than anything you'd write upfront.

## How It Works

```
Session N                              Session N+1
─────────                              ───────────
Conversation happens                   [spawn hook fires]
       │                                      │
       ▼                                      ▼
[stop hook fires]                      "2 pending suggestions
       │                                — say 'retro' to review"
       ▼                                      │
Analyze transcript:                           ▼
 • User corrections                    User reviews & applies
 • Retry loops (3+)                           │
 • Workarounds                                ▼
       │                               Agent is permanently
       ▼                               better 🎉
Write to .kiro/retro/pending/
```

## Detection Patterns

| Signal | Detection | Severity |
|--------|-----------|----------|
| **User correction** | User says "no," "wrong," "actually," "I meant" after agent turn | High |
| **Retry loop** | Same tool/approach invoked 3+ times | Medium |
| **User workaround** | User says "I'll do it manually," "never mind" | Medium |

## Sample Output

```json
{
  "conversation_id": "a1b2c3d4-...",
  "timestamp": "2026-07-13T16:00:00+00:00",
  "suggestions": [
    {
      "type": "steering_update",
      "severity": "high",
      "title": "Calendar search treated as proof of absence",
      "evidence": "Agent: 'No meeting found'... User: 'the meeting IS there'",
      "suggestion": "Add rule: calendar_search is title-only. Never assert absence from a title search alone."
    }
  ]
}
```

## Installation

```bash
# Clone this repo
git clone https://github.com/YOUR_USERNAME/retro-loop.git
cd retro-loop

# Make hooks executable
chmod +x .kiro/hooks/stop-self-learning-analyzer.py
chmod +x .kiro/hooks/spawn-learning-nudge.py
```

Then use Kiro normally. After a few sessions with corrections, you'll see:

> "You have 3 pending retro suggestions — say 'retro' to review."

## File Structure

```
.kiro/
├── hooks/
│   ├── stop-self-learning-analyzer.py   # Post-conversation analyzer
│   └── spawn-learning-nudge.py          # Session-start nudge
└── retro/
    └── pending/                          # Suggestion queue (JSON files)
        └── example-demo-session.json     # Sample suggestion
```

## Real-World Impact

After 3+ months of running this pattern:
- **80+ learned behavioral rules** accumulated from real usage
- Mistakes like "sending when user said draft" — caught once, never repeated
- Retry loops auto-detected and circuit-breaker rules added
- Missing capabilities surfaced and built into new skills

## Requirements

- [Kiro CLI](https://kiro.dev) with hook support
- Python 3.10+
- No external dependencies

## Testing

```bash
python3 test_analyzer.py -v
```

Smoke tests cover transcript parsing, correction detection, retry-loop detection, and workaround detection.

## License

[MIT](./LICENSE)
