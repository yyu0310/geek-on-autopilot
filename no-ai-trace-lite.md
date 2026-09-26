---
name: no-ai-trace-lite
description: Lightweight self-check for internal documents. Runs 3 mechanical greps and 4 quick semantic scans for the most common AI writing traces. Use the full /no-ai-trace for public-facing copy.
---

A lightweight self-check for internal documents. It's the small sibling of `/no-ai-trace`.

Use it on internal working documents that only you and your team read, such as proposals, work logs, architecture notes, and task briefs, right after you write one or rewrite it heavily. For anything public-facing, such as articles, README files, PRs, comments, messages, and talk scripts, run the full `/no-ai-trace` instead. A message to your manager counts as public-facing too, since a third person reads it.

Usage:
- `/no-ai-trace-lite <file path>` checks the given file
- With no path, check the internal document most recently written or heavily edited in this conversation

Steps:

1. Mechanical scan. Actually run the greps and go by their output:

````bash
grep -n "$(printf '\xe2\x80\x94')" "<file>"                                  # em dash, banned in internal docs too
grep -niE "not (just|only|merely) |, not [a-z ]{1,30}, but |不是.{0,15}而是" "<file>"  # negated-premise contrast, English and Chinese
grep -n '^```' "<file>"                                                     # fenced block around non-code content is a violation
````

A fenced block is fine for real code or terminal commands. For everything else, use a list, a table, or an arrow chain.

When you only changed part of an existing file, scan just the new lines so old text doesn't get flagged. For example, run `git diff -U0 "<file>" | grep '^+'` and apply the same patterns to that output. Old violations aren't part of this change. If a line you touched drags an old violation along, fix it while you're there.

2. Quick semantic scan. Look at these four only, not the full 17-rule check:
   - Warm-up opener: does the first paragraph get straight to the point?
   - Overturn narrative: does the text keep an old conclusion and then argue against it? Notes should state only the current correct practice, with a date.
   - Fragment parallelism: several very short sentences stacked for drama.
   - Parenthetical asides: is an explanation stuffed into parentheses? Use a comma or a colon and say it in one flow. Functional parentheses for prices, dates, and links stay.

3. Output (fixed format):
   - First line: "Found N issues", and say it even when N is 0
   - Per issue: rule, line number, original sentence, then the suggested rewrite
   - Judge each contrast hit one by one. Rhetorical emphasis is a violation. Informational use, like defining a scope or explaining a trade-off, isn't, so mark it "keep" and say why.
   - Fix the obvious ones directly. List the doubtful ones for the user to decide.

The full rule set and examples live in `/no-ai-trace`. This command is the mechanical subset plus a few checks for internal documents, so the rules aren't maintained twice.
