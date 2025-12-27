from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class Peak:
    x: float
    y: float
    index: int


def find_peaks(
    x: np.ndarray,
    y: np.ndarray,
    *,
    min_prominence: float | None = None,
    min_distance: int = 1,
) -> list[Peak]:
    """Simple local-maximum finder for quick peak hints."""
    if x.size == 0 or y.size == 0 or x.size != y.size:
        return []
    if min_distance < 1:
        min_distance = 1

    peaks: list[Peak] = []
    last_idx = -min_distance
    for i in range(1, len(y) - 1):
        if i - last_idx < min_distance:
            continue
        if y[i] <= y[i - 1] or y[i] <= y[i + 1]:
            continue

        if min_prominence is not None:
            baseline = max(y[i - 1], y[i + 1])
            if (y[i] - baseline) < min_prominence:
                continue

        peaks.append(Peak(x=float(x[i]), y=float(y[i]), index=i))
        last_idx = i

    return peaks
