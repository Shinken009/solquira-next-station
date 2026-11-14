"""Deterministic tradeoff explorer for agricultural rotations.

Translates observed multi-season NASA POWER signals and user-reported
field conditions into comparative indicators without simulating agronomic certainty.
"""
from __future__ import annotations
from .schema import FieldShiftInput, PathwayResult


PATHWAYS = [
    {
        "id": "continue",
        "name": "Continue baseline pattern",
        "sequence": ["Cereal", "Cereal", "Cereal"],
        "water_dependence": 3,
        "wet_access": 2,
        "ground_cover": 1,
        "diversity": 1,
        "evidence": "Illustrative baseline sequence; does not imply site-specific agronomic prescription.",
    },
    {
        "id": "legume",
        "name": "Diversify with legumes",
        "sequence": ["Cereal", "Legume", "Cover"],
        "water_dependence": 2,
        "wet_access": 2,
        "ground_cover": 2,
        "diversity": 3,
        "evidence": "Category comparison; local inoculation, species selection and market access require validation.",
    },
    {
        "id": "cover",
        "name": "Prioritize continuous soil cover",
        "sequence": ["Cover", "Cereal", "Legume"],
        "water_dependence": 3,
        "wet_access": 3,
        "ground_cover": 3,
        "diversity": 3,
        "evidence": "Cover crops reduce surface erosion but may transpire scarce moisture during dry establishment.",
    },
    {
        "id": "forage",
        "name": "Integrate forage pasture",
        "sequence": ["Forage", "Legume", "Forage"],
        "water_dependence": 2,
        "wet_access": 2,
        "ground_cover": 3,
        "diversity": 2,
        "evidence": "Perennial or annual forage provides soil stability; grazing management and fencing must be assessed.",
    },
]


def compare_pathways(context: dict, field_input: FieldShiftInput) -> list[PathwayResult]:
    dry_fraction = context["dry_day_fraction"]
    heavy_days = context["mean_heavy_rain_days"]

    # Descriptive signals, not crop physiological models
    rain_event_signal = min(1.0, heavy_days / 12.0)
    drainage_multipliers = {
        "well_drained": 0.65,
        "restricted": 1.25,
        "unknown": None,
    }
    drainage_mult = drainage_multipliers.get(field_input.drainage)

    results: list[PathwayResult] = []

    for plan in PATHWAYS:
        dry_exposure = round(100 * dry_fraction * plan["water_dependence"] / 3)
        wet_exposure = None
        if drainage_mult is not None:
            wet_exposure = round(min(100, 100 * rain_event_signal * plan["wet_access"] / 3 * drainage_mult))

        observations: list[str] = []

        # Hydroclimatic signal observations
        if dry_fraction >= 0.55 and plan["water_dependence"] >= 3:
            observations.append(
                f"Elevated dry-day frequency ({round(dry_fraction*100, 1)}% of seasonal days <1mm); "
                "verify supplemental irrigation or drought-tolerant cultivar before planting."
            )
        elif dry_fraction < 0.40:
            observations.append("Relatively frequent precipitation events recorded across the historical window.")

        if rain_event_signal >= 0.25 and plan["wet_access"] >= 3:
            observations.append(
                f"Multi-season average of {heavy_days:.1f} heavy rain days (>=20mm); "
                "evaluate machinery trafficability, soil compaction and field access."
            )

        # Field reported constraints
        if field_input.drainage == "restricted":
            observations.append("Restricted soil drainage is user-reported; assess risk of prolonged root saturation.")
        elif field_input.drainage == "unknown":
            observations.append("Drainage condition is unknown; wet-season soil trafficability cannot be determined.")

        if field_input.soil == "clayey":
            observations.append("Clayey texture self-reported: slow water infiltration and workability delays after rain.")
        elif field_input.soil == "sandy":
            observations.append("Sandy texture self-reported: rapid drainage and low plant-available water holding capacity.")
        elif field_input.soil == "loamy":
            observations.append("Loamy texture self-reported: balanced retention, but local profile depth remains unmeasured.")

        if field_input.previous_crop == "cereal" and plan["sequence"][0] == "Cereal":
            observations.append("Initial rotation step repeats a cereal crop: inspect disease carryover and weed pressure.")

        if not observations:
            observations.append("No hard exclusion detected; site-specific agronomic suitability remains unassessed.")

        primary = (
            dry_exposure if field_input.concern == "dry"
            else wet_exposure if field_input.concern == "wet"
            else round((dry_exposure + (wet_exposure or 50)) / 2)
        )

        results.append(
            PathwayResult(
                id=plan["id"],
                name=plan["name"],
                sequence=list(plan["sequence"]),
                dry_exposure_indicator=dry_exposure,
                wet_exposure_indicator=wet_exposure,
                primary_indicator=primary,
                ground_cover_level=plan["ground_cover"],
                rotation_diversity_level=plan["diversity"],
                observations=observations,
                limitation=plan["evidence"],
                agronomic_viability="not_assessed",
            )
        )

    # Sort based on farmer priorities (never an objective crop ranking)
    if field_input.priority == "water":
        results.sort(key=lambda item: (item.dry_exposure_indicator, item.id))
    elif field_input.priority == "soil":
        results.sort(key=lambda item: (-item.ground_cover_level, item.id))
    elif field_input.priority == "diversity":
        results.sort(key=lambda item: (-item.rotation_diversity_level, item.id))

    return results
