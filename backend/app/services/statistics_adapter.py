"""Pirathee's injectable bridge to Gaja's real, unchanged scientific package."""

from __future__ import annotations

import importlib
from collections.abc import Sequence
from types import ModuleType
from typing import TYPE_CHECKING, Protocol

from app.schemas.quality import ReviewedQualityPolicy
from app.schemas.repository import NormalizedMonthlyRecord

if TYPE_CHECKING:
    from app.statistics import AggregationResult, TrendResult


class ScienceInputError(ValueError):
    pass


class ScienceInsufficientData(ValueError):
    pass


class ScienceNumericalError(ValueError):
    pass


class StatisticsUnavailable(RuntimeError):
    pass


class StatisticsAdapter(Protocol):
    def aggregate_monthly(
        self,
        rows: Sequence[NormalizedMonthlyRecord],
        policy: ReviewedQualityPolicy,
        start_year: int,
        end_year: int,
    ) -> AggregationResult: ...

    def analyze(self, aggregation: AggregationResult, alpha: float) -> TrendResult: ...


class GajaStatisticsAdapter:
    def __init__(self, module: ModuleType | None = None) -> None:
        self._module = module

    def _engine(self) -> ModuleType:
        if self._module is None:
            try:
                self._module = importlib.import_module("app.statistics")
            except (ImportError, OSError):
                raise StatisticsUnavailable(
                    "Scientific engine is unavailable."
                ) from None
        return self._module

    def _call(self, function, *args, **kwargs):
        module = self._engine()
        try:
            return function(*args, **kwargs)
        except module.InsufficientDataError:
            raise ScienceInsufficientData(
                "At least 10 complete years are required."
            ) from None
        except module.InvalidDataError:
            raise ScienceInputError("Scientific inputs failed validation.") from None
        except module.NumericalAnalysisError:
            raise ScienceNumericalError("Scientific computation failed.") from None
        except Exception:
            raise ScienceNumericalError("Scientific computation failed.") from None

    def aggregate_monthly(
        self,
        rows: Sequence[NormalizedMonthlyRecord],
        policy: ReviewedQualityPolicy,
        start_year: int,
        end_year: int,
    ) -> AggregationResult:
        module = self._engine()
        accepted = frozenset(policy.accepted_quality_flags)
        monthly = tuple(
            module.MonthlyObservation(
                region_id=row.region_id,
                period=row.period,
                total_mm=row.precipitation_total_mm,
                quality_flag=row.quality_flag,
                valid_fraction=row.valid_fraction,
                validity="missing"
                if row.precipitation_total_mm is None
                else "valid"
                if row.quality_flag in accepted
                else "invalid",
            )
            for row in rows
        )
        return self._call(
            module.aggregate_annual_precipitation,
            monthly,
            policy=module.QualityPolicy(accepted, policy.minimum_valid_fraction),
            year_range=(start_year, end_year),
        )

    def analyze(self, aggregation: AggregationResult, alpha: float) -> TrendResult:
        module = self._engine()
        return self._call(
            module.analyze_annual_trend,
            aggregation.observations,
            alpha=alpha,
            excluded_years=aggregation.excluded_years,
        )


def get_statistics_adapter() -> StatisticsAdapter:
    # No import-time dependency on SciPy: missing science code receives its own 503.
    return GajaStatisticsAdapter()
