"""Gaja's public pure scientific interfaces for Pirathee's later API integration."""

from app.statistics.annual_aggregation import (
    QualityPolicy,
    aggregate_annual_precipitation,
)
from app.statistics.models import (
    AggregationResult,
    AnnualObservation,
    InsufficientDataError,
    InvalidDataError,
    MonthlyObservation,
    NumericalAnalysisError,
    TrendResult,
)
from app.statistics.trend_engine import analyze_annual_trend

__all__ = [
    "AggregationResult",
    "AnnualObservation",
    "InsufficientDataError",
    "InvalidDataError",
    "MonthlyObservation",
    "NumericalAnalysisError",
    "QualityPolicy",
    "TrendResult",
    "aggregate_annual_precipitation",
    "analyze_annual_trend",
]
