# -*- coding: utf-8 -*-
"""
侧边栏组件

绘图参数和 AI 配置的侧边栏。
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, List

import streamlit as st

from frontend.api_client import APIClient
from frontend.constants import PROMPT_PRESETS, DEFAULT_PALETTE


@dataclass(frozen=True)
class SidebarState:
    """侧边栏状态"""
    default_line_color: str
    line_width: float
    fig_style: str
    offset_percent: int
    xlabel: str
    ylabel: str
    hide_top_right: bool
    x_min: float | None
    x_max: float | None
    custom_legend_names: List[str]
    custom_colors: List[str]
    enable_ai_analysis: bool
    backend_url: str
    ai_model: str
    ai_prompt: str


def render_sidebar(uploaded_files: List[Any] | None) -> SidebarState:
    """渲染侧边栏"""
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
        custom_legend_names: List[str] = []
        custom_colors: List[str] = []
        
        if uploaded_files:
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
                            value=DEFAULT_PALETTE[idx % len(DEFAULT_PALETTE)],
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
            value=os.environ.get("FTIR_BACKEND_URL", "http://localhost:9000"),
            help="前端与生成的脚本都会调用该后端",
        ).rstrip("/")

        # 获取模型列表
        refresh_models = st.button("🔄 刷新模型列表", use_container_width=True)
        if refresh_models or "backend_models" not in st.session_state:
            try:
                client = APIClient(backend_url)
                models, source = client.fetch_models()
                st.session_state["backend_models"] = models
                st.session_state["backend_models_source"] = source
            except Exception:
                st.session_state["backend_models"] = []
                st.session_state["backend_models_source"] = ""

        backend_models: List[str] = st.session_state.get("backend_models", [])
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
        )

    return SidebarState(
        default_line_color=default_line_color,
        line_width=float(line_width),
        fig_style=str(fig_style),
        offset_percent=int(offset_percent),
        xlabel=str(xlabel),
        ylabel=str(ylabel),
        hide_top_right=bool(hide_top_right),
        x_min=(float(x_min) if x_min is not None else None),
        x_max=(float(x_max) if x_max is not None else None),
        custom_legend_names=custom_legend_names,
        custom_colors=custom_colors,
        enable_ai_analysis=bool(enable_ai_analysis),
        backend_url=str(backend_url),
        ai_model=str(ai_model),
        ai_prompt=str(ai_prompt),
    )
