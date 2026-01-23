# -*- coding: utf-8 -*-
"""
主视图组件

数据预览、图片预览、分析结果、代码生成等。
"""
from __future__ import annotations

import json
from typing import Any, List

import streamlit as st

from frontend.api_client import APIClient
from frontend.components.sidebar import SidebarState
from core.spectrum import extract_top_peaks, render_waterfall_png_bytes, build_code_template


def _compute_reference_span(spectra: List[Any]) -> float:
    """计算参考跨度"""
    spans: List[float] = []
    for spectrum in spectra:
        try:
            y_max = float(spectrum.y.max())
            y_min = float(spectrum.y.min())
            span = y_max - y_min
            if span > 0:
                spans.append(span)
        except Exception:
            continue

    spans_sorted = sorted(spans)
    if not spans_sorted:
        return 0.0

    mid = len(spans_sorted) // 2
    if len(spans_sorted) % 2 == 1:
        return float(spans_sorted[mid])
    return float(spans_sorted[mid - 1] + spans_sorted[mid]) / 2.0


def _analysis_key(*, uploaded_files: List[Any], offset_percent: int) -> str:
    """生成分析缓存键"""
    return "analysis::" + "|".join([f.name for f in uploaded_files]) + f"::offset_percent={offset_percent}"


def render_main_view(
    *,
    uploaded_files: List[Any],
    spectra: List[Any],
    sidebar: SidebarState
) -> None:
    """渲染主视图"""
    legend_names = (
        sidebar.custom_legend_names
        if len(sidebar.custom_legend_names) == len(uploaded_files)
        else [f.name for f in uploaded_files]
    )
    colors = (
        sidebar.custom_colors
        if len(sidebar.custom_colors) == len(uploaded_files)
        else [sidebar.default_line_color for _ in uploaded_files]
    )

    reference_span = _compute_reference_span(spectra)
    offset_value = reference_span * (float(sidebar.offset_percent) / 100.0)
    st.sidebar.caption(f"自动偏移量：{offset_value:.6g}  （参考跨度={reference_span:.6g}）")

    col1, col2 = st.columns([1, 2])

    stem = uploaded_files[0].name.rsplit(".", 1)[0]
    analysis_key = _analysis_key(uploaded_files=uploaded_files, offset_percent=sidebar.offset_percent)

    with col1:
        st.write("### 📊 数据预览")
        for idx, (f, spec) in enumerate(zip(uploaded_files, spectra)):
            with st.expander(f"文件 {idx + 1}: {f.name}", expanded=(idx == 0)):
                st.dataframe(spec.df.head(8), height=220, use_container_width=True)

        datasets = [(s.x, s.y, name, c) for s, name, c in zip(spectra, legend_names, colors)]
        png_bytes = render_waterfall_png_bytes(
            datasets,
            style=sidebar.fig_style,
            color=sidebar.default_line_color,
            linewidth=sidebar.line_width,
            x_label=sidebar.xlabel,
            y_label=sidebar.ylabel,
            x_min=sidebar.x_min,
            x_max=sidebar.x_max,
            hide_top_right=sidebar.hide_top_right,
            offset=offset_value,
        )

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
                    peak_payload: List[dict] = []
                    for name, spectrum in zip(legend_names, spectra):
                        peaks = extract_top_peaks(spectrum.x, spectrum.y, top_n=5, mode="auto")
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

                    final_prompt = (sidebar.ai_prompt or "").strip()
                    if peak_payload:
                        final_prompt = (final_prompt + "\n\n" + peak_hint).strip()

                    client = APIClient(sidebar.backend_url)
                    text = client.analyze_image(
                        model=sidebar.ai_model,
                        prompt=final_prompt,
                        png_bytes=png_bytes,
                    )

                st.session_state[analysis_key] = text
                last_text = text
            except Exception as exc:
                st.error(f"分析失败：{exc}")

        st.text_area(
            "文本分析结果",
            value=last_text,
            height=260,
        )

    with col2:
        analysis_text = st.session_state.get(analysis_key, "")
        code_template = build_code_template(
            file_names=[f.name for f in uploaded_files],
            legend_names=legend_names,
            colors=colors,
            default_color=sidebar.default_line_color,
            offset_percent=sidebar.offset_percent,
            linewidth=sidebar.line_width,
            style=sidebar.fig_style,
            x_label=sidebar.xlabel,
            y_label=sidebar.ylabel,
            drop_spines=sidebar.hide_top_right,
            x_min_value=sidebar.x_min,
            x_max_value=sidebar.x_max,
            enable_ai=sidebar.enable_ai_analysis,
            backend_url=sidebar.backend_url,
            ai_model=sidebar.ai_model,
            ai_prompt=sidebar.ai_prompt,
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

        if sidebar.enable_ai_analysis and not sidebar.backend_url:
            st.warning("你已开启 AI 分析，但后端地址为空")

        st.caption("💡 下载脚本后，请将其与数据文件放在同一文件夹下运行。")
