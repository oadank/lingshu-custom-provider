"""常见大模型服务商预设（OpenAI 兼容为主）。

【本地改造版 2026-09-14】在原版基础上新增 `custom` 自定义服务商：
- 接口地址（Base URL）由用户在设置页填写，保存于设置文件 llm_base_url 字段；
- get_provider('custom') 动态注入用户保存的地址，使 resolve_llm /
  resolve_llm_for_provider / save_settings / health_check 全链路生效；
- 其余 9 个预置服务商与原版完全一致。
"""
from __future__ import annotations

from typing import Any

PROVIDERS: dict[str, dict[str, Any]] = {
    "deepseek": {
        "id": "deepseek",
        "label": "DeepSeek",
        "group": "primary",
        "base_url": "https://api.deepseek.com",
        "default_model": "deepseek-v4-flash",
        "docs_url": "https://platform.deepseek.com/",
        "api_style": "openai",
        "supports_thinking": True,
        "thinking_style": "deepseek",
        "thinking_default_on": True,
        "models": [
            {"id": "deepseek-v4-flash", "label": "DeepSeek V4 Flash"},
            {"id": "deepseek-v4-pro", "label": "DeepSeek V4 Pro"},
        ],
    },
    "openai": {
        "id": "openai",
        "label": "OpenAI（GPT）",
        "group": "other",
        "base_url": "https://api.openai.com/v1",
        "default_model": "gpt-4o",
        "docs_url": "https://platform.openai.com/api-keys",
        "api_style": "openai",
        "supports_thinking": False,
        "models": [
            {"id": "gpt-4o", "label": "GPT-4o"},
            {"id": "gpt-4o-mini", "label": "GPT-4o mini"},
            {"id": "gpt-4.1", "label": "GPT-4.1"},
            {"id": "o4-mini", "label": "o4-mini"},
        ],
    },
    "gemini": {
        "id": "gemini",
        "label": "Google Gemini",
        "group": "other",
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "default_model": "gemini-2.5-flash",
        "docs_url": "https://aistudio.google.com/apikey",
        "api_style": "openai",
        "supports_thinking": False,
        "models": [
            {"id": "gemini-2.5-flash", "label": "Gemini 2.5 Flash"},
            {"id": "gemini-2.5-pro", "label": "Gemini 2.5 Pro"},
        ],
    },
    "claude": {
        "id": "claude",
        "label": "Claude（Anthropic）",
        "group": "other",
        "base_url": "https://api.anthropic.com",
        "default_model": "claude-sonnet-4-5",
        "docs_url": "https://console.anthropic.com/",
        "api_style": "anthropic",
        "supports_thinking": False,
        "models": [
            {"id": "claude-sonnet-4-5", "label": "Claude Sonnet 4.5"},
            {"id": "claude-opus-4-5", "label": "Claude Opus 4.5"},
            {"id": "claude-haiku-4-5", "label": "Claude Haiku 4.5"},
        ],
    },
    "kimi": {
        "id": "kimi",
        "label": "Kimi（月之暗面）",
        "group": "other",
        "base_url": "https://api.moonshot.cn/v1",
        "default_model": "kimi-k2.6",
        "docs_url": "https://platform.moonshot.cn/",
        "api_style": "openai",
        "supports_thinking": True,
        "thinking_style": "kimi",
        "thinking_default_on": True,
        "fixed_sampling": True,
        "models": [
            {"id": "kimi-k2.6", "label": "Kimi 2.6"},
            {"id": "kimi-k2.7-code", "label": "Kimi 2.7 Code"},
        ],
    },
    "minimax": {
        "id": "minimax",
        "label": "MiniMax",
        "group": "other",
        "base_url": "https://api.minimaxi.com/v1",
        "default_model": "MiniMax-M3",
        "docs_url": "https://platform.minimaxi.com/",
        "api_style": "openai",
        "supports_thinking": True,
        "thinking_style": "minimax",
        "thinking_default_on": True,
        "models": [
            {"id": "MiniMax-M3", "label": "MiniMax M3"},
            {"id": "MiniMax-M2.7", "label": "MiniMax M2.7"},
        ],
    },
    "glm": {
        "id": "glm",
        "label": "智谱 GLM",
        "group": "other",
        "base_url": "https://open.bigmodel.cn/api/paas/v4",
        "default_model": "glm-4.7",
        "docs_url": "https://open.bigmodel.cn/",
        "api_style": "openai",
        "supports_thinking": True,
        "thinking_style": "glm",
        "thinking_default_on": True,
        "supports_forced_tool_choice": False,
        "models": [
            {"id": "glm-4.7", "label": "GLM-4.7"},
            {"id": "glm-4.7-flash", "label": "GLM-4.7 Flash"},
            {"id": "glm-5", "label": "GLM-5"},
        ],
    },
    "qwen": {
        "id": "qwen",
        "label": "通义千问",
        "group": "other",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "default_model": "qwen-plus",
        "docs_url": "https://dashscope.console.aliyun.com/",
        "api_style": "openai",
        "supports_thinking": False,
        "models": [
            {"id": "qwen-plus", "label": "通义 Plus"},
            {"id": "qwen-max", "label": "通义 Max"},
            {"id": "qwen-turbo", "label": "通义 Turbo"},
        ],
    },
    "openrouter": {
        "id": "openrouter",
        "label": "OpenRouter",
        "group": "other",
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "openai/gpt-4o-mini",
        "docs_url": "https://openrouter.ai/keys",
        "api_style": "openai",
        "supports_thinking": False,
        "models": [
            {"id": "openai/gpt-4o-mini", "label": "GPT-4o mini"},
            {"id": "anthropic/claude-sonnet-4.5", "label": "Claude Sonnet 4.5"},
            {"id": "google/gemini-2.5-flash", "label": "Gemini 2.5 Flash"},
        ],
    },
    "custom": {
        "id": "custom",
        "label": "自定义接口",
        "group": "other",
        "base_url": "",
        "default_model": "",
        "docs_url": "",
        "api_style": "openai",
        "supports_thinking": False,
        "models": [],
    },
}

MODEL_MIGRATIONS: dict[str, str] = {
    "deepseek-chat": "deepseek-v4-flash",
    "deepseek-reasoner": "deepseek-v4-flash",
    "kimi-k2.5": "kimi-k2.6",
    "moonshot-v1-auto": "kimi-k2.6",
    "moonshot-v1-128k": "kimi-k2.6",
    "moonshot-v1-8k": "kimi-k2.6",
    "moonshot-v1-32k": "kimi-k2.6",
    "MiniMax-Text-01": "MiniMax-M3",
    "glm-4.5": "glm-4.7",
    "glm-4.5-flash": "glm-4.7-flash",
    "glm-4-flash": "glm-4.7-flash",
    "gemini-2.0-flash": "gemini-2.5-flash",
    "anthropic/claude-sonnet-4": "anthropic/claude-sonnet-4.5",
    "google/gemini-2.0-flash-001": "google/gemini-2.5-flash",
}


def _custom_base_url() -> str:
    """读取用户在设置里保存的自定义接口地址（llm_base_url）。"""
    try:
        import json

        from app.config import SETTINGS_FILE

        if SETTINGS_FILE.exists():
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            return str(data.get("llm_base_url") or "").strip()
    except Exception:
        pass
    return ""


def list_providers() -> list[dict[str, Any]]:
    return [
        {
            "id": p["id"],
            "label": p["label"],
            "group": p.get("group") or "other",
            "base_url": _custom_base_url() if p["id"] == "custom" else p["base_url"],
            "default_model": p["default_model"],
            "docs_url": p["docs_url"],
            "api_style": p["api_style"],
            "supports_thinking": bool(p.get("supports_thinking")),
            "models": list(p.get("models") or []),
        }
        for p in PROVIDERS.values()
    ]


def get_provider(provider_id: str) -> dict[str, Any]:
    key = (provider_id or "deepseek").strip().lower() or "deepseek"
    preset = PROVIDERS.get(key) or PROVIDERS["deepseek"]
    if preset["id"] == "custom":
        preset = {**preset, "base_url": _custom_base_url()}
    return preset


def normalize_model_id(provider_id: str, model: str | None) -> str:
    preset = get_provider(provider_id)
    mid = (model or "").strip()
    if mid in MODEL_MIGRATIONS:
        mid = MODEL_MIGRATIONS[mid]
    allowed = {str(m.get("id") or "") for m in (preset.get("models") or [])}
    if mid and allowed and mid not in allowed:
        mid = ""
    return mid or str(preset.get("default_model") or "")
