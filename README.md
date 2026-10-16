# Pickbox

Claude's questions arrive as a native pick list on your screen, wherever you are: the recommended answer pre-selected,
several picks when they combine, always "Not now". One glance, one click, from any screen.

> "cuts down decision fatigue across screens IMMENSELY" — Kody, the first user (2026-10-16)

## Install (Claude Code plugin)

```
/plugin install pickbox@<marketplace>
```

or add the hook yourself to `~/.claude/settings.json`:

```json
{"hooks": {"PreToolUse": [{"matcher": "AskUserQuestion", "hooks": [
  {"type": "command", "command": "python3 /path/to/pickbox/scripts/pickbox_hook.py", "timeout": 3600}]}]}}
```

How it works: Claude asks with its built-in question tool; Pickbox shows each question as a native list box (macOS),
returns your choice to Claude in the same turn, and steps aside (the normal terminal question appears) anywhere it
cannot show a box.

## Free and Pro (draft, pricing not set)

Free: the macOS pick list for Claude Code.
Pro leads with (Kody's pick, 2026-10-16): **answer from your phone** when away from the Mac.
Other Pro ideas:  when away from the Mac; Windows and Linux boxes; a decision inbox that batches
questions from several agents; safe-default timeouts; team routing; a decision log; any agent (Copilot, Cursor, Codex)
through MCP.
