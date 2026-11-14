"""Gaja's public pure scientific interfaces for Pirathee's later API integration."""

from app.statistics.annual_aggregation import (
    QualityPolicy,
    aggregate_annual_precipitation,
)
from app.statistics.audit import (
    AnnualSumSpotCheck,
    MonthlySpotCheck,
    RegionScientificAudit,
    audit_regional_trend,
    verify_annual_sum,
    verify_monthly_conversion,
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
    "AnnualSumSpotCheck",
    "InsufficientDataError",
    "InvalidDataError",
    "MonthlyObservation",
    "MonthlySpotCheck",
    "NumericalAnalysisError",
    "QualityPolicy",
    "RegionScientificAudit",
    "TrendResult",
    "aggregate_annual_precipitation",
    "analyze_annual_trend",
    "audit_regional_trend",
    "verify_annual_sum",
    "verify_monthly_conversion",
]
