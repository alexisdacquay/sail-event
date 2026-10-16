# References (external, read on demand)

| Ref | URL | Use at |
|---|---|---|
| Course repo | github.com/DataTalksClub/ai-dev-tools-zoomcamp | all |
| Rubric snapshot | work/rubric-2026-10-16.md | all |
| Lesson articles 1–5 | aishippingblog.com (see work/METHOD.md) | by step |
| retroloop (lesson 1 example) | github.com/alexeygrigorev/retroloop | S2, S3 |
| interview-canvas-share (lessons 2–4 example) | github.com/alexeygrigorev/interview-canvas-share | S4–S12 |
| hermes-pa (prior art, ideas only) | github.com/alexisdacquay/hermes-pa | S13 |
| 12-factor-agents | github.com/humanlayer/12-factor-agents | S12 responder, S13 scorer |

## 12-factor-agents, the factors to apply

| Factor | Where |
|---|---|
| 2 own your prompts | scorer prompt in repo, versioned |
| 4 tools are structured outputs | scorer returns {score, reason} as schema |
| 5 unify execution and business state | run/event state in the DB, not in the agent |
| 7 contact humans with tool calls | borderline → approval queue |
| 8 own your control flow | thresholds and triage in code, not in the model |
| 10 small, focused agents | scorer scores; responder responds; nothing else |
| 12 stateless reducer | score(event, criteria) → verdict, no memory |
