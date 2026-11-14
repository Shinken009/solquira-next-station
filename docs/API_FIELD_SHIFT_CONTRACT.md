# Contrato de API propuesto (no implementado) · 2026-11-14

**Aviso:** los siguientes son ejemplos sintéticos de *estructura*, sin observaciones ni números climáticos simulados. La forma final se acuerda contra el esquema `studio_schema.py` y el sistema real de sesión del backend. Todos los POST heredan `GET /solquira-api/studio/bootstrap`, cookie de sesión opaca, `X-Solquira-CSRF`, rate limits, tamaños y CORS/CSP seguros.

## Contexto

`POST /solquira-api/studio/field-shift/context`

```json
{
  "schemaVersion": "solquira.field-shift/1",
  "location": {"latitude": null, "longitude": null, "confirmed": true},
  "seasonWindow": {"calendar": "southern_hemisphere_example", "period": "apr_sep", "startYear": 2021, "endYear": 2025},
  "localEvidence": {"drainage": "unknown", "soilTexture": "unknown", "previousCrop": null, "source": "self_reported"},
  "farmerPriorities": ["water_resilience", "soil_cover"],
  "scenarioOptions": ["continue", "legume", "cover", "forage"]
}
```

`latitude` y `longitude` nulos son placeholders documentales: la validación real de entrada debe exigir latitud -90..90 y longitud -180..180 con punto confirmado; rechazar booleanos, NaN, infinito y coordenadas inválidas. La estación ilustrativa se elige conscientemente; fuera de Chile no se supone el mismo calendario.

## Evaluación

`POST /solquira-api/studio/field-shift/evaluate` debe usar `contextId` seguro ligado a sesión y punto, o un objeto validado, pero no aceptar coordenadas o resultados NASA afirmados por cliente como autoritativos. El resultado tipado:

```json
{
  "schemaVersion": "solquira.field-shift/1",
  "status": "unavailable",
  "sourceStatus": "unavailable",
  "provenance": {
    "provider": "NASA POWER",
    "dataset": "daily_point",
    "parameters": ["PRECTOTCORR", "T2M"],
    "timeStandard": "UTC",
    "retrievedAt": null,
    "requestedPeriod": null,
    "actualCoverage": null,
    "gridResolution": null,
    "sourceUrl": "https://power.larc.nasa.gov/docs/services/api/temporal/daily/",
    "units": {"precipitation": "mm/day", "temperature": "C"}
  },
  "seasonalIndicators": null,
  "pathways": [],
  "missingEvidence": ["NASA source currently unavailable"],
  "agronomicViability": "not_assessed",
  "interpretationStatus": "insufficient_evidence",
  "limitations": ["Historical gridded data, not parcel measurements or seasonal forecast"]
}
```

**No traducir `unavailable` a ceros ni valores predeterminados**, y no calcular pathway sin datos suficientes. Si hay datos válidos, `pathways` contiene objetos tipados con `id`, `conditions`, `benefits`, `tradeoffs`, `missingEvidence`, `evidenceRefs`, `agronomicViability:"not_assessed"`; datos numéricos sólo si obtenidos/computados con respaldo y unidades. Mantener separación entre **observado/modelado por NASA**, **autoinformado**, **supuesto de comparación** y **no disponible**.

## Tabla HTTP y errores

| Caso | Respuesta exigida |
|---|---|
| Sesión ausente/expirada | 401 sin consulta externa |
| CSRF ausente/incorrecto | 403 sin consulta externa |
| Exceso de presupuesto | 429 con backoff |
| Coordenadas, fechas o enums inválidos | 422 |
| NASA no responde | 503, o estado indisponible explícito; no inventar fallback |
| NASA cobertura parcial | Disponibilidad parcial/insuficiente y explicación |
| Comparación válida pero evidencia limitada | `agronomicViability=not_assessed` |

La política de caché debe asegurar que datos de otro punto/periodo no se presenten como propios y que el punto original no se sustituya por el punto redondeado. La sesión en proceso del backend existente obliga a probar sticky session o despliegue de instancia única, no asumir escalado horizontal.
