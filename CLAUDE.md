# CLAUDE.md

This repo contains Claude Code custom slash commands. Each `.md` file is a standalone command — no shared dependencies, no build step.

## How it works

Each `.md` file in the root becomes a `/command-name` slash command when symlinked to `~/.claude/commands/`. Claude Code reads the file as the command's instructions when the user types `/command-name`.

## Design decisions

**Self-contained rules.** `no-ai-trace.md` embeds all 17 rules inline. No external file dependencies — the command works immediately after install without additional setup.

**No machine-specific paths.** All references use generic descriptions ("the currently open file in IDE") or user-supplied paths. Nothing hardcoded to a specific machine.

**Language.** Commands are written in Traditional Chinese (zh-TW). The `claude-docs.md` routing table targets English-language official docs because that's where Claude's documentation lives.

## What not to change

- Do not add file path dependencies that point to a specific machine. If a command needs external data, embed it inline.
- `no-ai-trace.md` Rules 1–17, Part 2 rewrites, and the self-check list must stay in sync. If you add a rule, add the corresponding rewrite example and self-check item.
- `claude-docs.md` routing table URLs should only be updated when official Claude docs URLs actually change. Verify against `https://platform.claude.com/llms.txt` before updating.

## Adding a new command

1. Create a `.md` file in the root directory.
2. Write the command as a self-contained prompt — no external file dependencies.
3. Update all three README files with the new command's description.
4. Add a one-line entry to `llms.txt`.
