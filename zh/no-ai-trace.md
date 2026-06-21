通用型去除 AI 寫作痕跡自查。

用法：
- `/no-ai-trace` — 檢查對話中最近一次輸出的文案
- `/no-ai-trace [貼上文字]` — 檢查指定文字

步驟：

1. 確認要檢查的文字：
   - 用戶指令後有貼文字 → 檢查那段
   - 沒有 → 檢查對話中最近一次的文案輸出

2. 按以下 Part 1 禁止清單（Rule 1–17）逐條掃描，機械可判斷的直接抓，語意型的逐句判斷。

3. 按以下「輸出前自查」清單做最終確認。

4. 輸出格式（固定）：
   - 第一行：「共發現 N 處違規」（0 也要說）
   - 每條違規：`[Rule X 規則名稱] 原句` → 建議改法（參照下方 Part 2 改寫法）
   - 最後一行：語氣總評，一句話，讀起來像人還是機器人？

5. 0 違規時：語氣總評也要通過才輸出「✓ 通過」。

---

## Part 1：禁止清單（Red Flags）

這些模式一出現，立即刪除或改寫。

### 1. 術語堆疊

禁用詞：`leverage`, `utilize`, `synergy`, `robust framework`, `holistic approach`, `actionable insights`, `delve`

- (X) `We must leverage our core competencies to achieve synergy.`
- (X) `Let's delve into the key findings of this report.`

禁用副詞／形容詞堆疊：`highly`, `incredibly`, `deeply`, `seamlessly`, `cutting-edge`, `transformative`, `world-class`, `state-of-the-art`

- (X) `This is a highly effective and incredibly powerful solution that seamlessly integrates with your workflow.`

### 2. 否定前提對比句

禁用句型：`...is not just [A]; it is also [B]...` 及所有「否定前提再給正面結論」的變體，包含中文「不是…，而是…」。

- (X) `This solution is not just efficient; it is also scalable.`
- (X) `They see the hardware, not the doctrine.`
- (X) `He's not preparing for an invasion; he's manufacturing consent for other pressure.`
- (X) 這不是一個工具，而是一個生態系統。
- (X) 我們不是在追求速度，而是在追求品質。

### 3. 能力／狀態名詞化

- (X) `This software has the ability to detect errors.`
- (X) `This framework provides the capability of scaling.`
- (X) `The team's responsibility is the management of risk.`
- (X) `The team made a decision to proceed.`

### 4. 零縮寫（英）／翻譯腔（中）

- (X) `I am confident that it is the right decision.`
- (X) 中文寫出不自然、繞口的翻譯腔句式

### 5. 開場暖場句

- (X) `In today's fast-paced world, efficiency matters.`
- (X) `It is undeniable that the market is shifting.`
- (X) `In the complex landscape of modern finance...`

### 6. 被動／容器句

- (X) `This report contains an analysis of the market.`
- (X) `The data provides an indication of the trend.`

### 7. 繞圈隱喻

- (X) `The findings of the study serve to illuminate the problem.`
- (X) `This initiative aims to facilitate the growth of the ecosystem.`

### 8. 抽象階段描述

- (X) `The project is currently in the implementation phase.`
- (X) `We are in the process of evaluating potential solutions.`

### 9. 破折號（Em Dash）

任何情況都不用 `—`，改用逗號或重組句子。

- (X) `The results were clear — we needed a new approach.`
- (X) `The product is built for traders — not institutions.`

### 10. "The X is real" 確認句

AI 用這類句子確認讀者情緒，聽起來像在替讀者作答。直接刪除，換成具體陳述。

- (X) `The demand is real.`
- (X) `The gap is real.`
- (X) `The opportunity is real.`

### 11. 括號補述

括號內的補述削弱主句力道。重組成獨立句子，或直接刪掉。

- (X) `The platform provides liquidity solutions (especially for institutional players) across major chains.`
- (X) `The token (which launched in Q1) has seen strong volume growth.`

### 12. 自問自答

AI 愛用問句製造懸念，再自己回答。直接刪問句，說結論。

- (X) `So what does this mean for traders? It means faster execution and lower costs.`
- (X) `Why does this matter? Because liquidity determines price.`

### 13. 過渡詞濫用

`Furthermore`, `Moreover`, `Additionally`, `In conclusion`, `To summarize` 是 AI 最愛的段落膠水，用了就像報告範本。

- (X) `Furthermore, the platform supports multiple chains. Moreover, fees are competitive.`
- (X) `In conclusion, this represents a significant step forward.`

### 14. Hedge 保留句

這類句子假裝謙遜，實際上是在浪費讀者時間。直接刪除，說重點。

- (X) `It's worth noting that the market has shifted significantly.`
- (X) `It should be mentioned that this approach carries some risk.`
- (X) `It's important to understand that results may vary.`

### 15. 碎句排比製造假戲劇感

連續三個超短句，每句結構平行，製造虛假的「歷史感」或「緊張感」。

- (X) `New dot plot. New tone. New era.`
- (X) `New team. New rules. New game.`
- (X) `One decision. One moment. One chance.`

### 16. 二元框架 + 煽情代價句

用「一個事件，兩種結果」的框架，加上「都有代價」作結尾，製造人為緊張感。

- (X) `One meeting, two outcomes, and both have a price.`
- (X) `One number, two readings, and neither is free.`
- (X) `Two paths. One decision. Everything changes.`

### 17. 平行主詞拆句（假簡潔）

同一個動作，不同主詞，各自一句。把一個完整事實機械性地切成兩塊。

- (X) `T1 finished. HLE finished.`
- (X) `Sinner withdrew. Alcaraz withdrew.`
- (X) `France qualified. Spain qualified.`

---

## Part 2：改寫法（Do's）

### 1. 術語堆疊 → 最簡單直接的詞

`use` 和 `leverage` / `utilize` 意思一樣，永遠選 `use`。

- (O) `We should use our team's strengths to work better together.`
- (O) `This report examines the key findings.`

### 2. 否定前提對比句 → 直接說正面事實

刪掉前半句，直接說 B。

- (O) `This solution is efficient and scalable.`
- (O) 這是一個生態系統。
- (O) 我們追求品質。

### 3. 能力／狀態名詞化 → 強動詞

- (O) `This software detects errors.`
- (O) `This framework scales.`
- (O) `The team manages risk.`
- (O) `The team decided to proceed.`

### 4. 零縮寫 → 縮寫 + 口語

- (O) `I'm confident it's the right call.`
- 縮寫清單：`I'm`, `it's`, `that's`, `you're`, `we're`, `they're`, `don't`, `can't`

### 5. 開場暖場句 → 直接刪除，切入正題

### 6. 被動／容器句 → 主動句

- (O) `This report analyzes the market.`
- (O) `The data indicates the trend.`

### 7. 繞圈隱喻 → 最直接的動詞

- (O) `The findings explain the problem.`
- (O) `This initiative expands the ecosystem.`

### 8. 抽象階段描述 → 具體行動或數字

- (O) `We're reviewing three vendors this week.`
- (O) `The project is 50% complete.`

### 9. 破折號 → 逗號或重組句子

- (O) `The results were clear, and we needed a new approach.`

### 10. "The X is real" → 具體陳述

- (O) `Demand has grown 3x in six months.`
- (O) `The gap shows up in every liquidity report.`

### 11. 括號補述 → 重組成主句或刪除

- (O) `The platform provides liquidity solutions across major chains, with particular depth for institutional players.`

### 12. 自問自答 → 直接說結論

- (O) `Liquidity determines price.`

### 13. 過渡詞濫用 → 重組句子，讓邏輯自己說話

- (O) `The platform supports multiple chains and keeps fees competitive.`

### 14. Hedge 保留句 → 直接刪除，說重點

- (O) `The market has shifted significantly.`

### 15. 碎句排比 → 合成完整句子，或只留一句

- (O) `Warsh's first FOMC brings a new dot plot and a different tone.`

### 16. 二元框架煽情結尾 → 說機率或後果

- (O) `A dovish tilt likely pushes QQQ up 4–6% within 72 hours. A hawkish surprise cuts growth stocks 3% on the day.`

### 17. 平行主詞拆句 → 合成一句

- (O) `T1 and HLE both finished the regular season.`
- (O) `Both Sinner and Alcaraz withdrew.`
- (O) `France and Spain both qualified.`

---

## 輸出前自查（每次必過）

- 術語：有沒有 `leverage` / `utilize` / `synergy` / `delve` / `robust` / `holistic` / `actionable` 等禁用詞？
- 副詞形容詞：有沒有 `highly` / `incredibly` / `seamlessly` / `cutting-edge` / `transformative` 等堆疊？
- 對比句：有沒有「not just A, but B」/ 「不是…而是…」或任何否定前提句型？
- 能力名詞化：有沒有「has the ability to」/ 「made a decision to」/ 「the detection of」？
- 縮寫：英文有沒有用 `I'm` / `it's` / `you're`？中文讀起來像人說的話嗎？
- 開場：有沒有「In today's...」/ 「It is undeniable that...」這類暖場句？
- 容器句：有沒有 `contains an analysis of` / `provides an indication of` 這類結構？
- 繞圈：有沒有 `serve to illuminate` / `aims to facilitate` 這類迂迴動詞？
- 抽象階段：有沒有「in the implementation phase」這類空泛描述？改成實際行動或數字。
- 破折號：有沒有 `—`？全部換成逗號或重組。
- 確認句：有沒有「the X is real」？換成具體數字或事實。
- 括號：有沒有括號補述？重組或刪除。
- 自問自答：有沒有問句接自答？刪問句，直接說結論。
- 過渡詞：有沒有 `Furthermore` / `Moreover` / `In conclusion`？重組句子。
- Hedge：有沒有「It's worth noting」/ 「It should be mentioned」？直接刪。
- 碎句排比：有沒有三個連續超短句堆疊製造戲劇感？合成一句或只留一句。
- 二元煽情：有沒有「One X, two outcomes, and both have a price」這類收尾？換成具體機率和幅度。
- 平行拆句：有沒有「X did Y. Z did Y.」這種平行結構？合成一句。
- 語氣總檢：讀起來像「已經很厲害的人」，還是像「努力聽起來很厲害的機器人」？
