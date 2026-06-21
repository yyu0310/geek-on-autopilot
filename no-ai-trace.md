A general-purpose self-check for removing AI writing traces. Works on both English and Chinese output.

Usage:
- `/no-ai-trace` — check the most recent piece of writing in the conversation
- `/no-ai-trace [paste text]` — check the given text

Steps:

1. Confirm what to check:
   - Text pasted after the command → check that.
   - None → check the most recent writing output in the conversation.

2. Scan against the Part 1 red-flag list (Rules 1–17), rule by rule. Catch the mechanically detectable ones directly; judge the semantic ones sentence by sentence.

3. Run the final "self-check before output" list below.

4. Output format (fixed):
   - First line: "Found N issues" (say it even if 0)
   - Per issue: `[Rule X name] original sentence` → suggested rewrite (per Part 2 below)
   - Last line: an overall tone verdict, one sentence — does it read like a human or a robot?

5. At 0 issues: the tone verdict must also pass before you output "✓ passed".

---

## Part 1: Red flags

The moment these patterns appear, delete or rewrite.

### 1. Jargon stacking

Banned words: `leverage`, `utilize`, `synergy`, `robust framework`, `holistic approach`, `actionable insights`, `delve`

- (X) `We must leverage our core competencies to achieve synergy.`
- (X) `Let's delve into the key findings of this report.`

Banned adverb/adjective stacking: `highly`, `incredibly`, `deeply`, `seamlessly`, `cutting-edge`, `transformative`, `world-class`, `state-of-the-art`

- (X) `This is a highly effective and incredibly powerful solution that seamlessly integrates with your workflow.`

### 2. Negated-premise contrast

Banned pattern: `...is not just [A]; it is also [B]...` and every variant of "negate a premise, then give a positive conclusion", including the Chinese「不是…，而是…」.

- (X) `This solution is not just efficient; it is also scalable.`
- (X) `They see the hardware, not the doctrine.`
- (X) `He's not preparing for an invasion; he's manufacturing consent for other pressure.`
- (X) 這不是一個工具，而是一個生態系統。
- (X) 我們不是在追求速度，而是在追求品質。

### 3. Nominalized ability/state

- (X) `This software has the ability to detect errors.`
- (X) `This framework provides the capability of scaling.`
- (X) `The team's responsibility is the management of risk.`
- (X) `The team made a decision to proceed.`

### 4. No contractions (English) / translationese (Chinese)

- (X) `I am confident that it is the right decision.`
- (X) Chinese that reads as stiff, unnatural translationese

### 5. Warm-up openers

- (X) `In today's fast-paced world, efficiency matters.`
- (X) `It is undeniable that the market is shifting.`
- (X) `In the complex landscape of modern finance...`

### 6. Passive / container sentences

- (X) `This report contains an analysis of the market.`
- (X) `The data provides an indication of the trend.`

### 7. Roundabout metaphors

- (X) `The findings of the study serve to illuminate the problem.`
- (X) `This initiative aims to facilitate the growth of the ecosystem.`

### 8. Abstract phase descriptions

- (X) `The project is currently in the implementation phase.`
- (X) `We are in the process of evaluating potential solutions.`

### 9. Em dash

Never use `—` under any circumstances; use a comma or restructure the sentence.

- (X) `The results were clear — we needed a new approach.`
- (X) `The product is built for traders — not institutions.`

### 10. "The X is real" confirmation

AI uses these to confirm the reader's emotion, sounding like it's answering on the reader's behalf. Delete and replace with a concrete statement.

- (X) `The demand is real.`
- (X) `The gap is real.`
- (X) `The opportunity is real.`

### 11. Parenthetical asides

A parenthetical weakens the main clause. Restructure into a standalone sentence, or just cut it.

- (X) `The platform provides liquidity solutions (especially for institutional players) across major chains.`
- (X) `The token (which launched in Q1) has seen strong volume growth.`

### 12. Rhetorical question and self-answer

AI loves a question to build suspense, then answers it itself. Cut the question, state the conclusion.

- (X) `So what does this mean for traders? It means faster execution and lower costs.`
- (X) `Why does this matter? Because liquidity determines price.`

### 13. Transition-word overuse

`Furthermore`, `Moreover`, `Additionally`, `In conclusion`, `To summarize` are AI's favorite paragraph glue; using them reads like a report template.

- (X) `Furthermore, the platform supports multiple chains. Moreover, fees are competitive.`
- (X) `In conclusion, this represents a significant step forward.`

### 14. Hedge sentences

These fake humility while wasting the reader's time. Delete, get to the point.

- (X) `It's worth noting that the market has shifted significantly.`
- (X) `It should be mentioned that this approach carries some risk.`
- (X) `It's important to understand that results may vary.`

### 15. Fragment parallelism for fake drama

Three short sentences in a row, each with parallel structure, manufacturing a fake sense of "history" or "tension".

- (X) `New dot plot. New tone. New era.`
- (X) `New team. New rules. New game.`
- (X) `One decision. One moment. One chance.`

### 16. Binary framing + sentimental cost line

A "one event, two outcomes" frame capped with "both have a price", manufacturing artificial tension.

- (X) `One meeting, two outcomes, and both have a price.`
- (X) `One number, two readings, and neither is free.`
- (X) `Two paths. One decision. Everything changes.`

### 17. Parallel-subject splitting (fake concision)

Same action, different subjects, each as its own sentence. Mechanically cutting one complete fact into two.

- (X) `T1 finished. HLE finished.`
- (X) `Sinner withdrew. Alcaraz withdrew.`
- (X) `France qualified. Spain qualified.`

---

## Part 2: Rewrites (Do's)

### 1. Jargon stacking → the simplest, most direct word

`use` and `leverage` / `utilize` mean the same thing; always pick `use`.

- (O) `We should use our team's strengths to work better together.`
- (O) `This report examines the key findings.`

### 2. Negated-premise contrast → state the positive fact directly

Cut the first half, just say B.

- (O) `This solution is efficient and scalable.`
- (O) 這是一個生態系統。
- (O) 我們追求品質。

### 3. Nominalized ability/state → strong verb

- (O) `This software detects errors.`
- (O) `This framework scales.`
- (O) `The team manages risk.`
- (O) `The team decided to proceed.`

### 4. No contractions → contractions + colloquial

- (O) `I'm confident it's the right call.`
- Contractions: `I'm`, `it's`, `that's`, `you're`, `we're`, `they're`, `don't`, `can't`

### 5. Warm-up openers → cut them, get to the point

### 6. Passive / container sentences → active voice

- (O) `This report analyzes the market.`
- (O) `The data indicates the trend.`

### 7. Roundabout metaphors → the most direct verb

- (O) `The findings explain the problem.`
- (O) `This initiative expands the ecosystem.`

### 8. Abstract phase descriptions → concrete action or number

- (O) `We're reviewing three vendors this week.`
- (O) `The project is 50% complete.`

### 9. Em dash → comma or restructure

- (O) `The results were clear, and we needed a new approach.`

### 10. "The X is real" → concrete statement

- (O) `Demand has grown 3x in six months.`
- (O) `The gap shows up in every liquidity report.`

### 11. Parenthetical asides → fold into the main clause or cut

- (O) `The platform provides liquidity solutions across major chains, with particular depth for institutional players.`

### 12. Rhetorical question and self-answer → state the conclusion

- (O) `Liquidity determines price.`

### 13. Transition-word overuse → restructure, let the logic speak

- (O) `The platform supports multiple chains and keeps fees competitive.`

### 14. Hedge sentences → cut them, say the point

- (O) `The market has shifted significantly.`

### 15. Fragment parallelism → combine into a full sentence, or keep just one

- (O) `Warsh's first FOMC brings a new dot plot and a different tone.`

### 16. Binary sentimental ending → state the probability or consequence

- (O) `A dovish tilt likely pushes QQQ up 4–6% within 72 hours. A hawkish surprise cuts growth stocks 3% on the day.`

### 17. Parallel-subject splitting → combine into one sentence

- (O) `T1 and HLE both finished the regular season.`
- (O) `Both Sinner and Alcaraz withdrew.`
- (O) `France and Spain both qualified.`

---

## Self-check before output (must pass every time)

- Jargon: any banned words like `leverage` / `utilize` / `synergy` / `delve` / `robust` / `holistic` / `actionable`?
- Adverbs/adjectives: any stacking like `highly` / `incredibly` / `seamlessly` / `cutting-edge` / `transformative`?
- Contrast: any "not just A, but B" / 「不是…而是…」or any negated-premise pattern?
- Nominalized ability: any "has the ability to" / "made a decision to" / "the detection of"?
- Contractions: in English, using `I'm` / `it's` / `you're`? In Chinese, does it read like something a person would actually say?
- Openers: any warm-up like "In today's..." / "It is undeniable that..."?
- Container sentences: any structure like `contains an analysis of` / `provides an indication of`?
- Roundabout: any winding verbs like `serve to illuminate` / `aims to facilitate`?
- Abstract phase: any vague description like "in the implementation phase"? Change to a real action or number.
- Em dash: any `—`? Replace all with commas or restructure.
- Confirmation: any "the X is real"? Replace with a concrete number or fact.
- Parentheses: any parenthetical asides? Restructure or cut.
- Rhetorical: any question followed by self-answer? Cut the question, state the conclusion.
- Transitions: any `Furthermore` / `Moreover` / `In conclusion`? Restructure.
- Hedge: any "It's worth noting" / "It should be mentioned"? Cut it.
- Fragment parallelism: three short sentences stacked for drama? Combine into one or keep just one.
- Binary sentiment: any "One X, two outcomes, and both have a price" ending? Replace with a concrete probability and magnitude.
- Parallel splitting: any "X did Y. Z did Y." structure? Combine into one sentence.
- Overall tone: does it read like "someone who's already good", or like "a robot trying hard to sound good"?
