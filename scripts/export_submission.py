"""Build an explicit allowlist ZIP, never a recursive copy of the workspace."""
import json
from pathlib import Path
import re
import tomllib
import zipfile
from dotenv import dotenv_values
from eb1.config import ROOT

def public_files():
    files = [ROOT / name for name in ('app.py', 'README.md', 'requirements.txt', 'requirements.in', '.gitignore', '.gitattributes', '.env.example', 'start.ps1')]
    patterns = {'eb1': '*.py', 'scripts': '*.py', 'tests': '*.py', 'docs': '*.md',
                'corpus': '*', '.streamlit': '*.toml', 'evals': '*.json'}
    for folder, pattern in patterns.items():
        files.extend(p for p in (ROOT / folder).glob(pattern) if p.is_file())
    files.extend((ROOT / 'evals/results').glob('*.json'))
    files.extend((ROOT / 'evals/iteration1').glob('*.json'))
    files.extend((ROOT / 'evals/iteration2').glob('*.json'))
    files.extend((ROOT / 'evals/iteration3').glob('*.json'))
    files.extend((ROOT / 'corpus/index').glob('*'))
    files.extend((ROOT / '.github/workflows').glob('*.yml'))
    local_only = {'docs/DEMO_SCRIPT.md', '.streamlit/secrets.toml'}
    files = [path for path in files if path.relative_to(ROOT).as_posix() not in local_only]
    # Exact-key scan only, never print a key or a matching line.
    secrets = [v for k, v in dotenv_values(ROOT / '.env', encoding='utf-8-sig').items() if 'KEY' in k and v and len(v) >= 12]
    cloud_secrets = ROOT / 'runtime/deployment/streamlit.secrets.toml'
    if cloud_secrets.exists():
        secrets.append(tomllib.loads(cloud_secrets.read_text())['NEBIUS_API_KEY'])
    access_file = ROOT / 'runtime/deployment/VIEWER_ACCESS.txt'
    if access_file.exists():
        secrets.extend(re.findall(r'^Access code: (.+)$', access_file.read_text(), re.M))
    for path in files:
        path.resolve().relative_to(ROOT.resolve())
        relative = path.relative_to(ROOT).as_posix()
        if path.name == '.env' or path.name.endswith('.secrets.toml') or path.suffix in ('.pdf', '.docx', '.sqlite', '.db') or (path.suffix == '.npy' and relative != 'corpus/index/vectors.npy'):
            raise ValueError('A private/runtime file was selected for export')
        raw = path.read_bytes()
        if any(s.encode() in raw for s in secrets):
            raise ValueError('Secret scan failed; export stopped without displaying the secret')
    return sorted(set(files))


def main():
    files = public_files()
    output = ROOT / 'dist'
    output.mkdir(exist_ok=True)
    target = output / 'eb1-research-agent-week3-submission.zip'
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(set(files)):
            archive.write(path, path.relative_to(ROOT).as_posix())
    print(json.dumps({'zip': str(target), 'files': len(set(files)), 'bytes': target.stat().st_size,
                      'secret_scan': 'configured credentials passed', 'included': 'public policy index',
                      'excluded': ['.env', 'original PDFs', 'cloud job responses', 'runtime sessions', '.venv', 'demo scripts', 'Word reports', 'screenshots', 'cloud secrets', 'viewer access codes']}))

if __name__ == '__main__':
    main()
