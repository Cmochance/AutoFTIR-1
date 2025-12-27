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


AI_ENABLED = False
BACKEND_URL = os.environ.get("FTIR_BACKEND_URL") or 'http://localhost:8000'
AI_MODEL = os.environ.get("FTIR_AI_MODEL") or 'gemini-3-flash'
AI_PROMPT = '你是一名材料/固体化学方向研究人员。请根据该 FTIR 图谱图片给出简要分析，输出为纯文本。\n\n要求：\n1) 描述峰位分布与相对强度的总体特征（是否存在明显主峰、多相迹象）。\n2) 说明可能的结晶度/背景噪声情况（仅基于图像趋势，避免过度推断）。\n3) 给出 2–3 条可操作的后续建议（例如：对比标准卡/做峰拟合/校准零点）。'
PRECOMPUTED_ANALYSIS_TEXT = '作为一名材料化学研究人员，针对您提供的 FTIR 图谱，简要分析如下：\n\n**1. 峰位分布与相对强度特征**\n该图谱在 10°–80° (2θ) 范围内呈现出多个明显的衍射峰。\n*   **主峰分布：** 存在三个显著的强衍射峰，分别位于约 17.8°、24.2° 和 29.8° 附近。其中 17.8° 和 29.8° 处的峰强度最高，构成该物相的主要特征。\n*   **多相迹象：** 在 20°–30° 区间内峰形较为密集且存在肩峰（如 25° 附近），结合高角度区（40° 以上）分布的多个中弱强度尖锐峰，表明该样品可能含有多个物相，或者属于对称性较低的晶系（如单斜或三斜晶系）。\n\n**2. 结晶度与背景噪声情况**\n*   **结晶度：** 衍射峰整体较为尖锐，半高宽（FWHM）较小，说明样品具有较好的长程有序性，结晶度较高。\n*   **背景与噪声：** \n    *   在低角度区（10°–30°）观察到明显的隆起背景（鼓包），这通常暗示样品中存在少量无定形组分，或者是由于测试基底/制样厚度引起的背景散射。\n    *   信噪比尚可，但高角度区的基线波动略显粗糙，若需进行精修，可能需要增加采样时间以平滑曲线。\n\n**3. 后续操作建议**\n*   **物相检索（Phase ID）：** 优先将 17.8°、24.2° 和 29.8° 这几个强峰输入 PDF 数据库进行检索。重点关注可能存在的氧化物、氢氧化物或复杂的有机-无机杂化材料。\n*   **基线扣除与峰拟合：** 建议使用软件（如 Jade 或 Origin）进行基线扣除，并对 20°–30° 之间的重叠峰进行高斯/洛伦兹拟合，以确定确切的峰位和个数，从而判断是否存在杂相。\n*   **内标校准：** 观察到低角度起始端背景略高，建议检查是否存在零点偏移（Zero offset）。若需精确计算晶格常数，可添加硅粉（Si）作为内标进行二次扫描校准。'


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


def main() -> None:
    # 1. 设置全局风格
    plt.style.use('default')
    plt.rcParams['font.family'] = 'Arial'  # 科研常用字体
    plt.rcParams['font.size'] = 12

    # 2. 读取数据（.txt：两列数字，多个空格/空白分隔，无表头）
    data_path = BASE_DIR / '测试-1.txt'
    if not data_path.exists():
        print(f"未找到数据文件：{data_path}")
        print("")
        raise SystemExit(1)

    df = pd.read_csv(data_path, sep=r"\s+", engine="python", header=None, usecols=[0, 1])
    x = df.iloc[:, 0]
    y = df.iloc[:, 1]

    # 3. 创建画布
    fig, ax = plt.subplots(figsize=(6, 4.5), dpi=300)

    # 4. 绘图
    ax.plot(x, y, color='#1f77b4', linewidth=1.5, label='测试-1.txt')

    # 5. 细节调整
    ax.set_xlabel('2$\\theta$ (degree)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Intensity (a.u.)', fontsize=14, fontweight='bold')
    ax.tick_params(direction='in', length=6, width=1)
    # 去除上方和右方边框
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_linewidth(1.2)
    ax.spines['bottom'].set_linewidth(1.2)


    plt.legend(frameon=False)
    plt.tight_layout()

    # 6. 保存
    output_path = BASE_DIR / ('测试-1' + "_plot.png")
    plt.savefig(output_path)
    print(f"图片已保存为: {output_path}")

    # 7. 结果分析
    # - 若前端已执行“分析”，则把预先计算的文本直接写入 *_analysis.txt
    # - 否则在运行脚本时（可选）再调用后端执行分析
    analysis_path = output_path.with_name(output_path.stem + "_analysis.txt")
    if isinstance(PRECOMPUTED_ANALYSIS_TEXT, str) and PRECOMPUTED_ANALYSIS_TEXT.strip():
        analysis_path.write_text(PRECOMPUTED_ANALYSIS_TEXT.strip(), encoding="utf-8")
        print("分析结果已保存为: %s" % (analysis_path,))
    elif AI_ENABLED and BACKEND_URL:
        try:
            analysis_text = _call_backend_ai(image_path=output_path, prompt=AI_PROMPT)
            analysis_path.write_text(analysis_text, encoding="utf-8")
            print("分析结果已保存为: %s" % (analysis_path,))
        except Exception as exc:  # noqa: BLE001
            print("AI 分析失败（不影响出图）：%s" % (exc,))

    # 不弹出窗口，保证生成后直接退出


if __name__ == '__main__':
    try:
        main()
    except SystemExit:
        raise
    except Exception:  # noqa: BLE001
        print('运行出错：')
        traceback.print_exc()
