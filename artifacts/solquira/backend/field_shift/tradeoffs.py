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


# Human-readable interpretation is localized at the scientific source rather
# than guessing translations of generated sentences in the browser.
EVIDENCE_ES = {
    "continue": "Secuencia ilustrativa de referencia; no implica una recomendación agronómica para este terreno.",
    "legume": "Comparación por categorías; deben validarse especies, inoculación y acceso a mercados locales.",
    "cover": "Los cultivos de cobertura protegen la superficie, pero pueden consumir humedad escasa durante su establecimiento.",
    "forage": "Las forrajeras pueden estabilizar el suelo; deben evaluarse manejo del pastoreo y cercos.",
}


def compare_pathways(context: dict, field_input: FieldShiftInput) -> list[PathwayResult]:
    dry_fraction = context["dry_day_fraction"]
    heavy_days = context["mean_heavy_rain_days"]

    # Descriptive 0–100 indices, NOT probabilities of drought or waterlogging.
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
        observations_es: list[str] = []
        if dry_fraction >= 0.55 and plan["water_dependence"] >= 3:
            observations.append(
                f"Elevated dry-day frequency ({round(dry_fraction*100, 1)}% of seasonal days <1mm); "
                "verify supplemental irrigation or drought-tolerant cultivar before planting."
            )
            observations_es.append(
                f"Frecuencia elevada de días secos ({round(dry_fraction*100, 1)} % con menos de 1 mm); "
                "verificar disponibilidad de agua y adaptación del cultivo antes de sembrar."
            )
        elif dry_fraction < 0.40:
            observations.append("Relatively frequent precipitation events recorded across the historical window.")
            observations_es.append("Las estimaciones históricas muestran una frecuencia relativamente alta de días con precipitación.")

        if rain_event_signal >= 0.25 and plan["wet_access"] >= 3:
            observations.append(
                f"Multi-season average of {heavy_days:.1f} heavy rain days (>=20mm); "
                "evaluate machinery trafficability, soil compaction and field access."
            )
            observations_es.append(
                f"Promedio estacional de {heavy_days:.1f} días con lluvia de al menos 20 mm; "
                "revisar tránsito de maquinaria, compactación y acceso al terreno."
            )

        if field_input.drainage == "restricted":
            observations.append("Restricted drainage assumed for a demonstration; not a local measurement or regional average. Assess potential root saturation." if field_input.drainage_origin == "illustrative_demo" else "Restricted soil drainage is user-reported; assess risk of prolonged root saturation.")
            observations_es.append("Drenaje limitado supuesto para una demostración; no es una medición ni un promedio regional. Revisar posible saturación radicular." if field_input.drainage_origin == "illustrative_demo" else "El drenaje limitado fue declarado por la persona usuaria; verificar posibles periodos de saturación radicular.")
        elif field_input.drainage == "unknown":
            observations.append("Drainage condition is unknown; wet-season soil trafficability cannot be determined.")
            observations_es.append("El drenaje es desconocido; no puede estimarse el tránsito sobre el suelo durante periodos húmedos.")

        if field_input.soil == "clayey":
            observations.append("Illustrative assumption: clayey texture may slow infiltration and delay fieldwork after rain; not measured on-site." if field_input.soil_origin == "illustrative_demo" else "Clayey texture self-reported: slow water infiltration and workability delays after rain.")
            observations_es.append("Supuesto ilustrativo: una textura arcillosa podría dificultar la infiltración; no se midió en el terreno." if field_input.soil_origin == "illustrative_demo" else "Textura arcillosa declarada: podría dificultar la infiltración y retrasar labores después de lluvias.")
        elif field_input.soil == "sandy":
            observations.append("Illustrative assumption: sandy texture may drain rapidly and retain less plant-available water; not measured on-site." if field_input.soil_origin == "illustrative_demo" else "Sandy texture self-reported: rapid drainage and low plant-available water holding capacity.")
            observations_es.append("Supuesto ilustrativo: una textura arenosa podría drenar rápido y retener menos agua; no se midió en el terreno." if field_input.soil_origin == "illustrative_demo" else "Textura arenosa declarada: puede favorecer el drenaje rápido y reducir la retención de agua disponible.")
        elif field_input.soil == "loamy":
            observations.append("Illustrative assumption: loamy texture may balance retention; field texture and profile depth have not been measured." if field_input.soil_origin == "illustrative_demo" else "Loamy texture self-reported: balanced retention, but local profile depth remains unmeasured.")
            observations_es.append("Supuesto ilustrativo: una textura franca podría equilibrar la retención; no se ha medido el perfil del terreno." if field_input.soil_origin == "illustrative_demo" else "Textura franca declarada: retención potencialmente equilibrada; profundidad del perfil aún sin medir.")

        if field_input.previous_crop == "cereal" and plan["sequence"][0] == "Cereal":
            observations.append("Initial rotation step repeats a cereal crop: inspect disease carryover and weed pressure.")
            observations_es.append("La rotación vuelve a comenzar con cereal: revisar continuidad de patógenos y presión de malezas.")

        if not observations:
            observations.append("No hard exclusion detected; site-specific agronomic suitability remains unassessed.")
            observations_es.append("No se identificó una exclusión categórica; la aptitud agronómica local sigue sin evaluarse.")

        # Missing drainage cannot be replaced with an arbitrary middle score.
        # In particular, wet exposure=0 is a real zero, not a missing value.
        primary = (
            dry_exposure if field_input.concern == "dry"
            else wet_exposure if field_input.concern == "wet"
            else (round((dry_exposure + wet_exposure) / 2) if wet_exposure is not None else None)
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
                observations_es=observations_es,
                limitation=plan["evidence"],
                limitation_es=EVIDENCE_ES[plan["id"]],
                agronomic_viability="not_assessed",
            )
        )

    if field_input.priority == "water":
        results.sort(key=lambda item: (item.dry_exposure_indicator, item.id))
    elif field_input.priority == "soil":
        results.sort(key=lambda item: (-item.ground_cover_level, item.id))
    elif field_input.priority == "diversity":
        results.sort(key=lambda item: (-item.rotation_diversity_level, item.id))
    return results
