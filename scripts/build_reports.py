"""Summarize cached measurements and a separately recorded evidence audit."""
import hashlib
import json
from eb1.config import ROOT, CHAT_MODEL
from eb1.qa import validate_claims


def main():
    results = ROOT / 'evals/results'
    summary = json.loads((results / 'summary.json').read_text())
    review = json.loads((ROOT / 'evals/claim_review.json').read_text())
    supported = total = valid_claims = 0
    lines = ['# Week 2 evaluation', '',
             f'Final model: `{CHAT_MODEL}`. Public policy questions only. The two modes used the same corpus, embedding model and final answer prompt.', '',
             '## Measured results', '',
             '| Metric | Dense baseline | Hybrid + rerank |', '| --- | ---: | ---: |']
    d, h = summary['dense'], summary['hybrid']
    for label, key in [('Expected answer/clarify/refuse behavior', 'behavior_pass'), ('Request errors', 'request_errors'),
                       ('Mean gold precision@4', 'mean_gold_precision_at_4'), ('Mean gold recall@4', 'mean_gold_recall_at_4'),
                       ('p95 seconds (nearest rank)', 'p95_seconds_nearest_rank')]:
        lines.append(f"| {label} | {d[key]:.3f} | {h[key]:.3f} |")
    lines += ['', '## Per-question results', '', '| ID | Type | Behavior | Gold recall@4 | Seconds | Supported claims in audit |', '| --- | --- | --- | ---: | ---: | --- |']
    questions = json.loads((ROOT / 'evals/questions.json').read_text())
    for q in questions:
        path = results / f"{q['id']}_hybrid.json"
        row = json.loads(path.read_text(encoding='utf-8'))
        answer = row['answer']
        if answer['claims']:
            validate_claims(answer['claims'], answer['passages'])
            valid_claims += len(answer['claims'])
            entry = review['reviews'][q['id']]
            if entry.get('result_sha256') != hashlib.sha256(path.read_bytes()).hexdigest():
                raise ValueError('Evidence audit is stale; review changed outputs before reporting faithfulness.')
            flags = entry['supported']
            if len(flags) != len(answer['claims']):
                raise ValueError('Claim audit count mismatch')
            supported += sum(flags)
            total += len(flags)
            score = f'{sum(flags)}/{len(flags)}'
        else:
            score = 'N/A (no factual claims)'
        recall = row['recall_at_4']
        lines.append(f"| {q['id']} | {q['kind']} | {'Pass' if row['behavior_pass'] else 'Fail'} | {recall if recall is not None else 'N/A'} | {answer['seconds']:.2f} | {score} |")
    rate = supported / total
    lines += ['', '## Citation and claim audit', '',
              f'All {valid_claims} final hybrid claims passed source-ID and exact-excerpt checks. A separate Codex assistant evidence audit rated **{supported}/{total} claims ({rate:.1%}) fully supported** in question context. This exceeds the 90% development target but is not independent human or legal validation. The dense baseline was not separately audited for semantic claim support.', '',
              'One retained failure is C3 claim 1: the answer describes original contributions as a “mandatory criterion.” The supplied policy makes it one evidentiary route; the wording is too broad. The quote is real, which demonstrates why citation integrity is not the same as factual faithfulness. The app remains a research aid requiring source review.', '',
              '## Method and limits', '',
              '- Gold passage IDs and expected behaviors were written before the live evaluation. Nine answerable questions have 1–2 essential gold passages each; six non-answer cases are excluded from retrieval averages.',
              '- Gold precision is the fraction of four retrieved passages matching the small essential-gold set, not an exhaustive judgment that all other retrieved passages are irrelevant. Gold recall measures coverage of that set.',
              '- Behavior accuracy checks the returned status, not the full correctness of an answer. The semantic audit is reported separately and does not count refusals as supported factual claims.',
              '- Latency includes embedding, retrieval, reranking and generation. The three deterministic clarifications take approximately zero seconds. Runs used up to three concurrent evaluation requests; these small samples do not establish a stable speed advantage for hybrid retrieval.',
              '- Both modes retrieved all labeled essential evidence in this final sample. No retrieval-recall gain from reranking is claimed. The 15-question set was used during development and is not held out.',
              '- The corpus is an OCR-derived dated snapshot. Only selected source pages received visual checks. Independent review and a fresh held-out evaluation remain useful before broader use.', '',
              '## Failure analysis and iterations', '',
              '1. Direct text extraction was garbled. Upright image derivatives and LlamaParse OCR produced usable text; the original PDF was preserved.',
              '2. Table headings and generic “Considerations” labels initially lost useful section context. Cleaning now retains criterion headings and their context.',
              '3. Initial generation wrote quotations with ellipses or other changes; strict verification refused otherwise plausible answers. Evidence-ID selection now attaches exact source text in code.',
              '4. The initial model answered ambiguous category questions. A category clarification guard now handles those before retrieval.',
              '5. Source review found overbroad/tangential smaller-model claims even after behavior checks passed. The final larger model improved precision and observed latency, but one criterion-scope error remains and is explicitly scored as a failure.', '',
              'Earlier raw results are retained in `evals/iteration1`, `iteration2`, and `iteration3`. Final question definitions, raw answers, sources and timing are in `evals/questions.json` and `evals/results/`. Audit judgments are in `evals/claim_review.json`.']
    (ROOT / 'docs/WEEK2_EVALUATION.md').write_text('\n'.join(lines) + '\n', encoding='utf-8')
    summary['hybrid']['supported_claim_rate'] = {'supported': supported, 'total': total, 'rate': rate, 'reviewer': review['reviewer']}
    summary['hybrid']['citation_integrity_claims'] = valid_claims
    (results / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps({'supported': supported, 'claims': total, 'rate': rate, 'citation_integrity_claims': valid_claims}))


if __name__ == '__main__':
    main()
