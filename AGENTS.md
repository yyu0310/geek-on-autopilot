# AGENTS.md

This repo contains Claude Code custom slash commands. Each `.md` file is a standalone command — no shared dependencies, no build step.

## How it works

Each `.md` file in the root becomes a `/command-name` slash command when symlinked to `~/.claude/commands/`. Claude Code reads the file as the command's instructions when the user types `/command-name`. The root files are English (canonical); `zh/` holds the Traditional Chinese translation of each command. To run a command in Chinese, symlink `zh/command-name.md` instead.

## Design decisions

**Self-contained rules.** `no-ai-trace.md` embeds all 17 rules inline. No external file dependencies — the command works immediately after install without additional setup.

**No machine-specific paths.** All references use generic descriptions ("the currently open file in IDE") or user-supplied paths. Nothing hardcoded to a specific machine.

**Language.** English is canonical in the repo root; each command's Traditional Chinese (zh-TW) translation lives in `zh/` with the same filename. The root English file is what installs as the `/command` and shows in `/help`, so it's the front door for international users; `zh/` serves zh-TW/zh-CN readers and anyone who wants to run a command in Chinese. When editing a command, update both the root file and its `zh/` counterpart. The `claude-docs.md` routing table targets English-language official docs because that's where Claude's documentation lives.

## What not to change

- Do not add file path dependencies that point to a specific machine. If a command needs external data, embed it inline.
- `no-ai-trace.md` Rules 1–17, Part 2 rewrites, and the self-check list must stay in sync (in both the root English file and `zh/no-ai-trace.md`). If you add a rule, add the corresponding rewrite example and self-check item to both.
- `claude-docs.md` routing table URLs should only be updated when official Claude docs URLs actually change. Verify against `https://platform.claude.com/llms.txt` before updating.

## Adding a new command

Use `/open-source-skill` to handle the full workflow automatically:
1. Security scan (personal paths, account identifiers, external dependencies)
2. Cleanup with confirmation
3. Updates all three README files and `llms.txt`
4. Commit and push

Manual steps if needed:
1. Create the English `.md` file in the root directory (canonical) and its Chinese translation in `zh/` — self-contained, no external file dependencies.
2. Update all three README files: add a row to the commands table and a new detail section.
3. Add a one-line entry to `llms.txt` (link to the English root file).

**Configuration-required commands.** `open-source-skill.md` contains placeholder values (`REPO_LOCAL_PATH`, `GITHUB_URL`) that users must fill in before first use. This is intentional — it's a template that adapts to any geek-on-autopilot fork.
