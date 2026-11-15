# Solquira — Next Station

*Water shapes every landscape. Every season brings new choices.*

**A bilingual, open-source seasonal decision-support experience for the NASA Space Apps Challenge 2026 — Field Shift: Adapting Farms with NASA Data.**

[Explore the working application](https://solquira-next-station.vercel.app) · [Read the scientific methodology](docs/field-shift-methodology.md) · [Original Solquira platform](https://github.com/Shinken009/solquira)

## Why Next Station?

In Chile, farms can face prolonged water scarcity in Coquimbo and frequent rain with drainage challenges in Chiloé. Solquira — Next Station connects historical NASA climate information to what people know about their fields, helping them compare possibilities for the next agricultural season.

This is an adaptation of the pre-existing **Solquira** geospatial platform, not a replacement or a claim that the entire Studio was created during the hackathon. The original focus on desertification and land degradation remains central; Next Station extends the questions to wetter regions and seasonal water variability.

## Explore the application

1. **Choose a place.** Select and confirm a point on the CesiumJS 2D/3D map, or begin with illustrative locations in Coquimbo, Maule, and Chiloé.
2. **See the historical climate.** The Field Shift module retrieves NASA POWER gridded daily precipitation and temperature for **2021–2025**. It summarizes complete April–September or October–March windows, including dry days and heavy-rain events.
3. **Add what you know.** Report soil texture and drainage, leave information unknown, or choose a clearly labelled hypothetical teaching profile.
4. **Compare possibilities.** Examine four illustrative crop-rotation pathways through transparent deterministic indicators. Understand which assumptions affected the comparison and what remains to be checked locally.

The public Studio also offers its existing Territory, Anticipation, Guidance and Sources workspaces, in English and Spanish, with responsive layouts.

## How to interpret the results

- NASA POWER reports **historical estimates for a selected grid point**. They are not rainfall measurements from a particular farm, regional averages, or forecasts for an upcoming season.
- Comparative 0–100 indicators are **illustrative heuristics**, not probabilities, yield forecasts, experimentally calibrated crop models, or agronomic prescriptions.
- Historical temperature is available for context but does **not** directly change the current rotation scores. Soil texture currently informs explanations; local agronomic viability remains **not assessed**.
- Unknown or incomplete observations are identified rather than replaced with invented NASA readings. Farmers and advisers should verify drainage, soil characteristics, and crop requirements before field decisions.

The formulas, data-quality rules, provenance distinctions, thresholds, and model limitations are documented in [Field Shift — Science and Interpretation](docs/field-shift-methodology.md).

## Technology

- **Interactive application:** React, TypeScript, Vite and CesiumJS.
- **Seasonal analysis:** Python and Pydantic in an isolated Vercel function, with deterministic comparison rules.
- **Existing Studio services:** FastAPI on Akamai, reused through a same-origin bridge that retains opaque sessions and CSRF verification.
- **Map and weather context:** OpenStreetMap and Natural Earth; NASA GIBS imagery; Open-Meteo forecasts and ERA5-based comparisons available separately in the original Studio.

The source includes the application, required runtime components, package manifests and automated tests. The public frontend does not embed backend credentials.

## NASA data and other resources

| Resource | Role |
| --- | --- |
| [NASA POWER Daily Point API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) | Historical precipitation (`PRECTOTCORR`) and temperature (`T2M`) in the Field Shift analysis |
| [NASA Earthdata GIBS](https://gibs.earthdata.nasa.gov/) | Optional satellite imagery in the wider Studio |
| [Open-Meteo Forecast API](https://open-meteo.com/en/docs) | Separate short-range weather forecast in the original Studio |
| [Open-Meteo Historical Weather / ERA5](https://open-meteo.com/en/docs/historical-weather-api) and [Copernicus](https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels) | Independent historical context, **not** the Field Shift rotation input |
| [CesiumJS](https://cesium.com/platform/cesiumjs/), [OpenStreetMap](https://www.openstreetmap.org/copyright), [Natural Earth](https://www.naturalearthdata.com/about/terms-of-use/) | Interactive maps and reference cartography |
| [Lucide](https://lucide.dev/license), [React](https://react.dev/), [TypeScript](https://www.typescriptlang.org/), [Vite](https://vite.dev/) | Interface framework and icons |
| [Python](https://www.python.org/), [Pydantic](https://docs.pydantic.dev/), [FastAPI](https://fastapi.tiangolo.com/), [Vercel](https://vercel.com/) | Services and deployment |

Open-Meteo and OpenStreetMap data are credited under their applicable attribution requirements; Natural Earth data are in the public domain. The complete open-source dependency inventory is available in the checked-in package manifests and lockfiles.

## Development and AI/SI disclosure

This challenge submission builds on the independently developed [Solquira](https://github.com/Shinken009/solquira) project. OpenAI ChatGPT/Codex and other disclosed development assistants supported selected programming, code review, testing, and writing. Magnific supported production of the demonstration's narration, music and editing. NASA POWER observations themselves were **not** generated by AI. Any SI-generated audiovisual elements must be identified under NASA Space Apps rules; audio and development assistance are disclosed in the demonstration's metadata and the NASA submission.

The work is independently developed and **not endorsed by NASA**.

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).
