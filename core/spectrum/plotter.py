# -*- coding: utf-8 -*-
"""
光谱绘图模块

提供多种绘图功能和代码模板生成。
完全解耦，不依赖任何 Web 框架。
"""
from __future__ import annotations

import io
from functools import lru_cache
from pathlib import Path
from textwrap import dedent, indent
from typing import List, Tuple, Optional

import matplotlib.pyplot as plt


def create_plot_figure(
    x,
    y,
    *,
    style: str,
    color: str,
    linewidth: float,
    x_label: str,
    y_label: str,
    x_min: Optional[float],
    x_max: Optional[float],
    hide_top_right: bool,
    dpi: int = 300,
    figsize: Tuple[float, float] = (6, 4.5),
):
    """创建单曲线图"""
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    plt.style.use(style)
    ax.plot(x, y, color=color, linewidth=linewidth)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    if x_min is not None or x_max is not None:
        ax.set_xlim(x_min, x_max)
    if hide_top_right:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_linewidth(1.2)
        ax.spines["bottom"].set_linewidth(1.2)
    return fig, ax


def create_waterfall_figure(
    datasets: List[Tuple],
    *,
    style: str,
    color: str,
    linewidth: float,
    x_label: str,
    y_label: str,
    x_min: Optional[float],
    x_max: Optional[float],
    hide_top_right: bool,
    offset: float,
    dpi: int = 300,
    figsize: Tuple[float, float] = (6, 4.5),
):
    """创建瀑布图"""
    fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
    plt.style.use(style)
    for i, item in enumerate(datasets):
        if isinstance(item, tuple) and len(item) == 4:
            x, y, label, line_color = item
        else:
            x, y, label = item
            line_color = color
        y_plot = y + (i * float(offset))
        ax.plot(x, y_plot, color=str(line_color), linewidth=linewidth, label=str(label))
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    if x_min is not None or x_max is not None:
        ax.set_xlim(x_min, x_max)
    if hide_top_right:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.spines["left"].set_linewidth(1.2)
        ax.spines["bottom"].set_linewidth(1.2)
    return fig, ax


def render_plot_png_bytes(
    x,
    y,
    *,
    style: str,
    color: str,
    linewidth: float,
    x_label: str,
    y_label: str,
    x_min: Optional[float],
    x_max: Optional[float],
    hide_top_right: bool,
) -> bytes:
    """渲染单曲线图为 PNG 字节"""
    fig, _ = create_plot_figure(
        x,
        y,
        style=style,
        color=color,
        linewidth=linewidth,
        x_label=x_label,
        y_label=y_label,
        x_min=x_min,
        x_max=x_max,
        hide_top_right=hide_top_right,
    )
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def render_waterfall_png_bytes(
    datasets: List[Tuple],
    *,
    style: str,
    color: str,
    linewidth: float,
    x_label: str,
    y_label: str,
    x_min: Optional[float],
    x_max: Optional[float],
    hide_top_right: bool,
    offset: float,
) -> bytes:
    """渲染瀑布图为 PNG 字节"""
    fig, ax = create_waterfall_figure(
        datasets,
        style=style,
        color=color,
        linewidth=linewidth,
        x_label=x_label,
        y_label=y_label,
        x_min=x_min,
        x_max=x_max,
        hide_top_right=hide_top_right,
        offset=offset,
    )
    if datasets:
        ax.legend(frameon=False)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def build_code_template(
    *,
    file_names: List[str],
    legend_names: List[str],
    colors: List[str],
    default_color: str,
    offset_percent: int,
    linewidth: float,
    style: str,
    x_label: str,
    y_label: str,
    drop_spines: bool,
    x_min_value: Optional[float],
    x_max_value: Optional[float],
    enable_ai: bool,
    backend_url: str,
    ai_model: str,
    ai_prompt: str,
    analysis_text: Optional[str],
) -> str:
    """
    生成可独立运行的 Python 绘图脚本
    
    Args:
        file_names: 数据文件名列表
        legend_names: 图例名称列表
        colors: 颜色列表
        default_color: 默认颜色
        offset_percent: Y 轴偏移百分比
        linewidth: 线宽
        style: 绘图风格
        x_label: X 轴标签
        y_label: Y 轴标签
        drop_spines: 是否去除边框
        x_min_value: X 轴最小值
        x_max_value: X 轴最大值
        enable_ai: 是否启用 AI 分析
        backend_url: 后端地址
        ai_model: AI 模型
        ai_prompt: AI 提示词
        analysis_text: 预计算的分析文本
        
    Returns:
        str: Python 脚本内容
    """
    optional_xlim_block = ""
    if x_min_value is not None or x_max_value is not None:
        optional_xlim_block = f"    ax.set_xlim({x_min_value}, {x_max_value})\n"

    optional_spines_block = ""
    if drop_spines:
        spines = dedent(
            """
            # Remove top/right spines for a cleaner look
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_linewidth(1.2)
            ax.spines['bottom'].set_linewidth(1.2)
            """
        ).strip("\n")
        optional_spines_block = indent(spines, "    ") + "\n"

    @lru_cache(maxsize=1)
    def _get_plot_script_template():
        try:
            from jinja2 import Environment, FileSystemLoader, StrictUndefined
        except Exception as exc:
            raise RuntimeError("Missing dependency: jinja2. Run `pip install -r requirements.txt`.") from exc

        templates_dir = Path(__file__).resolve().parents[2] / "templates"
        env = Environment(
            loader=FileSystemLoader(str(templates_dir)),
            autoescape=False,
            undefined=StrictUndefined,
            keep_trailing_newline=True,
        )
        return env.get_template("ftir_template.py")

    first_name = file_names[0] if file_names else "waterfall"
    file_stem = first_name.rsplit(".", 1)[0]

    analysis_text_literal = "None"
    if isinstance(analysis_text, str) and analysis_text.strip():
        analysis_text_literal = repr(analysis_text.strip())

    context = {
        "enable_ai_literal": "True" if enable_ai else "False",
        "backend_url_literal": repr(backend_url),
        "model_literal": repr(ai_model),
        "prompt_literal": repr(ai_prompt),
        "analysis_text_literal": analysis_text_literal,
        "style_literal": repr(style),
        "default_color_literal": repr(default_color),
        "linewidth": float(linewidth),
        "x_label_literal": repr(x_label),
        "y_label_literal": repr(y_label),
        "file_names_literal": repr(file_names),
        "legend_names_literal": repr(legend_names),
        "colors_literal": repr(colors),
        "offset_percent_literal": int(offset_percent),
        "file_stem_literal": repr(file_stem),
        "optional_xlim_block": optional_xlim_block,
        "optional_spines_block": optional_spines_block,
    }

    return _get_plot_script_template().render(**context)
