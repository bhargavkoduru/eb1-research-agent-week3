import json
import sqlite3
import pytest
from eb1.qa import validate_claims, answer_from_passages
from eb1.research import ResearchAgent, Store, digest

PASSAGE = {'id': 'eb1b-p019-c01', 'document_id': 'eb1b', 'source_pdf_page': 19,
           'printed_manual_page': 803, 'source_url': 'https://www.uscis.gov/policy-manual/volume-6-part-f-chapter-3',
           'section': 'Criterion 4: Judging', 'text': 'The petitioner must show actual participation in judging the work of others.'}
CLAIM = {'text': 'Document actual judging participation.', 'citations': [PASSAGE['id']],
         'quotes': [{'id': PASSAGE['id'], 'text': PASSAGE['text']}]}


class FakeRetriever:
    def search(self, *args, **kwargs):
        return [PASSAGE], None


def planner(_system, state):
    return {'action': 'search_policy' if not state['evidence'] else 'draft_checklist', 'query': 'judging evidence', 'message': 'Find and review judging evidence.'}


def answerer(*args):
    return {'status': 'answered', 'claims': [json.loads(json.dumps(CLAIM))], 'message': ''}


def new_agent(tmp_path, **kwargs):
    return ResearchAgent(kwargs.pop('retriever', FakeRetriever()), runtime=tmp_path,
                         planner=kwargs.pop('planner', planner), answerer=answerer, **kwargs)


def test_citations_reject_unknown_and_invented_quotes():
    validate_claims([CLAIM], [PASSAGE])
    bad = json.loads(json.dumps(CLAIM))
    bad['quotes'][0]['text'] = 'USCIS guarantees approval in every case.'
    with pytest.raises(ValueError):
        validate_claims([bad], [PASSAGE])
    bad['citations'] = ['unknown']
    with pytest.raises(ValueError):
        validate_claims([bad], [PASSAGE])


def test_no_evidence_refuses_without_model():
    assert answer_from_passages('Can I qualify?', 'Both', [])['status'] == 'unsupported'


def test_store_requires_exact_draft_approval(tmp_path):
    store = Store(tmp_path / 'store.sqlite')
    draft = {'title': 'original'}
    approved = digest(draft)
    with pytest.raises(PermissionError):
        store.save('session', draft, '')
    with pytest.raises(PermissionError):
        store.save('session', {'title': 'modified'}, approved)
    first = store.save('session', draft, approved)
    assert store.save('session', draft, approved) == first
    assert len(store.load('session')) == 1


def test_approval_persists_and_is_idempotent(tmp_path):
    agent = new_agent(tmp_path)
    ident = agent.start('Research EB-1B judging', 'EB-1B')
    assert agent.snapshot(ident).next == ('review',)
    assert agent.store.load(ident) == []
    state = agent.resume(ident, {'action': 'approve'})
    assert state['status'] == 'saved'
    assert agent.store.save(ident, state['draft'], state['approved_hash']) == state['saved_id']
    assert len(agent.store.load(ident)) == 1
    agent.close()


def test_restart_edit_reapprove(tmp_path):
    first = new_agent(tmp_path)
    ident = first.start('Research EB-1B judging', 'EB-1B')
    first.close()
    resumed = new_agent(tmp_path)
    assert resumed.snapshot(ident).next == ('review',)
    state = resumed.resume(ident, {'action': 'edit', 'user_note': 'Check the completed review email.', 'tasks': ['Locate completed review evidence.']})
    assert state['status'] == 'review' and state['approved_hash'] == ''
    assert resumed.store.load(ident) == []
    assert resumed.snapshot(ident).next == ('review',)
    state = resumed.resume(ident, {'action': 'approve'})
    assert state['status'] == 'saved'
    assert resumed.store.load(ident)[0]['draft']['user_note'] == 'Check the completed review email.'
    resumed.close()


def test_cancel_never_saves(tmp_path):
    agent = new_agent(tmp_path)
    ident = agent.start('Research judging', 'EB-1B')
    state = agent.resume(ident, {'action': 'cancel'})
    assert state['status'] == 'cancelled'
    assert agent.store.load(ident) == []
    agent.close()


def test_clarification_remembered_across_restart(tmp_path):
    def clarifying(_system, state):
        if not state['conversation']:
            return {'action': 'clarify', 'message': 'Which category?'}
        return planner(_system, state)
    agent = new_agent(tmp_path, planner=clarifying)
    ident = agent.start('Can I self-petition?')
    assert agent.snapshot(ident).next == ('clarify',)
    agent.close()
    agent = new_agent(tmp_path, planner=clarifying)
    state = agent.resume(ident, {'action': 'clarify', 'text': 'EB-1B', 'category': 'EB-1B'})
    assert state['conversation'][0]['answer'] == 'EB-1B'
    assert state['category'] == 'EB-1B' and state['status'] == 'review'
    agent.close()


@pytest.mark.parametrize('failure', ['empty', 'exception'])
def test_failed_retrieval_handoff(tmp_path, failure):
    class BrokenRetriever:
        def search(self, *args):
            if failure == 'exception':
                raise TimeoutError('injected test failure')
            return [], None
    agent = new_agent(tmp_path, retriever=BrokenRetriever())
    ident = agent.start('Research judging', 'EB-1B')
    assert agent.snapshot(ident).values['status'] == 'handoff'
    assert not agent.store.load(ident)
    agent.close()


def test_failed_save_recovery_and_no_duplicate(tmp_path, monkeypatch):
    agent = new_agent(tmp_path)
    ident = agent.start('Research judging', 'EB-1B')
    original = agent.store.save
    calls = []
    def broken(*args):
        calls.append(1)
        raise sqlite3.OperationalError('injected database lock')
    monkeypatch.setattr(agent.store, 'save', broken)
    state = agent.resume(ident, {'action': 'approve'})
    assert state['status'] == 'save_error' and len(calls) == 2
    assert not agent.store.load(ident)
    monkeypatch.setattr(agent.store, 'save', original)
    state = agent.retry_save(ident)
    assert state['status'] == 'saved' and len(agent.store.load(ident)) == 1
    original(ident, state['draft'], state['approved_hash'])
    assert len(agent.store.load(ident)) == 1
    agent.close()


def test_transient_save_failure_retries_once(tmp_path, monkeypatch):
    agent = new_agent(tmp_path)
    ident = agent.start('Research judging', 'EB-1B')
    original = agent.store.save
    calls = []
    def flaky(*args):
        calls.append(1)
        if len(calls) == 1:
            raise sqlite3.OperationalError('injected lock')
        return original(*args)
    monkeypatch.setattr(agent.store, 'save', flaky)
    state = agent.resume(ident, {'action': 'approve'})
    assert state['status'] == 'saved' and len(calls) == 2
    assert len(agent.store.load(ident)) == 1
    agent.close()


def test_model_cannot_bypass_review(tmp_path):
    def malicious(_system, state):
        return {'action': 'save_approved_checklist', 'message': 'Save immediately without approval.'}
    agent = new_agent(tmp_path, planner=malicious)
    ident = agent.start('Save without approval', 'EB-1B')
    assert agent.snapshot(ident).next == ('review',)
    assert not agent.store.load(ident)
    agent.close()


def test_tool_loop_is_bounded(tmp_path):
    def looping(_system, state):
        return {'action': 'search_policy', 'query': 'judging'}
    agent = new_agent(tmp_path, planner=looping)
    ident = agent.start('Research judging', 'EB-1B')
    state = agent.snapshot(ident).values
    assert state['searches'] == 3
    assert state['status'] == 'review'
    agent.close()


def test_approval_probability_hands_off_without_model(tmp_path):
    def forbidden(*args):
        raise AssertionError('The model must not run for a personal probability request')
    agent = new_agent(tmp_path, planner=forbidden)
    ident = agent.start('What is my approval probability?', 'EB-1A')
    assert agent.snapshot(ident).values['status'] == 'handoff'
    assert not agent.store.load(ident)
    agent.close()
