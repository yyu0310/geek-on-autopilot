[English](README.md) | 繁體中文 | [简体中文](README.zh-CN.md)

# geek-on-autopilot

十二個讓 Claude Code 更順手的自訂斜線指令。

## 解決的問題

- AI 訓練資料有截止日，時效敏感的問題答案不可靠
- Claude 官方文件更新快，不知道去哪查
- 其他 AI 廠商也每週更新，消息散在部落格、文件與更新日誌裡
- AI 寫出來的文字有 AI 味，需要人工打磨
- 中文文案有 AI 味，英文規則掃不出來
- Session 結束後不知道自己做了什麼，沒有留下記錄
- Marp 簡報匯出前沒有統一的 QA 流程
- Pandoc 預設字體不支援中英混排，輸出 PDF 字體很醜
- AI 回答醫療問題會自信地幻覺，又沒有權威來源可查

## 指令一覽

| 指令 | 功能 |
|---|---|
| `/latest` | 強制網搜，禁止只靠訓練資料回答時效問題 |
| `/claude-docs` | 路由直達 Claude 官方文件，附來源 URL |
| `/latest-ai` | 查 Claude 以外的 AI 廠商官方消息，或整理近一週更新 |
| `/no-ai-trace` | 掃描 AI 寫作痕跡，17 條規則逐條檢查 |
| `/no-ai-trace-lite` | 內部文件用，3 項 grep 加 4 項快掃 |
| `/no-ai-trace-zh` | 中文文案專用的 AI 痕跡檢查 |
| `/session-review` | Session 收尾六區塊盤點，45 行以內 |
| `/marp-export` | Marp 簡報 QA、匯出 PDF、驗收輸出 |
| `/open-source-skill` | 資安掃描、清理、推入開源 repo 全流程 |
| `/md-to-pdf` | MD 轉 PDF，套用 PingFang TC 字體模板 |
| `/recover-from-log` | 從 session log 救回被改壞或誤刪的檔案內容 |
| `/med-check` | 醫療問題查權威文獻作答，禁用訓練資料 |

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

`/md-to-pdf` 與 `/marp-export` 會呼叫 repo 根目錄的 Python 腳本（`md2pdf.py`、`marp_export.py`），clone 下來的資料夾請留在原位，指令會從那裡執行腳本。

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

### `/latest-ai`

從各家 AI 公司的官方文件、新聞頁與更新日誌回答前沿 AI 問題，不靠訓練資料。`/claude-docs` 管 Claude，`/latest-ai` 管其他所有廠商與跨家彙整。給問題就路由到相關公司的官方來源，不給問題就整理近一週的產品更新，先掃主要廠商。

```
/latest-ai OpenAI 這個月有調整 API 價格嗎？
/latest-ai                     # 近一週彙整
```

---

### `/no-ai-trace`、`/no-ai-trace-lite`、`/no-ai-trace-zh`

三支 AI 寫作痕跡檢查器，依你手上的文字類型挑一支：

| 指令 | 適用 | 檢查方式 |
|---|---|---|
| `/no-ai-trace` | 對外英文文案：README、貼文、PR、信件 | 17 條規則，列出違規原句與建議改法，最後給語氣總評 |
| `/no-ai-trace-lite` | 內部工作文件：提案、日誌、架構說明 | 3 項機械 grep 加 4 項語意快掃，每次改完都能快速跑 |
| `/no-ai-trace-zh` | 中文文案 | Z1 到 Z11 中文專屬規則，如元敘事標籤、否定前提對比、翻譯腔，另含基本檢查 |

```
/no-ai-trace                    # 檢查對話中最近一次的文案
/no-ai-trace [貼上要檢查的文字]
/no-ai-trace-lite docs/proposal.md
/no-ai-trace-zh [貼上要檢查的中文]
```

`/no-ai-trace` 的 17 條規則涵蓋：術語堆疊、否定前提句、能力名詞化、破折號與分號、自問自答、過渡詞、碎句排比等常見 AI 寫作痕跡。

---

### `/session-review`

Claude Code session 結束前的六區塊盤點：

1. **精華蒸餾**：本次的重要決策、新知識點、值得記住的洞察（最多 8 條）
2. **遺漏事項**：只抓真正掉出所有追蹤系統的事（⬜ 待執行 / ❓ 待確認）
3. **已規劃事項**：未完成但已有歸屬的事，明確標示不算遺漏
4. **Memory 建議**：哪些值得存進 Claude 的記憶系統
5. **文檔檢查**：程式碼有改動的話，相關文件是否已同步更新
6. **QA 證據盤點**：有寫程式的話，有沒有跑過實際指令並留有輸出

全部輸出在 45 行以內。多個 session 平行做同一件事時，會一起蒸餾。

---

### `/marp-export`

Marp 簡報交稿前 QA 加匯出 PDF，由 repo 根目錄的 `marp_export.py` 執行：

1. `qa` 掃草稿標記（`TODO`、`FIXME`、`TBD`、`XXX` 與 `【` 括號），並確認本機圖片都存在
2. `export` 用 `npx` 與 `@marp-team/marp-cli` 產出 PDF
3. `verify` 確認 PDF 存在、不是空檔，且比原始檔新

需要：Node.js 與 Python 3

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

把 Markdown 檔轉成 PDF，字體用 PingFang TC（蘋方-繁）。PingFang TC 是中英混排 PDF 渲染 bug 最少的字體，Mac 生態免費內建，Windows / Linux 需另購。repo 根目錄的 `md2pdf.py` 執行整條流程：先 lint 掃 pandoc 已知陷阱，再用 pandoc 搭配隨附的 `reference_pingfang.docx` 模板轉 DOCX，接著用 LibreOffice 轉 PDF，最後用 `pdffonts` 檢查，直到所有字體都是 PingFang TC 才放行。另有 `--strip` 輸出不分頁的長條版，以及 `wordcount` 字數上限檢查。

全程本地轉換，不依賴任何第三方服務，文件內容不會傳出去，適合有隱私顧慮的工作文件。這個工具針對中文與中英混合文件，純英文檔案會過不了字體檢查。

需要：Python 3、pandoc、LibreOffice、poppler（`brew install pandoc poppler && brew install --cask libreoffice`）

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

---

### `/med-check`

回答醫療/健康問題時，強迫用權威醫界文獻作答，而不是會在健康主題上危險幻覺的訓練資料。強制「先檢索再回答」的流程：Cochrane 系統性回顧、臨床指引、PubMed 原始研究（走免費 E-utilities API，無需金鑰）、WHO/CDC/FDA/NIH 等權威衛生機構。每個結論標證據等級（有實證／證據不足／互相矛盾）、標不確定性、附 PMID 引用；查不到就老實說查不到，絕不腦補。它會先攔急症紅旗症狀並提醒就醫。

此為文獻整理輔助，非醫療診斷。

```
/med-check [你的健康問題]
/med-check                     # 用對話中最近一個健康問題
```

## 授權

MIT
