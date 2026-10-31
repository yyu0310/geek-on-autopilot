Distill and take stock before a session ends. Run these seven blocks in order:

**When several sessions work on the same thing in parallel, distill for all of them.** §1 to §4 should cover every session, not just your own. Take the other sessions' content from the entries they wrote into the project change log. Those entries are the version they already proofread, so don't rely on memory or on a summary of their messages.

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

⚠️ **Anything already on a waiting list, with a confirmed date or check-back day, already on a task list, or already covered by a command's trigger rules is not a loose end. Items this session should have finished go in §3, the rest in §4. Don't move them here to fill space.** If nothing fell out of the system, say "no loose ends this session" and don't force it. That sentence only means nothing fell out of the system, not that everything got done.

Before listing a loose end, grep the task lists and related session logs for a keyword. If it turns up, the item belongs in §3 or §4, not here.

**Sweep for leftovers when something was retired.** If this session deleted or retired something (a spreadsheet, a file, a habit, a workflow), grep the whole project folder for its name and see which documents still treat it as current. List any hit here marked ❓ and ask the user whether to update those too.

## 3. Unfinished in this session

Things this session was supposed to finish and didn't. They get a category of their own. **List them here whether or not they made it into a task list, queue, or handoff file**, because being written into a tracking system only means someone will pick it up, not that it's done.

What counts:
- Tasks taken on in this session, and things the user asked for this turn
- Steps a command says must be done this turn
- Changes made but not verified
- Decisions that wait on the user's reply

Format: bullet points, each as "what | why it isn't done | who does the next step".

Write "everything this session was meant to do is done" only when all of it is done. **Open the report with one line above §1 that gives the count for this category, counted in the 45-line limit**, for example "3 items still unfinished in this session". When this category has content, "no loose ends" is not allowed as the opening conclusion.

## 4. Already-planned items: not this session's job, already accounted for, won't be dropped

Items this session was meant to finish don't go here. They go in §3.

Things not done or not confirmed yet, but **already caught by a system**. List them so the user can relax, and mark clearly that they are not loose ends:
- Already on a waiting list for someone else's reply
- Already has a confirmed date or check-back day
- Already on a task list or schedule
- Already covered by a command's warning section or trigger rule, which fires automatically when the command runs

Format: bullet points, one sentence each: what it is + where it lives now + when it will move.

If there are none, say "no planned items" in one line.

## 5. Memory suggestions

**Principle: project-specific details don't go into memory, only into project files.**

Memory records only these types:
- The user's preferences or habits (user)
- Cross-project feedback (feedback)
- Background the user revealed about themselves (user)
- Index pointers to external resources (reference)

Project progress, decisions, and todos all go into that project's change log, not into memory.
If this session created a new project document: for a small project, skip the memory index, since grep will find it. Only a large cross-project effort gets one, and then memory records just "project name + document path" as an index, without copying the content.

Format: bullet points stating "which memory type to save under" and a one-sentence summary.

If nothing new is worth saving, say "no new memory suggestions this session".

## 6. Project-docs check

If this session changed code or ran technical operations, check whether these files are already up to date:
- The change log (does it record this session's operations and results)
- The architecture doc (do any architecture or logic changes need to be reflected)
- **Whether the related diagrams are current.** For the project you touched and its parent project, find every diagram source file, rendered image, and mermaid block embedded in a document, and check each one for stale state ("planned", "to do", an old schedule, an old machine, an old filename). If one is stale, fix the source, re-render, check it by eye, and update the numbered notes under the diagram too.
- **Sweep for leftovers when a mechanism was replaced.** If this session swapped out an API, a data source, or a tool, grep the whole project folder for the old terms (old endpoint, old function name, old service name) and update every document that still describes the old way. A design document can be missed even after the change log and the architecture doc were both updated.
- **When you fix a bug, sweep for the same cause.** If this session fixed a root cause (permissions, a path, a credential location, an API limit), grep other programs in the same environment for the same pattern and confirm none of them hit it too. If one did, list it in §2. Also check the other branches in the same program that make the same kind of decision: grep every place in the file where that decision is made, because fixing only one leaves an identical bug behind.
- **When you overturn an earlier conclusion, fix the rule that produced the wrong one.** If this session corrected a previous judgment, don't stop at the case file and the change log. Find where the rule that led to the wrong call is written and fix that too. Fixing only the case file leaves the source intact, and the next case gets misjudged the same way.

Format:
- ✅ updated / ⬜ not updated / n/a: no code changes this session (no update needed)

If a file isn't updated, name it directly and say what's missing instead of just saying "consider updating".

## 7. QA evidence check

If this session wrote or changed code, including personal scripts that never go to GitHub, list each piece and whether it has QA evidence:

- ✅ QA'd: the real command was run and the output was kept
- ⚠️ Not QA'd: written but never tested. Name it directly, remind the user to run real tests now, and list it in §3

If no code was written, say "no code this session, skipped". Don't let through any "wrote it, said it works, never ran it" case.

---

Output language follows the language the user used this session. The seven blocks plus the opening line stay under 45 lines.
