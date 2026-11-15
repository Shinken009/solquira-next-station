# Solquira — Next Station
**Understand the land. Prepare the next season.**

Solquira — Next Station is an open-source extension of the existing [Solquira](https://github.com/Shinken009/solquira) geospatial decision-support platform by R4Logic, adapted for the **NASA Space Apps Challenge 2026 — Field Shift: Adapting Farms with NASA Data**. The project explores how different seasonal water conditions—from drylands affected by desertification to rainy landscapes affected by excess water—change questions growers should ask before choosing crop-rotation pathways.

**Application:** https://solquira-next-station.vercel.app  
**Source:** https://github.com/Shinken009/solquira-next-station

## What the product does

1. **Locate and confirm** a field or an illustrative location on an interactive Cesium 3D/2D map.
2. **Inspect historical NASA evidence:** NASA POWER Daily Point AG precipitation (`PRECTOTCORR`) and temperature (`T2M`), with daily completeness rules across 2021–2025. Explore April–September and October–March seasonal windows.
3. **Explore the evidence:** seasonal rainfall totals, dry-day frequency, heavy-rain days and provenance; history is not a forecast.
4. **Add field knowledge:** report soil texture and drainage, leave them unknown, or explicitly load an **illustrative demonstration profile**. A demo profile is *hypothetical*, neither measured nor a regional statistical average.
5. **Compare four example crop-rotation pathways** using transparent, deterministic relative indices for drier/wetter conditions, ground cover and rotation diversity. These indices are **not probabilities, yield projections or local agronomic viability scores**.
6. **Review the limits and next field checks** before making a human decision.

Illustrative starting regions in Chile:
- **Coquimbo:** explore water scarcity and dryland stress.
- **Maule:** explore seasonality in a Mediterranean climate.
- **Chiloé:** explore frequent rainfall, drainage and field access.

Global coordinate selection remains available. The **four original Solquira Studio areas**—Territory, Anticipation, Guidance and Evidence—remain present, with ES/EN and light/dark modes. This is not a reduced stand-alone proof of concept.

## Architecture and deployment separation

```text
Next Station React/TypeScript + Cesium (Vercel)
  ├─ /solquira-api/studio/bootstrap, /location, /evidence, /power, ...
  │      -> original Solquira FastAPI on Akamai (not modified by this fork)
  └─ /solquira-api/studio/field-shift/{evaluate,healthz}
         -> isolated Vercel Python Function (api/field_shift.py)
              -> verify existing opaque Studio cookie + CSRF via Akamai /studio/evidence
              -> run bounded NASA POWER historical adapter + deterministic comparison
              -> return results with source, quality and assumption provenance
```

The isolated function validates session/CSRF before accessing NASA, limits request size/concurrency, and rejects unavailable/incomplete evidence rather than fabricating measurements. Per-instance Vercel limits are not distributed global quotas; the original Studio's admission policy still protects delegated verification. No credential is embedded in the frontend. The original [Solquira](https://solquira.vercel.app) continues separately.

## Reproducible science and limits

- **NASA POWER:** https://power.larc.nasa.gov/ — daily AG meteorology on a modeled grid; source endpoint https://power.larc.nasa.gov/api/temporal/daily/point .
- **NASA GIBS:** https://gibs.earthdata.nasa.gov/ — NASA imagery via the original geospatial Studio, with MODIS layers where available.
- **Period used in this Field Shift adapter:** 2021-01-01 through 2025-12-31 UTC. Five complete April–September seasons and four complete October–March seasons may be compared. A season with missing days is excluded; at least three complete seasons are required.
- **Interpretation:** gridded historical estimates are not parcel measurements; not a forecast for 2026/2027. Water-exposure indices are illustrative deterministic comparisons. Agronomic viability remains `not_assessed`; obtain local soil, crop, rainfall and technical field validation before action.
- **Field provenance:** `soil_origin` and `drainage_origin` distinguish `self_reported` from `illustrative_demo`.
- The model does not invent NASA observations when the source fails.

## Audited interpretation method

For a transparent, formula-by-formula description of NASA observation windows,
parameter thresholds, heuristic coefficients, sorting rules, missing data,
illustrative soil profiles and agronomic limitations, see the
[Field Shift methodology and science audit](docs/field-shift-methodology.md).

**Important:** Historic temperature is shown as context but does not currently
change the crop-rotation comparison indices. Soil texture contributes to
written context, while the illustrative wet-exposure index uses the
user-reported or demonstrative drainage category. These are scenario
explorations—not crop suitability predictions.

## Technology

React, TypeScript, Vite, CesiumJS, OpenStreetMap, Python 3.12, Pydantic, FastAPI (original Studio), Vercel Python Functions, NASA POWER Daily Point API, NASA GIBS, and deterministic rules. Code and design work include assistance from generative AI tools as disclosed below.

## Test and build

```bash
pnpm install --frozen-lockfile
pnpm run typecheck
pnpm --filter @workspace/solquira build

python -m pip install -r artifacts/solquira/backend/requirements.lock.txt
python -m unittest discover -s artifacts/solquira/backend -p 'test_*.py'
python scripts/check-fixtures.py
```

The backend suite was independently reproduced with **386 passing Python tests** after installing the test-only optional NumPy dependency; production front-end typechecking and build also passed in isolated Vercel QA. These are code-level checks, distinct from public HTTP integration and visual/browser acceptance.

## Original work, sources, and AI/SI disclosure

Next Station builds on the pre-existing open-source Solquira project and introduces a new challenge-focused, seasonality-oriented layer. Contributors retain responsibility for the project design, scientific assumptions, review, tests and decisions.

Generative AI/SI tools (ChatGPT, Codex/Antigravity when available, and Magnific for selected audiovisual assets) supported code drafting/review, bilingual copy, test generation and audiovisual editing. Generated code and copy have been reviewed and should be distinguished from real NASA or field observations. Any AI-generated video footage in the competition demo must carry a **visible on-screen watermark**, and generated audio/music must be identified in video metadata/description. No NASA logo or official NASA-branded design asset is generated or modified.

Other resources: [CesiumJS](https://cesium.com/platform/cesiumjs/), [OpenStreetMap](https://www.openstreetmap.org/copyright), [Vite](https://vite.dev/), [React](https://react.dev/), and [FastAPI](https://fastapi.tiangolo.com/). See `LICENSE` for project license and `docs/space-apps-submission.md` for public attribution and submission copy.
