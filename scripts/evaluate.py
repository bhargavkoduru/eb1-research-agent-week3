"""Live 15-question comparison. Results cache by question, mode and index version."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import statistics
from eb1.config import ROOT, CHAT_MODEL
from eb1.retrieval import Retriever, fingerprint
from eb1.qa import ask, ANSWER_PROMPT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--workers', type=int, default=3)
    args = parser.parse_args()
    questions = json.loads((ROOT / 'evals/questions.json').read_text())
    output = ROOT / 'evals/results'
    output.mkdir(parents=True, exist_ok=True)
    retriever = Retriever()
    version = hashlib.sha256((fingerprint() + CHAT_MODEL + ANSWER_PROMPT).encode()
                             + (ROOT / 'eb1/qa.py').read_bytes() + (ROOT / 'eb1/retrieval.py').read_bytes()).hexdigest()

    def run(q, mode):
        path = output / f"{q['id']}_{mode}.json"
        cache_key = hashlib.sha256((version + json.dumps(q, sort_keys=True)).encode()).hexdigest()
        if path.exists():
            cached = json.loads(path.read_text(encoding='utf-8'))
            if cached.get('cache_key') == cache_key and 'error' not in cached:
                return cached
        row = {'id': q['id'], 'mode': mode, 'kind': q['kind'], 'cache_key': cache_key, 'expected': q['expected'], 'gold_ids': q['gold_ids']}
        try:
            answer = ask(retriever, q['question'], q['category'], mode)
            retrieved = {p['id'] for p in answer['passages']}
            gold = set(q['gold_ids'])
            row.update(answer=answer, behavior_pass=answer['status'] == q['expected_status'],
                       precision_at_4=len(gold & retrieved) / len(retrieved) if gold else None,
                       recall_at_4=len(gold & retrieved) / len(gold) if gold else None,
                       human_claim_review=None, human_answer_correct=None)
        except Exception as exc:
            row.update(error=type(exc).__name__, behavior_pass=False)
        path.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding='utf-8')
        return row

    rows = []
    with ThreadPoolExecutor(max_workers=max(1, min(args.workers, 4))) as pool:
        futures = [pool.submit(run, q, mode) for q in questions for mode in ('dense', 'hybrid')]
        for future in as_completed(futures):
            row = future.result()
            rows.append(row)
            print(json.dumps({'id': row['id'], 'mode': row['mode'], 'behavior_pass': row['behavior_pass'],
                              'recall': row.get('recall_at_4'), 'seconds': row.get('answer', {}).get('seconds'), 'error': row.get('error')}), flush=True)
    summary = {}
    for mode in ('dense', 'hybrid'):
        selected = [r for r in rows if r['mode'] == mode]
        successful = [r for r in selected if 'answer' in r]
        times = sorted(r['answer']['seconds'] for r in successful)
        precisions = [r['precision_at_4'] for r in successful if r['precision_at_4'] is not None]
        recalls = [r['recall_at_4'] for r in successful if r['recall_at_4'] is not None]
        summary[mode] = {'questions': len(selected), 'request_errors': len(selected) - len(successful),
                         'behavior_pass': sum(r['behavior_pass'] for r in selected),
                         'mean_gold_precision_at_4': statistics.mean(precisions) if precisions else None,
                         'mean_gold_recall_at_4': statistics.mean(recalls) if recalls else None,
                         'p95_seconds_nearest_rank': times[min(len(times)-1, int(len(times)*.95))] if times else None,
                         'supported_claim_rate': 'Pending independent claim/evidence review; citation validation alone is not faithfulness.'}
    (output / 'summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
