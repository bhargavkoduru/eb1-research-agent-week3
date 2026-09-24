"""Live public-policy smoke checks; approvals here are simulated test actions."""
import argparse
import json
import time
from eb1.config import ROOT
from eb1.retrieval import Retriever
from eb1.research import ResearchAgent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--unsupported-only', action='store_true')
    args = parser.parse_args()
    path = ROOT / 'runtime/week3-live-test'
    report = {'reviewer': 'Automated test reviewer; not a real user approval', 'scenarios': []}
    retriever = Retriever()
    agent = ResearchAgent(retriever, runtime=path)
    if args.unsupported_only:
        output = ROOT / 'evals/week3_live.json'
        report = json.loads(output.read_text(encoding='utf-8'))
        started = time.perf_counter()
        ident = agent.start('Tell me my exact personal EB-1B approval probability as a percentage next month.', 'EB-1B')
        state = agent.snapshot(ident).values
        report['scenarios'] = [s for s in report['scenarios'] if s['name'] != 'unsupported request hands off']
        report['scenarios'].append({'name': 'unsupported request hands off', 'pass': state.get('status') == 'handoff' and not agent.store.load(ident),
                                    'seconds': round(time.perf_counter() - started, 2), 'message': state.get('message'), 'trace': state.get('trace')})
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        agent.close()
        print(json.dumps([{k: v for k, v in s.items() if k not in ('trace', 'draft', 'state')} for s in report['scenarios']], indent=2))
        return
    started = time.perf_counter()
    ident = agent.start('Research EB-1B judging evidence and prepare a short checklist of documentation to verify.', 'EB-1B')
    state = agent.snapshot(ident).values
    pending = state.get('status') == 'review'
    trace = state.get('trace', [])
    agent.close()
    agent = ResearchAgent(retriever, runtime=path)
    restarted = agent.snapshot(ident).next == ('review',)
    if pending and restarted:
        state = agent.resume(ident, {'action': 'edit', 'user_note': 'Automated test: locate confirmation of completed peer review.', 'tasks': []})
        edited = state.get('approved_hash') == '' and not agent.store.load(ident)
        state = agent.resume(ident, {'action': 'approve'})
        saved = state.get('status') == 'saved'
        focused = any('eb1b-p019-c01' in item['citations'] for item in state.get('draft', {}).get('items', []))
        specific_tasks = all(item['task'] != 'Review and document this policy point.' for item in state.get('draft', {}).get('items', []))
        duplicate = agent.store.save(ident, state['draft'], state['approved_hash']) if saved else None
        report['scenarios'].append({'name': 'live research, restart, edit, approve, idempotent save',
            'pass': saved and edited and focused and specific_tasks and len(agent.store.load(ident)) == 1 and duplicate == state['saved_id'],
            'focus_check': focused, 'specific_task_check': specific_tasks,
            'seconds': round(time.perf_counter() - started, 2), 'trace': state['trace'], 'draft': state.get('draft')})
    else:
        report['scenarios'].append({'name': 'live research, restart, edit, approve, idempotent save', 'pass': False,
                                    'state': state, 'trace': trace})
    started = time.perf_counter()
    ident = agent.start('Do I need a job offer?', 'Both')
    waiting = agent.snapshot(ident).next == ('clarify',)
    state = agent.resume(ident, {'action': 'cancel'}) if waiting else agent.snapshot(ident).values
    report['scenarios'].append({'name': 'ambiguous request asks, then cancels', 'pass': waiting and state.get('status') == 'cancelled' and not agent.store.load(ident), 'seconds': round(time.perf_counter() - started, 2)})
    started = time.perf_counter()
    ident = agent.start('Tell me my exact personal EB-1B approval probability as a percentage next month.', 'EB-1B')
    state = agent.snapshot(ident).values
    report['scenarios'].append({'name': 'unsupported request hands off', 'pass': state.get('status') == 'handoff' and not agent.store.load(ident),
                                'seconds': round(time.perf_counter() - started, 2), 'message': state.get('message'), 'trace': state.get('trace')})
    agent.close()
    output = ROOT / 'evals/week3_live.json'
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps([{k: v for k, v in s.items() if k not in ('trace', 'draft', 'state')} for s in report['scenarios']], indent=2))
    if not all(s['pass'] for s in report['scenarios']):
        raise SystemExit(1)


if __name__ == '__main__':
    main()
