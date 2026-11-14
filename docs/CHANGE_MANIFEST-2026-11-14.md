# Manifiesto de Cambios · Solquira — Next Station
**Fecha:** 2026-11-14  
**Repositorio:** `Shinken009/solquira-next-station`  
**Licencia:** Apache-2.0

---

### Resumen de Commits Realizados

1. **`77916c1`** — `feat(init): initialize Solquira Next Station baseline from verified 2026-11-10 audit`
   - Creación del repositorio independiente desde la base madura `codex/nasa-power-studio-20261110` (anclada sobre `803940d`).
   - Inclusión de las cuatro áreas de Studio, Cesium 3D, soporte bilingüe ES/EN, temas light/dark y admisión NASA POWER.
   - 270 archivos versionados, 46.605 inserciones netas.
2. **`0eb1a89`** — `fix(build): prune orphaned workspace references in pnpm lockfile for frozen-lockfile parity`
   - Corrección de raíz del error `Headless installation requires a pnpm-lock.yaml file` eliminando referencias obsoletas a prototipos fuera de workspace.
   - Paridad total de `pnpm install --frozen-lockfile`.
3. **`4c1c739`** — `chore(gitignore): register vercel environment exclusions`
   - Exclusión de `.vercel` y `.env*` para proteger el entorno local de filtraciones.
4. **`81a3342`** — `feat(science): add Field Shift multi-season NASA POWER aggregation and deterministic tradeoffs`
   - Creación del módulo `artifacts/solquira/backend/field_shift/` (`schema.py`, `seasonal.py`, `tradeoffs.py`, `adapter.py`, `routes.py`).
   - Agregación estacional plurianual (ventanas `apr_sep` y `oct_mar`), descarte estricto de temporadas incompletas, sentinels ($-999$), unidades verificadas (`mm/day`, `C`) y time-standard `UTC`.
   - Comparador determinista de 4 rotaciones agrícolas (`continue`, `legume`, `cover`, `forage`), exposición hídrica modulada por señales NASA y condición de drenaje/suelo auto-reportada.
   - Sello invariable de `agronomic_viability = "not_assessed"`.
   - Incorporación de `artifacts/solquira/backend/test_field_shift.py` (13 tests unitarios adicionales).
   - Montaje aditivo de rutas bajo `/solquira-api/studio/field-shift/`.
5. **`f4b0e35`** — `feat(ui): add Field Shift seasonal journey with rapid presets, rotation tradeoffs and bilinguality`
   - Creación de `FieldShiftJourney.tsx` y `field-shift.css` en `artifacts/solquira/src/studio/geo/`.
   - Presets de inicio rápido: Coquimbo (déficit hídrico/secano), Maule (transición mediterránea/rotación), Chiloé (paisaje húmedo/drenaje) sin limitar la navegación libre global.
   - Indicadores visuales de exposición a sequía y anegamiento, resumen estacional plurianual y procedencia de datos con enlace a la documentación oficial de NASA POWER.
   - Total paridad de idioma Español / English mediante `useStudioPreferences`.
   - Integración fluida en `FieldContext.tsx`.

---

### Archivos Afectados

```text
A  artifacts/solquira/backend/field_shift/__init__.py
A  artifacts/solquira/backend/field_shift/adapter.py
A  artifacts/solquira/backend/field_shift/routes.py
A  artifacts/solquira/backend/field_shift/schema.py
A  artifacts/solquira/backend/field_shift/seasonal.py
A  artifacts/solquira/backend/field_shift/tradeoffs.py
A  artifacts/solquira/backend/test_field_shift.py
M  artifacts/solquira/backend/studio_api.py
A  artifacts/solquira/src/studio/geo/FieldShiftJourney.tsx
A  artifacts/solquira/src/studio/geo/field-shift.css
M  artifacts/solquira/src/studio/geo/FieldContext.tsx
M  pnpm-lock.yaml
M  .gitignore
A  docs/BASELINE-2026-11-14.md
A  docs/PROVENANCE-2026-11-14.md
A  docs/QA-2026-11-14.md
A  docs/CHANGE_MANIFEST-2026-11-14.md
```
