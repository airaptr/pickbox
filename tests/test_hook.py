import json
import os
import subprocess
import sys
import unittest

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts", "pickbox_hook.py")
Q = {"tool_name": "AskUserQuestion", "tool_input": {"questions": [
    {"question": "Which add-ons?", "header": "Add-ons", "multiSelect": True,
     "options": [{"label": "Drive health (Recommended)", "description": "warn before a disk dies"},
                 {"label": "Secret sweep"}, {"label": "Credit juggler"}]},
    {"question": "Ship it?", "header": "Ship", "options": [{"label": "Yes"}, {"label": "No"}]}]}}


def run(event, answers):
    env = dict(os.environ, PICKBOX_FAKE_ANSWERS=json.dumps(answers), PICKBOX_FAKE_INDEX="0")
    p = subprocess.run([sys.executable, HOOK], input=json.dumps(event), capture_output=True, text=True, env=env)
    return json.loads(p.stdout) if p.stdout.strip() else None


class Hook(unittest.TestCase):
    def test_answers_come_back_for_every_question(self):
        out = run(Q, ["Drive health (Recommended) || Secret sweep", "Yes"])
        reason = out["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertEqual(out["hookSpecificOutput"]["permissionDecision"], "deny")
        self.assertIn('"Drive health (Recommended)", "Secret sweep"', reason)
        self.assertIn('"Ship it?": "Yes"', reason)

    def test_not_now_and_other_are_explained(self):
        reason = run(Q, ["NOT NOW", "Other (I'll type it in the chat)"])["hookSpecificOutput"]["permissionDecisionReason"]
        self.assertIn("Not now", reason)
        self.assertIn("own words", reason)

    def test_other_tools_are_left_alone(self):
        self.assertIsNone(run({"tool_name": "Bash", "tool_input": {}}, []))


if __name__ == "__main__":
    unittest.main()
