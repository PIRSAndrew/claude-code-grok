# Multi-Model Council Integration

This shows how to wire direct xAI API calls alongside OpenRouter in a parallel multi-model setup — so Grok calls go direct (no markup, no proxying) while other models (GPT, Gemini, Anthropic) continue through OpenRouter.

## The pattern

xAI's API is OpenAI-compatible. Same `chat/completions` endpoint, same request/response format. The only difference is the URL and auth header.

In your council script, add a routing function:

```python
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
XAI_URL = "https://api.x.ai/v1/chat/completions"

def _is_xai(model: str) -> bool:
    """Any model starting with 'grok' routes direct to xAI."""
    return model.startswith("grok")
```

Then in your `call_model()` function, branch on the model:

```python
async def call_model(client, openrouter_key, xai_key, model, messages, max_attempts=3):
    if _is_xai(model):
        url = XAI_URL
        headers = {"Authorization": f"Bearer {xai_key}", "Content-Type": "application/json"}
    else:
        url = OPENROUTER_URL
        headers = {
            "Authorization": f"Bearer {openrouter_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://your-app.com",
        }

    resp = await client.post(url, json={"model": model, "messages": messages}, headers=headers)
    # ... rest of your retry/error handling
```

## Model aliases

Use xAI's native model IDs (not OpenRouter's `x-ai/` prefixed versions) for direct calls:

```python
MODEL_ALIASES = {
    # Direct xAI (native IDs — no x-ai/ prefix)
    "grok": "grok-4.20-non-reasoning",
    "grok-reasoning": "grok-4.3",
    "grok-flagship": "grok-4.3",
    # OpenRouter (provider/model format)
    "gpt": "openai/gpt-5.4",
    "gemini": "google/gemini-3.1-pro-preview",
    "opus": "anthropic/claude-opus-4.6",
}
```

## Cost tracking

xAI's API returns `cost_in_usd_ticks` in the usage object (1 tick = 1/10,000,000 USD). OpenRouter returns a `cost` field directly. Handle both:

```python
def accumulate_usage(bucket, results):
    for r in results:
        u = r.get("usage") or {}
        for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
            v = u.get(key)
            if isinstance(v, (int, float)):
                bucket[key] = bucket.get(key, 0) + v
        # OpenRouter cost field
        cost = u.get("cost")
        if isinstance(cost, (int, float)):
            bucket["cost_usd"] = round(bucket.get("cost_usd", 0.0) + cost, 6)
        # xAI cost_in_usd_ticks (1 tick = 1/10M USD)
        ticks = u.get("cost_in_usd_ticks")
        if isinstance(ticks, (int, float)):
            bucket["cost_usd"] = round(bucket.get("cost_usd", 0.0) + ticks / 10_000_000, 6)
```

## Extending to other direct integrations

The same pattern works for any provider with an OpenAI-compatible API:

1. Add a URL constant for the provider
2. Add a `_is_<provider>(model)` routing function based on model name prefix
3. Branch in `call_model()` to select the right URL + auth header
4. Handle any provider-specific usage field differences

Providers with OpenAI-compatible APIs: xAI, Groq, Together AI, Fireworks, Mistral, Perplexity, and others.
