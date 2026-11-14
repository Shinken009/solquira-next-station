"""Schemas for Field Shift decision support.

Strict input validation and explicit provenance metadata.
"""
from __future__ import annotations
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


DrainageType = Literal["well_drained", "restricted", "unknown"]
SoilTextureType = Literal["clayey", "sandy", "loamy", "unknown"]
SeasonPeriodType = Literal["apr_sep", "oct_mar"]
PriorityType = Literal["water", "soil", "diversity"]
ConcernType = Literal["dry", "wet", "balanced"]


class FieldShiftInput(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    season: SeasonPeriodType = Field("apr_sep", description="Seasonal comparison window: apr_sep or oct_mar")
    drainage: DrainageType = Field("unknown", description="Drainage condition, possibly illustrative")
    soil: SoilTextureType = Field("unknown", description="Soil texture, possibly illustrative")
    drainage_origin: Literal["self_reported", "illustrative_demo"] = "self_reported"
    soil_origin: Literal["self_reported", "illustrative_demo"] = "self_reported"
    previous_crop: Optional[str] = Field(None, description="Previous season crop category")
    priority: Optional[PriorityType] = Field("water", description="Farmer stated exploration priority")
    concern: ConcernType = Field("dry", description="Primary hydroclimatic concern")

    @field_validator("latitude", "longitude")
    @classmethod
    def validate_finite(cls, v: float) -> float:
        import math
        if not math.isfinite(v):
            raise ValueError("Coordinates must be finite numbers")
        return round(v, 4)


class PathwayResult(BaseModel):
    id: str
    name: str
    sequence: list[str]
    dry_exposure_indicator: int
    wet_exposure_indicator: Optional[int] = None
    primary_indicator: Optional[int] = None
    ground_cover_level: int
    rotation_diversity_level: int
    observations: list[str]
    observations_es: list[str] = Field(default_factory=list)
    limitation: str
    limitation_es: str | None = None
    agronomic_viability: Literal["not_assessed"] = "not_assessed"


class SeasonSample(BaseModel):
    season_year: int
    days: int
    precipitation_mm: float
    dry_day_fraction: float
    heavy_rain_days: int
    temperature_mean_c: float


class SeasonalContext(BaseModel):
    label: str
    count: int
    sample_years: list[int]
    mean_rainfall_mm: float
    median_rainfall_mm: float
    dry_day_fraction: float
    mean_heavy_rain_days: float
    mean_temperature_c: float
    sample: list[SeasonSample]
    completeness_rule: str


class SourceProvenance(BaseModel):
    provider: str = "NASA POWER"
    dataset: str = "daily_point_ag"
    endpoint: str = "https://power.larc.nasa.gov/api/temporal/daily/point"
    parameters: list[str] = ["PRECTOTCORR", "T2M"]
    time_standard: str = "UTC"
    requested_latitude: float
    requested_longitude: float
    original_latitude: float
    original_longitude: float
    period_start: str
    period_end: str
    units: dict[str, str] = {"precipitation": "mm/day", "temperature": "C"}
    limitation: str = (
        "Historical gridded NASA estimates; not parcel observations, a seasonal forecast, "
        "a certified drought diagnosis or verified soil moisture."
    )
    source_url: str


class FieldShiftEvaluation(BaseModel):
    version: str = "solquira.field-shift/2.0"
    status: Literal["historical_evidence_available", "insufficient_evidence", "source_unavailable"]
    input: FieldShiftInput
    historical_context: Optional[SeasonalContext] = None
    pathways: list[PathwayResult]
    provenance: SourceProvenance
    quality: dict[str, int]
    assumptions: dict[str, str]
    disclaimers: list[str]
