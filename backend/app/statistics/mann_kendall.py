"""Original two-sided MK: exact ties, tie-corrected variance, continuity correction."""

import math
from collections import Counter
from collections.abc import Sequence

from scipy.stats import norm

from app.statistics.models import (
    AnnualObservation,
    MannKendallResult,
    checked_alpha,
    prepare_annual,
)

MK_METHOD = "two-sided-original-on-annual-totals"
MK_VERSION = "terratrend-mk-ties-continuity-normal-v1"


def mann_kendall(
    observations: Sequence[AnnualObservation], alpha: float = 0.05
) -> MannKendallResult:
    rows = prepare_annual(observations)
    alpha = checked_alpha(alpha)
    values = tuple(row.total_mm for row in rows)
    n = len(values)
    score = sum(
        (b > a) - (b < a) for i, a in enumerate(values) for b in values[i + 1 :]
    )
    ties = [count for count in Counter(values).values() if count > 1]
    variance = (
        n * (n - 1) * (2 * n + 5) - sum(t * (t - 1) * (2 * t + 5) for t in ties)
    ) / 18
    z = (score - math.copysign(1, score)) / math.sqrt(variance) if score else 0.0
    # SF avoids catastrophic cancellation in tiny two-sided tail probabilities.
    p_value = float(2 * norm.sf(abs(z)))
    return MannKendallResult(
        score,
        variance,
        z,
        p_value,
        alpha,
        bool(variance > 0 and p_value < alpha),
        MK_METHOD,
        MK_VERSION,
        len(ties),
    )
