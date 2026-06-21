---
name: med-check
description: Answer medical/health questions from the most authoritative medical literature and research; never rely on training data alone; answer by evidence level, mark uncertainty, cite sources
---

Answer medical and health questions from the most authoritative medical literature and research. Same spirit as `/latest`: **treat the medical knowledge in training data as a stale, possibly hallucinated candidate, not the conclusion** — every claim needs a source you actually retrieved this time.

Usage:
- `/med-check [health question]` — verify the given question
- `/med-check` — with no question, the target is the most recent medical/health question in the conversation

---

## 0. Iron rules (highest priority — violate one and start over)

- **Never use training data as the conclusion.** Every medical claim needs a source retrieved this time (PMID / guideline / authoritative-body page). Even when you think you know, search first, then answer.
- **If you can't find it, say "not enough evidence found"** — don't fill the gap from memory.
- **This is not a medical diagnosis.** For major decisions, starting/stopping medication, or worsening symptoms, tell the person to see a doctor and let a physician decide.

## 1. Catch red flags first

If the question involves an emergency red flag (chest pain, difficulty breathing, sudden one-sided weakness or slurred speech, heavy bleeding, altered consciousness, severe headache, suicidal ideation, bleeding/abdominal pain in pregnancy, high fever in an infant, etc.) → **first clearly advise seeking immediate care / the ER**, then discuss the literature. Safety always comes before verification.

## 2. Turn the plain-language question into a searchable clinical question

Break it down with PICO-lite: Population (who) / Intervention (taking what, doing what) / Comparison (compared to what) / Outcome (what effect you want to know).
List 2-3 search angles instead of searching only the core keyword (multiple angles per insight, so you don't miss relevant evidence).

## 3. Mandatory retrieval (evidence pyramid, high to low — reach at least level 3)

1. **Systematic reviews / meta-analyses** — highest evidence. `WebSearch` with `allowed_domains` locked to `cochranelibrary.com`, and search PubMed for systematic reviews / meta-analyses.
2. **Clinical guidelines** — UpToDate, NICE (`nice.org.uk`), USPSTF, specialty medical societies, national health authorities (`gov` sites). Look at consensus, not a single study.
3. **PubMed primary research** — `WebFetch` the free E-utilities API (no key needed):
   - esearch (get PMIDs):
     `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={query}&retmax=5&sort=relevance&retmode=json`
   - efetch (get abstracts):
     `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={comma-separated PMIDs}&rettype=abstract&retmode=text`
   - Study-quality ranking: RCT > cohort > case-control > case report / animal / in vitro. **Note the year, flag old studies, don't treat small samples as settled.**
   - **PubMed query pitfalls (tested):** ① AND-ing several terms together often returns off-topic papers under relevance sort (e.g. asking about a clinical effect but pulling chemical-synthesis papers). **Always read the efetch abstract to confirm it's on-topic before citing** — citing on a matching title alone will go wrong. ② Don't force `meta-analysis` / `systematic[sb]` as free terms in the query — it returns 0 results. To find high-evidence work, use WebSearch for Cochrane or filter by Article type on the PubMed site, not by stuffing the API term.
4. **Authoritative health bodies** — WHO, CDC, FDA, NIH/MedlinePlus (`WebSearch` locked to these domains), as public-health-level corroboration.

Print the actual esearch / efetch URLs you call, so the retrieval is checkable and reproducible.

## 4. Synthesize and grade

Tag each conclusion with an evidence level:
- ✅ **Supported** — high-quality studies or guidelines agree
- ⚠️ **Insufficient evidence** — only small samples / preliminary studies / animal experiments
- ❓ **Conflicting evidence** — studies or guidelines disagree; spell out where the split is

Include the level of consensus (do multiple guidelines agree), sample size, and year. **Never present a single small study as settled.**

## 5. Output format (concise, for your own use, no padding)

1. **Direct answer** + evidence-level tag
2. **Key evidence**, 2-4 points, each with a source (PMID link / guideline name / agency page)
3. **Uncertainty / points of dispute** (if any)
4. **When to see a doctor** — situations where you shouldn't self-judge
5. One-line disclaimer: this is a literature summary, not a medical diagnosis

## 6. When you can't find it

Honestly say "I can't currently find enough high-quality evidence". You may explain which sources you searched and why there's no result, but **never fall back on training data to invent an answer**. That's the whole reason this skill exists.
