# AGENTS.md

This repo contains Claude Code custom slash commands. Each `.md` file is a standalone command, no shared dependencies, no build step.

## How it works

Each `.md` file in the root becomes a `/command-name` slash command when symlinked to `~/.claude/commands/`. Claude Code reads the file as the command's instructions when the user types `/command-name`. The root files are English (canonical); `zh/` holds the Traditional Chinese translation of each command. To run a command in Chinese, symlink `zh/command-name.md` instead.

## Design decisions

**Self-contained rules.** `no-ai-trace.md` embeds all 17 rules inline. No external file dependencies. The command works immediately after install without additional setup.

**No machine-specific paths.** All references use generic descriptions ("the currently open file in IDE") or user-supplied paths. Nothing hardcoded to a specific machine.

**Language.** English is canonical in the repo root; each command's Traditional Chinese (zh-TW) translation lives in `zh/` with the same filename. The root English file is what installs as the `/command` and shows in `/help`, so it's the front door for international users; `zh/` serves zh-TW/zh-CN readers and anyone who wants to run a command in Chinese. When editing a command, update both the root file and its `zh/` counterpart. The `latest-claude.md` routing table targets English-language official docs because that's where Claude's documentation lives.

**Scripts.** Five commands ship scripts in the repo root, and each command file calls them by relative path:

| Command | Scripts |
| --- | --- |
| `md-to-pdf.md` | `md2pdf.py` (with `reference_pingfang.docx`) |
| `marp-export.md` | `marp_export.py` |
| `ref-audit.md` | `ref_audit.py`, `relink.py` |
| `docx-gen.md` | `docx_pdf.py` (imports `md2pdf.py`, so keep the two together), plus `docx-gen-tools/` with `package.json` and `workspace/example_qa_test.js` |
| `private-site.md` | `cf_private_site.py`, `site_lock_check.sh` |

The Python scripts use only the standard library (the one Node dependency is `docx` in `docx-gen-tools/`; `node_modules/` is git-ignored). `site_lock_check.sh` needs only bash and curl. Every script has a `--selftest` that runs in a temporary folder with no network: `cf_private_site.py` uses a fake Cloudflare API and `site_lock_check.sh` a fake curl. `cf_private_site.py` has no default credential location: it requires the `CF_ENV_FILE` environment variable and exits 5 without it. Scripts resolve helper files relative to themselves. After editing a script, run its selftest and update the matching command file in both languages.

A helper prompt or template that a command needs (like the review prompt in `private-site.md`) is embedded in the command file itself. Every `.md` in the repo root is installed as a slash command, so a separate template `.md` there would turn into a bogus command.

## What not to change

- Do not add file path dependencies that point to a specific machine. If a command needs external data, embed it inline.
- `no-ai-trace.md` Rules 1 to 17, Part 2 rewrites, and the self-check list must stay in sync (in both the root English file and `zh/no-ai-trace.md`). If you add a rule, add the corresponding rewrite example and self-check item to both.
- `latest-claude.md` routing table URLs should only be updated when official Claude docs URLs actually change. Verify against `https://platform.claude.com/llms.txt` before updating.

## Adding a new command

Use `/open-source-skill` to handle the full workflow automatically:
1. Security scan (personal paths, account identifiers, external dependencies)
2. Cleanup with confirmation
3. Updates all three README files and `llms.txt`
4. Commit and push

Manual steps if needed:
1. Create the English `.md` file in the root directory (canonical) and its Chinese translation in `zh/`: self-contained, no external file dependencies.
2. Update all three README files: add a row to the commands table and a new detail section.
3. Add a one-line entry to `llms.txt` (link to the English root file).

**Configuration-required commands.** `open-source-skill.md` contains placeholder values (`REPO_LOCAL_PATH`, `GITHUB_URL`) that users must fill in before first use. This is intentional: it's a template that adapts to any geek-on-autopilot fork.
