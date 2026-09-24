"""Restore the checked public index without provider calls at cloud startup."""
import hashlib
import json
import shutil
import threading
from .config import ROOT, INDEX
from .retrieval import fingerprint

_lock = threading.Lock()


def ensure_index():
    with _lock:
        manifest = INDEX / 'manifest.json'
        if manifest.exists():
            return
        bundled = ROOT / 'corpus/index'
        metadata = json.loads((bundled / 'manifest.json').read_text())
        if metadata['fingerprint'] != fingerprint():
            raise ValueError('The bundled index does not match the corpus or embedding model. Rebuild it before deployment.')
        hashes = json.loads((bundled / 'checksums.json').read_text())
        names = ('chunks.json', 'vectors.npy', 'manifest.json')
        for name in names:
            if hashlib.sha256((bundled / name).read_bytes()).hexdigest() != hashes[name]:
                raise ValueError('The bundled public index failed integrity checks.')
        INDEX.mkdir(parents=True, exist_ok=True)
        for name in names:  # Publish manifest last, after both data files are copied.
            temp = INDEX / (name + '.tmp')
            shutil.copyfile(bundled / name, temp)
            temp.replace(INDEX / name)
