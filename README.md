# EB-1 Research Agent - Week 3

This is the standalone **Week 3 submission**. The app opens directly to the research/checklist agent; there is no week selector or examiner login. The separate [Week 2 project](https://github.com/bhargavkoduru/eb1-policy-qa-week2) has its own repository.

Enter a research goal, inspect the source evidence, edit or cancel if needed, then approve and download the checklist.

Example: **Research EB-1B judging evidence and prepare a short checklist of documentation to verify.**

## Submission links

- Code: https://github.com/bhargavkoduru/eb1-research-agent-week3
- [Google Doc draft](docs/WEEK3_SUBMISSION.md)
- [Evaluation and retained limitations](docs/WEEK3_EVALUATION.md)
- [Requirement mapping and remaining actions](docs/SUBMISSION_CHECKLIST.md)
- [Architecture](docs/ARCHITECTURE.md) and [source preparation](docs/SOURCE_AUDIT.md)
- Hosted URL: **not deployed yet**. Follow [deployment instructions](docs/CLOUD_DEPLOYMENT.md).

The handouts require a Google Doc, a live demo video of at most five minutes, and GitHub assets for this week. Add the actual Doc/video links after creating them. A hosted app URL is an extra convenience. API keys and demo scripts are excluded from Git and the submission ZIP.

## Run a fresh copy

Use Python 3.12. From this repository's folder, in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item -LiteralPath .env.example -Destination .env
```

Only copy `.env.example` in a fresh checkout without an existing `.env`. Add your own `NEBIUS_API_KEY` to `.env`, then run:

```powershell
$env:EB1_HOSTED = 'false'
.\.venv\Scripts\python.exe -m streamlit run app.py --server.address 127.0.0.1
```

Open http://127.0.0.1:8501. The bundled public index restores automatically without parsing or embedding charges. A new LlamaParse job is not needed. On macOS/Linux, activate `.venv/bin/activate` and run `EB1_HOSTED=false streamlit run app.py --server.address 127.0.0.1`.

## Data and evaluation

The corpus contains 23 source pages from USCIS Policy Manual Volume 6, Part F, Chapters 2 and 3 (EB-1A/EB-1B), printed September 23, 2026. LlamaParse OCR was cached; LangChain chunks feed local NumPy vectors plus BM25, reciprocal-rank fusion and model reranking. Nebius supplies embeddings and generation. Policy research only; the app does not decide eligibility.

Five workflow scenarios were covered by live and deterministic checks: reviewed save, clarification, unsupported requests, restart/edit/cancel, and tool/save failure recovery. The final live run took 12.87 scripted seconds, excluding real human review. The manual baseline is not measured.

```powershell
$env:EB1_HOSTED = 'false'
.\.venv\Scripts\python.exe -m pytest -q tests
.\.venv\Scripts\python.exe -m scripts.smoke_week3
.\.venv\Scripts\python.exe -m scripts.export_submission
```

The standalone suite passed **27 tests** locally. Tests use substitutes for provider calls. The evaluation command makes paid Nebius requests; existing measurements are included. The ZIP is `dist/eb1-research-agent-week3-submission.zip`. [GitHub Actions](https://github.com/bhargavkoduru/eb1-research-agent-week3/actions/workflows/tests.yml) runs the standalone test suite.

## Hosting and privacy

The owner configures the Nebius key in server secrets; examiners enter no key or password. Questions and policy excerpts go to Nebius. Public retrieval data is shared; browser workspaces are separate. Download approved checklists before refreshing or closing the hosted app. Local SQLite checkpoints persist across local app restarts; hosted anonymous access lasts only for the current browser session.

Only public policy material is included. Original PDFs, candidate records, `.env`, cloud secrets, runtime databases and demo scripts stay outside Git. See [build provenance](docs/BUILD_ORIGIN.md) for the original shared implementation.
