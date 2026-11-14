# Protocolo QA y gates · 2026-11-14

El agente debe registrar PASS/FAIL/NOT RUN, comando, rama/SHA, fecha real, host, evidencia, captura/log y responsable. No heredar la afirmación «20 tests pasan» del ZIP simplificado como prueba de Next Station integrado.

| Gate | Verificación |
|---|---|
| G0 Audit | Árbol local, git status, AGENTS, SHA remoto y rutas efectivas inspeccionadas sin mutación |
| G1 Isolation | Nuevo workspace, `.git`/Vercel separados, secretos excluidos, originales intactos |
| G2 Parity | Tests Python, fixtures, typecheck, build, QA Cesium/UX del README original |
| G3 NASA | 2 coordenadas diferentes → resúmenes trazablemente diferentes con datos reales; período completo y unidades validadas |
| G4 Completeness | faltantes, 0 válido, -999 sentinels, días bisiestos, límites fechas, ventanas Oct–Mar, time-standard |
| G5 Decision | señales POWER alteran los tradeoffs; no «score» de viabilidad sin evidencia |
| G6 Human | suelos/prioridades auto-reportados y sin coerción; faltantes explicados |
| G7 Fail closed | offline/timeout NASA → indisponible sin números inventados; CIREN/IA no bloquean resultado determinista |
| G8 Security | 401 sesión, 403 CSRF, 422 contrato, 429 presupuesto, payload, CSP/CORS, cookies/host, no claves bundle |
| G9 Responsive | 320, 390, 1440 px; ES/EN, light/dark, teclado y lector; no perder Cesium/contexto |
| G10 API regression | endpoints maduros y `/v1/*` conservan contratos/latencias esenciales |
| G11 Vercel | Preview nuevo, rewrite del nuevo host, no modificar producción original |
| G12 Attribution | NOTICE, LICENSE, autoría previa, NASA/CIREN/terceros, uso de IA y limitaciones |

Comandos de referencia desde raíz, validados por el README remoto (adecuar al árbol real):

```powershell
python -m unittest discover -s artifacts/solquira/backend -p "test_*.py"
pnpm.cmd run typecheck
python scripts/check-fixtures.py
node --test scripts/test-land-evidence-client.mjs
# Iniciar servidor local con modo sin inferencia según README antes de QA navegador
node scripts/qa-environment-navigation.mjs http://127.0.0.1:8036
node scripts/qa-territorial-journey.mjs http://127.0.0.1:8036
node scripts/qa-land-evidence.mjs http://127.0.0.1:8036
node scripts/qa-cesium-selection.mjs http://127.0.0.1:8036
node scripts/qa-studio-preferences.mjs http://127.0.0.1:8036
```

**Gate operativo:** no desplegar nuevo backend en servidor compartido antes de probar feature flag y regresión; no inferir que un error Windows `EPERM` de symlinks Vercel signifique error de arquitectura. Si ocurre, registrar logs y realizar build remoto/CI con árbol limpio.
