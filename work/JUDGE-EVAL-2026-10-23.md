# Judge Evaluation: openrouter/free vs DeepSeek
Date: 2026-10-24
Dataset: 81 events across 9 criteria triples

## Setup
- A (reference): DeepSeek pro via Kilo
- B (today's model): DeepSeek v4.1 flash via Kilo
- C (candidate): openrouter/free (routes to different free models per call)
- Prompt: judge_v3 (the app's real prompt), temperature 0, json_object mode

## Free models used by OpenRouter

- `nvidia/nemotron-3.5-lightning:free`: 15 calls
- `cohere/north-mini-code:free`: 13 calls
- `recursive/flint-v1.0:free`: 10 calls
- `nvidia/nemotron-3.5-super-vl:free`: 10 calls
- `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free`: 9 calls
- `dots-studio/dots-3-note-preview:free`: 8 calls
- `nvidia/nemotron-3-ultra-550b-a55b:free`: 7 calls
- `poolside/laguna-s-2.1:free`: 5 calls
- `xingchen-agi/xing4.0-29b-a4b:free`: 4 calls

## Metrics

| Metric | B (flash) vs A | C (free) vs A | C+guard vs A |
|--------|---------------|--------------|-------------|
| Events judged | 81/81 | 81/81 | 81/81 |
| Decision agreement (90/40) | 82.7% | 84.0% | 84.0% |
| Score MAE | 8.0 | 9.5 | 9.5 |
| Schema violations (before) | 5 | 0 | — |
| Schema violations (after) | 0 | 0 | — |
| Latency p50 | 1.7s | 12.7s | 12.7s |
| Latency p95 | 3.0s | 35.2s | 35.2s |
| Errors | 0 | 0 | 0 |

## Cost per 100 events

| Route | Cost |
|-------|------|
| A (pro) | ~$0.50-1.00 |
| B (flash) | ~$0.05-0.10 |
| C (free) | $0.00 |
| C+guard | ~$0.05-0.15 |

## Failure examples (3 worst C vs A)

### 1. diff=90: A=5 C=95
- Event: Lizz Wright -- Berlin, DE
- Criteria: jazz in Berlin (Germany) next week
- A reason: This jazz concert in Berlin is on 2026-11-03, after next week (2026-10-26 to 2026-11-01).
- C reason: Jazz in Berlin on 3 November at Kammermusiksaal fits your next-week request well.
- C model: recursive/flint-v1.0:free

### 2. diff=90: A=5 C=95
- Event: [London] Enterprise AI Showcase (October) -- London, GB
- Criteria: AI meetups and tech events in London next week
- A reason: You asked for next week, but this London AI meetup is on 19 October, so dates don't match.
- C reason: The event is in London, matches the AI meetup topic, and occurs on October 19, 2026 — next week from today.
- C model: xingchen-agi/xing4.0-29b-a4b:free

### 3. diff=70: A=5 C=75
- Event: The Use of AI for Electronic and Print Media by London Bangla Press Club -- London, GB
- Criteria: AI meetups and tech events in London next week
- A reason: This AI talk in London is on 10 November, not next week.
- C reason: The event is in London and about AI, but takes place on 2026-11-10, outside next week, so it partially fits.
- C model: nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free

## Recommendation

Stay on DeepSeek. openrouter/free decision agreement is 84.0% (bare) / 84.0% (guarded), MAE 9.5.
The latency (12.7s p50, 35.2s p95) and unreliable model selection make it unsuitable even with guardrails.
Flash at 82.7% agreement and 8.0 MAE vs pro is the better economy option.
