將 Markdown 檔案轉成 PDF，使用 PingFang TC 字體。全程在本機執行，機密文件也能放心轉。

用法：
- `/md-to-pdf`：轉換 IDE 目前開啟的 .md 檔案
- `/md-to-pdf /path/to/file.md`：轉換指定路徑的 .md 檔案

設定：`md2pdf.py` 與 `reference_pingfang.docx` 放在 repo 根目錄，兩個檔案要留在同一個資料夾。腳本會自動找同資料夾的模板。想換模板，用 `--ref-docx PATH` 參數或設環境變數 `MD2PDF_REF_DOCX`。下面的指令預設你在 repo 根目錄執行，否則請改用 `md2pdf.py` 的完整路徑。

前置需求：
- pandoc：`brew install pandoc`
- LibreOffice：`brew install --cask libreoffice`
- poppler，字體檢查用的 `pdffonts`：`brew install poppler`
- PingFang TC 為 macOS 內建

步驟：

1. 確認目標路徑。用戶有指定就用指定的，沒有就取 IDE 目前開啟的檔案。

2. 先跑 lint：

```bash
python3 md2pdf.py lint "<file.md>"
```

exit 4 代表命中已知陷阱。列出行號，讓用戶決定要不要先修再轉。lint 檢查兩件事：起始數字大於 1 的序號列表，每個這類項目前面都要有空行，但補之前先看踩坑 8。單獨成段的 `![圖說](路徑)` 要照踩坑 3 處理。

3. 轉換：

```bash
python3 md2pdf.py convert "<file.md>"
```

PDF 會產生在來源檔旁邊。加 `--strip` 可輸出整份不分頁的長條版，避免表格被切開，檔名為 `<檔名>_strip.pdf`，與一般 PDF 並存。加 `--keep-docx` 保留中間檔，加 `--outdir DIR` 改輸出資料夾。

4. 來源檔有字數上限時，轉換前先跑 `python3 md2pdf.py wordcount "<file.md>" --max N`，exit 4 代表超過上限。

5. 腳本輸出原樣回報。exit code：
- 0 成功
- 2 pandoc 或 LibreOffice 失敗，保留 .docx 供排查
- 3 檔案不存在或不是 .md
- 4 硬門檻失敗，來源可能是 lint、wordcount、PDF 驗收，或字體 QA 一直不過
- 5 缺少相依工具，先看踩坑 5

已知踩坑：

1. **LibreOffice 在 macOS 的中文字體解析有隨機性。** 同一份 docx 每轉一次可能出現不同字體，跟模板指定哪個字體名稱無關。腳本會平行轉多份，逐份用 `pdffonts` 檢查，留下第一份所有字體都是 PingFang TC 的，最多重試 20 輪。平均約 15 秒，最壞約 45 秒。不要改成手動轉換。若自己手動轉，轉完用 `pdffonts file.pdf` 驗證，字體不對就重轉。

2. **單一 Enter 就是換行。** 腳本使用 `pandoc -f markdown+hard_line_breaks`，並先在暫存副本剝除行尾反斜線，舊檔才不會出現雙倍換行。原始檔不會被改動。

3. **圖說不要用單獨成段的 `![圖說](路徑)`。** pandoc 會把它轉成 Figure，圖說走 Image Caption 樣式，而這個樣式沒有指定中文字體，字體 QA 每次都過不了。正確寫法：圖說寫成一般文字行，緊接下一行放 `![](路徑){width=85%}`，兩行之間不留空行。圖片路徑以目前工作目錄為基準，先 `cd` 到 .md 所在資料夾再轉。

4. **成對的 `$` 會被當成 LaTeX 數學公式。** 像 `$AAPL 和 $MSFT` 這類文字會變成斜體襯線字加後備字體，字體 QA 每一輪都失敗。在暫存副本把每個 `$` 跳脫成 `\$`，例如 `sed -i '' 's/\$/\\$/g'`。PDF 顯示不變，原檔也不會被動到。要確認是不是這個原因，執行 `unzip -p file.docx word/document.xml | grep -o '<m:oMath>' | wc -l`，大於 0 就是中了。

5. **exit 5 常常只是 PATH 問題。** Claude Code 的 shell 常不含 `/opt/homebrew/bin`，裝了的工具看起來像缺件。先執行 `export PATH="/opt/homebrew/bin:$PATH"` 再重跑。用 `ls /opt/homebrew/bin` 確認清單裡真的沒有，才算缺件。

6. **PingFang TC 沒有的符號會拖進 Menlo。** 文中出現 PingFang TC 沒有字形的符號時，LibreOffice 會退回 Menlo-Regular，結果每次嘗試都過不了字體檢查，連主字體正確的那幾次也一樣。旗幟符號 `⚑`（U+2691）就會觸發。特徵是幾乎每次失敗的可疑字體清單都有 `Menlo-Regular`。找出那個特殊字元，在暫存副本移除或換掉，再重轉。帶變體選擇符的 emoji 如 `⚠️` 走 AppleColorEmoji，屬於豁免字體，不必處理。

7. **字體 QA 預期文件含中文。** 檢查只認 PingFang TC。完全沒有中文的文件會退回 Liberation Serif，項目符號則用 Symbol 字體，`convert` 會把 120 次嘗試全部跑完，最後以 exit 4 結束。這個工具是為中文與中英混合文件做的。純英文檔案請直接用 pandoc 加 LibreOffice，不走字體檢查。

8. **序號列表補空行的修法可能反效果。** 補了空行後，pandoc 會把整串列表判定成 loose list，在這個模板下，項目 2 以後可能被渲染成縮排更深的子清單，項目間出現大片留白。最常見於逐字引用、本身就帶數字編號的文字，例如貼上的 prompt。這類內容不需要清單語意。把每個編號的句點跳脫成 `N\.`，pandoc 就當純文字處理，轉完用 `pdftotext -layout` 確認編號。

自我測試：`python3 md2pdf.py --selftest` 會在暫存資料夾內跑內建測試。
