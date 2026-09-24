"""Nebius-only clients. Do not log requests, headers or raw provider errors."""
import json
from contextlib import contextmanager
from contextvars import ContextVar
from functools import lru_cache
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from .config import BASE_URL, CHAT_MODEL, EMBED_MODEL, api_key
from .usage import reserve_provider_calls

_progress = ContextVar('provider_progress', default=None)
# Optional reranking must not hold up the complete answer. Interactive calls
# fail promptly; the agent's planning calls still retry transient failures once.
CHAT_PROFILES = {'standard': (25, 1, 2400), 'answer': (25, 0, 1200), 'rerank': (8, 0, 512)}


@contextmanager
def response_progress(callback):
    token = _progress.set(callback)
    try:
        yield
    finally:
        _progress.reset(token)


def report_progress(message):
    callback = _progress.get()
    if callback is not None:
        callback(message)


@lru_cache
def chat(purpose='standard'):
    timeout, retries, max_tokens = CHAT_PROFILES[purpose]
    return ChatOpenAI(model=CHAT_MODEL, base_url=BASE_URL, api_key=api_key(),
                      temperature=0, max_tokens=max_tokens, timeout=timeout, max_retries=retries)


@lru_cache
def embeddings(query=False):
    client = OpenAIEmbeddings(model=EMBED_MODEL, base_url=BASE_URL, api_key=api_key(),
                            check_embedding_ctx_length=False, chunk_size=16,
                            request_timeout=12 if query else 60, max_retries=0 if query else 1)
    return MeteredEmbeddings(client, attempts=1 if query else 2)


class MeteredEmbeddings:
    def __init__(self, client, attempts=2):
        self.client = client
        self.attempts = attempts

    def embed_query(self, text):
        report_progress('Finding relevant policy passages…')
        reserve_provider_calls(self.attempts)
        return self.client.embed_query(text)

    def embed_documents(self, texts):
        reserve_provider_calls(self.attempts * max(1, (len(texts) + 15) // 16))
        return self.client.embed_documents(texts)


def json_call(system, payload, purpose='standard'):
    report_progress('Checking passage relevance…' if purpose == 'rerank' else 'Preparing a cited answer…')
    reserve_provider_calls(CHAT_PROFILES[purpose][1] + 1)
    response = chat(purpose).bind(response_format={'type': 'json_object'}).invoke([
        ('system', system + '\nReturn only a JSON object.'),
        ('human', json.dumps(payload, ensure_ascii=False)),
    ])
    content = response.content
    if not isinstance(content, str):
        raise ValueError('Model returned an unexpected content type')
    result = json.loads(content)
    if not isinstance(result, dict):
        raise ValueError('Model did not return a JSON object')
    return result
