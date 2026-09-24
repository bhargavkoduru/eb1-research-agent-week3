# Week 3 submission checklist

This custom use case follows the supplied Week 3 handout. Submit this repository for Week 3; [Week 2](https://github.com/bhargavkoduru/eb1-policy-qa-week2) is separate.

| Week 3 item | Evidence/status |
| --- | --- |
| Multi-step task, tool choices and state | Single model-driven LangGraph agent with four LangChain tools and SQLite checkpoints. |
| Read/write boundary and human intervention | Final save gated on exact-draft approval; edit, re-review and cancellation implemented. |
| Memory across restart | Local mode recovers goal, history, sources, draft, trace and approval state from checkpoints across restarts. Hosted visitors resume during their current browser session; refresh starts a new workspace. |
| Failure handling | Bounded calls, API retries, source-empty handoff, failed-save retention and idempotent retry. |
| End-to-end validation | Five scenario categories covered by live and deterministic checks; 27 standalone tests passed, including hosted access/isolation; see GitHub Actions. |
| Documentation and prompts | `WEEK3_SUBMISSION.md`, `WEEK3_EVALUATION.md`, `ARCHITECTURE.md` and `eb1/research.py`. |
| Manual baseline comparison | Not measured. Time one manual policy search and checklist preparation before claiming a time-saving percentage. |
| GitHub assets and live video up to five minutes | This repository and ZIP contain the Week 3 agent. Separate Week 3 video recording remains. |

## Finish this week's submission

1. Review `WEEK3_SUBMISSION.md` and `WEEK3_EVALUATION.md`, then copy them into your Google Doc. Add your name and final links.
2. Use **https://github.com/bhargavkoduru/eb1-research-agent-week3** as this week's GitHub link. It is public; no examiner invitation is needed.
3. Record a live demo of this app, at most five minutes, explaining the project, AI coding assistance and final result. Demo scripts stay local.
4. Optionally deploy this repository using `CLOUD_DEPLOYMENT.md`. Add the actual URL; examiners need no password or API key. Hosting is not yet complete.
5. Submit the Doc, video and GitHub links through the course form. Nothing has been submitted to the course on your behalf.

Demonstrate human approval before save. Use local mode for restart recovery; the hosted browser workspace is temporary. Do not claim a measured human time saving.
