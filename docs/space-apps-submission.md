# NASA Space Apps 2026 — Solquira Next Station — submission copy

**Submission deadline:** 15 November 2026, 11:59 PM local event time. Confirm in the NASA Space Apps submission form before submitting.  
**Selected challenge:** Field Shift: Adapting Farms with NASA Data  
**Team:** R4Logic  
**Project name:** Solquira — Next Station

## Project Summary (English; 146 words; 996 characters; under the 1500-character limit)

Water shapes every landscape, and every farming season brings new choices. In Chile, Coquimbo often faces limited rainfall, while Chiloé must also prepare for heavy rain and drainage problems. Solquira — Next Station extends the existing open-source Solquira geospatial platform for NASA Space Apps' Field Shift challenge.

Farmers and advisers choose a place on a map and explore NASA POWER's 2021–2025 historical precipitation and temperature records. They can add what they know about soil texture and drainage, or use clearly labelled hypothetical examples. Four illustrative crop-rotation pathways are compared using documented rules, with explanations of what the numbers mean and what still needs to be checked locally.

Next Station brings seasonal climate information and field knowledge into one bilingual workspace. It does not predict harvests, forecast next season's weather, or certify which crops will succeed. Instead, it helps people explore their options before the next season.

## Project Details (English)

**Problem.** A single prescribed crop-rotation pattern cannot address both drought and high-rainfall conditions. Decisions depend on the land, season, soil characteristics, local constraints, and a grower's priorities. Weather-grid datasets are powerful, but difficult for non-specialists to interpret responsibly.

**Solution.** Solquira — Next Station adapts an existing, openly developed geospatial Studio to the Field Shift challenge. It retains the complete Territory, Anticipation, Guidance, and Sources workspaces (the last is internally the evidence area) rather than creating a minimal replacement. Users may select any valid coordinates in a CesiumJS 3D/2D geographic interface, review the marker, and explicitly confirm the point. The Field Shift module queries NASA POWER's daily AG dataset for precipitation (PRECTOTCORR) and 2-m air temperature (T2M) between 2021 and 2025. It summarizes April–September and October–March seasonal windows, discards incomplete seasons, and refuses to invent missing observations.

**From NASA weather records to comparisons.** The interface presents seasonal precipitation totals, frequencies of days with less than 1 mm of rain, and days receiving at least 20 mm. These signals feed deterministic comparison rules for four illustrative rotation pathways: continue a cereal baseline, diversify with legumes, use living cover, or integrate forage. The 0–100 indices are explanatory comparisons; they are not event probabilities, yield forecasts, or validated agronomic prescriptions. Unknown drainage does not receive a fabricated intermediate value. Historical NASA POWER grid-point estimates are not on-site measurements.

**What people know about their land.** Farmers may report soil texture and drainage or leave them unknown. Optional demonstration profiles allow visitors to see how assumptions affect the comparison, but the response explicitly records their hypothetical provenance. The Studio supports Spanish and English, accessible presentations, light/dark modes, and mobile interaction. The Chilean demonstration places—Coquimbo (dryland), Maule (seasonal transition), and Chiloé (rainfall/excess-water context)—illustrate a method transferable internationally.

**Engineering.** React, TypeScript, Vite, CesiumJS, Python, Pydantic, deterministic hydrometeorological rules, NASA POWER Daily Point AG API, NASA GIBS for imagery in the wider Studio, OpenStreetMap and Natural Earth mapping resources, Lucide iconography, Vercel serverless execution, and an existing FastAPI Studio backend. The original Studio separately uses Open-Meteo forecasts and ERA5-based historical weather comparisons; those sources do not drive the Field Shift pathway calculations. User authorization uses opaque sessions, CSRF and bounded admission. Field Shift runs in a separate Vercel function and reuses existing Studio authentication without changing the original Solquira application or its Akamai server.

**What it can and cannot tell you.** This is a working, open-source decision-support prototype: it clarifies past climate variability, makes assumptions visible, and guides what a user should investigate next. It does not claim validated crop suitability, predict future seasonal weather, or replace soil testing and local agronomic advice. Further validation would require local soil and crop evidence, independent field trials, and farmer feedback.

## Independent science audit and source-code distinction

Detailed reproducible methodology:
https://github.com/Shinken009/solquira-next-station/blob/main/docs/field-shift-methodology.md

**Important for jury transparency:** Solquira is a pre-existing, independently
developed open-source geospatial platform. **Next Station** is the 2026 NASA
challenge-focused extension for seasonal NASA evidence and illustrative field
comparisons. Acknowledge that origin explicitly rather than claiming every
platform component was built during the hackathon.

The historic temperature signal is available as environmental context; it is
not a direct numerical input into the current pathway indicator formulas.
Likewise, demo soil texture changes written explanations rather than numerical
exposure indicators. The comparison uses category-level heuristics, not a
validated local crop-characteristics database, so no real-world crop
viability prediction is claimed.

## Public project link (Project*)

https://solquira-next-station.vercel.app

Additional open repository:
https://github.com/Shinken009/solquira-next-station

## Project demonstration link (Project Demonstration*)

**FINAL EDITED MASTER (not yet publicly hosted):** https://www.magnific.com/app/creation/3zb1xJaREY . This 28.9-second H.264/AAC MP4 replaces the earlier master. The 0–5.0 s introduction uses authentic screen capture from the running application, not AI-generated environmental footage. The large 'AI-GENERATED FOOTAGE' label is therefore no longer present. The original AI-generated narration and music remain, and are credited on the end card. The Magnific editor link is not an unrestricted public demo URL; upload this edited master to YouTube or another approved host and verify the anonymous URL.

**TO COMPLETE:** paste the final published YouTube video link after checking (a) duration <=30.0 s in the exported master, (b) visibility unrestricted in a private browsing window, (c) all visual material is authentic UI capture or non-generative graphics (the synthetic environmental opening was replaced), (d) AI narration/music and AI-assisted code/text are disclosed in description/metadata, (e) the source product captures remain authentic. Do not paste a protected Magnific editor or Vercel preview link as the required public demonstration.

## NASA Data (*)

- NASA POWER Prediction Of Worldwide Energy Resources — Daily Point API (AG), 2 m temperature T2M and precipitation PRECTOTCORR, UTC: https://power.larc.nasa.gov/docs/services/api/temporal/daily/
- NASA Earthdata Global Imagery Browse Services (GIBS) — spatial imagery layers used within the existing geospatial Studio: https://gibs.earthdata.nasa.gov/
- NASA GIBS API and attribution: https://nasa-gibs.github.io/gibs-api-docs/

NASA imagery acknowledgment: *We acknowledge the use of imagery provided by services from NASA's Global Imagery Browse Services (GIBS), part of NASA's Earth Science Data and Information System (ESDIS).*

## Space Agency Partner and Other Data / Tools

List these as separate *Link Text* / *Link URL* rows, under **Other Data**, not NASA Data. The original Studio's forecast and historical reanalysis are distinct from the NASA POWER Field Shift calculation.

- Original Solquira platform and source (pre-existing, Apache-2.0): https://github.com/Shinken009/solquira
- Open-Meteo Forecast API — independent 7-day Studio forecast: https://open-meteo.com/en/docs
- Open-Meteo Historical Weather API — separate ERA5-based reanalysis context in the original Studio: https://open-meteo.com/en/docs/historical-weather-api
- ECMWF/Copernicus Climate Data Store — ERA5 source: https://cds.climate.copernicus.eu/datasets/reanalysis-era5-single-levels
- Open-Meteo licensing and credits (API data CC BY 4.0; free public API subject to service terms): https://open-meteo.com/en/features#terms
- Natural Earth — fallback map resources (public-domain data): https://www.naturalearthdata.com/about/terms-of-use/
- Lucide — interface icons, ISC license: https://lucide.dev/license
- CesiumJS interactive 3D and 2D globe: https://cesium.com/platform/cesiumjs/
- OpenStreetMap maps and contributors, with attribution: https://www.openstreetmap.org/copyright
- React: https://react.dev/
- TypeScript: https://www.typescriptlang.org/
- Vite: https://vite.dev/
- Python: https://www.python.org/
- Pydantic: https://docs.pydantic.dev/
- FastAPI: https://fastapi.tiangolo.com/
- Vercel hosting/functions: https://vercel.com/
- Playwright — browser testing: https://playwright.dev/
- GitHub — public source repository and version history: https://github.com/
- Magnific creative/video tooling: https://www.magnific.com/
- OpenAI ChatGPT and Codex for code, scientific-copy and testing assistance: https://openai.com/

Check any additional assets, fonts, third-party music, datasets or libraries actually present in the final video/app before submitting. The source package manifests and lockfiles identify further dependencies. Do not imply a dataset directly drives the rotation calculation unless it really does. If Google Antigravity or any additional AI platform was actually used for the submitted build, disclose it in the SI selections and add its official link; do not list tools that were never used.

**Separation of sources:** NASA POWER = actual historical weather inputs for Field Shift. NASA GIBS = optional regional imagery in the existing Studio. Open-Meteo = the separate forecast and ERA5 reanalysis workspace. OpenStreetMap/Natural Earth = geographic reference. No listed dataset provides measured crop-trial performance or site-specific soil laboratory validation.

## Use of Super Intelligence (SI*)

Generated code and text: Generative AI assistants (OpenAI ChatGPT/Codex, and Google Antigravity if applicable during development) assisted with code drafting, localization, testing and review; the human creator remained responsible for engineering choices, data interpretation and final validation. Source code and this README describe these contributions. NASA POWER readings themselves were queried from NASA and were never artificially generated.

Video production: Magnific was used for audiovisual creation and editing, but **the final submitted demo does not contain the previously generated environmental footage**. That clip was replaced by a genuine screenshot of the deployed Solquira interface, composed with non-generative editing. The rest of the demo uses genuine application captures and simple graphic overlays. There is therefore no AI-generated visual footage in the final MP4 requiring a visual watermark. If any generated visual footage is reintroduced, NASA's visible-watermark requirement must be satisfied.

Generated audio: Any AI-synthesized narration or soundtrack should be declared in the YouTube description, production metadata and/or source credits. Generated soundtrack and voice are not NASA recordings.

Do **not** add a generated NASA logo, flag, mission identifier, or design element to the video or website.

## Public video description / metadata (copy after uploading)

**Title:** Solquira — Next Station | NASA Space Apps 2026 | Field Shift

**Description:**

Solquira — Next Station explores how farms face both water scarcity and heavy rain. See the working project: https://solquira-next-station.vercel.app

Public source: https://github.com/Shinken009/solquira-next-station

Challenge: NASA Space Apps Challenge 2026 — Field Shift: Adapting Farms with NASA Data.

This demonstration opens with an authentic screenshot of the working Solquira application and contains real product-screen captures, not AI-generated environmental footage. The original soundtrack and narration were AI-generated with assistance from Magnific and are credited on screen at the end. Magnific supported audiovisual production and editing. OpenAI ChatGPT/Codex assisted with code review, testing and writing; the project author checked the final work.

NASA POWER supplies historical gridded precipitation and temperature (2021–2025); NASA GIBS imagery is available in the wider Studio. Historical data do not forecast the next season. Crop-rotation comparisons are illustrative, not validated planting guidance. Solquira predates the hackathon; Next Station is the adapted Field Shift experience. NASA does not endorse this project.

Project data, sources, and methods: https://github.com/Shinken009/solquira-next-station/blob/main/docs/field-shift-methodology.md

**Metadata checklist:** Ensure the video platform's title/description identifies AI-generated narration and soundtrack; no synthetic environmental footage is present in this final version. Verify you have rights to use all footage/audio.

## Registration / eligibility check

- **Team:** R4Logic; verify the actual NASA Space Apps account is registered for the intended *local event* and the Field Shift challenge, and its member(s) are correctly listed. Do not assume an association from the public source repository.
- **Solo participation:** NASA Space Apps GO Team clarifies that the two-person minimum for Global Judging applies to the *Universal Event*, not local events; verify local-event membership before submitting (see https://github.com/nasa/spaceapps/discussions/1938).
- **Originality:** Explicitly distinguish the pre-hackathon Solquira platform from the Next Station contribution. Disclose code, content, audiovisual SI support and third-party resources.
- **Deadline:** 15 November 2026 at 11:59 PM in the registered event's local time. Confirm the exact deadline shown in the NASA dashboard.
- **Final action:** Complete all required sections and *submit for judging*, not merely save. Preserve the confirmation.

## Publish checklist

- [ ] Project summary, details and name checked in English.
- [ ] Independent anonymous browser can access the web app without a password, approval or registration.
- [ ] Main product demo runs with real NASA POWER historical evidence.
- [ ] Final revised demo duration **strictly <= 30 seconds**; the synthetic introductory footage has been replaced with a genuine app screenshot. AI audio acknowledged in the video and public description.
- [ ] Video audio/description explicitly identifies AI usage.
- [ ] Final YouTube link works in incognito without password, request for permission, or account sign-in.
- [ ] All NASA source and third-party tool links listed and verified, including Open-Meteo/ERA5, Natural Earth, Lucide, OpenStreetMap, original Solquira, and actual audiovisual resources.
- [ ] R4Logic event/team membership checked directly in NASA; local/Universal eligibility confirmed.
- [ ] Original Solquira identified as pre-existing work; Next Station described as the challenge extension.
- [ ] Project app, video, and code links each open in a private browser without access approval.
- [ ] All audio/visual usage rights and on-platform SI disclosures checked.
- [ ] Submit in the NASA Space Apps interface before the local deadline.
