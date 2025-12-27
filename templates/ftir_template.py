from __future__ import annotations

import base64
import json
import os
import traceback
import urllib.error
import urllib.request
from pathlib import Path


def _bootstrap_runtime() -> Path:
    base_dir = Path(__file__).resolve().parent
    # 临时环境变量：仅对当前运行进程有效
    os.environ["FTIR_PICTURE_BASE_DIR"] = str(base_dir)
    # 保证双击/任意目录启动时，读写都在脚本同目录
    os.chdir(base_dir)
    return base_dir


def _require_dependencies() -> None:
    missing = []
    try:
        import pandas  # noqa: F401
    except Exception:
        missing.append("pandas")
    try:
        import matplotlib  # noqa: F401
    except Exception:
        missing.append("matplotlib")

    if missing:
        print("缺少依赖，无法运行。请先安装：")
        print("  " + " ".join(missing))
        print("")
        print("建议在项目目录执行：")
        print("  pip install -r requirements.txt")
        print("")
        raise SystemExit(1)


BASE_DIR = _bootstrap_runtime()
_require_dependencies()


import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402


AI_ENABLED = {{ enable_ai_literal }}
BACKEND_URL = os.environ.get("FTIR_BACKEND_URL") or {{ backend_url_literal }}
AI_MODEL = os.environ.get("FTIR_AI_MODEL") or {{ model_literal }}
AI_PROMPT = {{ prompt_literal }}
PRECOMPUTED_ANALYSIS_TEXT = {{ analysis_text_literal }}

FILE_NAMES = {{ file_names_literal }}
LEGEND_NAMES = {{ legend_names_literal }}
COLORS = {{ colors_literal }}
DEFAULT_COLOR = {{ default_color_literal }}
OFFSET_PERCENT = {{ offset_percent_literal }}


def _median(values: list[float]) -> float:
    if not values:
        return 0.0
    arr = sorted(values)
    mid = len(arr) // 2
    if len(arr) % 2 == 1:
        return float(arr[mid])
    return (float(arr[mid - 1]) + float(arr[mid])) / 2.0


def _compute_offset_value(loaded: list[tuple[str, pd.Series, pd.Series]]) -> float:
    spans: list[float] = []
    for _, _, y in loaded:
        try:
            span = float(y.max()) - float(y.min())
            if span > 0:
                spans.append(span)
        except Exception:
            continue
    reference_span = _median(spans)
    return reference_span * (float(OFFSET_PERCENT) / 100.0)


def _extract_text_from_response(raw_text: str) -> str:
    try:
        data = json.loads(raw_text)
    except Exception:
        return raw_text.strip()

    if isinstance(data, str):
        return data.strip()

    if isinstance(data, dict):
        for key in ("result", "analysis", "text", "content", "message"):
            value = data.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

        choices = data.get("choices")
        if isinstance(choices, list) and choices:
            first = choices[0]
            if isinstance(first, dict):
                message = first.get("message")
                if isinstance(message, dict):
                    content = message.get("content")
                    if isinstance(content, str) and content.strip():
                        return content.strip()
                text = first.get("text")
                if isinstance(text, str) and text.strip():
                    return text.strip()

    return raw_text.strip()


def _call_backend_ai(*, image_path: Path, prompt: str) -> str:
    if not BACKEND_URL:
        raise RuntimeError("BACKEND_URL 为空：请设置环境变量 FTIR_BACKEND_URL 或在生成脚本时填入后端地址")

    api = BACKEND_URL.rstrip("/") + "/api/analyze-image"
    payload = {
        "model": AI_MODEL,
        "prompt": prompt,
        "image_mime": "image/png",
        "image_base64": base64.b64encode(image_path.read_bytes()).decode("ascii"),
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
        raise RuntimeError("AI API HTTP 错误: %s %s\n%s" % (exc.code, exc.reason, raw)) from exc
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("AI API 调用失败: %s" % (exc,)) from exc

    return _extract_text_from_response(raw)


def _extract_top_peak_ranges(x: pd.Series, y: pd.Series, *, top_n: int = 5) -> list[dict]:
    """Extract top peaks (auto max/min) and return approximate half-prominence ranges."""

    xs = pd.to_numeric(x, errors="coerce").astype(float)
    ys = pd.to_numeric(y, errors="coerce").astype(float)
    df = pd.DataFrame({"x": xs, "y": ys}).dropna()
    if len(df) < 3:
        return []

    def _smooth(series: pd.Series, window: int = 7) -> pd.Series:
        w = int(window)
        if w <= 1:
            return series
        if w % 2 == 0:
            w += 1
        return series.rolling(window=w, center=True, min_periods=1).mean()

    def _local_maxima_indices(s: pd.Series) -> list[int]:
        if len(s) < 3:
            return []
        arr = s.to_numpy()
        out: list[int] = []
        for i in range(1, len(arr) - 1):
            if arr[i] >= arr[i - 1] and arr[i] >= arr[i + 1] and (arr[i] > arr[i - 1] or arr[i] > arr[i + 1]):
                out.append(i)
        return out

    def _nearest_local_min_left(arr, i: int) -> int:
        j = i - 1
        while j > 0:
            if arr[j] <= arr[j - 1] and arr[j] <= arr[j + 1]:
                return j
            j -= 1
        return 0

    def _nearest_local_min_right(arr, i: int) -> int:
        j = i + 1
        n = len(arr)
        while j < n - 1:
            if arr[j] <= arr[j - 1] and arr[j] <= arr[j + 1]:
                return j
            j += 1
        return n - 1

    def _interp_x_at_level(xa, sa, i0: int, i1: int, level: float) -> float:
        x0, x1 = float(xa[i0]), float(xa[i1])
        y0, y1 = float(sa[i0]), float(sa[i1])
        if y0 == y1:
            return x0
        t = (level - y0) / (y1 - y0)
        return x0 + t * (x1 - x0)

    def _extract(kind: str, signal: pd.Series) -> list[dict]:
        s = _smooth(signal, window=7)
        arr = s.to_numpy()
        peak_is = _local_maxima_indices(s)
        if not peak_is:
            return []

        span = float(arr.max() - arr.min()) if len(arr) else 0.0
        min_prom = span * 0.01 if span > 0 else 0.0

        candidates: list[tuple[float, dict]] = []
        xa = df["x"].to_numpy()
        for peak_i in peak_is:
            lmin = _nearest_local_min_left(arr, peak_i)
            rmin = _nearest_local_min_right(arr, peak_i)
            baseline = float(max(arr[lmin], arr[rmin]))
            prom = float(arr[peak_i] - baseline)
            if prom <= 0 or prom < min_prom:
                continue

            level = baseline + 0.5 * prom
            li = peak_i
            while li > lmin and arr[li] > level:
                li -= 1
            left_x = float(xa[peak_i]) if li == peak_i else _interp_x_at_level(xa, arr, li, li + 1, level)

            ri = peak_i
            while ri < rmin and arr[ri] > level:
                ri += 1
            right_x = float(xa[peak_i]) if ri == peak_i else _interp_x_at_level(xa, arr, ri - 1, ri, level)

            lo = float(min(left_x, right_x))
            hi = float(max(left_x, right_x))
            candidates.append((prom, {"kind": kind, "center": float(xa[peak_i]), "range": [lo, hi], "prominence": prom}))

        candidates.sort(key=lambda t: t[0], reverse=True)
        return [d for _, d in candidates[: max(0, int(top_n))]]

    peaks_max = _extract("max", df["y"])
    peaks_min = _extract("min", -df["y"])
    score_max = sum(float(p.get("prominence", 0.0)) for p in peaks_max)
    score_min = sum(float(p.get("prominence", 0.0)) for p in peaks_min)
    peaks = peaks_min if score_min > score_max else peaks_max

    return [
        {
            "kind": d.get("kind"),
            "center": round(float(d.get("center", 0.0))),
            "range": [round(float(d["range"][0])), round(float(d["range"][1]))],
        }
        for d in peaks
        if isinstance(d, dict) and isinstance(d.get("range"), list) and len(d["range"]) == 2
    ]


def _append_peak_hint(prompt: str, peak_payload: list[dict]) -> str:
    p = (prompt or "").strip()
    if not peak_payload:
        return p
    hint = (
        "以下为从原始数据自动提取的前五个最强峰（含半高宽近似范围），x 单位通常为 cm-1，请以实际坐标轴为准。\n"
        + json.dumps(peak_payload, ensure_ascii=False)
    )
    return (p + "\n\n" + hint).strip()


def _read_two_column_data(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path, sep=None, engine="python", header=None, usecols=[0, 1])
    else:
        df = pd.read_csv(path, sep=r"\s+", engine="python", header=None, usecols=[0, 1])
    df.columns = ["x", "y"]
    df["x"] = pd.to_numeric(df["x"], errors="coerce")
    df["y"] = pd.to_numeric(df["y"], errors="coerce")
    df = df.dropna(subset=["x", "y"]).reset_index(drop=True)
    if df.empty:
        raise RuntimeError(f"未读取到有效数据（请确认前两列为数字）：{path}")
    return df


def main() -> None:
    # 1. 设置全局风格
    plt.style.use({{ style_literal }})
    plt.rcParams["font.family"] = "Arial"  # 科研常用字体
    plt.rcParams["font.size"] = 12

    if not isinstance(FILE_NAMES, list) or not FILE_NAMES:
        raise RuntimeError("FILE_NAMES 为空：请在生成脚本时传入要绘制的文件列表")

    # 2. 读取数据（前两列为 x/y；跳过表头等非数字行）
    loaded: list[tuple[str, pd.Series, pd.Series]] = []
    peak_payload: list[dict] = []

    for i, file_name in enumerate(FILE_NAMES):
        data_path = BASE_DIR / str(file_name)
        if not data_path.exists():
            raise RuntimeError(f"未找到数据文件：{data_path}")

        df = _read_two_column_data(data_path)
        x = df["x"]
        y = df["y"]

        label = str(file_name)
        if isinstance(LEGEND_NAMES, list) and i < len(LEGEND_NAMES) and str(LEGEND_NAMES[i]).strip():
            label = str(LEGEND_NAMES[i]).strip()

        loaded.append((label, x, y))
        peak_payload.append({"name": label, "peaks": _extract_top_peak_ranges(x, y, top_n=5)})

    # 3. 创建画布
    fig, ax = plt.subplots(figsize=(6, 4.5), dpi=300)

    offset_value = _compute_offset_value(loaded)

    # 4. 绘图（瀑布图：Y_plot = Y_original + i * OFFSET）
    for i, (label, x, y) in enumerate(loaded):
        y_plot = y + (i * float(offset_value))
        line_color = DEFAULT_COLOR
        if isinstance(COLORS, list) and i < len(COLORS) and str(COLORS[i]).strip():
            line_color = str(COLORS[i]).strip()
        ax.plot(x, y_plot, color=line_color, linewidth={{ linewidth }}, label=label)

    # 5. 细节调整
    ax.set_xlabel({{ x_label_literal }}, fontsize=14, fontweight="bold")
    ax.set_ylabel({{ y_label_literal }}, fontsize=14, fontweight="bold")
    ax.tick_params(direction="in", length=6, width=1)
{{ optional_xlim_block }}{{ optional_spines_block }}

    if loaded:
        plt.legend(frameon=False)
    plt.tight_layout()

    # 6. 保存
    output_path = BASE_DIR / ({{ file_stem_literal }} + "_waterfall.png")
    plt.savefig(output_path)
    print(f"图片已保存为: {output_path}")

    # 7. 结果分析
    analysis_path = output_path.with_name(output_path.stem + "_analysis.txt")
    if isinstance(PRECOMPUTED_ANALYSIS_TEXT, str) and PRECOMPUTED_ANALYSIS_TEXT.strip():
        analysis_path.write_text(PRECOMPUTED_ANALYSIS_TEXT.strip(), encoding="utf-8")
        print("分析结果已保存为: %s" % (analysis_path,))
    elif AI_ENABLED and BACKEND_URL:
        try:
            final_prompt = _append_peak_hint(AI_PROMPT, peak_payload)
            analysis_text = _call_backend_ai(image_path=output_path, prompt=final_prompt)
            analysis_path.write_text(analysis_text, encoding="utf-8")
            print("分析结果已保存为: %s" % (analysis_path,))
        except Exception as exc:  # noqa: BLE001
            print("AI 分析失败（不影响出图）：%s" % (exc,))


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001
        print("运行出错：")
        traceback.print_exc()
