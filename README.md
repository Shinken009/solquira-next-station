# Solquira — Next Station
## *Understand the land. Cultivate the future.*

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![NASA Space Apps 2026](https://img.shields.io/badge/NASA%20Space%20Apps-2026%20Field%20Shift-orange.svg)](https://www.spaceappschallenge.org/2026/challenges/field-shift-adapting-farms-with-nasa-data/)
[![Vercel Deployment](https://img.shields.io/badge/Vercel-Live%20Preview-success.svg)](https://solquira-next-station.vercel.app)

**Solquira — Next Station** is an open-source territorial decision-support platform created for the **NASA Space Apps Challenge 2026: Field Shift — Adapting Farms with NASA Data**.

Developed by **R4Logic**, Next Station extends the mature, full-scale Solquira Studio into an actionable seasonal adaptation journey:
$$\text{Confirmed Territory} \longrightarrow \text{NASA Earth Observation} \longrightarrow \text{Seasonal Signal} \longrightarrow \text{Self-Reported Constraints} \longrightarrow \text{Rotation Tradeoffs} \longrightarrow \text{Informed Human Decision}$$

---

## Live Deployments & Repository

- **Official Repository:** [https://github.com/Shinken009/solquira-next-station](https://github.com/Shinken009/solquira-next-station)
- **Live Application:** [https://solquira-next-station.vercel.app](https://solquira-next-station.vercel.app)
- **Verified Vercel Preview:** [https://solquira-next-station-g6jywo2ct-shinken009s-projects.vercel.app](https://solquira-next-station-g6jywo2ct-shinken009s-projects.vercel.app)

---

## Key Features

### 1. Full-Product Studio Parity (No Reduced Standalone Toy)
- **Four Core Workspace Areas:** *Territorio* (Territory), *Anticipación* (Anticipation), *Orientación* (Guidance), and *Evidencia* (Evidence).
- **Interactive 3D Geospatial Visualization:** High-performance **CesiumJS** globe with WebGL rendering and resilient 2D fallbacks (OpenStreetMap and Natural Earth).
- **True Bilinguality (ES/EN):** Fluent interface in Spanish and English with persistent accessibility preferences (Light / Dark themes).
- **Session Security & Privacy:** In-process opaque sessions, CSRF protection (`X-Solquira-CSRF`), strict Content Security Policy (CSP), and client-side PII isolation.

### 2. Multi-Season NASA POWER Historical Integration
- Direct integration with the **NASA POWER Daily Point API (AG Community)** for historical precipitation (`PRECTOTCORR`) and 2-meter air temperature (`T2M`).
- **Strict Seasonal Aggregation Windows:** Supports both `apr_sep` (Austral Autumn/Winter) and `oct_mar` (Austral Spring/Summer) across 5 comparative years (2021–2025).
- **Fail-Closed Completeness Policy:** Rejects incomplete seasons rather than distorting metrics with artificial zero-padding. At least three fully observed seasons are required before calculating multi-year averages.
- **Sentinel & Unit Validation:** Enforces `time-standard=UTC`, validates physical bounds ($0 \le \text{rain} \le 1500$ mm/day, $-90 \le T \le 75$ °C), and treats values $\le -900$ as absent.

### 3. Field Shift: Deterministic Tradeoff Explorer
- **Four Comparative Rotation Pathways:**
  1. *Continue baseline pattern:* Cereal $\to$ Cereal $\to$ Cereal.
  2. *Diversify with legumes:* Cereal $\to$ Legume $\to$ Cover.
  3. *Prioritize continuous living cover:* Cover $\to$ Cereal $\to$ Legume.
  4. *Integrate forage pasture:* Forage $\to$ Legume $\to$ Forage.
- **Observable Hydroclimatic Responsiveness:** NASA signals (dry-day share $<1$ mm/day and heavy rain frequency $\ge 20$ mm/day) directly alter calculated drought and waterlogging exposure indices.
- **Self-Reported Field Inputs:** Incorporates operator-stated soil drainage (`well_drained`, `restricted`, `unknown`), texture (`clayey`, `sandy`, `loamy`), and exploration priorities (`water`, `soil`, `diversity`).
- **Ethical Scientific Disclosure:** All alternatives are explicitly tagged with `agronomicViability = "not_assessed"` to prevent automated, unverified agricultural prescriptions.

### 4. Demonstrative Regional Presets
- **Coquimbo, Chile** (`-30.0400, -71.2500`): Water deficit pressure, living soil cover, and desertification protection in semi-arid drylands.
- **Maule, Chile** (`-35.4300, -71.6600`): Seasonal precipitation variability and crop rotation transitions in Mediterranean agricultural valleys.
- **Chiloé, Chile** (`-42.4800, -73.7600`): Excess surface water, machinery trafficability, and drainage management in temperate wet landscapes (*noting that wet landscapes face waterlogging, distinct from arid desertification*).
- *Global Free Selection:* The operator can freely click, search, or input coordinates anywhere on the planet.

---

## Architecture Overview

```text
       [React + TypeScript + Cesium Studio SPA (Vercel Independent)]
                    | Same-origin: /solquira-api/*
                    v
       [Vercel Rewrites Proxy with Strict CSP & HSTS]
                    |
                    v
       [FastAPI Backend (Session, CSRF, Concurrency Admission)]
         |-- /solquira-api/studio/bootstrap
         |-- /solquira-api/studio/location
         |-- /solquira-api/studio/evaluate
         |-- /solquira-api/studio/power           (1–31 day bounded query)
         `-- /solquira-api/studio/field-shift/*   (New additive namespace)
               |-- /evaluate                      (Multi-season NASA + Tradeoffs)
               `-- /healthz                       (Domain healthcheck)
                    |
                    v
       [NASA POWER Daily Point API (LaRC AG)]
```

---

## Local Development & Test Execution

### Prerequisites
- Python 3.11+ (tested on Python 3.12 and 3.14)
- Node.js 20+ (tested on Node 25.8.2)
- pnpm 10+ (tested on pnpm 11.0.0)

### 1. Install Dependencies
```bash
# Frontend & Monorepo workspace
pnpm install --frozen-lockfile

# Backend Python dependencies
pip install -r artifacts/solquira/backend/requirements.txt
```

### 2. Run Test Battery
```bash
# Backend test suite (378 tests)
python -m unittest discover -s artifacts/solquira/backend -p "test_*.py"

# Monorepo TypeScript typecheck
pnpm run typecheck

# Deterministic engine hash & fixtures validation (135 evaluations)
python scripts/check-fixtures.py

# Client land evidence integration tests
node --test scripts/test-land-evidence-client.mjs
```

### 3. Build Frontend for Production
```bash
pnpm --filter @workspace/solquira build
```

---

## Data Provenance & Scientific Disclaimers

1. **Gridded Model Estimates:** Data provided by NASA POWER (Prediction Of Worldwide Energy Resources) are satellite-assimilated global meteorological grids, not on-site farm weather stations or parcel sensors.
2. **Historical vs. Forecast:** Multi-season 5-year observations (2021–2025) provide comparative historical climatological context, not a seasonal forecast or yield prediction for upcoming seasons.
3. **No Automated Prescriptions:** Solquira Next Station is a decision-support and hypothesis exploration tool. It does not replace field visits, soil lab tests, or certified agronomist counsel.
4. **NASA Acknowledgment:** NASA data are in the public domain and used under NASA's open data policy. Mention of NASA or its missions does not imply endorsement, certification, or commercial sponsorship.

---

## Provenance & License

- **Base Project:** Derived from the open-source [Solquira](https://github.com/Shinken009/solquira) codebase created by Roberto Pizarro and the R4Logic team.
- **License:** Distributed under the [Apache License, Version 2.0](LICENSE).
- **Notices:** Third-party licenses, data sources, and libraries are cataloged in [NOTICE](NOTICE) and [docs/PROVENANCE-2026-11-14.md](docs/PROVENANCE-2026-11-14.md).
