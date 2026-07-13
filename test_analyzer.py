#!/usr/bin/env python3
"""
Smoke tests for stop-self-learning-analyzer.py

Run with: python3 -m pytest test_analyzer.py -v
Or standalone: python3 test_analyzer.py
"""

import importlib.util
import sys
import unittest
from pathlib import Path

# Load the hook module (filename has hyphens, so we can't `import` it normally)
_hook_path = Path(__file__).parent / ".kiro" / "hooks" / "stop-self-learning-analyzer.py"
_spec = importlib.util.spec_from_file_location("analyzer", _hook_path)
analyzer = importlib.util.module_from_spec(_spec)
sys.modules["analyzer"] = analyzer
_spec.loader.exec_module(analyzer)


class TestParseTurns(unittest.TestCase):
    def test_parses_user_and_assistant_turns(self):
        transcript = (
            "## User\n"
            "Do the thing\n"
            "## Assistant\n"
            "I did the thing\n"
        )
        turns = analyzer.parse_turns(transcript)
        self.assertEqual(len(turns), 2)
        self.assertEqual(turns[0]["role"], "user")
        self.assertEqual(turns[1]["role"], "assistant")


class TestFindUserCorrections(unittest.TestCase):
    def test_detects_correction_signal(self):
        turns = [
            {"role": "assistant", "content": "I sent the email to the wrong person."},
            {"role": "user", "content": "No, that's not what I asked for."},
        ]
        suggestions = analyzer.find_user_corrections(turns)
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["severity"], "high")
        self.assertEqual(suggestions[0]["type"], "steering_update")

    def test_no_false_positive_on_normal_turn(self):
        turns = [
            {"role": "assistant", "content": "Here is the summary you asked for."},
            {"role": "user", "content": "Thanks, that looks great."},
        ]
        suggestions = analyzer.find_user_corrections(turns)
        self.assertEqual(len(suggestions), 0)


class TestFindRetryLoops(unittest.TestCase):
    def test_detects_repeated_tool_calls(self):
        turns = [
            {"role": "assistant", "content": "<invoke name=\"search\">query=foo</invoke>"},
            {"role": "assistant", "content": "<invoke name=\"search\">query=foo</invoke>"},
            {"role": "assistant", "content": "<invoke name=\"search\">query=foo</invoke>"},
        ]
        suggestions = analyzer.find_retry_loops(turns)
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["severity"], "medium")

    def test_no_loop_below_threshold(self):
        turns = [
            {"role": "assistant", "content": "<invoke name=\"search\">query=foo</invoke>"},
        ]
        suggestions = analyzer.find_retry_loops(turns)
        self.assertEqual(len(suggestions), 0)


class TestFindWorkarounds(unittest.TestCase):
    def test_detects_workaround_signal(self):
        turns = [
            {"role": "user", "content": "Never mind, I'll do this myself."},
        ]
        suggestions = analyzer.find_workarounds(turns)
        self.assertEqual(len(suggestions), 1)
        self.assertEqual(suggestions[0]["type"], "new_skill")


if __name__ == "__main__":
    unittest.main()
