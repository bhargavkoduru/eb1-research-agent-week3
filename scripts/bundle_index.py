"""Package only the public corpus index; no candidates or user sessions."""
import hashlib
import json
import shutil
from eb1.config import ROOT, INDEX
from eb1.retrieval import fingerprint


def main():
    manifest = json.loads((INDEX / 'manifest.json').read_text())
    if manifest['fingerprint'] != fingerprint():
        raise ValueError('Rebuild the index before bundling it.')
    if (ROOT / 'corpus/pages.json').read_bytes() != (ROOT / 'data/corpus/pages.json').read_bytes():
        raise ValueError('The public corpus copy does not match the prepared corpus.')
    chunks = json.loads((INDEX / 'chunks.json').read_text(encoding='utf-8'))
    if any(c['document_id'] not in ('eb1a', 'eb1b') or c['source_sha256'] != 'cb8814dfed0d855edeac8f6bf160d9d686f2dddaf67fbecf73285e561db1143d' for c in chunks):
        raise ValueError('Only the reviewed public USCIS corpus can be bundled.')
    target = ROOT / 'corpus/index'
    target.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name in ('chunks.json', 'vectors.npy', 'manifest.json'):
        shutil.copyfile(INDEX / name, target / name)
        hashes[name] = hashlib.sha256((target / name).read_bytes()).hexdigest()
    (target / 'checksums.json').write_text(json.dumps(hashes, indent=2), encoding='utf-8')
    print(json.dumps({'public_chunks': len(chunks), 'dimensions': manifest['dimensions'], 'model_calls': 0}))


if __name__ == '__main__':
    main()
