# ZIP experimental: auditoría de reutilización · 2026-11-14

Paquete fuente: `reference_only/solquira-next-station-nasa-2026.zip` (prototipo creado previamente). **No instalar como app final ni usar como root de Vercel.**

**Aprovechables con refactor:**
- `backend/nasa_power.py`: normalización de unidades, validación de serie diaria, exclusión de ausentes y verificación de rango; revisar compatibilidad con POWER actual, límites de adquisición, caché y sesiones de Solquira.
- `backend/engine.py`: agrupación por temporadas Apr–Sep y Oct–Mar atravesando año; suma de lluvia y días descriptivos; revisar año de inicio y ventanas parciales.
- `backend/schema.py` y `tests/*`: fixtures y controles útiles; integrarlos a esquema/nombres/protocolo de tests del backend original.
- `docs/SCIENCE.md`: fundamentos y advertencias metodológicas; trasladar sólo afirmaciones respaldadas.

**No trasplantar:** `web/index.html`, `web/app.js`, `web/styles.css`, `backend/app.py` o su despliegue simplificado; no reemplazar componentes React/TS, sesiones, Cesium, fallbacks, validaciones, presupuestos o branding actual.

**CIREN:** `backend/ciren.py` usa IDs de capas y ventanas regionales codificadas; considerarlas **hipótesis a verificar**, no garantía de cobertura. La interfaz debe manejar `unavailable` y `outside_coverage`. No afirmar validez parcelaria ni usar campos desconocidos para puntuar.

**Heurísticos:** comparador del prototipo usa categorías y pesos ilustrativos para 4 rutas; conservar únicamente como tradeoffs declarados sin agronomic suitability. Nunca vincular cifras de ahorro/rendimiento a esos coeficientes.

**Error metodológico a evitar:** fuente con 90% de datos diarios no equivale a temporada 100% completa; para totales estacionales requerir integralidad por período o declarar cobertura explícita sin inventar cero. Los tests deben demostrarlo.
