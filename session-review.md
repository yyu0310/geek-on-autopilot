Distill and take stock before a session ends. Run these six blocks in order:

**When several sessions work on the same thing in parallel, distill for all of them.** §1 to §3 should cover every session. Take the other sessions' content from the entries they wrote into the project change log. Those entries are the version they already proofread, so don't rely on memory or on a summary of their messages.

## 1. Distill the essentials

Review the whole conversation and extract:
- The important **decisions** made this session (what was chosen, what was rejected)
- **Knowledge** newly learned or confirmed (tools, methods, rules)
- **Insights** that affect future work

Format: bullet points, one sentence each, no more than 8 items.

## 2. Take stock of loose ends: only what truly fell out of the system

List only things that are **undone and not in any tracking system**: not on a waiting list, not on a task list, and with no known check-back date. Those are the ones that will actually get dropped.
- Tasks where a direction was discussed but nothing landed and nothing was recorded
- A "do it later" from the user that no system caught

Format: bullet points, each marked "⬜ to do" or "❓ to confirm", plus one line on which system it should go into.

⚠️ **Anything already on a waiting list, with a confirmed date or check-back day, already on a task list, or already covered by a command's trigger rules is not a loose end. Put it in §3 and don't move it here to fill space.** If nothing fell out of the system, say "no loose ends this session" and don't force it.

## 3. Already-planned items: unfinished but accounted for, so they won't be dropped

Things not done or not confirmed yet, but **already caught by a system**. List them so the user can relax, and mark clearly that they are not loose ends:
- Already on a waiting list for someone else's reply
- Already has a confirmed date or check-back day
- Already on a task list or schedule
- Already covered by a command's warning section or trigger rule, which fires automatically when the command runs

Format: bullet points, one sentence each: what it is + where it lives now + when it will move.

If there are none, say "no planned items" in one line.

## 4. Memory suggestions

**Principle: project-specific details don't go into memory, only into project files.**

Memory records only these types:
- The user's preferences or habits (user)
- Cross-project feedback (feedback)
- Background the user revealed about themselves (user)
- Index pointers to external resources (reference)

Project progress, decisions, and todos all go into that project's change log, not into memory.
If this session created a new project document, memory records only "project name + document path" as an index, without copying the content.

Format: bullet points stating "which memory type to save under" and a one-sentence summary.

If nothing new is worth saving, say "no new memory suggestions this session".

## 5. Project-docs check

If this session changed code or ran technical operations, check whether these files are already up to date:
- The change log (does it record this session's operations and results)
- The architecture doc (do any architecture or logic changes need to be reflected)

Format:
- ✅ updated / ⬜ not updated / n/a: no code changes this session (no update needed)

If a file isn't updated, name it directly and say what's missing instead of just saying "consider updating".

## 6. QA evidence check

If this session wrote or changed code, including personal scripts that never go to GitHub, list each piece and whether it has QA evidence:

- ✅ QA'd: the real command was run and the output was kept
- ⚠️ Not QA'd: written but never tested. Name it directly and remind the user to run real tests now

If no code was written, say "no code this session, skipped". Don't let through any "wrote it, said it works, never ran it" case.

---

Output language follows the language the user used this session. The six blocks together stay under 45 lines.
