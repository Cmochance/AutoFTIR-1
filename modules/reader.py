from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path

import pandas as pd


@dataclass
class SpectrumData:
    df: pd.DataFrame
    x: pd.Series
    y: pd.Series
    source_name: str


def _decode_text(raw: bytes) -> str:
    for encoding in ("utf-8-sig", "utf-8", "gb18030", "gbk"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


def _finalize_two_column_df(df: pd.DataFrame, *, source_name: str) -> SpectrumData:
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
    buffer = io.BytesIO(raw)
    df = pd.read_csv(buffer, sep=r"\s+", engine="python", header=None, usecols=[0, 1])
    return _finalize_two_column_df(df, source_name=source_name)


def read_two_column_csv(raw: bytes, *, source_name: str) -> SpectrumData:
    text = _decode_text(raw)
    buffer = io.StringIO(text)
    df = pd.read_csv(
        buffer,
        sep=None,  # auto-detect common delimiters (comma/semicolon/tab, etc.)
        engine="python",
        header=None,
        usecols=[0, 1],
    )
    return _finalize_two_column_df(df, source_name=source_name)


def read_jdx(_: bytes, *, source_name: str) -> SpectrumData:
    raise RuntimeError(f"Unsupported file format (jdx): {source_name}")


def read_spc(_: bytes, *, source_name: str) -> SpectrumData:
    raise RuntimeError(f"Unsupported file format (spc): {source_name}")


def read_spectrum(raw: bytes, *, source_name: str) -> SpectrumData:
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
