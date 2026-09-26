---
name: latest-ai
description: 從各家 AI 公司的官方文件、官方消息與 changelog 抓一手資訊，回答 AI 前沿問題或彙整近一週產品更新。
---

專門從各家 AI 公司的一手官方來源（官方文件、blog、release notes、官方 X 帳號）抓資訊，回答 AI 前沿問題或彙整近期產品動態。它和兩個同系列指令並列：`/latest` 管通用的時效搜尋，`/claude-docs` 專管 Claude，`/latest-ai` 管其他各家與跨家彙整。這支只看下面清單裡的公司，且一律回到一手來源。

用法：
- `/latest-ai [問題]`：鎖定相關公司的官方來源查答案，最常見。
- `/latest-ai`：沒帶問題時，彙整**近一週**的產品更新與新消息。Tier 1 優先，Tier 2 有料才收。

核心原則（同 `/latest`）：
- 訓練資料有截止日，AI 領域每週都在變。腦中的答案一律當**過時候選**，自認知道也要先查再答。
- 只認一手來源：官方文件、官方 blog、release notes、官方 X 帳號、官方 GitHub。二手來源（新聞、論壇、教學）只補充背景，結論要回到一手來源確認。
- 如果問題其實是 Claude 自家功能，改用 `/claude-docs`。
- 下表 URL 可能改版。遇到 404 或明顯過時，先 WebSearch `[公司名] official blog` 或 `[公司名] official docs` 重新定位，再更新這張表。

## 公司來源路由表

### Tier 1：一定掃

| 公司 / 產品 | 官方 blog / news | 官方文件 | 官方 X | 備註 |
|---|---|---|---|---|
| **xAI / Grok** | https://x.ai/news | https://docs.x.ai | @xai @grok | Grok 產品消息常先在 X 平台公布 |
| **OpenAI / ChatGPT / Codex** | https://openai.com/news/ | https://platform.openai.com/docs | @OpenAI @OpenAIDevs | ChatGPT release notes：在 help.openai.com 搜「release notes」。Codex：openai.com/codex |
| **Google / Gemini** | https://blog.google/technology/ai/ 與 https://deepmind.google/discover/blog/ | https://ai.google.dev | @GoogleDeepMind @GoogleAIStudio | 文件為 Gemini API。agentic IDE Antigravity 在 https://antigravity.google |
| **DeepSeek** | https://api-docs.deepseek.com/news | https://api-docs.deepseek.com | @deepseek_ai | 模型發布多在 GitHub 與 X |
| **Apple** | https://www.apple.com/newsroom/ 與 https://machinelearning.apple.com | 無 | @Apple | Apple Intelligence 與 Siri 動態多經由 Newsroom 與 WWDC 發布 |
| **Qwen / 千問 / 阿里巴巴** | https://qwenlm.github.io/blog/ | https://help.aliyun.com | @Alibaba_Qwen | 文件為百煉 / DashScope API。聊天入口：chat.qwen.ai |
| **智譜 Z.ai / GLM** | https://z.ai/blog | https://docs.z.ai | @Zai_org | 開源權重在 Hugging Face 的 `zai-org` |
| **Meta AI** | https://ai.meta.com/blog/ 與 https://llama.com | 無 | @AIatMeta | 涵蓋 Meta 的模型系列與開源權重發布 |
| **跨家比較平台** | Artificial Analysis https://artificialanalysis.ai、Hugging Face Open LLM Leaderboard、Epoch AI https://epoch.ai | 無 | @ArtificialAnlys | 用來做跨家能力與性價比對照 |

### Tier 2：有明確相關才查，週報有料才收

| 公司 / 產品 | 官方 blog / news | 官方 X |
|---|---|---|
| **MiniMax** | https://www.minimax.io/news，文件在 minimax.io/platform | @MiniMax__AI |
| **Moonshot / Kimi** | https://moonshot.ai 與 https://kimi.ai，文件在 platform.kimi.ai/docs | @Kimi_Moonshot |
| **NVIDIA Nemotron** | https://research.nvidia.com/labs/nemotron/ 與 https://nvidianews.nvidia.com | @nvidia |
| **Manus** | https://manus.im/blog | @ManusAI_HQ |
| **Cursor** | https://cursor.com/changelog 與 https://cursor.com/blog | @cursor_ai |
| **Perplexity** | https://www.perplexity.ai/hub/blog | @perplexity_ai |

## 步驟

### A. 帶問題（`/latest-ai [問題]`）

1. 判斷問題命中哪家或哪幾家公司。問題可以跨家，例如「最新的 Gemini 和最新的 GPT 誰比較強」對應 Google、OpenAI 加比較平台。
2. 直奔該公司的官方來源：
   - 先 WebFetch 官方 blog、release notes 或文件的對應頁面，找 changelog 或 what's new。
   - GitHub 上的模型或工具，WebFetch repo 的 README 與 Releases。
   - 找不到明確目標頁時，WebSearch `[公司] [關鍵字]` 並帶上當年年份，但結論一定回到一手來源。
3. 至少換 2 個角度搜尋。產品常改名，單一關鍵字會漏。
4. 回答固定包含：**結論、資訊日期（何時發布或更新）、來源 URL**。和訓練資料的認知不同時，要主動標出差異。
5. 官方來源查不到明確資訊就直接說查不到，不用訓練資料補。

### B. 不帶問題（`/latest-ai`）：近一週彙整

1. 逐一掃 Tier 1 各家的官方 blog、news、release notes，抓**近 7 天**內的發布：新模型、新功能、API 變更、定價。
2. Tier 2 只在有明顯大新聞時才收。
3. 每則彙整成一行：**公司、一句話重點（日期）、來源 URL**，Tier 1 排前面。
4. 沒有新東西的公司直接省略，不硬湊。
5. 結尾補一句本週最值得注意的一項。
