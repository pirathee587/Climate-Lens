"""Synthetic MK references: hand calculation and pinned independent PyMannKendall."""

import math

import pymannkendall
import pytest

from app.statistics import AnnualObservation, InvalidDataError
from app.statistics.mann_kendall import mann_kendall


def rows(values):
    return [AnnualObservation(2000 + i, v) for i, v in enumerate(values)]


def test_hand_calculated_tie_variance_continuity_and_normal_tail():
    result = mann_kendall(rows([1, 2, 2, 3]))
    assert result.score == 5
    assert result.variance == pytest.approx(23 / 3)
    z = 4 / math.sqrt(23 / 3)
    assert result.z == pytest.approx(z)
    assert result.p_value == pytest.approx(math.erfc(z / math.sqrt(2)))
    assert result.tied_groups == 1


@pytest.mark.parametrize(
    "values",
    [
        list(range(1, 25)),
        list(range(25, 1, -1)),
        [7] * 15,
        [1, 2, 2, 3, 2, 4, 4, 4, 5, 6, 6, 8],
        [9, 3, 7, 2, 8, 4, 10, 5, 1, 6, 11, 3],
    ],
)
def test_pymannkendall_independent_reference(values):
    expected = pymannkendall.original_test(values, alpha=0.05)
    actual = mann_kendall(rows(values))
    assert actual.score == pytest.approx(expected.s)
    assert actual.variance == pytest.approx(expected.var_s)
    assert actual.z == pytest.approx(expected.z)
    assert actual.p_value == pytest.approx(expected.p, abs=2e-15)
    assert actual.reject_null == bool(expected.h)
    assert actual.method_version


@pytest.mark.parametrize("alpha", [0, 1, -1, float("nan"), float("inf"), True, "0.05"])
def test_invalid_alpha(alpha):
    with pytest.raises(InvalidDataError):
        mann_kendall(rows(range(1, 15)), alpha)


def test_constant_series_does_not_reject():
    result = mann_kendall(rows([100] * 24))
    assert (result.score, result.variance, result.z, result.p_value) == (0, 0, 0, 1)
    assert not result.reject_null
