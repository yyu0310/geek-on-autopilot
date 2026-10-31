---
name: docx-gen
description: 用程式碼自由編輯 Word 文件（自訂段落字體、顏色、表格），輸出乾淨 PDF
---

寫一份排版可控（不同段落字體與顏色、表格）的 Word 文件並輸出 PDF。底層是 dolanmiu/docx（npm）。比 markdown 轉檔多花 token，換來的是逐段文字的格式控制力。

用法：
- `/docx-gen <需求描述>`：描述要生成的文件內容與格式，直接生成 PDF

## 設定

`docx_pdf.py` 放在 repo 根目錄，旁邊是它匯入來做字體檢查的 `md2pdf.py`，兩個檔案要留在同一個資料夾。生成腳本放在 `docx-gen-tools/workspace/`。先跑一次：

```bash
cd docx-gen-tools && npm install
```

`docx-gen-tools/workspace/example_qa_test.js` 是已驗證過的完整範例，含表格、混合格式與 CJK 文字。新文件照抄結構、改內容即可。設定指令預設你從 repo 根目錄開始，否則請改用完整路徑。之後下面的指令都在 `docx-gen-tools/workspace/` 底下執行，所以腳本寫成 `../../docx_pdf.py`。

## 步驟

1. **在 `docx-gen-tools/workspace/` 下寫一支 `<name>.js`。** 必須放這個資料夾，`require('docx')` 才解析得到，不要另開資料夾。下面每一條都是實際轉檔踩出來的坑。

   - 每個 `TextRun` 的 `font` 一律傳物件 `{ ascii, eastAsia, hAnsi }`，三個 key 填同一個字體名，不要傳純字串。純字串只設拉丁字體，中文會落到 LibreOffice 自己亂猜的字體。
   - `Document` 建構子加 `styles.default.document.run.font`，以及 `heading1`、`heading2`、`title` 的 `run.font`，都填同一個字體物件。標題走獨立的樣式解析路徑，不會繼承 `TextRun` 的字體。
   - **全文件禁用 `italics: true`。** 只要任何一個 run 設了 italics，即使是純英文 run，LibreOffice headless 就會把整份文件的 CJK 字體全部換成行楷等裝飾體。這個失效是確定性的，重轉也沒用。中文或英文要斜體視覺，改用底線 `underline: {}` 或顏色。
   - 表格只要兩欄以上，`Table` 建構子必須同時給 `columnWidths`（陣列）。只在每個 `TableCell` 設 `width` 不夠，LibreOffice 會把整張表渲染成塌陷的黑色方塊，資料全部消失。
   - 表頭底色用 `shading: { type: ShadingType.CLEAR, fill: '顏色碼' }`，絕對不要用 `SOLID`，整格會變黑。
   - 大量重複內容（表格列、清單）用 for 迴圈生成，不要逐項手寫。省 token，改內容時也不會漏改。

2. **執行：**

   ```bash
   cd docx-gen-tools/workspace && node <name>.js
   ```

3. **Lint。** 機械式擋 italics 這個坑，養成先跑的習慣：

   ```bash
   python3 ../../docx_pdf.py lint "<name>.js"
   ```

   exit 4 會印出命中的行號。改掉 italics 再繼續，不要跳過。

4. **轉 PDF。** 用 LibreOffice headless，附自動字體 QA，最多重試 6 次：

   ```bash
   python3 ../../docx_pdf.py convert "<name>.docx"
   ```

   輸出原樣貼上。exit code：
   - 0 成功
   - 2 soffice 失敗或逾時
   - 3 輸入檔不存在或副檔名不符
   - 4 硬門檻失敗（lint 命中、PDF 驗收失敗，或重試後字體 QA 仍失敗；在這裡失敗，先回頭查步驟 1 是不是漏了 italics 或 `columnWidths`）
   - 5 環境缺件（soffice 或 pdffonts），照它印出的安裝指令轉述給用戶

5. **驗收 PDF。** `.docx` 中間檔預設留在 `workspace/`（轉檔成功後想刪，或用戶要乾淨資料夾，就加 `--remove-docx`）。只有頁數或字數明顯異常時，才用 `pdftoppm -jpeg -r 90 -f <頁> -l <頁> <pdf> <name>` 把頁面轉成圖來看，不要每次都做，截圖很貴。平常用 `pdftotext <pdf> -` 抽字，看 CJK 有沒有亂碼就夠了。

## 環境需求

失敗時檢查：
- Node.js 與 `docx` 套件（在 `docx-gen-tools/` 跑 `npm install`）
- LibreOffice：`brew install --cask libreoffice`
- Poppler（`pdffonts`、`pdftotext`、`pdftoppm`）：`brew install poppler`
- PingFang TC 為 macOS 內建。其他系統請把腳本裡的 `CJK_FONT` 改成你已安裝的 CJK 字體；字體檢查只會擋已知的手寫體與裝飾體

**不保證輸出精確字體。** macOS 上的 LibreOffice 挑 CJK 字體不固定，同一份 `.docx` 每次轉出的字體可能不同，同一份 PDF 內也可能混用。字體檢查和重試只會擋手寫體與裝飾體，無法保證一定是你指定的字體。需要精確字體就改從 Word 或 Pages 匯出。

腳本 exit code 慣例：0 成功／2 外部指令或網路失敗／3 檔案不存在／4 硬門檻失敗／5 缺少相依工具。
