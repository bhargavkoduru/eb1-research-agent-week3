from pathlib import Path
import streamlit as st
from streamlit.testing.v1 import AppTest
import eb1.qa
import eb1.retrieval
import eb1.research
PASSAGE = {'id': 'eb1b-p019-c01', 'document_id': 'eb1b', 'source_pdf_page': 19, 'source_url': 'https://www.uscis.gov/policy-manual/volume-6-part-f-chapter-3', 'section': 'Judging', 'text': 'The beneficiary must actually participate in judging.'}
CLAIM = {'text': 'Document completed judging.', 'citations': [PASSAGE['id']], 'quotes': [{'id': PASSAGE['id'], 'text': PASSAGE['text']}]}

def button(app, label):
    return next((b for b in app.button if b.label == label))

def test_review_buttons_enforce_separate_edit_and_approval(tmp_path, monkeypatch):
    real_agent = eb1.research.ResearchAgent

    class LocalRetriever:

        def search(self, *args, **kwargs):
            return ([PASSAGE], None)

    def planner(system, payload):
        return {'action': 'search_policy' if not payload['evidence'] else 'draft_checklist', 'query': 'judging'}

    def answerer(*args):
        return {'status': 'answered', 'claims': [CLAIM]}

    def factory(retriever, **kwargs):
        return real_agent(retriever, tmp_path, planner=planner, answerer=answerer)
    monkeypatch.setattr(eb1.retrieval, 'Retriever', LocalRetriever)
    monkeypatch.setattr(eb1.research, 'ResearchAgent', factory)
    st.cache_resource.clear()
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py'), default_timeout=20).run()
    app.sidebar.selectbox[0].set_value('EB-1B')
    app.text_area[0].set_value('Research judging evidence')
    button(app, 'Start research').click().run()
    assert not app.exception
    note = next((t for t in app.text_area if t.label == 'Your note (not verified policy)'))
    note.set_value('Review this tomorrow')
    button(app, 'Approve displayed draft and save').click().run()
    assert any(('Apply your edits first' in w.value for w in app.warning))
    button(app, 'Apply edits and review again').click().run()
    assert not app.exception
    button(app, 'Approve displayed draft and save').click().run()
    assert not app.exception
    assert any(('Saved to your workspace' in s.value for s in app.success))
    st.cache_resource.clear()
