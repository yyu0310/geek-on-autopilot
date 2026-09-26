English | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md)

# geek-on-autopilot

Twelve custom slash commands that make Claude Code more useful.

## Problems solved

- AI training data has a cutoff date, making time-sensitive answers unreliable
- Claude's official docs update fast, and finding the right page takes time
- Other AI vendors ship weekly too, and their news is scattered across blogs, docs, and changelogs
- AI-generated text has a recognizable AI voice that needs polishing
- Chinese writing has AI tells that English-first rules miss
- Sessions end without a clear record of what was decided or done
- No standardized QA before exporting Marp presentations
- Pandoc's default fonts break Chinese-English mixed PDFs
- AI answers medical questions with confident hallucinations and no authoritative source

## Commands

| Command | What it does |
|---|---|
| `/latest` | Forces web search before answering any time-sensitive question |
| `/claude-docs` | Routes directly to the right Claude docs page, with source URL |
| `/latest-ai` | Answers questions about AI vendors other than Claude from official sources, or compiles a past-week roundup |
| `/no-ai-trace` | Scans text against 17 AI writing anti-patterns |
| `/no-ai-trace-lite` | Fast 3-grep, 4-scan check for internal documents |
| `/no-ai-trace-zh` | Checks Chinese writing against Chinese-specific AI tells |
| `/session-review` | Six-block session wrap-up in under 45 lines |
| `/marp-export` | QA check, PDF export, and output verification for Marp presentations |
| `/open-source-skill` | Full SOP for cleaning and publishing a skill to your open-source repo |
| `/md-to-pdf` | Converts Markdown to PDF with a bundled PingFang TC font template |
| `/recover-from-log` | Recovers deleted or mangled file content from Claude Code session logs |
| `/med-check` | Answers medical questions from authoritative literature, never training data |

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

`/md-to-pdf` and `/marp-export` call a Python script in the repo root (`md2pdf.py`, `marp_export.py`). Keep the clone in place, since the commands run those scripts from it.

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

### `/latest-ai`

Answers frontier-AI questions from each vendor's official docs, news pages, and changelogs instead of training data. `/claude-docs` covers Claude. `/latest-ai` covers every other vendor and cross-vendor roundups. Given a question, it routes to the relevant company's official sources. With no question, it compiles the past week's product updates, scanning the major vendors first.

```
/latest-ai did OpenAI change its API pricing this month?
/latest-ai                     # past-week roundup
```

---

### `/no-ai-trace`, `/no-ai-trace-lite`, `/no-ai-trace-zh`

Three checkers for AI writing patterns. Pick one by the kind of text you have:

| Command | Use it for | How it checks |
|---|---|---|
| `/no-ai-trace` | Public-facing English copy: READMEs, posts, PRs, emails | 17 rules. Lists each violation with the original sentence and a suggested rewrite, then gives a tone verdict |
| `/no-ai-trace-lite` | Internal working documents: proposals, logs, architecture notes | 3 mechanical greps and 4 quick semantic scans, so it runs fast after every edit |
| `/no-ai-trace-zh` | Chinese copy | Rules Z1 to Z11 for tells specific to Chinese, like meta-narrative labels, negated-premise contrast, and translationese, plus baseline checks |

```
/no-ai-trace                   # Check the most recent output in the conversation
/no-ai-trace [paste your text]
/no-ai-trace-lite docs/proposal.md
/no-ai-trace-zh [貼上要檢查的中文]
```

The 17 rules in `/no-ai-trace` cover buzzword stacking, "not just A but B" negation openers, nominalization, em dashes and semicolons, rhetorical questions with self-answers, filler transition words, parallel fragment stacking, and more.

---

### `/session-review`

Six-block wrap-up before ending a Claude Code session:

1. **Key takeaways**: decisions made, things learned, insights worth keeping (max 8 items)
2. **Loose ends**: only what truly fell out of every tracking system (⬜ to-do / ❓ needs confirmation)
3. **Already-planned items**: unfinished but tracked elsewhere, so they don't count as loose ends
4. **Memory suggestions**: what's worth saving to Claude's memory system
5. **Doc check**: if code changed, whether related docs were updated
6. **QA evidence**: for any code written, whether a real command was run and its output kept

All six blocks in under 45 lines. When several sessions work on the same thing, it distills all of them.

---

### `/marp-export`

QA check and PDF export for Marp presentations, run by `marp_export.py` in the repo root:

1. `qa` scans for draft markers (`TODO`, `FIXME`, `TBD`, `XXX`, and the `【` bracket) and checks that every local image exists
2. `export` builds the PDF with `npx` and `@marp-team/marp-cli`
3. `verify` confirms the PDF exists, isn't empty, and is newer than the source

Requires: Node.js and Python 3

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

### `/md-to-pdf`

Converts Markdown to PDF using PingFang TC, the font with the fewest rendering bugs for Chinese-English mixed documents. It ships free with macOS, so Windows and Linux users need to source it separately. `md2pdf.py` in the repo root runs the pipeline: lint for known Pandoc traps, pandoc builds a DOCX from the bundled `reference_pingfang.docx` template, LibreOffice converts it to PDF, and a `pdffonts` check retries until every font is PingFang TC. Extras: `--strip` renders one tall page with no page breaks, and `wordcount` enforces a word limit.

Runs entirely on your machine. No third-party services and no document data sent anywhere, so it suits confidential files. It targets Chinese and mixed Chinese and English documents, and English-only files fail the font check.

Requires: Python 3, pandoc, LibreOffice, poppler (`brew install pandoc poppler && brew install --cask libreoffice`)

```
/md-to-pdf                    # Convert the currently open .md file
/md-to-pdf /path/to/file.md
```

---

### `/recover-from-log`

When a Claude Code operation (a `/simplify`, an accidental delete, a bad edit) mangles your file, this recovers the original from the session logs. Every session's `.jsonl` stores the full transcript, including the content of every file Read and the `old_string` of every Edit — so the pre-change version is still in there. The skill diagnoses which session and operation caused the damage, extracts the original, and restores it surgically: it keeps the good changes instead of blindly reverting the whole thing.

It also handles a sharp trap. A skill's own name (like `simplify`) is injected into every session's skill list, so a bare grep matches almost every session. The skill matches the actual command invocation instead, and excludes the current session before pinning the culprit.

```
/recover-from-log [filename]
```

---

### `/med-check`

Answers medical and health questions from authoritative medical literature instead of training data, which hallucinates dangerously on health topics. It forces a retrieval-first workflow: Cochrane systematic reviews, clinical guidelines, PubMed primary research (via the free E-utilities API, no key needed), and authoritative health bodies (WHO, CDC, FDA, NIH). Every claim is graded by evidence level (proven / insufficient / conflicting), tagged with uncertainty, and cited with a PMID link. If the literature comes up empty, it says so instead of inventing an answer. It screens for red-flag emergency symptoms first and reminds you to see a doctor.

This is a literature-research aid, not a medical diagnosis.

```
/med-check [your health question]
/med-check                     # use the most recent health question in the conversation
```

## License

MIT
