from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import secrets
import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest
from eb1 import access, bootstrap, usage
from eb1.research import ResearchAgent
from eb1.usage import UsageLedger, UsageLimitError
APP = str(Path(__file__).resolve().parents[1] / 'app.py')

def test_local_mode_rejects_public_bind(monkeypatch):
    monkeypatch.setattr(st, 'get_option', lambda name: '0.0.0.0')
    app = AppTest.from_file(APP, default_timeout=20).run()
    assert not app.exception
    assert any(('Local mode must bind' in e.value for e in app.error))
    assert not any((b.label == 'Start research' for b in app.button))

def test_workspace_separation_and_path_rejection(tmp_path, monkeypatch):
    monkeypatch.setenv('EB1_HOSTED', 'true')
    monkeypatch.setattr(access, 'RUNTIME', tmp_path)
    alice = access.viewer_runtime(secrets.token_hex(32))
    bob = access.viewer_runtime(secrets.token_hex(32))
    assert alice != bob and alice.is_relative_to(tmp_path)
    with pytest.raises((ValueError, PermissionError)):
        access.viewer_runtime('../../alice')
    with pytest.raises(PermissionError):
        access.viewer_runtime('local')
    planner = lambda *args: {'action': 'handoff', 'message': 'test only'}
    a = ResearchAgent(None, alice, planner=planner)
    b = ResearchAgent(None, bob, planner=planner)
    ident = a.start('Private research question', 'EB-1A')
    assert a.store.sessions()[0]['id'] == ident
    assert b.store.sessions() == []
    assert not b.snapshot(ident).values
    assert b.store.load(ident) == []
    a.close()
    b.close()

def test_atomic_usage_and_global_limit(tmp_path):
    meter = UsageLedger(tmp_path / 'usage.sqlite')

    def attempt(i):
        try:
            meter.reserve('viewer' + str(i % 2), 'attempts', 1, 100, 5)
            return 1
        except UsageLimitError:
            return 0
    with ThreadPoolExecutor(max_workers=8) as pool:
        assert sum(pool.map(attempt, range(16))) == 5
    restarted = UsageLedger(tmp_path / 'usage.sqlite')
    with pytest.raises(UsageLimitError):
        restarted.reserve('new-viewer', 'attempts', 1, 100, 5)

def test_viewer_limit_preserves_other_sessions_allowance(tmp_path):
    meter = UsageLedger(tmp_path / 'usage.sqlite')
    meter.reserve('alice', 'attempts', 2, 2, 20)
    with pytest.raises(UsageLimitError):
        meter.reserve('alice', 'attempts', 1, 2, 20)
    meter.reserve('bob', 'attempts', 1, 2, 20)

def test_provider_denied_without_actor_and_kill_switch(tmp_path, monkeypatch):
    monkeypatch.setenv('EB1_HOSTED', 'true')
    monkeypatch.setattr(usage, 'RUNTIME', tmp_path)
    with pytest.raises(UsageLimitError):
        usage.reserve_provider_calls()
    with usage.live_operation('alice'):
        usage.reserve_provider_calls()
    monkeypatch.setenv('EB1_ENABLE_LIVE_CALLS', 'false')
    with pytest.raises(UsageLimitError):
        with usage.live_operation('alice'):
            pytest.fail('Paused demo must not execute a call')

def test_graph_threads_keep_session_actor(tmp_path, monkeypatch):
    monkeypatch.setenv('EB1_HOSTED', 'true')
    monkeypatch.setattr(usage, 'RUNTIME', tmp_path / 'meter')
    seen = []

    def planner(*args):
        seen.append(usage._actor.get())
        usage.reserve_provider_calls()
        return {'action': 'handoff', 'message': 'Done'}
    agent = ResearchAgent(None, tmp_path / 'agent', planner=planner)
    with usage.live_operation('alice'):
        ident = agent.start('A public question', 'EB-1A')
    assert seen == ['alice']
    assert agent.snapshot(ident).values['message'] == 'Done'
    agent.close()

def test_cloud_bootstrap_without_api_calls(tmp_path, monkeypatch):
    monkeypatch.setattr(bootstrap, 'INDEX', tmp_path / 'index')
    bootstrap.ensure_index()
    assert (tmp_path / 'index/vectors.npy').exists()
    manifest = json.loads((tmp_path / 'index/manifest.json').read_text())
    assert manifest['chunks'] == 65
    bootstrap.ensure_index()

def test_browser_sessions_cannot_reuse_another_workspace(tmp_path, monkeypatch):
    monkeypatch.setenv('EB1_HOSTED', 'true')
    monkeypatch.setattr(access, 'RUNTIME', tmp_path)
    st.cache_resource.clear()
    alice = AppTest.from_file(APP, default_timeout=20).run()
    a = alice.session_state['_research_service'][1]
    a.planner = lambda *args: {'action': 'handoff', 'message': 'Test only'}
    ident = a.start('Question belonging only to the first visitor', 'EB-1A')
    alice.run()
    assert alice.session_state['research_id'] == ident
    bob = AppTest.from_file(APP, default_timeout=20)
    bob.query_params['_visitor_id'] = alice.session_state['_visitor_id']
    bob.query_params['research_id'] = ident
    bob.run()
    assert not alice.exception and (not bob.exception)
    assert alice.session_state['_visitor_id'] != bob.session_state['_visitor_id']
    b = bob.session_state['_research_service'][1]
    assert b is not a and b.store.sessions() == []
    assert not b.snapshot(ident).values
    assert not any((s.label == 'Resume a research session' for s in bob.selectbox))
    alice.run()
    assert alice.session_state['research_id'] == ident
    a.close()
    b.close()
    st.cache_resource.clear()

def test_public_app_opens_without_examiner_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv('EB1_HOSTED', 'true')
    monkeypatch.setenv('NEBIUS_API_KEY', '')
    monkeypatch.setattr(access, 'RUNTIME', tmp_path)
    st.cache_resource.clear()
    app = AppTest.from_file(APP, default_timeout=20).run()
    assert not app.exception and not app.error
    assert any(b.label == 'Start research' for b in app.button)
    assert not any(b.label == 'Sign in' for b in app.button)
    assert not app.sidebar.radio
    visitor = app.session_state['_visitor_id']
    app.run()
    assert app.session_state['_visitor_id'] == visitor
    app.session_state['_research_service'][1].close()
