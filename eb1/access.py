"""Password-free demo with a server-generated workspace per browser session."""
import re
import secrets
from .config import RUNTIME, hosted


def viewer_runtime(viewer):
    if viewer == 'local' and not hosted():
        return RUNTIME
    if not isinstance(viewer, str) or not re.fullmatch(r'[0-9a-f]{64}', viewer):
        raise PermissionError('Invalid workspace identity')
    return RUNTIME / 'visitors' / viewer


def require_viewer():
    import streamlit as st
    if not hosted():
        if st.get_option('server.address') not in ('127.0.0.1', 'localhost', '::1'):
            st.error('Local mode must bind to 127.0.0.1. Use start.ps1 or add --server.address 127.0.0.1.')
            st.stop()
        return 'local'
    # Never accept an identity from a URL, form, or shared username. A refresh
    # creates a new browser session, so previous hosted work is not recoverable.
    if '_visitor_id' not in st.session_state:
        st.session_state.clear()
        st.session_state['_visitor_id'] = secrets.token_hex(32)
    return st.session_state['_visitor_id']
