"""Prepare owner-only API settings for the public, password-free demo."""
import json
import tomllib
from eb1.config import ROOT, api_key


def main():
    target = ROOT / 'runtime/deployment'
    target.mkdir(parents=True, exist_ok=True)
    config_path = target / 'streamlit.secrets.toml'
    existing = tomllib.loads(config_path.read_text(encoding='utf-8')) if config_path.exists() else {}
    config = {
        'EB1_HOSTED': True,
        'EB1_ENABLE_LIVE_CALLS': existing.get('EB1_ENABLE_LIVE_CALLS', True),
        'NEBIUS_API_KEY': existing.get('NEBIUS_API_KEY') or api_key(),
        'EB1_VIEWER_DAILY_ACTIONS': existing.get('EB1_VIEWER_DAILY_ACTIONS', 30),
        'EB1_GLOBAL_DAILY_ACTIONS': existing.get('EB1_GLOBAL_DAILY_ACTIONS', 100),
        'EB1_VIEWER_DAILY_ATTEMPTS': existing.get('EB1_VIEWER_DAILY_ATTEMPTS', 120),
        'EB1_GLOBAL_DAILY_ATTEMPTS': existing.get('EB1_GLOBAL_DAILY_ATTEMPTS', 400),
    }
    # Replace obsolete viewer hashes while preserving the key and owner limits.
    lines = ['# Owner only: paste into Streamlit Advanced settings > Secrets. Never upload to GitHub.']
    lines += [name + ' = ' + json.dumps(value) for name, value in config.items()]
    config_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    (target / 'VIEWER_ACCESS.txt').write_text(
        'No examiner username or password is needed.\n'
        'The public app creates a separate workspace for each browser session.\n'
        'Share the deployed app URL in the Week 3 submission.\n'
        'API settings in streamlit.secrets.toml are for the owner only.\n'
        'See docs/CLOUD_DEPLOYMENT.md for the remaining hosting steps.\n', encoding='utf-8')
    print(json.dumps({'secrets_file': str(config_path), 'examiner_login_required': False, 'credentials_printed': False}))


if __name__ == '__main__':
    main()
