#!/usr/bin/env python3
"""Pickbox: Claude's questions arrive as a native pick list on your screen, wherever you are.

A Claude Code PreToolUse hook for the built-in AskUserQuestion tool. For each question it shows one native list box
(macOS today): the recommended option (the one marked "(Recommended)", else the first) is pre-selected, several can
be picked when the question allows it, "Other (I'll type it)" and "Not now" are always there. Your answers go back to
Claude in the same turn. If the box cannot be shown (not a Mac, no display, osascript missing), the hook steps aside
and the normal in-terminal question appears.

Why: one glance and one click from any screen. Kody, 2026-10-16: "cuts down decision fatigue across screens IMMENSELY".

Test seam: PICKBOX_FAKE_ANSWERS='["A", "B || C"]' answers the boxes without showing them.
"""
import json
import os
import platform
import subprocess
import sys

OTHER = "Other (I'll type it in the chat)"
RECOMMENDED = "(Recommended)"


def osa_quote(text):
    return '"' + str(text).replace("\\", "\\\\").replace('"', '\\"') + '"'


def pick(title, prompt, items, default, multi):
    """The chosen labels, [] for "Not now", or None when no box could be shown."""
    fake = os.environ.get("PICKBOX_FAKE_ANSWERS")
    if fake is not None:
        answers = json.loads(fake)
        idx = int(os.environ.get("PICKBOX_FAKE_INDEX", "0"))
        os.environ["PICKBOX_FAKE_INDEX"] = str(idx + 1)
        a = answers[idx] if idx < len(answers) else ""
        return [] if a == "NOT NOW" else [x for x in a.split(" || ") if x]
    if platform.system() != "Darwin":
        return None
    script = [
        "-e", f"set r to choose from list {{{', '.join(osa_quote(i) for i in items)}}} with title {osa_quote(title)} "
              f"with prompt {osa_quote(prompt)} default items {{{osa_quote(default)}}}"
              + (" with multiple selections allowed" if multi else "")
              + ' OK button name "Answer" cancel button name "Not now"',
        "-e", 'if r is false then return "\u0000NOT NOW"',
        "-e", 'set AppleScript\'s text item delimiters to "\u0001"', "-e", "return r as text"]
    try:
        p = subprocess.run(["osascript", *script], capture_output=True, text=True, timeout=3600)
    except (OSError, subprocess.SubprocessError):
        return None
    if p.returncode != 0:
        return None
    out = p.stdout.rstrip("\n")
    return [] if out == "\u0000NOT NOW" else [x for x in out.split("\u0001") if x]


def ask_all(tool_input):
    """[(question, [answers])] or None when the boxes cannot be shown."""
    results = []
    for q in tool_input.get("questions", []):
        labels = [o.get("label", "") for o in q.get("options", []) if o.get("label")]
        default = next((l for l in labels if RECOMMENDED.lower() in l.lower()), labels[0] if labels else OTHER)
        descriptions = {o.get("label"): o.get("description", "") for o in q.get("options", [])}
        detail = "\n".join(f"• {l}: {descriptions[l]}" for l in labels if descriptions.get(l))
        prompt = q.get("question", "") + (("\n\n" + detail) if detail else "")
        chosen = pick(q.get("header") or "Claude asks", prompt[:900], labels + [OTHER], default, bool(q.get("multiSelect")))
        if chosen is None:
            return None
        results.append((q.get("question", ""), chosen))
    return results


def reason_text(results):
    lines = ["The user answered in the on-screen pick list (Pickbox):"]
    for question, chosen in results:
        if not chosen:
            lines.append(f'- "{question}": they chose "Not now". Do not proceed with that decision; carry on with other work.')
        elif OTHER in chosen:
            lines.append(f'- "{question}": they want to answer in their own words. Ask them in the chat, briefly.')
        else:
            lines.append(f'- "{question}": ' + ", ".join(f'"{c}"' for c in chosen))
    lines.append("Act on these answers now; do not ask the same question again.")
    return "\n".join(lines)


def main():
    try:
        event = json.load(sys.stdin)
    except ValueError:
        return 0
    if event.get("tool_name") != "AskUserQuestion":
        return 0
    results = ask_all(event.get("tool_input") or {})
    if results is None:
        return 0  # no box possible: let the normal in-terminal question show
    # Deny the terminal prompt and hand the answers back in the reason, which Claude reads in this turn.
    print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                             "permissionDecisionReason": reason_text(results)}}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
