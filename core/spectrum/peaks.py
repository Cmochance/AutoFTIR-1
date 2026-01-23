# -*- coding: utf-8 -*-
"""
峰识别与分析模块

从光谱数据中提取峰位、峰形等信息。
完全解耦，不依赖任何 Web 框架。
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Literal, List

import numpy as np


@dataclass(frozen=True)
class PeakRange:
    """峰范围数据结构"""
    kind: Literal["max", "min"]
    left: float
    center: float
    right: float
    prominence: float


def _smooth(y: np.ndarray, window: int) -> np.ndarray:
    """简单移动平均平滑"""
    if window <= 1:
        return y
    w = int(window)
    if w % 2 == 0:
        w += 1
    if y.size < w:
        return y
    kernel = np.ones(w, dtype=float) / float(w)
    return np.convolve(y, kernel, mode="same")


def _local_maxima_indices(s: np.ndarray) -> np.ndarray:
    """查找局部最大值索引"""
    if s.size < 3:
        return np.array([], dtype=int)
    left = s[:-2]
    mid = s[1:-1]
    right = s[2:]
    mask = (mid >= left) & (mid >= right) & ((mid > left) | (mid > right))
    return np.nonzero(mask)[0] + 1


def _nearest_local_min_left(s: np.ndarray, i: int) -> int:
    """查找左侧最近的局部最小值"""
    j = i - 1
    while j > 0:
        if s[j] <= s[j - 1] and s[j] <= s[j + 1]:
            return j
        j -= 1
    return 0


def _nearest_local_min_right(s: np.ndarray, i: int) -> int:
    """查找右侧最近的局部最小值"""
    j = i + 1
    n = s.size
    while j < n - 1:
        if s[j] <= s[j - 1] and s[j] <= s[j + 1]:
            return j
        j += 1
    return n - 1


def _interp_x_at_level(x: np.ndarray, s: np.ndarray, i0: int, i1: int, level: float) -> float:
    """在指定水平线处插值 x 坐标"""
    x0, x1 = float(x[i0]), float(x[i1])
    y0, y1 = float(s[i0]), float(s[i1])
    if y0 == y1:
        return x0
    t = (level - y0) / (y1 - y0)
    return x0 + t * (x1 - x0)


def _half_prominence_width(
    *,
    x: np.ndarray,
    s: np.ndarray,
    peak_i: int,
    left_min_i: int,
    right_min_i: int,
    baseline: float,
    prominence: float,
) -> tuple[float, float]:
    """计算半高宽"""
    level = baseline + 0.5 * prominence

    li = peak_i
    while li > left_min_i and s[li] > level:
        li -= 1
    if li == peak_i:
        left_x = float(x[peak_i])
    else:
        left_x = _interp_x_at_level(x, s, li, li + 1, level)

    ri = peak_i
    while ri < right_min_i and s[ri] > level:
        ri += 1
    if ri == peak_i:
        right_x = float(x[peak_i])
    else:
        right_x = _interp_x_at_level(x, s, ri - 1, ri, level)

    return (left_x, right_x)


def _extract_peaks_from_signal(
    *,
    x: np.ndarray,
    s: np.ndarray,
    top_n: int,
    smooth_window: int,
    min_prominence_ratio: float,
    kind: Literal["max", "min"],
) -> List[PeakRange]:
    """从信号中提取峰"""
    ss = _smooth(s, smooth_window)
    peak_indices = _local_maxima_indices(ss)
    if peak_indices.size == 0:
        return []

    candidates: List[tuple[float, PeakRange]] = []
    global_span = float(np.nanmax(ss) - np.nanmin(ss)) if np.isfinite(ss).any() else 0.0
    min_prominence = (global_span * float(min_prominence_ratio)) if global_span > 0 else 0.0

    for peak_i in peak_indices.tolist():
        left_min_i = _nearest_local_min_left(ss, peak_i)
        right_min_i = _nearest_local_min_right(ss, peak_i)
        baseline = float(max(ss[left_min_i], ss[right_min_i]))
        prominence = float(ss[peak_i] - baseline)
        if prominence <= 0 or prominence < min_prominence:
            continue

        left_x, right_x = _half_prominence_width(
            x=x,
            s=ss,
            peak_i=peak_i,
            left_min_i=left_min_i,
            right_min_i=right_min_i,
            baseline=baseline,
            prominence=prominence,
        )
        center = float(x[peak_i])
        lo = float(min(left_x, right_x))
        hi = float(max(left_x, right_x))
        pr = PeakRange(kind=kind, left=lo, center=center, right=hi, prominence=prominence)
        candidates.append((prominence, pr))

    candidates.sort(key=lambda t: t[0], reverse=True)
    return [p for _, p in candidates[: max(0, int(top_n))]]


def extract_top_peaks(
    x,
    y,
    *,
    top_n: int = 5,
    mode: Literal["auto", "max", "min"] = "auto",
    smooth_window: int = 7,
    min_prominence_ratio: float = 0.01,
) -> List[PeakRange]:
    """
    提取前 N 个最强峰及其近似范围
    
    Args:
        x: X 坐标数据（波数/角度等）
        y: Y 坐标数据（强度等）
        top_n: 返回峰的数量
        mode: 
            - "max": 将峰视为 y 的局部最大值
            - "min": 将峰视为 y 的局部最小值（吸收谷）
            - "auto": 根据总显著性自动选择
        smooth_window: 平滑窗口大小
        min_prominence_ratio: 最小显著性比例
        
    Returns:
        List[PeakRange]: 峰列表
    """
    x_arr = np.asarray(x, dtype=float).reshape(-1)
    y_arr = np.asarray(y, dtype=float).reshape(-1)
    if x_arr.size != y_arr.size or x_arr.size < 3:
        return []

    mask = np.isfinite(x_arr) & np.isfinite(y_arr)
    x_arr = x_arr[mask]
    y_arr = y_arr[mask]
    if x_arr.size < 3:
        return []

    if mode == "max":
        return _extract_peaks_from_signal(
            x=x_arr,
            s=y_arr,
            top_n=top_n,
            smooth_window=smooth_window,
            min_prominence_ratio=min_prominence_ratio,
            kind="max",
        )
    if mode == "min":
        return _extract_peaks_from_signal(
            x=x_arr,
            s=-y_arr,
            top_n=top_n,
            smooth_window=smooth_window,
            min_prominence_ratio=min_prominence_ratio,
            kind="min",
        )

    # auto mode
    peaks_max = _extract_peaks_from_signal(
        x=x_arr,
        s=y_arr,
        top_n=top_n,
        smooth_window=smooth_window,
        min_prominence_ratio=min_prominence_ratio,
        kind="max",
    )
    peaks_min = _extract_peaks_from_signal(
        x=x_arr,
        s=-y_arr,
        top_n=top_n,
        smooth_window=smooth_window,
        min_prominence_ratio=min_prominence_ratio,
        kind="min",
    )

    score_max = float(sum(p.prominence for p in peaks_max))
    score_min = float(sum(p.prominence for p in peaks_min))
    return peaks_min if score_min > score_max else peaks_max


def format_peaks_for_prompt(
    peaks: List[PeakRange],
    *,
    x_unit: str = "cm-1",
    round_to: int = 0,
) -> str:
    """
    格式化峰数据为 Prompt 文本
    
    Args:
        peaks: 峰列表
        x_unit: X 轴单位
        round_to: 小数位数
        
    Returns:
        str: 格式化后的文本
    """
    payload = [
        {
            "kind": p.kind,
            "center": round(p.center, round_to),
            "range": [round(p.left, round_to), round(p.right, round_to)],
        }
        for p in peaks
    ]
    return (
        "以下为从原始数据自动提取的前五个最强峰（含半高宽近似范围）。"
        f" x 单位通常为 {x_unit}，请以实际坐标轴为准。\n"
        + json.dumps(payload, ensure_ascii=False)
    )
