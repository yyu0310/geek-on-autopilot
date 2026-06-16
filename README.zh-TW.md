[English](README.md) | 繁體中文 | [简体中文](README.zh-CN.md)

# geek-on-autopilot

五個讓 Claude Code 更順手的自訂斜線指令。

## 解決的問題

- AI 訓練資料有截止日，時效敏感的問題答案不可靠
- Claude 官方文件更新快，不知道去哪查
- AI 寫出來的文字有 AI 味，需要人工打磨
- Session 結束後不知道自己做了什麼，沒有留下記錄
- Marp 簡報匯出前沒有統一的 QA 流程

## 指令一覽

| 指令 | 功能 |
|---|---|
| `/latest` | 強制網搜，禁止只靠訓練資料回答時效問題 |
| `/claude-docs` | 路由直達 Claude 官方文件，附來源 URL |
| `/no-ai-trace` | 掃描 AI 寫作痕跡，17 條規則逐條檢查 |
| `/session-review` | Session 收尾四區塊盤點，35 行以內 |
| `/marp-export` | Marp 簡報 QA 檢查後匯出 PDF |
| `/open-source-skill` | 資安掃描、清理、推入開源 repo 全流程 |

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

## 授權

MIT
