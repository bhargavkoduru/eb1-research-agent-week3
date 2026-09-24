import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / '.env', encoding='utf-8-sig', override=False)


def setting(name, default=None):
    if name in os.environ:
        return os.environ[name]
    # Community Cloud supplies secrets outside the Git repository.
    import streamlit as st
    try:
        return st.secrets.get(name, default)
    except FileNotFoundError:
        return default


def hosted():
    return str(setting('EB1_HOSTED', 'true')).lower() not in ('0', 'false', 'no')


CHAT_MODEL = setting('NEBIUS_CHAT_MODEL', 'openai/gpt-oss-120b')
EMBED_MODEL = setting('NEBIUS_EMBED_MODEL', 'Qwen/Qwen3-Embedding-8B')
BASE_URL = 'https://api.tokenfactory.nebius.com/v1'
CORPUS = ROOT / 'data' / 'corpus' / 'pages.json'
if not CORPUS.exists():
    CORPUS = ROOT / 'corpus' / 'pages.json'
INDEX = ROOT / 'data' / 'index'
RUNTIME = ROOT / 'runtime'


def api_key():
    key = setting('NEBIUS_API_KEY', '')
    if not key:
        raise ValueError('Add NEBIUS_API_KEY to the local .env file.')
    return key
