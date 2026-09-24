# Week 3 build plan

Standalone EB-1 Research Agent - Week 3.

## Framework


One-liner: Help users turn a policy research question into a reviewed, cited research checklist in a Streamlit web app, replacing manual searching and note-taking, using four tools and handing off when sources are insufficient or before saving. Target normal completion within two minutes and successful handling of all five workflow scenarios. Measure the manual baseline rather than inventing it.

Four tools: `search_policy` (read), `load_research_session` (read), `draft_checklist` (prepare structured output), and `save_approved_checklist` (write after approval).

The model chooses whether to clarify the category/question, retrieve more policy evidence, prepare a draft, or hand off. Preserve conversation context, research question, sources, draft, review state, and saved record ID in SQLite-backed checkpoints. Human review supports approve, edit, and cancel; editing invalidates approval. Enforce approval in code, not just a prompt.

Use bounded tool loops and one retry for transient failures. Empty results lead to a truthful knowledge-gap response. A save failure must not be reported as success. Use idempotency to avoid duplicate saves after retries.

Five scenarios: successful reviewed save; missing information; unsupported question; restart during pending review followed by edit/cancel; injected tool/save error with recovery and no duplicate writes. Record end-to-end completion and timings.
