from __future__ import annotations

import base64
import io
import os

import httpx


def _make_png_base64() -> str:
    """Generate a small but valid PNG similar to the Streamlit preview."""

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(4, 3), dpi=150)
    ax.plot([10, 20, 30, 40], [1.0, 2.2, 1.6, 2.8])
    ax.set_xlabel("2θ")
    ax.set_ylabel("Intensity")
    ax.set_title("Smoke Test")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def main() -> None:
    b64 = _make_png_base64()
    model = os.environ.get("AI_TEST_MODEL", "gemini-3-flash").strip() or "gemini-3-flash"
    payload = {
        "model": model,
        "prompt": "请简要描述这张图，并给出你看到的主要元素。",
        "image_mime": "image/png",
        "image_base64": b64,
    }

    url = "http://127.0.0.1:8001/api/analyze-image"
    r = httpx.post(url, json=payload, timeout=120.0)
    print("status", r.status_code)
    print(r.text[:2000])


if __name__ == "__main__":
    main()
