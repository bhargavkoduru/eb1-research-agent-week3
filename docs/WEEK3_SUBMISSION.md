# Week 3 — Reviewed policy research checklist agent

## One-liner

My agent helps applicants turn an EB-1 policy question into a cited, reviewed checklist in a local Streamlit app, replacing manual chapter searching and note-taking through four tools, handing off when information is missing or unsupported and before final save, with a target of completing the workflow within two minutes and passing all five defined workflow scenarios.

The manual workflow cost and actual human review time have not been measured; the two-minute goal is a target, not a demonstrated end-to-end human completion time.

## Agent framework

| Field | Implementation |
| --- | --- |
| Goal | Research a policy question and prepare a checklist that the user can inspect, edit and approve. |
| Surface | Standalone Streamlit research app running locally on the user's computer. |
| Steps | Choose whether to clarify, load, search again, draft or hand off; pause for review; save after approval. |
| Tools | `search_policy` and `load_research_session` read; `draft_checklist` prepares a draft; `save_approved_checklist` writes a final approved record. |
| Memory | Goal, category, history, evidence, trace, draft and review state use SQLite checkpoints. Local SQLite state recovers across app restarts. |
| Limits | No personal eligibility decision, approval probability, invented candidate facts, LinkedIn scraping, email sending or automatic final save. |
| Human review | Approve displayed draft, edit suggested tasks/notes and review again, or cancel. Editing clears approval. |
| Recovery | One client retry for transient API failures; bounded planning/search; empty evidence hands off. Save retries once, retains failed state, and supports an idempotent retry. |
| Success | Five scenario categories tested. The original Qwen run took 12.87 scripted seconds; the current-model judging task reached review in 18.35 seconds and passed edit/save/recovery checks. Real human review time is excluded. |

## Why this is an agent

The model chooses the next action using the current goal and tool observations, including additional searches or clarification. LangGraph routes those decisions, stores state and interrupts for human review. Tool inputs and writes are enforced in code. This extends the Week 2 retrieval system rather than simply renaming a Q&A chain.

## Dataset, prompts and implementation

The agent reuses two English USCIS Policy Manual chapters on EB-1A and EB-1B: 23 source pages, 65 page-aware chunks, and the precomputed local vector index. LlamaParse OCR produced the cached Markdown after direct PDF extraction proved garbled; chapter, page and source-hash provenance are retained. The planner uses `openai/gpt-oss-120b` on Nebius. The exact planner prompt and four LangChain tool definitions are in `eb1/research.py`; shared answer/evidence instructions are in `eb1/qa.py`. The architecture and data locations are documented in `docs/ARCHITECTURE.md`.

Codex generated and revised original code from the user's requested scope. Testing specifically targeted restart behavior, edit-before-approval, cancellation, tool failures and duplicate-save prevention. Initial live testing exposed a generic checklist that did not address judging; a stronger model and an explicit focus check corrected that failure.

Selected user prompts given to Codex, reproduced verbatim:

- "Let's consider a simple project that can check all boxes laid out in the week2 and 3 files but can be wrapped up sooner, using any public repositories"
- "I need to submit separate github repositories for week 2 and 3"

The final submission uses local Streamlit execution and retains the agent's review-before-save boundary.

## Evaluation and learnings

The standalone suite passed 30 tests, including Streamlit form interactions, local UI behavior and optional access-control checks, workspace isolation and usage limits. Live checks covered a judged-evidence checklist with simulated review, ambiguity/cancellation and unsupported requests. Error/retry scenarios use controlled injected failures. See `docs/WEEK3_EVALUATION.md` and `evals/week3_live.json`.

Approval belongs in code, not only in the prompt. A durable checkpoint is necessary to resume an unfinished review. A successful save is not sufficient evidence of a useful checklist: topic focus and claim support must also be checked. No measured human time saving is claimed until the manual baseline is recorded.

## Repository

https://github.com/bhargavkoduru/eb1-research-agent-week3

## Response time follow-up

The current model, request timeouts and separate follow-up checks are documented in `docs/PERFORMANCE.md`. Earlier Qwen evaluation results remain preserved and are not presented as measurements of the replacement model.
