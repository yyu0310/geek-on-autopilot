Recover file content that some operation (e.g. /simplify, an accidental delete, a bad edit) removed or broke, from the Claude Code session log, and restore it safely.

When to use: the user says "some operation broke my file", "/xxx cut out my details", "help me recover what got deleted", "restore it to before the change".

How it works: Claude Code stores the full conversation of every session — including the content of every Read and the old_string/new_string of every Edit — in `~/.claude/projects/<project-slug>/<session-id>.jsonl`, one JSON per line. The original content from before the change is buried in these logs and can be pulled back out.

---

## Step 1: Diagnose — find the culprit session and operation

1. Ask first (if the user didn't say): which file got broken? roughly when? which command or operation caused it?
2. Locate the log directory: the folder under `~/.claude/projects/` matching this project (the folder name is the project's absolute path with `/` replaced by `-`, e.g. a project at `~/code/myrepo` becomes `-Users-you-code-myrepo`).
3. Search for the trigger point. **Key trap: don't grep a bare keyword.**
   - A skill name (like `simplify`) gets injected into every session's skill list, so a bare grep hits almost every session.
   - Match the **actual invocation** instead: `grep -l "command-name>/short-command-name" *.jsonl`, or the record of the file being Edited/Written.
   - **Exclude the current session**: this very conversation will match if you typed that keyword. Judge by timestamp (the last timestamp near now) or line count (just opened) and exclude it.
4. Once located, find the log line number and timestamp of the moment it triggered (e.g. which line `<command-name>/simplify</command-name>` appears on).
5. List every file Edited/Written **after the trigger line** (scan tool_use blocks' file_path with Python).

---

## Step 2: Compare — pull out the original content, separate "fix" from "damage"

**Most important idea: changes before the trigger point in the same session are usually normal work (bug fixes, added detail), not what you want to restore. Only changes after the trigger point are suspects.** Don't blindly roll back the whole thing — you'd kill the good fixes too.

How to pull out the original, by operation type:
- **Overwritten by a full Write**: scan back for the last `tool_result` where that file was Read — it holds the complete original text before the overwrite.
- **Changed/deleted by an Edit**: an Edit's `old_string` = before, `new_string` = after. Collect every Edit after the trigger point and compare what got cut.

Technical details:
- One JSON per log line. `message.content` may be a string or a block array. A `tool_use` block has `name`/`input`/`id`; a `tool_result` block has `tool_use_id`/`content`; pair the two by id.
- A Read's `tool_result` is in `cat -n` format (line number + tab prefix); strip the prefix with regex `^\s*\d+\t(.*)$` before restoring.
- Parse with Python (`json.loads` line by line), and write the recovered original to `/tmp/RESTORE_<filename>` for comparison — don't overwrite directly.

Output: clearly list for the user "content that was in the original and is now gone" (`diff <(original) current`, take the `^<` lines), and which changes are good fixes worth keeping.

---

## Step 3: Edit — plan the restore method

Pick a restore strategy by how bad the damage is. **Prefer surgery over a full overwrite:**
- **Fully emptied out**: if the original already includes the good fixes (the Read you pulled is after the good fixes), a full Write restore loses nothing. Confirm the original structure is intact first (for skill files, note that this project's skills have no YAML frontmatter — the first line is the description, don't lose the opening).
- **Only a few sections cut**: when the current file has both "good fixes" and "cut sections", **use Edit to put just the cut sections back** — don't overwrite the whole file (or you'll roll back the good fixes).
- **Disputed changes** (e.g. "read sequentially" changed to "read in parallel"): ask the user which version they want, don't decide for them.

---

## Step 4: Modify — run the restore and wrap up

1. Before touching anything, back up the recovered original to `/tmp/` (already done in Step 2).
2. Run the Write / Edit restore.
3. Report per file: which sections were restored, which good fixes were kept, which user choices were applied.
4. Wrap-up reminder: the original backup is still in `/tmp/` — clear it or not?
5. If this incident is worth recording (e.g. a certain command breaks a certain kind of file), suggest saving a memory.

---

**Throughout (don't say it, just do it):**
- Restoring overwrites a file and is irreversible — always pull and back up the original first, and show the user a diff before acting.
- Never blindly roll back whole sections; changes before the trigger point are good by default and should be kept.
- When you can't find the original Read, reconstruct from Edit old_strings; when neither exists, honestly say "this part of the log kept no original text, can't restore".
- Don't cross security lines: don't read the log content of forbidden files (if a log contains sensitive file content, treat it the same as the original file's read restrictions).
