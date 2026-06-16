將個人 skill 整理開源，加入你的 geek-on-autopilot repo。

⚙️ 使用前一次性設定：把下方兩個佔位符替換成你的實際值，存檔後即可使用。

```
REPO_LOCAL_PATH  = /your/local/path/to/geek-on-autopilot/
GITHUB_URL       = https://github.com/YOUR_USERNAME/geek-on-autopilot
```

用法：
- `/open-source-skill [skill 名稱]` — 指定 skill（在你的 Skill 目錄尋找對應 .md）
- `/open-source-skill` — 從 IDE 當前開啟的 skill 檔開始

---

## Step 1：讀取來源 skill

1. 確認來源檔路徑：
   - 用戶有指定名稱 → 在你的 Skill 目錄找 `[名稱].md`
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

# 外部本地檔依賴（讀取本地規則檔）
grep -n "讀取規則檔\|從以下路徑\|/Users/" [檔案]
```

掃描結果分類輸出：

| 類型 | 行號 | 內容 | 建議處理 |
|---|---|---|---|
| 個人路徑 | ... | ... | 改為通用描述 |
| 外部依賴 | ... | ... | 內嵌規則進 skill 本體 |
| 個人資訊 | ... | ... | 替換為通用版本 |

⏸ 列出所有問題後停下，等用戶確認處理方式。

---

## Step 3：清理

根據確認結果執行清理：

**個人絕對路徑：**
- `/Users/<your-username>/...` → 改為「IDE 當前開啟的檔案」或「你的專案路徑」

**外部本地檔依賴（最常見：no-ai-trace 類型）：**
- 讀取本地規則檔的步驟 → 把規則內容全部內嵌進 skill 本體
- 確認內嵌後 skill 可獨立運作，不需要任何本地檔案

**個人資訊：**
- 個人信箱 → `your-email@example.com`
- 個人姓名 → 刪除或改為通用稱呼

清理完後顯示 diff，⏸ 等用戶確認「這樣 OK」再繼續。

---

## Step 4：確認 README 內容

向用戶收集三語 README 需要的文字：

⏸ 詢問用戶提供以下內容（可先給草稿讓用戶修改）：

1. **指令一覽表的一行描述**（中文，10 字以內）
2. **詳細說明段落**（中文，3–5 行）：
   - 這個指令解決什麼問題
   - 用法範例（`/open-source-skill [skill 名稱]`）
3. **llms.txt 的一行英文描述**（50 字以內）

zh-TW 是 source of truth，英文和簡中從 zh-TW 轉換。

---

## Step 5：寫入 repo

確認後依序執行（全部完成再 commit，不逐步 commit）：

**5-A：複製 skill 檔**
```bash
cp [來源路徑] REPO_LOCAL_PATH/[skill名稱].md
```

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

在 `## Commands` 區塊末端加一行：
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

確認 push 成功後回報：GITHUB_URL

---

## 附錄：不適合開源的 skill 特徵

遇到以下情況，⏸ 停下來提醒用戶重新評估：

- Skill 核心邏輯依賴個人私有資料（個人財務、公司機密資料）
- Skill 包含無法通用化的本地工具
- 移除個人資訊後 skill 失去意義
- Skill 只是個人 SOP 的自動化，對其他人沒有參考價值

這類 skill 留在個人 Skill 目錄即可，不需要開源。
