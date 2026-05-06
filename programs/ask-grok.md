# Ask Grok — Program File

Read this file before every "Ask Grok" invocation. It contains:
1. **Model routing heuristics** — which Grok model to use for which task type
2. **Invocation log** — past calls that inform the heuristics
3. **Learning rules** — how to update heuristics from new data

---

## Task Type Taxonomy

Classify the task into one of these before selecting a model:

| Task Type | Examples |
|-----------|----------|
| `legal/contract` | Contract review, redlines, clause analysis, negotiation |
| `legal/general` | Case law questions, regulatory questions, general legal second opinion |
| `financial` | Financial modeling, quantitative analysis, valuation |
| `underwriting` | Deal analysis, credit review, risk assessment |
| `drafting` | Writing emails, agreements, memos |
| `research` | Factual lookups, competitor intel, market data, news |
| `general` | General second opinion on prose, quick checks, anything else |

---

## Model Routing Heuristics

Current routing rules (updated as log data accumulates):

| Task Type | Model Alias | Underlying Model | Rationale |
|-----------|-------------|-----------------|----------|
| `legal/contract` | `grok-reasoning` | `grok-4.3` | Contract reasoning benefits from slower, deeper analysis |
| `legal/general` | `grok-reasoning` | `grok-4.3` | Legal questions often have nuance that rewards reasoning |
| `financial` | `grok-reasoning` | `grok-4.3` | Quantitative analysis, multi-step reasoning |
| `underwriting` | `grok` | `grok-4.20-non-reasoning` | Pattern recognition; fast response preferred |
| `drafting` | `grok` | `grok-4.20-non-reasoning` | Stylistic, not analytical; fast is fine |
| `research` | `grok` | `grok-4.20-non-reasoning` | Factual recall; reasoning overhead not worth it |
| `general` | `grok` | `grok-4.20-non-reasoning` | Default; upgrade if complexity warrants |

**Override rule**: If the user explicitly says "reasoning" or "deep dive", always use `grok-reasoning`.

---

## How to Log an Invocation

After every "Ask Grok" call, append one row to the log table below:

```
| YYYY-MM-DD | task_type | one-line prompt summary (no sensitive data) | model_alias | quality | notes |
```

- **quality**: `good` = Grok added real value or caught something; `ok` = solid but nothing surprising; `miss` = wrong model tier
- **notes**: anything that would change future routing
- Do NOT log sensitive data — task type + prompt summary only

---

## Invocation Log

| Date | Task Type | Prompt Summary | Model Used | Quality | Notes |
|------|-----------|----------------|------------|---------|-------|
| _(first entry goes here)_ | | | | | |

---

## Routing Update Rules

After every 5 logged calls, review the log and ask:
- Are there task types consistently marked `miss` because the model was wrong tier? → Update the heuristic table.
- Are `legal/contract` or `financial` calls coming back `ok` instead of `good`? → Consider whether reasoning is actually adding value.
- Are `general` or `research` calls slow? → Those should never be on reasoning tier.

Update the heuristic table in place when patterns are clear.
