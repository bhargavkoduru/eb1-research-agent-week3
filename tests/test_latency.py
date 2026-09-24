import httpx
import numpy as np
import pytest
from openai import APITimeoutError
from langchain_openai import ChatOpenAI
from eb1 import models, qa, retrieval


def test_reranking_timeout_does_not_retry(monkeypatch):
    requests = []

    def transport(request):
        requests.append(request)
        raise httpx.ReadTimeout('Injected provider delay', request=request)

    client = httpx.Client(transport=httpx.MockTransport(transport))
    monkeypatch.setattr(models, 'api_key', lambda: 'test-key')
    monkeypatch.setattr(models, 'ChatOpenAI', lambda **kwargs: ChatOpenAI(**kwargs, http_client=client))
    models.chat.cache_clear()
    try:
        with pytest.raises(APITimeoutError):
            models.json_call('Rank the passages', {'passages': []}, purpose='rerank')
        assert len(requests) == 1
        assert requests[0].extensions['timeout']['read'] <= 8
    finally:
        models.chat.cache_clear()
        client.close()


def test_slow_reranking_uses_fusion_and_answer_timeout_keeps_sources(monkeypatch):
    retriever = retrieval.Retriever.__new__(retrieval.Retriever)
    retriever.chunks = [{'id': f'passage-{i}', 'document_id': 'eb1a', 'section': 'Judging',
                         'text': f'Actual participation in judging is described in passage {i}.'} for i in range(5)]
    retriever.vectors = np.array([[1.0, 0.0]] * 5)

    class Sparse:
        def get_scores(self, _tokens):
            return [5, 4, 3, 2, 1]

    class Embeddings:
        def embed_query(self, _text):
            return [1.0, 0.0]

    def slow_rerank(*args, **kwargs):
        assert kwargs['purpose'] == 'rerank'
        raise APITimeoutError(request=httpx.Request('POST', 'https://example.test'))

    def slow_answer(*args, **kwargs):
        raise APITimeoutError(request=httpx.Request('POST', 'https://example.test'))

    retriever.bm25 = Sparse()
    monkeypatch.setattr(retrieval, 'embeddings', lambda **kwargs: Embeddings())
    monkeypatch.setattr(retrieval, 'json_call', slow_rerank)
    monkeypatch.setattr(qa, 'json_call', slow_answer)
    result = qa.ask(retriever, 'What judging evidence is needed?', 'EB-1A')
    assert result['status'] == 'unavailable'
    assert result['claims'] == []
    assert len(result['passages']) == 4
    assert 'hybrid rank fusion' in result['retrieval_warning']
    assert 'retrieved policy passages' in qa.answer_markdown(result)
