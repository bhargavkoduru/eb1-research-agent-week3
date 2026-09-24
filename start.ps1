$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
if (-not (Test-Path -LiteralPath '.venv\Scripts\python.exe')) {
    throw 'Project environment is missing. Follow the setup commands in README.md.'
}
$env:EB1_HOSTED = 'false'
& '.\.venv\Scripts\python.exe' -m streamlit run app.py --server.address 127.0.0.1
