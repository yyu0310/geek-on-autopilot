Marp 簡報交稿前 QA 檢查 + 匯出 PDF。

用法：
- `/marp-export` — 匯出當前 IDE 開啟的 Marp .md 檔
- `/marp-export /path/to/file.md` — 匯出指定檔案

執行步驟：

1. 確認目標 .md 檔路徑：
   - 用戶有指定 → 直接用
   - 沒有 → 從 IDE 當前開啟的檔案取得

2. QA 檢查（全部通過才匯出）：

   **2-A 草稿標記掃描**
   ```bash
   grep -n "【" {目標檔案}
   ```
   若有輸出 → 列出行號與內容，⏸ 請用戶確認是否清除後再繼續

   **2-B 圖片路徑確認**
   掃描所有 `![` 引用，確認 `assets/` 資料夾存在且圖片檔案實際存在
   若有缺失圖片 → 列出並 ⏸ 等用戶確認

3. 匯出 PDF：
   ```bash
   cd "{目標檔案所在資料夾}"
   npx --yes @marp-team/marp-cli@latest "{檔名}.md" --pdf --allow-local-files -o "{檔名}.pdf"
   ```

4. 確認 PDF 生成（`ls "{檔名}.pdf"`）：
   - 成功 → 回報 PDF 路徑與檔案大小
   - 失敗 → 輸出錯誤訊息（npx 問題？node 版本？）
