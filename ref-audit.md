---
name: ref-audit
description: Reference audit. Before a folder is moved, renamed, or deleted, scan everything that may hard-code its path and produce an audit list so nothing breaks silently.
---

Run this before you move, rename, merge, or delete a folder. It sweeps every place that may hard-code the old path, so you don't discover a dead permission rule, a broken scheduled job, or a dead doc link a week later.

Usage: `/ref-audit projects/old-site` (give several strings if you like, and for a rename give both the old and the new name)

Setup: `ref_audit.py` and `relink.py` live in the repo root. The commands below assume you run them from there. Otherwise, use the full path. Both use only the standard library. The `sed -i ''` syntax below is macOS (BSD sed). On Linux use `sed -i`. The default launchd folder only exists on macOS.

## Steps

1. **Confirm the strings to scan.** Use the path fragment the user gave. For a rename, scan both the old and the new name.

2. **Cover all five domains. Skipping one is how things break.** The domain that bites hardest is usually not the docs.
   - **Project tree** under `--root` (default: current directory): `*.md *.py *.sh *.gs *.json *.plist`, skipping `._*` files, `node_modules`, and `.git`
   - **Claude Code settings**: `<root>/.claude/settings*.json` and `~/.claude/settings*.json`. Permission allowlists hard-code paths, and a move silently invalidates them.
   - **Claude memory**: the project's memory folder, where notes point at paths. The script derives its name from `--root`, but Claude Code names it after the folder you started Claude Code in. If that isn't `--root`, or you're unsure, pass `--memory-dir` explicitly. Otherwise this domain quietly reports no hits.
   - **`~/.claude/commands` symlinks**: where each link points
   - **Schedulers**: `~/Library/LaunchAgents` plists (`com.apple*` skipped), your crontab, and any sync tool's config file (pass it with `--sync-config`). A moved folder that a job or sync tool still points at fails silently.

   Run:

   ```bash
   python3 ref_audit.py "old-name" "new-name" --root /path/to/project --out /path/you/choose/ref_audit_report.md
   ```

   Paste the output into the conversation. Flags: `--no-gs` skips `.gs` files, `--no-launchd` skips the scheduler domain (plists, crontab, sync configs), and `--claude-dir`, `--memory-dir`, and `--launchd-dir` point at non-default locations. Judgment rule for the two skip flags: use them only when the target can't be referenced by an Apps Script file or a scheduled job (a folder of plain notes, say). If scripts or jobs might reference it, leave both flags off.

3. **Write the audit list** to a location the user chooses (`--out`), with the hit count per file. Keep it out of your capture or inbox folders: a mechanical report there is noise.

4. **Classify every hit** as "live file, must update" or "history file, keep as is". Old work logs, archived configs, and the audit list itself usually keep the old path.
   - For `settings.local.json` hits, split two kinds. A **permission rule** such as `Read(...)` is a live file and must be updated. A **one-off command record** such as `Bash(/bin/mv ...)` is history and harmless. The line itself tells you which.

5. **Verify what sed did against the full old path.** When the new path contains the old string (say `drafts` becomes `archive/drafts`), the grep count before and after sed doesn't change, so it looks like nothing was replaced. Grep for the old path including its parent folder, or spot-check the edited content.

6. **Check relative-path rows in config tables by existence, not by string.** A table that lists paths like `scripts/README.md` never mentions the moved folder's name, so name-based mapping misses it and the final grep can't see it. After the move, run `[ -e ]` or `ls` on every row.

## Pitfalls

1. **URL-encoded variants.** A Markdown link writes spaces as `%20`, for example `[Notes](../Q3%20Plan/notes.md)`. If the target name has a space, a plain-string scan misses it and sed won't replace it. `ref_audit.py` searches the `%20` form and the fully percent-encoded form for you. For the replacement, sed both spellings, then re-grep the whole tree at the end. A file that sat in the target list but escaped sed will show up there.

2. **Prefix and shorthand variants.** If the name carries a common prefix or qualifier (`Team Handbook`), docs often cite the shorter form (`Handbook`). Scanning only the full name misses those, and the missed ones tend to be the key live files, such as a design note that says "Handbook folder, stays put" and then misleads the next move. Also scan the core name without the prefix, with the full-name hits removed, and review the difference by hand.

3. **Name collides with a proper noun.** If the folder name is also a platform or product name (a folder `Atlas` and a product called Atlas), most hits mention the product and are not paths. Scan the name first, then scan the full path including the parent (`research/Atlas`, its `%20` form if the name has a space, and `Atlas/subfolder`). Take the live-file decision from the full-path scan. For the extra hits from the name scan, look at one line with `sed -n 'Np'`, confirm it is the proper noun, and move on.

4. **grep that honors `.gitignore`.** Wrappers such as ugrep and ripgrep skip files listed in `.gitignore` by default, so a manual re-grep can call a tree clean when it isn't. Add `--no-ignore-files` (ugrep) or `--no-ignore` (ripgrep), or just rerun `ref_audit.py`: it walks the tree itself and ignores `.gitignore`.

## If you go on to move the folder (after the user confirms)

Follow the safe-move routine:

0. **Rescan if the audit list isn't fresh.** A file written between the audit and the move can reference the old path too, and an old list will miss it.
1. Copy with `cp -R` (not `mv`), then compare file counts between source and destination, excluding `._*`.
2. Edit references file by file with `sed -i ''` (macOS syntax, on Linux use `sed -i`) and print before and after hit counts for each file.
   - **When the move changes folder depth, use `relink.py` instead.** String replacement can't compute the right number of `../` when a subfolder moves up or down a level, or a folder is renamed and moved back. After the move run:

     ```bash
     python3 relink.py --root /path/to/affected/parent --map "/old/abs/path=/new/abs/path" --also /path/to/live/file/outside.md
     ```

     It repairs both directions of breakage: links from other files to the old location, and outgoing links of the moved files. It keeps the `<>` or `%20` style, and `--dry-run` previews the changes.
3. Final check: re-grep the old path, where only the "history, keep as is" list should remain. Then run `python3 relink.py --root /path/to/parent --check`. Broken links must be 0 (exit 4 means some remain). Checking only links that mention the moved folder's name misses links that point at a script file.
4. Only now run `rm -rf` on the source, then verify the destination exists.
5. Update the folder map or index doc, and log the move in the project's work log.
6. While you are at the destination, look for an old folder with the same purpose or an empty shell. A move is the best moment to catch a zombie folder. Check it holds nothing, then clear it and update the index.

## Notes

- `ref_audit.py` reports `file:line` only. It never prints the matched line, so a hit inside a credential-looking file leaks nothing to the terminal or to the `--out` file.
- Scanning is a mechanical, zero-token job in the script. The classification step is judgment work that a mid-size model handles fine.

Exit codes for the scripts: 0 success, 2 external command or I/O failure, 3 file or folder not found, 4 hard gate failed, 5 missing dependency.
