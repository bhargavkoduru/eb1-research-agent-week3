"""Stage only the same inspected files used by the submission ZIP."""
import subprocess
from eb1.config import ROOT
from scripts.export_submission import public_files


if __name__ == '__main__':
    paths = [p.relative_to(ROOT).as_posix() for p in public_files()]
    subprocess.run(['git', 'add', '--', *paths], cwd=ROOT, check=True, capture_output=True)
    staged = subprocess.run(['git', 'diff', '--cached', '--name-only', '-z'], cwd=ROOT, check=True, capture_output=True).stdout.decode().split('\0')
    unexpected = set(filter(None, staged)) - set(paths)
    if unexpected:
        raise ValueError('Git index contains files outside the inspected allowlist; commit stopped.')
    print(f'Staged {len(list(filter(None, staged)))} inspected files. Credentials and demo scripts excluded.')
