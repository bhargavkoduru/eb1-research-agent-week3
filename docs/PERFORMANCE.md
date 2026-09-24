# Response time and reliability update

The default chat model is now `openai/gpt-oss-120b`, served through the same Nebius API and key. The embedding model, prepared corpus and index are unchanged. Existing `.env` files can override the default; set `NEBIUS_CHAT_MODEL=openai/gpt-oss-120b` to use this configuration.

On September 24, a live request using `Qwen/Qwen3-235B-A22B-Instruct-2507` took 132.14 seconds and failed: query embedding took 1.61 seconds, reranking 39.77 seconds, and answer generation exhausted two 45-second attempts. A tiny request to that model also timed out. These observations identify the affected request path, not a claim of a platform-wide outage.

## Current handling

- Query embedding uses a 12-second timeout without an automatic retry; batch ingestion retains its longer timeout.
- Optional reranking uses an 8-second timeout and no retry. Failure falls back to the existing dense/BM25 rank fusion.
- Answer generation uses a 25-second timeout and no retry. If the provider fails, Q&A reports the service as unavailable and retains retrieved passages for inspection, without inventing an answer.
- Agent planning uses a 25-second timeout with one transient retry. Human approval and durable saves remain enforced.
- The Q&A screen shows the active stage and elapsed waiting time. New submissions clear stale answers.
- Agent searches include the original goal alongside the model's chosen query, and checklist instructions explicitly request concrete tasks for that goal.

These are per-request timeouts, not a guaranteed total wall-clock deadline; network setup and multiple agent steps add time.

## Follow-up checks

The existing 15-question development set passed all 15 expected answer/clarify/refuse checks with the new model. Gold recall@4 was 1.0 for all nine answerable questions. The slowest response and nearest-rank p95 were 12.78 seconds, including the three immediate clarifications. This is a small sample and not a speed guarantee.

The exact judging question completed in the local browser in 11.31 seconds. A separate focused judging checklist reached review in 18.35 seconds, then passed scripted edit, approval, save and recovery after reopening the agent. This excludes real human review time.

Raw follow-up evidence is in `evals/performance_followup.json`. The original Qwen evaluation files are retained. Their 25/26 supported-claim audit and earlier latency numbers apply to that original run, not to the replacement model. The new behavior checks do not establish semantic claim accuracy or independent legal validation.
