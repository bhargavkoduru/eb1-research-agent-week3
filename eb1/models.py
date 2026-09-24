"""Nebius-only clients. Do not log requests, headers or raw provider errors."""
import json
from functools import lru_cache
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from .config import BASE_URL, CHAT_MODEL, EMBED_MODEL, api_key
from .usage import reserve_provider_calls


@lru_cache
def chat():
    return ChatOpenAI(model=CHAT_MODEL, base_url=BASE_URL, api_key=api_key(),
                      temperature=0, max_tokens=2400, timeout=45, max_retries=1)


@lru_cache
def embeddings():
    client = OpenAIEmbeddings(model=EMBED_MODEL, base_url=BASE_URL, api_key=api_key(),
                            check_embedding_ctx_length=False, chunk_size=16,
                            request_timeout=60, max_retries=1)
    return MeteredEmbeddings(client)


class MeteredEmbeddings:
    def __init__(self, client):
        self.client = client

    def embed_query(self, text):
        reserve_provider_calls(2)  # Reserve the initial call and its one possible retry.
        return self.client.embed_query(text)

    def embed_documents(self, texts):
        reserve_provider_calls(2 * max(1, (len(texts) + 15) // 16))
        return self.client.embed_documents(texts)


def json_call(system, payload):
    reserve_provider_calls(2)
    response = chat().bind(response_format={'type': 'json_object'}).invoke([
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
