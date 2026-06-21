將個人 skill 整理開源，加入你的 geek-on-autopilot repo。

⚙️ 使用前一次性設定：把下方三個佔位符替換成你的實際值，存檔後即可使用。

```
REPO_LOCAL_PATH  = /your/local/path/to/geek-on-autopilot/
GITHUB_URL       = https://github.com/YOUR_USERNAME/geek-on-autopilot
SKILL_DIR        = /your/local/path/to/your/skills/folder/
```

用法：
- `/open-source-skill [skill 名稱]` — 在 SKILL_DIR 尋找對應 .md
- `/open-source-skill` — 從 IDE 當前開啟的 skill 檔開始

---

## Step 0：開源適合性評估

掃描前先確認這個 skill 值得開源：

- 對其他用戶是否有獨立價值？（不依賴個人私有資料或特定工具）
- 去掉個人資訊後，核心邏輯是否仍然完整可用？

⏸ 兩個都 Yes → 繼續 Step 1。
有疑慮 → 停下來討論，保留在個人 Skill 即可，不必強行開源。

---

## Step 1：讀取來源 skill

1. 確認來源檔路徑：
   - 有指定名稱 → `SKILL_DIR/[名稱].md`
   - 沒有 → 從 IDE 當前開啟的檔案取得
2. 讀取全文，顯示 skill 名稱與前 5 行摘要

---

## Step 2：資安掃描

把以下 `<placeholder>` 換成你的實際值，再逐項執行：

```bash
# 個人絕對路徑
grep -n "/Users/<your-username>" [檔案]

# 個人信箱
grep -ni "gmail\.com\|<your-email-domain>" [檔案]

# GitHub 帳號識別符
grep -n "<your-github-username>" [檔案]

# 個人姓名（填入你的名字）
grep -n "<your-name>" [檔案]

# 外部本地檔依賴
grep -n "讀取規則檔\|從以下路徑\|/Users/" [檔案]
```

掃描結果分類輸出：

| 類型 | 行號 | 內容 | 建議處理 |
|---|---|---|---|
| 個人路徑 | ... | ... | 改為通用描述 |
| 外部依賴 | ... | ... | 內嵌規則進 skill 本體 |
| 個人資訊 | ... | ... | 替換為通用版本 |

**若所有掃描結果均為「無」→ 跳過 Step 3，直接進 Step 4。**

⏸ 有問題 → 列出後等用戶確認處理方式。

---

## Step 3：清理 + 翻譯（只改 repo 副本，自用版原檔絕不動）

**黃金原則：自用版（你個人 skill 目錄裡的原檔）永遠保持原樣，一個字都不改。** 開源是「複製一份出去再清理副本」，不是「就地清理原檔」。原檔裡的真實路徑、機器特定設定、個人慣用範例，是你自用時的便利，不該為了開源被犧牲。自用版與開源版本來就該有差別。

本 repo 架構：**根目錄是英文正本，中文翻譯放 `zh/`。** 根目錄那份才是安裝成 `/command`、在 `/help` 顯示的檔，所以必須是英文。依序執行：

1. **把來源檔複製進 `zh/`**（中文版）：
   ```bash
   cp [來源路徑] REPO_LOCAL_PATH/zh/[skill名稱].md
   ```
2. **清理 `zh/` 副本**（以下清理只對 repo 副本執行，來源檔不碰）：

   **個人絕對路徑：**
   - `/Users/<your-username>/...` → 改為「IDE 當前開啟的檔案」或「你的專案路徑」

   **外部本地檔依賴（最常見：no-ai-trace 類型）：**
   - 讀取本地規則檔的步驟 → 把規則內容全部內嵌進 skill 本體
   - 確認內嵌後 skill 可獨立運作，不需要任何本地檔案

   **個人資訊：**
   - 個人信箱 → `your-email@example.com`
   - 個人姓名 → 刪除或改為通用稱呼

3. **把清理過的中文翻成根目錄英文檔** `REPO_LOCAL_PATH/[skill名稱].md`：
   - 寫成 native 英文、遵守 `/no-ai-trace` 原則，不是逐字機翻。這個 repo 是作品集門面，英文品質就是它的第一印象。
   - 有 YAML frontmatter 的 skill：保留 frontmatter，`description` 翻成英文。

清理完後顯示 diff，⏸ 等用戶確認「這樣 OK」再繼續。

---

## Step 4：確認 README 內容

⏸ 向用戶收集以下內容（可先給草稿讓用戶修改）：

1. **指令一覽表的一行描述**（中文，10 字以內）
2. **詳細說明段落**（中文，3–5 行）：
   - 這個指令解決什麼問題
   - 用法範例
   - 如有特殊需求（如：需要 Node.js）一併說明
3. **llms.txt 的一行英文描述**（50 字以內）

zh-TW 是 source of truth，英文和簡中從 zh-TW 轉換。

---

## Step 5：寫入 repo

確認後依序執行（全部完成再 commit，不逐步 commit）：

**5-A：確認兩份指令檔都就位**（Step 3 已做）：英文正本在 `REPO_LOCAL_PATH/[skill名稱].md`，中文翻譯在 `REPO_LOCAL_PATH/zh/[skill名稱].md`，兩份都清理過、來源檔未被動過。

**5-B：更新三語 README**

每個 README 需要改兩處：

1. **指令一覽表**（在現有表格末端加一行）：
   ```
   | `/[指令名]` | [功能描述] |
   ```

2. **指令說明區塊**（在最後一個指令說明後加新區塊）：
   ````markdown
   ---

   ### `/[指令名]`

   [詳細說明]

   ```
   /[指令名] [用法範例]
   ```
   ````

語言切換列格式（三語都要有，目前語言純文字不加連結）：
```
[English](README.md) | [繁體中文](README.zh-TW.md) | [简体中文](README.zh-CN.md)
```

**5-C：更新 llms.txt**

在 `## Commands` 區塊末端加一行（連到英文正本）：
```
- [/[指令名]]([skill名稱].md): [英文一行描述]
```

**5-D：顯示所有變更的 diff**

⏸ 等用戶最終確認「可以推了」。

---

## Step 6：Commit + Push

```bash
cd REPO_LOCAL_PATH
git add .
git commit -m "feat: add /[skill名稱] command"
git push
```

若 repo 有版本管理（CHANGELOG.md、release tags），push 前先更新版號。

確認 push 成功後回報：GITHUB_URL

Push 成功後，更新 memory 裡的指令數：
```
~/.claude/projects/.../memory/reference_geek_on_autopilot.md
```
把指令總數 +1（例如「7 個 slash commands」→「8 個」）。

---

## 附錄：不適合開源的 skill 特徵

- Skill 核心邏輯依賴個人私有資料（個人財務、公司機密資料）
- Skill 包含無法通用化的本地工具
- 移除個人資訊後 skill 失去意義
- Skill 只是個人 SOP 的自動化，對其他人沒有參考價值

這類 skill 留在個人 Skill 目錄即可，不需要開源。
