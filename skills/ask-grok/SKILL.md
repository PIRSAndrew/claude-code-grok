---
name: ask-grok
description: >
  Send a prompt to xAI's Grok and return its response. Use when the user specifically
  names Grok — "ask grok", "what does grok say", "what does grok think", "run this
  by grok", "grok's take", "grok this", "grok opinion", "second opinion from grok",
  "send to grok". ANY mention of Grok as the target model triggers this skill, not
  llm-council — even if the phrasing sounds like a review request. llm-council is
  only for requests that explicitly want multiple models or the full council.
model: opus
---

# Ask Grok Skill

Direct xAI API access. One question in, one answer out.

## When to use

- After completing an analysis — want Grok's independent take on what you produced
- Quick second opinion when a full multi-model council is overkill

## When NOT to use

- Multi-model consensus → use `llm-council` instead
- Quick reasoning you already trust your primary model on → just answer, don't burn an API call

## How to invoke

The skill calls `xai_client.py` directly.

```bash
# Set your Python path
PYTHON_EXE="python3"  # macOS/Linux
# PYTHON_EXE="C:/Users/you/AppData/Local/Python/bin/python.exe"  # Windows

CLIENT="$CLAUDE_PROJECT_DIR/.claude/skills/shared/xai_client.py"
```

### Pattern 1 — Single short prompt

```bash
"$PYTHON_EXE" "$CLIENT" "Your question here"
```

### Pattern 2 — Long prompt via stdin (preferred for re-running an analysis)

Construct the full prompt — include the question, relevant context, and your analysis — and pipe via stdin:

```bash
cat <<'EOF' | "$PYTHON_EXE" "$CLIENT" - --system "You are a skeptical reviewer. Give your honest independent take."
[Original question]

[Relevant context]

[Your analysis or draft answer]

Question for you, Grok: do you agree? What did I miss or get wrong?
EOF
```

## Model selection

**Read `programs/ask-grok.md` before selecting a model.** That file has the current routing heuristics (task type → model) and the invocation log that informs them.

Quick reference:

| Alias | Underlying model | Default for |
|-------|-----------------|-------------|
| `grok` | `grok-4.20-non-reasoning` | `underwriting`, `drafting`, `research`, `general` |
| `grok-reasoning` | `grok-4.3` | `legal/contract`, `legal/general`, `financial` |

Pass via `--model`:

```bash
"$PYTHON_EXE" "$CLIENT" "..." --model grok-reasoning
```

## Presenting the result

After the call returns, present:

1. **What we asked Grok** — 1-line summary
2. **Grok's response** — quote or paraphrase verbatim. Don't editorialize unless asked.
3. **Where it disagrees** (if applicable) — the most useful signal from a second opinion
4. **Cost** — `[model X | tokens in/out]` footer

Don't blindly defer to Grok. The value is the cross-check, not the override.

## Logging (do this after every call)

Append one row to the invocation log in `programs/ask-grok.md`:

```
| YYYY-MM-DD | task_type | one-line prompt summary | model_alias | quality | notes |
```

Quality: `good` (added real value), `ok` (solid, nothing surprising), `miss` (wrong model tier).
After every 5 entries, check if routing heuristics should be updated.

## Prerequisites

- `XAI_API_KEY` in `.env` at workspace root or as env var
- Python 3.9+ with `httpx` installed (`pip install httpx`)
