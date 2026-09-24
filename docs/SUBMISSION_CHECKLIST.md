# Week 3 requirements alignment

This custom use case follows the supplied Week 3 handout. This repository covers Week 3; [Week 2](https://github.com/bhargavkoduru/eb1-policy-qa-week2) is separate.

| Week 3 item | Evidence/status |
| --- | --- |
| Multi-step task, tool choices and state | Single model-driven LangGraph agent with four LangChain tools and SQLite checkpoints. |
| Read/write boundary and human intervention | Final save gated on exact-draft approval; edit, re-review and cancellation implemented. |
| Memory across restart | Local mode recovers goal, history, sources, draft, trace and approval state from checkpoints across restarts. |
| Failure handling | Bounded calls, API retries, source-empty handoff, failed-save retention and idempotent retry. |
| End-to-end validation | Five scenario categories covered by live and deterministic checks; 27 standalone tests passed, including UI and workspace checks; see GitHub Actions. |
| Documentation and prompts | `WEEK3_SUBMISSION.md`, `WEEK3_EVALUATION.md`, `ARCHITECTURE.md` and `eb1/research.py`. |
| Manual baseline comparison | Not measured; no quantitative human time saving is claimed. |
| GitHub assets | This repository and ZIP contain the Week 3 agent. |

The supplied handout permits a custom use case. The checks above concern this project's chosen scope, not specialized requirements of unrelated sample projects. Measured results describe a small development evaluation; they do not establish performance on unseen questions.

The nine-field agent framework is included in `WEEK3_SUBMISSION.md`, although the handout labels the expanded framework optional. All five scenario categories passed; real human review time and manual workflow cost remain unmeasured.
