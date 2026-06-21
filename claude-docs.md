Look up the official Claude docs to answer questions about Claude's features, API, models, and parameters.

Official docs domain: https://platform.claude.com/docs/en/

Usage:
- `/claude-docs [question]` — look up the given question
- `/claude-docs` — with no question, infer what to look up from the conversation context

Steps:

1. Confirm the direction of the question (from the user's command or the conversation context).

2. Pick the page to check first based on the question type (**always use platform.claude.com**, not docs.anthropic.com):

   | Question type | Check first |
   |---|---|
   | **Availability / is it still usable / disabled / access eligibility / regional limits / a model missing from my account** | **WebSearch first + check https://www.anthropic.com/news; don't rely on the docs spec pages alone** |
   | Model names / versions / capability comparison | https://platform.claude.com/docs/en/docs/about-claude/models/overview |
   | Latest releases / new features / release notes | https://platform.claude.com/docs/en/release-notes/overview |
   | API parameters / request format / stop_reason | https://platform.claude.com/docs/en/api/messages |
   | Prompt Caching (5-minute / 1-hour) | https://platform.claude.com/docs/en/build-with-claude/prompt-caching |
   | Adaptive Thinking / Effort parameter | https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking |
   | Extended Thinking | https://platform.claude.com/docs/en/build-with-claude/extended-thinking |
   | Tool Use / Function Calling | https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview |
   | Web Search / Web Fetch (built-in tools) | https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool |
   | Computer Use | https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool |
   | MCP / MCP Connector | https://platform.claude.com/docs/en/agents-and-tools/mcp-connector |
   | Agent Skills | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview |
   | Files API | https://platform.claude.com/docs/en/build-with-claude/files |
   | Batch API / Message Batches | https://platform.claude.com/docs/en/build-with-claude/batch-processing |
   | Structured Outputs / JSON | https://platform.claude.com/docs/en/build-with-claude/structured-outputs |
   | Compaction / Context management | https://platform.claude.com/docs/en/build-with-claude/compaction |
   | Citations | https://platform.claude.com/docs/en/build-with-claude/citations |
   | Vision / image input | https://platform.claude.com/docs/en/build-with-claude/vision |
   | PDF support | https://platform.claude.com/docs/en/build-with-claude/pdf-support |
   | Token Counting | https://platform.claude.com/docs/en/build-with-claude/token-counting |
   | Claude Code / CLI / desktop app / hooks / skills | https://code.claude.com/docs/en/overview |
   | Overview of all features (start here when unsure how to classify) | https://platform.claude.com/docs/en/docs/build-with-claude/overview |

   Note: the Claude Code docs live on a separate domain, `code.claude.com/docs`, apart from the API docs.

   ⚠️ Tell a "feature question" apart from an "availability question":
   - **Feature question** (how to use this parameter, how large is this model's context) → check the docs spec page.
   - **Availability question** (is it still usable, why is it disabled, is it available in my region) → **the docs spec pages go stale and don't post deprecation notices; check news + WebSearch instead**.
   - **If the user provides a screenshot / client view** (e.g. a menu showing a model as disabled) → **trust the actual client state**; don't use the docs spec page to argue against what the user sees in front of them.

3. Use WebFetch to read the matching page directly (when a question maps to several pages, read the most relevant one first).

4. When the routing table doesn't cover it, or the page you read is wrong, fetch the official docs index first to find the right page:
   - API / platform questions: `curl -s https://platform.claude.com/llms.txt | grep -i "keyword"` (full index of ~1680 pages)
   - Claude Code questions: `curl -s https://code.claude.com/docs/llms.txt | grep -i "keyword"`
   - Only when the index doesn't find it either, use WebSearch: `site:platform.claude.com [question keyword]`

5. Answer directly from the docs content you read, citing the source URL.

6. If the docs have been updated (e.g. a new model ID or a renamed parameter) and differ from training data, go with the docs and flag the difference.

7. Truth hierarchy (priority when sources conflict): **the actual client view / live news announcements > docs spec pages > training data**. The docs are a spec reference, not the source of truth for live availability.
