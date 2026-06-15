查詢 Claude 官方文件，回答關於 Claude 功能、API、模型、參數的問題。

官方文件網域：https://platform.claude.com/docs/en/

用法：
- `/claude-docs [問題]` — 查詢指定問題
- `/claude-docs` — 沒有問題時，根據對話上下文判斷要查什麼

步驟：

1. 確認問題方向（從用戶指令或對話上下文中抓取）

2. 根據問題類型選擇優先查詢的頁面（**全部用 platform.claude.com**，不用 docs.anthropic.com）：

   | 問題類型 | 優先查詢 |
   |---|---|
   | **可用性 / 還能不能用 / 被停用 / 存取資格 / 地區限制 / 帳號看不到某模型** | **先 WebSearch + 查 https://www.anthropic.com/news，不要只看 docs 規格頁** |
   | 模型名稱 / 版本 / 能力比較 | https://platform.claude.com/docs/en/docs/about-claude/models/overview |
   | 最新發布 / 新功能 / Release Notes | https://platform.claude.com/docs/en/release-notes/overview |
   | API 參數 / 請求格式 / stop_reason | https://platform.claude.com/docs/en/api/messages |
   | Prompt Caching（5分鐘 / 1小時）| https://platform.claude.com/docs/en/build-with-claude/prompt-caching |
   | Adaptive Thinking / Effort 參數 | https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking |
   | Extended Thinking | https://platform.claude.com/docs/en/build-with-claude/extended-thinking |
   | Tool Use / Function Calling | https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview |
   | Web Search / Web Fetch（內建工具）| https://platform.claude.com/docs/en/agents-and-tools/tool-use/web-search-tool |
   | Computer Use | https://platform.claude.com/docs/en/agents-and-tools/tool-use/computer-use-tool |
   | MCP / MCP Connector | https://platform.claude.com/docs/en/agents-and-tools/mcp-connector |
   | Agent Skills | https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview |
   | Files API | https://platform.claude.com/docs/en/build-with-claude/files |
   | Batch API / Message Batches | https://platform.claude.com/docs/en/build-with-claude/batch-processing |
   | Structured Outputs / JSON | https://platform.claude.com/docs/en/build-with-claude/structured-outputs |
   | Compaction / Context 管理 | https://platform.claude.com/docs/en/build-with-claude/compaction |
   | Citations | https://platform.claude.com/docs/en/build-with-claude/citations |
   | Vision / 圖片輸入 | https://platform.claude.com/docs/en/build-with-claude/vision |
   | PDF 支援 | https://platform.claude.com/docs/en/build-with-claude/pdf-support |
   | Token Counting | https://platform.claude.com/docs/en/build-with-claude/token-counting |
   | Claude Code / CLI / 桌面版 / hooks / skills | https://code.claude.com/docs/en/overview |
   | 所有功能總覽（不確定歸類時先看這頁）| https://platform.claude.com/docs/en/docs/build-with-claude/overview |

   注意：Claude Code 的文件在獨立網域 `code.claude.com/docs`，和 API 文件分開。

   ⚠️ 區分「功能問題」與「可用性問題」：
   - **功能問題**（這個參數怎麼用、這個模型多大 context）→ 查 docs 規格頁。
   - **可用性問題**（還能用嗎、為什麼被 disabled、我這個地區能不能用）→ **docs 規格頁會過時且不寫停用公告，必須改查 news + WebSearch**。
   - **用戶若提供截圖/客戶端畫面**（例如選單顯示某模型 disabled）→ **以客戶端實際狀態為準**，不要用 docs 規格頁反駁用戶眼前看到的事實。

3. 用 WebFetch 直接讀取對應頁面（問題對應多個頁面時，優先讀最相關的一個）

4. 路由表沒涵蓋、或讀到的頁面不對時，先抓官方文件索引找正確頁面：
   - API / 平台類問題：`curl -s https://platform.claude.com/llms.txt | grep -i "關鍵字"`（1680 頁完整索引）
   - Claude Code 類問題：`curl -s https://code.claude.com/docs/llms.txt | grep -i "關鍵字"`
   - 索引也找不到時才用 WebSearch：`site:platform.claude.com [問題關鍵字]`

5. 根據讀到的文件內容直接回答，標注資料來源 URL

6. 如果文件有更新（例如新模型 ID、新參數名稱），和訓練資料不一樣時，以文件為準並主動說明差異

7. 真相層級（衝突時的優先序）：**客戶端實際畫面 / news 即時公告 > docs 規格頁 > 訓練資料**。docs 是規格參考，不是即時可用性的真相來源。
