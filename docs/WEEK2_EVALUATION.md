# Week 2 evaluation

Original evaluation model: `Qwen/Qwen3-235B-A22B-Instruct-2507`. Public policy questions only. The two modes used the same corpus, embedding model and final answer prompt.

## Measured results

| Metric | Dense baseline | Hybrid + rerank |
| --- | ---: | ---: |
| Expected answer/clarify/refuse behavior | 15.000 | 15.000 |
| Request errors | 0.000 | 0.000 |
| Mean gold precision@4 | 0.389 | 0.389 |
| Mean gold recall@4 | 1.000 | 1.000 |
| p95 seconds (nearest rank) | 10.280 | 7.570 |

## Per-question results

| ID | Type | Behavior | Gold recall@4 | Seconds | Supported claims in audit |
| --- | --- | --- | ---: | ---: | --- |
| D1 | direct | Pass | 1.0 | 7.57 | 3/3 |
| D2 | direct | Pass | 1.0 | 2.60 | 2/2 |
| D3 | direct | Pass | 1.0 | 4.69 | 3/3 |
| D4 | direct | Pass | 1.0 | 5.51 | 3/3 |
| D5 | direct | Pass | 1.0 | 4.80 | 3/3 |
| D6 | direct | Pass | 1.0 | 6.00 | 3/3 |
| C1 | cross_chapter | Pass | 1.0 | 3.88 | 3/3 |
| C2 | cross_chapter | Pass | 1.0 | 4.10 | 3/3 |
| C3 | cross_chapter | Pass | 1.0 | 6.05 | 2/3 |
| A1 | ambiguous | Pass | N/A | 0.00 | N/A (no factual claims) |
| A2 | ambiguous | Pass | N/A | 0.00 | N/A (no factual claims) |
| A3 | ambiguous | Pass | N/A | 0.00 | N/A (no factual claims) |
| U1 | unanswerable | Pass | N/A | 3.36 | N/A (no factual claims) |
| U2 | unanswerable | Pass | N/A | 2.66 | N/A (no factual claims) |
| U3 | unanswerable | Pass | N/A | 3.86 | N/A (no factual claims) |

## Citation and claim audit

All 26 final hybrid claims passed source-ID and exact-excerpt checks. A separate Codex assistant evidence audit rated **25/26 claims (96.2%) fully supported** in question context. This exceeds the 90% development target but is not independent human or legal validation. The dense baseline was not separately audited for semantic claim support.

One retained failure is C3 claim 1: the answer describes original contributions as a “mandatory criterion.” The supplied policy makes it one evidentiary route; the wording is too broad. The quote is real, which demonstrates why citation integrity is not the same as factual faithfulness. The app remains a research aid requiring source review.

## Method and limits

- Gold passage IDs and expected behaviors were written before the live evaluation. Nine answerable questions have 1–2 essential gold passages each; six non-answer cases are excluded from retrieval averages.
- Gold precision is the fraction of four retrieved passages matching the small essential-gold set, not an exhaustive judgment that all other retrieved passages are irrelevant. Gold recall measures coverage of that set.
- Behavior accuracy checks the returned status, not the full correctness of an answer. The semantic audit is reported separately and does not count refusals as supported factual claims.
- Latency includes embedding, retrieval, reranking and generation. The three deterministic clarifications take approximately zero seconds. Runs used up to three concurrent evaluation requests; these small samples do not establish a stable speed advantage for hybrid retrieval.
- Both modes retrieved all labeled essential evidence in this final sample. No retrieval-recall gain from reranking is claimed. The 15-question set was used during development and is not held out.
- The corpus is an OCR-derived dated snapshot. Only selected source pages received visual checks. Independent review and a fresh held-out evaluation remain useful before broader use.

## Failure analysis and iterations

1. Direct text extraction was garbled. Upright image derivatives and LlamaParse OCR produced usable text; the original PDF was preserved.
2. Table headings and generic “Considerations” labels initially lost useful section context. Cleaning now retains criterion headings and their context.
3. Initial generation wrote quotations with ellipses or other changes; strict verification refused otherwise plausible answers. Evidence-ID selection now attaches exact source text in code.
4. The initial model answered ambiguous category questions. A category clarification guard now handles those before retrieval.
5. Source review found overbroad/tangential smaller-model claims even after behavior checks passed. The final larger model improved precision and observed latency, but one criterion-scope error remains and is explicitly scored as a failure.

Earlier raw results are retained in `evals/iteration1`, `iteration2`, and `iteration3`. Final question definitions, raw answers, sources and timing are in `evals/questions.json` and `evals/results/`. Audit judgments are in `evals/claim_review.json`.

## Current runtime

The default model and timeout handling have since changed. See [the response-time follow-up](PERFORMANCE.md). The measurements above remain the original Qwen baseline.
