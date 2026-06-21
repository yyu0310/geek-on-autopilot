將指定 MD 檔案轉換為 PDF，使用 PingFang TC 字體模板。

⚙️ 使用前一次性設定：把下方佔位符替換成你的實際值，存檔後即可使用。

```
REFDIR = /your/local/path/to/geek-on-autopilot
```

`reference_pingfang.docx` 已包含在此 repo 中，複製 repo 後 REFDIR 設為 repo 根目錄路徑即可。

用法：
- `/md-to-pdf` — 轉換當前 IDE 開啟的 .md 檔案
- `/md-to-pdf /path/to/file.md` — 轉換指定路徑的 .md 檔案

執行步驟：

1. 確認目標 MD 檔路徑：
   - 用戶有指定路徑 → 直接用
   - 沒有 → 從 IDE 當前開啟的檔案取得路徑

2. 檢查格式陷阱（序號列表前必須有空行）：
   掃描 MD 內容，找出起始數字不是 1 的序號列表（`4.` `5.` 等），確認前面是否有空行。若有格式問題，列出行號讓用戶確認要不要先修再轉。

3. 執行轉換（兩步）：

```bash
FILE="<目標 MD 路徑>"
DIR=$(dirname "$FILE")
BASENAME=$(basename "$FILE" .md)
REFDIR="<geek-on-autopilot repo 路徑>"

# Step 1：MD → DOCX
pandoc "$FILE" --reference-doc="$REFDIR/reference_pingfang.docx" -o "$DIR/$BASENAME.docx"

# Step 2：DOCX → PDF
/Applications/LibreOffice.app/Contents/MacOS/soffice --headless --convert-to pdf "$DIR/$BASENAME.docx" --outdir "$DIR"
```

4. 確認 PDF 已生成（`ls "$DIR/$BASENAME.pdf"`）：
   - 成功 → 刪除中間檔 `rm "$DIR/$BASENAME.docx"`，回報 PDF 輸出路徑
   - 失敗 → 輸出錯誤訊息並診斷原因（pandoc 未安裝？LibreOffice 路徑錯誤？字體模板找不到？），保留 .docx 供排查

環境需求（若失敗時檢查）：
- pandoc：`brew install pandoc`
- LibreOffice：`brew install --cask libreoffice`
- 字體模板：`reference_pingfang.docx` 在 REFDIR 路徑下（已包含在此 repo 中）
