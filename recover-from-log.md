從 Claude Code session log 找回被某次操作（如 /simplify、誤刪、誤改）刪掉或改壞的檔案內容，並安全還原。

適用情境：用戶說「某個操作把我的檔案弄壞了」「/xxx 把我的細節砍掉了」「幫我把刪掉的東西找回來」「還原到改之前」。

核心原理：Claude Code 每個 session 都把完整對話（含每次 Read 的檔案內容、每次 Edit 的 old_string/new_string）存在 `~/.claude/projects/<專案slug>/<session-id>.jsonl`，一行一個 JSON。被改之前的原始內容就藏在這些 log 裡，可以撈出來還原。

---

## Step 1：診斷 — 找出兇手 session 與操作

1. 先問清楚（用戶沒講就問）：被弄壞的是哪個檔案？大概什麼時候？是哪個指令或操作造成的？
2. 定位 log 目錄：`~/.claude/projects/` 下對應本專案的資料夾（資料夾名是專案絕對路徑把 `/` 換成 `-`，例如專案在 `~/code/myrepo` 就是 `-Users-you-code-myrepo`）。
3. 搜尋觸發點。**關鍵陷阱：不要用裸關鍵字 grep**。
   - skill 名稱（如 `simplify`）會被注入到每個 session 的 skill 清單，裸 grep 會比中幾乎所有 session。
   - 要比中**實際呼叫**：`grep -l "command-name>/簡指令名" *.jsonl`，或檔案被 Edit/Write 的記錄。
   - **排除當前 session**：你自己這次對話如果打過該關鍵字也會被比中。用時間戳（最後一筆 timestamp 接近現在）或行數很少（剛開的）判斷並排除。
4. 鎖定後，找出觸發那一刻的 log 行號與 timestamp（例：`<command-name>/simplify</command-name>` 出現在第幾行）。
5. 列出**觸發行之後**被 Edit/Write 的所有檔案（用 Python 掃 tool_use blocks 的 file_path）。

---

## Step 2：比對 — 撈出原始內容，分清「修正」與「破壞」

**最重要的觀念：同一個 session 在觸發點之前的改動，通常是正常工作（修 bug、補細節），不是要還原的對象。只有觸發點之後的改動才是嫌疑犯。** 不要無腦整段回退，會把好的修正一起殺掉。

撈原始內容的方法依操作類型：
- **被整份 Write 覆蓋**：往前找該檔案最後一次被 Read 的 `tool_result`，裡面就是覆蓋前的完整原文。
- **被 Edit 改/刪**：Edit 的 `old_string` = 改之前，`new_string` = 改之後。蒐集觸發點後所有 Edit，對照看砍了什麼。

技術細節：
- log 一行一個 JSON。`message.content` 可能是字串或 block 陣列。`tool_use` block 有 `name`/`input`/`id`，`tool_result` block 有 `tool_use_id`/`content`，兩者用 id 配對。
- Read 的 `tool_result` 是 `cat -n` 格式（行號 + tab 前綴），還原前要用 regex `^\s*\d+\t(.*)$` 去掉前綴。
- 用 Python 解析（jsonl 逐行 `json.loads`），把撈到的原版寫到 `/tmp/RESTORE_<檔名>` 供對照，不要直接覆蓋。

產出：清楚列給用戶看「原版有、現在沒了的內容」（`diff <(原版) 現檔` 取 `^<` 行），以及哪些是該保留的好修正。

---

## Step 3：編輯 — 規劃還原方式

依破壞程度選還原策略，**寧可外科手術，不要整份覆蓋**：
- **整份被掏空**：若原版已含好的修正（撈到的 Read 是在好修正之後），可整份 Write 還原，零損失。先確認原版結構完整（skill 檔注意：本專案 skill 無 YAML frontmatter，第一行就是描述，別把開頭弄丟）。
- **只砍了幾段**：現檔同時有「好修正」和「被砍段落」時，**只用 Edit 把被砍的段落補回去**，不要整份覆蓋（否則會回退掉好修正）。
- **有爭議的改動**（如把「依序讀」改成「並行讀」）：先問用戶要哪個版本，不要替他決定。

---

## Step 4：修改 — 執行還原並收尾

1. 動手前先把撈到的原版備份到 `/tmp/`（已在 Step 2 做）。
2. 執行 Write / Edit 還原。
3. 逐檔回報：還原了哪些段落、保留了哪些好修正、套用了哪些用戶選擇。
4. 收尾提醒：原版備份還在 `/tmp/`，要不要清掉。
5. 若這次踩坑值得記（如某指令會破壞某類檔案），主動建議存一條 memory。

---

**全程注意（不說出來，自己執行）：**
- 還原是覆蓋檔案的不可逆操作，動手前一定先撈出原版備份、先給用戶看 diff。
- 絕不無腦整段回退；觸發點前的改動預設是好的，要保留。
- 撈不到原始 Read 時，靠 Edit 的 old_string 拼回；兩者都沒有就誠實說「這段 log 沒留原文，無法還原」。
- 拒絕踩資安線：不讀禁區檔案的 log 內容（若 log 內含敏感檔內容，比照原檔禁讀規則處理）。
