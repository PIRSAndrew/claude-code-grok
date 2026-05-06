"""
Shared xAI / Grok client for Claude Code workflows.

xAI API is OpenAI-compatible at https://api.x.ai/v1.

Note: xAI's Live Search API (search_parameters) was deprecated 2026 — real-time
web/X/news access is now via the Agent Tools API at https://docs.x.ai/docs/guides/tools/overview
which uses an Anthropic-style tool-use loop. This client is text-only.

Auth: XAI_API_KEY from env var or any .env walking up from this file.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import httpx

API_BASE = "https://api.x.ai/v1"
CHAT_URL = f"{API_BASE}/chat/completions"
RESPONSES_URL = f"{API_BASE}/responses"
MODELS_URL = f"{API_BASE}/models"

MODEL_ALIASES = {
    # Default — fast non-reasoning
    "grok": "grok-4.20-non-reasoning",
    "grok-fast": "grok-4.20-non-reasoning",
    "grok-4.20-non-reasoning": "grok-4.20-non-reasoning",
    # Reasoning — grok-4.3 handles all reasoning tiers via reasoning_effort param
    # Pass reasoning_effort="low"|"medium"|"high" via extra_body={"reasoning_effort": "medium"}
    "grok-reasoning": "grok-4.3",
    "grok-4-reasoning": "grok-4.3",
    "grok-flagship": "grok-4.3",
    "grok-4.3": "grok-4.3",
    "grok-4": "grok-4.3",
    # Responses API reasoning model (/v1/responses endpoint, not chat/completions)
    "grok-4.20-reasoning": "grok-4.20-0309-reasoning",
    "grok-4.20": "grok-4.20-0309-reasoning",
    # Legacy — retired May 15 2026, redirected to current equivalents
    "grok-3": "grok-4.3",
    "grok-3-mini": "grok-4.3",
    "grok-code": "grok-4.3",
    "grok-4-fast": "grok-4.20-non-reasoning",
    "grok-4-fast-non-reasoning": "grok-4.20-non-reasoning",
    "grok-4-1-fast-non-reasoning": "grok-4.20-non-reasoning",
    "grok-4-1-fast-reasoning": "grok-4.3",
}

# Default: grok-4.20-non-reasoning (replaced grok-4-1-fast-non-reasoning, May 15 2026).
# For reasoning: use alias "grok-reasoning" (grok-4.3) + extra_body={"reasoning_effort":"medium"}.
DEFAULT_MODEL = "grok-4.20-non-reasoning"
DEFAULT_TIMEOUT = 120


def _find_env_key(name: str) -> str | None:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        env = parent / ".env"
        if not env.exists():
            continue
        try:
            for line in env.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith(f"{name}="):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
        except OSError:
            continue
    return None


def get_api_key() -> str:
    key = os.environ.get("XAI_API_KEY") or _find_env_key("XAI_API_KEY")
    if not key:
        raise RuntimeError(
            "XAI_API_KEY not found. Set env var or add to .env at workspace root."
        )
    return key


def resolve_model(name: str) -> str:
    return MODEL_ALIASES.get(name.lower().strip(), name.strip())


def list_models() -> list[dict[str, Any]]:
    headers = {"Authorization": f"Bearer {get_api_key()}"}
    with httpx.Client(timeout=30) as client:
        resp = client.get(MODELS_URL, headers=headers)
        resp.raise_for_status()
        return resp.json().get("data", [])


def chat(
    prompt_or_messages: str | list[dict[str, str]],
    *,
    model: str = DEFAULT_MODEL,
    system: str | None = None,
    temperature: float = 0.7,
    timeout: float = DEFAULT_TIMEOUT,
    extra_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Call Grok. Returns dict with response text, model id, usage, finish_reason.

    prompt_or_messages: str OR OpenAI-format list of {"role","content"}
    model: alias ("grok", "grok-reasoning", "grok-flagship") or full id
    system: optional system prompt
    extra_body: additional fields merged into the request body
    """
    model_id = resolve_model(model)

    if isinstance(prompt_or_messages, str):
        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt_or_messages})
    else:
        messages = prompt_or_messages

    body: dict[str, Any] = {
        "model": model_id,
        "messages": messages,
        "temperature": temperature,
    }
    if extra_body:
        body.update(extra_body)

    headers = {
        "Authorization": f"Bearer {get_api_key()}",
        "Content-Type": "application/json",
    }

    with httpx.Client(timeout=timeout) as client:
        resp = client.post(CHAT_URL, headers=headers, json=body)
        if resp.status_code >= 400:
            raise RuntimeError(
                f"xAI API error {resp.status_code}: {resp.text[:500]}"
            )
        data = resp.json()

    choice = data["choices"][0]
    return {
        "response": choice["message"]["content"],
        "model": model_id,
        "finish_reason": choice.get("finish_reason"),
        "usage": data.get("usage", {}) or {},
    }


if __name__ == "__main__":
    import argparse
    import json
    import sys

    # Force UTF-8 on Windows so unicode doesn't mojibake.
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8")
        except (AttributeError, OSError):
            pass

    parser = argparse.ArgumentParser(description="xAI Grok client")
    parser.add_argument(
        "prompt",
        nargs="?",
        help="Prompt text. If omitted (or '-'), read from stdin.",
    )
    parser.add_argument("--model", default=DEFAULT_MODEL, help="Model alias or id")
    parser.add_argument("--system", default=None, help="System prompt")
    parser.add_argument(
        "--temperature", type=float, default=0.7, help="Sampling temperature"
    )
    parser.add_argument("--list-models", action="store_true")
    parser.add_argument("--json", action="store_true", help="Emit full result as JSON")
    args = parser.parse_args()

    if args.list_models:
        for m in list_models():
            print(m.get("id"))
        sys.exit(0)

    if args.prompt and args.prompt != "-":
        prompt = args.prompt
    else:
        prompt = sys.stdin.read()
    if not prompt.strip():
        print("ERROR: empty prompt", file=sys.stderr)
        sys.exit(1)

    result = chat(
        prompt,
        model=args.model,
        system=args.system,
        temperature=args.temperature,
    )

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print(result["response"])
        usage = result["usage"]
        meta = (
            f"\n---\n[model={result['model']} | "
            f"in={usage.get('prompt_tokens', '?')} "
            f"out={usage.get('completion_tokens', '?')} "
            f"finish={result['finish_reason']}]"
        )
        print(meta, file=sys.stderr)
