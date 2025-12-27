from __future__ import annotations

import json
import urllib.error
import urllib.request
from base64 import b64encode


def fetch_models(api_base: str) -> tuple[list[str], str]:
    if not api_base:
        return ([], "")
    url = f"{api_base}/api/models"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
        with urllib.request.urlopen(req, timeout=10) as resp:
            payload = resp.read().decode("utf-8", errors="replace")
        data = json.loads(payload)
        models = data.get("models") if isinstance(data, dict) else None
        source = data.get("source") if isinstance(data, dict) else ""
        if isinstance(models, list):
            out = [m for m in models if isinstance(m, str) and m.strip()]
            return (out, str(source or ""))
    except Exception:
        return ([], "")
    return ([], "")


def analyze_image(
    *,
    backend: str,
    model: str,
    prompt: str,
    png_bytes: bytes,
) -> str:
    if not backend:
        raise RuntimeError("后端地址为空：请在侧边栏填写后端地址")

    api = backend.rstrip("/") + "/api/analyze-image"
    payload = {
        "model": model,
        "prompt": prompt,
        "image_mime": "image/png",
        "image_base64": b64encode(png_bytes).decode("ascii"),
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Accept": "application/json, text/plain, */*",
    }

    req = urllib.request.Request(api, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace") if hasattr(exc, "read") else str(exc)
        raise RuntimeError("后端 HTTP 错误: %s %s\n%s" % (exc.code, exc.reason, raw)) from exc
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("后端调用失败: %s" % (exc,)) from exc

    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            text = data.get("text")
            if isinstance(text, str):
                return text.strip()
    except Exception:
        pass

    return raw.strip()
