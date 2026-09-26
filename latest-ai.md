---
name: latest-ai
description: Answer frontier-AI questions or compile a past-week product roundup by pulling from each AI company's official docs, news pages, and changelogs.
---

Pull from the primary, official sources of each AI company (docs, blog, release notes, official X accounts) to answer frontier-AI questions or summarize recent product news. It sits alongside two sibling commands: `/latest` handles general time-sensitive search, `/claude-docs` handles Claude only, and `/latest-ai` covers every other vendor plus cross-vendor roundups. It only looks at the companies in the tables below and always goes back to the primary source.

Usage:
- `/latest-ai [question]` looks up the answer in the official sources of the relevant companies. This is the common case.
- `/latest-ai` with no question compiles product updates and news from the **past week**. Scan Tier 1 first and include Tier 2 only when there's real news.

Core principles (same as `/latest`):
- Training data has a cutoff and AI changes weekly. Treat anything you remember as a **stale candidate** and check before answering, even when you feel sure.
- Only primary sources count: official docs, official blog, release notes, official X accounts, official GitHub. Secondary sources (news, forums, tutorials) can add context, but confirm every conclusion against a primary source.
- If the question is really about Claude's own features, use `/claude-docs` instead.
- URLs in the tables change over time. When one returns a 404 or looks stale, WebSearch `[company name] official blog` or `[company name] official docs` to find the new location, then update this table.

## Company source routing table

### Tier 1: always scan

| Company / product | Official blog / news | Official docs | Official X | Notes |
|---|---|---|---|---|
| **xAI / Grok** | https://x.ai/news | https://docs.x.ai | @xai @grok | Grok product news often lands on X first |
| **OpenAI / ChatGPT / Codex** | https://openai.com/news/ | https://platform.openai.com/docs | @OpenAI @OpenAIDevs | ChatGPT release notes: search "release notes" on help.openai.com. Codex: openai.com/codex |
| **Google / Gemini** | https://blog.google/technology/ai/ and https://deepmind.google/discover/blog/ | https://ai.google.dev | @GoogleDeepMind @GoogleAIStudio | Docs cover the Gemini API. The agentic IDE Antigravity lives at https://antigravity.google |
| **DeepSeek** | https://api-docs.deepseek.com/news | https://api-docs.deepseek.com | @deepseek_ai | Model releases mostly appear on GitHub and X |
| **Apple** | https://www.apple.com/newsroom/ and https://machinelearning.apple.com | none | @Apple | Apple Intelligence and Siri news mostly comes through the Newsroom and WWDC |
| **Qwen / Alibaba** | https://qwenlm.github.io/blog/ | https://help.aliyun.com | @Alibaba_Qwen | Docs cover the Bailian / DashScope API. Chat entry point: chat.qwen.ai |
| **Zhipu Z.ai / GLM** | https://z.ai/blog | https://docs.z.ai | @Zai_org | Open weights on Hugging Face under `zai-org` |
| **Meta AI** | https://ai.meta.com/blog/ and https://llama.com | none | @AIatMeta | Covers Meta's model families and open-weight releases |
| **Cross-vendor comparison sites** | Artificial Analysis https://artificialanalysis.ai, Hugging Face Open LLM Leaderboard, Epoch AI https://epoch.ai | none | @ArtificialAnlys | Use these for cross-vendor capability and price-performance comparisons |

### Tier 2: check when clearly relevant, or when the weekly roundup has news

| Company / product | Official blog / news | Official X |
|---|---|---|
| **MiniMax** | https://www.minimax.io/news, docs at minimax.io/platform | @MiniMax__AI |
| **Moonshot / Kimi** | https://moonshot.ai and https://kimi.ai, docs at platform.kimi.ai/docs | @Kimi_Moonshot |
| **NVIDIA Nemotron** | https://research.nvidia.com/labs/nemotron/ and https://nvidianews.nvidia.com | @nvidia |
| **Manus** | https://manus.im/blog | @ManusAI_HQ |
| **Cursor** | https://cursor.com/changelog and https://cursor.com/blog | @cursor_ai |
| **Perplexity** | https://www.perplexity.ai/hub/blog | @perplexity_ai |

## Steps

### A. With a question (`/latest-ai [question]`)

1. Work out which company or companies the question touches. It can span several, for example "which is stronger, the latest Gemini or the latest GPT" points to Google, OpenAI, and a comparison site.
2. Go straight to that company's official sources:
   - WebFetch the relevant official blog, release notes, or docs page and look for the changelog or "what's new" section.
   - For models and tools hosted on GitHub, WebFetch the repo's README and Releases page.
   - When there's no obvious target page, WebSearch `[company] [keyword]` with the current year, but always land the conclusion on a primary source.
3. Search from at least 2 angles. Products get renamed often and a single keyword will miss things.
4. Every answer includes the **conclusion, the information date (when it was published or updated), and the source URL**. Flag any difference from what your training data says.
5. If the official sources have nothing clear, say so plainly. Don't fill the gap from training data.

### B. Without a question (`/latest-ai`): past-week roundup

1. Scan the official blog, news page, and release notes of each Tier 1 company for anything published in the **last 7 days**: new models, new features, API changes, pricing.
2. Include Tier 2 only when there's clearly big news.
3. Write each item as one line: **Company, one-sentence takeaway (date), source URL**. Tier 1 goes first.
4. Leave out companies with nothing new. Don't pad the list.
5. Close with one sentence naming the single most notable item of the week.
