# -*- coding: utf-8 -*-
"""Streamlit app for multi-file FTIR comparison and waterfall plotting."""

from __future__ import annotations

import json
import os

import streamlit as st

from modules.peaks import extract_top_peaks
from modules.plotter import build_code_template, render_waterfall_png_bytes
from modules.reader import read_spectrum
from modules.vision_agent import analyze_image, fetch_models

st.set_page_config(page_title="AutoFTIR-Vision", layout="wide", page_icon="🧪")
st.title("🧪 AutoFTIR-Vision: 多文件对比与瀑布图")
st.markdown("上传您的 FTIR 数据，自动生成可编辑的 Matplotlib 绘图脚本。")


PROMPT_PRESETS: dict[str, str] = {
    "通用（简要结论）": """
你是一名材料/固体化学方向研究人员。请根据该 FTIR 图谱图片给出简要分析，输出为纯文本。

要求：
1) 描述吸收峰（或透过率谷）分布与相对强度的总体特征（是否存在明显主峰、多组分迹象）。
2) 结合典型波数区间，推测可能的官能团/键振动（避免过度推断，给出置信度）。
3) 给出 2–3 条可操作的后续建议（例如：基线校正、峰拟合、与标准谱库对比）。
""".strip(),
    "峰识别（列出主峰）": """
请从该 FTIR 图谱图片中识别主要吸收峰（或透过率谷），输出为纯文本。

输出格式：
- 主峰列表：按强度从高到低列出（尽量估计波数位置 cm⁻¹，给出相对强度等级：强/中/弱）。
- 备注：说明是否存在峰重叠、基线漂移、噪声或异常尖峰等。

注意：只根据图片可见信息，无法精确读数时请说明“估计”。
""".strip(),
    "官能团判定建议（不做硬判定）": """
请根据该 FTIR 图谱图片给出“官能团/物质类别判定建议”，输出为纯文本。

要求：
1) 不要直接断言具体化合物名称；请以“可能/需要对比”表述。
2) 提供建议的检索策略：例如与谱库对比、关注特征波数区间、排除水/CO₂干扰峰。
3) 若图谱疑似多组分或存在杂峰，请指出依据（峰位/峰形/基线）。
""".strip(),
    "峰形分析（定性）": """
请对该 FTIR 图谱图片的峰形进行定性分析，输出为纯文本。

关注点：
- 峰宽是否明显变宽（可能对应氢键增强/无序度增大/多组分叠加等）。
- 峰形是否对称/是否存在肩峰（可能对应峰重叠或多种化学环境）。
- 是否需要做基线校正与峰拟合（如 Gaussian/Lorentzian/Voigt）。

注意：只给出定性判断与建议，避免给出过度精确的数值结论。
""".strip(),
}


uploaded_files = st.file_uploader(
    "上传数据文件（支持 .txt/.csv/.jdx/.spc；自动读取前两列，跳过非数字行；.txt 为空格分隔，.csv 可为逗号/分号/Tab 分隔）",
    type=["txt", "csv", "jdx", "spc"],
    accept_multiple_files=True,
)


with st.sidebar:
    st.header("⚙️ 绘图参数")
    default_line_color = st.color_picker("默认线条颜色", "#1f77b4")
    line_width = st.slider("线条宽度", 0.5, 4.0, 1.5, 0.1)
    fig_style = st.selectbox("图表风格", ["default", "classic", "bmh", "seaborn-v0_8-white"])
    offset_percent = st.slider("Y轴堆叠偏移百分比 (%)", 0, 100, 10, 1)

    st.subheader("坐标轴设置")
    xlabel = st.text_input("X轴标签", r"Wavenumber (cm$^{-1}$)")
    ylabel = st.text_input("Y轴标签", "Intensity (a.u.)")
    hide_top_right = st.checkbox("去除右/上边框 (Nature风格)", value=True)
    x_min = st.number_input("X轴最小值 (可选)", value=None, step=1.0, format="%f")
    x_max = st.number_input("X轴最大值 (可选)", value=None, step=1.0, format="%f")

    st.subheader("图例命名（多文件）")
    custom_legend_names: list[str] = []
    custom_colors: list[str] = []
    if uploaded_files:
        palette = [
            "#1f77b4",
            "#ff7f0e",
            "#2ca02c",
            "#d62728",
            "#9467bd",
            "#8c564b",
            "#e377c2",
            "#7f7f7f",
            "#bcbd22",
            "#17becf",
        ]
        for idx, f in enumerate(uploaded_files):
            col_name, col_color = st.columns([4, 1])
            with col_name:
                custom_legend_names.append(
                    st.text_input(
                        f"文件 {idx + 1}: {f.name}",
                        value=f.name,
                        key=f"legend_name::{idx}::{f.name}",
                    )
                )
            with col_color:
                custom_colors.append(
                    st.color_picker(
                        "颜色",
                        value=palette[idx % len(palette)],
                        key=f"legend_color::{idx}::{f.name}",
                        label_visibility="collapsed",
                    )
                )
    else:
        st.caption("上传文件后，将在此处显示每条曲线的图例名称输入框。")

    st.subheader("AI 分析（后端）")
    enable_ai_analysis = st.checkbox("生成脚本时启用图片分析", value=False)

    backend_url = st.text_input(
        "后端地址（Backend URL）",
        value=os.environ.get("FTIR_BACKEND_URL", "http://localhost:8000"),
        help="前端与生成的脚本都会调用该后端；后端再去调用模型（API Key 在后端环境变量中）。",
    ).rstrip("/")

    refresh_models = st.button("🔄 刷新模型列表", use_container_width=True)
    if refresh_models or "backend_models" not in st.session_state:
        models, source = fetch_models(backend_url)
        st.session_state["backend_models"] = models
        st.session_state["backend_models_source"] = source

    backend_models: list[str] = st.session_state.get("backend_models", [])
    backend_models_source: str = st.session_state.get("backend_models_source", "")
    if backend_models_source:
        st.caption(f"模型列表来源：{backend_models_source}")

    default_model = None
    for candidate in ("gemini-3-flash", "glm-4v-plus-0111", "glm-4v"):
        if candidate in backend_models:
            default_model = candidate
            break

    ai_model = st.selectbox(
        "选择模型（Model）",
        options=backend_models or ["gemini-3-flash", "glm-4v-plus-0111", "glm-4v"],
        index=(backend_models.index(default_model) if default_model and backend_models else 0),
        help="模型列表由后端从已配置的 Provider/Base URL/API Key 尝试获取；若获取失败会使用回退列表。",
    )

    def _apply_prompt_preset() -> None:
        preset_name = st.session_state.get("ai_prompt_preset")
        if preset_name in PROMPT_PRESETS:
            st.session_state["ai_prompt"] = PROMPT_PRESETS[preset_name]

    st.selectbox(
        "预置提示词",
        options=list(PROMPT_PRESETS.keys()),
        index=0,
        key="ai_prompt_preset",
        on_change=_apply_prompt_preset,
    )
    if "ai_prompt" not in st.session_state:
        st.session_state["ai_prompt"] = PROMPT_PRESETS["通用（简要结论）"]
    ai_prompt = st.text_area(
        "分析提示词（Prompt）",
        key="ai_prompt",
        help="会一并提交给 API，用于指导模型输出。",
    )


if uploaded_files:
    try:
        spectra = [read_spectrum(f.getvalue(), source_name=f.name) for f in uploaded_files]
        legend_names = (
            custom_legend_names if len(custom_legend_names) == len(uploaded_files) else [f.name for f in uploaded_files]
        )
        colors = (
            custom_colors
            if len(custom_colors) == len(uploaded_files)
            else [default_line_color for _ in uploaded_files]
        )

        spans: list[float] = []
        for s in spectra:
            try:
                y_max = float(s.y.max())
                y_min = float(s.y.min())
                span = y_max - y_min
                if span > 0:
                    spans.append(span)
            except Exception:
                continue

        spans_sorted = sorted(spans)
        if spans_sorted:
            mid = len(spans_sorted) // 2
            reference_span = spans_sorted[mid] if (len(spans_sorted) % 2 == 1) else (spans_sorted[mid - 1] + spans_sorted[mid]) / 2.0
        else:
            reference_span = 0.0

        offset_value = reference_span * (float(offset_percent) / 100.0)
        st.sidebar.caption(f"自动偏移量（基于中位跨度）：{offset_value:.6g}  （参考跨度={reference_span:.6g}）")

        col1, col2 = st.columns([1, 2])
        with col1:
            st.write("### 📊 数据预览")
            for idx, (f, spec) in enumerate(zip(uploaded_files, spectra)):
                with st.expander(f"文件 {idx + 1}: {f.name}", expanded=(idx == 0)):
                    st.dataframe(spec.df.head(8), height=220, use_container_width=True)

            datasets = [(s.x, s.y, name, c) for s, name, c in zip(spectra, legend_names, colors)]
            png_bytes = render_waterfall_png_bytes(
                datasets,
                style=fig_style,
                color=default_line_color,
                linewidth=line_width,
                x_label=xlabel,
                y_label=ylabel,
                x_min=x_min,
                x_max=x_max,
                hide_top_right=hide_top_right,
                offset=offset_value,
            )

            stem = uploaded_files[0].name.rsplit(".", 1)[0]
            analysis_key = "analysis::" + "|".join([f.name for f in uploaded_files]) + f"::offset_percent={offset_percent}"
            last_text: str = st.session_state.get(analysis_key, "")

            header_left, header_right = st.columns([5, 1])
            with header_left:
                st.subheader("🖼️ 图片预览")
            with header_right:
                st.download_button(
                    "⬇️ 下载",
                    data=png_bytes,
                    file_name=f"{stem}_waterfall.png",
                    mime="image/png",
                    type="primary",
                    use_container_width=True,
                )
            st.image(png_bytes, caption="Waterfall Plot", use_container_width=True)

            st.divider()

            header_left, header_right = st.columns([5, 1])
            with header_left:
                st.subheader("🧠 结果分析")
            with header_right:
                st.download_button(
                    "⬇️ 下载",
                    data=(last_text or ""),
                    file_name=f"{stem}_analysis.txt",
                    mime="text/plain; charset=utf-8",
                    type="primary",
                    disabled=(not isinstance(last_text, str) or not last_text.strip()),
                    use_container_width=True,
                )

            do_analyze = st.button("分析", type="primary", use_container_width=True)
            if do_analyze:
                try:
                    with st.spinner("正在分析，请稍候..."):
                        peak_payload: list[dict] = []
                        for name, s in zip(legend_names, spectra):
                            peaks = extract_top_peaks(s.x, s.y, top_n=5, mode="auto")
                            peak_payload.append(
                                {
                                    "name": name,
                                    "peaks": [
                                        {
                                            "kind": p.kind,
                                            "center": round(p.center),
                                            "range": [round(p.left), round(p.right)],
                                        }
                                        for p in peaks
                                    ],
                                }
                            )

                        peak_hint = (
                            "以下为从原始数据自动提取的前五个最强峰（含半高宽近似范围），"
                            "x 单位通常为 cm-1，请以实际坐标轴为准。\n"
                            + json.dumps(peak_payload, ensure_ascii=False)
                        )

                        final_prompt = (ai_prompt or "").strip()
                        if peak_payload:
                            final_prompt = (final_prompt + "\n\n" + peak_hint).strip()

                        text = analyze_image(
                            backend=backend_url,
                            model=ai_model,
                            prompt=final_prompt,
                            png_bytes=png_bytes,
                        )

                    st.session_state[analysis_key] = text
                    last_text = text
                except Exception as exc:  # noqa: BLE001
                    st.error(f"分析失败：{exc}")

            st.text_area(
                "文本分析结果",
                value=last_text,
                height=260,
                help="该结果会被写入生成脚本（作为预先计算的分析文本）。",
            )

        with col2:
            analysis_key = "analysis::" + "|".join([f.name for f in uploaded_files]) + f"::offset_percent={offset_percent}"
            analysis_text = st.session_state.get(analysis_key, "")

            code_template = build_code_template(
                file_names=[f.name for f in uploaded_files],
                legend_names=legend_names,
                colors=colors,
                default_color=default_line_color,
                offset_percent=offset_percent,
                linewidth=line_width,
                style=fig_style,
                x_label=xlabel,
                y_label=ylabel,
                drop_spines=hide_top_right,
                x_min_value=x_min,
                x_max_value=x_max,
                enable_ai=enable_ai_analysis,
                backend_url=backend_url,
                ai_model=ai_model,
                ai_prompt=ai_prompt,
                analysis_text=analysis_text,
            )

            with st.expander("🐍 生成的 Python 代码（默认折叠）", expanded=False):
                st.code(code_template, language="python")
                st.download_button(
                    label="⬇️ 下载 .py 脚本文件",
                    data=code_template,
                    file_name=f"plot_waterfall_{uploaded_files[0].name.rsplit('.', 1)[0]}.py",
                    mime="text/x-python",
                    type="primary",
                )

            if enable_ai_analysis and not backend_url:
                st.warning("你已开启 AI 分析，但后端地址为空：生成脚本将不会调用分析接口。")

            st.caption("💡 下载脚本后，请将其与数据文件放在同一文件夹下运行。")

    except Exception as exc:  # noqa: BLE001
        st.error(f"处理错误: {exc}")
else:
    st.info("请上传一个或多个包含两列波数（cm⁻¹）与强度的 FTIR 数据文件开始体验。")
