# Matriz de portabilidad y archivos · 2026-11-14

| Fuente | Ruta real / artefacto | Destino conceptual | Acción |
|---|---|---|---|
| Solquira baseline | `artifacts/solquira/src/App.tsx` | Entrada SPA | Conservar sin segunda app |
| Solquira baseline | `artifacts/solquira/src/studio/Studio.tsx` y cercanos | Interfaz, flujo, estado | Extender con Field Shift |
| Solquira baseline | `artifacts/solquira/src/studio/studio-copy*` | Traducciones | ES/EN coherentes |
| Solquira baseline | `artifacts/solquira/backend/main.py` | FastAPI | Router aditivo, flag |
| Solquira baseline | `artifacts/solquira/backend/studio_api.py` | Sesiones/CSRF/admisión | Reutilizar controles actuales |
| Solquira baseline | `artifacts/solquira/backend/power.py` | POWER actual (1–31 días) | Auditar; no flexibilizar límite global |
| Solquira baseline | `studio_service.py` / esquemas | escenarios | Composición Field Shift tipada |
| Solquira baseline | `dryland_brief.py`, `studio_runtime.py`, `studio_budget.py` | IA opcional | Conservar Python autoridad, fallbacks |
| Solquira baseline | `vercel.json`, `pnpm-*`, `.vercelignore` | Build/proxy/security | Copiar desde fuente verificada a repo nuevo |
| ZIP prototipo | `backend/nasa_power.py` | Parser histórico | Revisión selectiva de fechas/unidades/ausentes |
| ZIP prototipo | `backend/engine.py` | Resúmenes Apr–Sep / Oct–Mar | Portar algoritmo tras test científico |
| ZIP prototipo | `backend/schema.py`, `tests/*` | Ideas de contrato/test | Reutilizar sin romper esquema maduro |
| ZIP prototipo | `backend/ciren.py` | Contexto regional opcional | **No usar IDs de capas ni cobertura sin validar** |
| ZIP prototipo | `web/*`, `backend/app.py` | SPA/API simplificada | **No importar** |

La nueva extensión debe crear los menores archivos y cambios posibles. Plan de namespaces recomendado: `POST /solquira-api/studio/field-shift/context`, `/evaluate` y `/evidence`, o extender `/studio/evaluate` tipadamente si la inspección técnica demuestra mejor compatibilidad. No crear endpoints duplicados inconsistentes. La respuesta NASA debe influir en tradeoffs; cualquier coeficiente heurístico se rotula como supuesto, no evidencia observacional.
