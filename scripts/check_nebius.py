import json
from eb1.models import embeddings, json_call
from eb1.config import CHAT_MODEL, EMBED_MODEL

if __name__ == '__main__':
    try:
        response = json_call('Return {"ok":true} as JSON.', {'test': 'connection only'})
        vector = embeddings().embed_query('USCIS public policy research test')
        print(json.dumps({'chat_model': CHAT_MODEL, 'chat_ok': response.get('ok') is True,
                          'embedding_model': EMBED_MODEL, 'dimensions': len(vector)}))
    except Exception as exc:
        print(json.dumps({'error_type': type(exc).__name__, 'message': 'Connection test failed; no credentials printed.'}))
        raise SystemExit(1)
