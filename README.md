# claude-code-grok

Direct xAI Grok integration for Claude Code. Bypasses OpenRouter and calls the xAI API directly — no markup, full model access, and a logging/routing layer that gets smarter over time.

## What's included

| File | Purpose |
|------|---------|
| `shared/xai_client.py` | Shared Python client for the xAI API (OpenAI-compatible) |
| `skills/ask-grok/SKILL.md` | Claude Code skill — auto-triggers on "ask grok", "grok's take", etc. |
| `programs/ask-grok.md` | Model routing rules + invocation log that compounds over time |
| `council-integration/INTEGRATION.md` | How to wire direct xAI into a multi-model council setup |

## Why direct xAI vs OpenRouter?

- **No markup** — pay xAI rates directly
- **Full model access** — including models OpenRouter doesn't expose
- **Future Agent Tools API** — xAI's real-time web/X/news retrieval when it's ready
- **Your logs** — routing decisions and invocation history stay local

## Prerequisites

- [Claude Code](https://claude.ai/code) installed
- Python 3.9+ with `httpx` (`pip install httpx`)
- An [xAI API key](https://console.x.ai/) — set as `XAI_API_KEY`

## Setup

### 1. Copy files into your Claude Code workspace

```
your-workspace/
└── .claude/
    ├── skills/
    │   ├── shared/
    │   │   └── xai_client.py      ← from shared/
    │   └── ask-grok/
    │       └── SKILL.md           ← from skills/ask-grok/
    └── programs/
        └── ask-grok.md            ← from programs/
```

### 2. Set your API key

Copy `.env.example` to `.env` at your workspace root and add your key:

```
XAI_API_KEY=xai-your-key-here
```

The client walks up from its own location looking for a `.env` — no additional config needed.

### 3. Update the Python path in `skills/ask-grok/SKILL.md`

Replace `PYTHON_EXE` with your Python interpreter path:
- **macOS/Linux**: `python3` or a virtualenv path
- **Windows**: your full Python path (e.g. `C:/Users/you/AppData/Local/Python/bin/python.exe`)

## Usage

Once installed, Claude Code will auto-trigger the skill on:
- "ask grok"
- "what does grok think"
- "grok's take on this"
- "run this by grok"
- "grok opinion"
- "second opinion from grok"

You can also call the client directly:

```bash
# Single prompt
python shared/xai_client.py "What is the capital of France?"

# Long prompt via stdin (safer for complex content)
cat prompt.txt | python shared/xai_client.py - --system "You are a skeptical reviewer."

# Use reasoning model
python shared/xai_client.py "Complex analytical question" --model grok-reasoning

# List available models
python shared/xai_client.py --list-models

# Get full JSON output (includes usage/tokens)
python shared/xai_client.py "Your question" --json
```

## Model aliases

| Alias | Model | Use for |
|-------|-------|---------|
| `grok` (default) | `grok-4.20-non-reasoning` | Most calls — fast, capable |
| `grok-reasoning` | `grok-4.3` | Deep analysis — legal, financial, complex reasoning |
| `grok-flagship` | `grok-4.3` | Same as grok-reasoning |

`grok-4.3` supports `reasoning_effort` levels (`low`/`medium`/`high`) via `extra_body`.

## Model routing + logging

The `programs/ask-grok.md` file is read before every invocation. It contains:

1. **Task type taxonomy** — classify the ask before selecting a model
2. **Routing heuristics** — which model to use for which task type
3. **Invocation log** — every call logged with quality rating
4. **Auto-update rules** — when the log has enough data, heuristics get updated

Current defaults:
- `legal/contract`, `legal/general`, `financial` → `grok-reasoning` (grok-4.3)
- `underwriting`, `drafting`, `research`, `general` → `grok` (grok-4.20-non-reasoning)

The routing table evolves as you log more calls. Quality ratings (`good`/`ok`/`miss`) drive heuristic updates every 5 entries.

## Extending to other models

The same pattern works for any OpenAI-compatible API:

1. Copy `shared/xai_client.py` and swap `API_BASE` to your provider's endpoint
2. Add a `SKILL.md` for that model following the same structure
3. Add a `programs/<model>.md` with its own routing table and log

For non-OpenAI-compatible APIs (Anthropic, Google), you'll need a provider-specific client, but the skill/program pattern is identical.

## Multi-model council integration

See `council-integration/INTEGRATION.md` for how to route specific models directly while keeping others on OpenRouter in a parallel multi-model setup.

## Model deprecation

xAI retires models periodically. When a model is deprecated:
1. Update `MODEL_ALIASES` in `shared/xai_client.py` to point to the replacement
2. Update `DEFAULT_MODEL` if the default was retired
3. Update the model table in `skills/ask-grok/SKILL.md`

The alias layer means your prompts never need to change — just update the mapping.

## License

MIT
