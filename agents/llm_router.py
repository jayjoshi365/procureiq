"""
LLM Router — unified interface for Claude, OpenAI, Deepseek, and Grok.

All agents and app.py route through here instead of calling provider SDKs directly.
Supports streaming and non-streaming calls with a consistent message format.

Usage:
    from agents.llm_router import call_llm, stream_llm, PROVIDERS

    text = call_llm(
        messages=[{"role": "user", "content": "Summarize this contract..."}],
        provider="openai",
        api_key="sk-...",
        system="You are a procurement expert.",
        model="gpt-4o-mini",
    )
"""
import os
from typing import Dict, List, Optional, Generator

# ── Provider registry ─────────────────────────────────────────────────
# Add new providers here without touching any other file.

PROVIDERS: Dict[str, Dict] = {
    "claude": {
        "name": "Claude (Anthropic)",
        "models": {
            "claude-sonnet-4-6":          "Sonnet 4.6 — Best quality",
            "claude-haiku-4-5-20251001":  "Haiku 4.5 — Fast & cheap",
        },
        "default_model": "claude-sonnet-4-6",
        "key_placeholder": "sk-ant-...",
        "key_help": "console.anthropic.com → API Keys",
        "supports_tool_use": True,
        "env_var": "ANTHROPIC_API_KEY",
        "base_url": None,
    },
    "openai": {
        "name": "ChatGPT (OpenAI)",
        "models": {
            "gpt-4o":      "GPT-4o — Best quality",
            "gpt-4o-mini": "GPT-4o Mini — Fast & cheap",
        },
        "default_model": "gpt-4o-mini",
        "key_placeholder": "sk-...",
        "key_help": "platform.openai.com → API Keys",
        "supports_tool_use": False,
        "env_var": "OPENAI_API_KEY",
        "base_url": None,
    },
    "deepseek": {
        "name": "Deepseek",
        "models": {
            "deepseek-chat":     "Deepseek V3 — Best value",
            "deepseek-reasoner": "Deepseek R1 — Deep reasoning",
        },
        "default_model": "deepseek-chat",
        "key_placeholder": "sk-...",
        "key_help": "platform.deepseek.com → API Keys",
        "supports_tool_use": False,
        "env_var": "DEEPSEEK_API_KEY",
        "base_url": "https://api.deepseek.com/v1",
    },
    "grok": {
        "name": "Grok (xAI)",
        "models": {
            "grok-3-mini": "Grok 3 Mini — Fast & cheap",
            "grok-3":      "Grok 3 — Best quality",
        },
        "default_model": "grok-3-mini",
        "key_placeholder": "xai-...",
        "key_help": "console.x.ai → API Keys",
        "supports_tool_use": False,
        "env_var": "GROK_API_KEY",
        "base_url": "https://api.x.ai/v1",
    },
}

DEFAULT_PROVIDER = "claude"


def get_default_model(provider: str) -> str:
    return PROVIDERS.get(provider, PROVIDERS[DEFAULT_PROVIDER])["default_model"]


def supports_tool_use(provider: str) -> bool:
    return PROVIDERS.get(provider, {}).get("supports_tool_use", False)


def get_server_key(provider: str) -> str:
    """Return a server-configured key for this provider (env var / Streamlit secrets)."""
    env_var = PROVIDERS.get(provider, {}).get("env_var", "")
    return os.getenv(env_var, "").strip()


# ── Anthropic caller ──────────────────────────────────────────────────

def _call_anthropic(messages: List[Dict], api_key: str, system: str,
                     model: str, max_tokens: int) -> str:
    try:
        import anthropic
    except ImportError:
        return "anthropic package not installed. Run: pip install anthropic"
    try:
        client = anthropic.Anthropic(api_key=api_key)
        kwargs: Dict = {"model": model, "max_tokens": max_tokens, "messages": messages}
        if system:
            kwargs["system"] = system
        resp = client.messages.create(**kwargs)
        return resp.content[0].text if resp.content else ""
    except Exception as e:
        return f"Claude API error: {e}"


def _stream_anthropic(messages: List[Dict], api_key: str, system: str,
                       model: str, max_tokens: int) -> Generator:
    try:
        import anthropic
    except ImportError:
        yield "anthropic package not installed."; return
    try:
        client = anthropic.Anthropic(api_key=api_key)
        kwargs: Dict = {"model": model, "max_tokens": max_tokens, "messages": messages}
        if system:
            kwargs["system"] = system
        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text
    except Exception as e:
        yield f"Claude API error: {e}"


# ── OpenAI-compatible caller (OpenAI, Deepseek, Grok) ─────────────────

def _build_oa_messages(messages: List[Dict], system: str) -> List[Dict]:
    """Prepend system message in OpenAI format."""
    result = []
    if system:
        result.append({"role": "system", "content": system})
    result.extend(messages)
    return result


def _call_openai_compat(messages: List[Dict], api_key: str, system: str,
                         model: str, base_url: Optional[str], max_tokens: int) -> str:
    try:
        from openai import OpenAI
    except ImportError:
        return "openai package not installed. Run: pip install openai"
    try:
        kwargs: Dict = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        client = OpenAI(**kwargs)
        resp = client.chat.completions.create(
            model=model,
            messages=_build_oa_messages(messages, system),
            max_tokens=max_tokens,
        )
        return resp.choices[0].message.content if resp.choices else ""
    except Exception as e:
        return f"{model} API error: {e}"


def _stream_openai_compat(messages: List[Dict], api_key: str, system: str,
                           model: str, base_url: Optional[str], max_tokens: int) -> Generator:
    try:
        from openai import OpenAI
    except ImportError:
        yield "openai package not installed."; return
    try:
        kwargs: Dict = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        client = OpenAI(**kwargs)
        stream = client.chat.completions.create(
            model=model,
            messages=_build_oa_messages(messages, system),
            max_tokens=max_tokens,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices else None
            if delta:
                yield delta
    except Exception as e:
        yield f"{model} API error: {e}"


# ── Public API ────────────────────────────────────────────────────────

def call_llm(
    messages: List[Dict[str, str]],
    provider: str = DEFAULT_PROVIDER,
    api_key: str = "",
    system: str = "",
    model: Optional[str] = None,
    max_tokens: int = 2048,
) -> str:
    """
    Call any supported LLM with a unified message list.

    Args:
        messages:   [{"role": "user"|"assistant", "content": "..."}]
        provider:   "claude" | "openai" | "deepseek" | "grok"
        api_key:    Provider API key
        system:     System prompt (optional)
        model:      Model override (uses provider default if omitted)
        max_tokens: Maximum tokens to generate (default 2048)

    Returns:
        Response text, or an error string prefixed with the provider name.
    """
    if not api_key:
        name = PROVIDERS.get(provider, {}).get("name", provider)
        return f"No API key for {name}. Enter your key in the sidebar."

    model = model or get_default_model(provider)

    if provider == "claude":
        return _call_anthropic(messages, api_key, system, model, max_tokens)

    info = PROVIDERS.get(provider)
    if not info:
        return f"Unknown provider '{provider}'. Choose from: {', '.join(PROVIDERS)}"

    return _call_openai_compat(messages, api_key, system, model, info.get("base_url"), max_tokens)


def stream_llm(
    messages: List[Dict[str, str]],
    provider: str = DEFAULT_PROVIDER,
    api_key: str = "",
    system: str = "",
    model: Optional[str] = None,
    max_tokens: int = 2048,
) -> Generator[str, None, None]:
    """Stream tokens from any supported LLM provider."""
    if not api_key:
        name = PROVIDERS.get(provider, {}).get("name", provider)
        yield f"No API key for {name}. Enter your key in the sidebar."
        return

    model = model or get_default_model(provider)

    if provider == "claude":
        yield from _stream_anthropic(messages, api_key, system, model, max_tokens)
        return

    info = PROVIDERS.get(provider)
    if not info:
        yield f"Unknown provider '{provider}'."
        return

    yield from _stream_openai_compat(messages, api_key, system, model, info.get("base_url"), max_tokens)
