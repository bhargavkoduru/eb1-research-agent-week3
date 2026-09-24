import pytest


@pytest.fixture(autouse=True)
def local_tests(monkeypatch):
    # Tests opt into hosted mode explicitly; provider calls use substitutes.
    monkeypatch.setenv('EB1_HOSTED', 'false')
    import streamlit as st
    original = st.get_option
    monkeypatch.setattr(st, 'get_option', lambda key: '127.0.0.1' if key == 'server.address' else original(key))
