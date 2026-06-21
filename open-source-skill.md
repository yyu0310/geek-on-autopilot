Clean up a personal skill and open-source it into your geek-on-autopilot repo.

⚙️ One-time setup before use: replace the three placeholders below with your actual values, save, and you're ready.

```
REPO_LOCAL_PATH  = /your/local/path/to/geek-on-autopilot/
GITHUB_URL       = https://github.com/YOUR_USERNAME/geek-on-autopilot
SKILL_DIR        = /your/local/path/to/your/skills/folder/
```

Usage:
- `/open-source-skill [skill name]` — find the matching .md in SKILL_DIR
- `/open-source-skill` — start from the skill file currently open in the IDE

---

## Step 0: Open-source suitability check

Before scanning, confirm the skill is worth open-sourcing:

- Does it have standalone value to other users? (no dependency on personal private data or a specific tool)
- After stripping personal info, is the core logic still complete and usable?

⏸ Both Yes → continue to Step 1.
Any doubt → stop and discuss; it's fine to keep it as a personal skill, no need to force it open.

---

## Step 1: Read the source skill

1. Confirm the source file path:
   - Name given → `SKILL_DIR/[name].md`
   - None → take the file currently open in the IDE.
2. Read the whole thing; show the skill name and a 5-line summary.

---

## Step 2: Security scan

Replace each `<placeholder>` below with your actual value, then run them one by one:

```bash
# Personal absolute paths
grep -n "/Users/<your-username>" [file]

# Personal email
grep -ni "gmail\.com\|<your-email-domain>" [file]

# GitHub account identifiers
grep -n "<your-github-username>" [file]

# Personal name (fill in your name)
grep -n "<your-name>" [file]

# External local-file dependencies
grep -n "read the rules file\|from the following path\|/Users/" [file]
```

Classify the scan results:

| Type | Line | Content | Suggested handling |
|---|---|---|---|
| Personal path | ... | ... | Change to a generic description |
| External dependency | ... | ... | Inline the rules into the skill body |
| Personal info | ... | ... | Replace with a generic version |

**If every scan result is "none" → skip Step 3, go straight to Step 4.**

⏸ Any issues → list them and wait for the user to confirm how to handle them.

---

## Step 3: Clean up + translate (only the repo copies; never touch the personal original)

**Golden rule: the personal version (the original in your skills folder) stays exactly as is — not one character changed.** Open-sourcing is "copy it out, then clean the copy", not "clean the original in place". The real paths, machine-specific settings, and personal go-to examples in the original are conveniences for your own use, and shouldn't be sacrificed for open-sourcing. The personal version and the open-source version are meant to differ.

This repo's layout: **English is canonical in the repo root; the Chinese translation lives in `zh/`.** The root file is what installs as the `/command` and shows in `/help`, so it must be English. Run these in order:

1. **Copy the source into `zh/`** (the Chinese version):
   ```bash
   cp [source path] REPO_LOCAL_PATH/zh/[skill name].md
   ```
2. **Clean the `zh/` copy** (the cleanup below runs on the repo copies only; the source is untouched):

   **Personal absolute paths:**
   - `/Users/<your-username>/...` → change to "the file currently open in the IDE" or "your project path"

   **External local-file dependencies (most common: the no-ai-trace type):**
   - Steps that read a local rules file → inline the whole rules content into the skill body
   - Confirm that after inlining, the skill runs standalone with no local files needed

   **Personal info:**
   - Personal email → `your-email@example.com`
   - Personal name → delete it or change to a generic label

3. **Translate the cleaned Chinese into the root file** `REPO_LOCAL_PATH/[skill name].md`:
   - Write native English following `/no-ai-trace` principles, not a literal machine translation. This repo is a portfolio piece; the English quality is the front door.
   - For skills with YAML frontmatter, keep the frontmatter and translate its `description` to English.

After cleanup, show the diff, ⏸ wait for the user to confirm "this is OK" before continuing.

---

## Step 4: Confirm README content

⏸ Collect the following from the user (you can offer a draft for them to edit):

1. **One-line description for the command table** (10 words or fewer)
2. **Detail section** (3–5 lines):
   - What problem this command solves
   - Usage example
   - Any special requirement (e.g. needs Node.js)
3. **One-line English description for llms.txt** (50 words or fewer)

zh-TW is the source of truth; English and Simplified Chinese are converted from zh-TW.

---

## Step 5: Write to the repo

After confirmation, run in order (commit only after everything is done, not step by step):

**5-A: Confirm both command files are in place** (done in Step 3): the English canonical at `REPO_LOCAL_PATH/[skill name].md` and the Chinese translation at `REPO_LOCAL_PATH/zh/[skill name].md`, both cleaned, with the source untouched.

**5-B: Update the three-language READMEs**

Each README needs two edits:

1. **Command table** (add a row at the end of the existing table):
   ```
   | `/[command]` | [description] |
   ```

2. **Command detail section** (add a new block after the last command's detail):
   ````markdown
   ---

   ### `/[command]`

   [detailed description]

   ```
   /[command] [usage example]
   ```
   ````

Language-switcher row format (all three languages; the current language is plain text with no link):
```
[English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md)
```

**5-C: Update llms.txt**

Add a line at the end of the `## Commands` section (link to the English root file):
```
- [/[command]]([skill name].md): [one-line English description]
```

**5-D: Show the diff of all changes**

⏸ Wait for the user's final "ready to push".

---

## Step 6: Commit + Push

```bash
cd REPO_LOCAL_PATH
git add .
git commit -m "feat: add /[skill name] command"
git push
```

If the repo has version management (CHANGELOG.md, release tags), bump the version before pushing.

After confirming the push succeeded, report: GITHUB_URL

After a successful push, update the command count in memory:
```
~/.claude/projects/.../memory/reference_geek_on_autopilot.md
```
Add 1 to the total command count (e.g. "7 slash commands" → "8").

---

## Appendix: signs a skill shouldn't be open-sourced

- The skill's core logic depends on personal private data (personal finance, company-confidential data)
- The skill includes a local tool that can't be generalized
- Removing personal info leaves the skill meaningless
- The skill is just automation of a personal SOP with no reference value to others

Keep these in your personal skills folder; no need to open-source them.
