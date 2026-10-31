---
name: med-check
description: Answer medical/health questions from the most authoritative medical literature and research; never rely on training data alone; answer by evidence level, mark uncertainty, cite sources
---

Answer medical and health questions from the most authoritative medical literature and research. Same spirit as `/latest`: **treat the medical knowledge in training data as a stale, possibly hallucinated candidate, not the conclusion**: every claim needs a source you actually retrieved this time.

Usage:
- `/med-check [health question]`: verify the given question
- `/med-check`: with no question, the target is the most recent medical/health question in the conversation

---

## 0. Iron rules (highest priority, violate one and start over)

- **Never use training data as the conclusion.** Every medical claim needs a source retrieved this time (PMID / guideline / authoritative-body page). Even when you think you know, search first, then answer.
- **If you can't find it, say "not enough evidence found"**: don't fill the gap from memory.
- **This is not a medical diagnosis.** For major decisions, starting/stopping medication, or worsening symptoms, tell the person to see a doctor and let a physician decide.

## 1. Catch red flags first

If the question involves an emergency red flag (chest pain, difficulty breathing, sudden one-sided weakness or slurred speech, heavy bleeding, altered consciousness, severe headache, suicidal ideation, bleeding/abdominal pain in pregnancy, high fever in an infant, etc.) → **first clearly advise seeking immediate care / the ER**, then discuss the literature. Safety always comes before verification.

## 2. Turn the plain-language question into a searchable clinical question

Break it down with PICO-lite: Population (who) / Intervention (taking what, doing what) / Comparison (compared to what) / Outcome (what effect you want to know).
List 2-3 search angles instead of searching only the core keyword (multiple angles per insight, so you don't miss relevant evidence).

**Question-type branch: looking up a physician's publications.** When the question is "what has Dr. X published" rather than a health question, take this route and skip the evidence pyramid below:
- Add `-g` when calling PubMed E-utilities with curl. Without it, curl treats the brackets in `[au]` as a glob and the response comes back empty.
- For authors who share the same initials, compare ForeName and affiliation in the efetch XML to rule out different people with the same name.
- Before 2014, PubMed mostly recorded only the first author's affiliation, so judge by the first author's affiliation plus the topic.

## 2b. Pre-search checks

- **Objective function:** what are the gains and the risks in this question? If the person hasn't said, ask first.
- **Decision relevance:** if you would do the same thing whatever the search finds, don't search. Say why instead (example: picking between two multivitamin brands, where the advice is the same either way).

## 3. Mandatory retrieval (evidence pyramid, high to low, stop at the first level that answers the question)

Dig further only in three cases: the guidelines are silent on a question that affects a decision, the guidelines contradict each other, or the person is making a major decision. The iron rules in section 0 still hold: stopping at the guideline level still needs a source you actually retrieved this time. Digging down to single studies on every question just surfaces contradictory noise, and a conclusion solid enough to act on is usually available at the guideline level.

1. **Systematic reviews / meta-analyses**: highest evidence. `WebSearch` with `allowed_domains` locked to `cochranelibrary.com`, and search PubMed for systematic reviews / meta-analyses.
2. **Clinical guidelines**: UpToDate, NICE (`nice.org.uk`), USPSTF, specialty medical societies, national health authorities (`gov` sites). Look at consensus, not a single study.
3. **PubMed primary research**: `WebFetch` the free E-utilities API (no key needed):
   - esearch (get PMIDs):
     `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term={query}&retmax=5&sort=relevance&retmode=json`
   - efetch (get abstracts):
     `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id={comma-separated PMIDs}&rettype=abstract&retmode=text`
   - Study-quality ranking: RCT > cohort > case-control > case report / animal / in vitro. **Note the year, flag old studies, don't treat small samples as settled.**
   - **PubMed query pitfalls (tested):** ① AND-ing several terms together often returns off-topic papers under relevance sort (e.g. asking about a clinical effect but pulling chemical-synthesis papers). **Always read the efetch abstract to confirm it's on-topic before citing**: citing on a matching title alone will go wrong. ② Don't force `meta-analysis` / `systematic[sb]` as free terms in the query, it returns 0 results. To find high-evidence work, use WebSearch for Cochrane or filter by Article type on the PubMed site, not by stuffing the API term.
   - **Source pitfalls (tested):** ① WebFetch on a Cochrane full-text page returns HTTP 412. Use esearch to find the PubMed abstract of the same review instead (journals often publish a condensed version). ② An efetch abstract won't show an expression of concern or a retraction, so before citing a key paper, search once more for its title plus "expression of concern" or "retraction". ③ WebSearch snippets can dress up a blog's claim as a research finding. For any mechanism explanation (the "why"), check the discussion section of the original paper (such as the PMC full text) and note whether the authors say "may" or state it as settled.
4. **Authoritative health bodies**: WHO, CDC, FDA, NIH/MedlinePlus (`WebSearch` locked to these domains), as public-health-level corroboration.

Print the actual esearch / efetch URLs you call, so the retrieval is checkable and reproducible.

## 4. Synthesize and grade

Tag each conclusion with an evidence level:
- ✅ **Supported**: high-quality studies or guidelines agree
- ⚠️ **Insufficient evidence**: only small samples / preliminary studies / animal experiments
- ❓ **Conflicting evidence**: studies or guidelines disagree; spell out where the split is

Include the level of consensus (do multiple guidelines agree), sample size, and year. **Never present a single small study as settled.**

**When the guidelines are silent, there is no standard answer.** For a detail question with no decision at stake, label it as noise, suggest the person pick whatever they like and can keep doing, and don't dig into papers.

## 5. Output format (concise, for your own use, no padding)

1. **Direct answer** + evidence-level tag
2. **Key evidence**, 2-4 points, each with a source (PMID link / guideline name / agency page)
3. **Uncertainty / points of dispute** (if any)
4. **When to see a doctor**: situations where you shouldn't self-judge
5. One-line disclaimer: this is a literature summary, not a medical diagnosis

**Label your sources.** Mark each conclusion with its source type (guideline / original systematic review / single study / AI synthesis), and check every number in the conclusion against the number in the efetch abstract. This keeps a review's findings, a single study, and your own judgment from blending together.

## 6. When you can't find it

Honestly say "I can't currently find enough high-quality evidence". You may explain which sources you searched and why there's no result, but **never fall back on training data to invent an answer**. That's the whole reason this skill exists.
