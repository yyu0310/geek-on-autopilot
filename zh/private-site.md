---
name: private-site
description: 把靜態網站或 html 上架成私人（invite-only）網站：Cloudflare Pages 直接上傳加 Access 白名單，只有受邀 email 輸入一次性驗證碼才進得去。含內容盤點與發布版轉換、先鎖後放、鎖驗證、獨立審查、排程更新、日常加人。用戶要把 html 或數據頁放上網給朋友看、做 invite-only 網站、限制誰能看時使用。
---

# /private-site：把靜態網站放到邀請名單後面

> 方案已定，不要重新比較：Cloudflare Pages 直接上傳加 Zero Trust Access 政策。不用 Apps Script 網頁應用程式：它拿不到一般帳號訪客的 email、必須「以訪客身分執行」、朋友會看到「未驗證應用程式」警告，白名單還要自己寫程式。也不用 GitHub Pages 加密碼：原始碼是公開的。

## 共用工具

兩支腳本都在 repo 根目錄，只用標準函式庫（shell 那支另需 `curl`）。下面的指令預設你在 repo 根目錄執行，否則請改用完整路徑。

| 工具 | 用途 |
| --- | --- |
| `cf_private_site.py` | 管 Access：`check`、`emails`、`apply <emails>`（整份覆蓋）、`harden`。一律帶 `--host X.pages.dev`，用 `python3 -I` 跑。需要環境變數 `CF_ENV_FILE`（見步驟 3） |
| `site_lock_check.sh` | 約 40 個 curl 探測，驗證未登入的人拿不到內容：`bash site_lock_check.sh <host> '<頁面獨有字串>' [部署網址檔]`。多頁網站設 `EXTRA_PATHS='/page2.html /b'`。只對你自己的網站執行。 |
| 審查 prompt | 給獨立 LLM 審查用的範本，在本檔最後 |

兩支腳本都有 `--selftest`（不連網，用假的 API 或假的 curl）。

## 步驟 1：範圍判斷（動手前，3 分鐘）

1-1 **內容是純靜態嗎**（html、css、js、圖，沒有後端、資料庫、寫入）？是，走本 SOP。有後端或要存資料，停手問用戶，那要 Workers 加 D1 另外設計。

1-2 **問用戶三件事。** 誰要看：白名單 email 清單，沒給就只放用戶自己。網址要叫什麼：專案名，英數小寫加連字號，得到 `<name>.pages.dev`。資料會不會更新，會的話看步驟 7。

1-3 **網站有自己版與朋友版之分嗎**（餘額、個資、本機連結）？有，走步驟 2-4 的發布版轉換。

## 步驟 2：發布前內容盤點（必做，沒看過內容不准發布）

2-1 機械掃描：對要發布的 html 搜你的使用者名稱、家目錄絕對路徑與其他私人路徑、你自己的名字、`api_key`、`token`、`Authorization`、`Bearer`、`password`、`密碼`，每項都要 0 筆。

2-2 抽出純文字（去掉 script 與 style）自己讀一遍，找個人資訊：金額、點數餘額、個資、人名。

2-3 看外部資源與連結。公開 CDN（jsdelivr 等）可以。指向本機 `.md` 的相對連結放上網會變死連結，要轉成純文字。

2-4 **有東西要藏，做「發布版轉換」。** 來源檔不動，部署腳本每次從來源檔轉出 `public/` 下的發布版，轉換後用 `assert` 檢查敏感字串已不存在、替換處數符合預期。來源檔結構變了就中止並發出警報，不會悄悄把餘額發出去。注意：由餘額算出的衍生值（「買得起幾件」「剩多少額度」）也會洩漏，整塊拿掉，不是只遮數字。程式裡的常數也要清掉，因為 view-source 看得到。

2-5 改完用 `node --check` 檢查內嵌 JS 語法，再檢查頁首文字還通順。

## 步驟 3：帳號與憑證（用戶自己做，助理不碰憑證）

3-1 Cloudflare 帳號要開 2FA（助理看不到，由用戶自己確認）。Zero Trust 用 Free 方案（50 人）。第一次進去要取 team name，它會變成登入頁網址，可在 Zero Trust Settings 改名，建議取好認的。

3-2 **兩把 token 分開。** 部署用只給 Account / Cloudflare Pages / Edit，放在跑部署的那台機器。設定用 Zero Trust 範本（Access Apps and Policies Edit，加上 Organizations、Identity Providers、Groups 的 Edit，這樣 `apply` 在沒有 One-time PIN 時才能建立它），只放在你管理 Access 的那台機器。已經有就直接用。token 可能到期，腳本回 403 先懷疑到期。缺權限就編輯同一把 token 加上去，內容不變。

3-3 **憑證檔的放法。** 每把 token 各放一個 env 檔（`CLOUDFLARE_API_TOKEN=...` 與 `CLOUDFLARE_ACCOUNT_ID=...`），放在任何 repo 之外、AI 工具讀不到的資料夾。檔案由用戶自己建立與複製。`cf_private_site.py` 透過**必填**的環境變數 `CF_ENV_FILE` 讀設定用的檔；它沒有預設位置，沒設這個變數就印出錯誤並以 exit 5 結束。部署腳本用自己的方式載入部署用的 env 檔。憑證只由程式讀取：助理不開憑證檔、不印 token、不貼進對話。權限 hook 或沙箱擋下指令時，照擋下訊息的指示做，不繞過，改請用戶在自己的終端機執行。

## 步驟 4：建專案、先鎖後放

4-1 建 Pages 專案：`wrangler pages project create <name> --production-branch main`（直接上傳，不經 git）。

4-2 **先鎖再第一次部署，不留公開空窗：** `CF_ENV_FILE=<設定用 env 檔> python3 -I cf_private_site.py apply --host <name>.pages.dev <emails>`。沒有 One-time PIN 會自動建，app 同時涵蓋正式網址與 `*.<name>.pages.dev`。接著跑 `harden`（session 7 天、Binding cookie、SameSite Lax、HttpOnly）。

4-3 跑 `check`，確認 app 的 destinations 兩筆都在。不要靠 Pages 後台的 Enable access policy 按鈕：它只鎖預覽網址，正式網址會公開。

## 步驟 5：部署

5-1 發布資料夾用 ASCII 路徑（`public/index.html`）。wrangler 本地安裝並釘版（`npm i --save-exact wrangler@<版本>`），不要每次用 `npx` 抓最新。排程 job 的 PATH 常常很精簡，腳本需要的路徑要在腳本裡自己 export。

5-2 部署指令：`wrangler pages deploy public --project-name <name> --branch main --commit-dirty=true`，兩個環境變數由你的腳本從部署用 env 檔載入。直接上傳不吃每月 500 次建置額度。

5-3 手動跑一次，記下部署網址。

## 步驟 6：驗證（沒貼證據不報完成）

6-1 跑 `bash site_lock_check.sh <host> '<頁面獨有字串>' [部署網址檔]`，要 exit 0 且 `fail=0`。標記字串是 egrep（ERE）語法，`(`、`+`、`[` 這類字元要跳脫（`'C\+\+'`），不合法的寫法會以 exit 2 拒絕。每個回應也會看狀態碼：2xx 算失敗（下面的 Cloudflare 路徑除外），host 完全沒回應也算失敗（exit 6），所以打錯 host 不會過關。其他狀態碼也算失敗，需手動查看。部署網址用 `wrangler pages deployment list --project-name <name> --json` 取 `Deployment` 欄，一行一個寫進檔再餵給它。腳本會拒絕你 host 以外的任何網址，部署網址沒回應也算失敗。`/cdn-cgi/trace` 與 `/cdn-cgi/access/*` 回 200 是 Cloudflare 標準內容，輸出會標成 `exempt_200`。

6-2 **獨立攻擊驗收。** 派一個 fresh-context 的 agent，給它 host，只用唯讀 curl 試繞過鎖：路徑變體、方法、偽造標頭、猜分支子網域。不登入、不猜驗證碼、不碰登入送出端點，只測你自己的網站。回報只收結論加表。

6-3 **獨立 LLM 審查。** 把本檔最後那份 prompt 範本的佔位符換成這次的實際值，存成暫存檔，交給另一個獨立、能上網的 LLM。給足夠長的逾時，完整跑一輪可能要十分鐘左右。它列的 curl 清單你自己跑。它引用的外部連結，沒開過之前都不當事實，並要求它把風險分成「有證據」與「未驗證」兩組回報。

6-4 **網站主人用白名單 email 實際登入**，看頁面、篩選、版面，助理無法代測。若登入後一直被導回登入頁，關掉 Binding cookie。

6-5 對發布檔再做一次步驟 2-1 的機械掃描。

## 步驟 7：資料會更新的網站

資料會更新就把部署腳本排程跑。

## 步驟 8：日常管理

8-1 **加人或移人：** `cf_private_site.py apply --host <host> <全部 email>` 是整份覆蓋，永遠寫全部人，跑完用 `emails` 讀回確認。`apply` 與 `emails` 的輸出含受邀者 email，需要時在自己的終端機跑，不要貼到公開處。

8-2 session 7 天，免費方案的 Access 登入紀錄只留 24 小時。朋友不用了就移除；加新朋友後的幾天，可以到 Zero Trust → Logs 看一眼。

8-3 被邀請的人可以另存或轉傳頁面，技術上擋不了，事前要跟對方講好。

## 踩坑（現象、原因、做法）

| 現象 | 原因 | 做法 |
| --- | --- | --- |
| Pages 後台點了 Enable access policy，正式網址還是公開 | 它只鎖預覽網址 | 用 `apply` 建 app，兩個 destination 都要在 |
| 加了一個 email，原本的人進不去了 | `apply` 整份覆蓋 | 永遠寫全部人，跑完用 `emails` 確認 |
| 登入頁網址是一串亂數 | 開通 Zero Trust 時隨機取的 team name | 在 Zero Trust Settings 改名，登入連結會變，白名單不受影響 |
| `/cdn-cgi/trace` 回 200 | 這是每個網站都會回的 Cloudflare 節點資訊 | 不用處理，檢查腳本會標成例外 |
| 登入後一直被導回登入頁 | Binding cookie 與瀏覽器環境不合 | `harden` 前先確認；出問題先關 Binding cookie |
| wrangler 在含非 ASCII 字元的路徑出問題 | 工具限制 | 發布資料夾用 ASCII |
| 排程 job 找不到 node 或 wrangler | job 的 PATH 很精簡 | 腳本內 export PATH，wrangler 本地安裝並釘版 |

## 附錄：獨立審查用的 prompt 範本

複製到暫存檔，把 `{HOST}`、`{TEAM}`、`{CONTENT}`、`{DEPLOY}` 換成這個網站的實際值。不要放 token、白名單 email 與任何憑證。

```text
你是紅隊顧問。以下是我自己擁有並授權測試的網站，我要在朋友使用前找出「不在白名單也能拿到頁面內容」的所有可能路徑。請用台灣繁體中文回答，並盡量搜尋官方文件與已公開的繞過案例（CVE、安全公告、社群回報），每個主張附來源 URL。

系統架構（全部事實）
- 內容：{CONTENT}（例如：2MB 靜態單檔 html，無後端、無 API、無資料庫、無 Pages Functions）。風險在「不該被未受邀者看到」與「被轉傳」。
- 託管：Cloudflare Pages 專案，direct upload（不經 git），正式網址 https://{HOST}，每次部署另有 https://<hash>.{HOST}。
- 鎖：Cloudflare Zero Trust Access（Free 方案），team name {TEAM}，Self-hosted application，destinations 為 {HOST} 與 *.{HOST}，登入方式只有 One-time PIN，Policy 只有 Allow 加 Emails 白名單，session 7 天、Binding cookie 開、SameSite Lax、HttpOnly 開。沒有 Bypass 或 Service Auth 政策，沒有自訂網域。
- 更新：{DEPLOY}（例如：排程 job 用只有 Pages Edit 的 API token 以 wrangler 部署）。
- 已測（未登入、curl）：正式網址與路徑變體、大小寫、HEAD/POST/PUT/OPTIONS、偽造 Access 標頭與 X-Forwarded-*、Host 偽造、部署雜湊網址、常見分支子網域，全部導向登入網域或被拒，內容 0 外洩。

請你做的事
1. 威脅建模，分四類列出所有可能讓「不在白名單的人」看到內容的路徑：
   a. Cloudflare Access 與 Pages 本身的已知繞過或設計缺口（*.pages.dev 別名與預覽網址的覆蓋範圍、舊部署是否持續可存取、/cdn-cgi/access/ 端點、JWT 與 cookie 驗證、OTP 流程如 email 正規化、大小寫、加號別名、同形字、重送與爆破限制、Free 方案差異）。
   b. 設定面失誤：本案現行設定有沒有漏洞；常見誤設與自查方法。
   c. 供應鏈與憑證面：API token 外洩路徑、wrangler 本地安裝、部署腳本、Cloudflare 帳號（2FA、成員）。
   d. 人為面：被白名單者轉傳連結或截圖、email 被接管、session 長度。
2. 每條給：可能性（高、中、低）、影響、我如何驗證、我怎麼修。
3. 把「可由外部、不登入、只用 HTTP 請求驗證」的項目整理成 curl 測試清單，只打 {HOST} 及其子網域；不要包含任何會對第三方 email 寄出 OTP 的步驟，也不要包含爆破。我會自己執行並回報。
4. 你自己可用網頁抓取工具對 https://{HOST}/ 與 https://{HOST}/cdn-cgi/access/ 底下的公開端點做不登入的 GET 觀察；不要嘗試登入、不要猜驗證碼、不要打非本案網域。看到什麼如實寫，沒看到就說沒有，不要編造。

輸出格式
結論先行：「找到 N 個值得處理的風險」。接著風險表（編號、類別、可能性、影響、驗證方式、修法），再附 curl 測試清單。所有「已驗證」都要有你實際看到的證據，否則標「未驗證」。
```
