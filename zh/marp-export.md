Marp 簡報交稿前 QA 檢查，再匯出 PDF。機械部分都在 `marp_export.py`，腳本放在 repo 根目錄，與本檔同層。

用法：
- `/marp-export`：匯出目前 IDE 開啟的 Marp .md 檔
- `/marp-export path/to/deck.md`：匯出指定檔案

前置：
- Python 3 與 Node.js（含 `npx`）。Marp CLI 透過 `npx` 執行，免另外安裝，第一次匯出會下載套件。
- PATH 找不到 `npx` 時，腳本會先找 Homebrew 與 nvm 的常見路徑，都找不到才以 exit 5 結束。自己手動跑 `npx` 時，要先把這些目錄補進 PATH。

執行步驟：

1. 確認目標 .md 路徑。用戶有指定就用，沒有就取 IDE 目前開啟的檔案。

2. 在 repo 根目錄跑 QA 檢查，或改用 `marp_export.py` 的完整路徑。通過才匯出。

   ```bash
   python3 marp_export.py qa deck.md
   ```

   掃描兩件事：
   - 草稿標記：`TODO`、`FIXME`、`TBD`、`XXX`，以及全形 `【` 括號。命中的每一行都會連同行號印出。
   - 本地圖片引用（`![alt](path)`，含 `![bg fit](path)`）指向的檔案不存在。遠端圖片不驗，每張會印一行 WARN。遠端圖片離線可能失效，每一張都要轉述給用戶。

   exit 4 時貼出輸出，⏸ 等用戶決定。清標記、補圖或刪引用都由用戶決定。

3. 匯出 PDF 並驗收。

   ```bash
   python3 marp_export.py export deck.md
   python3 marp_export.py verify deck.md
   ```

   `export` 會在簡報所在資料夾執行 `npx --yes @marp-team/marp-cli@latest deck.md --pdf --allow-local-files --no-stdin -o deck.pdf`，可用 `--timeout 秒數` 調整逾時，預設 300。`verify` 檢查同名 .pdf 存在、大於 0 bytes、且不比 .md 舊。兩者輸出都貼出來，並回報 PDF 路徑與大小。

   失敗時貼出錯誤輸出，檢查 npx、Node 版本與網路。

子指令：

| 指令 | 作用 |
| --- | --- |
| `qa <file.md>` | 草稿標記掃描與本地圖片存在性檢查 |
| `export <file.md>` | 透過 Marp CLI 匯出 PDF |
| `verify <file.md>` | 檢查 PDF 是否存在、大小與新舊 |

想測腳本本身，跑 `python3 marp_export.py --selftest`，測試只在暫存資料夾進行。

Exit code：

| 代碼 | 意義 |
| --- | --- |
| 0 | 成功 |
| 2 | 外部指令（npx）失敗或逾時 |
| 3 | 檔案不存在或不是 .md |
| 4 | 硬門檻 FAIL：QA 有問題，或 verify 未過 |
| 5 | 環境缺件：找不到 npx |

踩坑：
- marp-cli 常卡住，多半是 stdin 沒關。手動執行時要加 `--no-stdin`，並用 `< /dev/null` 導入空輸入。腳本已經兩者都做了。
- 圖片路徑以 .md 所在資料夾為基準解析，路徑含空格沒問題。
