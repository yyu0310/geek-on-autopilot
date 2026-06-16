English | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md)

# geek-on-autopilot

Five custom slash commands that make Claude Code more useful.

## Problems solved

- AI training data has a cutoff date, making time-sensitive answers unreliable
- Claude's official docs update fast, and finding the right page takes time
- AI-generated text has a recognizable AI voice that needs polishing
- Sessions end without a clear record of what was decided or done
- No standardized QA before exporting Marp presentations
- Pandoc's default fonts break Chinese-English mixed PDFs

## Commands

| Command | What it does |
|---|---|
| `/latest` | Forces web search before answering any time-sensitive question |
| `/claude-docs` | Routes directly to the right Claude docs page, with source URL |
| `/no-ai-trace` | Scans text against 17 AI writing anti-patterns |
| `/session-review` | Four-block session wrap-up in under 35 lines |
| `/marp-export` | QA check and PDF export for Marp presentations |
| `/open-source-skill` | Full SOP for cleaning and publishing a skill to your open-source repo |
| `/local-md-to-pdf` | Converts Markdown to PDF with a bundled PingFang TC font template |

## Install

Requires [Claude Code](https://claude.ai/code).

```bash
git clone https://github.com/yyu0310/geek-on-autopilot.git
cd geek-on-autopilot

# Install all commands
for f in *.md; do
  ln -sf "$(pwd)/$f" ~/.claude/commands/"$f"
done
```

Or install only what you need:

```bash
ln -sf "$(pwd)/latest.md" ~/.claude/commands/latest.md
```

After installing, type `/latest`, `/claude-docs`, etc. in Claude Code to use them.

## Commands in detail

### `/latest`

Forces a web search before answering questions with a time-sensitive answer. AI training data has a cutoff date. For questions about AI tools, model versions, API changes, or library support status, the training data's answer is treated as a stale candidate, not a conclusion.

```
/latest What's new in the latest Claude Code version?
```

---

### `/claude-docs`

Routes to the right Claude official docs page based on your question, with source URL. The routing table covers 20+ topics: API parameters, model specs, Prompt Caching, Tool Use, MCP, Agent Skills, and more.

```
/claude-docs how does prompt caching work?
/claude-docs latest available models
```

---

### `/no-ai-trace`

Scans text for AI writing patterns. Checks against 17 rules, lists each violation with the original sentence and a suggested rewrite, then gives an overall tone verdict.

```
/no-ai-trace                   # Check the most recent output in the conversation
/no-ai-trace [paste your text]
```

Rules cover: buzzword stacking, "not just A but B" negation openers, nominalization, em dashes, rhetorical questions with self-answers, filler transition words, parallel fragment stacking, and more.

---

### `/session-review`

Four-block wrap-up before ending a Claude Code session:

1. **Key takeaways** — decisions made, things learned, insights worth keeping (max 8 items)
2. **Open items** — things mentioned but not finished (⬜ to-do / ❓ needs confirmation)
3. **Memory suggestions** — what's worth saving to Claude's memory system
4. **Doc check** — if code changed, whether related docs were updated

All four blocks in under 35 lines.

---

### `/marp-export`

QA check and PDF export for Marp presentations:

1. Scans for draft markers (`【` prefix), waits for confirmation before proceeding
2. Verifies all `assets/` images exist
3. Exports PDF, reports path and file size

Requires: Node.js (uses `npx` to run `@marp-team/marp-cli`)

```
/marp-export                   # Export the currently open .md file
/marp-export /path/to/file.md
```

---

### `/open-source-skill`

Full SOP for open-sourcing a personal skill. Runs a six-category security scan (personal paths, email addresses, account identifiers, external file dependencies, and more), lists all issues for confirmation, then handles cleanup, updates all three README files and llms.txt, and commits and pushes.

Requires one-time setup: fill in your repo's local path and GitHub URL at the top of the skill file.

```
/open-source-skill session-review
/open-source-skill                  # start from the currently open skill file
```

---

### `/local-md-to-pdf`

Converts Markdown to PDF using PingFang TC, the font with the fewest rendering bugs for Chinese-English mixed documents. It ships free with macOS — Windows and Linux users need to source it separately. Conversion runs in two steps: pandoc builds a DOCX using the bundled `reference_pingfang.docx` template, then LibreOffice converts it to PDF. Before converting, scans for common Pandoc format traps (numbered lists missing a leading blank line). The font template is included in the repo — set one path after cloning and the command works immediately.

Runs entirely on your machine. No third-party services, no document data sent anywhere — suitable for confidential files.

Requires: pandoc, LibreOffice (`brew install pandoc && brew install --cask libreoffice`)

```
/local-md-to-pdf                    # Convert the currently open .md file
/local-md-to-pdf /path/to/file.md
```

## License

MIT
