---
name: score-steering
description: Advise a human on steering a coding agent using session evidence; never auto-fix.
disable-model-invocation: true
---

# Score steering

Read [`rubrics/human-steering.md`](rubrics/human-steering.md) relative to this file, including **all Assess and causality rules**. Inspect human interventions, what was known **at each turn**, agent reactions and task outcome. Do not infer a user's fault from the model's mistake or later information.

Score `1.0/0.8/0.4/0.2/N/A`; explain evidence and attributable impact. Attribute issues `human|agent|shared|external`, confidence `high|medium|low`. Independent of agent score; advisory only. No automatic edits to instructions, code, skills or config.

Output <= 140 words:
```
Steering: label/score (confidence)
Worked: <evidenced choice>
Improve: <one controllable issue + message reference, or none evidenced>
Responsibility: human|agent|shared|external
Better intervention: "<short wording, or not needed>"
Lesson: <one transferable lesson, or none evidenced>
```
No hindsight, fabricated causal claims, blame, or rewarding long prompts.
