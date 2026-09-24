import json
import streamlit as st
from eb1.config import ROOT, INDEX, CORPUS, CHAT_MODEL, hosted
from eb1.access import require_viewer, viewer_runtime
from eb1.bootstrap import ensure_index
from eb1.usage import UsageLimitError, live_operation
from eb1.retrieval import Retriever
from eb1.research import ResearchAgent, checklist_markdown
st.set_page_config(page_title='EB-1 Research Agent - Week 3', page_icon='📚', layout='wide')

@st.cache_resource
def services(index_version, corpus_version):
    return Retriever()

def research_service(viewer, index_version, corpus_version):
    version = (viewer, index_version, corpus_version)
    previous = st.session_state.get('_research_service')
    if previous is None or previous[0] != version:
        if previous is not None:
            previous[1].close()
        agent = ResearchAgent(services(index_version, corpus_version), runtime=viewer_runtime(viewer))
        st.session_state['_research_service'] = (version, agent)
    return st.session_state['_research_service'][1]

def sources_panel(passages):
    for p in passages:
        with st.expander(f"{p['document_id'].upper()} · PDF page {p['source_pdf_page']} · {p['section'][:100]}"):
            st.caption(f"Passage {p['id']} · printed manual page {p.get('printed_manual_page', 'unknown')}")
            st.markdown(p['text'])
            st.link_button('Open USCIS chapter', p['source_url'])

def safe_error(exc):
    if isinstance(exc, UsageLimitError):
        st.warning(str(exc))
        return
    st.error(f'The request could not finish ({type(exc).__name__}). Check your internet connection and Nebius access, then retry. Credentials are not shown.')
st.title('EB-1 Research Agent - Week 3')
st.write('Research EB-1A and EB-1B policy, review the proposed checklist, then approve and save.')
st.caption('USCIS Policy Manual · Volume 6, Part F, Chapters 2–3 · Snapshot: September 23, 2026')
st.info('Policy research only. This app does not decide eligibility. Check cited passages and current USCIS guidance before relying on an answer.')
viewer = require_viewer()
with st.sidebar:
    st.header('Your workspace')
    category = st.selectbox('Policy category', ['Both', 'EB-1A', 'EB-1B'])
    st.caption('Week 3 submission')
    if hosted():
        st.caption('No sign-in needed. This browser session has its own workspace. Questions and policy excerpts go to Nebius.')
        st.caption('Refreshing or closing this page starts a new workspace. Download approved checklists before leaving.')
    else:
        st.caption('Runs on this computer. Questions and retrieved policy excerpts go to Nebius. Saved sessions stay in local SQLite files.')
    st.caption('Use public policy questions here. Candidate uploads are not part of this version.')
    with st.expander('Project details'):
        st.write('LangChain · LangGraph · Nebius · LlamaParse')
        st.caption(f'Model: {CHAT_MODEL}')
        st.write('Local vectors + BM25 + reranking. LlamaParse results are cached.')
        st.markdown('See `docs/PROJECT_PLAN.md` and the evaluation reports in the project folder.')
manifest_path = INDEX / 'manifest.json'
try:
    ensure_index()
    index_version, corpus_version = (manifest_path.stat().st_mtime_ns, CORPUS.stat().st_mtime_ns)
    retriever = services(index_version, corpus_version)
except Exception as exc:
    safe_error(exc)
    st.stop()
try:
    agent = research_service(viewer, index_version, corpus_version)
except Exception as exc:
    safe_error(exc)
    st.stop()
st.subheader('Research a question, then review the checklist')
with st.form('new_research'):
    goal = st.text_area('Research goal', placeholder='Research EB-1B judging evidence and prepare a checklist of points to verify.', max_chars=3000)
    start = st.form_submit_button('Start research', type='primary')
if start:
    try:
        with st.spinner('The agent is choosing its next steps and researching…'):
            with live_operation(viewer):
                st.session_state['research_id'] = agent.start(goal, category)
        st.rerun()
    except Exception as exc:
        safe_error(exc)
sessions = agent.store.sessions()
if sessions:
    choices = {s['id']: s['goal'][:85] + ' · ' + s['id'][:6] for s in sessions}
    default_id = st.session_state.get('research_id', sessions[0]['id'])
    ids = list(choices)
    selected = st.selectbox('Resume a research session', ids, index=ids.index(default_id) if default_id in ids else 0, format_func=choices.get)
    st.session_state['research_id'] = selected
    snapshot = agent.snapshot(selected)
    state = snapshot.values
    st.caption(f"Session {selected[:8]} · {state.get('status', 'initializing')} · {state.get('category', '')}")
    if state.get('message'):
        st.write(state['message'])
    if snapshot.next and 'clarify' in snapshot.next:
        with st.form('clarification_' + selected):
            clarification = st.text_input('Your clarification')
            clarification_category = st.selectbox('Category for this research', ['Both', 'EB-1A', 'EB-1B'])
            continue_research = st.form_submit_button('Continue research')
            cancel_research = st.form_submit_button('Cancel research')
        if continue_research or cancel_research:
            try:
                with st.spinner('Continuing research…'):
                    if cancel_research:
                        agent.resume(selected, {'action': 'cancel'})
                    else:
                        with live_operation(viewer):
                            agent.resume(selected, {'action': 'clarify', 'text': clarification, 'category': clarification_category})
                st.rerun()
            except Exception as exc:
                safe_error(exc)
    draft = state.get('draft')
    if draft:
        st.caption('Tasks are suggested research actions. The cited policy statements explain the source requirements.')
        st.markdown(checklist_markdown(draft))
    if draft and snapshot.next and ('review' in snapshot.next):
        with st.form('review_' + selected + '_' + str(len(snapshot.metadata or {}))):
            st.caption('You can edit task wording and add notes. Cited policy statements remain tied to their evidence.')
            tasks = [st.text_input(f'Task {i + 1}', item['task'], key=f"{selected}_task_{i}_{state.get('approved_hash', '')}") for i, item in enumerate(draft['items'])]
            note = st.text_area('Your note (not verified policy)', value=draft.get('user_note', ''), max_chars=3000)
            edit = st.form_submit_button('Apply edits and review again')
            approve = st.form_submit_button('Approve displayed draft and save', type='primary')
            cancel = st.form_submit_button('Cancel checklist')
        if edit or approve or cancel:
            if approve and (note != draft.get('user_note', '') or tasks != [i['task'] for i in draft['items']]):
                st.warning('Apply your edits first, then approve the updated displayed draft.')
            else:
                try:
                    agent.resume(selected, {'action': 'edit' if edit else 'approve' if approve else 'cancel', 'tasks': tasks, 'user_note': note})
                    st.rerun()
                except Exception as exc:
                    safe_error(exc)
    if state.get('status') == 'saved':
        st.success('Saved to your workspace: ' + state['saved_id'])
        st.download_button('Download approved checklist', checklist_markdown(draft), file_name='eb1-research-checklist.md', mime='text/markdown')
    if state.get('status') == 'save_error' and st.button('Retry save'):
        try:
            agent.retry_save(selected)
            st.rerun()
        except Exception as exc:
            safe_error(exc)
    with st.expander('Research steps'):
        st.json(state.get('trace', []))
    if state.get('evidence'):
        with st.expander('Policy evidence collected'):
            sources_panel(state['evidence'])
