# Ciencia, metodología y procedencia · 2026-11-14

## Matriz de variables

| Variable | Origen | Uso P0 | Precisión/limitación |
|---|---|---|---|
| punto confirmado | Cesium/GPS opcional/usuario | seleccionar celda/contexto | No delimita predio; no almacenar sin consentimiento |
| `PRECTOTCORR` | NASA POWER Daily API AG | suma estacional | mm/día gridded/modelado, no pluviómetro predial |
| `T2M` | NASA POWER Daily API AG | temperatura media del período | °C a 2 m, no microclima predial |
| condición de drenaje, cultivo previo, suelo | agricultor/usuario | modular tradeoffs | `self_reported`, no medición verificada |
| prioridades (agua, suelo, diversidad, factibilidad) | usuario | ordenar la interpretación | preferencia, no evidencia de impacto |
| ERA5/Open-Meteo | producto original | contexto diferenciado | no mezclar 7d forecast con historia NASA |
| CIREN/IDE MINAGRI | fuente pública si disponible | lectura adicional voluntaria | licencia, cobertura, año/escala variables |
| GPM/SMAP/Landsat/SRTM | NASA opcional P1/P2 | evidencia futura sólo tras QA | no declarar integrado antes de hacerlo |

## Estaciones y cobertura

- Ventanas de demostración Chile: abril–septiembre (mismo año); octubre–marzo (anclada al año del octubre de inicio). Otras latitudes y usos agrícolas requieren calendario apropiado explícito.
- Utilizar períodos completos únicamente; para cada temporada enumerar días esperados y válidos (incluye años bisiestos); no sumar fechas ausentes como cero.
- El período 2021–2025 sirve como referencia experimental de 5 años, **no es una normal climatológica de 30 años** y no predice 2026/2027.
- Al menos tres estaciones completas comparables para promedios multiestacionales; si no, mostrar `insufficient_data`.
- Valor diario de precipitación menor que 1 mm/día y mayor o igual a 20 mm/día, si se usan, son umbrales descriptivos y declarados, nunca criterios universales de sequía/inundación.
- Nunca atribuir incremento de rendimiento, ahorro de agua o salud del suelo a una rotación sintética sin evaluaciones agronómicas independientes.
- Umbrales de alternativas son decisiones de interfaz y heurística; documentar cada regla y su sensibilidad; no usar nombre `suitability_score` ni ranking universal.
- En Coquimbo pueden discutirse déficits de agua y protección contra degradación; en Chiloé, exceso de precipitación y limitaciones reportadas de suelo húmedo. **Chiloé lluvioso no es «desertificación» por su lluvia**.

## Estado de fuentes

Las etiquetas de calidad permitidas deben distinguir: `observed_or_modeled_source`, `self_reported`, `illustrative_assumption`, `missing`, `unavailable`, `not_applicable`. Una imagen GIBS visual no demuestra por sí sola un NDVI/NDMI cuantitativo. Un polígono CIREN regional no constituye inspección parcelaria. Datos de NASA POWER históricos no son pronóstico.

**Cadena demostrable:** NASA POWER válida → resumen temporal reproducible → restricciones/contexto humanos → evaluación determinista de tradeoffs → evidencia y límites → explicación IA opcional. El paso NASA→evaluación debe tener prueba automatizada.

## Referencias oficiales
- https://power.larc.nasa.gov/docs/services/api/temporal/daily/
- https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/
- https://www.ciren.cl/suelo
- https://geoportal.cl/geoportal/catalog/42521/servicio-web-de-mapas-uso-de-la-tierra-ciren
