Answer questions from live information on the web. Never rely on training data alone. Use this for anything time-sensitive: frontier AI, tool feature changes, version support, pricing.

Usage:
- `/latest [question]` — search the given question
- `/latest` — with no question, the target is the most recent time-sensitive question in the conversation

Core principles:
- Training data has a cutoff. AI tools, models, and APIs change almost weekly, so **treat any answer from training data as a stale candidate, not the conclusion.**
- Even when you think you know the answer, search and verify before you reply.
- For questions about Claude's own features, route to `/claude-docs` and its official-docs path instead.

Steps:

1. Break the question down and list the time-sensitive points to verify (version numbers, support status, pricing, whether something shipped, whether something is deprecated).

2. When the question is about a specific tool or product, **go straight to its official docs** instead of a generic web search:
   - Find where the official docs live (if unsure, WebSearch `[tool name] official docs`).
   - Try fetching `[docs site]/llms.txt`. Many modern docs sites publish this index; grep a keyword to jump straight to the right page.
   - Use WebFetch to read the matching docs page; look for the changelog / release notes / what's new section.
   - For tools on GitHub, WebFetch the repo's README / CHANGELOG / Releases page.

3. When there's no clear target doc, or the docs aren't current enough, fill in with WebSearch. Keyword strategy:
   - Add the current year or "latest" to filter out old articles.
   - Prefer primary sources: official docs, official blog, GitHub repo, official X account.
   - Use secondary sources (news, forums, tutorials) only to supplement; confirm the conclusion against a primary source.
   - Search from at least 2 angles for the same question so a single keyword doesn't miss a new name (products get renamed often).

4. Every answer includes:
   - The conclusion (based on the latest information found).
   - The date of the information (when this feature or version shipped or was last updated).
   - The source URL.
   - If it differs from what training data suggested, flag the difference ("I previously assumed X, but the latest docs show Y").

5. When you can't find a definite answer, say so honestly ("I couldn't find clear information online"). Don't fall back on training data to fill the gap.
