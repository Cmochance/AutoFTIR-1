from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import json

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

try:
    from zhipuai import ZhipuAI
except Exception as exc:  # noqa: BLE001
    ZhipuAI = None  # type: ignore[assignment]
    _ZHIPUAI_IMPORT_ERROR = exc
else:
    _ZHIPUAI_IMPORT_ERROR = None


app = FastAPI(title="AutoFTIR Backend", version="0.1.0")


def _try_load_dotenv() -> None:
    """Best-effort load of project-root .env.

    约定：敏感信息（如 ZHIPUAI_API_KEY）放在本机的 .env 中，且不提交到仓库。
    云部署时依然推荐使用系统环境变量注入。
    """

    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return

    try:
        from dotenv import dotenv_values, load_dotenv  # type: ignore[import-not-found]

        # 先按常规规则加载：系统环境变量优先于 .env
        load_dotenv(dotenv_path=env_path, override=False)

        # 兼容场景：某些环境里变量已存在但为空字符串，load_dotenv(override=False) 不会覆盖。
        # 这里补齐“未设置或为空”的变量，确保确实能从文档读取到值。
        values = dotenv_values(env_path)
        for raw_key, value in values.items():
            if not raw_key or value is None:
                continue
            key = str(raw_key).strip().lstrip("\ufeff")
            if not key:
                continue
            current = os.environ.get(key)
            if current is None or not current.strip():
                os.environ[key] = str(value).strip()
    except Exception:
        # 若缺少依赖或解析失败，不阻塞启动；后续会通过 /api/health 暴露 has_api_key 状态
        return


_try_load_dotenv()


DEFAULT_MODELS_FALLBACK_ZHIPUAI: list[str] = [
    # 文本
    "glm-4-plus",
    "glm-4-air-250414",
    "glm-4-airx",
    "glm-4-long",
    "glm-4-flashx",
    "glm-4-flash-250414",
    # 视觉
    "glm-4v-plus-0111",
    "glm-4v",
    "glm-4v-flash",
]


DEFAULT_MODELS_FALLBACK_OPENAI_COMPAT: list[str] = [
    # 常见 OpenAI/中转站模型命名（并非穷举；仅用于无法拉取 /models 时的兜底）
    "gemini-3-flash",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gpt-4o",
    "gpt-4o-mini",
]


def _get_env(name: str, default: str = "") -> str:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip()


def _get_bool_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    v = raw.strip().lower()
    if v in {"1", "true", "yes", "y", "on"}:
        return True
    if v in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _get_base_url() -> str:
    # 官方 SDK 默认 base_url 为 https://open.bigmodel.cn/api/paas/v4/
    return _get_env("ZHIPUAI_BASE_URL", "https://open.bigmodel.cn/api/paas/v4").rstrip("/")


def _get_api_key() -> str:
    # 官方 SDK 也支持 ZHIPUAI_API_KEY
    return _get_env("ZHIPUAI_API_KEY", "")


def _get_ai_provider() -> str:
    # 可选：用于未来切换到其他厂商或 OpenAI 兼容服务
    # - zhipuai_sdk: 使用 zhipuai 官方 SDK（默认）
    # - openai_compat: 走 OpenAI 风格 HTTP /chat/completions
    return _get_env("AI_PROVIDER", "zhipuai_sdk").lower()


def _get_ai_base_url_fallback() -> str:
    # 若未提供 AI_BASE_URL，则回退到智谱 base_url
    return _get_env("AI_BASE_URL", _get_base_url()).rstrip("/")


def _get_ai_api_key_fallback() -> str:
    # 若未提供 AI_API_KEY，则回退到智谱 api key
    return _get_env("AI_API_KEY", _get_api_key())


def _ai_debug_enabled() -> bool:
    return _get_bool_env("AI_DEBUG", False)


def _require_sdk() -> None:
    if ZhipuAI is None:
        raise HTTPException(
            status_code=500,
            detail=f"后端缺少依赖 zhipuai，无法调用智谱接口：{_ZHIPUAI_IMPORT_ERROR}",
        )


def _create_client() -> Any:
    _require_sdk()
    api_key = _get_api_key()
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="未设置环境变量 ZHIPUAI_API_KEY（后端不会从前端接收厂商 key）",
        )

    base_url = _get_base_url()
    return ZhipuAI(api_key=api_key, base_url=base_url)  # type: ignore[misc]


def _join_url(base_url: str, path: str) -> str:
    base = (base_url or "").rstrip("/")
    p = (path or "").lstrip("/")
    if not base:
        return "/" + p
    return f"{base}/{p}"


def _extract_text_from_chat_completion(resp: Any) -> str | None:
    """Best-effort extract assistant text from various SDK/HTTP response shapes."""

    def _from_message_content(content: Any) -> str | None:
        if isinstance(content, str):
            return content
        # 一些实现会返回 list[{type,text}, ...]
        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    if item.strip():
                        parts.append(item)
                    continue
                if isinstance(item, dict):
                    t = item.get("text")
                    if isinstance(t, str) and t.strip():
                        parts.append(t.strip())
                    continue
                text_attr = getattr(item, "text", None)
                if isinstance(text_attr, str) and text_attr.strip():
                    parts.append(text_attr.strip())
            joined = "\n".join([p for p in parts if p])
            return joined if joined.strip() else None
        return None

    # dict 风格（HTTP JSON）
    if isinstance(resp, dict):
        try:
            choices = resp.get("choices")
            if isinstance(choices, list) and choices:
                msg = choices[0].get("message") if isinstance(choices[0], dict) else None
                if isinstance(msg, dict):
                    return _from_message_content(msg.get("content"))
        except Exception:
            return None

    # 对象风格（SDK）
    try:
        choices = getattr(resp, "choices", None)
        if isinstance(choices, list) and choices:
            msg = getattr(choices[0], "message", None)
            content = getattr(msg, "content", None) if msg is not None else None
            return _from_message_content(content)
    except Exception:
        return None

    return None


def _debug_dump_response(resp: Any) -> None:
    if not _ai_debug_enabled():
        return
    try:
        print("[AI_DEBUG] resp_type=", type(resp))
        # 尽量避免输出超大内容
        if isinstance(resp, dict):
            preview = json.dumps(resp, ensure_ascii=False)[:2000]
            print("[AI_DEBUG] resp_preview(dict)=", preview)
            return
        # SDK 对象：尝试 dict 化
        dump = None
        for attr in ("model_dump", "dict"):
            fn = getattr(resp, attr, None)
            if callable(fn):
                try:
                    dump = fn()
                    break
                except Exception:
                    dump = None
        if isinstance(dump, dict):
            preview = json.dumps(dump, ensure_ascii=False)[:2000]
            print("[AI_DEBUG] resp_preview(obj->dict)=", preview)
            return
        print("[AI_DEBUG] resp_str_preview=", str(resp)[:2000])
    except Exception:
        return


class ModelsResponse(BaseModel):
    base_url: str
    models: list[str]
    source: str = Field(description="remote|fallback")


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "base_url": _get_base_url(),
        "has_api_key": bool(_get_api_key()),
        "has_zhipuai_sdk": ZhipuAI is not None,
        "ai_provider": _get_ai_provider(),
    }


@app.get("/api/models", response_model=ModelsResponse)
def list_models() -> ModelsResponse:
    # 说明：智谱公开文档未明确给出稳定的“列模型”HTTP接口。
    # 因此这里采用“尽力远端拉取 + 失败回退”的策略：
    # - 若 base_url 下存在 OpenAI 风格 /models，则返回其数据
    # - 否则回退到内置的常用模型列表（含视觉模型）

    provider = _get_ai_provider()
    base_url = _get_ai_base_url_fallback().rstrip("/") if provider == "openai_compat" else _get_base_url().rstrip("/")
    api_key = _get_ai_api_key_fallback() if provider == "openai_compat" else _get_api_key()

    fallback_models = (
        DEFAULT_MODELS_FALLBACK_OPENAI_COMPAT if provider == "openai_compat" else DEFAULT_MODELS_FALLBACK_ZHIPUAI
    )

    if not api_key:
        return ModelsResponse(base_url=base_url, models=fallback_models, source="fallback")

    # 尝试走 OpenAI 风格 /models（不同中转站可能是 /models 或 /v1/models）
    try:
        import httpx

        headers = {"Authorization": f"Bearer {api_key}"}
        candidate_urls = [
            _join_url(base_url, "models"),
            _join_url(base_url, "v1/models"),
        ]
        data = None
        last_err: Exception | None = None
        for url in candidate_urls:
            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.get(url, headers=headers)
                if resp.status_code >= 400:
                    raise RuntimeError(f"GET {url} -> {resp.status_code}: {resp.text[:200]}")
                data = resp.json()
                break
            except Exception as exc:  # noqa: BLE001
                last_err = exc
                continue

        if data is None and last_err is not None:
            raise last_err

        models: list[str] = []
        if isinstance(data, dict) and isinstance(data.get("data"), list):
            for item in data["data"]:
                if isinstance(item, dict):
                    mid = item.get("id")
                    if isinstance(mid, str) and mid.strip():
                        models.append(mid.strip())

        if models:
            return ModelsResponse(base_url=base_url, models=sorted(set(models)), source="remote")

    except Exception:
        pass

    return ModelsResponse(base_url=base_url, models=fallback_models, source="fallback")


class AnalyzeImageRequest(BaseModel):
    model: str = Field(min_length=1)
    prompt: str = Field(min_length=1)
    image_base64: str = Field(min_length=1, description="纯 base64，不含 data:image/... 前缀")
    image_mime: str = Field(default="image/png")


class AnalyzeImageResponse(BaseModel):
    text: str
    model: str


@app.post("/api/analyze-image", response_model=AnalyzeImageResponse)
def analyze_image(req: AnalyzeImageRequest) -> AnalyzeImageResponse:
    provider = _get_ai_provider()
    # GLM-4V-Flash 不支持 base64（文档说明），因此仅在智谱 SDK 路径下拦截
    if provider != "openai_compat" and req.model.strip() == "glm-4v-flash":
        raise HTTPException(status_code=400, detail="glm-4v-flash 不支持 base64 图片输入，请改用 glm-4v 或 glm-4v-plus-0111")

    model = req.model.strip()
    prompt = req.prompt.strip()
    b64 = req.image_base64.strip()

    def _is_param_error(message: str) -> bool:
        m = (message or "").lower()
        # 常见：Error code: 400, with error text {"error":{"code":"1210"...}}
        return ("error code" in m and "400" in m and "1210" in m) or ("1210" in m and "参数" in message)

    # 更通用：优先 data URL（大量 OpenAI 兼容/多模态实现使用该格式）
    # 仍保留“纯 base64”的回退尝试，以兼容不同服务端解析方式。
    data_url = f"data:{req.image_mime};base64,{b64}"
    candidate_urls: list[str] = [data_url, b64]

    try:
        resp: Any | None = None
        last_exc: Exception | None = None

        if provider == "openai_compat":
            import httpx

            api_key = _get_ai_api_key_fallback()
            if not api_key:
                raise HTTPException(status_code=500, detail="未设置 AI_API_KEY（或 ZHIPUAI_API_KEY），无法调用 openai_compat")

            base_url = _get_ai_base_url_fallback()
            # 常见两种：base_url 已含 /v1 或不含
            candidate_endpoints = [
                _join_url(base_url, "chat/completions"),
                _join_url(base_url, "v1/chat/completions"),
            ]

            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            # 逐个尝试 endpoint 与图片 url 格式
            for endpoint in candidate_endpoints:
                for img_url in candidate_urls:
                    payload = {
                        "model": model,
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "image_url", "image_url": {"url": img_url}},
                                    {"type": "text", "text": prompt},
                                ],
                            }
                        ],
                    }
                    try:
                        with httpx.Client(timeout=120.0) as client:
                            r = client.post(endpoint, headers=headers, json=payload)
                        if r.status_code >= 400:
                            raise RuntimeError(f"POST {endpoint} -> {r.status_code}: {r.text[:500]}")
                        resp = r.json()
                        break
                    except Exception as exc:  # noqa: BLE001
                        last_exc = exc
                        # 若是参数错误，继续尝试其他组合
                        if _is_param_error(str(exc)):
                            continue
                        # 其他错误也继续尝试下一个 endpoint（提高通用性）
                        continue
                if resp is not None:
                    break
        else:
            # 默认：智谱官方 SDK
            client = _create_client()
            for img_url in candidate_urls:
                messages: list[dict[str, Any]] = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image_url", "image_url": {"url": img_url}},
                            {"type": "text", "text": prompt},
                        ],
                    }
                ]
                try:
                    resp = client.chat.completions.create(model=model, messages=messages)
                    break
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    if _is_param_error(str(exc)):
                        continue
                    raise

        if resp is None and last_exc is not None:
            raise last_exc

        _debug_dump_response(resp)

        text = _extract_text_from_chat_completion(resp)
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("模型未返回可用文本")

        return AnalyzeImageResponse(text=text.strip(), model=model)

    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=502, detail=f"智谱调用失败：{exc}") from exc
