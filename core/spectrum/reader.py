# -*- coding: utf-8 -*-
"""
光谱数据读取模块

支持多种文件格式，提供统一的数据结构输出。
完全解耦，不依赖任何 Web 框架。
"""
from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Union

import pandas as pd


@dataclass
class SpectrumData:
    """光谱数据结构"""
    df: pd.DataFrame
    x: pd.Series
    y: pd.Series
    source_name: str


def _decode_text(raw: bytes) -> str:
    """尝试多种编码解码文本"""
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _finalize_two_column_df(df: pd.DataFrame, *, source_name: str) -> SpectrumData:
    """标准化两列数据框"""
    if df.shape[1] < 2:
        raise RuntimeError(f"Expected at least 2 columns: {source_name}")

    df = df.iloc[:, :2].copy()
    df.columns = ["2Theta", "Intensity"]

    df["2Theta"] = pd.to_numeric(df["2Theta"], errors="coerce")
    df["Intensity"] = pd.to_numeric(df["Intensity"], errors="coerce")
    df = df.dropna(subset=["2Theta", "Intensity"]).reset_index(drop=True)

    if df.empty:
        raise RuntimeError(f"No valid numeric rows found: {source_name}")

    return SpectrumData(df=df, x=df["2Theta"], y=df["Intensity"], source_name=source_name)


def read_two_column_txt(raw: bytes, *, source_name: str) -> SpectrumData:
    """读取空格分隔的 TXT 文件"""
    buffer = io.BytesIO(raw)
    df = pd.read_csv(buffer, sep=r"\s+", engine="python", header=None, usecols=[0, 1])
    return _finalize_two_column_df(df, source_name=source_name)


def read_two_column_csv(raw: bytes, *, source_name: str) -> SpectrumData:
    """读取 CSV 文件（自动检测分隔符）"""
    text = _decode_text(raw)
    buffer = io.StringIO(text)
    df = pd.read_csv(
        buffer,
        sep=None,
        engine="python",
        header=None,
        usecols=[0, 1],
    )
    return _finalize_two_column_df(df, source_name=source_name)


def read_jdx(_: bytes, *, source_name: str) -> SpectrumData:
    """读取 JDX 格式（待实现）"""
    raise RuntimeError(f"Unsupported file format (jdx): {source_name}")


def read_spc(_: bytes, *, source_name: str) -> SpectrumData:
    """读取 SPC 格式（待实现）"""
    raise RuntimeError(f"Unsupported file format (spc): {source_name}")


def read_spectrum(raw: bytes, *, source_name: str) -> SpectrumData:
    """
    读取光谱数据文件
    
    Args:
        raw: 文件字节内容
        source_name: 源文件名（用于确定格式）
        
    Returns:
        SpectrumData: 标准化的光谱数据
        
    Raises:
        RuntimeError: 不支持的文件格式或读取失败
    """
    suffix = Path(source_name).suffix.lower()
    if suffix == ".txt":
        return read_two_column_txt(raw, source_name=source_name)
    if suffix == ".csv":
        return read_two_column_csv(raw, source_name=source_name)
    if suffix == ".jdx":
        return read_jdx(raw, source_name=source_name)
    if suffix == ".spc":
        return read_spc(raw, source_name=source_name)
    raise RuntimeError(f"Unsupported file format: {source_name}")


def read_spectrum_from_path(path: Union[str, Path]) -> SpectrumData:
    """
    从文件路径读取光谱数据
    
    Args:
        path: 文件路径
        
    Returns:
        SpectrumData: 标准化的光谱数据
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return read_spectrum(path.read_bytes(), source_name=path.name)
