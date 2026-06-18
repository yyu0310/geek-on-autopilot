[English](README.md) | 繁體中文 | [简体中文](README.zh-CN.md)

# geek-on-autopilot

五個讓 Claude Code 更順手的自訂斜線指令。

## 解決的問題

- AI 訓練資料有截止日，時效敏感的問題答案不可靠
- Claude 官方文件更新快，不知道去哪查
- AI 寫出來的文字有 AI 味，需要人工打磨
- Session 結束後不知道自己做了什麼，沒有留下記錄
- Marp 簡報匯出前沒有統一的 QA 流程
- Pandoc 預設字體不支援中英混排，輸出 PDF 字體很醜

## 指令一覽

| 指令 | 功能 |
|---|---|
| `/latest` | 強制網搜，禁止只靠訓練資料回答時效問題 |
| `/claude-docs` | 路由直達 Claude 官方文件，附來源 URL |
| `/no-ai-trace` | 掃描 AI 寫作痕跡，17 條規則逐條檢查 |
| `/session-review` | Session 收尾四區塊盤點，35 行以內 |
| `/marp-export` | Marp 簡報 QA 檢查後匯出 PDF |
| `/open-source-skill` | 資安掃描、清理、推入開源 repo 全流程 |
| `/md-to-pdf` | MD 轉 PDF，套用 PingFang TC 字體模板 |
| `/recover-from-log` | 從 session log 救回被改壞或誤刪的檔案內容 |

## 安裝

需要 [Claude Code](https://claude.ai/code)。

```bash
git clone https://github.com/yyu0310/geek-on-autopilot.git
cd geek-on-autopilot

# 安裝全部指令
for f in *.md; do
  ln -sf "$(pwd)/$f" ~/.claude/commands/"$f"
done
```

只裝需要的：

```bash
ln -sf "$(pwd)/latest.md" ~/.claude/commands/latest.md
```

安裝後在 Claude Code 輸入 `/latest`、`/claude-docs` 等即可使用。

## 指令說明

### `/latest`

強制網搜回答時效敏感問題。AI 的訓練資料有截止日，AI 前沿技術、版本支援性、API 異動等問題，訓練資料裡的答案視為過時候選，不是結論。

```
/latest Claude Code 最新版本有什麼新功能？
```

---

### `/claude-docs`

根據問題類型，直接取得對應的 Claude 官方文件頁面，附來源 URL。路由表涵蓋 API 參數、模型規格、Prompt Caching、Tool Use、MCP、Agent Skills 等 20+ 個主題。

```
/claude-docs prompt caching 怎麼用？
/claude-docs 最新模型有哪些？
```

---

### `/no-ai-trace`

掃描文案的 AI 寫作痕跡。根據 17 條規則逐條檢查，列出違規原句和建議改法，最後給語氣總評。

```
/no-ai-trace                    # 檢查對話中最近一次的文案
/no-ai-trace [貼上要檢查的文字]
```

17 條規則涵蓋：術語堆疊、否定前提句、能力名詞化、破折號濫用、自問自答、過渡詞、碎句排比等常見 AI 寫作痕跡。

---

### `/session-review`

Claude Code session 結束前的四區塊盤點：

1. **精華蒸餾** — 本次的重要決策、新知識點、值得記住的洞察（最多 8 條）
2. **遺漏事項** — 對話中提到但沒有完成的事（⬜ 待執行 / ❓ 待確認）
3. **Memory 建議** — 哪些值得存進 Claude 的記憶系統
4. **文檔檢查** — 程式碼有改動的話，相關文件是否已同步更新

全部輸出在 35 行以內。

---

### `/marp-export`

Marp 簡報交稿前 QA + 匯出 PDF：

1. 掃草稿標記（`【`開頭的備注），有的話等確認清掉
2. 確認 `assets/` 圖片都存在
3. 匯出 PDF，回報路徑與檔案大小

需要：Node.js（用 `npx` 執行 `@marp-team/marp-cli`）

```
/marp-export                   # 匯出 IDE 當前開啟的 .md 檔
/marp-export /path/to/file.md
```

---

### `/open-source-skill`

把個人 skill 開源的完整 SOP。自動掃描個人路徑、帳號識別符、外部依賴等六類資安問題，列出問題等確認，清理後更新三語 README 和 llms.txt，最後 commit + push。

需要一次性設定：在 skill 檔頂部填入你的 repo 本地路徑和 GitHub URL。

```
/open-source-skill session-review
/open-source-skill                  # 從 IDE 當前開啟的 skill 開始
```

---

### `/md-to-pdf`

把 Markdown 檔轉成 PDF，字體用 PingFang TC（蘋方-繁）。PingFang TC 是中英混排 PDF 渲染 bug 最少的字體，Mac 生態免費內建，Windows / Linux 需另購。流程是兩步：先用 pandoc 轉 DOCX，再用 LibreOffice 轉 PDF。轉換前會先掃格式陷阱（序號列表前是否有空行），避免 pandoc 解析出錯。`reference_pingfang.docx` 字體模板已包含在 repo 中，clone 後設定一個路徑即可使用。

全程本地轉換，不依賴任何第三方服務，文件內容不會傳出去，適合有隱私顧慮的工作文件。

需要：pandoc、LibreOffice（`brew install pandoc && brew install --cask libreoffice`）

```
/md-to-pdf                    # 轉換 IDE 當前開啟的 .md 檔
/md-to-pdf /path/to/file.md
```

---

### `/recover-from-log`

當 Claude Code 的某次操作（`/simplify`、誤刪、誤改）把檔案弄壞時，從 session log 撈回原始內容還原。每個 session 的 `.jsonl` 都存了完整對話，包含每次 Read 過的檔案原文和每次 Edit 的 `old_string`，被改之前的版本還在裡面。skill 會診斷是哪個 session、哪次操作造成的，撈出原版，外科手術式還原：保留好的修正，而不是無腦整段回退。

它也處理一個尖銳的陷阱。skill 名稱（例如 `simplify`）會被注入到每個 session 的 skill 清單，裸 grep 幾乎會比中所有 session。這個 skill 改成比中實際的指令呼叫，並排除當前 session，才鎖定真正的兇手。

```
/recover-from-log [檔名]
```

## 授權

MIT
