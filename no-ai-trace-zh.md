---
name: no-ai-trace-zh
description: Self-check Chinese writing for AI traces (READMEs, docs, messages, reports) before sending or pushing. Use it when the text is mainly Chinese, and use /no-ai-trace when it's mainly English.
---

A self-check for removing AI writing traces from Chinese text. The rules below are self-contained, so this command runs on its own. It pairs well with `/no-ai-trace`, which covers the general 17 rules for English.

Core principle: a person writing Chinese is explaining one thing clearly. AI writing Chinese is often performing "I'm careful", "I'm well structured", "I'm professional".

Use it on Chinese-first outward-facing text: READMEs, zh-TW docs, messages, reports, Chinese PR descriptions. Anything a third person will read gets the full check, even if it's "just" a status update to a manager.

Usage:
- `/no-ai-trace-zh` checks the most recent piece of Chinese writing in the conversation
- `/no-ai-trace-zh [paste text]` checks the given text
- `/no-ai-trace-zh <file path>` checks the given file

Steps:

1. Confirm what to check.
   - Text or a path after the command: check that.
   - Nothing given: check the most recent Chinese writing output in the conversation, including files you just wrote or edited.

2. Run the mechanical greps first (see "Mechanical greps" below). Judge every hit by hand, because a hit is only a candidate.

3. Scan Part Z (Z1 to Z11), then the baseline checks (G1 to G6). Judge semantic patterns sentence by sentence.

4. Run the "Self-check before output" list at the end.

5. Output format (fixed):
   - First line: 「共發現 N 處違規」 (Found N issues). Say it even when N is 0.
   - Per issue: `[Z# or G# rule name] original sentence` then the suggested rewrite.
   - For 「不是…而是…」 patterns, judge each hit. Rhetorical lift counts as an issue. A factual boundary line ("this repo doesn't do X") is marked 「保留」 (keep) with a one-sentence reason.
   - Last line: an overall tone verdict in one sentence. Does it read like a person explaining something, or like an AI product description or talk-you-out-of-it essay?

6. At 0 issues, the tone verdict must also pass before you output 「✓ 通過」.

## Mechanical greps

Run these on the target file. Treat each hit as a candidate and judge it in context.

- Meta labels: `誠實的範圍|重要說明|溫馨提醒|特別注意|核心洞察|一句話總結`
- Contrast frames: `不是.{0,20}而是|並非.{0,20}而是|與其說.{0,20}不如`
- Fake-formal transitions: `值得注意的是|需要強調的是|綜上所述|總的來說|不得不說`
- Verb padding: `進行(處理|優化|分析|檢查|評估)`
- Em dash, including the Chinese double dash: `grep -n "$(printf '\xe2\x80\x94')" file`
- Parenthetical asides: full-width `（[^）]{1,80}）` and half-width `\([A-Za-z ]{2,}\)`. Judge each hit. Informational asides can be marked 「保留」. Code comments and variable names like `(el)` are excluded. The range goes up to 80 characters because long asides that contain URLs slip past a short range.

---

## Part Z: Chinese red flags

The moment one of these patterns appears, delete or rewrite. Chinese names, criteria and example sentences stay in Chinese. A short English gloss follows where it helps.

### Z1. 元敘事標籤 (Meta-narrative labels, among the worst)

A heading or callout that announces the writer's stance instead of writing the content. Typical phrases:

- 誠實的範圍、誠實講、坦率地說、必須先說清楚
- 重要說明、溫馨提醒、特別注意、特別聲明
- 核心洞察、關鍵收穫、一句話總結、快速總覽
- 給讀者的話、在開始之前

- (X) `> **誠實的範圍。** 這個工具目前沒有離線模式…`
- (X) `## 重要說明`
- (X) `坦率地說，這個工具有極限。`

Fix: delete the label and write the limit or the point straight into one sentence of body text. If you need a section, use a neutral heading such as 「範圍」「限制」「怎麼用」 (scope, limits, how to use). Don't advertise your own honesty.

- (O) `這個工具目前沒有離線模式，資料需要連網同步。`

### Z2. 否定前提對比 (Negated-premise contrast, very common in Chinese)

The Chinese-specific form of the "not A but B" pattern. Fix on sight unless it's a factual boundary (see the exception below).

- 不是…而是…、並非…而是…、與其說…不如…、不在於…而在於…
- 不是 X 的替代，而是 Y (as an opener this stacks a talk-you-out-of-it tone on top of the contrast)

- (X) `這不是 Excel 的替代品，而是互補工具。`
- (X) `我們不是在追求速度，而是在追求品質。`

- (O) `Excel 仍負責日常試算，這個工具專做資料清洗。`
- (O) `我們優先品質。`

Exception (mark 「保留」 when checking): when you're really drawing a boundary and telling the reader "we don't do A", say it flat. Don't force the "not A but B" frame. Example: `本 repo 不做 memory 同步。` (This repo doesn't sync memory.)

### Z3. 翻譯腔／公文腔 (Translationese and officialese)

- 進行 + verb: `進行處理`、`進行優化`、`進行分析`, so use the verb directly
- 具有…的能力／具備…功能, so use 能…、可…
- 在…方面、就…而言 used as a filler opener
- 「針對…進行…」「基於…進行…」

- (X) `本工具可針對查詢進行多角度分析。`
- (O) `多角度搜尋後再回答。`

### Z4. 假正式過渡與 hedge (Fake-formal transitions and hedges)

- 值得注意的是、需要強調的是、不得不說、總的來說、總體而言、綜上所述、由此可見
- 在某種程度上、從某種意義上說、相對而言 (when there's no baseline to compare against)

- (X) `值得注意的是，備援伺服器通常比主機慢。`
- (O) `備援伺服器通常比主機慢。`

### Z5. 開場暖場／自我矮化 (Warm-up openers and self-deprecation)

- 在當今…、隨著 AI 的發展…、不可否認…
- 「先講結論再展開」 used as an empty heading, when no conclusion actually comes first
- Opening with 「做不到／不是替代／限制很多」 as if it were the selling point

Delete them. Start from what the reader wants to do or what they get.

### Z6. 空泛抬升 (Empty amplification)

- 不僅…更…、不但…還… (when both halves carry the same information)
- 全面、深度、顯著、有效提升 (with no number or example)

- (X) `這不僅提升效率，更能顯著改善品質。`
- (O) `同樣的問題，加前綴後會標來源日期、分開事實與意見。`

### Z7. 模板序號腔 (Template numbering)

Use 「首先…其次…最後…」 only when the steps really have an order. If it's a rhetorical skeleton applied to every paragraph, switch to topic subheadings or plain bullets.

### Z8. 文件開場套話 (Document-opening boilerplate)

- 本文以 A 作為 B 的簡稱 (shorten it, or just define it at first use)
- 本專案旨在…、本倉庫的目標是…

- (X) `本文以 CLI 作為命令列介面的簡稱，以 PR 作為合併請求的簡稱。`
- (O) `文中 CLI = 命令列介面，PR = 合併請求。`

Or write the full name once at first use and put the abbreviation in parentheses.

### Z9. 括號補述、破折號 (Parenthetical asides and em dashes)

Chinese text bans the em dash character (U+2014) just like English does, and that includes the Chinese double-dash form. Fold a parenthetical into the main sentence when you can, and otherwise give it its own sentence.

A Chinese term followed by its English original or a glossary translation, such as `同儕帶領（peer-led）` or `跨部門協作（cross-functional collaboration）`, also counts as an issue. It makes the main sentence heavy even when the aside only annotates the term. If the Chinese term already says it, drop the English parenthetical. If you truly need the original term (a proper noun, an industry abbreviation), use the English alone and don't put the two side by side.

- (X) `改用同儕帶領（peer-led）取代高價講師或活動公司`
- (O) `改用同儕帶領取代高價講師或活動公司`

### Z10. 結論段勸退腔 (Talk-you-out-of-it endings)

If the closing paragraph is only 「所以別指望／只留一件小事／其餘一切仍靠 X」, the reader has already left.

- (X) `留著它做一件事就好。其餘一切，Word 仍是主力。`
- (O) `日常編輯用 Word，需要批次轉檔時用這個工具。`

### Z11. 假對稱「能／不能」 (Fake-symmetric "can / can't")

Two chapters of equal length, one for "what it can do" and one for "what it can't", let the limits compete with the selling points for space. Put the limits in one short 「範圍」 paragraph at the end instead of splitting the page in half.

---

## Baseline checks (G1 to G6)

These general patterns show up in Chinese too. They're written out here so the command doesn't depend on any other file.

### G1. 反問自答 (Rhetorical question and self-answer)

- (X) `這對交易者意味著什麼？意味著更快的成交與更低的成本。`
- (O) `交易者拿到更快的成交與更低的成本。`

### G2. 「X 是真實的」確認句 ("The X is real" confirmations)

- (X) `這個需求是真實存在的。` `這個缺口是真實的。`
- (O) `半年內需求成長了三倍。`

Replace it with a concrete number or fact.

### G3. 碎句排比 (Fragment parallelism for fake drama)

- (X) `新的團隊。新的規則。新的賽局。`
- (O) `新團隊帶來新規則，賽局也不一樣了。`

Merge into one sentence or keep just one of the three.

### G4. 二元框架加感傷代價句 (Binary framing with a sentimental cost line)

- (X) `一場會議，兩種結果，都有代價。`
- (O) `偏鴿的結果，三天內大盤可能漲 4% 到 6%。偏鷹的結果，成長股當天跌約 3%。`

State the probability or magnitude.

### G5. 並列主詞拆句 (Parallel-subject splitting)

- (X) `甲隊晉級。乙隊晉級。`
- (O) `甲隊和乙隊都晉級了。`

### G6. 行話堆疊 (Buzzword stacking)

- Stacks like 賦能、抓手、閉環、打造生態、全方位、一站式 with no concrete claim behind them
- (X) `本平台賦能開發者，打造全方位協作閉環。`
- (O) `開發者可以在同一個頁面寫程式、審查、部署。`

---

## Self-check before output (must pass every time)

- Meta labels: any 「誠實的範圍／重要說明／溫馨提醒」 style label?
- Contrast: any 「不是…而是…」 as an opener or used repeatedly?
- Officialese: any 「進行 X」「具有…能力」「值得注意的是」?
- Opening: does it state the purpose directly, or start with a disclaimer or a talk-you-out-of-it?
- Limits: has a limitation been inflated into a chapter as big as the selling points?
- Warm-ups and empty lifts: any 「在當今…」「不僅…更…」「全面／深度／顯著」 with no number behind it?
- Numbering: is 「首先…其次…最後…」 used where the steps have no real order?
- Parentheses and dashes: any em dash? Any parenthetical aside, including a Chinese term with an English gloss?
- Baseline: any rhetorical self-answer (G1), "is real" confirmation (G2), stacked fragments (G3), binary cost line (G4), split parallel subjects (G5), or buzzword stack (G6)?
- Overall tone: does it read like a person explaining something, or like a "responsible AI product description"?
