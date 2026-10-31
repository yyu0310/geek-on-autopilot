Clean up a personal skill and open-source it into your geek-on-autopilot repo.

⚙️ One-time setup before use: replace the three placeholders below with your actual values, save, and you're ready.

```
REPO_LOCAL_PATH  = /your/local/path/to/geek-on-autopilot/
GITHUB_URL       = https://github.com/YOUR_USERNAME/geek-on-autopilot
SKILL_DIR        = /your/local/path/to/your/skills/folder/
```

Usage:
- `/open-source-skill [skill name]`: find the matching .md in SKILL_DIR
- `/open-source-skill`: start from the skill file currently open in the IDE

---

## Step 0: Open-source suitability check

Before scanning, confirm the skill is worth open-sourcing:

- Does it have standalone value to other users? (no dependency on personal private data or a specific tool)
- After stripping personal info, is the core logic still complete and usable?
- **Is the source someone else's?** Anything downloaded, adapted, or distilled from another person's work is never open-sourced, whether or not they granted a license. Crediting them doesn't replace this check. Judge by evidence, not impression: if the source file contains wording like "source", "adapted from", "upstream", "original", or "distilled from", or its step order matches a public skill (when in doubt, curl the upstream text and compare headings and examples), treat it as third-party. If the user's recollection conflicts with the file, show them the evidence instead of going along with the recollection.

⏸ First two Yes, third No → continue to Step 1.
Any doubt → stop and discuss; it's fine to keep it as a personal skill, no need to force it open.
Third is Yes (third-party source) → stop and report. Don't clean it, translate it, or put it in the repo.

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

# Company or employer name
grep -n "<your-company>" [file]

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

**Golden rule: the personal version (the original in your skills folder) stays exactly as is, not one character changed.** Open-sourcing is "copy it out, then clean the copy", not "clean the original in place". The real paths, machine-specific settings, and personal go-to examples in the original are conveniences for your own use, and shouldn't be sacrificed for open-sourcing. The personal version and the open-source version are meant to differ.

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

   **Company name and personal info:**
   - Company or employer name → `your company`, `the platform`, or delete it
   - Personal email → `your-email@example.com`
   - Personal name → delete it or change to a generic label

3. **Translate the cleaned Chinese into the root file** `REPO_LOCAL_PATH/[skill name].md`:
   - Write native English following `/no-ai-trace` principles, not a literal machine translation. This repo is a portfolio piece; the English quality is the front door.
   - For skills with YAML frontmatter, keep the frontmatter and translate its `description` to English.

**Skills that ship a script:** after cleanup, run `--selftest` for real and compare the pass count with the personal version. Cleanup counts as successful only when both pass in full. Don't rely on a subagent's self-report. When a subagent translates or cleans, keep the selftest fixtures in their original language. Translated fixtures can fail checks that depend on the original language, and the score then drops for a reason unrelated to the code.

After cleanup, show the diff, ⏸ wait for the user to confirm "this is OK" before continuing.

---

## Step 4: Confirm README content

⏸ Collect the following from the user (you can offer a draft for them to edit):

1. **One-line description for the command table** (10 words or fewer)
2. **Detail section** (3 to 5 lines):
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

First confirm the commit identity is your noreply address (geek-on-autopilot is a public repo):
```bash
git -C REPO_LOCAL_PATH config user.email
# should be <id>+<your-github-username>@users.noreply.github.com
# if not: git -C REPO_LOCAL_PATH config user.email "<id>+<your-github-username>@users.noreply.github.com"
```

Neither your real name nor your computer's hostname may appear in a commit's author field, so check `git config user.name` before pushing as well.

Add files one by one. Don't use `git add .`. How to split commits: for each skill, the English canonical file gets one commit and the zh translation gets another, and the README and llms.txt changes go in a separate docs commit. This applies to a new skill and to an update of an existing one. GitHub's contribution graph counts commits rather than pushes, so splitting this way also gives a more granular history.

If the repo shows unrelated file-mode changes (644 to 755, common after moving a folder), always pass `-c core.fileMode=false` to `git add`, or the mode change gets pulled into the commit. zsh won't split a string variable into a command and its arguments, so don't store a git command in a variable and expand it. Wrap it in a function instead.

```bash
cd REPO_LOCAL_PATH
g() { git -c core.fileMode=false "$@"; }

g add [skill name].md
g status  # confirm only the English canonical file is staged
git commit -m "feat: add /[skill name] command"

g add zh/[skill name].md
g status  # confirm only the zh translation is staged
git commit -m "docs: add zh translation of /[skill name]"

g add README.md README.zh-TW.md README.zh-CN.md llms.txt
g status  # confirm only the docs files are staged
git commit -m "docs: document /[skill name] in README and llms.txt"

git push
```

When updating an existing skill, use `feat: <what changed> to /[skill name]` for the English canonical commit and `docs: sync zh translation of ...` for the zh commit. Add the third docs commit only if the docs changed. When a batch covers several skills, split each skill on its own instead of merging them into one big commit. After committing, run `git show --summary --format= HEAD~N..HEAD | grep -c "mode change"` and confirm it prints 0 before you push.

If the repo has version management (CHANGELOG.md, release tags), bump the version before pushing.

After confirming the push succeeded, report: GITHUB_URL

Update the command total wherever you record it (for example "7 slash commands" to "8") only when you added a new command. Updating an existing skill doesn't change it.

---

## Appendix: signs a skill shouldn't be open-sourced

- The content was downloaded, adapted, or distilled from someone else's work (a third-party source, regardless of license)
- The skill's core logic depends on personal private data (personal finance, company-confidential data)
- The skill includes a local tool that can't be generalized
- Removing personal info leaves the skill meaningless
- The skill is just automation of a personal SOP with no reference value to others

Keep these in your personal skills folder; no need to open-source them.
