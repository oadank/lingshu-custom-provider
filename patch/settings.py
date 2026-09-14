"""Settings read/save + LLM health check.

【本地改造版 2026-09-14】在原版基础上支持 custom 服务商的接口地址：
- 新增 llm_bases（每服务商的自定义 Base URL 映射）持久化；
- 保存 llm_base_url 时写入 llm_bases[provider]，custom 服务商取用；
- 其余逻辑与原版一致。
"""
import json

from app.config import SETTINGS_FILE, load_settings, resolve_llm, resolve_llm_for_provider
from app.errors import friendly_user_message
from app.llm.deepseek import DeepSeekError
from app.llm.providers import get_provider, list_providers
from app.schemas import SettingsOut, SettingsUpdate
from openai import AsyncOpenAI


def mask_key(key: str) -> str:
    key = key.strip()
    if not key:
        return ""
    if len(key) <= 8:
        return "*" * len(key)
    return key[:4] + "****" + key[-4:]


def get_settings_out() -> SettingsOut:
    cfg = load_settings()
    llm = resolve_llm(cfg)
    keys = llm.get("keys") or {}
    models = llm.get("models") or {}
    provider = llm["provider"]
    key = llm["api_key"]
    masked_map = {pid: mask_key(val) for pid, val in keys.items() if val}
    has_map = {pid: bool((val or "").strip()) for pid, val in keys.items()}
    if (cfg.deepseek_api_key or "").strip() and not has_map.get("deepseek"):
        has_map["deepseek"] = True
        masked_map["deepseek"] = mask_key(cfg.deepseek_api_key)
    has_any = any(has_map.values()) or bool(key)
    return SettingsOut(
        has_api_key=bool(key),
        has_any_api_key=has_any,
        api_key_masked=mask_key(key),
        llm_provider=provider,
        llm_model=llm["model"],
        llm_base_url=llm["base_url"],
        deepseek_model=llm["model"],
        deepseek_base_url=llm["base_url"],
        provider_label=llm["label"],
        supports_thinking=bool(llm["supports_thinking"]),
        provider_keys_masked=masked_map,
        provider_has_key=has_map,
        provider_models=models,
    )


def save_settings(payload: SettingsUpdate) -> SettingsOut:
    current = {}
    if SETTINGS_FILE.exists():
        current = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    data = payload.model_dump(exclude_unset=True)
    provider = str(data.get("llm_provider") or current.get("llm_provider") or "deepseek").strip().lower()
    preset = get_provider(provider)
    keys = dict(current.get("llm_keys") or {})
    if not isinstance(keys, dict):
        keys = {}
    models = dict(current.get("llm_models") or {})
    if not isinstance(models, dict):
        models = {}
    bases = dict(current.get("llm_bases") or {})
    if not isinstance(bases, dict):
        bases = {}

    new_key = data.get("llm_api_key")
    if new_key is None and data.get("deepseek_api_key") is not None:
        new_key = data.get("deepseek_api_key")
    if isinstance(new_key, str):
        trimmed = new_key.strip()
        if trimmed:
            keys[provider] = trimmed
        elif new_key == "":
            keys.pop(provider, None)

    new_model = data.get("llm_model")
    if new_model is None and data.get("deepseek_model") is not None:
        new_model = data.get("deepseek_model")
    if isinstance(new_model, str) and new_model.strip():
        models[provider] = new_model.strip()
    elif provider in models and preset.get("default_model"):
        models[provider] = str(preset["default_model"])

    new_base = data.get("llm_base_url")
    if new_base is None and data.get("deepseek_base_url") is not None:
        new_base = data.get("deepseek_base_url")
    if isinstance(new_base, str):
        tb = new_base.strip()
        if tb:
            bases[provider] = tb
        elif new_base == "":
            bases.pop(provider, None)

    requested = provider
    prev_active = str(current.get("llm_provider") or "deepseek").strip().lower() or "deepseek"
    is_picker_switch = (
        "llm_provider" in data
        and "llm_model" not in data
        and "llm_api_key" not in data
        and "deepseek_api_key" not in data
        and "deepseek_model" not in data
    )
    if is_picker_switch:
        active_provider = requested
    elif requested == "deepseek" or not str(keys.get(prev_active) or "").strip():
        active_provider = requested
    else:
        active_provider = prev_active
    if not str(keys.get(active_provider) or "").strip():
        active_provider = requested

    active_preset = get_provider(active_provider)
    active_key = str(keys.get(active_provider) or "").strip()
    active_model = str(models.get(active_provider) or active_preset.get("default_model") or "").strip()
    active_base = str(active_preset.get("base_url") or "").strip()
    if active_provider == "custom":
        active_base = str(bases.get("custom") or "").strip()

    current["llm_provider"] = active_provider
    current["llm_keys"] = keys
    current["llm_models"] = models
    current["llm_bases"] = bases
    current["llm_api_key"] = active_key
    current["llm_model"] = active_model
    current["llm_base_url"] = active_base
    if active_provider == "deepseek":
        current["deepseek_api_key"] = active_key
        current["deepseek_model"] = active_model or "deepseek-v4-flash"
        current["deepseek_base_url"] = active_base or "https://api.deepseek.com"

    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
    return get_settings_out()


async def health_check(provider_id: str | None = None, model: str | None = None) -> dict:
    if provider_id:
        llm = resolve_llm_for_provider(provider_id, model=model)
    else:
        llm = resolve_llm()
    if not llm["api_key"]:
        return {"ok": False, "message": f"尚未填写「{llm['label']}」的 API Key", "models": []}
    if not llm["base_url"] and llm["provider"] != "claude":
        return {"ok": False, "message": "服务商缺少 Base URL 预设", "models": []}

    if llm["api_style"] == "anthropic":
        from app.llm.anthropic import anthropic_chat

        text = await anthropic_chat(
            api_key=llm["api_key"],
            base_url=llm["base_url"],
            model=llm["model"] or "claude-sonnet-4-5",
            messages=[{"role": "user", "content": "ping"}],
            temperature=0,
            max_tokens=16,
        )
        return {
            "ok": True,
            "message": f"连接正常（{llm['label']} / {llm['model']}）",
            "models": [llm["model"]] if llm["model"] else [],
            "sample": (text or "")[:80],
        }

    from app.llm.deepseek import apply_thinking

    client = AsyncOpenAI(api_key=llm["api_key"], base_url=llm["base_url"])
    kwargs = {
        "model": llm["model"],
        "messages": [{"role": "user", "content": "ping"}],
        "max_tokens": 16,
        "temperature": 0,
    }
    kwargs = apply_thinking(kwargs, thinking=False)
    await client.chat.completions.create(**kwargs)
    return {"ok": True, "message": f"连接正常（{llm['label']} / {llm['model']}）", "models": []}


def providers_out() -> dict:
    return {"providers": list_providers()}


async def remote_models(
    provider_id: str | None = None,
    base_url: str | None = None,
    api_key: str | None = None,
) -> dict:
    """从 OpenAI 兼容端点拉取可用模型列表（GET {base_url}/models）。"""
    cfg = load_settings()
    pid = (provider_id or "").strip().lower() or "custom"
    keys = dict(cfg.llm_keys or {})
    if not isinstance(keys, dict):
        keys = {}
    preset = get_provider(pid)
    url = (base_url or "").strip() or str(preset.get("base_url") or "").strip()
    if pid == "custom":
        url = (base_url or cfg.llm_base_url or "").strip()
    key = (api_key or "").strip() or (keys.get(pid) or "").strip()
    if not url:
        return {"ok": False, "message": "请先填写接口地址（Base URL）", "models": []}
    if not url.endswith("/"):
        url += "/"
    import httpx

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.get(url + "models", headers={"Authorization": "Bearer " + key})
        resp.raise_for_status()
        data = resp.json()
        items = data.get("data") if isinstance(data, dict) else data
        ids = sorted(
            {
                str(m.get("id") or "").strip()
                for m in (items or [])
                if isinstance(m, dict) and str(m.get("id") or "").strip()
            }
        )
        return {"ok": True, "models": ids, "message": f"获取到 {len(ids)} 个模型"}
    except Exception as exc:
        return {"ok": False, "message": "拉取失败：" + str(exc)[:160], "models": []}
