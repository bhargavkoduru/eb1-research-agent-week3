"""Run from the project root: python -m scripts.setup_index."""
import json
from eb1.retrieval import build_index

if __name__ == '__main__':
    try:
        print(json.dumps(build_index(), indent=2))
    except Exception as exc:
        print(f'Index setup failed ({type(exc).__name__}). Check credentials, connectivity and the prepared corpus.')
        raise SystemExit(1)
