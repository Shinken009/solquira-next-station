# Field Shift — Science and Interpretation Audit

Solquira — Next Station extends the existing Solquira Studio to help users compare
**illustrative** seasonal management pathways. The historic NASA POWER series are
real external data; the crop-rotation *scores* are human-designed, deterministic
scenario indicators and **have not been field-calibrated or validated as forecasts**.

## 1. Data origin, time and geography

- Source: [NASA POWER Daily Point API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) using the Agroclimatology (AG) community.
- Parameters: `PRECTOTCORR` (daily precipitation, mm/day) and `T2M` (mean 2-m air temperature, °C). The API is explicitly requested with `time-standard=UTC`.
- Historical interval: January 1, 2021 through December 31, 2025.
- One **user-confirmed coordinate** is rounded to 0.01° for the NASA point request. These are estimates associated with the POWER meteorological grid, **not a sensor, surveyed farm boundary, precipitation gauge or regional mean**.
- Windows: April–September (up to five complete seasons) or October–March (up to four complete seasons). At least three complete equivalent seasonal windows are required.
- Quality control: reject invalid units and UTC, out-of-range/non-finite values, malformed metadata and total records with less than 85% completeness. Only seasonal windows having **100% of the expected daily records** are included. Otherwise, fail closed without fabricating NASA observations.

## 2. Historical climate features

For each fully observed season, calculate:

- `P`: rainfall total, the sum of daily `PRECTOTCORR`, in millimetres;
- `D`: fraction of days with precipitation **below 1 mm** (0–1);
- `H`: number of days with precipitation **at least 20 mm**;
- `T`: mean daily `T2M`, in °C.

The five- or four-season summary aggregates these by mean, and reports mean and
median rainfall totals and the individual seasonal observations. `T` is
presented as **historical context**, but **is not used in the current rotation
indicator formulas**. This is a specific current limitation, not an AI model.

## 3. Deterministic illustrative comparison

The application compares four *category-level illustrative sequences*:

| ID | Three-step illustrative sequence | Water dependence `w` | Wet access `a` | Ground cover | Diversity |
| --- | --- | ---: | ---: | ---: | ---: |
| continue | Cereal → Cereal → Cereal | 3 | 2 | 1 | 1 |
| legume | Cereal → Legume → Cover | 2 | 2 | 2 | 3 |
| cover | Cover → Cereal → Legume | 3 | 3 | 3 | 3 |
| forage | Forage → Legume → Forage | 2 | 2 | 3 | 2 |

The category coefficients `w`, `a`, cover and diversity are **illustrative
expert-system design assumptions**, not observed crop-trial measurements or
validated cultivar tolerances. Actual species, rotation duration, agroecological
viability and local agronomic performance remain **not assessed**.

For each pathway:

```text
D = mean over complete seasons of the fraction of days with precipitation < 1 mm
H = mean over complete seasons of the count of days with precipitation >= 20 mm

dry_index = round(100 × D × w / 3)

rain_signal = min(1, H / 12)
drainage_multiplier = 0.65 if well_drained, 1.25 if restricted,
                      undefined if unknown

wet_index = round(min(100, 100 × rain_signal × a / 3 × drainage_multiplier))
            or missing when drainage is unknown

primary_index = dry_index                   if concern == "dry"
                wet_index                   if concern == "wet"
                round((dry_index+wet_index)/2) if concern == "balanced"
                missing                     if a required wet_index is missing
```

The thresholds (1 mm/day, 20 mm/day), the reference value of **12 heavy-rain
days**, and the drainage multipliers are disclosed **heuristics**. The
resulting 0–100 numbers are **not calibrated percentages, the probability of
drought/waterlogging, crop yield projections, historical frequencies of crop
failure, or measured site risk**.

### Sort semantics

- Priority **Water management:** ascending `primary_index` for the user's selected dry, wet, or balanced concern. Missing `primary_index` is never replaced with an invented score.
- Priority **Soil cover:** descending fixed ground-cover category level.
- Priority **Diversity:** descending fixed rotation-diversity category level.

Sorting shows how *illustrative assumptions* compare; ranking never implies a
validated best farm rotation.

## 4. What farmer input changes

- **Drainage:** choosing well-drained or restricted changes the **heuristic wet index** and explanatory notes; leaving it unknown keeps wet indices missing.
- **Soil texture:** sandy/clayey/loamy selection changes **contextual explanatory observations**, not the current numeric exposure indices.
- **Main concern:** chooses which of the dry/wet indices drives the water-priority ranking.
- **Priority:** sorts the already computed illustrative pathways; it does not alter NASA data.
- **Previous crop:** the backend supports an optional crop category for an additional warning. The current Field Shift web panel does not yet collect a complete rotation history or cultivar-level agronomic attributes.

Profiles prefilled for Coquimbo, Maule and Chiloé are **explicitly opt-in
hypothetical demonstrations**, **not representative regional averages**. If the
person enters their own field characteristics, the provenance is recorded as
`self_reported` rather than `illustrative_demo`; neither constitutes a
laboratory or site-verified soil measurement.

## 5. Scientific and operational boundaries

- Seasonal NASA POWER climate history is **not a next-season forecast**.
- Gridded historical meteorology is **not parcel-scale soil moisture**.
- A single historic grid point cannot estimate crop yield, farm profitability,
  soil infiltration, trafficability or optimal planting dates without further
  local evidence.
- The system does not ingest a validated local crop trait database, soil
  laboratory survey, calibration trial or peer-reviewed agronomic viability
  model into its present pathway coefficients.
- The method does not currently verify results with Chilean farm field trials.
- NASA POWER API access depends on an external service and the availability of
  complete multi-year observations. Failure should produce an unavailable
  response, **not synthetic observations**.

## 6. Reproducibility

Executable implementation:
`artifacts/solquira/backend/field_shift/{adapter.py,seasonal.py,tradeoffs.py}`.

Regression tests:
`artifacts/solquira/backend/test_field_shift.py`, with integration and
authorization coverage in the backend suite. The November 14 audit ran
**387 Python unit tests successfully**, including water-priority ordering for
dry/wet contexts. The deployed Vercel endpoint independently returned
validated NASA historical evidence for Coquimbo and Chiloé after the fix.

Original project: [Solquira](https://github.com/Shinken009/solquira).
NASA challenge extension: [Solquira — Next Station](https://github.com/Shinken009/solquira-next-station).

The original Solquira platform predates this challenge. Next Station's
seasonality/adaptation layer and submission materials are described separately
to avoid presenting pre-existing software as an entirely new hackathon build.
